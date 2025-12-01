from supabase import create_client, Client
from app.core.settings import settings


class SupabaseManager:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_key
        )

    def upsert_game(self, data: dict):
        return (
            self.client.table("games")
            .upsert(data, on_conflict="source_url" if data.get("source_url") else "id")
            .execute()
            .data
        )


supabase_manager = SupabaseManager()


def search_games(query: str):
    return (
        supabase_manager.client.table("games")
        .select("*")
        .or_(f"title.ilike.%{query}%,description.ilike.%{query}%")
        .execute()
        .data
    )
