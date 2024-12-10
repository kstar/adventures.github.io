#!/usr/bin/env python
#
# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
# License: MIT License

import sqlite3
import pykstars
from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astropy.coordinates import ICRS, get_constellation
import astropy.units as u
import re
from bs4 import BeautifulSoup
import glob
import os
import tqdm
import logging
import time
import json
from typing import Dict, List, Tuple
from collections import deque
from pathlib import Path
import markdown
from urllib.parse import unquote
import numpy as np

logger = logging.getLogger('build_dso_db')
logger.setLevel(logging.INFO)
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOC_DIRECTORY = SCRIPT_DIR / ".." / "docs"
GLOB_PATTERNS = ['*.md', '*.htm*']
DATABASE = SCRIPT_DIR / 'adventures.db'
RESOLUTION_FAILURE_FILE = SCRIPT_DIR / 'unresolved.json'
resolution_failures = {}
COMMIT_INTERVAL = 100

MD_HREF_FINDER = re.compile(r'\[(?:[^\[\]]|\[[^\[\]]*\])+\]\(((?:[^\(\)]|\([^\(\)]*\))+)\)') # Allows non-nested [] in the link text and non-nested () in the URL; needed because of SIMBAD objects e.g. "[R77] 16" as well as webpage names that have parantheses.

HTM_LEVEL = 3
indexer = pykstars.Indexer(HTM_LEVEL)

conn = sqlite3.connect(DATABASE.as_posix())
cursor = conn.cursor()

# Below are files that are essentially catalogs / complete or long lists of objects and not selections; or otherwise must be skipped
skip_files = re.compile('|'.join('(?:' + pat + ')' for pat in [
    r'(?:NGC|IC|UGC) +[0-9]+ *(?:-+|thru|through) *(?:(?:NGC|IC|UGC) *)?[0-9]+.*\.html?', # Skip Steve Gottlieb's notes as they are lists of all objects
    r'(?:NGC|IC|UGC) complete.*\.html?',
    r'UGC \(4-4-20\)\.htm',
    r'Introduction \(4-4-20\)\.htm',
    r'.*\.old',
    r'.*\.html#',
    r'dso_index_constellation.md',
    r'steve.ngc.htm',
]))

def scan_files() -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, str]]: # { simbad_id: { visible_id: [filename,] } }, { filename: article_title }
    pattern = re.compile(r'<x-dso(?:-link)?(?: simbad="([^"]*)")?>((?:(?!</x-dso).)+)</x-dso(?:-link)?>')
    match_title = {extension: re.compile(pattern) for extension, pattern in [
        ('.md', r'\ntitle: *(.+)\r?\n'),
        ('.html', r'<title>((?:(?!</title>).)+)</title>'),
    ]}

    files = [x for xs in [list(DOC_DIRECTORY.glob(glob_pattern)) for glob_pattern in GLOB_PATTERNS] for x in xs]
    targets = {}
    articles = {}
    for filename in tqdm.tqdm(files):
        basename = filename.name
        extension = os.path.splitext(basename)[1]
        if skip_files.match(basename) or basename.startswith('.#'):
            logger.info(f'Skipping {basename}')
            continue
        with filename.open('r') as f:
            text = f.read()
            if extension == '.htm':
                extension = '.html' # Standardize HTML
            try:
                title_match = match_title[extension].search(text)
            except KeyError as e:
                logger.error(f'Files of type {extension} are unhandled in title extraction')
                # raise NotImplementedError(f'Unhandled extension {extension}')

            if title_match:
                title = title_match.group(1)
                if title.startswith('"') and title.endswith('"'):
                    title = title[1:-1]
                if pattern.match(title): # ugh
                    logger.warning(f'Title in file {basename} has <x-dso> tag in it :-/')
                    title = pattern.sub(r'\2', title) # Strip <x-dso...> tags
                articles[basename] = title # articles = {basename.html: title}
            else:
                logger.error(f'No title was found in file {basename}')
                
            for simbad, common in pattern.findall(text):
                if not simbad or len(simbad) == 0:
                    simbad = common
                targets.setdefault(simbad, {}).setdefault(common, []).append(basename) # targets = {simbad_id: {display_id: [article_basename1.htm, article_basename2.html]}}
    return targets, articles

