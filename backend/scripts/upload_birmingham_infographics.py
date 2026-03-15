#!/usr/bin/env python3
"""Upload Birmingham infographics to database"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase import _client


def upload_birmingham() -> None:
    """Upload Birmingham infographics"""
    
    # Try professional URLs first, fallback to simple ones
    urls_file = Path(__file__).parent.parent.parent / "assets" / "birmingham_professional_urls.json"
    fallback_file = Path(__file__).parent.parent.parent / "birmingham_infographics_urls.json"
    
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            infographics_urls = json.load(f)
        print("📄 Using professional infographics URLs\n")
    elif fallback_file.exists():
        with open(fallback_file, 'r', encoding='utf-8') as f:
            infographics_urls = json.load(f)
        print("📄 Using basic infographics URLs\n")
    else:
        print(f"❌ No infographics URLs found")
        print(f"   Checked: {urls_file}")
        print(f"   Fallback: {fallback_file}")
        return
    
    print("📦 Uploading Birmingham Infographics...\n")
    print(f"📋 Found {len(infographics_urls)} infographics to upload:")
    for key in infographics_urls:
        print(f"   ✓ {key}")
    print()
    
    # Search for Birmingham game
    print("🔍 Searching for Birmingham in database...\n")
    
    try:
        response = _client.table("games").select("id,slug,title").ilike("slug", "%birmingham%").execute()
        
        if not response.data:
            # Try other variations
            response = _client.table("games").select("id,slug,title").ilike("title", "%birmingham%").execute()
        
        if response.data:
            birmingham = response.data[0]
            slug = birmingham["slug"]
            title = birmingham["title"]
            print(f"✅ Found: {title} (slug: {slug})")
            print("   Uploading infographics...\n")
            
            try:
                update_response = _client.table("games").update({
                    "infographics": infographics_urls
                }).eq("slug", slug).execute()
                
                if update_response.data:
                    print(f"✅ Successfully uploaded {len(infographics_urls)} infographics to {title}\n")
                else:
                    print(f"⚠️  Update returned empty response")
                    print(f"   This may indicate the 'infographics' column doesn't exist yet.")
                    print(f"   Check if database migration has been applied.\n")
            
            except Exception as e:
                print(f"⚠️  Upload error: {e}")
                print(f"   Ensure database migration SQL has been applied in Supabase dashboard.\n")
        
        else:
            print("❌ Birmingham not found in database")
            print("   Available options:")
            print("   1. Create via API: POST /api/search?q=Birmingham&generate=true")
            print("   2. Or manually add to database first\n")
            return
    
    except Exception as e:
        print(f"❌ Database error: {e}\n")
        return
    
    # Display test instructions
    print("📋 NEXT: Test Carousel Display\n")
    print("1. Navigate to Birmingham game page:")
    print(f"   http://localhost:5173/games/{slug}\n")
    print("2. Look for the 📊 図解 tab (appears only if infographics loaded)")
    print("3. Verify carousel navigation:")
    print("   - Click ← → arrows to move between images")
    print("   - Click dot buttons to jump to specific slides")
    print("   - See counter showing '1 / 5'\n")


if __name__ == "__main__":
    upload_birmingham()
