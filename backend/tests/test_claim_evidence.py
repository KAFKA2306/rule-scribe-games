import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.evidence import (
    Claim,
    ClaimDetailResponse,
    ClaimTarget,
    EvidenceBinding,
    EvidenceBindingDetail,
    EvidenceSource,
    EvidenceTraceResponse,
    SourceLocator,
    build_claim_trace,
)
from app.routers import games


def _claim(claim_id: str = "claim.rule.end", **overrides) -> Claim:
    payload = {
        "claim_id": claim_id,
        "ruleset_id": "ruleset-1",
        "claim_type": "rule_statement",
        "normalized_payload": {"statement": "The game ends at round end."},
        "target": ClaimTarget(target_type="rule_node", rule_id="rule.game-end"),
    }
    payload.update(overrides)
    return Claim(**payload)


def _source(source_id: str = "source.publisher.rules", **overrides) -> EvidenceSource:
    payload = {
        "source_id": source_id,
        "url": "https://publisher.example/rules",
        "source_type": "publisher_rules",
        "trust_metadata": {"official_source": True},
    }
    payload.update(overrides)
    return EvidenceSource(**payload)


def _binding_detail(
    *,
    claim_id: str = "claim.rule.end",
    binding_id: str = "binding.rule.end.publisher",
    source: EvidenceSource | None = None,
    relation: str = "supports",
    locator: SourceLocator | None = None,
) -> EvidenceBindingDetail:
    source = source or _source()
    binding = EvidenceBinding(
        binding_id=binding_id,
        claim_id=claim_id,
        source_id=source.source_id,
        locator_id=locator.locator_id if locator else None,
        relation=relation,
    )
    return EvidenceBindingDetail(binding=binding, source=source, locator=locator)


def test_one_source_can_support_multiple_claims_without_entity_level_verification():
    source = _source()
    first = build_claim_trace(
        _claim("claim.rule.end"),
        [_binding_detail(claim_id="claim.rule.end", binding_id="binding.rule.end", source=source)],
    )
    second_claim = _claim(
        "claim.rule.score",
        normalized_payload={"statement": "Score remaining coins."},
        target=ClaimTarget(target_type="rule_node", rule_id="rule.scoring"),
    )
    second = build_claim_trace(
        second_claim,
        [_binding_detail(claim_id="claim.rule.score", binding_id="binding.rule.score", source=source)],
    )

    assert first.support_status.value == "supported"
    assert second.support_status.value == "supported"
    assert first.bindings[0].source.source_id == second.bindings[0].source.source_id


def test_multiple_sources_can_support_one_claim():
    claim = _claim()
    publisher = _source()
    platform = _source(
        "source.platform.rules",
        url="https://platform.example/game/rules",
        source_type="platform_rules",
        trust_metadata={"official_source": False},
    )
    trace = build_claim_trace(
        claim,
        [
            _binding_detail(binding_id="binding.publisher", source=publisher),
            _binding_detail(binding_id="binding.platform", source=platform),
        ],
    )

    assert trace.support_status.value == "supported"
    assert trace.projection_eligible is True
    assert {item.source.source_id for item in trace.bindings} == {"source.publisher.rules", "source.platform.rules"}


def test_support_and_contradiction_are_preserved_as_contested_not_overwritten():
    claim = _claim()
    trace = build_claim_trace(
        claim,
        [
            _binding_detail(binding_id="binding.support", relation="supports"),
            _binding_detail(
                binding_id="binding.contradiction",
                source=_source("source.errata", url="https://publisher.example/errata", source_type="publisher_errata"),
                relation="contradicts",
            ),
        ],
    )

    assert trace.support_status.value == "contested"
    assert trace.projection_eligible is False
    assert {item.binding.relation.value for item in trace.bindings} == {"supports", "contradicts"}


def test_official_source_does_not_make_unsupported_field_projection_eligible():
    claim = _claim(
        "claim.metadata.age",
        claim_type="metadata",
        normalized_payload={"value": 10},
        target=ClaimTarget(target_type="game_metadata", field_path="min_age"),
    )
    trace = build_claim_trace(
        claim,
        [_binding_detail(claim_id=claim.claim_id, binding_id="binding.age.context", relation="contextualizes")],
    )

    assert trace.bindings[0].source.trust_metadata["official_source"] is True
    assert trace.support_status.value == "unresolved"
    assert trace.projection_eligible is False


