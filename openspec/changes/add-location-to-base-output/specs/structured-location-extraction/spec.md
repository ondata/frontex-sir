## ADDED Requirements

### Requirement: Extractor SHALL emit structured location fields per SIR
The extraction output SHALL include the following location fields for each SIR record: `where_clear`, `location_text_raw`, `country_or_area`, `location_type`, `precision_level`, `geocodable`, `geocodable_query`, `lat`, `lon`, and `uncertainty_note`.

#### Scenario: Explicit location is present in source report
- **WHEN** a SIR report contains explicit location details
- **THEN** the extractor returns populated structured location fields consistent with the source evidence

#### Scenario: Location evidence is insufficient
- **WHEN** a SIR report does not provide enough location detail
- **THEN** the extractor sets uncertain fields to `null` and preserves uncertainty notes when available

### Requirement: Extractor SHALL keep backward-compatible location text field
The extractor SHALL keep `location_details` in each SIR record to preserve compatibility with existing consumers.

#### Scenario: Existing consumer reads location_details only
- **WHEN** downstream tooling ignores new fields
- **THEN** it can continue to use `location_details` without schema breakage

### Requirement: Extractor SHALL enforce geocodable and precision rubrics
The extractor SHALL classify `precision_level` and `geocodable` according to prompt-defined rubrics and SHALL only emit `geocodable_query` when geocoding is practical.

#### Scenario: Location is practically geocodable
- **WHEN** report text identifies a bounded and actionable place/area
- **THEN** `geocodable` is `yes` and `geocodable_query` is populated

#### Scenario: Location is ambiguous or redacted
- **WHEN** report text is generic, conflicting, or redacted
- **THEN** `geocodable` is `no` and `geocodable_query` is `null`

### Requirement: Summary export SHALL include structured location columns
`summary.csv` SHALL include the structured location columns required for downstream analysis.

#### Scenario: Summary is generated from extracted records
- **WHEN** summary writer runs
- **THEN** it outputs location columns including `precision_level`, `geocodable`, and `geocodable_query`

