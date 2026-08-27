import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import sitemap  # noqa: E402


def reviewed_game(slug: str, title: str, **overrides):
    game = {
        "slug": slug,
        "title": title,
        "updated_at": "2026-08-06T12:34:56Z",
        "image_url": None,
        "identity_status": "verified",
        "content_review_status": "human_reviewed",
    }
    game.update(overrides)
    return game


@pytest.mark.asyncio
async def test_image_entries_are_nested_under_their_game_url(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_recent(limit: int = 100, offset: int = 0):
        return {
            "data": [reviewed_game("catan", "カタン", image_url="/assets/games/catan.webp")],
            "total": 1,
        }

    monkeypatch.setattr(sitemap, "list_recent", fake_list_recent)
    monkeypatch.setenv("NEXT_PUBLIC_BASE_URL", "https://example.test")

    xml_text = await sitemap.get_sitemap_xml()
    root = ET.fromstring(xml_text)

    url_tag = f"{{{sitemap.NS_SITEMAP}}}url"
    image_tag = f"{{{sitemap.NS_IMAGE}}}image"
    loc_tag = f"{{{sitemap.NS_SITEMAP}}}loc"
    image_loc_tag = f"{{{sitemap.NS_IMAGE}}}loc"
    image_title_tag = f"{{{sitemap.NS_IMAGE}}}title"

    assert all(child.tag == url_tag for child in root)
    game_url = next(
        child
        for child in root
        if child.findtext(loc_tag) == "https://example.test/games/catan"
    )
    images = game_url.findall(image_tag)
    assert len(images) == 1
    assert images[0].findtext(image_loc_tag) == "https://example.test/assets/games/catan.webp"
    assert images[0].find(image_title_tag) is None


@pytest.mark.asyncio
async def test_invalid_game_slugs_are_not_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_recent(limit: int = 100, offset: int = 0):
        return {
            "data": [
                reviewed_game("valid-game", "Valid", updated_at=None),
                reviewed_game(None, "Legacy null", updated_at=None),
                reviewed_game("  ", "Legacy blank", updated_at=None),
            ],
            "total": 3,
        }

    monkeypatch.setattr(sitemap, "list_recent", fake_list_recent)
    monkeypatch.setenv("NEXT_PUBLIC_BASE_URL", "https://example.test")

    xml_text = await sitemap.get_sitemap_xml()

    assert "https://example.test/games/valid-game" in xml_text
    assert "/games/None" not in xml_text
    assert "/games/  " not in xml_text


@pytest.mark.asyncio
async def test_retired_mixed_game_record_is_not_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_recent(limit: int = 100, offset: int = 0):
        return {
            "data": [
                reviewed_game("game", "Mixed"),
                reviewed_game("hack-clad", "HacKClaD"),
                reviewed_game("raise-your-goblets", "Raise Your Goblets"),
            ],
            "total": 3,
        }

    monkeypatch.setattr(sitemap, "list_recent", fake_list_recent)
    monkeypatch.setenv("NEXT_PUBLIC_BASE_URL", "https://example.test")

    xml_text = await sitemap.get_sitemap_xml()

    assert "https://example.test/games/game" not in xml_text
    assert "https://example.test/games/hack-clad" in xml_text
    assert "https://example.test/games/raise-your-goblets" in xml_text


@pytest.mark.asyncio
async def test_review_required_game_is_excluded_but_reviewed_game_remains(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_recent(limit: int = 100, offset: int = 0):
        return {
            "data": [
                reviewed_game(
                    "heart-of-crown-2nd-edition",
                    "ハートオブクラウン 第二版",
                    content_review_status="review_required",
                ),
                reviewed_game("uno", "ウノ"),
            ],
            "total": 2,
        }

    monkeypatch.setattr(sitemap, "list_recent", fake_list_recent)
    monkeypatch.setenv("NEXT_PUBLIC_BASE_URL", "https://example.test")

    xml_text = await sitemap.get_sitemap_xml()

    assert "https://example.test/games/heart-of-crown-2nd-edition" not in xml_text
    assert "https://example.test/games/uno" in xml_text
