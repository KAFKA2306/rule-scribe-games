import asyncio
import sys
from app.core.settings import settings
from supabase import create_client

async def main():
    print("Connecting to Supabase...")
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    print("Fetching all games...")
    # Fetch all games (assuming < 1000 for now, or use range if more)
    # Supabase default limit is often 1000.
    response = client.table("games").select("*").execute()
    games = response.data
    
    print(f"Found {len(games)} games.")
    
    critical_fields = ["title", "description", "rules_content", "slug", "image_url"]
    warning_fields = ["official_url", "summary", "min_players", "max_players"]
    
    missing_critical = 0
    missing_warning = 0
    
    print(f"\n{'ID':<36} | {'Title':<30} | {'Missing Fields'}")
    print("-" * 100)
    
    for game in games:
        missing = []
        is_critical = False
        
        for field in critical_fields:
            val = game.get(field)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                missing.append(f"{field}(CRITICAL)")
                is_critical = True
                
        for field in warning_fields:
            val = game.get(field)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                missing.append(field)
                
        if missing:
            if is_critical:
                missing_critical += 1
            else:
                missing_warning += 1
            
            title = game.get("title", "NO TITLE")
            print(f"{game['id']:<36} | {title[:30]:<30} | {', '.join(missing)}")

    print("-" * 100)
    print(f"Summary: {len(games)} games total.")
    print(f"Games with CRITICAL missing fields: {missing_critical}")
    print(f"Games with WARNING missing fields: {missing_warning}")
    
    if missing_critical > 0:
        print("FAIL: Critical data missing.")
        sys.exit(1)
    
    print("SUCCESS: No critical data missing.")

if __name__ == "__main__":
    asyncio.run(main())
