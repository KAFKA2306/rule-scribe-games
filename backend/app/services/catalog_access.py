import logging
from typing import Any

import anyio

from app.core import supabase
from app.core.settings import settings

logger = logging.getLogger("catalog.access")


async def get_catalog_editor_role(user_id: str | None) -> str | None:
    """Return an explicit active catalog role; missing server credentials fail closed."""
    user_id = str(user_id or "").strip()
    if not user_id or not settings.supabase_key or supabase.is_local():
        return None

    def _q() -> str | None:
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
        role = str(rows[0].get("role") or "").strip()
        return role if role in {"owner", "editor"} else None

    try:
        return await anyio.to_thread.run_sync(_q)
    except Exception:
        logger.exception("catalog_editor_lookup_failed")
        return None


async def record_catalog_mutation(
    *,
    editor_user_id: str,
    game: dict[str, Any],
    slug: str,
    action: str,
    changed_fields: list[str],
) -> None:
    """Write metadata-only audit evidence using the production audit schema."""
    if not settings.supabase_key or supabase.is_local():
        return

    payload = {
        "actor_user_id": editor_user_id,
        "game_slug": slug,
        "action": action,
        "changed_fields": sorted(set(changed_fields)),
        "outcome": "succeeded",
    }

    def _q() -> None:
        supabase._get_client().table("catalog_mutation_audit").insert(payload).execute()

    try:
        await anyio.to_thread.run_sync(_q)
    except Exception:
        logger.exception("catalog_mutation_audit_failed", extra={"slug": slug, "action": action})
