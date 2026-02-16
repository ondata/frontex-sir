## 1. Prompt and Schema

- [ ] 1.1 Add structured location block instructions to `prompts/extract_sir.txt`.
- [ ] 1.2 Extend `SirRecord` with new location fields and normalization validators.

## 2. Output Integration

- [ ] 2.1 Update summary writer to include new location columns in `summary.csv`.
- [ ] 2.2 Ensure backward compatibility for existing consumers using `location_details`.

## 3. Validation and Documentation

- [ ] 3.1 Run extraction on a representative sample and verify location distribution via DuckDB.
- [ ] 3.2 Update README/operational docs with the new location output contract.

