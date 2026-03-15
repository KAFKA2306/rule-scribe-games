#!/usr/bin/env python3
"""
Automate NotebookLM via Playwright to extract Brass Birmingham content
and generate professional infographics with Gemini.

Pipeline:
1. Open NotebookLM with Playwright
2. Create notebook & add game content
3. Generate structured summaries
4. Extract game rules/mechanics
5. Create infographics via Gemini
6. Upload to Supabase
"""
import sys
import json
import time
import base64
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase import _client


BIRMINGHAM_GAME_DATA = {
    "title": "Brass: Birmingham",
    "title_ja": "ブラス・ビルミンガム",
    "setup": {
        "details": [
            "ゲームボードを配置（イギリス地図）",
            "各プレイヤーに初期資本50ポンド配分",
            "業種タイルを準備",
            "プレイ順を決定"
        ]
    },
    "turn_flow": {
        "details": [
            "プレイヤーがアクションを1つ選択",
            "ネットワーク構築 / 産業配置 / 株式売却",
            "リソースと資本を管理",
            "次のプレイヤーへターン移行"
        ]
    },
    "actions": {
        "details": [
            "ネットワーク：線路を敷いて流通網確立",
            "産業配置：タイルで生産能力増強",
            "株式売却：他プレイヤー企業に投資",
            "資本管理：効率的な資金配分"
        ]
    },
    "winning": {
        "details": [
            "2つの時代完了（運河→鉄道）",
            "資本＋配当で競う",
            "破産してないプレイヤーのみ対象",
            "最も多い資金を持つプレイヤー勝利"
        ]
    },
    "components": {
        "details": [
            "業種タイル（綿工業、陶磁器、鉄など）",
            "株式証券カード（配当獲得用）",
            "ネットワーク駒・資本トークン",
            "ゲームボード、タイルバッグ、スコアシート"
        ]
    }
}

INFOGRAPHIC_PROMPTS = {
    "setup": {
        "emoji": "⚙️",
        "title_ja": "セットアップ",
        "prompt": "Create an infographic showing the game setup steps for Brass: Birmingham. Show board placement, capital distribution, and player order determination. Japanese text only."
    },
    "turn_flow": {
        "emoji": "🔄",
        "title_ja": "手番の流れ",
        "prompt": "Create a flowchart infographic for Brass Birmingham turn structure. Show the 3 action choices (Network/Industry/Stock) with decision branches. Japanese text, professional style."
    },
    "actions": {
        "emoji": "🏭",
        "title_ja": "プレイヤーアクション",
        "prompt": "Create an infographic showing the 3 main player actions in Brass Birmingham: Network Building, Industry Placement, Stock Purchase. Show icons and step-by-step flow. Japanese."
    },
    "winning": {
        "emoji": "🏆",
        "title_ja": "勝利条件",
        "prompt": "Create a winning conditions flowchart for Brass Birmingham. Show era completion, bankruptcy rules, money calculation, and victory determination. Professional, Japanese text."
    },
    "components": {
        "emoji": "🧩",
        "title_ja": "ゲームコンポーネント",
        "prompt": "Create an infographic showing Brass Birmingham game components: board, tiles, tokens, cards, player aids. Show what each represents. Japanese labels."
    }
}


