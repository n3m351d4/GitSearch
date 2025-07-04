#!/usr/bin/env python3
"""gh_dork_download.py – массовый скачиватель файлов по GitHub Code Search.

CLI: нужны только `--token` и `--dork`.
* Сохраняет файлы и CSV‑отчёт в каталог **output/**.
* Всегда начинает новую сессию (без резюме).
* `findings.csv` содержит колонку `match_line` (первая строка с совпадением) и
  `context_excerpt` (±2 строки вокруг неё).
* Перед стартом проверяет Search‑лимит GitHub и ждёт сброса, если `remaining=0`.
"""
from __future__ import annotations

import argparse
import csv
import re
import shlex
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Set

import requests
from requests.exceptions import RequestException
from tqdm import tqdm

GITHUB_API_URL = "https://api.github.com/search/code"
PER_PAGE = 100
MAX_PAGES = 100  # 10 000 результатов (GitHub всё равно вернёт ≤1 000)
RATE_SLEEP = 1   # секунда между страницами
OUTPUT_DIR = "output"

abort = False

###############################################################################
# Signal handler
###############################################################################

def handle_sigint(signum, frame):  # type: ignore[assign]
    global abort
    abort = True
    print("\n[!] Прерывание… завершаем после текущего запроса.", file=sys.stderr)


signal.signal(signal.SIGINT, handle_sigint)

###############################################################################
# CLI
###############################################################################

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download GitHub search hits and log findings.")
    p.add_argument("--token", required=True, help="GitHub Personal Access Token")
    p.add_argument("--dork", required=True, help="GitHub search dork, e.g. 'filename:.env DB_PASSWORD'")
    return p.parse_args()

###############################################################################
# Rate‑limit helpers
###############################################################################

def rate_status(headers: dict) -> tuple[int, int]:
    """Return (remaining, reset_epoch) for Search API rate‑limit."""
    try:
        resp = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=10)
        data = resp.json()["resources"]["search"]
        return int(data["remaining"]), int(data["reset"])
    except Exception as exc:
        print(f"[WARN] Не удалось получить /rate_limit: {exc}", file=sys.stderr)
        return 0, int(time.time()) + 60


def wait_until(reset_epoch: int):
    wait = reset_epoch - int(time.time()) + 2  # +2 сек страховка
    if wait > 0:
        eta = datetime.fromtimestamp(reset_epoch).strftime("%H:%M:%S")
        print(f"[RATE] Ждём {wait}s до {eta}", file=sys.stderr)
        time.sleep(wait)

###############################################################################
# Utility helpers
###############################################################################

def html_to_raw(html_url: str) -> str:
    """Convert https://github.com/.../blob/... → raw.githubusercontent.com/..."""
    return html_url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")


def save_file(raw_url: str, dest_path: Path) -> None:
    try:
        r = requests.get(raw_url, timeout=30)
        r.raise_for_status()
    except RequestException as e:
        print(f"[!] Не удалось скачать {raw_url}: {e}", file=sys.stderr)
        return

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(r.content)


def build_patterns(dork: str) -> List[re.Pattern[str]]:
    """Из dork‑строки выделяем токены без ':' и строим regex‑паттерны."""
    tokens = shlex.split(dork)
    search_tokens = [t for t in tokens if ':' not in t]
    if not search_tokens:
        search_tokens = [tokens[-1]]  # fallback – последний токен
    return [re.compile(re.escape(tok), re.IGNORECASE) for tok in search_tokens]


def first_match_line(lines: List[str], patterns: List[re.Pattern[str]]) -> tuple[int, str]:
    """Возвращает (номер строки, текст) первого совпадения любого паттерна."""
    for idx, line in enumerate(lines):
        for pat in patterns:
            if pat.search(line):
                return idx + 1, line.strip()[:500]
    return 0, ""


def context_excerpt(lines: List[str], idx: int) -> str:
    if idx == 0:
        return ""
    start = max(idx - 2, 0)
    end = min(idx + 1, len(lines))
    return "".join(lines[start:end]).strip()[:1000]

###############################################################################
# Main
###############################################################################

def main() -> None:
    args = parse_args()

    out_root = Path(OUTPUT_DIR)
    out_root.mkdir(parents=True, exist_ok=True)
    csv_path = out_root / "findings.csv"

    processed: Set[str] = set()

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["repo", "file_path", "line_number", "match_line", "context_excerpt", "github_url"])

        headers = {
            "Authorization": f"token {args.token}",
            "Accept": "application/vnd.github.v3.text-match+json",
            "User-Agent": "gh_dork_download/1.4",
        }

        # Проверяем лимит до старта
        remaining, reset_epoch = rate_status(headers)
        print(
            f"[RATE] Search remaining: {remaining}/30; reset @ {datetime.fromtimestamp(reset_epoch).strftime('%H:%M:%S')}"
        )
        if remaining == 0:
            wait_until(reset_epoch)

        patterns = build_patterns(args.dork)

        pbar = tqdm(total=MAX_PAGES, desc="Pages", unit="page")
        try:
            for page in range(1, MAX_PAGES + 1):
                if abort:
                    break

                params = {"q": args.dork, "per_page": PER_PAGE, "page": page}
                resp = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=60)
                if resp.status_code == 403 and "rate limit" in resp.text.lower():
                    remaining, reset_epoch = rate_status(headers)
                    wait_until(reset_epoch)
                    continue

                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    break

                for item in items:
                    html_url = item["html_url"]
                    if html_url in processed:
                        continue

                    repo = item["repository"]["full_name"]
                    rel_path = item["path"]
                    raw_url = html_to_raw(html_url)
                    dest_path = out_root / "github.com" / repo / rel_path

                    save_file(raw_url, dest_path)

                    try:
                        lines = dest_path.read_text(errors="ignore").splitlines()
                    except Exception:
                        lines = []
                    line_no, match_line = first_match_line(lines, patterns)
                    excerpt = context_excerpt(lines, line_no - 1)

                    writer.writerow([repo, rel_path, line_no, match_line, excerpt, html_url])
                    csv_file.flush()
                    processed.add(html_url)

                time.sleep(RATE_SLEEP)
                pbar.update(1)
                if len(items) < PER_PAGE:
                    break
        finally:
            pbar.close()
            print("[+] Завершено. Итоги записаны в", csv_path)


if __name__ == "__main__":
    main()
