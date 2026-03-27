# Adding Observing Reports

This document provides instructions for both humans and AI agents to process new observing reports (ORs) from email (`.eml`) or Word (`.docx`) sources into the `docs/` folder of this repository.

## Prerequisites

- **Python 3 / uv**: Most scripts are Python-based and should be run using `uv run`.
- **Pandoc**: Required for Word document conversion.
- **ImageMagick (mogrify)**: Required for image compression.
- **Parallel**: Used by some shell scripts.

## Step 1: Initial Conversion

Place the source files in the `predocs/` folder (standard convention) and run the appropriate script from the repository root.

### From Email (.eml)
Use the `ingest_email.py` script. It extracts the HTML body, converts it to Markdown, and saves image attachments to `docs/assets/`.
```bash
uv run scripts/ingest_email.py predocs/your_report.eml
```

### From Word (.docx)
Use the `docx_to_md.sh` shell script.
```bash
scripts/docx_to_md.sh predocs/your_report.docx
```
*Note: This script uses `pandoc` under the hood. It extracts media to `docs/assets/` and attempts a basic front-matter guess.*

---

## Step 2: Web-friendly Renaming

The scripts often generate filenames with spaces or encoded characters. Rename the resulting `.md` file in `docs/` to a web-friendly URL slug.

**Pattern:** `OR_YYYYMMDD_Location_Description.md`  
**Example:** `OR_20241230_Lake_Sonoma.md`

---

## Step 3: Front-matter & Content Cleanup

Open the new Markdown file and verify the Jekyll front-matter:

1.  **Layout**: Must be `layout: or`.
2.  **Title**: Ensure it is clean and descriptive.
3.  **Author**: 
    - Verify the author from the source document.
    - If the author cannot be determined with certainty, **leave the field blank**. Do not guess or hallucinate an author.
4.  **Content**: Remove any duplicate headers or artifacts introduced during conversion (common with the `.docx` script).

---

## Step 4: Image Compression

Large images slow down the site. Check for new assets in `docs/assets/` that exceed **500kB**.

Compress them using `mogrify` to balance file size and visual quality:
```bash
mogrify -resize 1000x1000\> -quality 90 docs/assets/large_image.jpeg
```

---

## Step 5: DSO Tagging (Deep Sky Objects)

To enable interactive features, astronomical objects must be wrapped in `<x-dso>` tags. Use the `apply_dso.py` script:

```bash
uv run scripts/apply_dso.py --file docs/OR_your_slug.md
```
*Note: Only run this on the newly added files to maintain a clean git diff.*

---

## Step 6: Final Review & Staging

1.  **Human Review**: Open the Markdown file to ensure images are rendering correctly and the text formatting is consistent with other reports.
2.  **Staging**: Stage the Markdown file and its associated assets in `docs/assets/`.
    ```bash
    git add docs/OR_your_slug.md docs/assets/associated_images...
    ```
3.  **Verification**: Run `git status` to ensure no unrelated files were modified.
