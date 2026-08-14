import json
from pathlib import Path

from app.services.rule_quality import compare_passes, evaluate_candidate

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "evaluation" / "rules" / "golden-v1.json").read_text(encoding="utf-8"))


def _game(slug: str) -> dict:
    return next(game for game in GOLDEN["games"] if game["slug"] == slug)


def _correct_candidate(game: dict) -> dict:
    return {
        "edition": game["edition"],
        "language": game["language"],
        "claims": [
            {
                "id": claim["id"],
                "status": "confirmed",
                "source_ids": [claim["source_ids"][0]],
            }
            for claim in game["claims"]
        ],
    }


def test_known_correct_fixture_passes():
    game = _game("yro")
    metrics = evaluate_candidate(game, _correct_candidate(game))
    assert metrics["release_pass"] is True
    assert metrics["factual_correctness"] == 1.0
    assert metrics["provenance_completeness"] == 1.0


def test_unsupported_claim_fails():
    game = _game("yro")
    candidate = _correct_candidate(game)
    candidate["claims"].append({"id": "invented-extra-rule", "status": "confirmed", "source_ids": []})
    metrics = evaluate_candidate(game, candidate)
    assert metrics["unsupported_claims"] == 1
    assert metrics["release_pass"] is False


def test_critical_contradiction_fails():
    game = _game("flip-7-with-a-vengeance")
    candidate = _correct_candidate(game)
    candidate["claims"][0]["status"] = "contradicted"
    metrics = evaluate_candidate(game, candidate)
    assert metrics["contradictions"] == 1
    assert metrics["critical_errors"] == 1
    assert metrics["release_pass"] is False


def test_edition_and_language_mismatch_fail():
    game = _game("yro")
    candidate = _correct_candidate(game)
    candidate["edition"] = "unknown edition"
    candidate["language"] = "ja"
    metrics = evaluate_candidate(game, candidate)
    assert metrics["edition_match"] is False
    assert metrics["language_match"] is False
    assert metrics["release_pass"] is False


def test_missing_provenance_fails():
    game = _game("flip-7-with-a-vengeance")
    candidate = _correct_candidate(game)
    candidate["claims"][0]["source_ids"] = []
    metrics = evaluate_candidate(game, candidate)
    assert metrics["provenance_completeness"] < 1.0
    assert metrics["release_pass"] is False


def test_malformed_candidate_fails_closed():
    game = _game("yro")
    metrics = evaluate_candidate(game, {"edition": game["edition"]})
    assert metrics["schema_valid"] is False
    assert metrics["release_pass"] is False


def test_second_pass_regression_keeps_first_pass():
    game = _game("yro")
    first = _correct_candidate(game)
    second = _correct_candidate(game)
    second["claims"].append({"id": "invented-extra-rule", "status": "confirmed", "source_ids": []})
    comparison = compare_passes(game, first, second)
    assert comparison["no_regression"] is False
    assert comparison["selected_pass"] == "first"
    assert comparison["release_pass"] is True


def test_second_pass_improvement_is_selected():
    game = _game("flip-7-with-a-vengeance")
    first = _correct_candidate(game)
    first["claims"][0]["status"] = "contradicted"
    second = _correct_candidate(game)
    comparison = compare_passes(game, first, second)
    assert comparison["no_regression"] is True
    assert comparison["selected_pass"] == "second"
    assert comparison["release_pass"] is True
