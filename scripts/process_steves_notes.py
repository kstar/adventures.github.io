#!/usr/bin/env python3
"""
Process Steve Gottlieb's NGC/IC/UGC observation notes into HTML pages.

Reads plain text notes from docs/assets/{catalog}_notes.txt and generates:
- Clean HTML pages split by 1000 objects (NGC0.html, IC0.html, etc.)
- A single UGC.html page for all UGC objects
- Redirect pages from old filenames to new ones
"""

import re
import os
import html
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_FOLDER = os.path.join(SCRIPT_DIR, "..", "docs")

CATALOGS = ("ngc", "ic", "ugc")
# Catalogs that get split into 1000-object pages; others become a single page
SPLIT_CATALOGS = ("ngc", "ic")
MAX = {"ngc": 7840, "ic": 5386, "ugc": 12915}

OBJ_REGEX = re.compile(r"^(NGC|IC|UGC) ([0-9]+)\b")
SEPARATOR_REGEX = re.compile(r"^\*{10,}$")


def get_page_index(number: int) -> int:
    return (number - 1) // 1000


def get_filename(catalog: str, page_index: int = 0) -> str:
    cat = catalog.upper()
    if catalog not in SPLIT_CATALOGS:
        return f"{cat}.html"
    return f"{cat}{page_index}.html"


def get_page_title(catalog: str, page_index: int = 0) -> str:
    cat = catalog.upper()
    if catalog not in SPLIT_CATALOGS:
        return f"Steve Gottlieb's {cat} Notes"
    start = page_index * 1000 + 1
    end = min(start + 999, MAX[catalog])
    return f"Steve Gottlieb's {cat} Notes &mdash; {cat} {start}\u2013{end}"


# Build complete page sequence for prev/next navigation
ALL_PAGES: list[str] = []
for _cat in CATALOGS:
    if _cat in SPLIT_CATALOGS:
        max_page = get_page_index(MAX[_cat])
        for _i in range(max_page + 1):
            ALL_PAGES.append(get_filename(_cat, _i))
    else:
        ALL_PAGES.append(get_filename(_cat))

PAGE_INDEX_MAP = {page: idx for idx, page in enumerate(ALL_PAGES)}


def get_nav_links(filename: str) -> tuple[str | None, str | None]:
    idx = PAGE_INDEX_MAP[filename]
    prev_page = ALL_PAGES[idx - 1] if idx > 0 else None
    next_page = ALL_PAGES[idx + 1] if idx < len(ALL_PAGES) - 1 else None
    return prev_page, next_page


# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

PREAMBLE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="assets/common.css?version=8" />
<script type="text/javascript" src="assets/common.js?version=4"></script>
<script type="text/javascript">document.disableCSVMaker = true; document.disableDSO = true;</script>
<title>{title}</title>
<link rel="stylesheet" href="assets/steve_notes.css?version=0" />
</head>
<body>
<center><h1>{title}</h1></center>
"""


def nav_bar_html(prev_page: str | None, next_page: str | None) -> str:
    if prev_page:
        prev_link = f'<a href="{prev_page}">\u25c0 Prev Page</a>'
    else:
        prev_link = '<span class="disabled">\u25c0 Prev Page</span>'

    if next_page:
        next_link = f'<a href="{next_page}">Next Page \u25b6</a>'
    else:
        next_link = '<span class="disabled">Next Page \u25b6</span>'

    return f"""\
<script src="assets/steve_search.js?version=0"></script>
<nav class="sticky-nav">
  <select id="nav-catalog">
    <option value="NGC">NGC</option>
    <option value="IC">IC</option>
    <option value="UGC">UGC</option>
  </select>
  <input type="text" id="nav-object" placeholder="e.g. 891" />
  <button type="button" onclick="steveSearchGo('nav-catalog', 'nav-object')">Go</button>
  <span class="sep">|</span>
  {prev_link}
  <span class="sep">|</span>
  <a href="steve.ngc.htm#catalog-table">Index</a>
  <span class="sep">|</span>
  {next_link}
