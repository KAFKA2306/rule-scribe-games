from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MECHANICAL_DNA_PATH = "/api/games/skull-king/connections?limit=8"
SOURCE_BOUND_GLOSSARY_PATH = "/api/games/skull-king/glossary?language_code=ja"
CATALOG_AUTH_PATH = "/api/games/splendor"
PUBLIC_GAMES_PAGE_SIZE = 100
SITEMAP_PATH = "/sitemap.xml"
MISSING_GAME_PATH = "/games/this-game-does-not-exist"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
INDEXABILITY_STATE_VERSION = 1


def validate_mechanical_dna_payload(payload: Any) -> int:
    if not isinstance(payload, dict):
        raise ValueError("Mechanical DNA response must be a JSON object")

    expected = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"unexpected {key}: {payload.get(key)!r}; expected {value!r}")

    connections = payload.get("connections")
    if not isinstance(connections, list):
        raise ValueError("connections must be a JSON array")

    return len(connections)


def validate_source_bound_glossary_payload(payload: Any) -> int:
    if not isinstance(payload, dict):
        raise ValueError("Glossary response must be a JSON object")
    if payload.get("status") != "available":
        raise ValueError(f"unexpected glossary status: {payload.get('status')!r}; expected 'available'")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("glossary entries must be a JSON array")

    source_bound_references: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("glossary entries must contain JSON objects")
        references = entry.get("rule_references")
        if not isinstance(references, list):
            raise ValueError("glossary rule_references must be a JSON array")
        for reference in references:
            if not isinstance(reference, dict):
                raise ValueError("glossary rule_references must contain JSON objects")
            if reference.get("verification_status") == "source_bound":
                source_bound_references.append(reference)

    if not source_bound_references:
        raise ValueError(
            "production glossary has no source-bound rule references; "
            "canonical RuleSet data may be missing or migrations may not be applied"
        )

    for reference in source_bound_references:
        if not str(reference.get("rule_set_id") or "").strip():
            raise ValueError("source-bound glossary rule reference is missing rule_set_id")
        if not str(reference.get("source_url") or "").strip():
            raise ValueError("source-bound glossary rule reference is missing source_url")

    return len(source_bound_references)


def validate_anonymous_catalog_patch_status(status_code: int) -> None:
    if status_code not in {401, 403}:
        raise ValueError(
            "anonymous catalog PATCH must fail with HTTP 401 or 403; "
            f"received {status_code}"
        )


