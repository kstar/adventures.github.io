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

---

## Step 7: Deployment & Linking

Once the author has verified that the reports display correctly on the website, they must be linked from the main observing reports index and the site highlights.

### Updating the Observing Reports Index
1.  Open `docs/observing.reports.htm`.
2.  Locate the table of reports.
3.  Add a new section for the current month and year if it doesn't exist (e.g., `March 2026`).
4.  Add the new report(s) to the table. **Crucially, reports are dated and sorted by the date they were added to the site, not the date of the observation.**
5.  Follow the existing HTML table pattern:
    ```html
    <tr>
      <th>27</th> <!-- Day of the month added -->
      <td><div align="left">Report Title</div></td>
      <td><a href="/OR_slug.html">Author Name</a></td>
    </tr>
    ```

### Updating Site Highlights
1.  Open `docs/_data/highlights.csv`.
2.  Add a new row for each report (or group of reports) at the top of the file (reverse chronological order).
3.  Format: `date,page,description`
    - `date`: YYYY-MM-DD
    - `page`: The `.html` filename (optional if included in description link).
    - `description`: A short description, often including a link and the author's name.
