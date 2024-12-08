# Copyright (c) 2024 Akarsh Simha <akarsh@kde.org>
# SPDX-License-Identifier: MIT
import re
from collections import OrderedDict

CATALOG_REGEXES = [ # FIXME: Handle `ESO 456-SC38` / `ESO 597-G36`
    r'\b(?:NGC|IC|UGC) ?[0-9]+ ??[A-Za-z]?\b', # ABCs
    r'\b(?:VV|Hickson|HCG|KTG|KPG) ?[0-9]+?[A-Za-z]?\b', # Components
    r'\bESO ?[0-9]+-(?:SC|G|N)?[0-9]+\b', # ESO
    r'\b(?:K|PK|PNG|CGCG|MCG|IRAS)[+\- ][0-9\.+\-]+\b', # Hyphenated / Coordinate-based
    r'\b(?:MCG)[+\- ][0-9\.+\-]+[A-Fa-f]?\b', # Hyphenated / Coordinate-based, MCG allows a/b/c
    r'\b(?:2MASS|2MASSX|SDSS|RCS|RCS2) J?[0-9\.]+[+-][0-9\.]+\b', # J2000 based
    r'\b[VIX]+ Zw [0-9]+\b', # Zwicky
    r'\b(?:Simeis|Sharpless|Sim|Cr|Collinder|Cederblad|Ced|HD|SAO|HIP|vdB|Mrk|Mailyan|VV|Trumpler|Tr|Arp|Abell|PN A66|ACO|AGC|PGC|LEDA|B|Barnard|HH|Messier|Rose) ?[0-9]+\b', # Simple catalogs
    r'\bRCG ?[0-9]{4}\b', # Another name for ACO? But could stand for Rose compact group, which is why we enforce 4-digits
    r'\bSh ?2[ -][0-9]+\b', # Sharpless
    r'\b(?:M|Min|Minkowski) [0-9]-[0-9]+\b', # Minkowksi
    r'\b(?:Pal|Palomar|Terzan) [0-9]{1,2}\b', # Palomar and Terzan
    r'\bM ?[0-9]{1,3}\b(?! *(?:[Ww]rench|[Bb]olt|[nN]ut|[tT]hread|[Ss]panner|[hH]ex|[aA]ll[ae]n)(?:[^-]+|$))', # Messier (and not referring to metric hardware)
]
OBJECT_REGEX = '(' + '|'.join(['(?:' + regex + ')' for regex in CATALOG_REGEXES]) + ')' # Matches an object designation in a capture group
COMPILED_OBJECT_REGEX = re.compile(OBJECT_REGEX)
REPLACEMENT_REGEX = r'<x-dso[^>]*>(?:(?!</x-dso>|</x-dso-link>).)*</x-dso(?:-link)?>|(?:= *)?' + OBJECT_REGEX # Matches any object designation that is not preceded by '=', '= ' or is placed immediately after an <x-dso> or <x-dso-link> tag
COMPILED_REPLACEMENT_REGEX = re.compile(REPLACEMENT_REGEX)

CONSTELLATIONS = {
    'AND': 'Andromeda',
    'ANT': 'Antlia',
    'APS': 'Apus',
    'AQL': 'Aquila',
    'AQR': 'Aquarius',
    'ARA': 'Ara',
    'ARI': 'Aries',
    'AUR': 'Auriga',
    'BOO': 'Boötes',
    'CAE': 'Caelum',
    'CAM': 'Camelopardalis',
    'CAP': 'Capricornus',
    'CAR': 'Carina',
    'CAS': 'Cassiopeia',
    'CEN': 'Centaurus',
    'CEP': 'Cepheus',
    'CET': 'Cetus',
    'CHA': 'Chameleon',
    'CIR': 'Circinus',
    'CMA': 'Canis Major',
    'CMI': 'Canis Minor',
    'CNC': 'Cancer',
    'COL': 'Columba',
    'COM': 'Coma Berenices',
    'CRA': 'Corona Australis',
    'CRB': 'Corona Borealis',
    'CRT': 'Crater',
    'CRU': 'Crux',
    'CRV': 'Corvus',
    'CVN': 'Canes Venatici',
    'CYG': 'Cygnus',
    'DEL': 'Delphinus',
    'DOR': 'Dorado',
    'DRA': 'Draco',
    'EQU': 'Equuleus',
    'ERI': 'Eridanus',
    'FOR': 'Fornax',
    'GEM': 'Gemini',
    'GRU': 'Grus',
    'HER': 'Hercules',
    'HOR': 'Horologium',
    'HYA': 'Hydra',
    'HYI': 'Hydrus',
    'IND': 'Indus',
    'LAC': 'Lacerta',
    'LEO': 'Leo',
    'LEP': 'Lepus',
    'LIB': 'Libra',
    'LMI': 'Leo Minor',
    'LUP': 'Lupus',
    'LYN': 'Lynx',
    'LYR': 'Lyra',
    'MEN': 'Mensa',
    'MIC': 'Microscopium',
    'MON': 'Monoceros',
    'MUS': 'Musca',
    'NOR': 'Norma',
    'OCT': 'Octans',
    'OPH': 'Ophiuchus',
    'ORI': 'Orion',
    'PAV': 'Pavo',
    'PEG': 'Pegasus',
    'PER': 'Perseus',
    'PHE': 'Phoenix',
    'PIC': 'Pictor',
    'PSA': 'Piscis Austrinus',
    'PSC': 'Pisces',
    'PUP': 'Puppis',
    'PYX': 'Pyxis',
    'RET': 'Reticulum',
    'SCL': 'Sculptor',
    'SCO': 'Scorpius',
    'SCT': 'Scutum',
    'SER': 'Serpens',
    'SEX': 'Sextans',
    'SGE': 'Sagitta',
    'SGR': 'Sagittarius',
    'TAU': 'Taurus',
    'TEL': 'Telescopium',
    'TRA': 'Triangulum Australe',
    'TRI': 'Triangulum',
    'TUC': 'Tucana',
    'UMA': 'Ursa Major',
    'UMI': 'Ursa Minor',
    'VEL': 'Vela',
    'VIR': 'Virgo',
    'VOL': 'Volans',
    'VUL': 'Vulpecula',
}

simbadification = OrderedDict([
    ('Collinder ', 'Cl Collinder '),
    ('simeis', 'Sim'),
    ('cgcg', 'Z'),
    ('agc', 'ACO'),
    ('minkowski 1-', 'PN M 1-'),
    ('minkowski 2-', 'PN M 2-'),
    ('minkowski 3-', 'PN M 3-'),
    ('minkowski 4-', 'PN M 4-'),
    ('minkowksi', 'Min'),
    ('m 1-', 'PN M 1-'),
    ('m 2-', 'PN M 2-'),
    ('b ', 'Barnard '),
    ('cr ', 'Collinder '),
    ('sh2 ', 'Sh2-'),
    ('sharpless ', 'Sh2-'),
    ('KTG', 'K79'),
    ('Hickson', 'HCG'),
    ('k ', 'PN K '),
    ('Cederblad', 'Ced'),
    ('RCG', 'ACO'),
    ('Rose ', '[R77] '),
])

desimbadification = OrderedDict([
    ('PN A66 ', 'Abell PN '),
    ('ACO ', 'Abell '),
    ('PN M ', 'Minkowski '),
    ('K79 ', 'KTG '),
    ('Cl ', ''),
    ('Sim ', 'Simeis '),
    ('Sh2', 'Sh 2'),
    ('SKHB ', 'M31-G'),
    ('Z ', 'CGCG '),
    ('[R77] ', 'Rose '),
])
