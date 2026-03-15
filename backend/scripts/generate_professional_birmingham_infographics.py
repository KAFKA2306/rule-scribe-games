#!/usr/bin/env python3
"""Generate professional Birmingham infographics using Gemini + SVG"""
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.gemini import GeminiClient
from app.core.llm_manager import LLMKeyRotator
import json


def create_professional_svg(
    title_jp: str,
    subtitle: str,
    details: list[str],
    color: str,
    emoji: str
) -> str:
    """Create professional SVG infographic with details"""
    
    # Calculate dynamic height based on details
    base_height = 600
    detail_height = len(details) * 50
    total_height = max(base_height, 400 + detail_height)
    
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
  
  <!-- Background -->
  <rect width="900" height="{total_height}" fill="url(#bgGrad)"/>
  
  <!-- Top accent bar -->
  <rect x="0" y="0" width="900" height="8" fill="white" opacity="0.8"/>
  
  <!-- Content frame -->
  <rect x="30" y="30" width="840" height="{total_height - 60}" fill="none" stroke="white" stroke-width="3" rx="12" opacity="0.9"/>
  
  <!-- Decorative side accent -->
  <rect x="30" y="30" width="8" height="{total_height - 60}" fill="white" opacity="0.7" rx="4"/>
  
  <!-- Title section -->
  <text x="450" y="100" font-family="Arial, sans-serif" font-size="64" font-weight="bold" text-anchor="middle" fill="white" filter="url(#shadow)">
    {emoji}
  </text>
  
  <text x="450" y="170" font-family="Arial, sans-serif" font-size="48" font-weight="bold" text-anchor="middle" fill="white">
    {title_jp}
  </text>
  
  <!-- Subtitle -->
  <text x="450" y="230" font-family="Arial, sans-serif" font-size="28" text-anchor="middle" fill="white" opacity="0.95">
    {subtitle}
  </text>
  
  <!-- Separator line -->
  <line x1="80" y1="260" x2="820" y2="260" stroke="white" stroke-width="2" opacity="0.6"/>
  
  <!-- Details section -->
'''
    
    y_pos = 320
    for i, detail in enumerate(details):
        # Truncate long text
        if len(detail) > 60:
            detail = detail[:57] + "..."
        
        svg_content += f'''  <!-- Detail {i+1} -->
  <circle cx="100" cy="{y_pos - 10}" r="8" fill="white" opacity="0.8"/>
  <text x="130" y="{y_pos}" font-family="Arial, sans-serif" font-size="18" fill="white">
    {detail}
  </text>
'''
        y_pos += 50
    
    svg_content += f'''
  <!-- Bottom decorative elements -->
  <circle cx="100" cy="{total_height - 50}" r="6" fill="white" opacity="0.5"/>
  <circle cx="800" cy="{total_height - 50}" r="6" fill="white" opacity="0.5"/>
</svg>'''
    
    return svg_content


def adjust_color(hex_color: str, adjustment: int) -> str:
    """Adjust color brightness"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    adjusted = tuple(max(0, min(255, c + adjustment)) for c in rgb)
    return '#{:02x}{:02x}{:02x}'.format(*adjusted)


async def generate_infographics():
    """Generate professional infographics using Gemini descriptions"""
    
    print("🎨 Generating Professional Birmingham Infographics\n")
    print("=" * 60 + "\n")
    
    # Initialize Gemini
    _gemini = GeminiClient()
    _key_rotator = LLMKeyRotator("GEMINI_API_KEY")
    
    # Define infographic types with game knowledge
    infographics = {
        "turn_flow": {
            "emoji": "🔄",
            "title": "手番の流れ",
            "color": "#8B4513",
            "details": ["ネットワーク配置", "産業建設", "株式取引", "次のプレイヤーへ"]
        },
        "setup": {
            "emoji": "⚙️",
            "title": "セットアップ",
            "color": "#696969",
            "details": ["ボード配置", "産業マーカー配置", "初期資本配分", "プレイ順決定"]
        },
        "actions": {
            "emoji": "🏭",
            "title": "プレイヤーのアクション",
            "color": "#A9A9A9",
            "details": ["ネットワーク構築", "産業タイル配置", "株式取引実行", "資源管理"]
        },
        "winning": {
            "emoji": "🏆",
            "title": "勝利条件",
            "color": "#DAA520",
            "details": ["2時代完了後", "最高金銭獲得者", "破産しない", "得点集計"]
        },
        "components": {
            "emoji": "🧩",
            "title": "ゲームコンポーネント",
            "color": "#CD853F",
            "details": ["産業タイル", "株式証券", "ネットワーク駒", "資本カード"]
        },
    }
    
    infographics_urls = {}
    assets_dir = Path(__file__).parent.parent.parent / "assets" / "infographics"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    for infographic_type, config in infographics.items():
        print(f"📝 Generating: {config['title']} ({infographic_type})")
        
        details = config.get("details", ["説明1", "説明2", "説明3"])
        print(f"   ✓ Using {len(details)} game details")
        
        # Create SVG
        svg = create_professional_svg(
            config["title"],
            infographic_type.replace("_", " ").title(),
            details,
            config["color"],
            config["emoji"]
        )
        
        # Save SVG
        filename = f"birmingham_{infographic_type}.svg"
        filepath = assets_dir / filename
        filepath.write_text(svg, encoding='utf-8')
        print(f"   ✓ Saved SVG: {filepath.name}")
        
        # Create data URL
        encoded = base64.b64encode(svg.encode()).decode()
        data_url = f"data:image/svg+xml;base64,{encoded}"
        infographics_urls[infographic_type] = data_url
        print(f"   ✓ Created data URL\n")
    
    # Save URLs
    urls_file = assets_dir.parent / "birmingham_professional_urls.json"
    with open(urls_file, 'w', encoding='utf-8') as f:
        json.dump(infographics_urls, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"\n✅ Professional infographics generated!")
    print(f"📄 URLs saved to: {urls_file}\n")
    print(f"📸 SVG files saved to: {assets_dir}\n")
    
    return infographics_urls


if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_infographics())
