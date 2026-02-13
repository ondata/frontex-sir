# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Extracts structured data (JSON/CSV) from Frontex **Serious Incident Reports (SIR)** PDFs using Gemini. The pipeline has two steps: download ZIPs → extract PDFs → send each PDF to Gemini → validate output with Pydantic.

## Environment

Python virtual environment is in `.venv`. Activate before running Python scripts:

```bash
source .venv/bin/activate
```

Required env variable:

```bash
export GEMINI_API_KEY="..."
```

## Running the pipeline

```bash
# Step 1: download ZIPs and extract PDFs
./process_sir_zips.sh zip_urls.txt

# Step 2: extract structured data from PDFs
python3 extract_sir_pdf_gemini.py pdfs --output-dir analysis_output

# Force reprocessing (ignore skip logic)
python3 extract_sir_pdf_gemini.py pdfs --output-dir analysis_output --no-skip-existing

# Process a single PDF
python3 extract_sir_pdf_gemini.py pdfs/pad-2025-00419/somefile.pdf --output-dir analysis_output
```

## Key files

- `extract_sir_pdf_gemini.py` — main script; uploads each PDF to Gemini File API, validates response with Pydantic (`SirRecord`, `ExtractionPayload`, `BatchOutput`), writes `.extracted.json` + summary CSV/JSON
- `process_sir_zips.sh` — downloads ZIPs from `zip_urls.txt`, extracts PDFs into `pdfs/<zip_stem>/`
- `zip_urls.txt` — one ZIP URL per line; `#` = comment

## Output structure

```
analysis_output/
├── summary.csv                    # global summary across all batches
├── summary_totals.json            # global totals
└── <batch>/
    ├── summary.csv
    ├── summary_totals.json
    └── <filename>.extracted.json  # per-PDF output
```

## Skip logic

- Folder skipped if `analysis_output/<batch>/summary.csv` exists
- Single PDF skipped if `<filename>.extracted.json` exists

## Data model

`SirRecord` (Pydantic): `sir_id` (format `DDDDD/YYYY`), `report_date`, `incident_date`, `location_details`, `dead_confirmed`, `injured_confirmed`, `missing_confirmed`, `dead_possible_min/max`, `note_contesto`, `evidenza_testuale`, `confidenza` (alta/media/bassa), `evidence_pages`.

## Git LFS

PDFs (`*.pdf`) and ZIPs (`*.zip`) are tracked via Git LFS (configured in `.gitattributes`).
