
#!/usr/bin/env python3
"""
Это нейросетевой говнокод, но вам понравится!
Берем ключи тут: @git_keys_shop_bot
git_dork_search.py
Stream‑download matching files from GitHub Code Search directly to disk,
avoiding large in‑memory buffers.

Usage:
  python3 git_dork_search.py \
    --token YOUR_GITHUB_PAT \
    --dork "filename:.env DB_PASSWORD" \
    [--output-dir /path/to/output] \
    [--resume]

Options:
  --token       GitHub Personal Access Token with repo/code read scopes.
  --dork        GitHub Code Search query (dork).
  --output-dir  Base directory for downloaded files (default: ./output).
  --resume      Skip files already listed in findings.csv.

The script streams every matched file straight to disk, so RAM usage stays
constant even for multi‑gigabyte results.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import List, Set

import requests
from tqdm import tqdm

API_URL = "https://api.github.com/search/code"
RAW_ACCEPT = "application/vnd.github.v3.raw"
TEXT_MATCH_ACCEPT = "application/vnd.github.v3.text-match+json"
CHUNK_SIZE = 32 * 1024  # 32 KB


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GitHub dork search & streamed downloader")
    p.add_argument("--token", required=True, help="GitHub Personal Access Token")
    p.add_argument("--dork", required=True, help="Search query, e.g. 'filename:.env DB_PASSWORD'")
    p.add_argument("--output-dir", default="output", help="Folder for downloads (default: output)")
    p.add_argument("--resume", action="store_true", help="Resume from existing findings.csv")
    return p.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv_header(csv_path: Path) -> None:
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "repo",
                "file_path",
                "line_number",
                "context_excerpt",
                "github_url",
            ])


def append_csv(csv_path: Path, row: List[str]) -> None:
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def download_file(item: dict, headers: dict, local_path: Path) -> bool:
    """Stream the raw file to *local_path*. Returns True on success."""
    raw_url = item["url"]
    with requests.get(
        raw_url,
        headers={**headers, "Accept": RAW_ACCEPT},
        stream=True,
        timeout=60,
    ) as r:
        if not r.ok:
            return False
        ensure_dir(local_path.parent)
        with local_path.open("wb") as f:
            for chunk in r.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
    return True


def safe_extract_text_match(item: dict) -> tuple[str, str]:
    """Return (fragment, line_number) safely without KeyError."""
    text_matches = item.get("text_matches", [])
    fragment = "<no context>"
    line_number: str | int = "?"
    if text_matches:
        first_match_block = text_matches[0]
        fragment = (first_match_block.get("fragment") or "<no context>").replace("\n", " ")
        matches_list = first_match_block.get("matches", [])
        if matches_list:
            line_number = matches_list[0].get("line_number", "?")
    return fragment, str(line_number)


def main() -> None:
    args = parse_args()
    headers = {
        "Authorization": f"token {args.token}",
        "Accept": TEXT_MATCH_ACCEPT,
        "User-Agent": "git-dork-search/1.1",
    }

    output_base = Path(args.output_dir).resolve()
    ensure_dir(output_base)
    csv_path = output_base / "findings.csv"
    write_csv_header(csv_path)

    seen: Set[str] = set()
    if args.resume and csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as f:
            next(f, None)  # skip header
            for line in f:
                parts = line.rstrip("\n").split(",", 2)
                if len(parts) >= 2:
                    seen.add(f"{parts[0]}/{parts[1]}")

    print(f"[+] Saving files under {output_base}\n")

    for page in tqdm(range(1, 101), desc="Pages", unit="page"):
        params = {"q": args.dork, "per_page": 100, "page": page}
        r = requests.get(API_URL, headers=headers, params=params, timeout=60)
        if r.status_code == 422:
            sys.exit("[!] Invalid dork query syntax. Aborting.")
        if r.status_code == 403:
            reset = r.headers.get("X-RateLimit-Reset", "?")
            sys.exit(f"[!] Rate‑limit exceeded. Retry after {reset}.")

        data = r.json()
        items = data.get("items", [])
        if not items:
            break  # no more results

        for item in items:
            repo = item["repository"]["full_name"]
            file_path = item["path"]
            unique_id = f"{repo}/{file_path}"
            if unique_id in seen:
                continue

            local_path = output_base / "github.com" / repo / file_path
            success = download_file(item, headers, local_path)
            if not success:
                continue

            fragment, line_number = safe_extract_text_match(item)

            append_csv(csv_path, [repo, file_path, line_number, fragment, item["html_url"]])
            seen.add(unique_id)

        time.sleep(1)  # stay within 60 req/min safety margin

    print("[✓] Done. Review findings.csv and the output directory.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
