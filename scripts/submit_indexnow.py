#!/usr/bin/env python3
"""Notify IndexNow after verified production releases.

The production sitemap is the authority for currently indexable URLs. Curated-game
removals may additionally submit the retired canonical URL so search engines can
revisit its 404/410 state. No retry is performed: protocol/API failures are loud.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib import error, parse, request

DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
DEFAULT_KEY_FILE = Path("frontend/public/indexnow.txt")
INDEXNOW_ENDPOINT = "https://api.indexnow.org/IndexNow"
SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
MAX_URLS = 10_000


class IndexNowError(RuntimeError):
    pass


def read_key(path: Path) -> str:
    key = path.read_text(encoding="utf-8").strip()
    if not key or any(ch.isspace() for ch in key):
        raise IndexNowError("IndexNow key file must contain one non-empty token")
    return key


def normalize_base_url(value: str) -> str:
    parsed = parse.urlsplit(value.rstrip("/"))
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        raise IndexNowError("Base URL must be an HTTPS origin")
    return f"https://{parsed.netloc}"


def validate_same_host_url(url: str, base_url: str) -> str:
    parsed = parse.urlsplit(url)
    base = parse.urlsplit(base_url)
    if parsed.scheme != "https" or parsed.netloc != base.netloc:
        raise IndexNowError(f"IndexNow URL is outside canonical HTTPS host: {url}")
    if parsed.username or parsed.password or parsed.fragment:
        raise IndexNowError(f"IndexNow URL contains unsupported credentials/fragment: {url}")
    return url


def parse_sitemap(xml_text: str, base_url: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise IndexNowError("Production sitemap is not valid XML") from exc
    urls: list[str] = []
    seen: set[str] = set()
    for node in root.findall("s:url/s:loc", SITEMAP_NS):
        value = (node.text or "").strip()
        if not value:
            continue
        value = validate_same_host_url(value, base_url)
        if value not in seen:
            seen.add(value)
            urls.append(value)
    if not urls:
        raise IndexNowError("Production sitemap contains no canonical URLs")
    if len(urls) > MAX_URLS:
        raise IndexNowError(f"Production sitemap exceeds IndexNow batch limit: {len(urls)}")
    return urls


def fetch_text(url: str, *, timeout: float = 20.0) -> tuple[int, str]:
    req = request.Request(url, headers={"User-Agent": "RuleScribe-IndexNow/1.0"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), body


def verify_production_key(base_url: str, key: str) -> str:
    key_url = f"{base_url}/indexnow.txt"
    status, body = fetch_text(key_url)
    if status != 200 or body.strip() != key:
        raise IndexNowError(f"Production IndexNow key verification failed: HTTP {status} {key_url}")
    return key_url


def parse_changed_files(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        raise IndexNowError(f"Changed-files input does not exist: {path}")
    entries: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        if len(parts) < 2:
            raise IndexNowError(f"Invalid git --name-status row: {raw}")
        status = parts[0]
        file_path = parts[-1]
        entries.append((status, file_path))
    return entries


def select_urls(entries: list[tuple[str, str]], sitemap_urls: list[str], base_url: str) -> list[str]:
    sitemap_set = set(sitemap_urls)
    selected: set[str] = set()
    global_public_change = False

    for status, file_path in entries:
        if file_path.startswith("frontend/src/") or file_path in {
            "backend/app/main.py",
            "backend/app/routers/games.py",
            "backend/app/services/seo_renderer.py",
            "backend/app/services/sitemap.py",
            "vercel.json",
        }:
            global_public_change = True
            continue
        if file_path.startswith("backend/app/db/migrations/") and file_path.endswith(".sql"):
            global_public_change = True
            continue
        prefix = "data/curated-games/"
        if file_path.startswith(prefix) and file_path.endswith(".json"):
            slug = Path(file_path).stem
            game_url = f"{base_url}/games/{slug}"
            if status.startswith("D"):
                selected.add(game_url)
            elif game_url in sitemap_set:
                selected.add(game_url)
            selected.add(f"{base_url}/")

    if global_public_change:
        selected.update(sitemap_urls)

    ordered = sorted(validate_same_host_url(url, base_url) for url in selected)
    if len(ordered) > MAX_URLS:
        raise IndexNowError(f"Selected URL count exceeds IndexNow batch limit: {len(ordered)}")
    return ordered


def submit_urls(base_url: str, key: str, key_url: str, urls: list[str], *, timeout: float = 20.0) -> int:
    if not urls:
        return 0
    payload = json.dumps(
        {
            "host": parse.urlsplit(base_url).netloc,
            "key": key,
            "keyLocation": key_url,
            "urlList": urls,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = request.Request(
        INDEXNOW_ENDPOINT,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "RuleScribe-IndexNow/1.0"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = int(response.status)
    except error.HTTPError as exc:
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise IndexNowError(f"IndexNow submission failed: HTTP {status} {body}") from exc
    if status not in (200, 202):
        raise IndexNowError(f"IndexNow submission returned unexpected HTTP {status}")
    return status


def self_test() -> None:
    base = DEFAULT_BASE_URL
    xml = """<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
    <url><loc>https://bodoge-no-mikata.vercel.app/</loc></url>
    <url><loc>https://bodoge-no-mikata.vercel.app/games/splendor</loc></url>
    <url><loc>https://bodoge-no-mikata.vercel.app/games/splendor</loc></url>
    </urlset>"""
    urls = parse_sitemap(xml, base)
    assert urls == [f"{base}/", f"{base}/games/splendor"]
    selected = select_urls(
        [("M", "data/curated-games/splendor.json")], urls, base
    )
    assert selected == [f"{base}/", f"{base}/games/splendor"]
    deleted = select_urls(
        [("D", "data/curated-games/retired-game.json")], urls, base
    )
    assert deleted == [f"{base}/", f"{base}/games/retired-game"]
    assert select_urls([("M", "README.md")], urls, base) == []
    assert select_urls([("M", "frontend/src/App.jsx")], urls, base) == sorted(urls)
    try:
        validate_same_host_url("https://example.com/games/x", base)
    except IndexNowError:
        pass
    else:
        raise AssertionError("external host must fail")
    print("IndexNow deterministic checks: OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--changed-files-file", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.changed_files_file is None:
        parser.error("--changed-files-file is required unless --self-test is used")

    base_url = normalize_base_url(args.base_url)
    key = read_key(args.key_file)
    key_url = verify_production_key(base_url, key)
    sitemap_status, sitemap_xml = fetch_text(f"{base_url}/sitemap.xml")
    if sitemap_status != 200:
        raise IndexNowError(f"Production sitemap fetch failed: HTTP {sitemap_status}")
    sitemap_urls = parse_sitemap(sitemap_xml, base_url)
    entries = parse_changed_files(args.changed_files_file)
    urls = select_urls(entries, sitemap_urls, base_url)
    if not urls:
        print(f"IndexNow key verified; no public canonical URL changed; submitted=0 keyLocation={key_url}")
        return 0
    status = submit_urls(base_url, key, key_url, urls)
    print(f"IndexNow submitted={len(urls)} status={status} keyLocation={key_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (IndexNowError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
