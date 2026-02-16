## 1. Filtering and CLI

- [ ] 1.1 Implement annual-report detector helper in extraction pipeline.
- [ ] 1.2 Apply annual-report skip before API upload/generation.
- [ ] 1.3 Add CLI flags `--skip-annual-reports` and `--no-skip-annual-reports`.

## 2. Metrics and Logging

- [ ] 2.1 Add explicit skip log line for annual-report files.
- [ ] 2.2 Add `files_skipped_annual_report` to group/global totals output.

## 3. Validation and Docs

- [ ] 3.1 Validate behavior on mixed batch (annual + valid SIR `Final_Report` names).
- [ ] 3.2 Update README with skip behavior and override usage.

