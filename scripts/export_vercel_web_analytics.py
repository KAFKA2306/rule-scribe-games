#!/usr/bin/env python3
"""Export production Vercel Web Analytics into durable, privacy-safe history."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

VISITS_API_URL = "https://api.vercel.com/v1/query/web-analytics/visits/aggregate"
EVENTS_API_URL = "https://api.vercel.com/v1/query/web-analytics/events/aggregate"
AFFILIATE_EVENT_NAME = "Affiliate Outbound"
SCHEMA_VERSION = 1
ROLLING_LIMIT = 100


def normalize_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("Vercel analytics response data must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Vercel analytics rows must be objects")
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, str) or len(timestamp) < 10:
            raise ValueError("Vercel analytics row is missing timestamp")
        normalized.append(
            {
                "date": timestamp[:10],
                "pageviews": int(row.get("pageviews", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
        )
    return normalized


def normalize_event_days(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("Vercel event response data must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Vercel event rows must be objects")
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, str) or len(timestamp) < 10:
            raise ValueError("Vercel event row is missing timestamp")
        normalized.append(
            {
                "date": timestamp[:10],
                "count": int(row.get("count", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
        )
    return normalized


def normalize_visit_dimension(rows: Any, dimension: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("Vercel visit breakdown data must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Vercel visit breakdown rows must be objects")
        value = row.get(dimension)
        if value is None:
            value = ""
        normalized.append(
            {
                dimension: str(value),
                "pageviews": int(row.get("pageviews", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
        )
    return normalized


def normalize_event_dimension(rows: Any, output_key: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("Vercel event breakdown data must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Vercel event breakdown rows must be objects")
        value = row.get("eventData")
        if value is None:
            value = ""
        normalized.append(
            {
                output_key: str(value),
                "count": int(row.get("count", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
        )
    return normalized


def completed_days(rows: list[dict[str, Any]], today_utc: str) -> list[dict[str, Any]]:
    """Exclude the in-progress UTC day so persisted daily values are final."""
    return [row for row in rows if row["date"] < today_utc]


def read_existing(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"schema_version": SCHEMA_VERSION, "days": [], "affiliate_outbound_days": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported analytics history schema_version")
    if not isinstance(data.get("days"), list):
        raise ValueError("Analytics history days must be a list")
    if not isinstance(data.get("affiliate_outbound_days", []), list):
        raise ValueError("Analytics affiliate_outbound_days must be a list")
    return data


def merge_history(
    existing: dict[str, Any], fresh_days: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    for row in existing.get("days", []):
        if isinstance(row, dict) and isinstance(row.get("date"), str):
            by_date[row["date"]] = {
                "date": row["date"],
                "pageviews": int(row.get("pageviews", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
    for row in fresh_days:
        by_date[row["date"]] = row
    return [by_date[key] for key in sorted(by_date)]


def merge_event_history(
    existing: dict[str, Any], fresh_days: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    for row in existing.get("affiliate_outbound_days", []):
        if isinstance(row, dict) and isinstance(row.get("date"), str):
            by_date[row["date"]] = {
                "date": row["date"],
                "count": int(row.get("count", 0)),
                "visitors": int(row.get("visitors", 0)),
            }
    for row in fresh_days:
        by_date[row["date"]] = row
    return [by_date[key] for key in sorted(by_date)]


def fetch_aggregate(
    *,
    api_url: str,
    token: str,
    project_id: str,
    team_id: str,
    since: str,
    until: str,
    by: str,
    filter_expression: str,
    limit: int = ROLLING_LIMIT,
) -> Any:
    params = parse.urlencode(
        {
            "projectId": project_id,
            "teamId": team_id,
            "since": since,
            "until": until,
            "by": by,
            "filter": filter_expression,
            "limit": str(limit),
        }
    )
    req = request.Request(
        f"{api_url}?{params}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "rule-scribe-games-web-analytics/2",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            payload = json.load(response)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(
            f"Vercel Web Analytics API returned HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(
            f"Vercel Web Analytics API request failed: {exc.reason}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("Vercel analytics response must be an object")
    return payload.get("data")


def fetch_daily(
    *, token: str, project_id: str, team_id: str, since: str, until: str
) -> list[dict[str, Any]]:
    return normalize_rows(
        fetch_aggregate(
            api_url=VISITS_API_URL,
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
            by="day",
            filter_expression="environment eq 'production'",
        )
    )


def fetch_affiliate_daily(
    *, token: str, project_id: str, team_id: str, since: str, until: str
) -> list[dict[str, Any]]:
    return normalize_event_days(
        fetch_aggregate(
            api_url=EVENTS_API_URL,
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
            by="day",
            filter_expression=f"eventName eq '{AFFILIATE_EVENT_NAME}'",
        )
    )


def fetch_visit_breakdown(
    *,
    token: str,
    project_id: str,
    team_id: str,
    since: str,
    until: str,
    dimension: str,
) -> list[dict[str, Any]]:
    return normalize_visit_dimension(
        fetch_aggregate(
            api_url=VISITS_API_URL,
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
            by=dimension,
            filter_expression="environment eq 'production'",
        ),
        dimension,
    )


def fetch_affiliate_breakdown(
    *,
    token: str,
    project_id: str,
    team_id: str,
    since: str,
    until: str,
    property_name: str,
) -> list[dict[str, Any]]:
    return normalize_event_dimension(
        fetch_aggregate(
            api_url=EVENTS_API_URL,
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
            by=f"eventData/{property_name}",
            filter_expression=f"eventName eq '{AFFILIATE_EVENT_NAME}'",
        ),
        property_name,
    )


def write_history(
    output: Path,
    existing: dict[str, Any],
    fresh_days: list[dict[str, Any]],
    affiliate_days: list[dict[str, Any]],
    request_paths: list[dict[str, Any]],
    referrers: list[dict[str, Any]],
    affiliate_providers: list[dict[str, Any]],
    affiliate_games: list[dict[str, Any]],
    collected_at: str,
    rolling_since: str,
    rolling_until: str,
) -> None:
    result = {
        "schema_version": SCHEMA_VERSION,
        "source": VISITS_API_URL,
        "event_source": EVENTS_API_URL,
        "scope": "production pageviews plus Affiliate Outbound custom events",
        "collected_at": collected_at,
        "days": merge_history(existing, fresh_days),
        "affiliate_outbound_days": merge_event_history(existing, affiliate_days),
        "rolling_window": {
            "since": rolling_since,
            "until": rolling_until,
            "limit_per_breakdown": ROLLING_LIMIT,
            "request_paths": request_paths,
            "referrers": referrers,
            "affiliate_by_provider": affiliate_providers,
            "affiliate_by_game": affiliate_games,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def self_test() -> None:
    existing = {
        "schema_version": 1,
        "days": [
            {"date": "2026-08-18", "pageviews": 2, "visitors": 2},
            {"date": "2026-08-19", "pageviews": 3, "visitors": 2},
        ],
        "affiliate_outbound_days": [
            {"date": "2026-08-19", "count": 1, "visitors": 1},
        ],
    }
    fresh = normalize_rows(
        [
            {
                "timestamp": "2026-08-19T00:00:00.000Z",
                "pageviews": 5,
                "visitors": 4,
            },
            {
                "timestamp": "2026-08-20T00:00:00.000Z",
                "pageviews": 7,
                "visitors": 6,
            },
            {
                "timestamp": "2026-08-21T00:00:00.000Z",
                "pageviews": 1,
                "visitors": 1,
            },
        ]
    )
    fresh = completed_days(fresh, "2026-08-21")
    assert merge_history(existing, fresh) == [
        {"date": "2026-08-18", "pageviews": 2, "visitors": 2},
        {"date": "2026-08-19", "pageviews": 5, "visitors": 4},
        {"date": "2026-08-20", "pageviews": 7, "visitors": 6},
    ]

    event_days = normalize_event_days(
        [
            {"timestamp": "2026-08-19T00:00:00.000Z", "count": 2, "visitors": 2},
            {"timestamp": "2026-08-20T00:00:00.000Z", "count": 3, "visitors": 2},
            {"timestamp": "2026-08-21T00:00:00.000Z", "count": 1, "visitors": 1},
        ]
    )
    event_days = completed_days(event_days, "2026-08-21")
    assert merge_event_history(existing, event_days) == [
        {"date": "2026-08-19", "count": 2, "visitors": 2},
        {"date": "2026-08-20", "count": 3, "visitors": 2},
    ]
    assert normalize_visit_dimension(
        [{"requestPath": "/games/camel-up", "pageviews": 4, "visitors": 2}],
        "requestPath",
    ) == [{"requestPath": "/games/camel-up", "pageviews": 4, "visitors": 2}]
    assert normalize_event_dimension(
        [{"eventData": "amazon", "count": 2, "visitors": 2}], "provider"
    ) == [{"provider": "amazon", "count": 2, "visitors": 2}]
    print("web analytics exporter self-test: OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("data/analytics/web-traffic.json")
    )
    parser.add_argument("--existing", type=Path)
    parser.add_argument("--since-days", type=int, default=31)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.since_days < 1 or args.since_days > 100:
        parser.error("--since-days must be between 1 and 100")

    token = os.environ.get("VERCEL_TOKEN", "").strip()
    project_id = os.environ.get("VERCEL_PROJECT_ID", "").strip()
    team_id = os.environ.get("VERCEL_ORG_ID", "").strip()
    missing = [
        name
        for name, value in (
            ("VERCEL_TOKEN", token),
            ("VERCEL_PROJECT_ID", project_id),
            ("VERCEL_ORG_ID", team_id),
        )
        if not value
    ]
    if missing:
        raise SystemExit("Missing required environment variables: " + ", ".join(missing))

    now = datetime.now(timezone.utc)
    today_utc = now.date().isoformat()
    since = (now - timedelta(days=args.since_days)).date().isoformat()
    until = today_utc

    fresh_days = completed_days(
        fetch_daily(
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
        ),
        today_utc,
    )
    affiliate_days = completed_days(
        fetch_affiliate_daily(
            token=token,
            project_id=project_id,
            team_id=team_id,
            since=since,
            until=until,
        ),
        today_utc,
    )
    request_paths = fetch_visit_breakdown(
        token=token,
        project_id=project_id,
        team_id=team_id,
        since=since,
        until=until,
        dimension="requestPath",
    )
    referrers = fetch_visit_breakdown(
        token=token,
        project_id=project_id,
        team_id=team_id,
        since=since,
        until=until,
        dimension="referrerHostname",
    )
    affiliate_providers = fetch_affiliate_breakdown(
        token=token,
        project_id=project_id,
        team_id=team_id,
        since=since,
        until=until,
        property_name="provider",
    )
    affiliate_games = fetch_affiliate_breakdown(
        token=token,
        project_id=project_id,
        team_id=team_id,
        since=since,
        until=until,
        property_name="gameSlug",
    )

    write_history(
        args.output,
        read_existing(args.existing),
        fresh_days,
        affiliate_days,
        request_paths,
        referrers,
        affiliate_providers,
        affiliate_games,
        now.isoformat(),
        since,
        until,
    )
    print(
        "wrote "
        f"{len(fresh_days)} completed traffic day(s), "
        f"{len(affiliate_days)} affiliate day(s), and rolling breakdowns to {args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
