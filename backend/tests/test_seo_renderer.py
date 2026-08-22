from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import seo_renderer


def _section(*texts: str):
    return SimpleNamespace(
        status="available" if texts else "not_available",
        items=[SimpleNamespace(rule_id=f"rule-{index}", text=text) for index, text in enumerate(texts, 1)],
    )


def _projection(*, quick=(), setup=(), flow=(), end=(), scoring=()):
    return SimpleNamespace(
        status="available",
        quick_rules=_section(*quick),
        setup=_section(*setup),
        game_flow=_section(*flow),
        end_condition=_section(*end),
        scoring=_section(*scoring),
    )


def test_page_title_has_no_generated_strategy_variant() -> None:
    assert seo_renderer._page_title("スカルキング") == "「スカルキング」のルール・出典 | ボドゲのミカタ"


def test_open_ended_player_count_does_not_invent_maximum() -> None:
    structured, label = seo_renderer._player_count_projection({"min_players": 3, "max_players": None})

    assert structured == {"@type": "QuantitativeValue", "minValue": 3}
    assert label == "3人以上"


@pytest.mark.asyncio
async def test_missing_game_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    async def missing(_slug: str):
        return None

    monkeypatch.setattr(seo_renderer, "get_by_slug", missing)

    assert await seo_renderer.generate_seo_html("missing") is None


@pytest.mark.asyncio
async def test_game_ssr_uses_canonical_projection_and_escapes_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def game(_slug: str):
        return {
            "id": "game-1",
            "slug": "safe-game",
            "title": 'Bad </title><script>alert("title")</script>',
            "summary": 'Summary <img src=x onerror=alert("summary")>',
            "rules_content": 'LEGACY RULE MUST NOT RENDER',
            "min_players": 2,
            "max_players": 4,
            "play_time": 30,
            "image_url": "/images/game.webp",
        }

    async def canonical_projection(_slug: str):
        return _projection(flow=('Canonical </pre><script>alert("rules")</script>',))

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        """<!doctype html>
<html lang="ja">
<head>
<title>ボドゲのミカタ</title>
<meta name="description" content="home" />
<meta property="og:title" content="home" />
<meta property="og:description" content="home" />
<meta property="og:url" content="https://bodoge-no-mikata.vercel.app/" />
<meta property="og:image" content="https://bodoge-no-mikata.vercel.app/og-image.webp" />
<meta name="twitter:title" content="home" />
<meta name="twitter:description" content="home" />
<meta name="twitter:image" content="https://bodoge-no-mikata.vercel.app/og-image.webp" />
<link rel="canonical" href="https://bodoge-no-mikata.vercel.app/" />
</head>
<body><div id="root"></div></body>
</html>""",
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_load_canonical_projection", canonical_projection)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("safe-game")

    assert rendered is not None
    assert 'href="https://bodoge-no-mikata.vercel.app/games/safe-game"' in rendered
    assert 'property="og:url" content="https://bodoge-no-mikata.vercel.app/games/safe-game"' in rendered
    assert 'data-game-seo="true"' in rendered
    assert 'data-breadcrumb-seo="true"' in rendered
    assert '"@type":"BreadcrumbList"' in rendered
    assert '"name":"ゲーム一覧","item":"https://bodoge-no-mikata.vercel.app/"' in rendered
    assert '"item":"https://bodoge-no-mikata.vercel.app/games/safe-game"' in rendered
    assert 'data-ssr-game="true"' in rendered
    assert '<nav aria-label="パンくずリスト">' in rendered
    assert '<a href="/">ゲーム一覧</a>' in rendered
    assert 'aria-current="page"' in rendered
    assert 'LEGACY RULE MUST NOT RENDER' not in rendered
    assert '<script>alert("title")</script>' not in rendered
    assert '<script>alert("rules")</script>' not in rendered
    assert '<img src=x onerror=alert("summary")>' not in rendered
    assert '&lt;script&gt;alert(&quot;rules&quot;)&lt;/script&gt;' in rendered
    assert "\\u003cscript" in rendered


@pytest.mark.asyncio
async def test_game_ssr_fails_closed_when_projection_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def game(_slug: str):
        return {
            "id": "game-1",
            "slug": "no-rules",
            "title": "No rules",
            "rules_content": "OLD ROW RULE",
        }

    async def no_projection(_slug: str):
        return None

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><title>x</title></head><body><div id="root"></div></body></html>',
        encoding="utf-8",
    )
    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_load_canonical_projection", no_projection)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("no-rules")

    assert rendered is not None
    assert "OLD ROW RULE" not in rendered
    assert "正準RuleSet projectionは未整備です。" in rendered


@pytest.mark.parametrize("slug", ["game", "hack-clad"])
@pytest.mark.asyncio
async def test_known_mixed_game_records_are_noindex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    slug: str,
) -> None:
    async def game(_slug: str):
        return {
            "slug": slug,
            "title": "Mixed record",
            "identity_status": "unverified",
            "summary": "mixed identity fixture",
        }

    async def no_projection(_slug: str):
        return None

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><meta name="robots" content="index, follow" /></head>'
        '<body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_load_canonical_projection", no_projection)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html(slug)

    assert rendered is not None
    assert '<meta name="robots" content="noindex, follow" />' in rendered
    assert 'content="index, follow"' not in rendered
