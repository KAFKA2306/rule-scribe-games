from typing import List, Protocol, Dict, Any, Optional
import sys
import traceback
import anyio

try:
    from supabase import create_client, Client  # type: ignore
except Exception:  # pragma: no cover
    Client = None  # type: ignore
    create_client = None  # type: ignore

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
    async def list_recent(self, limit: int = 100) -> List[Dict[str, Any]]: ...


def _client() -> Optional[Client]:
    if (
        not settings.supabase_url
        or settings.supabase_url == PLACEHOLDER
        or not settings.supabase_key
        or settings.supabase_key == PLACEHOLDER
        or create_client is None
    ):
        print(
            "Warning: Supabase credentials missing or client library not found. Falling back to Mock.",
            file=sys.stderr,
        )
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}", file=sys.stderr)
        return None


class SupabaseGameRepository(GameRepository):
    def __init__(self, client: Client):
        self.client = client

    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:

            def _search():
                # Note: ilike syntax for 'OR' filter in supabase-py might vary by version
                # using a raw filter string or built-in methods.
                return (
                    self.client.table("games")
                    .select("*")
                    .or_(f"title.ilike.*{query}*,description.ilike.*{query}*")
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_search)
        except Exception as e:
            print(f"Error in Supabase search: {e}", file=sys.stderr)
            traceback.print_exc()
            return []

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:

            def _upsert():
                title = data.get("title") or ""
                if title:
                    data["slug"] = slugify(title)

                key = "slug"
                if data.get("source_url"):
                    key = "source_url"

                return (
                    self.client.table("games")
                    .upsert(data, on_conflict=key)
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_upsert)
        except Exception as e:
            print(f"Error in Supabase upsert: {e}", file=sys.stderr)
            return []

    async def get_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        try:

            def _get():
                res = (
                    self.client.table("games")
                    .select("*")
                    .eq("id", game_id)
                    .execute()
                    .data
                )
                return res[0] if res else None

            return await anyio.to_thread.run_sync(_get)
        except Exception as e:
            print(f"Error in Supabase get_by_id: {e}", file=sys.stderr)
            return None

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        try:

            def _get():
                res = (
                    self.client.table("games")
                    .select("*")
                    .eq("slug", slug)
                    .execute()
                    .data
                )
                return res[0] if res else None

            return await anyio.to_thread.run_sync(_get)
        except Exception as e:
            print(f"Error in Supabase get_by_slug: {e}", file=sys.stderr)
            return None

    async def update_summary(self, game_id: int, summary: str) -> bool:
        try:

            def _update():
                (
                    self.client.table("games")
                    .update({"summary": summary})
                    .eq("id", game_id)
                    .execute()
                )
                return True

            return await anyio.to_thread.run_sync(_update)
        except Exception as e:
            print(f"Error in Supabase update_summary: {e}", file=sys.stderr)
            return False

    async def update_structured_data(self, game_id: int, structured_data: dict) -> bool:
        try:

            def _update():
                (
                    self.client.table("games")
                    .update({"structured_data": structured_data})
                    .eq("id", game_id)
                    .execute()
                )
                return True

            return await anyio.to_thread.run_sync(_update)
        except Exception as e:
            print(f"Error in Supabase update_structured_data: {e}", file=sys.stderr)
            return False

    async def list_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:

            def _list():
                return (
                    self.client.table("games")
                    .select("*")
                    .order("updated_at", desc=True)
                    .limit(limit)
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_list)
        except Exception as e:
            print(f"Error in Supabase list_recent: {e}", file=sys.stderr)
            return []


class NoopGameRepository(GameRepository):
    async def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def get_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        return None

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        return None

    async def update_summary(self, game_id: int, summary: str) -> bool:
        return False

    async def update_structured_data(self, game_id: int, structured_data: dict) -> bool:
        return False

    async def list_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return []


def _repo() -> GameRepository:
    client = _client()
    if client is None:
        return NoopGameRepository()
    return SupabaseGameRepository(client)


supabase_repository: GameRepository = _repo()
