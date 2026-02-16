## Why

The extractor currently stores location mostly as free text (`location_details`), which limits mapping, aggregation, and reproducible geospatial analysis. We need a normalized location block in base output to make SIR records queryable across batches.

## What Changes

- Add structured location fields to each extracted SIR record (`where_clear`, `location_text_raw`, `country_or_area`, `location_type`, `precision_level`, `geocodable`, `geocodable_query`, `lat`, `lon`, `uncertainty_note`).
- Keep `location_details` for backward compatibility.
- Add extraction rubrics for location precision and geocodability in the prompt.
- Include new location fields in `summary.csv`.

## Capabilities

### New Capabilities
- `structured-location-extraction`: Extract and normalize location attributes for each SIR record with explicit rubrics and null-safe behavior.

### Modified Capabilities
- None.

## Impact

- Affected code: `extract_sir_pdf_gemini.py`, `prompts/extract_sir.txt`.
- Affected output: `.extracted.json`, `summary.csv`.
- Affected docs: `README.md`, operational run guidance.
- No breaking API change expected; additive schema extension.

