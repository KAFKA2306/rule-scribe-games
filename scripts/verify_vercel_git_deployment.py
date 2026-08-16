#!/usr/bin/env python3
"""Verify that Vercel has a READY production deployment for the expected GitHub SHA.

This script is read-only: it never creates or retries a Vercel deployment.
"""

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
TERMINAL_FAILURE_STATES = {"ERROR", "CANCELED", "CANCELLED", "BLOCKED"}
READY_STATE = "READY"


@dataclass(frozen=True)
class DeploymentMatch:
    deployment_id: str
    url: str | None
    state: str
    commit_sha: str


def _deployment_state(deployment: dict) -> str:
    return str(deployment.get("state") or deployment.get("readyState") or "UNKNOWN").upper()


def find_deployment_for_sha(payload: dict, expected_sha: str) -> DeploymentMatch | None:
    """Return the newest production deployment for the exact GitHub commit SHA."""
    deployments = payload.get("deployments") or []
    for deployment in deployments:
        meta = deployment.get("meta") or {}
        commit_sha = str(meta.get("githubCommitSha") or "")
        if commit_sha != expected_sha:
            continue
        if deployment.get("target") not in (None, "production"):
            continue
        return DeploymentMatch(
            deployment_id=str(deployment.get("uid") or deployment.get("id") or ""),
            url=deployment.get("url"),
            state=_deployment_state(deployment),
            commit_sha=commit_sha,
        )
    return None


def fetch_production_deployments(*, token: str, team_id: str, project_id: str, limit: int = 20) -> dict:
    query = urlencode(
        {
            "teamId": team_id,
            "projectId": project_id,
            "target": "production",
            "limit": str(limit),
        }
    )
    request = Request(
        f"{API_BASE}/v6/deployments?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed Vercel API origin
        return json.load(response)


def append_summary(message: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def verify(*, token: str, team_id: str, project_id: str, expected_sha: str, timeout_seconds: int, poll_seconds: int) -> DeploymentMatch:
    deadline = time.monotonic() + timeout_seconds
    last_state = "not-found"
    last_error: Exception | None = None

    while True:
        try:
            payload = fetch_production_deployments(token=token, team_id=team_id, project_id=project_id)
            last_error = None
            match = find_deployment_for_sha(payload, expected_sha)
            if match:
                last_state = match.state
                if match.state == READY_STATE:
                    return match
                if match.state in TERMINAL_FAILURE_STATES:
                    raise RuntimeError(
                        f"Vercel production deployment {match.deployment_id} for {expected_sha} ended in {match.state}"
                    )
        except RuntimeError:
            raise
        except Exception as exc:  # network/API failure: retry only read checks, never deployment creation
            last_error = exc
            last_state = "api-unavailable"

        if time.monotonic() >= deadline:
            detail = f"; last API error: {last_error}" if last_error else ""
            raise TimeoutError(
                f"Vercel production deployment for {expected_sha} was not READY within "
                f"{timeout_seconds}s (last state: {last_state}){detail}"
            )
        time.sleep(poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--project-id", default=os.getenv("VERCEL_PROJECT_ID"))
    parser.add_argument("--team-id", default=os.getenv("VERCEL_ORG_ID"))
    parser.add_argument("--token", default=os.getenv("VERCEL_TOKEN"))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--poll-seconds", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [name for name, value in (("project-id", args.project_id), ("team-id", args.team_id), ("token", args.token)) if not value]
    if missing:
        print("Missing required Vercel verification inputs: " + ", ".join(missing), file=sys.stderr)
        return 2

    try:
        match = verify(
            token=args.token,
            team_id=args.team_id,
            project_id=args.project_id,
            expected_sha=args.sha,
            timeout_seconds=max(1, args.timeout_seconds),
            poll_seconds=max(1, args.poll_seconds),
        )
    except Exception as exc:
        message = f"### Vercel production verification: FAILED\n\nExpected GitHub SHA: `{args.sha}`\n\n{exc}"
        append_summary(message)
        print(str(exc), file=sys.stderr)
        return 1

    deployment_url = f"https://{match.url}" if match.url else "(URL unavailable)"
    message = (
        "### Vercel production verification: READY\n\n"
        f"- GitHub SHA: `{match.commit_sha}`\n"
        f"- Deployment: `{match.deployment_id}`\n"
        f"- URL: {deployment_url}\n"
        "- Deployment source: not asserted by this verifier"
    )
    append_summary(message)
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
