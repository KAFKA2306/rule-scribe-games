import logging
from datetime import UTC, datetime
from typing import Any

import anyio

from app.core import supabase
from app.services.identity_coherence import audit_title_work_coherence

logger = logging.getLogger("agents.game_service")
_TITLE_FIELDS = ("title", "title_ja", "title_en")


class GameIdentityConflictError(ValueError):
    """Raised when a mutation cannot be tied to one verified canonical work."""


async def _load_identity_coherence_context() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if supabase.is_local():
        raise GameIdentityConflictError("Title identity changes require verified alias bindings")

    def _q() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        client = supabase._get_client()
        games = client.table("games").select("id,slug,work_id,title,title_ja,title_en").execute().data
        aliases = client.table("game_title_aliases").select("game_id,title").execute().data
        return games, aliases

    return await anyio.to_thread.run_sync(_q)


async def _load_source_work_bindings(source_url: str) -> set[str]:
    if supabase.is_local():
        raise GameIdentityConflictError("Source URL changes require canonical evidence bindings")

    def _q() -> set[str]:
        client = supabase._get_client()
        source_rows = client.table("evidence_sources").select("source_id").eq("url", source_url).execute().data
        source_ids = sorted({str(row.get("source_id") or "") for row in source_rows if row.get("source_id")})
        if not source_ids:
            return set()

        binding_rows = (
            client.table("evidence_bindings")
            .select("claim_id")
            .in_("source_id", source_ids)
            .eq("relation", "supports")
            .execute()
            .data
        )
        claim_ids = sorted({str(row.get("claim_id") or "") for row in binding_rows if row.get("claim_id")})
        if not claim_ids:
            return set()

        claim_rows = (
            client.table("claims")
            .select("claim_id,rule_set_id")
            .in_("claim_id", claim_ids)
            .eq("lifecycle_status", "accepted")
            .execute()
            .data
        )
        rule_set_ids = sorted({str(row.get("rule_set_id") or "") for row in claim_rows if row.get("rule_set_id")})
        if not rule_set_ids:
            return set()

        rule_set_rows = client.table("rule_sets").select("id,game_id").in_("id", rule_set_ids).execute().data
        game_ids = sorted({str(row.get("game_id") or "") for row in rule_set_rows if row.get("game_id")})
        if not game_ids:
            return set()

        game_rows = client.table("games").select("id,work_id").in_("id", game_ids).execute().data
        return {str(row.get("work_id") or "") for row in game_rows if row.get("work_id")}

    return await anyio.to_thread.run_sync(_q)


async def _validate_manual_source_update(game: dict[str, Any], safe_updates: dict[str, Any]) -> None:
    if "source_url" not in safe_updates or safe_updates["source_url"] == game.get("source_url"):
        return

    source_url = str(safe_updates.get("source_url") or "").strip()
    if not source_url:
        return

    work_id = str(game.get("work_id") or "")
    source_work_ids = await _load_source_work_bindings(source_url)
    if source_work_ids != {work_id}:
        if not source_work_ids:
            reason = "source_unbound"
        elif work_id not in source_work_ids:
            reason = "source_bound_to_another_work"
        else:
            reason = "source_bound_to_multiple_works"
        raise GameIdentityConflictError(f"Manual source URL update requires reviewed evidence binding: {reason}")


async def _validate_manual_title_update(
    game: dict[str, Any],
    merged: dict[str, Any],
    safe_updates: dict[str, Any],
) -> None:
    changed_fields = {
        field for field in _TITLE_FIELDS if field in safe_updates and safe_updates[field] != game.get(field)
    }
    if not changed_fields:
        return

    games, aliases = await _load_identity_coherence_context()
    game_id = str(game.get("id") or "")
    candidate = {key: merged.get(key) for key in ("id", "slug", "work_id", *_TITLE_FIELDS)}
    catalog = [candidate if str(row.get("id") or "") == game_id else row for row in games]
    if not any(str(row.get("id") or "") == game_id for row in games):
        catalog.append(candidate)

    findings = [
        finding
        for finding in audit_title_work_coherence(catalog, aliases)
        if str(finding.get("game_id") or "") == game_id and finding.get("field") in changed_fields
    ]
    if findings:
        reasons = ", ".join(sorted({str(finding["reason"]) for finding in findings}))
        raise GameIdentityConflictError(f"Manual title update requires reviewed identity evidence: {reasons}")


class GameService:
    def __init__(self):
        self.use_local = True
        try:
            supabase._get_client()
            self.use_local = False
            logger.info("Supabase connected. Using cloud DB.")
        except Exception:
            logger.warning("Supabase not configured. Falling back to local SQLite.")
            from app.core import local_db

            local_db.init_db()

    async def get_game_by_slug(self, slug: str) -> dict[str, Any] | None:
        return await supabase.get_by_slug(slug)

    async def update_game_manual(self, slug: str, updates: dict[str, Any]) -> dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise ValueError(f"Game not found for slug: {slug}")

        protected = {"id", "slug", "work_id", "identity_status"}
        safe_updates = {key: value for key, value in updates.items() if key not in protected}
        merged = {**game, **safe_updates}
        await _validate_manual_title_update(game, merged, safe_updates)
        await _validate_manual_source_update(game, safe_updates)
        merged["updated_at"] = datetime.now(UTC).isoformat()
        out = await supabase.upsert(merged)
        if not out:
            raise RuntimeError(f"Update failed for game: {slug}")
        return out[0]
