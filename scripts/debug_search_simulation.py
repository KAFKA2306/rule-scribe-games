import asyncio
from app.core.settings import settings
from supabase import create_client

async def main():
    print("Connecting to Supabase...")
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    print("Fetching ALL games...")
    response = client.table("games").select("*").execute()
    games = response.data
    print(f"Total games: {len(games)}")
    
    query = "splendor"
    
    matches = []
    
    for g in games:
        # Simulate frontend search logic
        text_fields = [
            g.get("title"),
            g.get("title_ja"),
            g.get("title_en"),
            g.get("summary"),
            g.get("description"),
            g.get("rules_content")
        ]
        
        # Simple inclusion check (case insensitive)
        is_match = False
        match_reason = []
        for text in text_fields:
            if text and query in text.lower():
                is_match = True
                match_reason.append(text[:20] + "...")
        
        if is_match:
            matches.append((g, match_reason))
            
    print(f"\nFrontend Search Simulation for '{query}': Found {len(matches)} matches.")
    for g, reasons in matches:
        print(f" - [{g['title']}] (Slug: {g['slug']}) | ID: {g['id']}")
        # print(f"   Matches in: {reasons}")

    # Check specifically for Splendor game
    splendor = next((g for g in games if "Splendor" in (g.get("title") or "")), None)
    if splendor:
        print(f"\nTarget 'Splendor' Game Data:")
        print(f"Title: {splendor.get('title')}")
        print(f"Title JA: {splendor.get('title_ja')}")
        print(f"Slug: {splendor.get('slug')}")
    else:
        print("\nTarget 'Splendor' game NOT found by title iteration.")

if __name__ == "__main__":
    asyncio.run(main())