def resolve_and_store(targets):
    # Contains SIMBAD data
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `objects` ("
                   "    main_id TEXT PRIMARY KEY,"
                   "    ra REAL NOT NULL,"
                   "    dec REAL NOT NULL,"
                   "    type TEXT,"
                   "    constellation TEXT NOT NULL,"
                   "    trixel INTEGER NOT NULL)")
    cursor.execute("CREATE INDEX IF NOT EXISTS `idx_trixel_on_objects` ON objects(trixel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS `idx_constellation_on_objects` ON objects(constellation)")
    cursor.execute("CREATE INDEX IF NOT EXISTS `idx_type_on_objects` ON objects(type)")

    # Contains mappings from SIMBAD query id -> SIMBAD internal main id
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `queries` ("
                   "    simbad_id TEXT PRIMARY KEY,"
                   "    main_id TEXT NOT NULL)")

    # Contains mappings from display designations -> SIMBAD internal main id
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `displayed` ("
                   "    row_id INTEGER PRIMARY KEY,"
                   "    display_id TEXT NOT NULL,"
                   "    main_id TEXT NOT NULL,"
                   "    UNIQUE(display_id, main_id))")

    simbad = Simbad()
    simbad.add_votable_fields('otype', 'ra(d)', 'dec(d)')
    cached_simbad_ids = {row[0] for row in cursor.execute("SELECT simbad_id FROM `queries`")}
    # from IPython import embed
    # embed()

    batch_count = 0
    for simbad_id in tqdm.tqdm(targets):
        if simbad_id not in cached_simbad_ids:
            try:
                result = simbad.query_object(simbad_id.strip(' '))
            except Exception as e:
                logger.error(f'Encountered exception {e} trying to query SIMBAD for object {simbad_id}')
                continue

            try:
                if result is None:
                    raise RuntimeError('SIMBAD resolution failed')
                result = result[0]

                # from IPython import embed
                # embed()

                main_id = result['MAIN_ID'].replace('  ', ' ') # Ugh, SIMBAD main-ids need not be unique and have multiple spaces
                ra = float(result['RA_d'])
                dec = float(result['DEC_d'])
                otype = result['OTYPE']
                if np.isnan(ra) or np.isnan(dec):
                    raise RuntimeError("NaN coordinates from SIMBAD")
            except Exception as simbad_exception:
                # Try NED
                try:
                    result = Ned.query_object(simbad_id.strip(' '))[0]
                except Exception as ned_exception:
                    resolution_failures[simbad_id] = [filename for _, filenames in targets[simbad_id].items() for filename in filenames]
                    logger.error(f'Failed to resolve object {simbad_id} mentioned in articles [' + ', '.join(resolution_failures[simbad_id]) + '] using SIMBAD or NED.\nSIMBAD Exception: '+f'{simbad_exception}'+'\nNED Exception: '+f'{ned_exception}')
                    continue
                ra = float(result['RA'])
                dec = float(result['DEC'])
                otype = result['Type']
                main_id = simbad_id.strip(' ') # NED has no concept of MAIN_ID :-(

            if cursor.execute(f'SELECT `main_id` FROM `objects` WHERE `main_id` = "{main_id}"').fetchone() is None:
                # Main ID is not in object table
                try:
                    trixel = indexer.get_trixel(ra, dec)
                    constellation = get_constellation(ICRS(ra * u.deg, dec * u.deg), short_name=True)
                except Exception as e:
                    logger.error(f'Weird behavior trying to index object {main_id} with (ra, dec) = ({ra}, {dec}). Will treat as unresolved')
                    resolution_failures[simbad_id] = [filename for _, filenames in targets[simbad_id].items() for filename in filenames]
                    continue
                    

                # print(f'Resolved Object: {simbad_id}, ra: {ra:0.2f}, dec: {dec:0.2f}, otype: {otype}, trixel: {trixel}, constellation: {constellation}')
                cursor.execute("INSERT INTO objects(main_id, ra, dec, type, constellation, trixel) VALUES (?, ?, ?, ?, ?, ?)",
                               (main_id, ra, dec, otype, constellation, trixel))
                batch_count += 1

            # SIMBAD id was not in the database, add it
            cursor.execute("INSERT INTO queries(simbad_id, main_id) VALUES (?, ?)", (simbad_id, main_id))
            batch_count += 1
            time.sleep(0.1) # To avoid overloading SIMBAD

        else:
            main_id_row = cursor.execute(f'SELECT `main_id` FROM `queries` WHERE `simbad_id` = "{simbad_id}"').fetchone()
            assert main_id_row is not None, f'{simbad_id}'
            main_id = main_id_row[0]

        for display_id in targets[simbad_id]:
            cursor.execute("INSERT OR IGNORE INTO displayed(display_id, main_id) VALUES (?, ?)", (display_id, main_id)) # N.B. Be wary of joining on display_id as sometimes it can be garbage and duplicate, e.g. "<x-dso>NGC 70</x-dso>, <x-dso simbad="NGC 71">71</x-dso> and <x-dso simbad="NGC 72">72</x-dso>" to smoothen the article flow
            batch_count += 1

        if batch_count >= COMMIT_INTERVAL:
            conn.commit()
            batch_count = 0

    conn.commit()

def process_articles(targets, articles):
    # Contains mappings from article to display_id
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `mentions` ("
                   "    mention_id INTEGER PRIMARY KEY,"
                   "    filename TEXT NOT NULL,"
                   "    simbad_id TEXT NOT NULL,"
                   "    display_id TEXT)")
    cursor.execute("CREATE INDEX IF NOT EXISTS `idx_simbad_id_on_mentions` ON mentions(simbad_id)")
    cursor.execute("DELETE FROM `mentions`") # clear the table
    for simbad_id in targets:
        for display_id, filenames in targets[simbad_id].items():
            for filename in filenames:
                cursor.execute("INSERT INTO mentions(filename, simbad_id, display_id) VALUES (?, ?, ?)",
                               (filename, simbad_id, None if display_id == simbad_id else display_id))

    cursor.execute(f"CREATE TABLE IF NOT EXISTS `articles` ("
                   "    filename TEXT PRIMARY KEY,"
                   "    title TEXT)")
    cursor.execute("DELETE FROM `articles`")
    for filename, title in articles.items():
        cursor.execute("INSERT INTO articles(filename, title) VALUES (?, ?)", (filename, title))
    conn.commit()

