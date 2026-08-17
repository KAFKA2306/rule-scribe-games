import html
import json
import logging
import os
import re
from pathlib import Path

from app.core.supabase import get_by_slug

logger = logging.getLogger(__name__)
BASE_URL = "https://bodoge-no-mikata.vercel.app"


def _replace_or_insert_tag(document: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, document, count=1, flags=re.IGNORECASE | re.DOTALL)
    if count:
        return updated
    return document.replace("</head>", f"  {replacement}\n</head>", 1)


def _meta_tag(document: str, *, attr: str, key: str, content: str) -> str:
    escaped_content = html.escape(content, quote=True)
    escaped_key = re.escape(key)
    pattern = rf'<meta\b(?=[^>]*\b{attr}=["\']{escaped_key}["\'])[^>]*>'
    replacement = f'<meta {attr}="{html.escape(key, quote=True)}" content="{escaped_content}" />'
    return _replace_or_insert_tag(document, pattern, replacement)


def _safe_json_script(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def _page_title(game: dict, title: str) -> str:
    structured_data = game.get("structured_data")
    has_strategy = isinstance(structured_data, dict) and bool(structured_data.get("strategy_analysis"))
    strategy_label = "・戦略" if has_strategy else ""
    return f"「{title}」のルール{strategy_label}・インスト要約 | ボドゲのミカタ"


async def generate_seo_html(slug: str) -> str | None:
    game = await get_by_slug(slug)
    if not game:
        return None

    title = str(game.get("title_ja") or game.get("title") or game.get("name") or "Untitled")
    description = str(game.get("summary") or game.get("description") or "")
    image_url = str(game.get("image_url") or f"{BASE_URL}/assets/no-image.webp")
    if image_url.startswith("/"):
        image_url = f"{BASE_URL}{image_url}"

    game_url = f"{BASE_URL}/games/{slug}"
    page_title = _page_title(game, title)
    seo_description = description or f"「{title}」の登録済みルール要約と出典情報を確認できます。"

    structured_data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Game",
        "name": title,
        "description": seo_description,
        "image": image_url,
        "url": game_url,
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
        structured_data["timeRequired"] = f"PT{game.get('play_time')}M"

    root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
    possible_paths = [
        root / "frontend" / "dist" / "index.html",
        root / "public" / "index.html",
        root / "index.html",
    ]
    html_content = ""
    for path in possible_paths:
        try:
            if path.exists():
                html_content = path.read_text(encoding="utf-8")
                break
        except Exception as exc:
            logger.warning(f"Error reading path {path}: {exc}")

    if not html_content:
        logger.error(f"index.html template not found in {possible_paths}")
        html_content = '<html lang="ja"><head><title>ボドゲのミカタ</title></head><body><div id="root"></div></body></html>'

    escaped_title = html.escape(page_title, quote=False)
    html_content = _replace_or_insert_tag(
        html_content,
        r"<title\b[^>]*>.*?</title>",
        f"<title>{escaped_title}</title>",
    )
    html_content = _meta_tag(html_content, attr="name", key="description", content=seo_description)
    html_content = _meta_tag(html_content, attr="property", key="og:title", content=page_title)
    html_content = _meta_tag(html_content, attr="property", key="og:description", content=seo_description)
    html_content = _meta_tag(html_content, attr="property", key="og:url", content=game_url)
    html_content = _meta_tag(html_content, attr="property", key="og:image", content=image_url)
    html_content = _meta_tag(html_content, attr="name", key="twitter:title", content=page_title)
    html_content = _meta_tag(html_content, attr="name", key="twitter:description", content=seo_description)
    html_content = _meta_tag(html_content, attr="name", key="twitter:image", content=image_url)

    canonical_tag = f'<link rel="canonical" href="{html.escape(game_url, quote=True)}" />'
    html_content = _replace_or_insert_tag(
        html_content,
        r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>',
        canonical_tag,
    )

    json_ld = _safe_json_script(structured_data)
    script_tag = f'<script type="application/ld+json" data-game-seo="true">{json_ld}</script>'
    html_content = html_content.replace("</head>", f"  {script_tag}\n</head>", 1)

    safe_title = html.escape(title)
    safe_summary = html.escape(str(game.get("summary") or ""))
    safe_rules = html.escape(str(game.get("rules_content") or "")[:2000])
    players_info = ""
    if game.get("min_players"):
        max_players = game.get("max_players") or game.get("min_players")
        players_info = (
            f"<p><strong>プレイ人数:</strong> {html.escape(str(game.get('min_players')))}-"
            f"{html.escape(str(max_players))}人</p>"
        )
    time_info = ""
    if game.get("play_time"):
        time_info = f"<p><strong>プレイ時間:</strong> {html.escape(str(game.get('play_time')))}分</p>"

    ssr_content = f"""<div id="root">
  <article itemscope itemtype="https://schema.org/Game" data-ssr-game="true">
    <nav aria-label="ゲーム一覧へのナビゲーション">
      <a href="/">ゲーム一覧</a>
    </nav>
    <h1 itemprop="name">{safe_title}</h1>
    <section>
      <h2>要約</h2>
      <p itemprop="description">{safe_summary}</p>
    </section>
    <section>
      <h2>基本情報</h2>
      {players_info}
      {time_info}
    </section>
    <section>
      <h2>ルール</h2>
      <pre itemprop="text">{safe_rules}</pre>
    </section>
  </article>
</div>"""
    return html_content.replace('<div id="root"></div>', ssr_content, 1)