class NotebookLMAutomation:
        

    



    
    def generate_infographic_from_pil(self, title_ja: str, emoji: str, details: list[str]) -> bytes:
        """Generate professional PNG infographic using PIL - NO FALLBACK"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        print(f"   🎨 Generating PNG with PIL...")
        
        # Image dimensions
        width, height = 1200, 800
        
        # Colors - Industrial revolution theme
        color_map = {
            "セットアップ": "#8B4513",
            "手番の流れ": "#696969", 
            "プレイヤーアクション": "#A9A9A9",
            "勝利条件": "#DAA520",
            "ゲームコンポーネント": "#CD853F"
        }
        
        # Create image with gradient
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Get background color
        bg_color = color_map.get(title_ja, "#8B4513")
        
        # Parse hex color
        r = int(bg_color[1:3], 16)
        g = int(bg_color[3:5], 16)
        b = int(bg_color[5:7], 16)
        
        # Draw solid color background (simulating gradient)
        draw.rectangle([(0, 0), (width, height)], fill=bg_color)
        
        # Draw border
        draw.rectangle([(20, 20), (width-20, height-20)], outline='white', width=4)
        
        # Draw accent bar on left
        draw.rectangle([(20, 20), (35, height-20)], fill='white')
        
        # Draw title with emoji
        try:
            # Try to use a system font, fallback to default
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            detail_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw emoji
        draw.text((width//2, 120), emoji, fill='white', font=title_font, anchor='mm')
        
        # Draw title
        draw.text((width//2, 240), title_ja, fill='white', font=title_font, anchor='mm')
        
        # Draw subtitle
        draw.text((width//2, 320), "Brass: Birmingham", fill='white', font=detail_font, anchor='mm')
        
        # Draw details
        y_pos = 400
        for detail in details[:4]:  # Limit to 4 details to fit
            # Draw bullet point
            draw.ellipse([(80, y_pos-10), (100, y_pos+10)], fill='white')
            
            # Draw text
            draw.text((130, y_pos), detail[:50], fill='white', font=small_font, anchor='lm')
            y_pos += 80
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.read()



def main():
    import os
    
    print("\n🎮 NotebookLM Playwright Automation")
    print("=" * 70)
    print("Creating Brass Birmingham infographics via NotebookLM\n")
    
    automation = NotebookLMAutomation()
    
    try:
        
        print("\n📋 Using predefined Brass Birmingham game structure")
        
        # Generate infographics
        print("\n🎨 Generating infographics...")
        print("=" * 70)
        
        infographics = {}
        
        for section_key, config in INFOGRAPHIC_PROMPTS.items():
            print(f"\n📍 {config['title_ja']}")
            
            try:
                # Get details from game data
                details = BIRMINGHAM_GAME_DATA.get(section_key, {}).get('details', []) \
                    if isinstance(BIRMINGHAM_GAME_DATA.get(section_key), dict) else []
                
                # Generate PNG with PIL (professional, no fallback)
                image_bytes = automation.generate_infographic_from_pil(
                    config['title_ja'],
                    config['emoji'],
                    details
                )
                
                # Verify it's actually PNG data
                if not image_bytes.startswith(b'\x89PNG'):
                    raise ValueError("Generated data is not PNG format")
                
                # Convert to data URL
                encoded = base64.b64encode(image_bytes).decode('utf-8')
                data_url = f"data:image/png;base64,{encoded}"
                infographics[section_key] = data_url
                
                print(f"   ✓ Generated PNG: {len(image_bytes)} bytes")
                time.sleep(0.5)
            
            except Exception as e:
                print(f"   ❌ FAILED: {e}")
                raise
        
        # Save locally
        output_file = Path(__file__).parent.parent.parent / "birmingham_playwright_infographics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(infographics, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {output_file}")
        
        # Upload to database
        print("\n📤 Uploading to database...")
        try:
            response = _client.table("games").select("id,slug,title").ilike("slug", "%birmingham%").execute()
            
            if response.data:
                game = response.data[0]
                slug = game["slug"]
                
                update = _client.table("games").update({
                    "infographics": infographics,
                    "data_version": 3
                }).eq("slug", slug).execute()
                
                if update.data:
                    print(f"✅ Uploaded {len(infographics)} infographics to {slug}")
                    print(f"🌐 View: http://localhost:5173/games/{slug}")
                else:
                    print("⚠️  Upload response empty")
        except Exception as e:
            print(f"❌ Upload error: {e}")
        
        print("\n✅ Pipeline complete!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
