#!/usr/bin/env python
#
# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
# License: MIT License

import sqlite3
from datetime import datetime, timezone
import logging
import os
import re
from common import desimbadification, CONSTELLATIONS, make_constellation_map, COMPILED_OBJECT_REGEX, SIMBAD_OTYPE
from pathlib import Path
import json

logger = logging.getLogger('build_dso_db')
logger.setLevel(logging.INFO)
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOC_DIRECTORY = SCRIPT_DIR / ".." / "docs"
DATABASE = SCRIPT_DIR / 'adventures.db'
ARTICLES_COLLAPSE_LIMIT = 3

conn = sqlite3.connect(DATABASE.as_posix())
cursor = conn.cursor()

article_titles = dict(cursor.execute("SELECT filename, title FROM articles").fetchall())

exclude = ["dsf_ootw.md", "dsf_ootw_constellation.md"]

query = """
SELECT mentions.filename, objects.main_id, objects.ra, objects.dec, objects.type, mentions.simbad_id, objects.constellation, objects.aliases, COALESCE(display_id, mentions.simbad_id) as display_id from mentions
inner join queries on  queries.simbad_id = mentions.simbad_id
inner join objects on queries.main_id = objects.main_id
inner join reachability on reachability.filename = mentions.filename
where reachability.reachable = 1 and mentions.simbad_id not like "HD %" and mentions.simbad_id not like "SAO %"
"""

if len(exclude) > 0:
    query += "and mentions.filename not in (\"" + '", "'.join(exclude) + "\")"

query += "order by constellation, objects.main_id, mentions.display_id"

data = {} # {constellation: {main_id: {simbad_ids: {...}, display_ids: [...], aliases: [...], type: ..., ra: ..., dec: ...}}}
for filename, main_id, ra, dec, type_, simbad_id, constellation, aliases, display_id in cursor.execute(query):
    main_id_dict = data.setdefault(constellation, {}).setdefault(main_id, {})
    main_id_dict.setdefault('simbad_ids', set()).add(simbad_id)
    main_id_dict.setdefault('display_ids', {}).setdefault(display_id, []).append(filename)
    main_id_dict.setdefault('aliases', []).extend(json.loads(aliases) if aliases else [])
    main_id_dict['type'] = type_
    main_id_dict['ra'] = ra
    main_id_dict['dec'] = dec

for objects in data.values():
    for main_id_dict in objects.values():
        # Resolve winning ID
        winning_id = None
        valid_ids = set()
        for display_id in main_id_dict['display_ids']:
            if re.match(r'^[A-Z][A-Za-z]+.*|^[MB] ?[0-9]+$|^[MKZ] ?[0-9]+-[0-9]+[A-Za-z]$|^[IV] ?Zw ?[0-9]+$', display_id):
                if winning_id is None:
                    winning_id = display_id
                valid_ids.add(winning_id)
        for simbad_id in main_id_dict['simbad_ids']:
            obj_lcase = simbad_id.lower()
            for prefix, desimbad in desimbadification.items():
                if obj_lcase.startswith(prefix.lower()):
                    simbad_id = desimbad + obj_lcase[len(prefix):]
            if winning_id is None:
                winning_id = simbad_id
            valid_ids.add(simbad_id)
        for alias in main_id_dict['aliases']:
            if (not alias.startswith('2MASX')) and (not alias.startswith('2MASS')) and (not alias.startswith('SDSS ')) and (not alias.startswith('SDSSJ')):
                valid_ids.add(alias)

        main_id_dict['valid_ids'] = valid_ids
        main_id_dict['display_id'] = winning_id # Note: singular, not plural
        main_id_dict['simbad_id'] = sorted(main_id_dict['simbad_ids'])[0] # Note: singular, pick any
        main_id_dict['filenames'] = sorted({fn for fns in main_id_dict['display_ids'].values() for fn in fns}, key=lambda fn: article_titles[fn])

parents = {
    filename: parent
    for filename, parent in cursor.execute("select filename, parent from reachability where reachable = 1")
}

component_matcher = re.compile(r'\b(?:Rose|[R77]|HCG|VV|KTG|K77|Hickson) ?[0-9]+[a-f]\b', re.IGNORECASE)

def popularity_score(obj: dict) -> float:
    count_or = 0
    count_article = 0
    for fn in obj['filenames']:
        if parents[fn] == 'observing.reports.htm':
            count_or += 1
            continue
        match =  COMPILED_OBJECT_REGEX.search(article_titles[fn])
        if match:
            all_ids = {
                _id.replace(' ', '') for _id in
                set(obj['valid_ids']) | set(obj['display_ids']) | {obj['simbad_id'],}
            }
            if match.group().replace(' ', '') not in all_ids:
                count_article -= 0.5
        count_article += 1
    score = count_article + count_or/2.0
    if component_matcher.match(obj['display_id']):
        score -= 0.5
    return -score


