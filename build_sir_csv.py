#!/usr/bin/env python3
"""Build relational CSVs from SIR extracted JSON files.

Produces:
  <output-dir>/sir_records.csv   — one row per SirRecord
  <output-dir>/violations.csv    — one row per possible_violation
"""

import argparse
import csv
import json
from pathlib import Path

SIR_RECORDS_FIELDS = [
    "record_uid",
    "batch",
    "source_file",
    "record_index",
    "model",
    "generated_at_utc",
    "sir_id",
    "report_date",
    "incident_date",
    "location_details",
    "where_clear",
    "location_text_raw",
    "country_or_area",
    "location_type",
    "precision_level",
    "geocodable",
    "geocodable_query",
    "lat",
    "lon",
    "uncertainty_note",
    "dead_confirmed",
    "injured_confirmed",
    "missing_confirmed",
    "dead_possible_min",
    "dead_possible_max",
    "possible_violations_count",
    "context_note",
    "libyan_coast_guard_involved",
    "evidence_quote",
    "confidence",
    "evidence_pages",
]

VIOLATIONS_FIELDS = [
    "record_uid",
    "sir_id",
    "source_file",
    "violation_index",
    "violation_name",
    "legal_basis",
    "assessment",
]


def build_csvs(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_dir.glob("**/*.extracted.json"))
    if not json_files:
        print(f"No .extracted.json files found in {input_dir}")
        return

    record_uid = 0
    records_written = 0
    violations_written = 0

    with open(output_dir / "sir_records.csv", "w", newline="", encoding="utf-8") as rf, \
         open(output_dir / "violations.csv", "w", newline="", encoding="utf-8") as vf:

        rw = csv.DictWriter(rf, fieldnames=SIR_RECORDS_FIELDS)
        vw = csv.DictWriter(vf, fieldnames=VIOLATIONS_FIELDS)
        rw.writeheader()
        vw.writeheader()

        for json_path in json_files:
            batch = json_path.parent.name
            try:
                with open(json_path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except json.JSONDecodeError as exc:
                print(f"WARN: skipping {json_path} ({exc})")
                continue

            source_file = data.get("source_file", "")
            model = data.get("model", "")
            generated_at_utc = data.get("generated_at_utc", "")

            for rec_idx, rec in enumerate(data.get("records", [])):
                record_uid += 1
                violations = rec.get("possible_violations") or []
                evidence_pages = rec.get("evidence_pages") or []

                rw.writerow({
                    "record_uid": record_uid,
                    "batch": batch,
                    "source_file": source_file,
                    "record_index": rec_idx,
                    "model": model,
                    "generated_at_utc": generated_at_utc,
                    "sir_id": rec.get("sir_id", ""),
                    "report_date": rec.get("report_date", ""),
                    "incident_date": rec.get("incident_date", ""),
                    "location_details": rec.get("location_details", ""),
                    "where_clear": rec.get("where_clear", ""),
                    "location_text_raw": rec.get("location_text_raw", ""),
                    "country_or_area": rec.get("country_or_area", ""),
                    "location_type": rec.get("location_type", ""),
                    "precision_level": rec.get("precision_level", ""),
                    "geocodable": rec.get("geocodable", ""),
                    "geocodable_query": rec.get("geocodable_query", ""),
                    "lat": rec.get("lat", ""),
                    "lon": rec.get("lon", ""),
                    "uncertainty_note": rec.get("uncertainty_note", ""),
                    "dead_confirmed": rec.get("dead_confirmed", ""),
                    "injured_confirmed": rec.get("injured_confirmed", ""),
                    "missing_confirmed": rec.get("missing_confirmed", ""),
                    "dead_possible_min": rec.get("dead_possible_min", ""),
                    "dead_possible_max": rec.get("dead_possible_max", ""),
                    "possible_violations_count": len(violations),
                    "context_note": rec.get("context_note", ""),
                    "libyan_coast_guard_involved": rec.get("libyan_coast_guard_involved", ""),
                    "evidence_quote": rec.get("evidence_quote", ""),
                    "confidence": rec.get("confidence", ""),
                    "evidence_pages": ",".join(str(p) for p in evidence_pages),
                })
                records_written += 1

                for v_idx, v in enumerate(violations):
                    vw.writerow({
                        "record_uid": record_uid,
                        "sir_id": rec.get("sir_id", ""),
                        "source_file": source_file,
                        "violation_index": v_idx,
                        "violation_name": v.get("violation_name", ""),
                        "legal_basis": v.get("legal_basis", ""),
                        "assessment": v.get("assessment", ""),
                    })
                    violations_written += 1

    print(f"Written {records_written} records → {output_dir / 'sir_records.csv'}")
    print(f"Written {violations_written} violations → {output_dir / 'violations.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build relational CSVs from SIR extracted JSON files.")
    parser.add_argument("--input-dir", default="analysis_output", type=Path,
                        help="Directory containing .extracted.json files (default: analysis_output)")
    parser.add_argument("--output-dir", default="output_csv", type=Path,
                        help="Directory for output CSVs (default: output_csv)")
    args = parser.parse_args()

    build_csvs(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
