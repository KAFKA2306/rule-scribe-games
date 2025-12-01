from typing import List, Protocol, Dict, Any, Optional

import anyio

try:  # supabase sdk may be absent in some environments (e.g., preview deploys)
    from supabase import Client, create_client  # type: ignore
except Exception:  # pragma: no cover - best-effort fallback
    Client = None  # type: ignore
    create_client = None  # type: ignore

from app.core.settings import settings, PLACEHOLDER


class GameRepository(Protocol):
    async def search(self, query: str) -> List[Dict[str, Any]]:
        ...

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        ...


def _create_client() -> Optional[Client]:
    """
    Return a Supabase client when credentials look valid; otherwise None so the
    app can fall back to mock behaviour instead of crashing at import time.
    """
    if create_client is None:
        return None
    if PLACEHOLDER in settings.supabase_url or PLACEHOLDER in settings.supabase_key:
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception:
        return None


class SupabaseGameRepository(GameRepository):
    """
    Infrastructure adapter that wraps the sync Supabase client and exposes
    async methods using thread offloading to avoid blocking the event loop.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client: Client = client or _create_client()
        if self.client is None:
            raise ValueError("Supabase client could not be initialized.")

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
        conflict_target = "source_url" if data.get("source_url") else "title"

        try:
            def _upsert():
                return (
                    self.client.table("games")
                    .upsert(data, on_conflict=conflict_target)
                    .execute()
                    .data
                )

            return await anyio.to_thread.run_sync(_upsert)
        except Exception:
            return []


class NoopGameRepository(GameRepository):
    """
    Safe fallback used when Supabase credentials are missing/invalid.
    """

    async def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    async def upsert(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []


def _init_repository() -> GameRepository:
    client = _create_client()
    if client is None:
        return NoopGameRepository()
    try:
        return SupabaseGameRepository(client)
    except Exception:
        return NoopGameRepository()


supabase_repository: GameRepository = _init_repository()
