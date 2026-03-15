import asyncio
import re

from supabase import create_client

from app.core.settings import settings


def simple_slugify(text):
    if not text:
        return None
    s = str(text).lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s


async def main():
    client = create_client(settings.supabase_url, settings.supabase_key)
    response = client.table("games").select("*").execute()
    games = response.data
    count_fixed = 0
    print(f"Checking {len(games)} games for missing slugs...")
    for game in games:
        current_slug = game.get("slug")
        if not current_slug or current_slug.strip() == "":
            title_en = game.get("title_en")
            title = game.get("title")
            base = title_en if title_en else title
            new_slug = simple_slugify(base)
            if not new_slug:
                new_slug = f"game-{game['id'][:8]}"
            print(f"Fixing Game [{title}]: New Slug -> {new_slug}")
            try:
                client.table("games").update({"slug": new_slug}).eq("id", game["id"]).execute()
                count_fixed += 1
            except Exception as e:
                print(f"Error updating {title}: {e}")
    print(f"Finished. Fixed {count_fixed} games.")


if __name__ == "__main__":
    asyncio.run(main())
