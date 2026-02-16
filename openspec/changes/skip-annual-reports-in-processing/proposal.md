## Why

The pipeline currently sends non-SIR annual reports to Gemini, wasting API calls and runtime while producing empty record outputs. We need a safe pre-filter to skip annual reports without skipping valid SIR files.

## What Changes

- Add annual-report detection by filename/path patterns before API upload/call.
- Skip matched files with explicit log line.
- Add CLI override (`--no-skip-annual-reports`).
- Track skipped annual reports in group/global totals.

## Capabilities

### New Capabilities
- `annual-report-filtering`: Detect and skip annual report PDFs pre-API while preserving valid SIR processing.

### Modified Capabilities
- None.

## Impact

- Affected code: `extract_sir_pdf_gemini.py` filtering and counters.
- Affected output: totals JSON gains annual-report skip counter.
- Affected docs: README operational flags and skip behavior.
- Related tracking: issue #3.

