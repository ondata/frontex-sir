#!/usr/bin/env python3
"""
Fetches all SIR documents from the Frontex PRD:
- Appends new download URLs to zip_urls.txt (idempotent)
- Writes full metadata to sir_documents.jsonl (one record per document)

Usage:
    python3 fetch_sir_zip_urls.py
    python3 fetch_sir_zip_urls.py --dry-run
    python3 fetch_sir_zip_urls.py --output other_file.txt --jsonl other_file.jsonl
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

LISTING_URL = (
    "https://prd.frontex.europa.eu/"
    "?form-fields%5Bdocument-tag%5D%5B0%5D=409"
    "&form-fields%5Bpaged%5D={page}"
)
DIALOG_URL = (
    "https://prd.frontex.europa.eu/"
    "wp-content/themes/template/templates/cards/1/dialog.php"
    "?card-post-id=2722&document-post-id={doc_id}"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; frontex-sir-scraper/1.0)"}
SLEEP = 0.5  # seconds between requests


def get_doc_ids_from_page(page: int, session: requests.Session) -> list[str]:
    url = LISTING_URL.format(page=page)
    r = session.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return re.findall(r"document-post-id=(\d+)", r.text)


def parse_date(raw: str) -> str | None:
    """Convert DD.MM.YYYY to ISO YYYY-MM-DD, return None if unparseable."""
    try:
        return datetime.strptime(raw.strip(), "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return raw.strip() or None


def get_metadata_from_dialog(doc_id: str, session: requests.Session) -> dict:
    url = DIALOG_URL.format(doc_id=doc_id)
    r = session.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    html = r.text

    # Title
    title_m = re.search(
        r'<div class="title">Title</div><div class="text">([^<]+)</div>', html
    )
    title = title_m.group(1).strip() if title_m else None

    # Publication date: <div class="publish-date text">DD.MM.YYYY</div>
    date_m = re.search(r'<div class="publish-date text">([^<]+)</div>', html)
    publication_date = parse_date(date_m.group(1)) if date_m else None

    # Language: <div class="title">Language</div><div class="card-terms-with-commas text">EN</div>
    lang_m = re.search(
        r'<div class="title">Language</div><div class="card-terms-with-commas text">([^<]+)</div>',
        html,
    )
    language = lang_m.group(1).strip() if lang_m else None

    # Document format: same pattern
    fmt_m = re.search(
        r'<div class="title">Document format</div><div class="card-terms-with-commas text">([^<]+)</div>',
        html,
    )
    document_format = fmt_m.group(1).strip() if fmt_m else None

    # Tags
    tags = re.findall(r'href="[^"]*document-tag[^"]*"[^>]*>([^<]+)<', html)
    tags = [t.strip() for t in tags if t.strip()]

    # Download URLs with labels
    download_urls = [
        {"url": m[0], "label": m[1].strip()}
        for m in re.findall(
            r'<option value="(https://[^"]+\.(?:zip|pdf))"[^>]*>([^<]+)</option>', html
        )
    ]

    # Document page URL
    page_url_m = re.search(r'href="(https://prd\.frontex\.europa\.eu/document/[^"]+)"', html)
    document_page_url = page_url_m.group(1) if page_url_m else None

    return {
        "doc_id": doc_id,
        "title": title,
        "publication_date": publication_date,
        "language": language,
        "document_format": document_format,
        "tags": tags,
        "download_urls": download_urls,
        "document_page_url": document_page_url,
    }


def load_existing_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    urls = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.add(line)
    return urls


def load_existing_doc_ids(jsonl_path: Path) -> set[str]:
    if not jsonl_path.exists():
        return set()
    ids = set()
    for line in jsonl_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                ids.add(json.loads(line)["doc_id"])
            except (json.JSONDecodeError, KeyError):
                pass
    return ids


def main():
    parser = argparse.ArgumentParser(description="Fetch Frontex SIR document metadata")
    parser.add_argument(
        "--output",
        default="zip_urls.txt",
        help="URL list output file (default: zip_urls.txt)",
    )
    parser.add_argument(
        "--jsonl",
        default="sir_documents.jsonl",
        help="JSONL metadata output file (default: sir_documents.jsonl)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results without writing to files",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=20,
        help="Max pages to scrape (default: 20)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    jsonl_path = Path(args.jsonl)

    existing_urls = load_existing_urls(output_path)
    existing_doc_ids = load_existing_doc_ids(jsonl_path)
    print(f"Existing URLs : {len(existing_urls)}", file=sys.stderr)
    print(f"Existing docs : {len(existing_doc_ids)}", file=sys.stderr)

    session = requests.Session()
    new_urls: list[str] = []
    new_docs: list[dict] = []
    doc_ids_seen: set[str] = set()

    for page in range(args.pages):
        print(f"Scraping listing page {page + 1}/{args.pages}...", file=sys.stderr)
        doc_ids = get_doc_ids_from_page(page, session)
        if not doc_ids:
            print(f"  No more results at page {page + 1}, stopping.", file=sys.stderr)
            break
        time.sleep(SLEEP)

        for doc_id in doc_ids:
            if doc_id in doc_ids_seen:
                continue
            doc_ids_seen.add(doc_id)

            meta = get_metadata_from_dialog(doc_id, session)

            for item in meta["download_urls"]:
                url = item["url"]
                if url not in existing_urls and url not in new_urls:
                    print(f"  + {url}", file=sys.stderr)
                    new_urls.append(url)

            if doc_id not in existing_doc_ids:
                new_docs.append(meta)

            time.sleep(SLEEP)

    print(f"\nNew URLs  : {len(new_urls)}", file=sys.stderr)
    print(f"New docs  : {len(new_docs)}", file=sys.stderr)

    if args.dry_run:
        for url in new_urls:
            print(url)
        return

    if new_urls:
        with output_path.open("a") as f:
            for url in new_urls:
                f.write(url + "\n")
        print(f"Appended {len(new_urls)} URLs to {output_path}", file=sys.stderr)

    if new_docs:
        with jsonl_path.open("a") as f:
            for doc in new_docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print(f"Appended {len(new_docs)} docs to {jsonl_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
