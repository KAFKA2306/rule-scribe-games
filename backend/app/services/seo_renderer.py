import html
import json
import logging
import os
import re
from pathlib import Path

from app.core.supabase import get_by_slug
from app.services.player_summary import project_player_summary
from app.services.presentation_projection import PresentationProjectionReadError, PresentationProjectionService
from app.services.rulesets import RuleSetService
from app.services.search_visibility import should_hide_game_from_search

logger = logging.getLogger(__name__)
BASE_URL = "https://bodoge-no-mikata.vercel.app"


class CanonicalRuleText(str):
    """Canonical rule text with the RuleSet identity used to produce it."""

    def __new__(cls, value: str, ruleset):
        instance = super().__new__(cls, value)
        instance.ruleset = ruleset
        return instance


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


def _page_title(game: dict, title: str, *, has_canonical_rules: bool) -> str:
    if not has_canonical_rules:
        return f"「{title}」の基本情報 | ボドゲのミカタ"

    structured_data = game.get("structured_data")
    has_strategy = isinstance(structured_data, dict) and bool(structured_data.get("strategy_analysis"))
    strategy_label = "・戦略" if has_strategy else ""
    return f"「{title}」のルール{strategy_label}・インスト要約 | ボドゲのミカタ"


def _player_count_projection(game: dict) -> tuple[dict[str, object] | None, str]:
    min_players = game.get("min_players")
    max_players = game.get("max_players")
    if not min_players and not max_players:
        return None, ""

    quantitative_value: dict[str, object] = {"@type": "QuantitativeValue"}
    if min_players:
        quantitative_value["minValue"] = min_players
    if max_players:
        quantitative_value["maxValue"] = max_players

    if min_players and max_players:
        label = f"{min_players}人" if min_players == max_players else f"{min_players}-{max_players}人"
    elif min_players:
        label = f"{min_players}人以上"
    else:
        label = f"最大{max_players}人"
    return quantitative_value, label


def _play_time_projection(game: dict) -> tuple[str | None, str]:
    min_minutes = game.get("play_time_min_minutes")
    max_minutes = game.get("play_time_max_minutes")
    legacy_minutes = game.get("play_time")

    if min_minutes is None and max_minutes is None and legacy_minutes is not None:
        min_minutes = legacy_minutes
        max_minutes = legacy_minutes

    if min_minutes is not None and max_minutes is not None:
        if min_minutes == max_minutes:
            return f"PT{min_minutes}M", f"{min_minutes}分"
        return None, f"{min_minutes}-{max_minutes}分"
    if min_minutes is not None:
        return None, f"{min_minutes}分以上"
    if max_minutes is not None:
        return None, f"最大{max_minutes}分"
    return None, ""


def _render_projection_rules(projection) -> str | None:
    sections = (
        ("セットアップ", projection.setup),
        ("ゲーム進行", projection.game_flow),
        ("終了条件・勝利", projection.end_condition),
        ("得点", projection.scoring),
    )
    rendered: list[str] = []
    for label, section in sections:
        if not section.items:
            continue
        rendered.append(f"## {label}\n" + "\n".join(f"- {item.text}" for item in section.items))
    return "\n\n".join(rendered) or None


async def _canonical_rule_text(slug: str) -> str | None:
    rulesets = await RuleSetService().get_by_slug(slug)
    if not rulesets or rulesets.status != "available":
        return None

    candidates = [
        ruleset
        for ruleset in rulesets.rulesets
        if ruleset.is_active and ruleset.verification_status == "source_bound"
    ]
    for ruleset in candidates:
        try:
            projection = await PresentationProjectionService().get_by_slug(
                slug,
                rule_set_id=ruleset.ruleset_id,
                language_code=ruleset.language_code or "ja",
            )
        except PresentationProjectionReadError:
            logger.exception("Canonical SSR projection failed for %s/%s", slug, ruleset.ruleset_id)
            raise
        if projection is None or projection.status != "available":
            continue
        rendered = _render_projection_rules(projection)
        if rendered:
            return CanonicalRuleText(rendered, ruleset)
    return None


