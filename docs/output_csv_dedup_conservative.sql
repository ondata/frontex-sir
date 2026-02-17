-- Conservative dedup workflow for output_csv/sir_records.csv
-- Objective: keep multiple rows for the same sir_id only when substantial fields differ.
--
-- Substantial-change signature fields:
-- - incident_date
-- - report_date
-- - country_or_area
-- - where_clear
-- - location_type
-- - dead_confirmed / injured_confirmed / missing_confirmed
-- - possible_violations_count
--
-- Within each (sir_id, signature), keep the best row by quality ranking.
--
-- Run:
-- duckdb :memory: ".read docs/output_csv_dedup_conservative.sql"

CREATE OR REPLACE TEMP VIEW sir_conservative_ranked AS
WITH base AS (
  SELECT
    *,
    CASE confidence
      WHEN 'high' THEN 2
      WHEN 'medium' THEN 1
      WHEN 'low' THEN 0
      ELSE -1
    END AS confidence_score,
    (
      CASE WHEN report_date IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN incident_date IS NOT NULL AND incident_date <> '' THEN 1 ELSE 0 END +
      CASE WHEN country_or_area IS NOT NULL AND country_or_area <> '' THEN 1 ELSE 0 END +
      CASE WHEN where_clear IS NOT NULL AND where_clear <> '' THEN 1 ELSE 0 END +
      CASE WHEN geocodable IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN geocodable_query IS NOT NULL AND geocodable_query <> '' THEN 1 ELSE 0 END +
      CASE WHEN dead_confirmed IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN injured_confirmed IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN missing_confirmed IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN possible_violations_count IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN evidence_quote IS NOT NULL AND evidence_quote <> '' THEN 1 ELSE 0 END +
      CASE WHEN evidence_pages IS NOT NULL AND evidence_pages <> '' THEN 1 ELSE 0 END
    ) AS completeness_score,
    CASE
      WHEN lower(source_file) LIKE '%email%' THEN 0
      WHEN lower(source_file) LIKE '%annual%' THEN 0
      WHEN lower(source_file) LIKE '%sea-borders-surveillance-report%' THEN 0
      WHEN lower(source_file) LIKE '%sea_surveillance_report%' THEN 0
      ELSE 1
    END AS source_priority,
    COALESCE(dead_confirmed, 0) + COALESCE(injured_confirmed, 0) + COALESCE(missing_confirmed, 0) AS impact_score,
    -- event signature: if this changes, keep a separate row for the same sir_id
    CONCAT_WS(
      '||',
      COALESCE(CAST(report_date AS VARCHAR), ''),
      COALESCE(incident_date, ''),
      COALESCE(TRIM(country_or_area), ''),
      COALESCE(TRIM(where_clear), ''),
      COALESCE(location_type, ''),
      COALESCE(CAST(dead_confirmed AS VARCHAR), ''),
      COALESCE(CAST(injured_confirmed AS VARCHAR), ''),
      COALESCE(CAST(missing_confirmed AS VARCHAR), ''),
      COALESCE(CAST(possible_violations_count AS VARCHAR), '')
    ) AS event_signature
  FROM 'output_csv/sir_records.csv'
  WHERE sir_id IS NOT NULL
), ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY sir_id, event_signature
      ORDER BY
        source_priority DESC,
        completeness_score DESC,
        confidence_score DESC,
        report_date DESC NULLS LAST,
        TRY_CAST(incident_date AS DATE) DESC NULLS LAST,
        impact_score DESC,
        possible_violations_count DESC NULLS LAST,
        source_file ASC,
        record_index ASC
    ) AS rn
  FROM base
)
SELECT * FROM ranked;

COPY (
  SELECT
    record_uid,
    batch,
    source_file,
    record_index,
    model,
    generated_at_utc,
    sir_id,
    report_date,
    incident_date,
    location_details,
    where_clear,
    location_text_raw,
    country_or_area,
    location_type,
    precision_level,
    geocodable,
    geocodable_query,
    lat,
    lon,
    uncertainty_note,
    dead_confirmed,
    injured_confirmed,
    missing_confirmed,
    dead_possible_min,
    dead_possible_max,
    possible_violations_count,
    context_note,
    libyan_coast_guard_involved,
    evidence_quote,
    confidence,
    evidence_pages
  FROM sir_conservative_ranked
  WHERE rn = 1
  ORDER BY sir_id, report_date NULLS LAST, incident_date NULLS LAST, source_file
) TO 'output_csv/sir_records_conservative.csv' (HEADER, DELIMITER ',');

COPY (
  SELECT v.*
  FROM 'output_csv/violations.csv' v
  JOIN (SELECT record_uid FROM sir_conservative_ranked WHERE rn = 1) k USING (record_uid)
  ORDER BY v.sir_id, v.record_uid, v.violation_index
) TO 'output_csv/violations_conservative.csv' (HEADER, DELIMITER ',');

-- Mapping table for auditability: which original rows were merged in each kept signature
COPY (
  SELECT
    sir_id,
    event_signature,
    COUNT(*) AS source_rows_in_signature,
    MIN(report_date) AS min_report_date,
    MAX(report_date) AS max_report_date,
    STRING_AGG(DISTINCT source_file, ' | ' ORDER BY source_file) AS source_files
  FROM sir_conservative_ranked
  GROUP BY 1, 2
  ORDER BY sir_id
) TO 'output_csv/sir_records_conservative_groups.csv' (HEADER, DELIMITER ',');

-- Quick sanity checks
SELECT
  (SELECT COUNT(*) FROM 'output_csv/sir_records.csv') AS original_rows,
  (SELECT COUNT(*) FROM 'output_csv/sir_records_dedup.csv') AS strict_dedup_rows,
  (SELECT COUNT(*) FROM 'output_csv/sir_records_conservative.csv') AS conservative_rows,
  (SELECT COUNT(DISTINCT sir_id) FROM 'output_csv/sir_records_conservative.csv') AS conservative_distinct_sir_id;

SELECT
  (SELECT COUNT(*) FROM 'output_csv/violations.csv') AS original_violations,
  (SELECT COUNT(*) FROM 'output_csv/violations_dedup.csv') AS strict_dedup_violations,
  (SELECT COUNT(*) FROM 'output_csv/violations_conservative.csv') AS conservative_violations;
