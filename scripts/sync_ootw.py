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

escape_regex = re.compile(r'[_{\*`\(\)}]|---+')

def markdown_escape(s: str) -> str:
    io = StringIO()
    i = 0
    j = 0
    for match in escape_regex.finditer(s):
        j = match.start()
        io.write(s[i:j] + '\\')
        i = j
    io.write(s[j:])

    return io.getvalue()

try:
    sheet_id = os.environ['DSF_OOTW_GOOGLE_SHEET_ID']
except KeyError as e:
    raise RuntimeError(f'You must export `DSF_OOTW_GOOGLE_SHEET_ID` to the spreadsheet ID of Wouter van Reeven\'s "All Objects of the Week" spreadsheet.')

output_path = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'), 'docs')
output_filename = 'dsf_ootw.md'


csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
print(f'CSV URL: {csv_url}')
data = requests.get(csv_url)
content = data.content.decode('utf-8')
read_header = False
replacer = regex.Replacer()
REGEX = r'(?<!\()(?<!\(\s)' + regex.OBJECT_REGEX
COMPILED_REGEX = re.compile(REGEX)

with open(os.path.join(output_path, output_filename), 'w') as output:
    output.write( # Front matter and posting
    """---
layout: default
title: Deep-Sky Forum Object of the Week
author: DSF OOTW team; compiled by Wouter van Reeven.
---

Every Sunday, one of several experienced visual deep-sky observers posts an "[Object of the Week](https://www.deepskyforum.com/forumdisplay.php?8-Object-of-the-Week-2024-(OOTW))" on the [Deep Sky Forum](https://www.deepskyforum.com). This page is a full listing of all OOTW posts. The list was created by Wouter van Reeven and brought into Adventures in Deep Space by Akarsh Simha. DeepSkyForum is run by Dragan Nikin and Jimi Lowrey.

{% raw %}
<script type="text/javascript">
document.disableCSVMaker = true;
document.disableDSO = true;
// Add _target = "blank" to all links so that they open in a new page/window
{
let _existingOnload = window.onload;
window.onload = function() {
// Call the existing onload function if it exists
if (typeof _existingOnload === 'function') {
_existingOnload();
}
// Add target="_blank" to links
document.querySelectorAll('a').forEach((anchor_tag) =>{anchor_tag.target = "_blank";});
}
}
</script>
{% endraw %}
""")

    for row in csv.reader(content.splitlines(), delimiter=','):
        if not read_header:
            # Header row
            read_header = True
            output.write('|' + '|'.join(row[:4]) + '|\n')
            output.write(''.join(['| ---- ']*4) + '|\n')
            continue
        if len(row[4]) == 0: # Blank entry
            continue
        row = list(map(markdown_escape, row[:4])) + [row[4],]

        parts = row[4].split('?')
        url = '?'.join([parts[0],] + list(map(urlencode, parts[1:])))

        output.write(f'|{row[0]}|{row[1]}|[{row[2]}]({url})|' + COMPILED_REGEX.sub(replacer, row[3]) + '|\n')

    output.write('\n{% raw %}\n<br />\n<div style="text-align: right; margin-right: 10px;">\nLast updated: ' + datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '\n</div>\n{% endraw %}\n\n----\n')
    
