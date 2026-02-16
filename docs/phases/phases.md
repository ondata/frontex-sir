# Project Phases

## Current phase

Phase 2 - Backlog processing and quality control

## Milestones

1. Phase 1 - Pipeline foundation (completed)
- [x] Ingestion pipeline (`fetch_sir_zip_urls.py`, `process_sir_zips.sh`)
- [x] Structured extraction (`extract_sir_pdf_gemini.py`)
- [x] Incremental mode (`--max-new-files`)

2. Phase 2 - Backlog processing and QA (in progress)
- [ ] Process all pending PDFs in `pdfs/` with incremental runs
- [ ] Run sample-based QA on extracted records
- [ ] Publish run-level metrics (coverage, failures, invalid records)

3. Phase 3 - Consolidation and publication (planned)
- [ ] Produce consolidated final dataset
- [ ] Document stable analysis queries (DuckDB)
- [ ] Freeze v1 output schema and workflow

## Baseline snapshot (2026-02-16)

- Documents indexed: 96
- PDFs available: 418
- Extracted JSON outputs: 29
