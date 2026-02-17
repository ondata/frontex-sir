-- output_csv analysis queries
-- Run with:
-- duckdb :memory: ".read docs/output_csv_analysis_queries.sql"
-- or copy a single query and execute directly.

-- 1) Coverage: records, sir_id distinti, record senza sir_id
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT sir_id) AS distinct_sir_id,
  SUM(CASE WHEN sir_id IS NULL THEN 1 ELSE 0 END) AS null_sir_id
FROM 'output_csv/sir_records.csv';

-- 2) Trend annuale dei record
SELECT
  SUBSTR(COALESCE(CAST(report_date AS VARCHAR), incident_date), 1, 4) AS year,
  COUNT(*) AS records
FROM 'output_csv/sir_records.csv'
GROUP BY 1
ORDER BY 1;

-- 3) Trend annuale impatti umani
SELECT
  SUBSTR(COALESCE(CAST(report_date AS VARCHAR), incident_date), 1, 4) AS year,
  SUM(COALESCE(dead_confirmed, 0)) AS dead_confirmed,
  SUM(COALESCE(injured_confirmed, 0)) AS injured_confirmed,
  SUM(COALESCE(missing_confirmed, 0)) AS missing_confirmed
FROM 'output_csv/sir_records.csv'
GROUP BY 1
ORDER BY 1;

-- 4) Totali complessivi impatti (incl. range morti possibili)
SELECT
  SUM(COALESCE(dead_confirmed, 0)) AS dead_confirmed_total,
  SUM(COALESCE(injured_confirmed, 0)) AS injured_confirmed_total,
  SUM(COALESCE(missing_confirmed, 0)) AS missing_confirmed_total,
  SUM(COALESCE(dead_possible_min, 0)) AS dead_possible_min_total,
  SUM(COALESCE(dead_possible_max, 0)) AS dead_possible_max_total
FROM 'output_csv/sir_records.csv';

-- 5) Impatti per tipo luogo (sea/land/facility/mixed)
SELECT
  location_type,
  COUNT(*) AS records,
  SUM(COALESCE(dead_confirmed, 0)) AS dead_confirmed,
  SUM(COALESCE(injured_confirmed, 0)) AS injured_confirmed,
  SUM(COALESCE(missing_confirmed, 0)) AS missing_confirmed
FROM 'output_csv/sir_records.csv'
GROUP BY 1
ORDER BY dead_confirmed DESC;

-- 6) Geocodificabilita e qualita localizzazione
SELECT
  geocodable,
  COUNT(*) AS records
FROM 'output_csv/sir_records.csv'
GROUP BY 1
ORDER BY records DESC;

-- 7) Hotspot geografici (split di country_or_area su virgole)
WITH countries AS (
  SELECT TRIM(x) AS country
  FROM 'output_csv/sir_records.csv',
  UNNEST(STRING_SPLIT(COALESCE(country_or_area, ''), ',')) AS t(x)
)
SELECT country, COUNT(*) AS records
FROM countries
WHERE country <> ''
GROUP BY 1
ORDER BY records DESC
LIMIT 20;

-- 8) Ranking violazioni piu frequenti
SELECT
  violation_name,
  COUNT(*) AS n
FROM 'output_csv/violations.csv'
GROUP BY 1
ORDER BY n DESC
LIMIT 25;

-- 9) Distribuzione assessment violazioni (likely/possible/unclear/not_stated)
SELECT
  assessment,
  COUNT(*) AS n
FROM 'output_csv/violations.csv'
GROUP BY 1
ORDER BY n DESC;

-- 10) Top casi prioritari per gravita (morti/feriti/dispersi + violazioni)
SELECT
  sir_id,
  report_date,
  country_or_area,
  COALESCE(dead_confirmed, 0) AS dead_confirmed,
  COALESCE(injured_confirmed, 0) AS injured_confirmed,
  COALESCE(missing_confirmed, 0) AS missing_confirmed,
  COALESCE(possible_violations_count, 0) AS possible_violations_count,
  confidence,
  evidence_pages
FROM 'output_csv/sir_records.csv'
ORDER BY
  COALESCE(dead_confirmed, 0) DESC,
  COALESCE(injured_confirmed, 0) DESC,
  COALESCE(missing_confirmed, 0) DESC,
  COALESCE(possible_violations_count, 0) DESC
LIMIT 30;
