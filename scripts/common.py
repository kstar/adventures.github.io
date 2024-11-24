# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
# SPDX-License-Identifier: MIT
import re

CATALOG_REGEXES = [
    r'\b(?:NGC|IC|UGC) ?[0-9]+ ??[A-Za-z]?\b', # ABCs
    r'\b(?:VV|Hickson|HCG|KTG|KPG) ?[0-9]+?[A-Za-z]?\b', # Components
    r'\b(?:K|PK|PNG|CGCG|MCG|ESO|IRAS)[+\- ][0-9\.+\-]+\b', # Hyphenated / Coordinate-based
    r'\b(?:2MASS|2MASSX|SDSS|RCS|RCS2) J?[0-9\.]+[+-][0-9\.]+\b', # J2000 based
    r'\b[VIX]+ Zw [0-9]+\b', # Zwicky
    r'\b(?:Simeis|Sharpless|Sim|Cr|Collinder|Cederblad|Ced|HD|SAO|HIP|vdB|Mrk|Mailyan|VV|Trumpler|Tr|Arp|Abell|PN A66|ACO|AGC|PGC|LEDA|B|Barnard|HH|Messier) ?[0-9]+\b', # Simple catalogs
    r'\bSh ?2[ -][0-9]+\b', # Sharpless
    r'\b(?:M|Min|Minkowski) [0-9]-[0-9]+\b', # Minkowksi
    r'\b(?:Pal|Palomar|Terzan) [0-9]{1,2}\b', # Palomar and Terzan
    r'\bM ?[0-9]{1,3}\b(?! *(?:[Ww]rench|[Bb]olt|[nN]ut|[tT]hread|[Ss]panner|[hH]ex|[aA]ll[ae]n)(?:[^-]+|$))', # Messier (and not referring to metric hardware)
]
OBJECT_REGEX = '(' + '|'.join(['(?:' + regex + ')' for regex in CATALOG_REGEXES]) + ')' # Matches an object designation in a capture group
COMPILED_OBJECT_REGEX = re.compile(OBJECT_REGEX)
REPLACEMENT_REGEX = r'<x-dso[^>]*>(?:(?!</x-dso>|</x-dso-link>).)*</x-dso(?:-link)?>|(?:= *)?' + OBJECT_REGEX # Matches any object designation that is not preceded by '=', '= ' or is placed immediately after an <x-dso> or <x-dso-link> tag
COMPILED_REPLACEMENT_REGEX = re.compile(REPLACEMENT_REGEX)
