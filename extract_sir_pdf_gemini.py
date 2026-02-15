#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from google import genai
from google.genai import types
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


Confidence = Literal["high", "medium", "low"]
LocationType = Literal["sea", "land", "facility", "mixed", "unknown"]
PrecisionLevel = Literal["exact", "approximate", "broad", "unknown"]
Geocodable = Literal["yes", "no"]
SIR_ID_PATTERN = re.compile(r"\b\d{5}/\d{4}\b")


class SirRecord(BaseModel):
    sir_id: str = Field(pattern=r"^\d{5}/\d{4}$")
    report_date: Optional[str] = None
    incident_date: Optional[str] = None
    location_details: Optional[str] = None
    where_clear: Optional[str] = None
    location_text_raw: Optional[str] = None
    country_or_area: Optional[str] = None
    location_type: Optional[LocationType] = None
    precision_level: Optional[PrecisionLevel] = None
    geocodable: Optional[Geocodable] = None
    geocodable_query: Optional[str] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)
    uncertainty_note: Optional[str] = None
    dead_confirmed: Optional[int] = Field(default=None, ge=0)
    injured_confirmed: Optional[int] = Field(default=None, ge=0)
    missing_confirmed: Optional[int] = Field(default=None, ge=0)
    dead_possible_min: Optional[int] = Field(default=None, ge=0)
    dead_possible_max: Optional[int] = Field(default=None, ge=0)
    context_note: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("context_note", "note_contesto")
    )
    libyan_coast_guard_involved: Optional[bool] = None
    evidence_quote: str = Field(
        min_length=1,
        validation_alias=AliasChoices("evidence_quote", "evidenza_testuale"),
    )
    confidence: Confidence = Field(
        validation_alias=AliasChoices("confidence", "confidenza")
    )
    evidence_pages: list[int] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> str:
        mapping = {
            "alta": "high",
            "media": "medium",
            "bassa": "low",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        key = str(value).strip().lower()
        if key not in mapping:
            raise ValueError(f"Invalid confidence value: {value}")
        return mapping[key]

    @field_validator("location_type", mode="before")
    @classmethod
    def normalize_location_type(cls, value: object) -> object:
        if value is None:
            return None
        key = str(value).strip().lower()
        mapping = {
            "sea": "sea",
            "land": "land",
            "facility": "facility",
            "mixed": "mixed",
            "unknown": "unknown",
        }
        if key not in mapping:
            raise ValueError(f"Invalid location_type value: {value}")
        return mapping[key]

    @field_validator("precision_level", mode="before")
    @classmethod
    def normalize_precision_level(cls, value: object) -> object:
        if value is None:
            return None
        key = str(value).strip().lower()
        mapping = {
            "exact": "exact",
            "approximate": "approximate",
            "broad": "broad",
            "unknown": "unknown",
        }
        if key not in mapping:
            raise ValueError(f"Invalid precision_level value: {value}")
        return mapping[key]

    @field_validator("geocodable", mode="before")
    @classmethod
    def normalize_geocodable(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, bool):
            return "yes" if value else "no"
        key = str(value).strip().lower()
        mapping = {
            "yes": "yes",
            "no": "no",
            "true": "yes",
            "false": "no",
        }
        if key not in mapping:
            raise ValueError(f"Invalid geocodable value: {value}")
        return mapping[key]

    @field_validator("lat", "lon", mode="before")
    @classmethod
    def normalize_decimal_coordinate(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        s = str(value).strip()
        if not s or s.lower() in {"null", "none", "na", "n/a"}:
            return None

        # Enforce decimal numeric format only, no cardinal/dms annotations.
        if any(ch in s.lower() for ch in ["n", "s", "e", "w", "°", "'", '"']):
            raise ValueError(
                "Coordinate must be decimal numeric value without N/E/S/W or DMS symbols"
            )

        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError as exc:
            raise ValueError(
                f"Coordinate must be decimal numeric value: {value}"
            ) from exc

    @model_validator(mode="after")
    def check_possible_range(self) -> "SirRecord":
        if (
            self.dead_possible_min is not None
            and self.dead_possible_max is not None
            and self.dead_possible_max < self.dead_possible_min
        ):
            raise ValueError("dead_possible_max must be >= dead_possible_min")
        return self


class ExtractionPayload(BaseModel):
    records: list[SirRecord] = Field(default_factory=list)


class BatchOutput(BaseModel):
    source_file: str
    model: str
    generated_at_utc: str
    records: list[SirRecord]
    dead_confirmed_total: int = Field(ge=0)
    injured_confirmed_total: int = Field(ge=0)
    missing_confirmed_total: int = Field(ge=0)
    dead_possible_total_min: int = Field(ge=0)
    dead_possible_total_max: int = Field(ge=0)
    records_invalid_skipped: int = Field(default=0, ge=0)


def normalize_model_name(model: str) -> str:
    if model.startswith("gemini/"):
        return model.split("/", 1)[1]
    return model


def read_pdf_targets(path_arg: str) -> list[Path]:
    src = Path(path_arg)
    if not src.exists():
        raise FileNotFoundError(f"Input path not found: {src}")
    if src.is_file():
        if src.suffix.lower() != ".pdf":
            raise ValueError(f"Input file must be .pdf: {src}")
        return [src]
    return sorted(p for p in src.rglob("*.pdf") if p.is_file())


def group_targets_by_top_folder(
    targets: list[Path], input_path: str
) -> dict[str, list[Path]]:
    src = Path(input_path)
    if src.is_file():
        return {".": sorted(targets)}

    src_resolved = src.resolve()
    grouped: dict[str, list[Path]] = {}
    for pdf in targets:
        try:
            rel = pdf.resolve().relative_to(src_resolved)
        except ValueError:
            rel = Path(pdf.name)
        group = rel.parts[0] if len(rel.parts) > 1 else "."
        grouped.setdefault(group, []).append(pdf)

    for group in grouped:
        grouped[group] = sorted(grouped[group])
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def should_exclude(path: Path, patterns: list[str]) -> bool:
    if not patterns:
        return False
    s = str(path)
    name = path.name
    for pat in patterns:
        if Path(s).match(pat) or Path(name).match(pat):
            return True
    return False


def build_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def extract_json(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Empty model response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    obj = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if obj:
        return json.loads(obj.group(1))

    raise ValueError("Could not parse JSON from model response")


def upload_pdf(client: genai.Client, pdf_path: Path) -> types.File:
    with open(pdf_path, "rb") as fh:
        uploaded = client.files.upload(
            file=fh,
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=pdf_path.name,
            ),
        )
    return uploaded


def call_gemini(
    client: genai.Client,
    model: str,
    uploaded_file: types.File,
    prompt: str,
    max_retries: int = 3,
) -> dict:
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type="application/pdf",
                    ),
                    types.Part.from_text(text=prompt),
                ],
                config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                },
            )
            text = getattr(response, "text", None)
            if not text:
                raise ValueError("Gemini response did not contain text output")
            return extract_json(text)
        except (ValueError, json.JSONDecodeError):
            raise
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = 5 * 2**attempt
            print(f"  [RETRY {attempt + 1}/{max_retries}] {exc} — waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def sum_opt(records: list[SirRecord], attr: str) -> int:
    return sum(getattr(r, attr) or 0 for r in records)


def sum_max_possible(records: list[SirRecord]) -> int:
    total = 0
    for rec in records:
        if rec.dead_possible_max is not None:
            total += rec.dead_possible_max
        elif rec.dead_possible_min is not None:
            total += rec.dead_possible_min
    return total


def extract_numeric_sir_id(value: object) -> Optional[str]:
    if value is None:
        return None
    match = SIR_ID_PATTERN.search(str(value))
    if not match:
        return None
    return match.group(0)


def parse_valid_sir_records(
    raw_json: dict, pdf_file: Path
) -> tuple[list[SirRecord], int]:
    if not isinstance(raw_json, dict):
        raise ValueError("Model response JSON root must be an object")

    raw_records = raw_json.get("records", [])
    if raw_records is None:
        raw_records = []
    if not isinstance(raw_records, list):
        raise ValueError("Model response field 'records' must be an array")

    valid_records: list[SirRecord] = []
    skipped = 0
    examples: list[str] = []

    for idx, raw_rec in enumerate(raw_records, start=1):
        if not isinstance(raw_rec, dict):
            skipped += 1
            if len(examples) < 3:
                examples.append(f"#{idx}: non-object record")
            continue

        normalized = raw_rec.copy()
        sir_id = extract_numeric_sir_id(normalized.get("sir_id"))
        if not sir_id:
            skipped += 1
            if len(examples) < 3:
                raw_id = str(normalized.get("sir_id", "null"))[:60]
                examples.append(f"#{idx}: invalid sir_id={raw_id!r}")
            continue
        normalized["sir_id"] = sir_id

        try:
            valid_records.append(SirRecord.model_validate(normalized))
        except ValidationError as exc:
            skipped += 1
            if len(examples) < 3:
                first = str(exc).splitlines()[0]
                examples.append(f"#{idx} {sir_id}: {first}")
            continue

    if skipped:
        detail = f" Examples: {', '.join(examples)}." if examples else ""
        print(
            f"  [WARN] {pdf_file.name}: skipped {skipped} non-SIR/invalid records.{detail}",
            file=sys.stderr,
        )

    return valid_records, skipped


def process_file(
    client: genai.Client,
    model: str,
    pdf_file: Path,
    out_dir: Path,
    skip_existing: bool,
    prompt_path: Path,
) -> tuple[Path, BatchOutput]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_file.stem}.extracted.json"

    if skip_existing and out_path.exists():
        print(f"  [SKIP] {out_path} already exists")
        existing = BatchOutput.model_validate_json(out_path.read_text(encoding="utf-8"))
        return out_path, existing

    prompt = build_prompt(prompt_path)
    uploaded = upload_pdf(client, pdf_file)
    try:
        raw_json = call_gemini(client, model, uploaded, prompt)
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass

    records, records_invalid_skipped = parse_valid_sir_records(raw_json, pdf_file)
    result = BatchOutput(
        source_file=str(pdf_file),
        model=model,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        records=records,
        dead_confirmed_total=sum_opt(records, "dead_confirmed"),
        injured_confirmed_total=sum_opt(records, "injured_confirmed"),
        missing_confirmed_total=sum_opt(records, "missing_confirmed"),
        dead_possible_total_min=sum_opt(records, "dead_possible_min"),
        dead_possible_total_max=sum_max_possible(records),
        records_invalid_skipped=records_invalid_skipped,
    )

    out_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path, result


