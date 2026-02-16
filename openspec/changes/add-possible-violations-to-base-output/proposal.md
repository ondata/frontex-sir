## Why

SIR reports often include a section on possible fundamental-rights violations, but this information is not consistently stored as structured data. Without a normalized array, robust counting and comparison across SIRs is not possible.

## What Changes

- Add `possible_violations` array per SIR record.
- Normalize each item with `violation_name`, `legal_basis`, and `assessment`.
- Add summary derivatives for tabular analysis: `possible_violations_count` and `possible_violations_json`.
- Update extraction prompt to parse "Possible violation(s) of fundamental rights enquired" sections.

## Capabilities

### New Capabilities
- `possible-violations-extraction`: Extract and normalize possible-violations entries per SIR and expose them for aggregate analysis.

### Modified Capabilities
- None.

## Impact

- Affected code: `extract_sir_pdf_gemini.py`, `prompts/extract_sir.txt`.
- Affected outputs: per-record JSON and `summary.csv`.
- Related tracking: issue #4 (`@sapomnia` request).
- No breaking change expected; additive fields only.

