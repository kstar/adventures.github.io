#!/usr/bin/env python3
#
# Copyright (c) Akarsh Simha 2024 <akarsh@kde.org>
# Licensed under MIT License

# NOTE: To protect the OOTW Google Sheet, the spreadsheet ID must be exported
# into the shell environment

import csv
import os
import apply_dso as regex
import requests
import re
from datetime import datetime, timezone
from io import StringIO
from urllib.parse import quote_plus as urlencode
from collections import namedtuple

ESCAPE_REGEX = re.compile(r'[_{\*`\(\)}]|---+')

def markdown_escape(s: str) -> str:
    io = StringIO()
    i = 0
    j = 0
    for match in ESCAPE_REGEX.finditer(s):
        j = match.start()
        io.write(s[i:j] + '\\')
        i = j
    io.write(s[j:])

    return io.getvalue()

SHEET_ID = '1uyXGm2SjtR-fJmHgD5yqkXok4wAPgjx8tWWhRekq7B4'

REGEX = r'(?<!\()(?<!\(\s)' + regex.OBJECT_REGEX
COMPILED_REGEX = re.compile(REGEX)

CONSTELLATIONS = {
    'And': 'Andromeda',
    'Ant': 'Antlia',
    'Aps': 'Apus',
    'Aql': 'Aquila',
    'Aqr': 'Aquarius',
    'Ara': 'Ara',
    'Ari': 'Aries',
    'Aur': 'Auriga',
    'Boo': 'Böotes',
    'Cae': 'Caelum',
    'Cam': 'Camelopardalis',
    'Cap': 'Capricornus',
    'Car': 'Carina',
    'Cas': 'Cassiopeia',
    'Cen': 'Centaurus',
    'Cep': 'Cepheus',
    'Cet': 'Cetus',
    'Cha': 'Chameleon',
    'Cir': 'Circinus',
    'CMa': 'Canis Major',
    'CMi': 'Canis Minor',
    'Cnc': 'Cancer',
    'Col': 'Columba',
    'Com': 'Coma Berenices',
    'CrA': 'Corona Australis',
    'CrB': 'Corona Borealis',
    'Crt': 'Crater',
    'Cru': 'Crux',
    'Crv': 'Corvus',
    'CVn': 'Canes Venatici',
    'Cyg': 'Cygnus',
    'Del': 'Delphinus',
    'Dor': 'Dorado',
    'Dra': 'Draco',
    'Eql': 'Equuleus',
    'Eri': 'Eridanus',
    'For': 'Fornax',
    'Gem': 'Gemini',
    'Gru': 'Grus',
    'Her': 'Hercules',
    'Hor': 'Horologium',
    'Hya': 'Hydra',
    'Hyi': 'Hydrus',
    'Ind': 'Indus',
    'Lac': 'Lacerta',
    'Leo': 'Leo',
    'Lep': 'Lepus',
    'Lib': 'Libra',
    'LMi': 'Leo Minor',
    'Lup': 'Lupus',
    'Lyn': 'Lynx',
    'Lyr': 'Lyra',
    'Men': 'Mensa',
    'Mic': 'Microscopium',
    'Mon': 'Monoceros',
    'Mus': 'Musca',
    'Nor': 'Norma',
    'Oct': 'Octans',
    'Oph': 'Ophiuchus',
    'Ori': 'Orion',
    'Pav': 'Pavo',
    'Peg': 'Pegasus',
    'Per': 'Perseus',
    'Phe': 'Phoenix',
    'Pic': 'Pictor',
    'PsA': 'Piscis Austrinus',
    'Psc': 'Pisces',
    'Pup': 'Puppis',
    'Pyx': 'Pyxis',
    'Ret': 'Reticulum',
    'Scl': 'Sculptor',
    'Sco': 'Scorpius',
    'Sct': 'Scutum',
    'Ser': 'Serpens',
    'Sex': 'Sextans',
    'Sge': 'Sagitta',
    'Sgr': 'Sagittarius',
    'Tau': 'Taurus',
    'Tel': 'Telescopium',
    'TrA': 'Triangulum Australe',
    'Tri': 'Triangulum',
    'Tuc': 'Tucana',
    'UMa': 'Ursa Major',
    'UMi': 'Ursa Minor',
    'Vel': 'Vela',
    'Vir': 'Virgo',
    'Vol': 'Volans',
    'Vul': 'Vulpecula',
}

OOTWRow = namedtuple('OOTWRow', [
    'date',    # Date string of the OOTW
    'author',  # Author's name
    'title',   # Title of OOTW post
    'objects', # Free-form string containing objects mentioned in the post
    'url',     # URL to the DSF OOTW post
    'ignore',  # Unused
    'primary', # Primary object's designation (usually SIMBAD-friendly)
    'ra',      # RA, sexagesimal hours (J2000)
    'dec',     # Dec, sexagesimal degrees (J2000)
    'constellation', # 3-letter IAU abbreviation of the constellation
    'type',    # Type code of object in SIMBAD
    'designations', # Designations output by SIMBAD
        ])