def indexability_reasons(game: dict[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if game.get("identity_status") != "verified":
        reasons.append("identity_not_verified")
    if game.get("content_review_status") != "human_reviewed":
        reasons.append("content_not_human_reviewed")
    return tuple(reasons)


def indexable_slugs(games: list[dict[str, Any]]) -> list[str]:
    slugs: list[str] = []
    for game in games:
        slug = str(game.get("slug") or "").strip()
        if slug and not indexability_reasons(game):
            slugs.append(slug)
    return sorted(set(slugs))


def load_indexability_state(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("indexability state must be a JSON object")
    if set(payload) != {"version", "indexable_slugs"}:
        raise ValueError("indexability state must contain only version and indexable_slugs")
    if payload.get("version") != INDEXABILITY_STATE_VERSION:
        raise ValueError(
            "unsupported indexability state version: "
            f"{payload.get('version')!r}; expected {INDEXABILITY_STATE_VERSION}"
        )
    slugs = payload.get("indexable_slugs")
    if not isinstance(slugs, list) or not all(isinstance(slug, str) and slug.strip() for slug in slugs):
        raise ValueError("indexability state indexable_slugs must be a non-empty-string JSON array")
    if len(slugs) != len(set(slugs)):
        raise ValueError("indexability state indexable_slugs must not contain duplicates")
    return set(slugs)


def write_indexability_state(path: Path, slugs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": INDEXABILITY_STATE_VERSION, "indexable_slugs": sorted(slugs)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_indexability_state(current_slugs: list[str], previous_path: Path | None) -> dict[str, Any]:
    if previous_path is None:
        return {
            "comparison_status": "UNVERIFIED",
            "newly_promoted": None,
            "newly_demoted": None,
        }
    if not previous_path.is_file():
        raise ValueError(f"previous indexability state does not exist: {previous_path}")
    previous_slugs = load_indexability_state(previous_path)
    current = set(current_slugs)
    return {
        "comparison_status": "verified",
        "newly_promoted": sorted(current - previous_slugs),
        "newly_demoted": sorted(previous_slugs - current),
    }


def build_indexability_report(games: list[dict[str, Any]], sitemap_urls: set[str], base_url: str) -> dict[str, Any]:
    expected_indexable: set[str] = set()
    reasons = Counter()

    for game in games:
        slug = str(game.get("slug") or "").strip()
        if not slug:
            reasons["missing_slug"] += 1
            continue
        game_reasons = indexability_reasons(game)
        if game_reasons:
            reasons.update(game_reasons)
            continue
        expected_indexable.add(f"{base_url.rstrip('/')}/games/{slug}")

    sitemap_game_urls = {url for url in sitemap_urls if "/games/" in url}
    missing_from_sitemap = sorted(expected_indexable - sitemap_game_urls)
    unexpected_in_sitemap = sorted(sitemap_game_urls - expected_indexable)
    if missing_from_sitemap or unexpected_in_sitemap:
        raise ValueError(
            "production sitemap does not match the public indexability contract: "
            f"missing={missing_from_sitemap}, unexpected={unexpected_in_sitemap}"
        )

    return {
        "public_games": len(games),
        "indexable": len(expected_indexable),
        "non_indexable": len(games) - len(expected_indexable),
        "reason_counts": dict(sorted(reasons.items())),
        "sitemap_game_urls": len(sitemap_game_urls),
        "missing_from_sitemap": missing_from_sitemap,
        "unexpected_in_sitemap": unexpected_in_sitemap,
    }


def _request(base_url: str, path: str, timeout_seconds: float, accept: str) -> tuple[int, bytes]:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        headers={
            "Accept": accept,
            "User-Agent": "rule-scribe-games-production-contract/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def fetch_public_games(base_url: str, timeout_seconds: float = 20.0) -> list[dict[str, Any]]:
    games: list[dict[str, Any]] = []
    expected_total: int | None = None
    offset = 0

    while expected_total is None or offset < expected_total:
        path = f"/api/games?limit={PUBLIC_GAMES_PAGE_SIZE}&offset={offset}"
        status, body = _request(base_url, path, timeout_seconds, "application/json")
        if status != 200:
            raise RuntimeError(f"public games endpoint returned HTTP {status} at offset={offset}")

        payload = json.loads(body)
        page = payload.get("games")
        total = payload.get("total")
        if not isinstance(page, list):
            raise ValueError("public games response must contain a games array")
        if not isinstance(total, int) or total < 0:
            raise ValueError(f"public games response must contain a non-negative integer total; received {total!r}")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise ValueError(
                "public games total changed while paginating: "
                f"expected={expected_total}, received={total}, offset={offset}"
            )
        if not page and offset < expected_total:
            raise ValueError(
                "public games pagination ended before total rows were collected: "
                f"expected={expected_total}, collected={len(games)}, offset={offset}"
            )

        games.extend(page)
        offset += len(page)

    if expected_total is None or len(games) != expected_total:
        raise ValueError(
            "production indexability audit requires the full public catalog: "
            f"expected={expected_total!r}, collected={len(games)}"
        )
    return games


def verify_anonymous_catalog_patch(base_url: str, timeout_seconds: float = 20.0) -> int:
    """Verify the production catalog mutation boundary without changing data."""

    url = f"{base_url.rstrip('/')}{CATALOG_AUTH_PATH}"
    request = Request(
        url,
        data=b"{}",
        method="PATCH",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "rule-scribe-games-production-contract/1.0",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            status_code = response.status
    except HTTPError as exc:
        status_code = exc.code

    validate_anonymous_catalog_patch_status(status_code)
    return status_code


def verify_search_indexability(base_url: str, timeout_seconds: float = 20.0) -> tuple[dict[str, Any], list[str]]:
    games = fetch_public_games(base_url, timeout_seconds)

    sitemap_status, sitemap_body = _request(base_url, SITEMAP_PATH, timeout_seconds, "application/xml")
    if sitemap_status != 200:
        raise RuntimeError(f"sitemap endpoint returned HTTP {sitemap_status}")
    root = ET.fromstring(sitemap_body)
    sitemap_urls = {loc.text for loc in root.findall("sm:url/sm:loc", SITEMAP_NS) if loc.text}

    report = build_indexability_report(games, sitemap_urls, base_url)

    non_indexable = next((game for game in games if indexability_reasons(game)), None)
    if non_indexable is not None:
        slug = str(non_indexable.get("slug") or "").strip()
        page_status, page_body = _request(base_url, f"/games/{slug}", timeout_seconds, "text/html")
        if page_status != 200 or b'content="noindex, follow"' not in page_body:
            raise ValueError(
                f"non-indexable production game must remain HTTP 200 with noindex, follow: slug={slug}, status={page_status}"
            )
        report["noindex_sample"] = slug

    missing_status, _ = _request(base_url, MISSING_GAME_PATH, timeout_seconds, "text/html")
    if missing_status != 404:
        raise ValueError(f"missing game must return HTTP 404; received {missing_status}")
    report["missing_game_status"] = missing_status
    return report, indexable_slugs(games)


def verify_production(base_url: str, timeout_seconds: float = 20.0) -> int:
    url = f"{base_url.rstrip('/')}{MECHANICAL_DNA_PATH}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "rule-scribe-games-production-contract/1.0",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError(f"Mechanical DNA production endpoint returned HTTP {response.status}")
        payload = json.load(response)

    return validate_mechanical_dna_payload(payload)


def verify_source_bound_glossary(base_url: str, timeout_seconds: float = 20.0) -> int:
    status, body = _request(base_url, SOURCE_BOUND_GLOSSARY_PATH, timeout_seconds, "application/json")
    if status != 200:
        raise RuntimeError(f"source-bound glossary endpoint returned HTTP {status}")
    return validate_source_bound_glossary_payload(json.loads(body))


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify canonical production API contracts")
    parser.add_argument(
        "--base-url",
        default="https://bodoge-no-mikata.vercel.app",
        help="Canonical production origin",
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--previous-indexability-state", type=Path)
    parser.add_argument("--indexability-state-output", type=Path)
    args = parser.parse_args()

    connection_count = verify_production(args.base_url, args.timeout_seconds)
    source_bound_glossary_references = verify_source_bound_glossary(args.base_url, args.timeout_seconds)
    auth_status = verify_anonymous_catalog_patch(args.base_url, args.timeout_seconds)
    indexability, current_slugs = verify_search_indexability(args.base_url, args.timeout_seconds)
    indexability.update(compare_indexability_state(current_slugs, args.previous_indexability_state))

    if args.indexability_state_output is not None:
        write_indexability_state(args.indexability_state_output, current_slugs)

    print(
        "Production API contracts: OK "
        f"(mechanical_dna_connections={connection_count}, "
        f"source_bound_glossary_references={source_bound_glossary_references}, "
        f"anonymous_catalog_patch={auth_status})"
    )
    print(json.dumps({"search_indexability": indexability}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
