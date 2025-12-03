import os
import time
from typing import Optional
from app.core.setup import apply_initial_setup

# Load env vars first
apply_initial_setup()

from amazon_paapi import AmazonApi
from supabase import create_client, Client
from app.core.settings import settings

# Initialize Amazon API
# These must be set in .env
ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")
REGION = "JP"

def get_amazon_client():
    if not ACCESS_KEY or not SECRET_KEY or not PARTNER_TAG:
        print("Missing Amazon PA-API credentials. Skipping Amazon search.")
        return None
    return AmazonApi(ACCESS_KEY, SECRET_KEY, PARTNER_TAG, REGION)

def search_product(amazon, title: str) -> Optional[str]:
    """
    Search for a game title on Amazon and return the URL of the first match.
    Returns None if no match found or error occurs.
    """
    try:
        # Search in ToysAndGames category
        items = amazon.search_items(keywords=title, search_index="ToysAndGames", item_count=1)
        if items and items.items:
            item = items.items[0]
            print(f"Found match for '{title}': {item.item_info.title.display_value} ({item.asin})")
            return item.detail_page_url
    except Exception as e:
        print(f"Error searching for '{title}': {e}")
    return None

def run_batch():
    print("Starting Amazon ASIN Batch...")
    
    # Initialize Supabase client
    url: str = settings.supabase_url
    key: str = settings.supabase_key
    supabase: Client = create_client(url, key)

    # Initialize Amazon client
    amazon = get_amazon_client()
    if not amazon:
        return

    # Fetch all games
    # Note: For a large DB, pagination would be needed. 
    # Currently assuming < 1000 games for simplicity.
    response = supabase.table("games").select("id, title, structured_data").execute()
    games = response.data

    updated_count = 0
    
    for game in games:
        title = game.get("title")
        sd = game.get("structured_data") or {}
        affiliate_urls = sd.get("affiliate_urls") or {}
        
        # Skip if Amazon link already exists
        if "amazon" in affiliate_urls:
            continue
            
        print(f"Processing: {title}")
        
        # Search Amazon
        url = search_product(amazon, title)
        
        if url:
            # Update DB
            affiliate_urls["amazon"] = url
            sd["affiliate_urls"] = affiliate_urls
            
            try:
                supabase.table("games").update({"structured_data": sd}).eq("id", game["id"]).execute()
                print(f"Updated {title} with URL: {url}")
                updated_count += 1
                # Sleep to avoid rate limits
                time.sleep(1) 
            except Exception as e:
                print(f"Failed to update {title}: {e}")
        else:
            print(f"No match found for {title}")
            
    print(f"Batch complete. Updated {updated_count} games.")

if __name__ == "__main__":
    run_batch()
