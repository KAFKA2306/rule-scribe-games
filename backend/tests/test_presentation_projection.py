import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.presentation_projection import (
    GlossaryProjectionSection,
    PresentationProjectionResponse,
    ProjectedGlossaryEntry,
    ProjectedRule,
    ProjectionEvidence,
    ProjectionSectionKind,
    ProjectionSectionStatus,
    RuleProjectionSection,
)
from app.routers import presentation
from app.services.presentation_projection import (
    PresentationProjectionService,
    accepted_supported_claim,
    project_rule_rows,
    projection_to_json_ld,
)


def test_claim_requires_accepted_supported_uncontradicted_evidence():
    base = {
        "claim_id": "claim.rule.end",
        "rule_id": "rule.end",
        "normalized_payload": {"statement": "End at round end."},
    }
    supports = [{"source_id": "source.publisher", "relation": "supports"}]

    assert accepted_supported_claim({**base, "lifecycle_status": "candidate"}, supports) is None
    assert accepted_supported_claim({**base, "lifecycle_status": "unknown"}, supports) is None
    assert accepted_supported_claim({**base, "lifecycle_status": "rejected"}, supports) is None

    contested = [*supports, {"source_id": "source.errata", "relation": "contradicts"}]
    assert accepted_supported_claim({**base, "lifecycle_status": "accepted"}, contested) is None

    eligible = accepted_supported_claim({**base, "lifecycle_status": "accepted"}, supports)
    assert eligible is not None
    assert eligible["source_ids"] == ["source.publisher"]


def test_rule_projection_rejects_stale_claim_and_variant():
    eligible_claims = {
        "rule.current": [
            {
                "claim_id": "claim.current",
                "normalized_payload": {"statement": "Current canonical statement."},
                "source_ids": ["source.publisher"],
            }
        ],
        "rule.stale": [
            {
                "claim_id": "claim.stale",
                "normalized_payload": {"statement": "Old statement."},
                "source_ids": ["source.publisher"],
            }
        ],
        "rule.variant": [
            {
                "claim_id": "claim.variant",
                "normalized_payload": {"statement": "Optional variant."},
                "source_ids": ["source.publisher"],
            }
        ],
    }
    rules = [
        {
            "rule_id": "rule.current",
            "node_type": "game_end",
            "normalized_statement": "Current canonical statement.",
            "sequence": 1,
        },
        {
            "rule_id": "rule.stale",
            "node_type": "scoring",
            "normalized_statement": "New statement.",
            "sequence": 2,
        },
        {
            "rule_id": "rule.variant",
            "node_type": "variant",
            "normalized_statement": "Optional variant.",
            "sequence": 3,
        },
    ]

    projected = project_rule_rows(rules, eligible_claims)
    assert [item.rule_id for item in projected] == ["rule.current"]
    assert projected[0].evidence.claim_id == "claim.current"
    assert projected[0].evidence.claim_lifecycle == "accepted"
    assert projected[0].evidence.support_status == "supported"


def test_rule_projection_selects_current_claim_when_earlier_accepted_claim_is_stale():
    rules = [
        {
            "rule_id": "rule.end",
            "node_type": "game_end",
            "normalized_statement": "Current end condition.",
            "sequence": 1,
        }
    ]
    eligible_claims = {
        "rule.end": [
            {
                "claim_id": "claim.001.stale",
                "normalized_payload": {"statement": "Old end condition."},
                "source_ids": ["source.old"],
            },
            {
                "claim_id": "claim.002.current",
                "normalized_payload": {"statement": "Current end condition."},
                "source_ids": ["source.current"],
            },
        ]
    }

    projected = project_rule_rows(rules, eligible_claims)
    assert len(projected) == 1
    assert projected[0].evidence.claim_id == "claim.002.current"
    assert projected[0].evidence.source_ids == ["source.current"]


def test_projection_evidence_requires_at_least_one_supporting_source():
    with pytest.raises(ValidationError):
        ProjectionEvidence(claim_id="claim.empty", source_ids=[])


def test_available_and_not_available_section_contracts_are_strict():
    with pytest.raises(ValidationError):
        RuleProjectionSection(
            kind=ProjectionSectionKind.QUICK_RULES,
            status=ProjectionSectionStatus.AVAILABLE,
            items=[],
        )

    with pytest.raises(ValidationError):
        RuleProjectionSection(
            kind=ProjectionSectionKind.QUICK_RULES,
            status=ProjectionSectionStatus.NOT_AVAILABLE,
            items=[
                {
                    "rule_id": "rule.end",
                    "node_type": "game_end",
                    "text": "End.",
                    "evidence": {"claim_id": "claim.end", "source_ids": ["source.publisher"]},
                }
            ],
        )


