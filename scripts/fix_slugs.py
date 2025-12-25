import asyncio
import re
from app.core.settings import settings
from supabase import create_client
from app.utils.slugify import slugify  # Assuming this exists, otherwise we implement a simple one

# Fallback slugify if import fails or we want custom behavior
def simple_slugify(text):
    if not text:
        return None
    # Remove non-alphanumeric (except hyphens/spaces), lower case, replace spaces with hyphens
    s = str(text).lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    return s

async def main():
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    # Fetch games with missing slugs
    # Or just fetch all and check
    response = client.table("games").select("*").execute()
    games = response.data
    
    count_fixed = 0
    
    print(f"Checking {len(games)} games for missing slugs...")
    
    for game in games:
        current_slug = game.get("slug")
        if not current_slug or current_slug.strip() == "":
            # Generate new slug
            title_en = game.get("title_en")
            title = game.get("title")
            
            # Prefer English title for slug, else main title if it looks ascii, else random?
            # actually app.utils.slugify handles japanese?
            # Let's try to make a readable slug.
            
            base =  title_en if title_en else title
            new_slug = simple_slugify(base)
            
            if not new_slug:
                new_slug = f"game-{game['id'][:8]}"
            
            # De-duplicate if needed? Supabase might error if unique constraint exists.
            # We'll just try to update.
            
            print(f"Fixing Game [{title}]: New Slug -> {new_slug}")
            
            try:
                client.table("games").update({"slug": new_slug}).eq("id", game["id"]).execute()
                count_fixed += 1
            except Exception as e:
                print(f"Error updating {title}: {e}")

    print(f"Finished. Fixed {count_fixed} games.")

if __name__ == "__main__":
    asyncio.run(main())