def test_source_without_precise_locator_is_valid_and_does_not_invent_one():
    detail = _binding_detail(locator=None)
    assert detail.binding.locator_id is None
    assert detail.locator is None

    with pytest.raises(ValidationError):
        SourceLocator(locator_id="locator.empty", source_id="source.publisher.rules")


def test_printed_text_and_normalized_ability_are_separate_claim_targets():
    printed = _claim(
        "claim.ability.printed",
        claim_type="printed_text",
        normalized_payload={"text": "Gain 1 gold."},
        target=ClaimTarget(target_type="ability_printed_text", ability_id="ability.treasure"),
    )
    normalized = _claim(
        "claim.ability.normalized",
        claim_type="normalized_rule",
        normalized_payload={"effect": {"resource": "gold", "delta": 1}},
        target=ClaimTarget(target_type="ability_normalized", ability_id="ability.treasure"),
    )

    assert printed.target.target_type.value == "ability_printed_text"
    assert normalized.target.target_type.value == "ability_normalized"
    assert printed.claim_id != normalized.claim_id


def test_same_component_can_have_supported_and_unresolved_property_claims():
    cost = _claim(
        "claim.component.cost",
        claim_type="component_property",
        normalized_payload={"value": 2},
        target=ClaimTarget(
            target_type="component_property",
            component_id="card.scout",
            property_key="cost",
            ordinal=0,
        ),
    )
    faction = _claim(
        "claim.component.faction",
        claim_type="component_property",
        normalized_payload={"value": "sun"},
        target=ClaimTarget(
            target_type="component_property",
            component_id="card.scout",
            property_key="faction",
            ordinal=0,
        ),
    )
    supported = build_claim_trace(cost, [_binding_detail(claim_id=cost.claim_id, binding_id="binding.cost")])
    unresolved = build_claim_trace(faction, [])

    assert supported.projection_eligible is True
    assert unresolved.projection_eligible is False
    assert unresolved.support_status.value == "unresolved"


def test_target_contract_rejects_mixed_or_incomplete_target_fields():
    with pytest.raises(ValidationError):
        ClaimTarget(target_type="component_property", component_id="card.scout", property_key="cost")

    with pytest.raises(ValidationError):
        ClaimTarget(target_type="rule_node", rule_id="rule.end", ability_id="ability.invalid")


class FakeEvidenceService:
    async def get_trace(self, slug, ruleset_id, target):
        if slug == "missing":
            return None
        claim = _claim(
            ruleset_id=ruleset_id,
            target=target,
            normalized_payload={"statement": "Verified fixture."},
        )
        trace = build_claim_trace(claim, [_binding_detail(claim_id=claim.claim_id)])
        return EvidenceTraceResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=ruleset_id,
            target=target,
            claims=[trace],
        )

    async def get_claim(self, slug, ruleset_id, claim_id):
        if slug == "missing" or claim_id == "missing":
            return None
        claim = _claim(claim_id, ruleset_id=ruleset_id)
        trace = build_claim_trace(claim, [_binding_detail(claim_id=claim_id, binding_id="binding.claim.detail")])
        return ClaimDetailResponse(game_id="game-1", slug=slug, ruleset_id=ruleset_id, trace=trace)


def _app():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_evidence_service] = lambda: FakeEvidenceService()
    return app


def test_evidence_api_traces_rule_node_and_requires_explicit_ruleset():
    client = TestClient(_app())
    response = client.get(
        "/api/games/example/evidence",
        params={"rule_set_id": "ruleset-1", "target_type": "rule_node", "rule_id": "rule.game-end"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["claims"][0]["support_status"] == "supported"
    assert payload["claims"][0]["projection_eligible"] is True

    missing_ruleset = client.get(
        "/api/games/example/evidence",
        params={"target_type": "rule_node", "rule_id": "rule.game-end"},
    )
    assert missing_ruleset.status_code == 422


def test_evidence_api_rejects_invalid_target_shape():
    client = TestClient(_app())
    response = client.get(
        "/api/games/example/evidence",
        params={"rule_set_id": "ruleset-1", "target_type": "component_property", "component_id": "card.scout", "property_key": "cost"},
    )
    assert response.status_code == 422


def test_claim_detail_api_returns_trace():
    client = TestClient(_app())
    response = client.get("/api/games/example/claims/claim.rule.end", params={"rule_set_id": "ruleset-1"})
    assert response.status_code == 200
    assert response.json()["trace"]["claim"]["claim_id"] == "claim.rule.end"
