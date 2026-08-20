from typing import Any

_METADATA_FIELDS = (
    "min_players",
    "max_players",
    "play_time",
    "min_age",
    "published_year",
)


def audit_metadata_source_work_coherence(
    games: list[dict[str, Any]],
    source_work_ids_by_url: dict[str, set[str]],
) -> list[dict[str, Any]]:
    """Report metadata whose source cannot be tied uniquely to the game's work.

    This audit does not claim that a source supports each individual metadata value.
    It only checks the existing source-to-work evidence boundary and fails closed when
    metadata is present without a source uniquely bound to the current canonical work.
    """
    findings: list[dict[str, Any]] = []

    for game in games:
        game_id = str(game.get("id") or "")
        work_id = str(game.get("work_id") or "")
        if not game_id or not work_id:
            continue

        populated_fields = [field for field in _METADATA_FIELDS if game.get(field) is not None]
        if not populated_fields:
            continue

        source_url = str(game.get("source_url") or "").strip()
        if not source_url:
            status = "review_required"
            reason = "metadata_source_missing"
            bound_work_ids: set[str] = set()
        else:
            bound_work_ids = source_work_ids_by_url.get(source_url, set())
            if bound_work_ids == {work_id}:
                continue
            if not bound_work_ids:
                status = "review_required"
                reason = "metadata_source_unbound"
            elif work_id not in bound_work_ids:
                status = "identity_conflict"
                reason = "metadata_source_bound_to_different_work"
            else:
                status = "review_required"
                reason = "metadata_source_bound_to_multiple_works"

        findings.append(
            {
                "game_id": game_id,
                "slug": game.get("slug"),
                "work_id": work_id,
                "fields": populated_fields,
                "source_url": source_url or None,
                "status": status,
                "reason": reason,
                "bound_work_ids": sorted(bound_work_ids),
            }
        )

    return findings
