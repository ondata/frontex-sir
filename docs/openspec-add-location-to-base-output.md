# OpenSpec Change: Add Location Extraction to Base Output

## Status
Proposed

## Owner
Frontex SIR Extractor maintainers

## Context
The base extractor currently focuses on victim-related fields.  
Location is partially present in `location_details`, but not normalized enough for mapping, aggregation, or geospatial analysis.

The `location_probe_v2` experiment on 20 PDFs showed that location can be extracted with useful structure:
- 36 SIR records extracted
- geocodable classification available (`yes/no`)
- confidence and precision can be separated (`high/medium/low`, `exact/approximate/broad/unknown`)

## Goal
Extend the **base extraction output** (`.extracted.json` and `summary.csv`) with structured location fields for each SIR, without breaking existing workflows.

## Non-Goals
- Automatic geocoding to coordinates in this change
- GIS pipeline integration
- Historical backfill of all previous outputs (can be done separately)

## Proposed Schema Additions (per SIR record)
Add these optional fields:
- `where_clear` (string|null)
- `location_text_raw` (string|null)
- `country_or_area` (string|null)
- `location_type` (`sea|land|facility|mixed|unknown|null`)
- `precision_level` (`exact|approximate|broad|unknown|null`)
- `geocodable` (`yes|no|null`)
- `geocodable_query` (string|null)
- `lat` (number|null)
- `lon` (number|null)
- `uncertainty_note` (string|null)

Keep `location_details` for backward compatibility.

## Prompt Update
Merge location instructions from `location_probe_v2` into the main prompt (`prompts/extract_sir.txt`) so the default run returns both:
1. victim metrics
2. structured location block per SIR

Use strict confidence rubric:
- `high`: explicit named place/bounded maritime area
- `medium`: inferred from context
- `low`: generic/redacted/conflicting clues

Use strict geocodable rubric:
- `yes`: practical bounded query possible
- `no`: too generic/redacted/ambiguous

## Implementation Plan
1. Update `SirRecord` in `extract_sir_pdf_gemini.py` with new location fields.
2. Update CSV summary columns (`write_summary`) to include new location fields.
3. Update prompt (`prompts/extract_sir.txt`) with location schema and strict rubrics.
4. Update docs (`README.md`, `CLAUDE.md`) with new output fields.
5. Run validation on a 20-PDF sample and verify distribution quality with DuckDB.

## Acceptance Criteria
1. Running `python3 extract_sir_pdf_gemini.py <input> --output-dir <out>` produces valid JSON with new location fields for each record.
2. `summary.csv` includes `precision_level`, `geocodable`, `geocodable_query`, and `confidence`.
3. On the 20-PDF sample, `confidence` is not collapsed to a single value (e.g. not all `high`).
4. On the same sample, both `geocodable=yes` and `geocodable=no` appear.
5. Existing consumers that only use old fields continue to work (new fields are additive and optional).

## Validation Queries (DuckDB)
```sql
SELECT precision_level, confidence, COUNT(*) n
FROM read_csv_auto('analysis_output/location_probe_v2_20/summary.csv')
GROUP BY 1,2 ORDER BY n DESC;

SELECT geocodable, COUNT(*) n
FROM read_csv_auto('analysis_output/location_probe_v2_20/summary.csv')
GROUP BY 1;
```
