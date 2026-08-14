#!/usr/bin/env python3
"""Read-only Vercel deployment-budget preflight for production workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.vercel.com"
DEFAULT_LIMIT = 100
WINDOW_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class BudgetDecision:
    state: str
    deployment_count: int | None
    latest_production_sha: str | None
    reason: str


def _deployments(payload: dict) -> list[dict]:
    value = payload.get("deployments") or []
    return value if isinstance(value, list) else []


def latest_ready_production_sha(payload: dict) -> str | None:
    for deployment in _deployments(payload):
        state = str(deployment.get("state") or deployment.get("readyState") or "").upper()
        if deployment.get("target") != "production" or state != "READY":
            continue
        meta = deployment.get("meta") or {}
        sha = meta.get("githubCommitSha")
        if sha:
            return str(sha)
    return None


def decide_budget(
    *,
    team_payload: dict,
    project_payload: dict,
    expected_sha: str,
    threshold: int = DEFAULT_LIMIT,
) -> BudgetDecision:
    latest_sha = latest_ready_production_sha(project_payload)
    if latest_sha == expected_sha:
        return BudgetDecision("current", len(_deployments(team_payload)), latest_sha, "production already matches current main SHA")

    count = len(_deployments(team_payload))
    # The API request is capped at `threshold`. Reaching the cap is enough to
    # know that another deployment would exceed/press the observed Free limit.
    if count >= threshold:
        return BudgetDecision(
            "quota_saturated",
            count,
            latest_sha,
            f"at least {count} team deployments were observed in the last 24 hours",
        )

    return BudgetDecision("deployable", count, latest_sha, f"{count} team deployments observed in the last 24 hours")


def fetch_json(*, token: str, path: str, params: dict[str, str | int]) -> dict:
    query = urlencode(params)
    request = Request(
        f"{API_BASE}{path}?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed Vercel API origin
        return json.load(response)


def inspect_budget(*, token: str, team_id: str, project_id: str, expected_sha: str, now_ms: int | None = None) -> BudgetDecision:
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    since_ms = now_ms - WINDOW_SECONDS * 1000
    team_payload = fetch_json(
        token=token,
        path="/v6/deployments",
        params={"teamId": team_id, "since": since_ms, "limit": DEFAULT_LIMIT},
    )
    project_payload = fetch_json(
        token=token,
        path="/v6/deployments",
        params={"teamId": team_id, "projectId": project_id, "target": "production", "limit": 20},
    )
    return decide_budget(team_payload=team_payload, project_payload=project_payload, expected_sha=expected_sha)


def write_github_output(decision: BudgetDecision) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    if not path:
        return
    values = {
        "state": decision.state,
        "deployment_count": "unknown" if decision.deployment_count is None else str(decision.deployment_count),
        "latest_production_sha": decision.latest_production_sha or "",
        "reason": decision.reason.replace("\n", " "),
    }
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def append_summary(decision: BudgetDecision) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("### Vercel deployment budget\n\n")
        handle.write(f"- State: `{decision.state}`\n")
        handle.write(f"- 24h deployment count: `{decision.deployment_count if decision.deployment_count is not None else 'unknown'}`\n")
        handle.write(f"- Latest production SHA: `{decision.latest_production_sha or 'unknown'}`\n")
        handle.write(f"- Reason: {decision.reason}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--project-id", default=os.getenv("VERCEL_PROJECT_ID"))
    parser.add_argument("--team-id", default=os.getenv("VERCEL_ORG_ID"))
    parser.add_argument("--token", default=os.getenv("VERCEL_TOKEN"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [name for name, value in (("project-id", args.project_id), ("team-id", args.team_id), ("token", args.token)) if not value]
    if missing:
        decision = BudgetDecision("unknown", None, None, "missing inputs: " + ", ".join(missing))
    else:
        try:
            decision = inspect_budget(
                token=args.token,
                team_id=args.team_id,
                project_id=args.project_id,
                expected_sha=args.sha,
            )
        except Exception as exc:
            # API unavailability is not evidence that production is current or
            # that quota is available. Catch-up deployment therefore fails closed.
            decision = BudgetDecision("unknown", None, None, f"Vercel budget API unavailable: {exc}")

    write_github_output(decision)
    append_summary(decision)
    print(json.dumps(decision.__dict__, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
