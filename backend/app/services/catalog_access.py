import logging
from typing import Any

import anyio

from app.core import supabase
from app.core.settings import settings

logger = logging.getLogger("catalog.access")


async def get_catalog_editor_role(user_id: str | None) -> str | None:
    """Return an explicit catalog role; missing server credentials fail closed."""
    user_id = str(user_id or "").strip()
    if not user_id or not settings.supabase_key or supabase.is_local():
        return None

    def _q() -> str | None:
        rows = (
            supabase._get_client()
            .table("catalog_editors")
            .select("role")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        role = str(rows[0].get("role") or "").strip()
        return role if role in {"editor", "admin"} else None

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
    """Write metadata-only audit evidence without request bodies or tokens."""
    if not settings.supabase_key or supabase.is_local():
        return

    payload = {
        "editor_user_id": editor_user_id,
        "game_id": game.get("id"),
        "slug": slug,
        "action": action,
        "changed_fields": sorted(set(changed_fields)),
    }

    def _q() -> None:
        supabase._get_client().table("catalog_mutation_audit").insert(payload).execute()

    try:
        await anyio.to_thread.run_sync(_q)
    except Exception:
        # The catalog mutation has already succeeded. Preserve availability while
        # making audit failure visible to operations rather than leaking payloads.
        logger.exception("catalog_mutation_audit_failed", extra={"slug": slug, "action": action})
