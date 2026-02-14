# Repository Guidelines

## Project Structure & Module Organization
This repository extracts structured data from Frontex SIR PDFs.

- `fetch_sir_zip_urls.py`: scrapes Frontex metadata and updates `zip_urls.txt` + `sir_documents.jsonl`.
- `process_sir_zips.sh`: downloads ZIP/PDF sources into `rawdata/` and prepares PDFs in `pdfs/<batch>/`.
- `extract_sir_pdf_gemini.py`: sends PDFs to Gemini and writes outputs to `analysis_output/`.
- `prompts/`: extraction prompts (default: `prompts/extract_sir.txt`).
- `docs/`: supporting documentation.
- `rawdata/`, `pdfs/`, `analysis_output/`: data artifacts (large files tracked with Git LFS where applicable).

## Build, Test, and Development Commands
Use the local virtual environment:

```bash
source .venv/bin/activate
export GEMINI_API_KEY="..."
```

Core commands:

- `python3 fetch_sir_zip_urls.py --dry-run` checks new URLs/metadata without writing.
- `./process_sir_zips.sh zip_urls.txt` downloads and extracts PDFs.
- `python3 extract_sir_pdf_gemini.py pdfs --output-dir analysis_output` runs full extraction.
- `python3 extract_sir_pdf_gemini.py pdfs/pad-2025-00419/file.pdf --output-dir analysis_output` processes one PDF.
- `python3 extract_sir_pdf_gemini.py pdfs --no-skip-existing` forces reprocessing.

## Data Analysis with DuckDB
For analysis and synthesis of tabular outputs, prefer DuckDB over ad-hoc scripts when working on `*.csv` and `*.jsonl`.

Examples:

- `duckdb :memory: "SELECT count(*) FROM 'sir_documents.jsonl';"`
- `duckdb :memory: "SELECT substr(publication_date,1,4) AS year, count(*) FROM 'sir_documents.jsonl' GROUP BY 1 ORDER BY 1;"`
- `duckdb :memory: "SELECT sir_id, dead_confirmed FROM 'analysis_output/summary.csv' ORDER BY dead_confirmed DESC NULLS LAST LIMIT 20;"`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation, explicit type hints, clear function names (`snake_case`).
- Bash: `set -euo pipefail`, defensive checks, lowercase `snake_case` vars.
- Keep scripts idempotent when possible (`--dry-run`, skip-existing behavior).
- Name outputs predictably: `<pdf_stem>.extracted.json`, per-folder `summary.csv`, `summary_totals.json`.

## Testing Guidelines
There is no formal automated test suite yet. Validate changes with:

1. `python3 fetch_sir_zip_urls.py --dry-run`
2. A small extraction run on one folder or one PDF
3. Manual inspection of `analysis_output/*/summary.csv` and `summary_totals.json`

When changing parsing/schema logic, include at least one before/after output example in your PR notes.

## Commit & Pull Request Guidelines
Follow the existing history style: Conventional Commit prefixes such as `feat:` and `docs:` (e.g., `feat: add prompt-path option`).

PRs should include:

1. What changed and why
2. Commands run for validation
3. Data impact (files/fields affected, reprocessing needed or not)
4. Any API cost/runtime implications

## Security & Configuration Tips
- Never commit secrets; use `GEMINI_API_KEY` via environment variables.
- Treat `rawdata/`, `pdfs/`, and generated outputs as large artifacts; avoid unnecessary churn in tracked binaries.
