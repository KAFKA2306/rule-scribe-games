import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

class SupabaseManager:
    def __init__(self):
        self.client: Client | None = None
        self.is_connected = False
        if url and key:
            try:
                self.client = create_client(url, key)
                self.is_connected = True
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}")

    def get_client(self):
        return self.client

supabase_manager = SupabaseManager()

# Mock data for fallback
MOCK_GAMES = [
    {
        "id": 1,
        "title": "Catan",
        "description": "Collect resources and build settlements.",
        "rules_content": "Players roll dice to collect resources..."
    },
    {
        "id": 2,
        "title": "Wingspan",
        "description": "Attract birds to your wildlife preserve.",
        "rules_content": "Play bird cards into your habitat..."
    }
]

def search_games(query: str):
    if supabase_manager.is_connected:
        try:
            # Simple text search on title or description
            response = supabase_manager.client.table("games") \
                .select("*") \
                .or_(f"title.ilike.%{query}%,description.ilike.%{query}%") \
                .execute()
            return response.data
        except Exception as e:
            print(f"Supabase search error: {e}")
            return _fallback_search(query)
    else:
        return _fallback_search(query)

def _fallback_search(query: str):
    print("Using fallback search")
    query = query.lower()
    return [g for g in MOCK_GAMES if query in g["title"].lower() or query in g["description"].lower()]
