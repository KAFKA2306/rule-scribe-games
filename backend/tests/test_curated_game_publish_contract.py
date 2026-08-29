from pathlib import Path

from app.scripts.curated_game_fast_path_v2 import LEGACY_RULE_FIELDS, catalog_write_payload
from app.scripts.curated_game_workflow import load_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
SKULL_KING = REPO_ROOT / "data" / "curated-games" / "skull-king.json"


def test_curated_release_does_not_publish_legacy_rule_fields():
    spec = load_spec(SKULL_KING)

    payload = catalog_write_payload(spec, "work-1")

    assert payload["work_id"] == "work-1"
    assert payload["slug"] == "skull-king"
    assert payload["source_url"] == spec.source.url
    for field in LEGACY_RULE_FIELDS:
        assert payload[field] is None
