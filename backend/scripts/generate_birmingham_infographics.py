#!/usr/bin/env python3
"""Generate SVG infographics for Birmingham"""
import base64
from pathlib import Path


def create_svg(title_jp: str, subtitle: str, color: str, emoji: str) -> str:
    """Create SVG infographic with styled layout"""
    svg_content = f'''<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:0.9" />
      <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="800" height="600" fill="url(#grad)"/>
  
  <!-- Decorative border -->
  <rect x="20" y="20" width="760" height="560" fill="none" stroke="white" stroke-width="3" rx="8"/>
  
  <!-- Accent lines -->
  <line x1="50" y1="80" x2="750" y2="80" stroke="white" stroke-width="2" opacity="0.6"/>
  <line x1="50" y1="520" x2="750" y2="520" stroke="white" stroke-width="2" opacity="0.6"/>
  
  <!-- Title -->
  <text x="400" y="220" font-family="sans-serif" font-size="56" font-weight="bold" text-anchor="middle" fill="white" text-shadow="0 2 4 rgba(0,0,0,0.3)">
    {emoji} {title_jp}
  </text>
  
  <!-- Subtitle -->
  <text x="400" y="350" font-family="sans-serif" font-size="32" text-anchor="middle" fill="white" opacity="0.95">
    {subtitle}
  </text>
  
  <!-- Decorative dots -->
  <circle cx="100" cy="500" r="8" fill="white" opacity="0.6"/>
  <circle cx="700" cy="500" r="8" fill="white" opacity="0.6"/>
  <circle cx="400" cy="550" r="6" fill="white" opacity="0.6"/>
</svg>'''
    return svg_content


def save_infographic(filename: str, svg_content: str) -> None:
    """Save SVG file"""
    output_dir = Path(__file__).parent.parent.parent / "assets" / "infographics"
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    filepath.write_text(svg_content, encoding='utf-8')
    print(f"✅ Saved: {filepath}")


def create_dataurl(svg_content: str) -> str:
    """Convert SVG string to base64 data URL"""
    encoded = base64.b64encode(svg_content.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


# Birmingham infographics
birmingham_infographics = {
    "turn_flow": {
        "emoji": "🔄",
        "title": "手番の流れ",
        "subtitle": "各プレイヤーがアクションを交互に実行",
        "color": "#8B4513",  # saddle brown
    },
    "setup": {
        "emoji": "⚙️",
        "title": "セットアップ",
        "subtitle": "工業化時代の産業ボードを配置",
        "color": "#696969",  # dim gray
    },
    "actions": {
        "emoji": "🏭",
        "title": "アクション",
        "subtitle": "工場建設、労働者雇用、商品生産",
        "color": "#A9A9A9",  # dark gray
    },
    "winning": {
        "emoji": "🏆",
        "title": "勝利条件",
        "subtitle": "最も金銭を獲得したプレイヤー",
        "color": "#DAA520",  # goldenrod
    },
    "components": {
        "emoji": "🧩",
        "title": "コンポーネント",
        "subtitle": "ワーカー、資源、建物タイル",
        "color": "#CD853F",  # peru
    },
}

print("📦 Generating Birmingham Infographics...\n")

infographics_urls = {}
for infographic_type, config in birmingham_infographics.items():
    svg = create_svg(config["title"], config["subtitle"], config["color"], config["emoji"])
    filename = f"birmingham_{infographic_type}.svg"
    save_infographic(filename, svg)
    infographics_urls[infographic_type] = create_dataurl(svg)

print(f"\n✅ Generated {len(birmingham_infographics)} infographics for Birmingham")
print(f"\nData URLs ready for upload:")
for key in infographics_urls:
    print(f"  ✓ {key}")

# Save data URLs to file
import json
output_file = Path(__file__).parent.parent.parent / "birmingham_infographics_urls.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(infographics_urls, f, indent=2)
print(f"\n📄 Saved URLs to: {output_file}")
