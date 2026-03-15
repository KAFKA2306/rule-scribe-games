import asyncio
import os
import sys

# Ensure backend directory is in path for app imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.supabase import upsert, get_by_slug

async def generate_infographic(game_title, game_title_ja, section_name, section_data, style="professional_clean"):
    """Generate a specialized infographic prompt using Nano Banana Pro style."""
    
    prompt = f"""
Create a clear, professional instructional infographic for the board game "{game_title}" (Japanese: "{game_title_ja}").

Visualize: {section_name}
Use this structured data: {section_data}

Requirements:
- All text must be in natural, easy-to-read Japanese (large, legible font)
- Professional board game rulebook style: clean lines, icons, color coding (use consistent palette)
- Include step numbers, arrows, and short explanatory captions
- Add small English subtitle only if necessary for international clarity
- Style: {style}
- High resolution, perfect text rendering, no distortion
- Make it educational and glanceable – users should understand the mechanic from this image alone
"""
    
    print(f"🎨 Generating {section_name} for {game_title_ja}...")
    # Using placeholders/output_slides for now
    return f"https://rule-scribe-games.vercel.app/output_slides/magnolia_{section_name.lower().replace(' ', '_')}.png"

async def deploy():
    slug = "magnolia"
    
    print(f"🚀 Deploying to Supabase for {slug}...")
    # Verify game exists first and get full details
    game = await get_by_slug(slug)
    if not game:
        print(f"✗ Game {slug} not found in database. Please ingest first.")
        return

    title = game["title"]
    title_ja = game["title_ja"]
    
    sections = {
        "setup": "3x3グリッド領地、手札5枚、初期資金1金または配置アクション。",
        "turn_flow": "ドロー、配置（3択）、戦争、発展・収入・VPの各フェイズを同時進行。",
        "actions": "2金獲得、1金＋1枚配置、2枚配置。垂直・水平の配置コンボが重要。",
        "winning": "40 VP到達または9枚配置で終了。所持金3金ごとに1 VP加算。",
        "components": "ユニットカード102枚、VPボード、軍事力ボード、コイン、プレイヤーシート。"
    }
    
    infographics_urls = {}
    for key, data in sections.items():
        url = await generate_infographic(title, title_ja, key, data)
        infographics_urls[key] = url

    # Use upsert as per app.core.supabase logic
    update_data = {
        "id": game["id"],
        "slug": slug,
        "title": title,
        "title_ja": title_ja,
        "infographics": infographics_urls
    }
    result = await upsert(update_data)
    
    if result:
        print(f"✓ Successfully updated {slug} with {len(infographics_urls)} infographics.")
        print(f"🔗 View at: http://localhost:5173/games/{slug}")
    else:
        print(f"✗ Failed to update {slug}.")

if __name__ == "__main__":
    asyncio.run(deploy())
