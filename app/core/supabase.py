from typing import List, Dict, Any, Optional
import anyio
from supabase import create_client
from app.core.settings import settings
from app.utils.slugify import slugify

_client = create_client(settings.supabase_url, settings.supabase_key)
_TABLE = "games"


async def search(query: str) -> List[Dict[str, Any]]:
    def _q():
        return (
            _client.table(_TABLE)
            .select("*")
            .or_(f"title.ilike.*{query}*,description.ilike.*{query}*")
            .execute()
            .data
        )

    return await anyio.to_thread.run_sync(_q)


async def upsert(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    def _q():
        if data.get("title"):
            data["slug"] = slugify(data["title"])
        key = "source_url" if data.get("source_url") else "slug"
        return _client.table(_TABLE).upsert(data, on_conflict=key).execute().data

    return await anyio.to_thread.run_sync(_q)


async def get_by_id(game_id: int) -> Optional[Dict[str, Any]]:
    def _q():
        r = _client.table(_TABLE).select("*").eq("id", game_id).execute().data
        return r[0] if r else None

    return await anyio.to_thread.run_sync(_q)


async def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    def _q():
        r = _client.table(_TABLE).select("*").eq("slug", slug).execute().data
        return r[0] if r else None

    return await anyio.to_thread.run_sync(_q)


async def list_recent(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    def _q():
        return (
            _client.table(_TABLE)
            .select("*")
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
            .data
        )

    return await anyio.to_thread.run_sync(_q)


async def increment_view_count(game_id: str) -> None:
    def _q():
        r = _client.table(_TABLE).select("view_count").eq("id", game_id).execute().data
        if r:
            _client.table(_TABLE).update(
                {"view_count": (r[0].get("view_count") or 0) + 1}
            ).eq("id", game_id).execute()

    await anyio.to_thread.run_sync(_q)
