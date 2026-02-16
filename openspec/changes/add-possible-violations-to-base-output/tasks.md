## 1. Prompt and Model

- [ ] 1.1 Extend `prompts/extract_sir.txt` with explicit `possible_violations` extraction rules.
- [ ] 1.2 Add `PossibleViolation` model and `possible_violations` field in `SirRecord`.
- [ ] 1.3 Add assessment normalization (`likely|possible|unclear|not_stated`).

## 2. Output and Compatibility

- [ ] 2.1 Add `possible_violations_count` and `possible_violations_json` to `summary.csv`.
- [ ] 2.2 Ensure backward compatibility for records with no violation section (`[]` default).

## 3. Validation and Docs

- [ ] 3.1 Validate on known SIR examples containing multiple violations.
- [ ] 3.2 Validate on records without violation section.
- [ ] 3.3 Document aggregation query in project documentation.