def _render_ruleset_identity(canonical_rules: str | None, game: dict) -> str:
    ruleset = getattr(canonical_rules, "ruleset", None)
    facts: list[str] = []

    if ruleset is not None:
        if ruleset.edition_label:
            facts.append(f"<p><strong>版:</strong> {html.escape(str(ruleset.edition_label))}</p>")
        if ruleset.language_code:
            facts.append(f"<p><strong>言語:</strong> {html.escape(str(ruleset.language_code))}</p>")
        if ruleset.platform:
            facts.append(f"<p><strong>プラットフォーム:</strong> {html.escape(str(ruleset.platform))}</p>")
        revision = ruleset.revision_label or ruleset.source_revision
        if revision:
            facts.append(f"<p><strong>改訂:</strong> {html.escape(str(revision))}</p>")

    review_status = game.get("content_review_status")
    if review_status:
        facts.append(f"<p><strong>内容確認状態:</strong> {html.escape(str(review_status))}</p>")

    source_trust = game.get("source_trust")
    if source_trust:
        facts.append(f"<p><strong>出典の信頼状態:</strong> {html.escape(str(source_trust))}</p>")

    source_url = game.get("source_url")
    if isinstance(source_url, str) and source_url.startswith(("https://", "http://")):
        safe_url = html.escape(source_url, quote=True)
        facts.append(
            f'<p><strong>登録済み出典:</strong> <a href="{safe_url}" rel="noopener noreferrer">出典を確認</a></p>'
        )

    if not facts:
        return ""
    return "    <section>\n      <h2>出典・確認状態</h2>\n      " + "\n      ".join(facts) + "\n    </section>\n"


async def generate_seo_html(slug: str) -> str | None:
    game = await get_by_slug(slug)
    if not game:
        return None

    canonical_rules = await _canonical_rule_text(slug)
    game = project_player_summary(game, source_bound=canonical_rules is not None)

    title = str(game.get("title_ja") or game.get("title") or game.get("name") or "Untitled")
    description = str(game.get("summary") or game.get("description") or "")
    image_url = str(game.get("image_url") or f"{BASE_URL}/assets/no-image.webp")
    if image_url.startswith("/"):
        image_url = f"{BASE_URL}{image_url}"

    game_url = f"{BASE_URL}/games/{slug}"
    page_title = _page_title(game, title, has_canonical_rules=canonical_rules is not None)
    seo_description = description or f"「{title}」の登録済みルール要約と出典情報を確認できます。"
    hide_from_search = should_hide_game_from_search(game)

    structured_data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Game",
        "name": title,
        "description": seo_description,
        "image": image_url,
        "url": game_url,
    }
    player_count, player_count_label = _player_count_projection(game)
    if player_count:
        structured_data["numberOfPlayers"] = player_count
    if game.get("min_age"):
        structured_data["audience"] = {
            "@type": "PeopleAudience",
            "suggestedMinAge": game.get("min_age"),
        }
    time_required, play_time_label = _play_time_projection(game)
    if time_required:
        structured_data["timeRequired"] = time_required

    breadcrumb_data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "ゲーム一覧",
                "item": f"{BASE_URL}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": title,
                "item": game_url,
            },
        ],
    }

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
    if hide_from_search:
        html_content = _meta_tag(html_content, attr="name", key="robots", content="noindex, follow")
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
    breadcrumb_json_ld = _safe_json_script(breadcrumb_data)
    breadcrumb_script_tag = (
        f'<script type="application/ld+json" data-breadcrumb-seo="true">{breadcrumb_json_ld}</script>'
    )
    html_content = html_content.replace(
        "</head>",
        f"  {script_tag}\n  {breadcrumb_script_tag}\n</head>",
        1,
    )

    safe_title = html.escape(title)
    safe_summary = html.escape(str(game.get("summary") or ""))
    safe_rules = html.escape(canonical_rules) if canonical_rules else ""
    ruleset_identity_section = _render_ruleset_identity(canonical_rules, game)
    rules_section = ""
    if safe_rules:
        rules_section = f"""    <section>
      <h2>出典付きルール要約</h2>
      <pre itemprop="text">{safe_rules}</pre>
    </section>
"""
    players_info = ""
    if player_count_label:
        players_info = f"<p><strong>プレイ人数:</strong> {html.escape(player_count_label)}</p>"
    time_info = ""
    if play_time_label:
        time_info = f"<p><strong>プレイ時間:</strong> {html.escape(play_time_label)}</p>"

    ssr_content = f"""<div id="root">
  <article itemscope itemtype="https://schema.org/Game" data-ssr-game="true">
    <nav aria-label="パンくずリスト">
      <ol>
        <li><a href="/">ゲーム一覧</a></li>
        <li aria-current="page">{safe_title}</li>
      </ol>
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
{ruleset_identity_section}{rules_section}  </article>
</div>"""
    return html_content.replace('<div id="root"></div>', ssr_content, 1)
