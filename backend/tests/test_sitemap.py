import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import sitemap  # noqa: E402


@pytest.mark.asyncio
async def test_image_entries_are_nested_under_their_game_url(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_for_sitemap() -> list[dict[str, str]]:
        return [
            {
                "slug": "catan",
                "title": "カタン",
                "updated_at": "2026-08-06T12:34:56Z",
                "image_url": "/assets/games/catan.webp",
            }
        ]

    monkeypatch.setattr(sitemap, "list_for_sitemap", fake_list_for_sitemap)
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
