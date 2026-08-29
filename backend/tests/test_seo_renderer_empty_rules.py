from pathlib import Path

import pytest

from app.services import seo_renderer


@pytest.mark.asyncio
async def test_ssr_omits_rule_section_when_no_rule_text(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def game(_slug: str):
        return {
            "slug": "unverified-game",
            "title": "未確認ゲーム",
            "summary": "ルール一次資料の確認待ちです。",
            "rules_content": None,
            "identity_status": "unverified",
        }

    async def no_canonical_rules(_slug: str):
        return None

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><title>ボドゲのミカタ</title></head><body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_canonical_rule_text", no_canonical_rules)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("unverified-game")

    assert rendered is not None
    assert "<h2>ルール</h2>" not in rendered
    assert '<pre itemprop="text">' not in rendered


@pytest.mark.asyncio
async def test_ssr_keeps_rule_section_when_rule_text_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def game(_slug: str):
        return {
            "slug": "legacy-game",
            "title": "確認済みゲーム",
            "summary": "確認済みです。",
            "rules_content": "手番ではカードを1枚引く。",
            "identity_status": "verified",
        }

    async def no_canonical_rules(_slug: str):
        return None

    template_dir = tmp_path / "frontend" / "dist"
    template_dir.mkdir(parents=True)
    (template_dir / "index.html").write_text(
        '<html lang="ja"><head><title>ボドゲのミカタ</title></head><body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    monkeypatch.setattr(seo_renderer, "get_by_slug", game)
    monkeypatch.setattr(seo_renderer, "_canonical_rule_text", no_canonical_rules)
    monkeypatch.setenv("LAMBDA_TASK_ROOT", str(tmp_path))

    rendered = await seo_renderer.generate_seo_html("legacy-game")

    assert rendered is not None
    assert "<h2>ルール</h2>" in rendered
    assert "手番ではカードを1枚引く。" in rendered
