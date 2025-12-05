from typing import List, Protocol, Dict, Any, Optional
import sys
import anyio

try:
    from supabase import create_client, Client
except Exception as e:
    print(f"Failed to import supabase: {e}", file=sys.stderr)
    Client = None
    create_client = None
from app.core.settings import settings, PLACEHOLDER
from app.utils.slugify import slugify


class GameRepository(Protocol):
    async def search(self, query: str) -> List[Dict[str, Any]]: ...

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]: ...

    async def get_by_id(self, game_id: int) -> Optional[Dict[str, Any]]: ...

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]: ...

    async def update_summary(self, game_id: int, summary: str) -> bool: ...

    async def update_structured_data(
        self, game_id: int, structured_data: dict
    ) -> bool: ...

    async def list_recent(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]: ...

    async def find_exact_or_prefix(self, query: str) -> Optional[Dict[str, Any]]: ...

    async def increment_view_count(self, game_id: str) -> None: ...


def _client() -> Optional[Client]:
    if (
        not settings.supabase_url
        or settings.supabase_url == PLACEHOLDER
        or (not settings.supabase_key)
        or (settings.supabase_key == PLACEHOLDER)
        or (create_client is None)
    ):
        print(
            "Supabase client could not be initialized. Check dependencies and environment variables.",
            file=sys.stderr,
        )
        return None
    return create_client(settings.supabase_url, settings.supabase_key)


class SupabaseGameRepository(GameRepository):
    def __init__(self, client: Client):
        self.client = client
        self.valid_columns = {
            "id",
            "slug",
            "title",
            "description",
            "summary",
            "rules_content",
            "source_url",
            "image_url",
            "structured_data",
            "view_count",
            "search_count",
            "data_version",
            "is_official",
            "min_players",
            "max_players",
            "play_time",
            "min_age",
            "published_year",
            "title_ja",
            "title_en",
            "official_url",
            "bgg_url",
            "bga_url",
            "amazon_url",
            "audio_url",
            "created_at",
            "updated_at",
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        def _search():
            return (
                self.client.table("games")
                .select("*")
                .or_(f"title.ilike.*{query}*,description.ilike.*{query}*")
                .execute()
                .data
            )

        return await anyio.to_thread.run_sync(_search)

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        def _upsert():
            filtered_data = {k: v for (k, v) in data.items() if k in self.valid_columns}
            title = filtered_data.get("title") or ""
            if title:
                filtered_data["slug"] = slugify(title)
            key = "slug"
            if filtered_data.get("source_url"):
                key = "source_url"
            return (
                self.client.table("games")
                .upsert(filtered_data, on_conflict=key)
                .execute()
                .data
            )

        return await anyio.to_thread.run_sync(_upsert)

    async def get_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        def _get():
            res = (
                self.client.table("games").select("*").eq("id", game_id).execute().data
            )
            return res[0] if res else None

        return await anyio.to_thread.run_sync(_get)

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        def _get():
            res = self.client.table("games").select("*").eq("slug", slug).execute().data
            return res[0] if res else None

        return await anyio.to_thread.run_sync(_get)

    async def update_summary(self, game_id: int, summary: str) -> bool:
        def _update():
            self.client.table("games").update({"summary": summary}).eq(
                "id", game_id
            ).execute()
            return True

        return await anyio.to_thread.run_sync(_update)

    async def update_structured_data(self, game_id: int, structured_data: dict) -> bool:
        def _update():
            self.client.table("games").update({"structured_data": structured_data}).eq(
                "id", game_id
            ).execute()
            return True

        return await anyio.to_thread.run_sync(_update)

    async def list_recent(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        def _list():
            return (
                self.client.table("games")
                .select("*")
                .order("updated_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
                .data
            )

        return await anyio.to_thread.run_sync(_list)

    async def find_exact_or_prefix(self, query: str) -> Optional[Dict[str, Any]]:
        def _find():
            res = (
                self.client.table("games").select("*").eq("slug", query).execute().data
            )
            if res:
                return res[0]
            res = (
                self.client.table("games")
                .select("*")
                .or_(
                    f"title.ilike.{query},title_ja.ilike.{query},title_en.ilike.{query}"
                )
                .limit(1)
                .execute()
                .data
            )
            if res:
                return res[0]
            res = (
                self.client.table("games")
                .select("*")
                .or_(
                    f"title.ilike.{query}%,title_ja.ilike.{query}%,title_en.ilike.{query}%"
                )
                .limit(1)
                .execute()
                .data
            )
            return res[0] if res else None

        return await anyio.to_thread.run_sync(_find)

    async def increment_view_count(self, game_id: str) -> None:
        def _increment():
            res = (
                self.client.table("games")
                .select("view_count")
                .eq("id", game_id)
                .execute()
                .data
            )
            if res:
                current = res[0].get("view_count") or 0
                self.client.table("games").update({"view_count": current + 1}).eq(
                    "id", game_id
                ).execute()

        await anyio.to_thread.run_sync(_increment)


def _repo() -> GameRepository:
    client = _client()
    if client is None:
        raise RuntimeError(
            "Supabase client could not be initialized. Check dependencies and environment variables."
        )
    return SupabaseGameRepository(client)


supabase_repository: GameRepository = _repo()