</nav>
<script>
document.getElementById('nav-object').addEventListener('keyup', function(e) {{
  if (e.keyCode === 13) {{ e.preventDefault(); steveSearchGo('nav-catalog', 'nav-object'); }}
}});
</script>
"""


POSTAMBLE = """\
</body>
</html>
"""

REDIRECT_TEMPLATE = """\
<!DOCTYPE html>
<html><head>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<title>Moved</title>
</head><body>
<p>This page has permanently moved to <a href="{target}">{target}</a>.</p>
</body></html>
"""


def process_catalog(catalog: str) -> None:
    """Read a catalog's notes file and write out HTML pages."""
    path = os.path.join(DOCS_FOLDER, "assets", f"{catalog}_notes.txt")
    split = catalog in SPLIT_CATALOGS

    with open(path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # pages[page_index] = list of HTML fragments
    # For single-page catalogs, everything goes into page 0
    pages: dict[int, list[str]] = {}
    current_page: int | None = None

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        # Separator between objects
        if SEPARATOR_REGEX.match(line.strip()):
            if current_page is not None:
                pages.setdefault(current_page, []).append(
                    '<hr class="dso-separator"/>\n'
                )
            continue

        # Blank line — skip (paragraph spacing from <p> margins)
        if len(line.strip()) == 0:
            continue

        # Check for new object header (only match the catalog being processed)
        obj_match = OBJ_REGEX.match(line)
        if obj_match and obj_match.group(1) == catalog.upper():
            cat_name = obj_match.group(1)
            number = int(obj_match.group(2))
            current_page = get_page_index(number) if split else 0
            obj_id = f"{cat_name} {number}"

            escaped_rest = html.escape(line[len(obj_id) :])
            markup = (
                f'<a name="{html.escape(obj_id)}" class="dso-anchor"></a>'
                f"<x-dso>{html.escape(obj_id)}</x-dso>"
                f"{escaped_rest}"
            )
            pages.setdefault(current_page, []).append(f"<p>{markup}</p>\n")
            logger.info(f"Object: {obj_id}")
        else:
            if current_page is not None:
                pages.setdefault(current_page, []).append(
                    f"<p>{html.escape(line)}</p>\n"
                )

    # Write each page
    for page_index in sorted(pages.keys()):
        filename = get_filename(catalog, page_index)
        filepath = os.path.join(DOCS_FOLDER, filename)
        title = get_page_title(catalog, page_index)
        prev_page, next_page = get_nav_links(filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(PREAMBLE.format(title=title))
            for fragment in pages[page_index]:
                f.write(fragment)
            f.write(nav_bar_html(prev_page, next_page))
            f.write(POSTAMBLE)

        logger.info(f"Wrote {filepath}")


def generate_redirects() -> None:
    """Generate redirect pages from old filenames to new ones."""
    redirects: dict[str, str] = {}

    # NGC: old "NGC start-end.html" naming
    for i in range(get_page_index(MAX["ngc"]) + 1):
        target = get_filename("ngc", i)
        start = i * 1000 + 1
        end = min(start + 999, MAX["ngc"])
        redirects[f"NGC {start}-{end}.html"] = target

        # Zero-padded / alternate-range variants that exist in the repo
        if i == 0:
            redirects["NGC 0001-999.html"] = target
            redirects["NGC 0001-1000.htm"] = target
        else:
            alt_start = i * 1000
            alt_end = alt_start + 999
            if alt_end > MAX["ngc"]:
                alt_end = MAX["ngc"]
            redirects[f"NGC {alt_start}-{alt_end}.html"] = target

    redirects["NGC complete.html"] = get_filename("ngc", 0)

    # IC: old "IC start thru IC end.html" naming
    for i in range(get_page_index(MAX["ic"]) + 1):
        target = get_filename("ic", i)
        start = i * 1000 + 1
        end = min(start + 999, MAX["ic"])
        redirects[f"IC {start} thru IC {end}.html"] = target

    redirects["IC 1-5386 complete.html"] = get_filename("ic", 0)

    # UGC: old split "UGC 00001-01000.html" naming → single UGC.html
    target = get_filename("ugc")
    for i in range(get_page_index(MAX["ugc"]) + 1):
        start = i * 1000 + 1
        end = min(start + 999, MAX["ugc"])
        redirects[f"UGC {start:05d}-{end:05d}.html"] = target

    # Write redirect files
    for old_name, target in redirects.items():
        filepath = os.path.join(DOCS_FOLDER, old_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(REDIRECT_TEMPLATE.format(target=target))
        logger.info(f"Redirect: {old_name} -> {target}")


def main() -> None:
    for catalog in CATALOGS:
        process_catalog(catalog)
    generate_redirects()


if __name__ == "__main__":
    main()
