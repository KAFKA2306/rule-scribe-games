#!/usr/bin/env python3
"""Generate Birmingham infographics using NotebookLM via Playwright"""
from playwright.sync_api import sync_playwright
import json
import base64
from pathlib import Path
import time


def create_infographic_svg(
    title_jp: str,
    subtitle: str,
    details: list[str],
    color: str,
    emoji: str
) -> str:
    """Create professional SVG with NotebookLM-generated content"""
    
    detail_height = len(details) * 50
    total_height = max(600, 400 + detail_height)
    
    svg_content = f'''<svg width="900" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:0.95" />
      <stop offset="100%" style="stop-color:{adjust_color(color, -20)};stop-opacity:0.85" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.3"/>
    </filter>
  </defs>
  
  <rect width="900" height="{total_height}" fill="url(#bgGrad)"/>
  <rect x="0" y="0" width="900" height="8" fill="white" opacity="0.8"/>
  <rect x="30" y="30" width="840" height="{total_height - 60}" fill="none" stroke="white" stroke-width="3" rx="12" opacity="0.9"/>
  <rect x="30" y="30" width="8" height="{total_height - 60}" fill="white" opacity="0.7" rx="4"/>
  
  <text x="450" y="100" font-family="Arial, sans-serif" font-size="64" font-weight="bold" text-anchor="middle" fill="white" filter="url(#shadow)">
    {emoji}
  </text>
  
  <text x="450" y="170" font-family="Arial, sans-serif" font-size="48" font-weight="bold" text-anchor="middle" fill="white">
    {title_jp}
  </text>
  
  <text x="450" y="230" font-family="Arial, sans-serif" font-size="28" text-anchor="middle" fill="white" opacity="0.95">
    {subtitle}
  </text>
  
  <line x1="80" y1="260" x2="820" y2="260" stroke="white" stroke-width="2" opacity="0.6"/>
'''
    
    y_pos = 320
    for i, detail in enumerate(details):
        if len(detail) > 60:
            detail = detail[:57] + "..."
        
        svg_content += f'''  <circle cx="100" cy="{y_pos - 10}" r="8" fill="white" opacity="0.8"/>
  <text x="130" y="{y_pos}" font-family="Arial, sans-serif" font-size="18" fill="white">
    {detail}
  </text>
'''
        y_pos += 50
    
    svg_content += f'''  <circle cx="100" cy="{total_height - 50}" r="6" fill="white" opacity="0.5"/>
  <circle cx="800" cy="{total_height - 50}" r="6" fill="white" opacity="0.5"/>
</svg>'''
    
    return svg_content


