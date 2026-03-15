#!/usr/bin/env python3
"""
Generate sample infographic SVG images for board games.
Creates realistic placeholder infographics that can be displayed in the carousel.
"""
import base64
from pathlib import Path


def create_svg_infographic(title: str, subtitle: str, color_hex: str, width=800, height=600):
    """Create a sample infographic as SVG"""
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="{color_hex}"/>
  
  <!-- Gradient overlay -->
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:rgba(0,0,0,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgba(0,0,0,0.2);stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#grad)"/>
  
  <!-- Top border -->
  <line x1="50" y1="80" x2="{width-50}" y2="80" stroke="white" stroke-width="3"/>
  
  <!-- Bottom border -->
  <line x1="50" y1="{height-80}" x2="{width-50}" y2="{height-80}" stroke="white" stroke-width="3"/>
  
  <!-- Title -->
  <text x="{width//2}" y="220" font-size="56" font-weight="bold" fill="white" text-anchor="middle" font-family="Arial, sans-serif">
    {title}
  </text>
  
  <!-- Subtitle -->
  <text x="{width//2}" y="350" font-size="32" fill="#dcdcdc" text-anchor="middle" font-family="Arial, sans-serif">
    {subtitle}
  </text>
  
  <!-- Decorative circles -->
  <circle cx="100" cy="100" r="20" fill="white" opacity="0.3"/>
  <circle cx="{width-100}" cy="{height-100}" r="20" fill="white" opacity="0.3"/>
</svg>'''
    return svg


def generate_infographics():
    """Generate all infographic types for Splendor"""
    output_dir = Path(__file__).parent.parent.parent / "assets" / "infographics"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    infographics = {
        "turn_flow": {
            "title": "🔄 手番の流れ",
            "subtitle": "3つのアクションから1つを選択",
            "color": "#FF6B6B",  # Red
        },
        "setup": {
            "title": "⚙️ セットアップ",
            "subtitle": "発展カード・宝石・貴族タイルを配置",
            "color": "#4ECDC4",  # Teal
        },
        "actions": {
            "title": "🎲 アクション一覧",
            "subtitle": "A: 宝石3色 | B: 同色2枚 | C: カード購入 | D: 予約+黄金",
            "color": "#45B7D1",  # Blue
        },
        "winning": {
            "title": "🏆 勝利条件",
            "subtitle": "15点以上の名声ポイントを集める",
            "color": "#FFA07A",  # Salmon
        },
        "components": {
            "title": "🧩 ゲームコンポーネント",
            "subtitle": "発展カード・宝石トークン・貴族タイル",
            "color": "#98D8C8",  # Mint
        },
    }
    
    urls = {}
    for key, config in infographics.items():
        # Generate SVG
        svg_content = create_svg_infographic(
            config["title"],
            config["subtitle"],
            config["color"]
        )
        
        # Save locally
        output_path = output_dir / f"splendor_{key}.svg"
        output_path.write_text(svg_content)
        print(f"✓ Generated: {output_path}")
        
        # For this demo, we'll use data URLs (embedded SVG)
        # In production, you'd upload these to Cloudinary or a CDN
        data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"
        urls[key] = data_url
    
    return urls


def generate_catan_infographics():
    """Generate infographics for Catan (partial demo)"""
    output_dir = Path(__file__).parent.parent.parent / "assets" / "infographics"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    infographics = {
        "setup": {
            "title": "⚙️ セットアップ",
            "subtitle": "六角形タイルを配置してゲーム盤を作る",
            "color": "#D2B48C",  # Tan
        },
        "actions": {
            "title": "🎲 ターンのアクション",
            "subtitle": "サイコロ振る → リソース受け取る → 建設または交易",
            "color": "#90EE90",  # Light Green
        },
    }
    
    urls = {}
    for key, config in infographics.items():
        svg_content = create_svg_infographic(
            config["title"],
            config["subtitle"],
            config["color"]
        )
        
        output_path = output_dir / f"catan_{key}.svg"
        output_path.write_text(svg_content)
        print(f"✓ Generated: {output_path}")
        
        data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"
        urls[key] = data_url
    
    return urls


if __name__ == "__main__":
    print("🎨 Generating Sample Infographics")
    print("=" * 50)
    
    splendor_urls = generate_infographics()
    print("\n✓ Splendor infographics:")
    for key, url in splendor_urls.items():
        print(f"  - {key}: {url}")
    
    catan_urls = generate_catan_infographics()
    print("\n✓ Catan infographics:")
    for key, url in catan_urls.items():
        print(f"  - {key}: {url}")
    
    # Output as JSON for use in upload script
    import json
    data = {
        "splendor": splendor_urls,
        "catan": catan_urls,
    }
    
    output_file = Path(__file__).parent / "infographics_urls.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ URLs saved to: {output_file}")
