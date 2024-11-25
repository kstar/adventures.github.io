#!/usr/bin/env python3
"""
Finds DSO identifiers and wraps them in <x-dso> tags, translating into SIMBADese if appropriate
"""
import re
import sys
import argparse
from collections import OrderedDict
from common import COMPILED_OBJECT_REGEX, COMPILED_REPLACEMENT_REGEX

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
    ('k ', 'PN K '),
    ('Cederblad', 'Ced'),
])

class Replacer:
    """
    A regex replacer function object that wraps DSO identifiers with <x-dso> etc. tags

    Example usage:
    ```
    replacer = Replacer()
    COMPILED_REPLACEMENT_REGEX.sub(replacer, haystack)
    ```

    The above will replace the first occurrence of every DSO identifier in the string `haystack`,

    i.e. "NGC 591" -> "<x-dso>NGC 591</x-dso>"

    If `tag='x-dso-link'` is passed to the constructor instead, it will replace

    "NGC 591" -> "<x-dso-link>NGC 591</x-dso-link>"

    The regex provided must pick out the identifiers you want to tag. The replacer function only applies the translation table for SIMBAD.
    """
    def __init__(self, unique=True, tag='x-dso'):
        """
        unique: if set to True, only the first occurrence of a given identifier is tagged
        """
        super().__init__()
        self._unique_matches = set()
        self._unique = unique
        self._tag = tag

    def __call__(self, match):
        section = match.group(0)
        if section.startswith('='):
            # Alternate designation, do not tag but include for duplicates
            self._unique_matches.add(match.group(1))
            return section

        match_text = match.group(1)
        if not match_text:
            assert section.startswith('<x-dso'), f'Programming error. Match text {match_text}'
            for submatches in COMPILED_OBJECT_REGEX.finditer(section):
                submatch = submatches.group(1)
                assert submatch, f'{submatch}'
                self._unique_matches.add(submatch)
                print(f'*** Added {submatch} to unique_matches which now contains {self._unique_matches}', file=sys.stderr)
            return section
            
        if match_text and (match_text not in self._unique_matches or (not self._unique)):
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
                return f'<{self._tag} simbad="{simbadese}">{match_text}</{self._tag}>'
            return f'<{self._tag}>{match_text}</{self._tag}>'
        return match.group(0)

def main():
    replacer = Replacer()
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Perform the substitution in-place on file. If no file is provided, the input is read from stdin and output written to stdout', required=False, default=None)
    args = parser.parse_args()
    if args.file is not None:
        with open(args.file, 'r') as f:
            data = f.read()
    else:
        data = sys.stdin.read()

    data = COMPILED_REPLACEMENT_REGEX.sub(replacer, data)

    if args.file is not None:
        with open(args.file, 'w') as f:
            f.write(data)
    else:
        sys.stdout.write(data)

if __name__ == "__main__":
    main()
