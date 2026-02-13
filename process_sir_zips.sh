#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./process_sir_zips.sh <zip_urls.txt> [--zip-dir DIR] [--pdf-dir DIR]

Behavior:
  1) Downloads each ZIP into --zip-dir (default: rawdata/) if not already present.
  2) Extracts only PDF files from each ZIP.
  3) Writes PDFs into --pdf-dir/<zip_stem>/ (default: pdfs/), skipping existing files.

Input format:
  - One ZIP URL per line.
  - Empty lines and lines starting with '#' are ignored.
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

URLS_FILE="$1"
shift

ZIP_DIR="rawdata"
PDF_DIR="pdfs"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --zip-dir)
      ZIP_DIR="${2:-}"
      shift 2
      ;;
    --pdf-dir)
      PDF_DIR="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$URLS_FILE" ]]; then
  echo "Input file not found: $URLS_FILE" >&2
  exit 1
fi

require_cmd curl
require_cmd unzip
require_cmd find
require_cmd mktemp

mkdir -p "$ZIP_DIR" "$PDF_DIR"

downloaded=0
download_skipped=0
pdf_extracted=0
pdf_skipped=0
failures=0

while IFS= read -r line || [[ -n "$line" ]]; do
  # Trim leading/trailing whitespace.
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"

  [[ -z "$line" ]] && continue
  [[ "$line" == \#* ]] && continue

  url="$line"
  zip_name="$(basename "${url%%\?*}")"
  zip_name="${zip_name// /_}"
  zip_path="$ZIP_DIR/$zip_name"
  zip_stem="${zip_name%.zip}"
  out_dir="$PDF_DIR/$zip_stem"
  mkdir -p "$out_dir"

  if [[ -f "$zip_path" ]]; then
    echo "[SKIP download] $zip_name"
    ((download_skipped+=1))
  else
    echo "[DOWNLOAD] $url -> $zip_path"
    curl -fL --retry 3 --retry-delay 2 -o "$zip_path" "$url"
    ((downloaded+=1))
  fi

  tmp_dir="$(mktemp -d)"
  if ! unzip -q -o "$zip_path" -d "$tmp_dir"; then
    echo "[ERROR] Cannot extract $zip_path" >&2
    ((failures+=1))
    rm -rf "$tmp_dir"
    continue
  fi

  found_pdf=0
  while IFS= read -r -d '' pdf_path; do
    found_pdf=1
    pdf_name="$(basename "$pdf_path")"
    pdf_name="${pdf_name// /_}"
    out_pdf="$out_dir/$pdf_name"

    if [[ -f "$out_pdf" ]]; then
      echo "  [SKIP PDF] $out_pdf"
      ((pdf_skipped+=1))
    else
      cp -f "$pdf_path" "$out_pdf"
      echo "  [PDF] $pdf_name -> $out_pdf"
      ((pdf_extracted+=1))
    fi
  done < <(find "$tmp_dir" -type f \( -iname '*.pdf' -o -iname '*.PDF' \) -print0 | sort -z)

  if [[ $found_pdf -eq 0 ]]; then
    echo "  [WARN] No PDF found in $zip_name"
  fi

  rm -rf "$tmp_dir"
done < "$URLS_FILE"

echo
echo "Done."
echo "Downloads: new=$downloaded skipped=$download_skipped"
echo "PDF files: new=$pdf_extracted skipped=$pdf_skipped"
echo "Failures:  $failures"

if [[ $failures -gt 0 ]]; then
  exit 1
fi
