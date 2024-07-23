#!/usr/bin/env python3
"""
Finds DSO identifiers and wraps them in <x-dso> tags, translating into SIMBADese if appropriate
"""
import re
import sys
from collections import OrderedDict

CATALOG_REGEXES = [
    r'\b(?:NGC|IC|UGC) ?[0-9]+ ??[A-Za-z]?\b', # ABCs
    r'\b(?:VV|Hickson|HCG|KTG|KPG) ?[0-9]+?[A-Za-z]?\b', # Components
    r'\b(?:K|PK|PNG|CGCG|MCG|ESO|IRAS)[+\- ][0-9\.+\-]+\b', # Hyphenated / Coordinate-based
    r'\b(?:2MASS|2MASSX|SDSS|RCS|RCS2) J?[0-9\.]+[+-][0-9\.]+\b', # J2000 based
    r'\b[VIX]+ Zw [0-9]+\b', # Zwicky
    r'\b(?:Simeis|Sharpless|Sim|Cr|Collinder|Cederblad|Ced|HD|SAO|HIP|vdB|Mrk|Mailyan|VV|Trumpler|Tr|Arp|Abell|PN A66|ACO|AGC|PGC|LEDA|B|Barnard|HH|Messier) ?[0-9]+\b', # Simple catalogs
    r'\bSh2[ -][0-9]+\b', # Sharpless
    r'\b(?:M|Min|Minkowski) [0-9]-[0-9]+\b', # Minkowksi
    r'\b(?:Pal|Palomar) [0-9]{1,2}\b', # Palomar
    r'\bM ?[0-9]{1,3}\b(?! *(?:[Ww]rench|[Bb]olt|[nN]ut|[tT]hread|[Ss]panner|[hH]ex|[aA]ll[ae]n)(?:[^-]+|$))', # Messier (and not referring to metric hardware)
]
OBJECT_REGEX = '(?<!= )(?<!=)(' + '|'.join(['(?:' + regex + ')' for regex in CATALOG_REGEXES]) + ')'
COMPILED_OBJECT_REGEX = re.compile(OBJECT_REGEX)

simbadification = OrderedDict([
    ('simeis', 'Sim'),
    ('cgcg', 'Z'),
    ('agc', 'ACO'),
    ('minkowski 2-', 'PN M 2-'),
    ('minkowksi', 'Min'),
    ('m 1-', 'Min 1-'),
    ('m 2-', 'PN M 2-'),
    ('b ', 'Barnard '),
    ('cr ', 'Collinder '),
    ('sh2 ', 'Sh2-'),
    ('sharpless ', 'Sh2-'),
    ('KTG', 'K79'),
    ('Hickson', 'HCG'),
])

class Replacer:
    """
    A regex replacer function object that wraps DSO identifiers with <x-dso> tags

    Example usage:
    ```
    replacer = Replacer()
    COMPILED_OBJECT_REGEX.sub(replacer, haystack)
    ```

    The above will replace the first occurrence of every DSO identifier in the string `haystack`,

    i.e. "NGC 591" -> "<x-dso>NGC 591</x-dso>"

    The regex provided must pick out the identifiers you want to tag. The replacer function only applies the translation table for SIMBAD.
    """
    def __init__(self, unique=True):
        """
        unique: if set to True, only the first occurrence of a given identifier is tagged
        """
        super().__init__()
        self._unique_matches = set()
        self._unique = unique

    def __call__(self, match):
        match_text = match.group(0)
        if (match_text not in self._unique_matches) or (not self._unique):
            self._unique_matches.add(match_text)

            simbadese = None
            obj_lcase = match_text.lower()
            if obj_lcase.startswith('abell '):
                try:
                    num = int(re.match(r'abell ([0-9]+)', obj_lcase).groups()[0])
                except:
                    pass
                else:
                    if num <= 86:
                        # Assume PN
                        simbadese = f'PN A66 {num}'
            else:
                for key, value in simbadification.items():
                    if obj_lcase.startswith(key.lower()):
                        simbadese = value + obj_lcase[len(key):]
            if simbadese:
                return f'<x-dso simbad="{simbadese}">{match_text}</x-dso>'
            return f'<x-dso>{match_text}</x-dso>'
        return match_text

if __name__ == "__main__":
    replacer = Replacer()
    sys.stdout.write(COMPILED_OBJECT_REGEX.sub(replacer, sys.stdin.read()))

