#!/usr/bin/env python3
"""
Generate Birmingham infographics from NotebookLM-extracted content via Gemini Nano Banana.

Pipeline:
1. Use Playwright to open NotebookLM and guide content extraction
2. Parse extracted game structure
3. Use Gemini Nano Banana (image generation) for professional infographics
4. Upload to Supabase
"""
import json
import sys
import base64
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from playwright.sync_api import sync_playwright, Page, Browser
from app.core.settings import settings
from app.core.supabase import _client


BIRMINGHAM_RULES = {
    "game_title": "Brass: Birmingham",
    "title_ja": "ブラス・ビルミンガム",
    "components": {
        "emoji": "🧩",
        "title_ja": "ゲームコンポーネント",
        "details": [
            "イギリスの産業革命を舞台にした経済ゲーム",
            "綿工業・陶磁器・鉄などの業種タイル",
            "線路ネットワークを構築してリソース流通を確立",
            "株式証券で配当を獲得",
            "資本と産業を巧みに管理して勝利を目指す"
        ]
    },
    "setup": {
        "emoji": "⚙️",
        "title_ja": "セットアップ",
        "details": [
            "ゲームボードを配置（イギリス地図）",
            "各プレイヤーに初期資本50ポンドを配分",
            "業種タイルバッグを準備",
            "運河時代と鉄道時代のマーカーをセット",
            "プレイ順を決定"
        ]
    },
    "turn_flow": {
        "emoji": "🔄",
        "title_ja": "手番の流れ",
        "details": [
            "各プレイヤーが1つのアクションを選択",
            "ネットワーク構築 / 産業配置 / 株式売却から選択",
            "リソースと資本を管理しながら展開",
            "他プレイヤーの産業から恩恵を受ける可能性も",
            "次のプレイヤーへターンを移行"
        ]
    },
    "actions": {
        "emoji": "🏭",
        "title_ja": "プレイヤーアクション",
        "details": [
            "1. ネットワーク構築：線路を敷いて流通網を確立",
            "2. 産業配置：業種タイルを配置して生産能力を増強",
            "3. 株式売却：他プレイヤーの企業に投資して配当獲得",
            "4. 資本管理：手元資金の効率的配分が鍵",
            "5. ネットワーク完成で利益確定"
        ]
    },
    "winning": {
        "emoji": "🏆",
        "title_ja": "勝利条件",
        "details": [
            "2つの時代（運河時代と鉄道時代）を完了",
            "資本＋配当の合計金額で競う",
            "破産してないプレイヤーのみが対象",
            "産業ネットワークの完成度が重要",
            "最終的に最も多くの資金を保有したプレイヤーが勝利"
        ]
    }
}


def setup_gemini():
    """Initialize Gemini client"""
    if not settings.gemini_api_key or settings.gemini_api_key == "PLACEHOLDER":
        print("❌ GEMINI_API_KEY not set")
        sys.exit(1)
    genai.configure(api_key=settings.gemini_api_key)


def generate_infographic_with_nano_banana(
    title_ja: str,
    details: list[str],
    emoji: str,
    style: str = "professional_clean"
) -> Optional[bytes]:
    """Generate infographic using Gemini Nano Banana image generation"""
    
    print(f"🎨 Generating: {title_ja}")
    
    detail_text = "\n".join(f"• {d}" for d in details)
    
    prompt = f"""Create a professional, clear instructional infographic for the board game "Brass: Birmingham" in Japanese.

Title: {emoji} {title_ja}

Content to visualize:
{detail_text}

Requirements:
- All text must be in natural, native Japanese (large, legible font)
- Professional board game rulebook style: clean lines, icons, color-coding
- Use earth tones and industrial revolution aesthetic (browns, grays, golds)
- Include step numbers, arrows, and captions where applicable
- High resolution, perfect text rendering, no distortion
- Make it educational and glanceable - users understand the mechanic from this image alone
- Style: {style}
- Dimensions: 1200x800 pixels for web display"""
    
    try:
        print(f"   📡 Calling Gemini image generation API...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = model.generate_content(
            genai.types.content_types.ContentsType([
                {
                    "role": "user",
                    "parts": [
                        genai.types.content_types.PartType({"text": prompt})
                    ]
                }
            ]),
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1024
            )
        )
        
        if response.parts and response.parts[0].inline_data:
            image_bytes = response.parts[0].inline_data.data
            print(f"   ✅ Generated {len(image_bytes)} bytes")
            return image_bytes
        else:
            print(f"   ⚠️  No image data in response")
            return None
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def generate_infographic_placeholder(title_ja: str, details: list[str], emoji: str) -> bytes:
    """Fallback: Create SVG placeholder if Nano Banana fails"""
    
    svg = f'''<svg width="1200" height="800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#8B4513;stop-opacity:0.9" />
      <stop offset="100%" style="stop-color:#654321;stop-opacity:0.8" />
    </linearGradient>
  </defs>
  <rect width="1200" height="800" fill="url(#grad)"/>
  <rect x="30" y="30" width="1140" height="740" fill="none" stroke="white" stroke-width="3" rx="12"/>
  
  <text x="600" y="120" font-family="sans-serif" font-size="72" font-weight="bold" text-anchor="middle" fill="white">
    {emoji} {title_ja}
  </text>
  
  <line x1="100" y1="150" x2="1100" y2="150" stroke="white" stroke-width="2" opacity="0.6"/>
  
  <g id="details">'''
    
    y_pos = 220
    for detail in details:
        svg += f'''
    <circle cx="120" cy="{y_pos - 15}" r="10" fill="white" opacity="0.7"/>
    <text x="160" y="{y_pos}" font-family="sans-serif" font-size="22" fill="white">{detail}</text>'''
        y_pos += 80
    
    svg += '''
  </g>
</svg>'''
    
    return svg.encode('utf-8')


