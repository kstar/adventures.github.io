#!/usr/bin/env python
#
# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
# License: MIT License

import sqlite3
from datetime import datetime, timezone
import logging
import os
import re
from common import desimbadification, CONSTELLATIONS
from pathlib import Path

logger = logging.getLogger('build_dso_db')
logger.setLevel(logging.INFO)
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOC_DIRECTORY = SCRIPT_DIR / ".." / "docs"
DATABASE = SCRIPT_DIR / 'adventures.db'

conn = sqlite3.connect(DATABASE.as_posix())
cursor = conn.cursor()

article_titles = dict(cursor.execute("SELECT filename, title FROM articles").fetchall())

exclude = ["dsf_ootw.md", "dsf_ootw_constellation.md"]

query = """
SELECT mentions.filename, objects.main_id, objects.type, mentions.simbad_id, objects.constellation, COALESCE(display_id, mentions.simbad_id) as display_id from mentions
inner join queries on  queries.simbad_id = mentions.simbad_id
inner join objects on queries.main_id = objects.main_id
inner join reachability on reachability.filename = mentions.filename
where reachability.reachable = 1 and mentions.simbad_id not like "HD %" and mentions.simbad_id not like "SAO %"
"""

if len(exclude) > 0:
    query += "and mentions.filename not in (\"" + '", "'.join(exclude) + "\")"

query += "order by constellation, objects.main_id, mentions.display_id"

data = {}
for filename, main_id, type_, simbad_id, constellation, display_id in cursor.execute(query):
    main_id_dict = data.setdefault(constellation, {}).setdefault(main_id, {})
    main_id_dict.setdefault('simbad_ids', set()).add(simbad_id)
    main_id_dict.setdefault('display_ids', {}).setdefault(display_id, []).append(filename)
    main_id_dict['type'] = type_

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

        main_id_dict['valid_ids'] = valid_ids
        main_id_dict['display_id'] = winning_id # Note: singular, not plural
        main_id_dict['simbad_id'] = sorted(main_id_dict['simbad_ids'])[0] # Note: singular, pick any
        main_id_dict['filenames'] = sorted({fn for fns in main_id_dict['display_ids'].values() for fn in fns}, key=lambda fn: article_titles[fn])

with open('../docs/dso_index_constellation.md', 'w') as output:
    output.write(
"""---
layout: bigtable
title: Deep Sky Object Index
author: Deep-Sky Adventurers
open_new_page: false
disable_dso: true
---

This is an index of all objects featured in Adventures in Deep Space pages (including articles and observing reports), organized by constellation. The Deep-Sky Forum objects of the week are excluded, which have their own [index](/dsf_ootw_constellation.html). This feature is still in beta and there are many errors and issues with it. Hope you find it useful! - Akarsh Simha


""")

    # Write constellation index
    count = 0
    output.write('## Index\n\n')
    for con in sorted(data):
        if count != 0 and count % 11 == 0:
            output.write('|\n')
        try:
            output.write(f'|[{con}](#{CONSTELLATIONS[con.upper()].lower().replace(" ", "-")} "{CONSTELLATIONS[con.upper()]}")')
        except KeyError:
            raise RuntimeError(f'Invalid constellation `{con}`')
        count += 1
    while count % 11 != 0:
        output.write('|&nbsp;')
        count += 1
    output.write('|\n')

    output.write('\n\n---\n\n')


    for constellation in sorted(data):
        objects = data[constellation]
        output.write(f'## {CONSTELLATIONS[constellation.upper()]}\n\n')
        output.write('\n'.join([
            f'<table class="constellation_index" id="{constellation}">',
            f'<thead><tr><th>Object</th><th>Also known as</th><th>Type</th><th>Featured in</th></tr></thead>',
            f'<tbody>',
        ]))
        for main_id in sorted(objects.keys(), key=lambda k: (-len(objects[k]['filenames']), objects[k]['display_id'])):
            main_id_dict = objects[main_id]
            simbad_id = main_id_dict['simbad_id']
            display_id = main_id_dict['display_id']
            valid_ids = set(main_id_dict['valid_ids'])
            valid_ids.discard(display_id)
            valid_ids = ', '.join(sorted(valid_ids))
            type_ = main_id_dict['type']
            articles = '<ul>' + ' '.join([
                f'<li class="index_article"><a href="/' + filename.replace('.md', '.html') + f'" class="index_article">{article_titles[filename]}</a></li>'
                for filename in main_id_dict['filenames']
            ]) + '</ul>'
            output.write(f'<tr><td><x-dso-link simbad="{simbad_id}">{display_id}</x-dso-link></td><td>{valid_ids}</td><td>{type_}</td><td>{articles}</td></tr>' + '\n')
        output.write('\n</tbody>\n</table>')
        output.write('\n\n[▲ Index](#index){:.top}\n\n---\n\n')

    output.write('\n{% raw %}\n<br />\n<div style="text-align: right; margin-right: 10px;">\nLast updated: ' + datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '\n</div>\n{% endraw %}\n\n----\n')



