import asyncio
from app.core.settings import settings
from supabase import create_client

async def main():
    print("Connecting to Supabase...")
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    print("Checking for 'Splendor' in database...")
    # Check exact match or like match
    response = client.table("games").select("*").ilike("title", "%Splendor%").execute()
    games = response.data
    
    if not games:
        print("FAIL: 'Splendor' NOT found in title search.")
        # Try finding by Japanese title if "ルネサンス" (Renaissance) mentioned in history
        response_ja = client.table("games").select("*").ilike("title_ja", "%宝石の煌き%").execute()
        games_ja = response_ja.data
        if games_ja:
             print(f"FOUND by Japanese title '宝石の煌き': {len(games_ja)} games.")
             for g in games_ja:
                 print(f"ID: {g['id']}, Title: {g['title']}, Title_JA: {g['title_ja']}, Slug: {g['slug']}")
        else:
             print("FAIL: '宝石の煌き' also not found.")
    else:
        print(f"FOUND {len(games)} games with 'Splendor' in title.")
        for g in games:
            print(f"ID: {g['id']}, Title: {g['title']}, Slug: {g['slug']}")
            print(f"Description: {g.get('description')[:50]}..." if g.get('description') else "No Description")

if __name__ == "__main__":
    asyncio.run(main())
