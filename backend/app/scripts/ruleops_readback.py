from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
USER_AGENT = "rule-scribe-games-ruleops-readback/1.0"


@dataclass(frozen=True)
class ReadbackResult:
    slug: str
    ok: bool
    game_http: int | None
    ruleset_http: int | None
    page_http: int | None
    identity_status: str | None
    active_source_bound_rulesets: int | None
    legacy_rules_content_present: bool | None
    affiliate_path_present: bool | None
    view_count: int | None
    expected_text_missing: list[str]
    error: str | None = None


def _get(url: str, timeout_seconds: float, *, accept: str) -> tuple[int, str, str]:
    request = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.headers.get("Content-Type", ""), body


def _get_json(url: str, timeout_seconds: float) -> tuple[int, dict[str, Any]]:
    status, _, body = _get(url, timeout_seconds, accept="application/json")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError(f"GET {url} must return a JSON object")
    return status, payload


def _affiliate_present(game: dict[str, Any]) -> bool:
    if game.get("amazon_url"):
        return True
    affiliate_urls = game.get("affiliate_urls")
    return isinstance(affiliate_urls, dict) and any(bool(value) for value in affiliate_urls.values())


def _active_source_bound_count(payload: dict[str, Any]) -> int:
    return sum(
        1
        for item in payload.get("rulesets", [])
        if isinstance(item, dict)
        and bool(item.get("is_active", True))
        and item.get("status") == "active"
        and item.get("verification_status") in {"source_bound", "verified"}
    )


def readback_game(
    base_url: str,
    slug: str,
    *,
    expected_text: list[str] | None = None,
    timeout_seconds: float = 20.0,
) -> ReadbackResult:
    escaped = quote(slug, safe="")
    root = base_url.rstrip("/")
    expected = expected_text or []
    try:
        game_status, game = _get_json(f"{root}/api/games/{escaped}", timeout_seconds)
        ruleset_status, rulesets = _get_json(
            f"{root}/api/games/{escaped}/rule-sets", timeout_seconds
        )
        page_status, _, page = _get(
            f"{root}/games/{escaped}", timeout_seconds, accept="text/html"
        )
        missing = [text for text in expected if text not in page]
        active_count = _active_source_bound_count(rulesets)
        ok = (
            game_status == 200
            and ruleset_status == 200
            and page_status == 200
            and active_count >= 1
            and not bool(game.get("rules_content"))
            and not missing
        )
        return ReadbackResult(
            slug=slug,
            ok=ok,
            game_http=game_status,
            ruleset_http=ruleset_status,
            page_http=page_status,
            identity_status=str(game.get("identity_status") or "unknown"),
            active_source_bound_rulesets=active_count,
            legacy_rules_content_present=bool(game.get("rules_content")),
            affiliate_path_present=_affiliate_present(game),
            view_count=int(game.get("view_count") or 0),
            expected_text_missing=missing,
        )
    except Exception as exc:
        return ReadbackResult(
            slug=slug,
            ok=False,
            game_http=None,
            ruleset_http=None,
            page_http=None,
            identity_status=None,
            active_source_bound_rulesets=None,
            legacy_rules_content_present=None,
            affiliate_path_present=None,
            view_count=None,
            expected_text_missing=expected,
            error=f"{type(exc).__name__}: {exc}",
        )


def generate_report(
    slugs: list[str],
    *,
    expected_text: dict[str, list[str]] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = 20.0,
    workers: int = 8,
) -> dict[str, Any]:
    expected_map = expected_text or {}
    results: list[ReadbackResult] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(
                readback_game,
                base_url,
                slug,
                expected_text=expected_map.get(slug, []),
                timeout_seconds=timeout_seconds,
            ): slug
            for slug in slugs
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item.slug)
    return {
        "schema_version": "1.0",
        "source": base_url.rstrip("/"),
        "games": len(results),
        "passed": sum(1 for item in results if item.ok),
        "failed": sum(1 for item in results if not item.ok),
        "results": [asdict(item) for item in results],
    }


def _load_expected(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected-text file must be a JSON object mapping slug to string arrays")
    result: dict[str, list[str]] = {}
    for slug, values in payload.items():
        if not isinstance(slug, str) or not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise ValueError("expected-text file must map string slugs to arrays of strings")
        result[slug] = values
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch production readback for source-bound games")
    parser.add_argument("slugs", nargs="+")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--expected-text-json", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = generate_report(
        args.slugs,
        expected_text=_load_expected(args.expected_text_json),
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        workers=args.workers,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
