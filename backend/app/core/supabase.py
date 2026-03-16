from typing import Any

import anyio
from supabase import create_client

from app.core.settings import settings
from app.utils.slugify import slugify

_TABLE = "games"

try:
    if settings.supabase_url and settings.supabase_key:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    else:
        print("CRITICAL: Supabase client not initialized due to missing settings!")
        _client = None
except Exception as e:
    print(f"CRITICAL: Failed to initialize Supabase client: {e}")
    _client = None


async def search(query: str) -> list[dict[str, Any]]:
    def _q():
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

    return await anyio.to_thread.run_sync(_q)


_URL_FIELDS = [
    "bgg_url",
    "bga_url",
    "official_url",
    "image_url",
    "amazon_url",
    "audio_url",
    "source_url",
]


async def upsert(data: dict[str, Any]) -> list[dict[str, Any]]:
    def _q():
        if data.get("title"):
            data["slug"] = slugify(str(data["title"]))
        for f in _URL_FIELDS:
            if data.get(f) == "":
                data[f] = None
        if data.get("id"):
            key = "id"
        else:
            key = "source_url" if data.get("source_url") else "slug"
        return _client.table(_TABLE).upsert(data, on_conflict=key).execute().data

    return await anyio.to_thread.run_sync(_q)


async def get_by_id(game_id: int) -> dict[str, Any] | None:
    def _q():
        r = _client.table(_TABLE).select("*").eq("id", game_id).execute().data
        return r[0] if r else None

    return await anyio.to_thread.run_sync(_q)


async def get_by_slug(slug: str) -> dict[str, Any] | None:
    def _q():
        r = _client.table(_TABLE).select("*").eq("slug", slug).execute().data
        return r[0] if r else None

    return await anyio.to_thread.run_sync(_q)


async def list_recent(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
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
            count = r[0].get("view_count")
            current = int(count) if count is not None else 0
            _client.table(_TABLE).update({"view_count": current + 1}).eq("id", game_id).execute()

    await anyio.to_thread.run_sync(_q)
