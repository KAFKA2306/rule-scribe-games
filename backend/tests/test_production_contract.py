import pytest

from app.scripts.verify_production_contract import validate_mechanical_dna_payload


def test_validate_mechanical_dna_payload_accepts_canonical_contract():
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "game_id": "game-id",
        "slug": "skull-king",
        "connections": [],
    }

    assert validate_mechanical_dna_payload(payload) == 0


def test_validate_mechanical_dna_payload_allows_future_connections():
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
        "connections": [{"slug": "another-game"}],
    }

    assert validate_mechanical_dna_payload(payload) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("algorithm_version", "legacy-label-match"),
        ("status", "not_available"),
        ("slug", "other-game"),
        ("connections", None),
    ],
)
def test_validate_mechanical_dna_payload_fails_closed(field, value):
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
        "connections": [],
    }
    payload[field] = value

    with pytest.raises(ValueError):
        validate_mechanical_dna_payload(payload)