def process_reachability():
    # Contains graph structure of hyperlinks
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `reachability` ("
                   "    filename TEXT PRIMARY KEY,"
                   "    reachable BOOLEAN NOT NULL CHECK (reachable IN (0, 1)),"
                   "    parent TEXT)")
    cursor.execute("CREATE INDEX IF NOT EXISTS `idx_parent_on_reachability` ON reachability(parent)")
    cursor.execute("DELETE FROM `reachability`") # clear the table

    href_in_md = re.compile(r'\[(?:[^\[\]]|(?:\[[^\]]*\]))+\]\(/?((?:[^()]+|\([^()]*\))+)\)') # FIXME: Does not handle nested parantheses / brackets

    # Breadth first search
    visited = { 'dso_index_constellation.md' } # Skip the index, because that defeats reachability
    queue = deque([ 'index.html', 'headbar.html' ]) # Start nodes
    parent = {}
    while len(queue) > 0:
        current = queue.popleft()
        if current in visited or skip_files.match(current):
            continue

        path = DOC_DIRECTORY / current
        extension = os.path.splitext(current)[1]
        stime = time.time()
        if extension in ('.md'):
            with path.open('r') as md_file:
                hrefs = MD_HREF_FINDER.findall(md_file.read())
                # Note: markdown's md -> HTML conversion isn't equivalent to kramdown and so it messes things up, better to use regexes
                # html_content = markdown.markdown(md_file.read()) # Convert to HTML
                # soup = BeautifulSoup(html_content, features='html5lib')
                
        elif extension in ('.htm', '.html'):
            with path.open('r') as html_file:
                soup = BeautifulSoup(html_file.read(), features='html5lib')
                # Find all <a ...> tags that point to ADS articles in the current file
                hrefs = filter(lambda href: href is not None, map(lambda tag: tag.get('href'), soup.find_all("a")))
        elif extension in ('.obs', '.xls', '.jpg', '.jpeg', '.pdf', '.png', '.svg', '.gif'):
            continue # Known ignorable extensions
        else:
            # raise RuntimeError(f'The following file has an unhandled extension for reachability <a...> tag extraction: {current}')
            logger.warning(f'Ignoring file {current} which has unhandled extension for reachability analysis')
            continue


        # if current == 'catalogs.md':
        #     from IPython import embed
        #     embed(header=current)

        # Treat HTTP redirects as a single link
        http_redirect = soup.find("meta", attrs={"http-equiv": "Refresh"})
        if http_redirect:
            hrefs = [re.compile(r'^.*URL=([^\s]*)(?:\s|\b).*$', re.IGNORECASE).sub(r'\1', http_redirect.get('content')).strip('"'),]

        hrefs = map(lambda href: unquote(href).lstrip('/').split('#')[0].split('?')[0], hrefs) # Remove any in-file anchors or GET parameters
        hrefs = filter(lambda href: href and (not href.startswith('mailto:')) and (not href.startswith('http')), hrefs) # Filter out mailto and external links (we assume that all internal links are /foo.html and not prefixed with the full URL)


        for href in hrefs:
            child_path = DOC_DIRECTORY / href
            if not child_path.exists():
                child_path = child_path.with_suffix('.md') # Convert .html to .md to find the source file
            if not child_path.exists():
                raise RuntimeError(f'Could not identify destination file for href {href} in file {path}. Tried {child_path} but it does not exist!')
            child = child_path.name # Use the source filename for consistency
            queue.append(child_path.name)
            if child not in parent:
                parent[child] = current

        visited.add(current)
        # logger.warning(f'Took {time.time()-stime:0.2f}s to process file {current}')

    # Store results in database table
    for filepaths in (DOC_DIRECTORY.glob(glob_pattern) for glob_pattern in GLOB_PATTERNS):
        for filepath in filepaths:
            basename = filepath.name
            reachable = 1 if (basename in visited) else 0
            cursor.execute(f"INSERT INTO reachability(filename, reachable, parent) VALUES (?, ?, ?)",
                           (basename, reachable, parent.get(basename, None)))
    conn.commit()
    

def main():
    logger.info(f'Extracting targets from files matching patterns {GLOB_PATTERNS} in {DOC_DIRECTORY}')
    targets, articles = scan_files()

    logger.info(f'Querying SIMBAD, and caching and indexing target information')
    resolve_and_store(targets)

    logger.info(f'Writing resolution failures to {RESOLUTION_FAILURE_FILE}')
    with RESOLUTION_FAILURE_FILE.open('w') as f:
        json.dump(resolution_failures, f, indent=2)

    logger.info(f'Indexing articles')
    process_articles(targets, articles)

    logger.info(f'Processing reachability')
    process_reachability()

    logger.info(f'Done')

if __name__ == "__main__":
    main()
