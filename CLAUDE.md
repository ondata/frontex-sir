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

# Use custom prompt file (for A/B testing)
python3 extract_sir_pdf_gemini.py pdfs --prompt-path prompts/extract_sir_v2.txt
```

## Key files

- `extract_sir_pdf_gemini.py` — main script; uploads each PDF to Gemini File API, validates response with Pydantic (`SirRecord`, `ExtractionPayload`, `BatchOutput`), writes `.extracted.json` + summary CSV/JSON
- `process_sir_zips.sh` — downloads ZIPs from `zip_urls.txt`, extracts PDFs into `pdfs/<zip_stem>/`
- `zip_urls.txt` — one ZIP URL per line; `#` = comment
- `prompts/extract_sir.txt` — system prompt for Gemini extraction (versioned for A/B testing)

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

## Preferred analysis tool

Per analizzare e fare sintesi di file `jsonl` e `csv`, usare DuckDB come prima scelta.

Esempi:

```bash
duckdb :memory: "SELECT count(*) FROM 'sir_documents.jsonl';"
duckdb :memory: "SELECT substr(publication_date,1,4) AS year, count(*) FROM 'sir_documents.jsonl' GROUP BY 1 ORDER BY 1;"
duckdb :memory: "SELECT * FROM 'analysis_output/summary.csv' LIMIT 20;"
```

## Skip logic

- Folder skipped if `analysis_output/<batch>/summary.csv` exists
- Single PDF skipped if `<filename>.extracted.json` exists

## Data model

`SirRecord` (Pydantic): `sir_id` (format `DDDDD/YYYY`), `report_date`, `incident_date`, `location_details`, `where_clear`, `location_text_raw`, `country_or_area`, `location_type`, `precision_level`, `geocodable` (`yes|no`), `geocodable_query`, `lat`, `lon`, `uncertainty_note`, `dead_confirmed`, `injured_confirmed`, `missing_confirmed`, `dead_possible_min/max`, `context_note`, `libyan_coast_guard_involved` (bool|null), `evidence_quote`, `confidence` (`high|medium|low`), `evidence_pages`.

## Git LFS

PDFs (`*.pdf`) and ZIPs (`*.zip`) are tracked via Git LFS (configured in `.gitattributes`).

## GitHub discussions ondata

Le discussioni di ondata sono nel repo `ondata/attivita`. Usare GraphQL (non REST) per interagire:

```bash
# Leggere una discussion
gh api graphql -f query='{ repository(owner: "ondata", name: "attivita") { discussion(number: 107) { id title } } }'

# Commentare una discussion (serve il node ID della discussion)
gh api graphql -f query='mutation { addDiscussionComment(input: { discussionId: "D_kwDOKQU8-M4AkIAA", body: "testo" }) { comment { url } } }'
```
