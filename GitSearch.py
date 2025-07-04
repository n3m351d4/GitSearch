#!/usr/bin/env python3
"""gitparse.py — GitHub dork search downloader
НЕЙРОСЕТЕВОЙ ГОВНОКОД, НО ОНО РАБОТАЕТ, МНЕ ПОФИГ
• Стрим‑скачивание файлов на диск без больших буферов
• Корректная обработка ограничений GitHub Search API
• Извлечение фрагмента ±1 строка вокруг совпадения и запись в findings.csv

Usage:
  python3 gitparse.py \
    --token YOUR_GITHUB_PAT \
    --dork "filename:.env AWS_ACCESS_KEY_ID" \
    [--output-dir ./output] \
    [--resume]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from requests.exceptions import RequestException
from tqdm import tqdm

BASE_URL = "https://api.github.com/search/code"
PER_PAGE = 100
MAX_PAGES = 100
RATE_BUFFER = 3  # extra seconds to wait after reset
CONTEXT_LINES = 1  # ± n строк вокруг совпадения


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GitHub dork code‑search & downloader")
    p.add_argument("--token", required=True, help="GitHub Personal Access Token (repo/code read scope)")
    p.add_argument("--dork", required=True, help="GitHub Code Search query string")
    p.add_argument("--output-dir", default="output", help="Directory to save downloaded files")
    p.add_argument("--resume", action="store_true", help="Skip files that already exist")
    return p.parse_args()


def build_headers(token: str) -> Dict[str, str]:
    """Request headers: ask API to return text_matches."""
    return {
        "Authorization": f"token {token}",
        # Header _must_ be exactly this to receive text_matches blocks
        "Accept": "application/vnd.github.text-match+json",
        "User-Agent": "gitparse.py",
    }


def rate_limit_sleep(resp: requests.Response) -> None:
    """Sleep until GitHub rate‑limit resets."""
    retry_after = resp.headers.get("Retry-After")
    if retry_after is not None:
        wait = int(float(retry_after))
    else:
        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait = reset - int(time.time())
    if wait < 0:
        wait = 60  # fallback 1 min
    print(f"[!] Rate‑limit hit. Waiting {wait + RATE_BUFFER} s…", file=sys.stderr)
    time.sleep(wait + RATE_BUFFER)


def save_file(raw_url: str, dest_path: Path, headers: Dict[str, str]) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(raw_url, headers=headers, stream=True, timeout=30) as r:
        r.raise_for_status()
        with dest_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def extract_context(matches: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Return (line_number, context_excerpt).

    GitHub returns a `fragment` containing the matching line plus CONTEXT_LINES
    lines around it when we request the *text-match* media type.
    """
    if not matches:
        return "?", ""

    m = matches[0]
    line_no = str(m.get("line_number", "?"))
    fragment = m.get("fragment", "")
    # Compact multiple lines for CSV; keep tabs/spaces trimmed
    context = " … ".join(filter(None, (l.strip() for l in fragment.split("\n"))))
    # Limit length to keep CSV reasonable
    return line_no, context[:500]


def main() -> None:
    args = parse_args()
    headers = build_headers(args.token)
    out_root = Path(args.output_dir).resolve()
    print(f"[+] Saving files under {out_root}\n", file=sys.stderr)

    findings_path = out_root / "findings.csv"
    findings_path.parent.mkdir(parents=True, exist_ok=True)

    with findings_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(["repo", "file_path", "line_number", "context_excerpt", "github_url"])

        for page in tqdm(range(1, MAX_PAGES + 1), desc="Pages"):
            params = {
                "q": args.dork,
                "per_page": PER_PAGE,
                "page": page,
            }
            try:
                resp = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            except RequestException as e:
                print(f"[!] Request error: {e}", file=sys.stderr)
                break

            # Handle rate-limits
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                rate_limit_sleep(resp)
                continue  # retry same page
            elif resp.status_code >= 400:
                print(f"[!] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
                break

            data = resp.json()
            items: List[Dict[str, Any]] = data.get("items", [])
            if not items:
                break

            for item in items:
                repo_full = item["repository"]["full_name"]
                file_path = item["path"]
                html_url = item["html_url"]
                raw_url = html_url.replace("https://github.com", "https://raw.githubusercontent.com").replace("/blob/", "/")

                dest_path = out_root / repo_full / file_path
                if args.resume and dest_path.exists():
                    # Context might still be useful; ensure it's logged
                    if dest_path.exists():
                        line_no, context = extract_context(item.get("text_matches", []))
                        writer.writerow([repo_full, file_path, line_no, context, html_url])
                    continue

                # Download file (stream)
                try:
                    save_file(raw_url, dest_path, headers)
                except RequestException as e:
                    print(f"[!] Download failed {raw_url}: {e}", file=sys.stderr)
                    continue

                # Write finding row
                line_no, context = extract_context(item.get("text_matches", []))
                writer.writerow([repo_full, file_path, line_no, context, html_url])

            # Friendly delay: GitHub allows ~30 searches/min with PAT
            time.sleep(2)

    print("[✓] Done")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: sys.exit("[!] Interrupted"))
    main()
