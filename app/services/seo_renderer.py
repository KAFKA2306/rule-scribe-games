import os
import json
from datetime import datetime, timedelta
from app.core.supabase import _client, _TABLE

def generate_seo_html(slug: str) -> str:
    """
    Fetches game data and injects SEO meta tags into the index.html template.
    """
    # 1. Fetch game data
    try:
        response = _client.table(_TABLE).select("*").eq("slug", slug).single().execute()
        game = response.data
    except Exception as e:
        print(f"Error fetching game for SEO: {e}")
        game = None

    # 2. Prepare Meta Data
    if game:
        title = game.get("title_ja") or game.get("title") or game.get("name") or "Untitled"
        description = game.get("summary") or game.get("description") or f"「{title}」のルールをAIが瞬時に要約。インスト時間を短縮。"
        image_url = game.get("image_url")
        
        # Ensure image is absolute URL
        if image_url and not image_url.startswith("http"):
            image_url = f"https://bodoge-no-mikata.vercel.app{image_url}"
        elif not image_url:
             image_url = f"https://bodoge-no-mikata.vercel.app/assets/games/{slug}.png"
             
        published = game.get("published_year")
        
        # Prepare structured data (JSON-LD)
        structured_data = {
            "@context": "https://schema.org",
            "@type": "Game",
            "name": title,
            "description": description,
            "image": image_url,
            "url": f"https://bodoge-no-mikata.vercel.app/games/{slug}",
        }
        
        if game.get("min_players") or game.get("max_players"):
            structured_data["numberOfPlayers"] = {
                "@type": "QuantitativeValue",
                "minValue": game.get("min_players"),
                "maxValue": game.get("max_players") or game.get("min_players")
            }
            
        if game.get("min_age"):
            structured_data["audience"] = {
                "@type": "PeopleAudience",
                "suggestedMinAge": game.get("min_age")
            }
            
        if game.get("play_time"):
             structured_data["timeRequired"] = {
                 "@type": "Duration",
                 "value": f"PT{game.get('play_time')}M"
             }

        json_ld = json.dumps(structured_data, ensure_ascii=False)
    else:
        # Fallback for known slug but missing data, or just error
        title = "ボドゲのミカタ"
        description = "世界中のボードゲームのルールをAIが要約・検索できるツール"
        image_url = "https://bodoge-no-mikata.vercel.app/og-image.png"
        json_ld = ""

    # 3. Read Template
    # In Vercel, the pure static files from frontend build are usually in a specific location.
    # But often we just want to read the 'index.html' that Vite produced.
    # Depending on deployment, it might be in 'frontend/dist/index.html' or just 'public/index.html' if copy is done.
    # For now, let's try to locate it relative to this file.
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Try different common paths for index.html
    possible_paths = [
        os.path.join(base_dir, "frontend", "dist", "index.html"), # Standard Vite build
        os.path.join(base_dir, "public", "index.html"), # sometimes moved here
        os.path.join(base_dir, "index.html"), # root
    ]
    
    html_content = ""
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                html_content = f.read()
            break
            
    if not html_content:
        # Fallback if file not found (e.g. locally if not built)
        # We'll return a basic skeleton so bots verify the tags, 
        # but real user might see broken page if JS bundle lines aren't there.
        # Ideally we should error or fallback.
        print("Warning: index.html template not found.")
        return f"<html><head><title>{title}</title></head><body><h1>Template not found</h1></body></html>"

    # 4. Inject Tags
    # We replace <title>...</title> and widely generic meta tags
    
    # Replace Title
    html_content = html_content.replace(
        "ボドゲのミカタ | AIでルールを瞬時に要約。インスト時間を短縮", 
        f"{title} | ボドゲのミカタ"
    )
    
    # Replace Description (using regex or simple replacement if we know exact string)
    # The template has a specific description we saw in index.html.
    old_desc = "「説明書を読むのが面倒」「インスト準備に時間がかかる」そんな悩みをAIが解決。ボドゲのミカタは、世界中のボードゲームのルールを瞬時に要約・検索できるツールです。海外ゲームの和訳や、プレイ中のルール確認にも最適。"
    html_content = html_content.replace(old_desc, description)
    
    # Replace OG info (simplistic replacement, assuming specific order/format matches source)
    # Ideally use a soup library but keep dependencies minimal.
    # We will inject NEW tags at the end of <head> to override or strictly replace if possible.
    # Let's try appending to <head> as it's safer than regex on minified HTML.
    # But for Title/Desc/OG, duplicate tags are bad. 
    # Let's try to act on the 'property="og:title" content="..."' segments.
    
    # Actually, simpler strategy: 
    # Just inject the NEW tags right before </head>. 
    # Browsers and Bots often take the LAST definition or we can rely on React Helmet clearing properly once it hydrates (if it does).
    # But for raw HTML, duplicates are messy.
    # Let's try to target the known placeholders from verified index.html
    
    # Target specific META tags if possible.
    # We know the specific strings from the `view_file` of `frontend/index.html`.
    
    replacements = {
        'content="ボドゲのミカタ | AIでルールを瞬時に要約。インスト時間を短縮"': f'content="{title} | ボドゲのミカタ"',
        'content="https://bodoge-no-mikata.vercel.app/og-image.png"': f'content="{image_url}"',
    }
    
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)

    # Inject JSON-LD
    if json_ld:
        script_tag = f'<script type="application/ld+json">{json_ld}</script>'
        html_content = html_content.replace("</head>", f"{script_tag}</head>")
        
    return html_content
