import json
from pathlib import Path

from app.services.search_visibility import EXCLUDED_GAME_SLUGS


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data" / "identity-conflicts" / "game.json"


def test_game_identity_conflict_report_is_source_backed_and_quarantined() -> None:
    data = json.loads(REPORT.read_text(encoding="utf-8"))

    assert data["slug"] == "game"
    assert data["slug"] in EXCLUDED_GAME_SLUGS
    assert data["decision"]["status"] == "identity_conflict"
    assert data["decision"]["normal_mutation_allowed"] is False
    assert data["decision"]["indexable"] is False
    assert data["decision"]["destructive_auto_merge_allowed"] is False

    works = data["canonical_works"]
    assert [work["title_ja"] for work in works] == [
        "ワインと毒とゴブレット",
        "みんなでぽんこつペイント",
    ]
    assert len({work["source_url"] for work in works}) == 2
    assert all(work["source_url"].startswith("https://hobbyjapan.games/") for work in works)

    assigned_fields = {
        field
        for work in works
        for field in work["field_assignment"]
    }
    assert {"title", "description", "rules_content"} <= assigned_fields
    assert {"title_ja", "title_en", "summary", "structured_data.keywords"} <= assigned_fields

    assert set(data["unresolved_fields"]) == {
        "min_players",
        "max_players",
        "play_time",
        "published_year",
        "source_url",
    }
