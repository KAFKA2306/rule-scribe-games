from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import GameDetail, GameUpdate


VALID_BGA_URL = "https://en.boardgamearena.com/gamepanel?game=azul"


def test_bga_url_is_supported_across_read_and_update_models():
    detail = GameDetail(id="game-1", title="Azul", bga_url=VALID_BGA_URL)
    update = GameUpdate(bga_url=VALID_BGA_URL)

    assert detail.bga_url == VALID_BGA_URL
    assert update.bga_url == VALID_BGA_URL


@pytest.mark.parametrize(
    "url",
    [
        "http://en.boardgamearena.com/gamepanel?game=azul",
        "https://boardgamearena.example/gamepanel?game=azul",
        "https://evil.example/?next=https://boardgamearena.com",
    ],
)
def test_bga_url_rejects_non_https_or_non_bga_hosts(url):
    with pytest.raises(ValidationError):
        GameUpdate(bga_url=url)


def test_blank_bga_url_normalizes_to_none():
    assert GameUpdate(bga_url="  ").bga_url is None


def test_local_database_schema_and_upsert_include_bga_url():
    source = Path("backend/app/core/local_db.py").read_text(encoding="utf-8")

    assert "bga_url TEXT" in source
    assert "ALTER TABLE games ADD COLUMN bga_url TEXT" in source
    assert "bga_url=excluded.bga_url" in source
