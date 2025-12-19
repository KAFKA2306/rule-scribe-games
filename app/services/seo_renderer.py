import os
import json
from app.core.supabase import _client, _TABLE


def generate_seo_html(slug: str) -> str:
    response = _client.table(_TABLE).select("*").eq("slug", slug).single().execute()
    game = response.data

    title = game.get("title_ja") or game.get("title") or game.get("name")
    description = game.get("summary") or game.get("description")
    image_url = game.get("image_url")

    if image_url and not image_url.startswith("http"):
        image_url = f"https://bodoge-no-mikata.vercel.app{image_url}"

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
            "maxValue": game.get("max_players") or game.get("min_players"),
        }

    if game.get("min_age"):
        structured_data["audience"] = {
            "@type": "PeopleAudience",
            "suggestedMinAge": game.get("min_age"),
        }

    if game.get("play_time"):
        structured_data["timeRequired"] = {
            "@type": "Duration",
            "value": f"PT{game.get('play_time')}M",
        }

    # Optimized SEO Title & Description based on Keyword Research
    page_title = f"「{title}」のルール・インストをAI要約 | 遊び方・3行解説"
    
    # Construct a rich description that targets "Inst" and "How to play" intent
    seo_description = f"「{title}」のルールをAIが瞬時に要約。インスト準備や遊び方の確認に。「{title}」のセットアップ、勝利条件、流れを3行で解説。"
    if description:
         seo_description += f" {description}"

    # Update structured data to use the optimized description
    structured_data["description"] = seo_description

    json_ld = json.dumps(structured_data, ensure_ascii=False)

    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    possible_paths = [
        os.path.join(base_dir, "frontend", "dist", "index.html"),
        os.path.join(base_dir, "public", "index.html"),
        os.path.join(base_dir, "index.html"),
    ]

    html_content = ""
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                html_content = f.read()
            break

    assert html_content, f"index.html template not found in {possible_paths}"

    # Replace Title
    html_content = html_content.replace(
        "ボドゲのミカタ | AIでルールを瞬時に要約。インスト時間を短縮",
        page_title,
    )

    # Replace Description (Old boilerplate -> New optimized description)
    old_desc_marker = "「説明書を読むのが面倒」「インスト準備に時間がかかる」そんな悩みをAIが解決。ボドゲのミカタは、世界中のボードゲームのルールを瞬時に要約・検索できるツールです。海外ゲームの和訳や、プレイ中のルール確認にも最適。"
    html_content = html_content.replace(old_desc_marker, seo_description)

    replacements = {
        'content="ボドゲのミカタ | AIでルールを瞬時に要約。インスト時間を短縮"': f'content="{page_title}"',
        'content="https://bodoge-no-mikata.vercel.app/og-image.png"': f'content="{image_url}"',
        'property="og:url" content="https://bodoge-no-mikata.vercel.app/"': f'property="og:url" content="https://bodoge-no-mikata.vercel.app/games/{slug}"',
        'link rel="canonical" href="https://bodoge-no-mikata.vercel.app/"': f'link rel="canonical" href="https://bodoge-no-mikata.vercel.app/games/{slug}"',
    }
    
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)

    script_tag = f'<script type="application/ld+json">{json_ld}</script>'
    html_content = html_content.replace("</head>", f"{script_tag}</head>")

    return html_content
