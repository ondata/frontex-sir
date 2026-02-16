## ADDED Requirements

### Requirement: Processor SHALL skip annual-report PDFs before API calls
The processor SHALL detect annual-report PDFs by safe filename/path patterns and SHALL skip them before any Gemini upload or generation request.

#### Scenario: File matches annual-report pattern
- **WHEN** an input PDF path/name matches annual-report patterns (for example `annual_report`, `annual-report`, `annual report`)
- **THEN** the processor skips the file and does not call Gemini APIs

### Requirement: Processor SHALL avoid unsafe generic report filtering
The processor SHALL NOT skip files only because they include the generic token `report`; filtering MUST avoid false positives for valid SIR names.

#### Scenario: Valid SIR filename includes Final_Report
- **WHEN** a valid SIR filename contains `Final_Report`
- **THEN** the file is processed normally and not treated as annual report

### Requirement: Processor SHALL support annual-report skip override
The CLI SHALL support disabling annual-report filtering via explicit override flag.

#### Scenario: Override is enabled
- **WHEN** user runs processor with `--no-skip-annual-reports`
- **THEN** annual-report files are not auto-skipped by this filter

### Requirement: Totals SHALL include annual-report skip count
Per-group and global totals SHALL include `files_skipped_annual_report`.

#### Scenario: Batch contains annual and non-annual PDFs
- **WHEN** processor completes the batch
- **THEN** totals report non-zero `files_skipped_annual_report` and processed file counts remain correct