def _empty_projection(slug="example", rule_set_id="ruleset-1"):
    empty = PresentationProjectionService._empty_rule_section
    return PresentationProjectionResponse(
        status="not_available",
        game_id="game-1",
        slug=slug,
        rule_set_id=rule_set_id,
        language_code="ja",
        synopsis=empty(ProjectionSectionKind.SYNOPSIS),
        quick_rules=empty(ProjectionSectionKind.QUICK_RULES),
        setup=empty(ProjectionSectionKind.SETUP),
        game_flow=empty(ProjectionSectionKind.GAME_FLOW),
        end_condition=empty(ProjectionSectionKind.END_CONDITION),
        scoring=empty(ProjectionSectionKind.SCORING),
        glossary=GlossaryProjectionSection(status=ProjectionSectionStatus.NOT_AVAILABLE),
        common_errors=empty(ProjectionSectionKind.COMMON_ERRORS),
        pro_tips=empty(ProjectionSectionKind.PRO_TIPS),
    )


def _available_projection():
    empty = PresentationProjectionService._empty_rule_section
    rule = ProjectedRule(
        rule_id="rule.end",
        node_type="game_end",
        text="The game ends at round end.",
        evidence=ProjectionEvidence(claim_id="claim.end", source_ids=["source.publisher"]),
    )
    quick = RuleProjectionSection(
        kind=ProjectionSectionKind.QUICK_RULES,
        status=ProjectionSectionStatus.AVAILABLE,
        items=[rule],
    )
    glossary = GlossaryProjectionSection(
        status=ProjectionSectionStatus.AVAILABLE,
        items=[
            ProjectedGlossaryEntry(
                concept_id="concept.round",
                label="ラウンド",
                definition="ゲーム進行の一区切り。",
                rule_ids=["rule.end"],
            )
        ],
    )
    return PresentationProjectionResponse(
        status="available",
        game_id="game-1",
        slug="example",
        rule_set_id="ruleset-ja-v1",
        language_code="ja",
        synopsis=empty(ProjectionSectionKind.SYNOPSIS),
        quick_rules=quick,
        setup=empty(ProjectionSectionKind.SETUP),
        game_flow=empty(ProjectionSectionKind.GAME_FLOW),
        end_condition=RuleProjectionSection(
            kind=ProjectionSectionKind.END_CONDITION,
            status=ProjectionSectionStatus.AVAILABLE,
            items=[rule],
        ),
        scoring=empty(ProjectionSectionKind.SCORING),
        glossary=glossary,
        common_errors=empty(ProjectionSectionKind.COMMON_ERRORS),
        pro_tips=empty(ProjectionSectionKind.PRO_TIPS),
    )


def test_json_ld_adapter_uses_only_canonical_projected_rules_and_concepts():
    data = projection_to_json_ld(_available_projection(), "Example Game")

    assert data["@type"] == "Game"
    assert data["name"] == "Example Game"
    assert {entry["propertyID"]: entry["value"] for entry in data["identifier"]} == {
        "slug": "example",
        "ruleSet": "ruleset-ja-v1",
    }
    assert data["subjectOf"] == [
        {
            "@type": "CreativeWork",
            "identifier": "rule.end",
            "text": "The game ends at round end.",
        }
    ]
    assert data["about"] == [
        {
            "@type": "DefinedTerm",
            "termCode": "concept.round",
            "name": "ラウンド",
            "description": "ゲーム進行の一区切り。",
        }
    ]
    assert "pro_tips" not in data
    assert "common_errors" not in data


class FakePresentationService:
    async def get_by_slug(self, slug, rule_set_id, language_code="ja"):
        if slug == "missing":
            return None
        return _empty_projection(slug, rule_set_id)


def _app():
    app = FastAPI()
    app.include_router(presentation.router, prefix="/api")
    app.dependency_overrides[presentation.get_presentation_projection_service] = lambda: FakePresentationService()
    return app


def test_projection_api_requires_explicit_ruleset_and_returns_fail_closed_payload():
    client = TestClient(_app())
    response = client.get(
        "/api/games/example/presentation",
        params={"rule_set_id": "ruleset-1", "language_code": "ja"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "not_available"
    assert payload["rule_set_id"] == "ruleset-1"
    assert payload["common_errors"]["status"] == "not_available"
    assert payload["pro_tips"]["status"] == "not_available"

    missing_ruleset = client.get("/api/games/example/presentation")
    assert missing_ruleset.status_code == 422


def test_projection_api_keeps_missing_game_distinct_from_missing_projection():
    client = TestClient(_app())
    response = client.get("/api/games/missing/presentation", params={"rule_set_id": "ruleset-1"})
    assert response.status_code == 404
