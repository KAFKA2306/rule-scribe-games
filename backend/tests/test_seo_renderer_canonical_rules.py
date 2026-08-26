from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import seo_renderer
from app.services.seo_renderer import _render_projection_rules


def _section(*texts: str):
    return SimpleNamespace(items=[SimpleNamespace(text=text) for text in texts])


def test_render_projection_rules_keeps_player_facing_sections():
    projection = SimpleNamespace(
        setup=_section("setup rule"),
        game_flow=_section("flow rule one", "flow rule two"),
        end_condition=_section("end rule"),
        scoring=_section(),
    )

    rendered = _render_projection_rules(projection)

    assert rendered is not None
    assert "## セットアップ" in rendered
    assert "- setup rule" in rendered
    assert "## ゲーム進行" in rendered
    assert "- flow rule one" in rendered
    assert "- flow rule two" in rendered
    assert "## 終了条件・勝利" in rendered
    assert "- end rule" in rendered
    assert "## 得点" not in rendered


@pytest.mark.asyncio
async def test_source_bound_ssr_uses_same_neutral_summary_as_public_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    async def game(_slug: str):
        return {
            "slug": "ito",
            "title": "ito",
            "title_ja": "イト",
            "summary": "unreviewed legacy summary",
            "description": "unreviewed legacy description",
            "content_review_status": "review_required",
        }

    async def canonical(_slug: str):
        return "## ゲーム進行\n- 出典付きルール"

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><meta name="description" content="home" /></head>'
        '<body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_canonical_rule_text", canonical)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("ito")

    neutral = "「イト」の出典付きルール要約と出典情報を確認できます。"
    assert rendered is not None
    assert neutral in rendered
    assert 'name="description" content="「イト」の出典付きルール要約と出典情報を確認できます。"' in rendered
    assert 'itemprop="description">「イト」の出典付きルール要約と出典情報を確認できます。</p>' in rendered
    assert "unreviewed legacy summary" not in rendered
    assert "unreviewed legacy description" not in rendered
