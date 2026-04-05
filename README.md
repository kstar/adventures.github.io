# Adventures in Deep Space (adventures.github.io)

This repository contains the source code for the "Adventures in Deep Space" website, hosted on GitHub Pages. It uses Jekyll and Liquid to render Markdown and HTML into a static site.

## Repository Structure

- `docs/`: Contains the primary website source code, including `_config.yml` and content files (`.md`, `.htm`, `.html`).
- `docs/assets/`: Stores images and other BLOB assets.
  - **Note:** Please be mindful of the size of this directory. Ensure assets are optimized and avoid adding excessively large files to maintain repository health.
- `scripts/`: Contains Python and shell scripts for data processing, maintenance, and site generation.
- `pyproject.toml` / `uv.lock`: Configuration for the Python environment and dependencies.

## Local Development

To run the website locally for testing and development, follow these steps:

### Prerequisites

- Ruby (refer to `docs/Gemfile` for versioning)
- Bundler (`gem install bundler`)
- Jekyll

### Running the Website

1. Navigate to the `docs/` directory:
   ```bash
   cd docs
   ```
2. Install dependencies:
   ```bash
   bundle install
   ```
3. Start the Jekyll server:
   ```bash
   bundle exec jekyll serve
   ```
4. Once the server is running, navigate your browser to:
   `http://localhost:4000`

## Python Environment

The repository includes a suite of scripts in `scripts/` to manage DSO (Deep Sky Object) data, ingest emails, and fix formatting.

- **Python Version:** 3.13 (managed via `.python-version`)
- **Dependency Management:** Use `uv` or `pip` to manage dependencies listed in `pyproject.toml` or `scripts/requirements.txt`.

```bash
# Example: Install dependencies using uv
uv sync
```
