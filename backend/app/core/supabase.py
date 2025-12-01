import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")

class SupabaseManager:
    def __init__(self):
        self.client: Client | None = None
        self.is_connected = False
        if url and key:
            try:
                self.client = create_client(url, key)
                self.is_connected = True
            except Exception as e: print(f"Supabase init error: {e}")

    def upsert_game(self, data: dict):
        if not self.is_connected: return None
        try:
            return self.client.table("games").upsert(
                data, on_conflict="source_url" if data.get("source_url") else "id"
            ).execute().data
        except Exception as e:
            print(f"Upsert error: {e}")
            return None

supabase_manager = SupabaseManager()

def search_games(query: str):
    if not supabase_manager.is_connected: return []
    try:
        return supabase_manager.client.table("games").select("*").or_(f"title.ilike.%{query}%,description.ilike.%{query}%").execute().data
    except Exception: return []
