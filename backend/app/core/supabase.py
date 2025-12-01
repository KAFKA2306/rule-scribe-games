from typing import List, Protocol, Dict, Any, Optional

import anyio

try:
    from supabase import create_client, Client  # type: ignore
except Exception:  # pragma: no cover
    Client = None  # type: ignore
    create_client = None  # type: ignore

from app.core.settings import settings, PLACEHOLDER


class GameRepository(Protocol):
    async def search(self, query: str) -> List[Dict[str, Any]]: ...
    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]: ...


def _client() -> Optional[Client]:
    if (
        not settings.supabase_url
        or settings.supabase_url == PLACEHOLDER
        or not settings.supabase_key
        or settings.supabase_key == PLACEHOLDER
        or create_client is None
    ):
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception:
        return None


class SupabaseGameRepository(GameRepository):
    def __init__(self, client: Client):
        self.client = client

    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            def _search():
                return (
                    self.client.table("games")
                    .select("*")
                    .or_(f"title.ilike.%{query}%,description.ilike.%{query}%")
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_search)
        except Exception:
            return []

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            def _upsert():
                key = "source_url" if data.get("source_url") else "title"
                return (
                    self.client.table("games")
                    .upsert(data, on_conflict=key)
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_upsert)
        except Exception:
            return []


class NoopGameRepository(GameRepository):
    async def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []


def _repo() -> GameRepository:
    client = _client()
    if client is None:
        return NoopGameRepository()
    return SupabaseGameRepository(client)


supabase_repository: GameRepository = _repo()
