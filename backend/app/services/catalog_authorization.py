import logging
from typing import Literal

import anyio

from app.core import supabase

logger = logging.getLogger("security.catalog")
CatalogAction = Literal["manual_update", "regenerate"]
AuditOutcome = Literal["allowed", "denied", "succeeded", "not_found", "failed"]


async def get_catalog_editor_role(user_id: str) -> str | None:
    """Resolve a verified Auth user against the server-only catalog editor allowlist."""
    if not user_id or supabase.is_local():
        return None

    def _q():
        rows = (
            supabase._get_client()
            .table("catalog_editors")
            .select("role")
            .eq("user_id", user_id)
            .eq("active", True)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        role = str(rows[0].get("role") or "")
        return role if role in {"owner", "editor"} else None

    return await anyio.to_thread.run_sync(_q)


async def record_catalog_mutation_audit(
    *,
    actor_user_id: str,
    game_slug: str,
    action: CatalogAction,
    changed_fields: list[str],
    outcome: AuditOutcome,
) -> None:
    """Persist secret-free catalog authorization/mutation evidence before returning."""
    if not actor_user_id or supabase.is_local():
        raise RuntimeError("Catalog mutation audit requires configured server-side Supabase access")

    payload = {
        "actor_user_id": actor_user_id,
        "game_slug": game_slug,
        "action": action,
        "changed_fields": sorted(set(changed_fields)),
        "outcome": outcome,
    }

    def _q():
        supabase._get_client().table("catalog_mutation_audit").insert(payload).execute()

    await anyio.to_thread.run_sync(_q)
    logger.info(
        "catalog_mutation_audit",
        extra={
            "actor_user_id": actor_user_id,
            "game_slug": game_slug,
            "action": action,
            "changed_fields": payload["changed_fields"],
            "outcome": outcome,
        },
    )
