## ADDED Requirements

### Requirement: Extractor SHALL emit possible_violations array per SIR
For each SIR record, the extractor SHALL include `possible_violations` as an array. Each element SHALL represent one violation item listed in the report section on possible violations.

#### Scenario: Report lists multiple possible violations
- **WHEN** a SIR report includes multiple listed violations
- **THEN** the extractor outputs one `possible_violations` element per listed item

#### Scenario: Report does not contain possible-violations section
- **WHEN** the section is absent
- **THEN** the extractor outputs `possible_violations` as an empty array

### Requirement: Violation items SHALL be normalized with explicit fields
Each item in `possible_violations` SHALL include `violation_name` (required), `legal_basis` (nullable), and `assessment` normalized to `likely|possible|unclear|not_stated`.

#### Scenario: Assessment explicitly stated in source
- **WHEN** source text labels the assessment (for example likely or unclear)
- **THEN** extractor maps it to the normalized enum values

#### Scenario: Assessment missing in source
- **WHEN** no explicit assessment is available for a listed violation
- **THEN** extractor sets `assessment` to `not_stated`

### Requirement: Summary export SHALL include violation-derived fields
`summary.csv` SHALL include `possible_violations_count` and `possible_violations_json` for each SIR row.

#### Scenario: Summary row for record with two violations
- **WHEN** a record has two entries in `possible_violations`
- **THEN** `possible_violations_count` equals `2` and `possible_violations_json` serializes both entries