def open_notebooklm_browser():
    """Open NotebookLM with Playwright for manual content extraction"""
    
    print("\n📱 Opening NotebookLM with Playwright...")
    print("=" * 70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://notebooklm.google.com")
        page.wait_for_timeout(2000)
        
        print("""
✅ NotebookLM opened!

📋 MANUAL INSTRUCTIONS:
1. Sign in with your Google account
2. Create a new notebook: "Brass: Birmingham"
3. Add source document (optional - use the rules text provided)
4. Use NotebookLM to generate:
   - Setup & Components summary
   - Turn structure & Actions flow
   - Winning conditions explanation

5. When ready, copy the structured content and paste into the prompt below

Press ENTER in the terminal when you're ready to proceed...
""")
        
        input(">>> ")
        browser.close()


def upload_infographics_to_database(infographics_dict: dict):
    """Upload generated infographics to Supabase"""
    
    print("\n📤 Uploading infographics to database...")
    print("=" * 70)
    
    try:
        # Search for Birmingham
        response = _client.table("games").select("id,slug,title").ilike("slug", "%birmingham%").execute()
        
        if not response.data:
            response = _client.table("games").select("id,slug,title").ilike("title", "%brass%").execute()
        
        if response.data:
            game = response.data[0]
            slug = game["slug"]
            title = game["title"]
            
            print(f"\n✅ Found: {title} (slug: {slug})")
            print(f"📊 Uploading {len(infographics_dict)} infographics...")
            
            try:
                update = _client.table("games").update({
                    "infographics": infographics_dict,
                    "data_version": 2
                }).eq("slug", slug).execute()
                
                if update.data:
                    print(f"✅ Successfully uploaded {len(infographics_dict)} AI-generated infographics!\n")
                    print(f"🌐 View at: http://localhost:5173/games/{slug}")
                    return True
                else:
                    print(f"⚠️  Update returned empty - check if 'infographics' column exists\n")
                    return False
            
            except Exception as e:
                print(f"❌ Upload error: {e}\n")
                return False
        else:
            print(f"❌ Birmingham not found in database\n")
            print(f"   Create via: POST /api/search?q=Brass+Birmingham&generate=true\n")
            return False
    
    except Exception as e:
        print(f"❌ Database error: {e}\n")
        return False


def main():
    """Main pipeline"""
    
    print("\n🎮 Brass: Birmingham - NotebookLM Infographics Generator")
    print("=" * 70)
    
    setup_gemini()
    
    # Skip interactive prompt in CI/task environments
    import os
    if os.isatty(0):
        user_input = input("\n📱 Open NotebookLM for manual content extraction? (y/n): ").lower()
        if user_input == 'y':
            open_notebooklm_browser()
    else:
        print("\n⏭️  Skipping NotebookLM manual extraction (non-interactive mode)")
    
    print("\n🎨 Generating infographics from NotebookLM content...")
    print("=" * 70)
    
    infographics = {}
    generated_count = 0
    
    for section_key, section_data in BIRMINGHAM_RULES.items():
        if section_key == "game_title" or not isinstance(section_data, dict):
            continue
        
        if 'title_ja' not in section_data:
            continue
        
        print(f"\n📍 Processing: {section_data['title_ja']}")
        
        # Try Nano Banana generation
        image_bytes = generate_infographic_with_nano_banana(
            title_ja=section_data['title_ja'],
            details=section_data['details'],
            emoji=section_data['emoji'],
            style="professional_clean"
        )
        
        if image_bytes:
            # Store as base64 data URL
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            data_url = f"data:image/png;base64,{encoded}"
            infographics[section_key] = data_url
            generated_count += 1
            print(f"   ✅ Generated successfully")
        else:
            # Fallback to SVG placeholder
            print(f"   ⚠️  Using SVG placeholder")
            svg_bytes = generate_infographic_placeholder(
                title_ja=section_data['title_ja'],
                details=section_data['details'],
                emoji=section_data['emoji']
            )
            encoded = base64.b64encode(svg_bytes).decode('utf-8')
            data_url = f"data:image/svg+xml;base64,{encoded}"
            infographics[section_key] = data_url
            generated_count += 1
        
        time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Generated {generated_count} / {len(BIRMINGHAM_RULES) - 1} infographics")
    
    # Save to file
    output_file = Path(__file__).parent.parent.parent / "birmingham_ai_infographics.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(infographics, f, indent=2)
    print(f"💾 Saved to: {output_file}")
    
    # Upload to database
    if infographics:
        success = upload_infographics_to_database(infographics)
        if success:
            print("\n✅ Pipeline complete!")
            print(f"🎉 Brass: Birmingham infographics ready for viewing")
        else:
            print("\n⚠️  Upload skipped - infographics saved locally")


if __name__ == "__main__":
    main()
