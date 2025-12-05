import asyncio
import sys
import os
import httpx
from supabase import create_client, Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    print(f"Loading .env from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                (key, value) = line.split("=", 1)
                os.environ[key] = value
from app.core.settings import settings

URL_COLUMNS = [
    "source_url",
    "image_url",
    "official_url",
    "bgg_url",
    "bga_url",
    "amazon_url",
    "audio_url",
]


async def check_url(client: httpx.AsyncClient, url: str) -> bool:
    if not url:
        return True
    try:
        response = await client.get(url, follow_redirects=True, timeout=10.0)
        if 200 <= response.status_code < 300:
            return True
        else:
            print(f"[-] Invalid URL (Status {response.status_code}): {url}")
            return False
    except Exception as e:
        print(f"[-] Error checking URL {url}: {e}")
        return False


async def main():
    print(f"DEBUG: SUPABASE_URL='{settings.supabase_url}'")
    print(f"DEBUG: SUPABASE_KEY='{settings.supabase_key[:5]}...'")
    if (
        not settings.supabase_url
        or not settings.supabase_key
        or settings.supabase_url == "PLACEHOLDER"
    ):
        print(
            "Error: Supabase credentials not found or invalid in environment variables."
        )
        return
    try:
        supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return
    print("Fetching all games from Supabase...")
    print("Fetching all games from Supabase...")
    response = supabase.table("games").select("*").limit(1000).execute()
    games = response.data
    print(f"Found {len(games)} games. Starting validation...")
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}
    ) as http_client:
        for game in games:
            game_id = game.get("id")
            title = game.get("title", "Unknown")
            print(f"\nChecking game: {title} (ID: {game_id})")
            updates = {}
            for col in URL_COLUMNS:
                url = game.get(col)
                if url:
                    print(f"  Checking {col}: {url} ... ", end="", flush=True)
                    is_valid = await check_url(http_client, url)
                    if is_valid:
                        print("OK")
                    else:
                        print("INVALID -> Marking for deletion")
                        updates[col] = None
            if updates:
                print(f"  Updating game {game_id} with changes: {updates}")
                try:
                    supabase.table("games").update(updates).eq("id", game_id).execute()
                    print("  Update successful.")
                except Exception as e:
                    print(f"  Update failed: {e}")
    print("\nValidation complete.")


if __name__ == "__main__":
    asyncio.run(main())
