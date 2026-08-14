from typing import Any

RULE_QUALITY_GOLDEN_VERSION = "golden-v1"
RULE_PROMPT_VERSION = "metadata-source-bound-v1"
_ALLOWED_STATUSES = {"confirmed", "unsupported", "contradicted", "unknown"}


def evaluate_candidate(golden_game: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    claims = candidate.get("claims")
    schema_valid = isinstance(claims, list) and isinstance(candidate.get("edition"), str) and isinstance(
        candidate.get("language"), str
    )
    if not schema_valid:
        return {
            "schema_valid": False,
            "edition_match": False,
            "language_match": False,
            "factual_correctness": 0.0,
            "coverage": 0.0,
            "unsupported_claims": 0,
            "contradictions": 0,
            "provenance_completeness": 0.0,
            "critical_errors": 1,
            "release_pass": False,
        }

    expected_claims = {claim["id"]: claim for claim in golden_game.get("claims", [])}
    allowed_sources = {source["id"] for source in golden_game.get("sources", [])}
    candidate_claims = {claim.get("id"): claim for claim in claims if isinstance(claim, dict) and claim.get("id")}

    confirmed = 0
    unsupported = 0
    contradicted = 0
    known = 0
    sourced_confirmed = 0
    critical_errors = 0

    for claim_id, expected in expected_claims.items():
        actual = candidate_claims.get(claim_id, {"status": "unknown", "source_ids": []})
        status = actual.get("status", "unknown")
        if status not in _ALLOWED_STATUSES:
            status = "unsupported"
        if status != "unknown":
            known += 1
        if status == "confirmed":
            confirmed += 1
            source_ids = actual.get("source_ids") or []
            expected_sources = set(expected.get("source_ids") or [])
            if set(source_ids) & expected_sources & allowed_sources:
                sourced_confirmed += 1
            elif expected.get("critical", False):
                critical_errors += 1
        elif status == "unsupported":
            unsupported += 1
            if expected.get("critical", False):
                critical_errors += 1
        elif status == "contradicted":
            contradicted += 1
            if expected.get("critical", False):
                critical_errors += 1

    for claim_id, actual in candidate_claims.items():
        if claim_id not in expected_claims and actual.get("status") in {"confirmed", "unsupported", "contradicted"}:
            unsupported += 1

    total = max(len(expected_claims), 1)
    assessed = confirmed + unsupported + contradicted
    factual_correctness = confirmed / assessed if assessed else 0.0
    provenance = sourced_confirmed / confirmed if confirmed else 0.0
    edition_match = candidate.get("edition") == golden_game.get("edition")
    language_match = candidate.get("language") == golden_game.get("language")
    release_pass = (
        critical_errors == 0
        and unsupported == 0
        and contradicted == 0
        and edition_match
        and language_match
        and provenance == 1.0
        and schema_valid
    )
    return {
        "schema_valid": schema_valid,
        "edition_match": edition_match,
        "language_match": language_match,
        "factual_correctness": round(factual_correctness, 6),
        "coverage": round(known / total, 6),
        "unsupported_claims": unsupported,
        "contradictions": contradicted,
        "provenance_completeness": round(provenance, 6),
        "critical_errors": critical_errors,
        "release_pass": release_pass,
    }


def compare_passes(golden_game: dict[str, Any], first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_metrics = evaluate_candidate(golden_game, first)
    second_metrics = evaluate_candidate(golden_game, second)
    no_regression = (
        second_metrics["factual_correctness"] >= first_metrics["factual_correctness"]
        and second_metrics["coverage"] >= first_metrics["coverage"]
        and second_metrics["unsupported_claims"] <= first_metrics["unsupported_claims"]
        and second_metrics["contradictions"] <= first_metrics["contradictions"]
        and second_metrics["provenance_completeness"] >= first_metrics["provenance_completeness"]
        and second_metrics["critical_errors"] <= first_metrics["critical_errors"]
    )
    if second_metrics["release_pass"] and no_regression:
        selected = "second"
        selected_metrics = second_metrics
    else:
        selected = "first"
        selected_metrics = first_metrics
    return {
        "first": first_metrics,
        "second": second_metrics,
        "no_regression": no_regression,
        "selected_pass": selected,
        "release_pass": selected_metrics["release_pass"],
    }
