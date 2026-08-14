import anyio
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

from app.core import local_db
from app.core.settings import settings

logger = logging.getLogger("core.db_provider")
_TABLE = "games"
_IMAGE_BUCKET = "game-images"

# Storage objects verified against the production Supabase project on 2026-08-14.
# Keep this explicit: a missing image must not be inferred from a slug.
_STORAGE_IMAGE_OVERRIDES = {
    "splendor": "splendor.png",
    "yokohama-duel": "yokohama-duel.png",
}

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


def _normalize_lookup(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold().strip()
    return re.sub(r"[^\w]+", "", normalized, flags=re.UNICODE)


def _search_rank(game: Dict[str, Any], query: str) -> tuple[int, str]:
    q = _normalize_lookup(query)
    candidates = [
        game.get("slug"),
        game.get("title"),
        game.get("title_ja"),
        game.get("title_en"),
    ]
    normalized = [_normalize_lookup(str(value)) for value in candidates if value]
    if q and q in normalized:
        rank = 0
    elif q and any(value.startswith(q) for value in normalized):
        rank = 1
    elif q and any(q in value for value in normalized):
        rank = 2
    else:
        rank = 3
    return rank, str(game.get("title_ja") or game.get("title") or "")


def _with_canonical_storage_image(game: Dict[str, Any]) -> Dict[str, Any]:
    """Replace audited stale image references with their public Storage URL."""
    slug = str(game.get("slug") or "").strip()
    storage_name = _STORAGE_IMAGE_OVERRIDES.get(slug)
    if not storage_name or not settings.supabase_url:
        return game

    current = str(game.get("image_url") or "").strip()
    if current and "via.placeholder.com" not in current and not current.startswith("/assets/games/"):
        return game

    normalized = dict(game)
    normalized["image_url"] = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{_IMAGE_BUCKET}/{storage_name}"
    )
    return normalized


async def search(query: str) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    if is_local():
        res = local_db.list_recent(limit=10000)
        q = _normalize_lookup(query)
        rows = []
        for game in res["data"]:
            haystacks = [
                game.get("slug"),
                game.get("title"),
                game.get("title_ja"),
                game.get("title_en"),
                game.get("summary"),
                game.get("description"),
            ]
            if any(q in _normalize_lookup(str(value)) for value in haystacks if value):
                rows.append(game)
        return sorted(rows, key=lambda game: _search_rank(game, query))

    def _q():
        client = _get_client()
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        direct_rows = (
            client.table(_TABLE)
            .select("*")
            .or_(
                ",".join(
                    [
                        f'title.ilike."{term}"',
                        f'title_ja.ilike."{term}"',
                        f'title_en.ilike."{term}"',
                        f'description.ilike."{term}"',
                    ]
                )
            )
            .limit(100)
            .execute()
            .data
        )

        normalized_query = _normalize_lookup(query)
        alias_filters = [f'title.ilike."{term}"']
        if normalized_query:
            alias_filters.append(f'normalized_title.ilike."*{normalized_query}*"')
        alias_rows = (
            client.table("game_title_aliases")
            .select("game_id")
            .or_(",".join(alias_filters))
            .limit(100)
            .execute()
            .data
        )
        alias_game_ids = list(dict.fromkeys(row["game_id"] for row in alias_rows if row.get("game_id")))
        alias_games = []
        if alias_game_ids:
            alias_games = client.table(_TABLE).select("*").in_("id", alias_game_ids).execute().data

        deduped: dict[str, Dict[str, Any]] = {}
        for row in [*direct_rows, *alias_games]:
            row_id = str(row.get("id") or "")
            if row_id:
                deduped[row_id] = _with_canonical_storage_image(row)

        return sorted(deduped.values(), key=lambda game: _search_rank(game, query))

    return await anyio.to_thread.run_sync(_q)


async def list_recent(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    if is_local():
        return local_db.list_recent(limit=limit, offset=offset)

    def _q():
        res = (
            _get_client()
            .table(_TABLE)
            .select("*", count="exact")
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return {
            "data": [_with_canonical_storage_image(row) for row in res.data],
            "total": res.count,
        }

    return await anyio.to_thread.run_sync(_q)


async def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    if is_local():
        return local_db.get_by_slug(slug)

    def _q():
        rows = _get_client().table(_TABLE).select("*").eq("slug", slug).execute().data
        if rows:
            return _with_canonical_storage_image(rows[0])

        aliases = (
            _get_client()
            .table("game_slug_aliases")
            .select("game_id")
            .eq("alias_slug", slug)
            .limit(1)
            .execute()
            .data
        )
        if not aliases:
            return None

        rows = _get_client().table(_TABLE).select("*").eq("id", aliases[0]["game_id"]).execute().data
        return _with_canonical_storage_image(rows[0]) if rows else None

    return await anyio.to_thread.run_sync(_q)


async def upsert_game(game_data: Dict[str, Any]) -> Dict[str, Any]:
    if is_local():
        local_db.upsert_game(game_data)
        return game_data

    def _q():
        return _get_client().table(_TABLE).upsert(game_data).execute().data[0]

    return await anyio.to_thread.run_sync(_q)


async def create_unverified_game(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new unverified work+edition pair for an authenticated generation request."""
    if is_local():
        local_db.upsert_game(game_data)
        return game_data

    def _q():
        client = _get_client()
        canonical_title = str(game_data.get("title_ja") or game_data.get("title") or "").strip()
        if not canonical_title:
            raise ValueError("Generated game is missing a title")

        work_rows = (
            client.table("game_works")
            .insert({"canonical_title": canonical_title, "identity_status": "unverified"})
            .execute()
            .data
        )
        if not work_rows:
            raise RuntimeError("Failed to create canonical game work")

        work_id = work_rows[0]["id"]
        payload = dict(game_data)
        payload["work_id"] = work_id
        payload["identity_status"] = "unverified"
        payload["source_trust"] = "unknown"
        payload["content_review_status"] = "ai_draft"
        try:
            rows = client.table(_TABLE).insert(payload).execute().data
            if not rows:
                raise RuntimeError("Failed to create game edition")
            return _with_canonical_storage_image(rows[0])
        except Exception:
            # Avoid leaving an orphan work when the edition insert fails.
            client.table("game_works").delete().eq("id", work_id).execute()
            raise

    return await anyio.to_thread.run_sync(_q)


async def increment_view_count(game_id: str) -> None:
    if is_local():
        return

    def _q():
        rows = _get_client().table(_TABLE).select("view_count").eq("id", game_id).execute().data
        if rows:
            count = rows[0].get("view_count") or 0
            _get_client().table(_TABLE).update({"view_count": count + 1}).eq("id", game_id).execute()

    await anyio.to_thread.run_sync(_q)


# Legacy alias
async def upsert(data: dict[str, Any]) -> List[dict[str, Any]]:
    return [await upsert_game(data)]


async def list_for_sitemap() -> list[dict[str, Any]]:
    if is_local():
        res = local_db.list_recent(limit=50000)
        return [
            {
                "slug": g["slug"],
                "title": g["title"],
                "updated_at": g["updated_at"],
                "image_url": g.get("image_url"),
            }
            for g in res["data"]
            if str(g.get("slug") or "").strip()
        ]

    def _q():
        rows = (
            _get_client()
            .table(_TABLE)
            .select("slug, title, updated_at, image_url")
            .execute()
            .data
        )
        return [
            _with_canonical_storage_image(row)
            for row in rows
            if str(row.get("slug") or "").strip()
        ]

    return await anyio.to_thread.run_sync(_q)
