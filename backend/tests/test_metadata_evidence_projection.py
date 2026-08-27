from app.services.metadata_evidence_projection import _payload_matches_current_value


def test_scalar_metadata_requires_exact_current_value() -> None:
    game = {"min_players": 2, "play_time": 30}

    assert _payload_matches_current_value(game, "min_players", {"value": 2}) is True
    assert _payload_matches_current_value(game, "min_players", {"value": 3}) is False
    assert _payload_matches_current_value(game, "play_time", {"value": 30}) is True
    assert _payload_matches_current_value(game, "play_time", {}) is False


def test_mechanics_evidence_requires_exact_array_match() -> None:
    game = {"structured_data": {"mechanics": ["Deck Building", "Hand Management"]}}

    assert (
        _payload_matches_current_value(
            game,
            "structured_data.mechanics",
            {"value": ["Deck Building", "Hand Management"]},
        )
        is True
    )
    assert (
        _payload_matches_current_value(
            game,
            "structured_data.mechanics",
            {"value": ["Deck Building"]},
        )
        is False
    )
    assert (
        _payload_matches_current_value(
            game,
            "structured_data.mechanics",
            {"value": ["Hand Management", "Deck Building"]},
        )
        is False
    )


def test_mechanics_evidence_fails_closed_on_missing_or_wrong_types() -> None:
    assert (
        _payload_matches_current_value(
            {"structured_data": {}},
            "structured_data.mechanics",
            {"value": []},
        )
        is False
    )
    assert (
        _payload_matches_current_value(
            {"structured_data": {"mechanics": ["Drafting"]}},
            "structured_data.mechanics",
            {"value": "Drafting"},
        )
        is False
    )
    assert (
        _payload_matches_current_value(
            {"structured_data": "not-an-object"},
            "structured_data.mechanics",
            {"value": ["Drafting"]},
        )
        is False
    )
