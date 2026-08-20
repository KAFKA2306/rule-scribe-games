import re
import unicodedata
from collections import defaultdict
from typing import Any

_TITLE_FIELDS = ("title", "title_ja", "title_en")


def _normalize_title(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold().strip()
    return re.sub(r"[^\w]+", "", normalized, flags=re.UNICODE)


def audit_title_work_coherence(
    games: list[dict[str, Any]],
    aliases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Report title fields whose explicit alias bindings do not identify one work.

    The audit is intentionally fail-closed: titles with no explicit alias binding or
    bindings to multiple works are reported as review_required instead of being
    guessed into a work.
    """
    game_work_by_id = {
        str(game.get("id")): str(game.get("work_id"))
        for game in games
        if game.get("id") and game.get("work_id")
    }

    works_by_title: dict[str, set[str]] = defaultdict(set)
    for alias in aliases:
        game_id = str(alias.get("game_id") or "")
        normalized = _normalize_title(str(alias.get("title") or ""))
        work_id = game_work_by_id.get(game_id)
        if normalized and work_id:
            works_by_title[normalized].add(work_id)

    findings: list[dict[str, Any]] = []
    for game in games:
        game_id = str(game.get("id") or "")
        work_id = str(game.get("work_id") or "")
        if not game_id or not work_id:
            continue

        for field in _TITLE_FIELDS:
            raw_value = game.get(field)
            if not raw_value:
                continue
            normalized = _normalize_title(str(raw_value))
            bound_works = works_by_title.get(normalized, set())

            if bound_works == {work_id}:
                continue

            if work_id in bound_works and len(bound_works) > 1:
                status = "review_required"
                reason = "title_alias_bound_to_multiple_works"
            elif bound_works:
                status = "identity_conflict"
                reason = "title_bound_to_different_work"
            else:
                status = "review_required"
                reason = "title_has_no_verified_alias_binding"

            findings.append(
                {
                    "game_id": game_id,
                    "slug": game.get("slug"),
                    "work_id": work_id,
                    "field": field,
                    "value": raw_value,
                    "status": status,
                    "reason": reason,
                    "bound_work_ids": sorted(bound_works),
                }
            )

    return findings
