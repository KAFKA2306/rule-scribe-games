#!/usr/bin/env python3
"""Upload generated infographics and test carousel display"""
import asyncio
import sys
import json
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase import _client


def encode_svg_to_dataurl(svg_path: str) -> str:
    """Convert SVG file to base64 data URL"""
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    encoded = base64.b64encode(svg_content.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


async def upload_infographics() -> None:
    """Upload generated infographics to games"""
    assets_dir = Path(__file__).parent.parent.parent / "assets" / "infographics"
    
    print("📦 Generating Infographics Data URLs...\n")
    
    # Map SVG files to Splendor game
    splendor_infographics = {
        "turn_flow": encode_svg_to_dataurl(str(assets_dir / "splendor_turn_flow.svg")),
        "setup": encode_svg_to_dataurl(str(assets_dir / "splendor_setup.svg")),
        "actions": encode_svg_to_dataurl(str(assets_dir / "splendor_actions.svg")),
        "winning": encode_svg_to_dataurl(str(assets_dir / "splendor_winning.svg")),
        "components": encode_svg_to_dataurl(str(assets_dir / "splendor_components.svg")),
    }
    
    # Map SVG files to Catan game
    catan_infographics = {
        "setup": encode_svg_to_dataurl(str(assets_dir / "catan_setup.svg")),
        "actions": encode_svg_to_dataurl(str(assets_dir / "catan_actions.svg")),
    }
    
    print("✅ Data URLs created")
    print(f"   - Splendor: {len(splendor_infographics)} infographics")
    print(f"   - Catan: {len(catan_infographics)} infographics\n")
    
    # Try to find games and upload
    print("🔍 Searching for games...\n")
    
    try:
        # Get Splendor
        response = _client.table("games").select("id,slug,title").eq("slug", "splendor").execute()
        splendor = response.data[0] if response.data else None
        
        if splendor:
            print(f"✅ Found: {splendor['title']} (slug: {splendor['slug']})")
            print("   Uploading infographics...")
            
            update_response = _client.table("games").update({
                "infographics": splendor_infographics
            }).eq("slug", "splendor").execute()
            
            if update_response.data:
                print("   ✅ Successfully updated with 5 infographics\n")
            else:
                print("   ⚠️  Update returned empty response\n")
        else:
            print("❌ Splendor not found in database. Create it first with: POST /api/search?q=Splendor&generate=true\n")
    
    except Exception as e:
        print(f"⚠️  Could not update Splendor: {e}")
        print("   Ensure database migration has been applied.\n")
        return
    
    try:
        # Get Catan
        response = _client.table("games").select("id,slug,title").eq("slug", "catan").execute()
        catan = response.data[0] if response.data else None
        
        if catan:
            print(f"✅ Found: {catan['title']} (slug: {catan['slug']})")
            print("   Uploading infographics...")
            
            update_response = _client.table("games").update({
                "infographics": catan_infographics
            }).eq("slug", "catan").execute()
            
            if update_response.data:
                print("   ✅ Successfully updated with 2 infographics\n")
            else:
                print("   ⚠️  Update returned empty response\n")
        else:
            print("❌ Catan not found in database. Create it first with: POST /api/search?q=Catan&generate=true\n")
    
    except Exception as e:
        print(f"⚠️  Could not update Catan: {e}\n")
    
    # Display test instructions
    print("\n📋 NEXT STEPS TO TEST CAROUSEL:\n")
    print("1. Start dev servers (if not already running):")
    print("   task dev\n")
    print("2. Navigate to game detail page:")
    print("   - Splendor: http://localhost:5173/games/splendor")
    print("   - Catan: http://localhost:5173/games/catan\n")
    print("3. Look for the 📊 図解 tab below the rules")
    print("4. Verify carousel displays all infographics correctly\n")
    print("✅ Carousel features to test:")
    print("   - Navigation arrows (← →) move between images")
    print("   - Dot buttons at bottom select slides")
    print("   - Counter shows current position (e.g., '1 / 5')")
    print("   - SVG images render without errors")


if __name__ == "__main__":
    asyncio.run(upload_infographics())
