import anyio
import logging
from typing import Any, Dict, List, Optional
from app.core import local_db
from app.core.settings import settings
from app.utils.slugify import slugify

logger = logging.getLogger("core.db_provider")
_TABLE = "games"

_client = None
try:
    from supabase import create_client
    if settings.supabase_url and settings.supabase_key:
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Cloud DB (Supabase) provider initialized.")
    else:
        logger.warning("Supabase credentials missing. Local-first mode active.")
except Exception as e:
    logger.warning(f"Supabase client init failed ({e}). Local-first mode active.")

def is_local() -> bool:
    return _client is None

def _get_client():
    if _client is None:
        raise RuntimeError("Supabase not configured. Using Local-First.")
    return _client

async def search(query: str) -> List[Dict[str, Any]]:
    if is_local():
        # Search the entire local DB
        res = local_db.list_recent(limit=10000)
        q = query.lower()
        return [g for g in res["data"] if q in (g.get("title") or "").lower() or q in (g.get("title_ja") or "").lower()]
    
    def _q():
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        return _get_client().table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data
    return await anyio.to_thread.run_sync(_q)

async def list_recent(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    if is_local():
        return local_db.list_recent(limit=limit, offset=offset)
    
    def _q():
        res = (
            _get_client().table(_TABLE)
            .select("*", count="exact")
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return {"data": res.data, "total": res.count}
    return await anyio.to_thread.run_sync(_q)

async def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    if is_local():
        return local_db.get_by_slug(slug)
    
    def _q():
        r = _get_client().table(_TABLE).select("*").eq("slug", slug).execute().data
        return r[0] if r else None
    return await anyio.to_thread.run_sync(_q)

async def upsert_game(game_data: Dict[str, Any]) -> Dict[str, Any]:
    if is_local():
        local_db.upsert_game(game_data)
        return game_data
    
    def _q():
        return _get_client().table(_TABLE).upsert(game_data).execute().data[0]
    return await anyio.to_thread.run_sync(_q)

async def increment_view_count(game_id: str) -> None:
    if is_local(): return
    def _q():
        r = _get_client().table(_TABLE).select("view_count").eq("id", game_id).execute().data
        if r:
            count = r[0].get("view_count") or 0
            _get_client().table(_TABLE).update({"view_count": count + 1}).eq("id", game_id).execute()
    await anyio.to_thread.run_sync(_q)

# Legacy alias
async def upsert(data: dict[str, Any]) -> List[dict[str, Any]]:
    return [await upsert_game(data)]

async def list_for_sitemap() -> list[dict[str, Any]]:
    if is_local():
        res = local_db.list_recent(limit=50000)
        return [{"slug": g["slug"], "title": g["title"], "updated_at": g["updated_at"], "image_url": g.get("image_url")} for g in res["data"]]
    
    def _q():
        return _get_client().table(_TABLE).select("slug, title, updated_at, image_url").execute().data
    return await anyio.to_thread.run_sync(_q)