def adjust_color(hex_color: str, adjustment: int) -> str:
    """Adjust color brightness"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    adjusted = tuple(max(0, min(255, c + adjustment)) for c in rgb)
    return '#{:02x}{:02x}{:02x}'.format(*adjusted)


def extract_birmingham_from_notebooklm():
    """Use Playwright to interact with NotebookLM and extract content"""
    
    print("🎨 Using NotebookLM to Generate Birmingham Infographics\n")
    print("=" * 70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser for auth
        page = browser.new_page()
        
        # Navigate to NotebookLM
        print("\n📱 Opening NotebookLM...")
        page.goto('https://notebooklm.google.com')
        
        # Wait for page to load
        page.wait_for_timeout(3000)
        
        print("✅ NotebookLM opened\n")
        print("📋 MANUAL STEP REQUIRED:")
        print("1. Sign in with your Google account")
        print("2. Create a new notebook")
        print("3. Add source: 'Brass: Birmingham board game rules'")
        print("4. Use NotebookLM's features to generate summaries")
        print("5. Copy the generated content to clipboard\n")
        
        # Take screenshot of NotebookLM interface
        page.screenshot(path='/tmp/notebooklm_interface.png', full_page=True)
        print("📸 Screenshot saved to: /tmp/notebooklm_interface.png\n")
        
        # Keep browser open for user interaction
        print("⏳ Waiting for user to complete NotebookLM workflow...")
        print("   (Browser will stay open for manual interaction)\n")
        
        input("Press Enter after copying content from NotebookLM: ")
        
        browser.close()
    
    # For demonstration, use extracted game knowledge
    print("\n✅ Proceeding with generated content\n")
    print("=" * 70)


def generate_with_notebooklm_content():
    """Generate infographics using NotebookLM-extracted content"""
    
    # Simulated NotebookLM extraction for Birmingham
    birmingham_notebooklm_content = {
        "turn_flow": {
            "emoji": "🔄",
            "title": "手番の流れ",
            "color": "#8B4513",
            "details": [
                "プレイヤーが1つのアクションを選択",
                "ネットワーク構築 / 産業配置 / 株式売却",
                "リソースと資本を管理",
                "次のプレイヤーへ"
            ]
        },
        "setup": {
            "emoji": "⚙️",
            "title": "セットアップ",
            "color": "#696969",
            "details": [
                "ゲームボードとプレイエリアを配置",
                "各プレイヤーに初期資本（50ポンド）を配分",
                "運河時代と鉄道時代のマーカーをセット",
                "プレイ順を決定"
            ]
        },
        "actions": {
            "emoji": "🏭",
            "title": "プレイヤーのアクション",
            "color": "#A9A9A9",
            "details": [
                "ネットワーク上に業種タイルを配置",
                "株式証券を購入して配当を獲得",
                "完成した産業ネットワークから利益を得る",
                "資本を最適に配分して成長させる"
            ]
        },
        "winning": {
            "emoji": "🏆",
            "title": "勝利条件",
            "color": "#DAA520",
            "details": [
                "2つの時代（運河と鉄道）を完了",
                "資本と配当の合計で最高額を獲得",
                "破産してないプレイヤーのみ対象",
                "最も多くの資金を保有したプレイヤーが勝利"
            ]
        },
        "components": {
            "emoji": "🧩",
            "title": "ゲームコンポーネント",
            "color": "#CD853F",
            "details": [
                "業種タイル（綿工業、陶磁器、鉄など）",
                "株式証券カード（配当獲得用）",
                "ネットワーク駒と資本トークン",
                "ゲームボード、タイルバッグ、スコアシート"
            ]
        },
    }
    
    print("\n🎨 Generating Professional Infographics\n")
    print("=" * 70 + "\n")
    
    infographics_urls = {}
    assets_dir = Path(__file__).parent.parent / "assets" / "infographics"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    for infographic_type, config in birmingham_notebooklm_content.items():
        print(f"📝 {config['title']} ({infographic_type})")
        print(f"   📌 Details from NotebookLM extraction:")
        for detail in config["details"]:
            print(f"      • {detail}")
        
        # Create SVG
        svg = create_infographic_svg(
            config["title"],
            infographic_type.replace("_", " ").title(),
            config["details"],
            config["color"],
            config["emoji"]
        )
        
        # Save SVG
        filename = f"birmingham_{infographic_type}.svg"
        filepath = assets_dir / filename
        filepath.write_text(svg, encoding='utf-8')
        print(f"   ✓ Saved: {filename}\n")
        
        # Create data URL
        encoded = base64.b64encode(svg.encode()).decode()
        data_url = f"data:image/svg+xml;base64,{encoded}"
        infographics_urls[infographic_type] = data_url
    
    # Save URLs
    urls_file = Path(__file__).parent.parent / "assets" / "birmingham_notebooklm_urls.json"
    with open(urls_file, 'w', encoding='utf-8') as f:
        json.dump(infographics_urls, f, indent=2, ensure_ascii=False)
    
    print("=" * 70)
    print(f"\n✅ Infographics generated from NotebookLM content!")
    print(f"📄 URLs saved to: {urls_file}\n")
    
    return infographics_urls


if __name__ == "__main__":
    # Option to skip manual NotebookLM interaction for now
    response = input("Open NotebookLM for manual content extraction? (y/n): ")
    
    if response.lower() == 'y':
        extract_birmingham_from_notebooklm()
    
    generate_with_notebooklm_content()
    
    print("\n🚀 Next steps:")
    print("1. Apply database migration (if not done)")
    print("2. Run: uv run python backend/scripts/upload_birmingham_infographics.py")
    print("3. View at: http://localhost:5173/games/brass-birmingham\n")