with open('../docs/dso_index_constellation.md', 'w') as output:
    output.write(
"""---
layout: bigtable
title: Deep Sky Object Index
author: Deep-Sky Adventurers
open_new_page: false
disable_dso: true
---

<style>
td { word-wrap: break-word; }
</style>

This is an index of all objects featured in Adventures in Deep Space pages (including articles and observing reports), organized by constellation. The Deep-Sky Forum objects of the week are excluded, which have their own [index](/dsf_ootw_constellation.html). [Steve Gottlieb's NGC/IC/UGC logs](/steve.ngc.htm) are also excluded since it is exhaustive.

The data including aliases, object type classifications, and positions (used to compute constellation) ultimately comes from the <a href="https://simbad.u-strasbg.fr/">SIMBAD</a> Astronomical Database, or less-frequently from the <a href="https://ned.ipac.caltech.edu/">NASA Extragalactic Database (NED)</a>. Some type abbreviations are translated to common parlance for your convenience. When the type abbreviations are as used on SIMBAD / NED, you can use <a href="https://simbad.cds.unistra.fr/guide/otypes.htx">the SIMBAD type page</a> or <a href="https://ned.ipac.caltech.edu/help/ui/nearposn-list_objecttypes?popup=1">the NED type page</a> for reference.

The objects within each constellation are sorted by a popularity score, calculated as (no. of article features) + ½(no. of observing report features) - ½(no. of articles with a different object name in the title) - ½(if object is a subcomponent of a compact group / interaction)

If you'd like to help improve this feature, please submit an MR on the <a href='https://github.com/kstar/adventures.github.io'>github repo</a>. Hope you find it useful!<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp; - Akarsh Simha


""")

    # Write constellation index
    count = 0
    output.write('## Index\n\n')
    output.write(make_constellation_map(data.keys()))
    # for con in sorted(data):
    #     if count != 0 and count % 11 == 0:
    #         output.write('|\n')
    #     try:
    #         output.write(f'|[{con}](#{CONSTELLATIONS[con.upper()].lower().replace(" ", "-")} "{CONSTELLATIONS[con.upper()]}")')
    #     except KeyError:
    #         raise RuntimeError(f'Invalid constellation `{con}`')
    #     count += 1
    # while count % 11 != 0:
    #     output.write('|&nbsp;')
    #     count += 1
    # output.write('|\n')

    output.write('\n\n---\n\n')

    def remove_ads_prefix(article_title: str) -> str:
        if article_title.lower().startswith("adventures in deep space: "):
            return article_title[26:]
        return article_title

    def truncate_article_title(article_title: str) -> str:
        TRUNCATE_LIMIT = 40
        if len(article_title) > TRUNCATE_LIMIT:
            return article_title[:(TRUNCATE_LIMIT - 2)] + '…'
        return article_title

    make_article_entry = lambda filename: f'<li class="index_article"><a href="/' + filename.replace('.md', '.html') + f'" class="index_article">{truncate_article_title(remove_ads_prefix(article_titles[filename]))}</a></li>'


    for constellation in sorted(data):
        objects = data[constellation]
        output.write(f'## {CONSTELLATIONS[constellation.upper()]}\n\n')
        output.write('\n'.join([
            f'<table class="constellation_index" id="{constellation}">',
            f'<thead><tr><th>Object</th><th>Also known as</th><th><a href="https://simbad.cds.unistra.fr/guide/otypes.htx">Type</a></th><th>Featured in</th></tr></thead>',
            f'<tbody>',
        ]))
        for main_id in sorted(objects.keys(), key=lambda k: (popularity_score(objects[k]), objects[k]['display_id'])):
            main_id_dict = objects[main_id]
            simbad_id = main_id_dict['simbad_id']
            display_id = main_id_dict['display_id']
            valid_ids = set(main_id_dict['valid_ids'])
            valid_ids.discard(display_id)
            valid_ids = ', '.join(sorted(valid_ids))
            type_ = main_id_dict['type']
            type_ = SIMBAD_OTYPE.get(type_, type_)
            articles = ['<ul>']
            article_files = main_id_dict['filenames']
            articles += [make_article_entry(article_file) for article_file in article_files[:ARTICLES_COLLAPSE_LIMIT]]
            if len(article_files) == ARTICLES_COLLAPSE_LIMIT + 1:
                articles += [make_article_entry(article_files[-1]),]
            elif len(article_files) > ARTICLES_COLLAPSE_LIMIT:
                articles += ['<details>', f'<summary>{len(article_files) - ARTICLES_COLLAPSE_LIMIT} more...</summary>'] + [make_article_entry(article_file) for article_file in article_files[ARTICLES_COLLAPSE_LIMIT:]] + ['</details>']
            articles += ['</ul>']
            articles = ' '.join(articles)
            output.write(f'<tr><td><x-dso-link simbad="{simbad_id}" data-ra="{ra}" data-dec="{dec}">{display_id}</x-dso-link></td><td>{valid_ids}</td><td>{type_}</td><td style="min-width: 35%">{articles}</td></tr>' + '\n')
        output.write('\n</tbody>\n</table>')
        output.write('\n\n[▲ Index](#index){:.top}\n\n---\n\n')

    output.write('\n{% raw %}\n<br />\n<div style="text-align: right; margin-right: 10px;">\nLast updated: ' + datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '\n</div>\n{% endraw %}\n\n----\n')