def map_on_spreadsheet_rows(function, markdown=True):
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    data = requests.get(csv_url)
    content = data.content.decode('utf-8')
    read_header = False

    for row in csv.reader(content.splitlines(), delimiter=','):
        if not read_header:
            # Header row
            read_header = True
            continue

        data = OOTWRow(*row)

        if data.url.strip(' \t') == '':
            continue # Ignore empty data

        # URL Encode the post title
        parts = data.url.split('?')
        url = '?'.join([parts[0],] + list(map(urlencode, parts[1:])))
        data._replace(url=url)

        if markdown:
            data._replace(title=markdown_escape(data.title))

        function(data)


def main():
    output_path = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'), 'docs')

    chronological = open(os.path.join(output_path, 'dsf_ootw.md'), 'w')
    chronological.write( # Front matter and posting
"""---
layout: bigtable
title: Deep-Sky Forum Object of the Week
author: DSF OOTW team; Wouter van Reeven; Akarsh Simha.
open_in_new_page: true
disable_dso: true
---

Every Sunday, one of several experienced visual deep-sky observers posts an "[Object of the Week](https://www.deepskyforum.com/forumdisplay.php?8-Object-of-the-Week-2024-(OOTW))" on the [Deep Sky Forum](https://www.deepskyforum.com). This page is a full listing of all OOTW posts, latest first. The list was compiled by Wouter van Reeven and imported into Adventures in Deep Space by Akarsh Simha. DeepSkyForum is run by Dragan Nikin and Jimi Lowrey.

To see the objects organized by constellation, click [here](dsf_ootw_constellation.html). To see this data as a spreadsheet, click [here](https://docs.google.com/spreadsheets/d/1uyXGm2SjtR-fJmHgD5yqkXok4wAPgjx8tWWhRekq7B4/).

""")

    constellation = open(os.path.join(output_path, 'dsf_ootw_constellation.md'), 'w')
    constellation.write( # Front matter and posting
"""---
layout: bigtable
title: Deep-Sky Forum Object of the Week (by Constellation)
author: DSF OOTW team; Wouter van Reeven; Akarsh Simha.
open_in_new_page: true
disable_dso: true
---

Every Sunday, one of several experienced visual deep-sky observers posts an "[Object of the Week](https://www.deepskyforum.com/forumdisplay.php?8-Object-of-the-Week-2024-(OOTW))" on the [Deep Sky Forum](https://www.deepskyforum.com). This page is a full listing of all OOTW posts, organized by constellation. The list was compiled by Wouter van Reeven and imported into Adventures in Deep Space by Akarsh Simha. DeepSkyForum is run by Dragan Nikin and Jimi Lowrey.

To see the objects organized by chronology, click [here](dsf_ootw.html). To see this data as a spreadsheet, click [here](https://docs.google.com/spreadsheets/d/1uyXGm2SjtR-fJmHgD5yqkXok4wAPgjx8tWWhRekq7B4/).

""")

    replacer = regex.Replacer(tag='x-dso-link')
    rows = []
    rows_by_constellation = {}

    def process_row(data):
        c = data.constellation.upper()
        rows_by_constellation.setdefault(c, []).append(len(rows))
        rows.append(f'|{data.date}|[{data.title}]({data.url})|{data.author}|{COMPILED_REGEX.sub(replacer, data.objects.strip(" "))}|{c}|\n')

    map_on_spreadsheet_rows(process_row)

    header = '|Date|Title|Author|Object(s)|Constellation|'
    header += '\n' + ''.join(['|----',] * header.count('|')) + '|\n'
    chronological.write(header)
    for row in rows[::-1]:
        chronological.write(row)
    chronological.write('\n{% raw %}\n<br />\n<div style="text-align: right; margin-right: 10px;">\nLast updated: ' + datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '\n</div>\n{% endraw %}\n\n----\n')

    count = 0
    constellation.write('## Index\n\n')
    for con in sorted(rows_by_constellation.keys()):
        if count != 0 and count % 11 == 0:
            constellation.write('|\n')
        constellation.write(f'|[{con}](#{con.lower()})')
        count += 1
    while count % 11 != 0:
        constellation.write('|&nbsp;')
        count += 1
    constellation.write('|\n')

    constellation.write('\n\n---\n\n')

    header = '|Date|Title|Author|Object(s)|'
    header += '\n' + ''.join(['|----',] * header.count('|')) + '|\n'
    for con, inds in rows_by_constellation.items():
        constellation.write(f'## {con}\n\n')
        constellation.write(header)
        for ind in inds[::-1]:
            raw_row = rows[ind].split('|')
            constellation.write('|'.join(raw_row[:-2] + raw_row[-1:]))
        constellation.write('\n\n[▲ Index](#index){:.top}\n\n---\n\n')
        
    constellation.write('\n{% raw %}\n<br />\n<div style="text-align: right; margin-right: 10px;">\nLast updated: ' + datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '\n</div>\n{% endraw %}\n\n----\n')
    chronological.close()
    constellation.close()

if __name__ == "__main__":
    main()
