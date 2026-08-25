from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
USER_AGENT = "rule-scribe-games-ruleops-candidates/1.0"


@dataclass(frozen=True)
class Candidate:
    slug: str
    title: str
    view_count: int
    search_count: int
    has_affiliate_path: bool
    identity_status: str
    source_url: str | None
    source_trust: str
    content_review_status: str
    has_active_source_bound_ruleset: bool | None
    has_legacy_rules_content: bool | None
    triage_state: str
    blocker_reason: str | None
    read_error: str | None = None


def _get_json(url: str, timeout_seconds: float) -> Any:
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError(f"GET {url} returned HTTP {response.status}")
        return json.load(response)


def _active_source_bound(ruleset_payload: dict[str, Any]) -> bool:
    return any(
        bool(item.get("is_active", True))
        and item.get("status") == "active"
        and item.get("verification_status") in {"source_bound", "verified"}
        for item in ruleset_payload.get("rulesets", [])
        if isinstance(item, dict)
    )


def _affiliate_present(game: dict[str, Any]) -> bool:
    if game.get("amazon_url"):
        return True
    affiliate_urls = game.get("affiliate_urls")
    return isinstance(affiliate_urls, dict) and any(bool(value) for value in affiliate_urls.values())


def _triage(
    game: dict[str, Any],
    has_source_bound: bool | None,
    read_error: str | None,
) -> tuple[str, str | None]:
    if read_error:
        return "blocked", "production_read_failed"
    if has_source_bound:
        return "already_source_bound", None
    if game.get("identity_status") != "verified":
        return "needs_review", "identity_not_verified"
    if not game.get("source_url") or game.get("source_trust") not in {
        "official_publisher",
        "authorized_partner",
    }:
        return "needs_review", "primary_source_not_bound"
    return "source_triage", None


def build_candidate(
    game: dict[str, Any],
    *,
    has_source_bound: bool | None,
    has_legacy_rules_content: bool | None,
    read_error: str | None = None,
) -> Candidate:
    triage_state, blocker_reason = _triage(game, has_source_bound, read_error)
    return Candidate(
        slug=str(game.get("slug") or ""),
        title=str(game.get("title_ja") or game.get("title") or game.get("slug") or ""),
        view_count=int(game.get("view_count") or 0),
        search_count=int(game.get("search_count") or 0),
        has_affiliate_path=_affiliate_present(game),
        identity_status=str(game.get("identity_status") or "unverified"),
        source_url=game.get("source_url"),
        source_trust=str(game.get("source_trust") or "unknown"),
        content_review_status=str(game.get("content_review_status") or "unknown"),
        has_active_source_bound_ruleset=has_source_bound,
        has_legacy_rules_content=has_legacy_rules_content,
        triage_state=triage_state,
        blocker_reason=blocker_reason,
        read_error=read_error,
    )


def candidate_sort_key(candidate: Candidate) -> tuple[int, int, int, str]:
    return (
        -candidate.view_count,
        -int(candidate.has_affiliate_path),
        -candidate.search_count,
        candidate.slug,
    )


def _fetch_catalog(base_url: str, timeout_seconds: float, page_size: int = 100) -> list[dict[str, Any]]:
    games: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urlencode({"limit": page_size, "offset": offset, "sort": "popular"})
        payload = _get_json(f"{base_url.rstrip('/')}/api/games?{query}", timeout_seconds)
        page = payload.get("games", [])
        if not isinstance(page, list):
            raise ValueError("/api/games response must contain a games array")
        games.extend(item for item in page if isinstance(item, dict) and item.get("slug"))
        total = int(payload.get("total") or 0)
        offset += len(page)
        if not page or offset >= total:
            return games


def _fetch_state(base_url: str, slug: str, timeout_seconds: float) -> tuple[bool, bool]:
    escaped_slug = quote(slug, safe="")
    detail = _get_json(f"{base_url.rstrip('/')}/api/games/{escaped_slug}", timeout_seconds)
    rulesets = _get_json(f"{base_url.rstrip('/')}/api/games/{escaped_slug}/rule-sets", timeout_seconds)
    return _active_source_bound(rulesets), bool(detail.get("rules_content"))


def generate_report(
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_seconds: float = 20.0,
    workers: int = 8,
    include_source_bound: bool = False,
) -> dict[str, Any]:
    games = _fetch_catalog(base_url, timeout_seconds)
    by_slug = {str(game["slug"]): game for game in games}
    candidates: list[Candidate] = []

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_to_slug = {
            executor.submit(_fetch_state, base_url, slug, timeout_seconds): slug for slug in by_slug
        }
        for future in as_completed(future_to_slug):
            slug = future_to_slug[future]
            game = by_slug[slug]
            try:
                has_source_bound, has_legacy = future.result()
                candidate = build_candidate(
                    game,
                    has_source_bound=has_source_bound,
                    has_legacy_rules_content=has_legacy,
                )
            except Exception as exc:  # keep the rest of the batch observable
                candidate = build_candidate(
                    game,
                    has_source_bound=None,
                    has_legacy_rules_content=None,
                    read_error=f"{type(exc).__name__}: {exc}",
                )
            if include_source_bound or candidate.triage_state != "already_source_bound":
                candidates.append(candidate)

    candidates.sort(key=candidate_sort_key)
    return {
        "schema_version": "1.0",
        "source": base_url.rstrip("/"),
        "catalog_games": len(games),
        "candidate_games": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank public catalog games that still need source-bound RuleSet work"
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--include-source-bound", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = generate_report(
        args.base_url,
        timeout_seconds=args.timeout_seconds,
        workers=args.workers,
        include_source_bound=args.include_source_bound,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
