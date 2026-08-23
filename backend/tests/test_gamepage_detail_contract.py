from pathlib import Path

from app.models import GamePageDetail


def test_gamepage_detail_schema_covers_fields_consumed_by_frontend():
    source = Path("frontend/src/pages/GamePage.jsx").read_text(encoding="utf-8")
    required_fields = {
        "rules_content",
        "setup_summary",
        "gameplay_summary",
        "end_game_summary",
        "structured_data",
    }

    model_fields = set(GamePageDetail.model_fields)
    assert required_fields <= model_fields
    for field in required_fields - {"structured_data"}:
        assert f"game.{field}" in source
