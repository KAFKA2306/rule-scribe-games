from types import SimpleNamespace

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
