from datetime import UTC, datetime

import pytest

from app.models.component_catalog import ComponentKind
from app.models.rule_graph import RuleGraphReadResponse, RuleNode, RuleNodeType
from app.models.vrchat_manifest import CapabilityName
from app.models.vrchat_readiness import (
    ReadinessAuditRecord,
    ReadinessStatus,
    RequirementState,
    RuleCoverageDimension,
    RuleCoverageState,
)
from app.services.vrchat_readiness_audit import VrchatReadinessAuditService
from app.services.vrchat_readiness_policy import StrictVrchatReadinessAuditService

AUDITED_AT = datetime(2026, 8, 14, tzinfo=UTC)


def _node(
    rule_id: str,
    node_type: RuleNodeType,
    *,
    evidence_ref: str | None = None,
    source_url: str | None = None,
    metadata: dict | None = None,
) -> RuleNode:
    return RuleNode(
        rule_id=rule_id,
        node_type=node_type,
        normalized_statement=rule_id,
        verification_status="verified",
        evidence_ref=evidence_ref,
        source_url=source_url,
        metadata=metadata or {},
    )


def _graph(nodes: list[RuleNode]) -> RuleGraphReadResponse:
    return RuleGraphReadResponse(
        status="available",
        game_id="game-1",
        slug="game-one",
        rule_set_id="ruleset-1",
        nodes=nodes,
    )


def test_source_url_alone_does_not_satisfy_field_level_evidence():
    graph = _graph(
        [
            _node(
                "setup.only-url",
                RuleNodeType.SETUP,
                source_url="https://example.invalid/rules",
            )
        ]
    )

    coverage, _, blockers = StrictVrchatReadinessAuditService._rule_coverage(graph)
    setup = next(item for item in coverage if item.dimension == RuleCoverageDimension.SETUP)

    assert setup.state == RuleCoverageState.UNVERIFIED
    assert "RULE_EVIDENCE_INSUFFICIENT:setup" in blockers


def test_component_kind_is_not_promoted_to_runtime_capability():
    assessments, blockers = StrictVrchatReadinessAuditService._capability_assessments(
        _graph([]),
        component_sets=[],
        component_kinds={ComponentKind.CARD},
    )
    by_capability = {item.capability: item for item in assessments}

    assert blockers == []
    assert by_capability[CapabilityName.DECK].requirement == RequirementState.UNKNOWN


def test_only_explicit_verified_metadata_requires_capability():
    graph = _graph(
        [
            _node(
                "action.draw",
                RuleNodeType.ACTION,
                evidence_ref="evidence.action.draw",
                metadata={"vrchat_capabilities": {"deck": "required"}},
            )
        ]
    )

    assessments, blockers = StrictVrchatReadinessAuditService._capability_assessments(
        graph,
        component_sets=[],
        component_kinds=set(),
    )
    by_capability = {item.capability: item for item in assessments}

    assert blockers == []
    assert by_capability[CapabilityName.DECK].requirement == RequirementState.REQUIRED
    assert by_capability[CapabilityName.DECK].evidence_refs == ["action.draw"]


@pytest.mark.asyncio
async def test_unverified_source_asset_reuse_prevents_ready_promotion(monkeypatch):
    async def fake_base_audit_ruleset(self, *args, **kwargs):
        return ReadinessAuditRecord(
            gameId="game-1",
            slug="game-one",
            title="Game One",
            rulesetId="ruleset-1",
            readinessStatus=ReadinessStatus.READY,
            playerCountStatus="known",
            recommendedModuleClass="generic-state-machine",
            manifestProjectable=True,
            moduleId="vrmine.game-one",
            moduleVersionRange=">=1.0.0,<2.0.0",
            promotableToCatalog=True,
            auditedAt=AUDITED_AT,
        )

    monkeypatch.setattr(VrchatReadinessAuditService, "_audit_ruleset", fake_base_audit_ruleset)
    service = StrictVrchatReadinessAuditService()

    record = await service._audit_ruleset(object(), object())

    assert record.rights_blockers == ["SOURCE_ASSET_REUSE_UNVERIFIED"]
    assert record.readiness_status == ReadinessStatus.REVIEW_REQUIRED
    assert record.promotable_to_catalog is False
