from __future__ import annotations

import argparse
from typing import Any

import httpx

from app.scripts.curated_game_fast_path_v2 import (
    DEFAULT_BASE_URL,
    generate_artifacts,
    verify_frontend_release,
)
from app.scripts.curated_game_workflow import CuratedGameSpec, WorkflowError, load_all_specs

# Curated specs still own product identity and provenance. Player-facing rule/editorial
# content can move independently through the source-bound RuleSet pipeline and must not
# become a second release authority here.
MUTABLE_PLAYER_CONTENT_FIELDS = frozenset(
    {
        "description",
        "summary",
        "rules_content",
        "setup_summary",
        "gameplay_summary",
        "end_game_summary",
        "structured_data",
        "content_review_status",
    }
)


def release_catalog_contract(game: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in game.items()
        if key not in MUTABLE_PLAYER_CONTENT_FIELDS
    }


def validate_release_catalog_fields(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    for key, expected_value in release_catalog_contract(expected).items():
        # The public response intentionally omits some storage-only fields.
        if key not in actual:
            continue
        if actual[key] != expected_value:
            raise WorkflowError(f"production catalog mismatch at game.{key}")


def verify_catalog_release_live(spec: CuratedGameSpec, base_url: str) -> None:
    base = base_url.rstrip("/")
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        response = client.get(f"{base}/api/games/{spec.slug}")
        if response.status_code != 200:
            raise WorkflowError(f"production API failed for {spec.slug}: HTTP {response.status_code}")
        payload = response.json()

    if payload.get("slug") != spec.slug:
        raise WorkflowError(f"production API returned the wrong slug for {spec.slug}")
    if payload.get("source_url") != spec.source.url:
        raise WorkflowError(f"production API source provenance mismatch for {spec.slug}")
    if not payload.get("work_id"):
        raise WorkflowError(f"production API record has no canonical work_id for {spec.slug}")
    validate_release_catalog_fields(spec.game, payload)


def verify_release(specs: list[CuratedGameSpec], base_url: str) -> None:
    generate_artifacts(specs)
    verify_frontend_release(specs, base_url)
    for spec in specs:
        verify_catalog_release_live(spec, base_url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    verify_release(load_all_specs(), args.base_url)


if __name__ == "__main__":
    main()