def write_summary(
    records: list[dict], totals: dict, out_dir: Path
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "summary.csv"
    json_path = out_dir / "summary_totals.json"

    fields = [
        "source_file",
        "model",
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
        "libyan_coast_guard_involved",
        "confidence",
        "evidence_pages",
        "evidence_quote",
        "context_note",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in records:
            row = row.copy()
            row["evidence_pages"] = ",".join(
                str(x) for x in row.get("evidence_pages", [])
            )
            writer.writerow(row)

    json_path.write_text(
        json.dumps(totals, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return csv_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract SIR victim + location fields from PDF using Gemini File API + Pydantic schema."
    )
    parser.add_argument("input_path", help="PDF file or directory containing PDF files")
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model name (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--output-dir",
        default="analysis_output",
        help="Directory where JSON outputs will be written",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude PDF files. Can be used multiple times.",
    )
    parser.add_argument(
        "--min-seconds-between-calls",
        type=float,
        default=4.0,
        help="Minimum delay between Gemini API calls (default: 4.0).",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip PDFs that already have an extracted JSON output (default: on).",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Re-process PDFs even if output already exists.",
    )
    parser.add_argument(
        "--prompt-path",
        default="prompts/extract_sir.txt",
        help="Path to prompt file (default: prompts/extract_sir.txt)",
    )
    parser.add_argument(
        "--skip-completed-groups",
        action="store_true",
        default=True,
        help="Skip groups/folders that already have summary.csv (default: on).",
    )
    parser.add_argument(
        "--no-skip-completed-groups",
        dest="skip_completed_groups",
        action="store_false",
        help="Do not skip groups by summary.csv; useful for incremental daily batches.",
    )
    parser.add_argument(
        "--max-new-files",
        type=int,
        default=0,
        help="Process at most N new files requiring API calls (0 = no limit).",
    )
    args = parser.parse_args()

    if args.max_new_files < 0:
        print("--max-new-files must be >= 0", file=sys.stderr)
        return 1

    if args.max_new_files > 0 and args.skip_completed_groups:
        print(
            "[INFO] --max-new-files detected: disabling group-summary skip for incremental processing."
        )
        args.skip_completed_groups = False
    incremental_mode = args.max_new_files > 0

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable", file=sys.stderr)
        return 1

    try:
        targets = read_pdf_targets(args.input_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    targets = [p for p in targets if not should_exclude(p, args.exclude)]
    if not targets:
        print("No .pdf files found in input path", file=sys.stderr)
        return 1

    model = normalize_model_name(args.model)
    client = genai.Client(api_key=api_key)
    out_dir = Path(args.output_dir)
    prompt_path = Path(args.prompt_path)
    groups = group_targets_by_top_folder(targets, args.input_path)

    failures = 0
    files_processed = 0
    all_rows: list[dict] = []
    total_dead_confirmed = 0
    total_injured_confirmed = 0
    total_missing_confirmed = 0
    total_dead_possible_min = 0
    total_dead_possible_max = 0
    total_records_invalid_skipped = 0
    files_skipped_by_limit = 0
    api_calls_made = 0
    groups_with_work = 0
    limit_reached = False

    for group_name, group_targets in groups.items():
        if limit_reached:
            break

        group_out_dir = out_dir if group_name == "." else out_dir / group_name

        # If a folder-level summary exists, assume that folder was already processed.
        group_summary_csv = group_out_dir / "summary.csv"
        if (
            args.skip_existing
            and args.skip_completed_groups
            and group_summary_csv.exists()
        ):
            group_label = (
                group_name if group_name != "." else Path(args.input_path).name or "."
            )
            print(f"[SKIP GROUP] {group_label} (found {group_summary_csv})")
            continue

        groups_with_work += 1
        group_failures = 0
        group_files_processed = 0
        group_rows: list[dict] = []
        group_dead_confirmed = 0
        group_injured_confirmed = 0
        group_missing_confirmed = 0
        group_dead_possible_min = 0
        group_dead_possible_max = 0
        group_records_invalid_skipped = 0
        group_had_activity = False

        for pdf_file in group_targets:
            group_out_json = group_out_dir / f"{pdf_file.stem}.extracted.json"
            needs_api_call = not (args.skip_existing and group_out_json.exists())

            # Incremental mode: ignore already-processed files to avoid reloading/rewriting summaries.
            if incremental_mode and not needs_api_call:
                continue

            if (
                needs_api_call
                and incremental_mode
                and api_calls_made >= args.max_new_files
            ):
                limit_reached = True
                break

            try:
                if (
                    needs_api_call
                    and api_calls_made > 0
                    and args.min_seconds_between_calls > 0
                ):
                    print(f"[WAIT] sleeping {args.min_seconds_between_calls:.1f}s")
                    time.sleep(args.min_seconds_between_calls)

                out_path, result = process_file(
                    client,
                    model,
                    pdf_file,
                    group_out_dir,
                    args.skip_existing,
                    prompt_path,
                )
                if needs_api_call:
                    api_calls_made += 1

                print(f"[OK] {pdf_file} -> {out_path}")
                group_had_activity = True
                group_files_processed += 1
                group_dead_confirmed += result.dead_confirmed_total
                group_injured_confirmed += result.injured_confirmed_total
                group_missing_confirmed += result.missing_confirmed_total
                group_dead_possible_min += result.dead_possible_total_min
                group_dead_possible_max += result.dead_possible_total_max
                group_records_invalid_skipped += result.records_invalid_skipped
                for rec in result.records:
                    row = rec.model_dump(mode="json")
                    row["source_file"] = result.source_file
                    row["model"] = result.model
                    group_rows.append(row)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                failures += 1
                group_failures += 1
                group_had_activity = True
                print(f"[ERROR] {pdf_file}: {exc}", file=sys.stderr)
            except Exception as exc:
                failures += 1
                group_failures += 1
                group_had_activity = True
                print(f"[ERROR] {pdf_file}: {exc}", file=sys.stderr)

        if not group_had_activity:
            continue

        group_input_label = (
            args.input_path if group_name == "." else f"{args.input_path}/{group_name}"
        )
        group_totals = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "input_path": group_input_label,
            "files_processed": group_files_processed,
            "files_failed": group_failures,
            "records_total": len(group_rows),
            "dead_confirmed_total": group_dead_confirmed,
            "injured_confirmed_total": group_injured_confirmed,
            "missing_confirmed_total": group_missing_confirmed,
            "dead_possible_total_min": group_dead_possible_min,
            "dead_possible_total_max": group_dead_possible_max,
            "records_invalid_skipped": group_records_invalid_skipped,
            "files_skipped_by_limit": 0,
        }
        groups_with_work += 1
        if not incremental_mode:
            csv_path, json_path = write_summary(group_rows, group_totals, group_out_dir)
            print(f"[SUMMARY] {csv_path}")
            print(f"[SUMMARY] {json_path}")

        files_processed += group_files_processed
        total_dead_confirmed += group_dead_confirmed
        total_injured_confirmed += group_injured_confirmed
        total_missing_confirmed += group_missing_confirmed
        total_dead_possible_min += group_dead_possible_min
        total_dead_possible_max += group_dead_possible_max
        total_records_invalid_skipped += group_records_invalid_skipped
        all_rows.extend(group_rows)

    if groups_with_work == 0:
        if incremental_mode:
            print("[DONE] Incremental batch: no new files found.")
        else:
            print("[DONE] Nothing to process: all folders already have summary.csv")
        return 0

    totals = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_path": args.input_path,
        "files_processed": files_processed,
        "files_failed": failures,
        "records_total": len(all_rows),
        "dead_confirmed_total": total_dead_confirmed,
        "injured_confirmed_total": total_injured_confirmed,
        "missing_confirmed_total": total_missing_confirmed,
        "dead_possible_total_min": total_dead_possible_min,
        "dead_possible_total_max": total_dead_possible_max,
        "records_invalid_skipped": total_records_invalid_skipped,
        "files_skipped_by_limit": files_skipped_by_limit,
    }

    # In incremental mode avoid writing partial summaries.
    if incremental_mode:
        limit_text = f"/{args.max_new_files}" if args.max_new_files > 0 else ""
        print(
            f"[DONE] Incremental batch processed {files_processed}{limit_text} new files; failures={failures}."
        )
    # When processing multiple top-level folders, also emit one global summary at output root.
    elif len(groups) > 1 or "." not in groups:
        csv_path, json_path = write_summary(all_rows, totals, out_dir)
        print(f"[SUMMARY ALL] {csv_path}")
        print(f"[SUMMARY ALL] {json_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
