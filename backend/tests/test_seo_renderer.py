from pathlib import Path

import pytest

from app.services import seo_renderer


def test_page_title_omits_strategy_when_unavailable() -> None:
    game = {"structured_data": {"strategy_analysis": None}}

    assert seo_renderer._page_title(game, "スカルキング") == "「スカルキング」のルール・インスト要約 | ボドゲのミカタ"


def test_page_title_includes_strategy_when_available() -> None:
    game = {"structured_data": {"strategy_analysis": "終盤では得点状況を見てビッドを調整する。"}}

    assert seo_renderer._page_title(game, "Example") == "「Example」のルール・戦略・インスト要約 | ボドゲのミカタ"


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
async def test_game_ssr_replaces_metadata_and_escapes_db_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def game(_slug: str):
        return {
            "id": "game-1",
            "slug": "safe-game",
            "title": 'Bad </title><script>alert("title")</script>',
            "summary": 'Summary <img src=x onerror=alert("summary")>',
            "rules_content": '</pre><script>alert("rules")</script>',
            "min_players": 2,
            "max_players": 4,
            "play_time": 30,
            "image_url": "/images/game.webp",
        }

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
    assert '<script>alert("title")</script>' not in rendered
    assert '<script>alert("rules")</script>' not in rendered
    assert '<img src=x onerror=alert("summary")>' not in rendered
    assert '&lt;script&gt;alert(&quot;rules&quot;)&lt;/script&gt;' in rendered
    assert "\\u003cscript" in rendered


@pytest.mark.asyncio
async def test_known_mixed_game_record_is_noindex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def game(_slug: str):
        return {
            "slug": "game",
            "title": "Mixed record",
            "identity_status": "unverified",
            "summary": "mixed identity fixture",
        }

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><meta name="robots" content="index, follow" /></head>'
        '<body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("game")

    assert rendered is not None
    assert '<meta name="robots" content="noindex, follow" />' in rendered
    assert 'content="index, follow"' not in rendered
