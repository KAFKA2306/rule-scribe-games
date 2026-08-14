from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.models.component_catalog import ComponentKind
from app.models.rule_graph import RuleGraphReadResponse, RuleVerificationStatus
from app.models.vrchat_manifest import CapabilityName
from app.models.vrchat_readiness import (
    CapabilityAssessment,
    ReadinessAuditRecord,
    ReadinessStatus,
    RequirementState,
    RuleCoverageAssessment,
    RuleCoverageDimension,
    RuleCoverageState,
)
from app.services.vrchat_readiness_audit import VrchatReadinessAuditService, _COVERAGE_TYPES

_RIGHTS_BLOCKER = "SOURCE_ASSET_REUSE_UNVERIFIED"


class StrictVrchatReadinessAuditService(VrchatReadinessAuditService):
    """Fail-closed production policy for the VRChat readiness audit.

    The base service owns catalog traversal and module binding checks. This policy
    owns evidence, capability and rights semantics so production execution cannot
    silently promote weak source linkage or inferred runtime requirements.
    """

    @staticmethod
    def _rule_coverage(
        rule_graph: RuleGraphReadResponse,
    ) -> tuple[list[RuleCoverageAssessment], list[str], list[str]]:
        data_blockers: list[str] = []
        evidence_blockers: list[str] = []
        assessments: list[RuleCoverageAssessment] = []

        for dimension, node_types in _COVERAGE_TYPES.items():
            nodes = [node for node in rule_graph.nodes if node.node_type in node_types]
            if not nodes:
                assessments.append(
                    RuleCoverageAssessment(
                        dimension=dimension,
                        state=RuleCoverageState.MISSING,
                    )
                )
                data_blockers.append(f"RULE_COVERAGE_MISSING:{dimension.value}")
                continue

            states = {node.verification_status for node in nodes}
            evidence_bound = all(bool(node.evidence_ref) for node in nodes)
            if states == {RuleVerificationStatus.VERIFIED} and evidence_bound:
                state = RuleCoverageState.VERIFIED
            elif states <= {
                RuleVerificationStatus.VERIFIED,
                RuleVerificationStatus.SOURCE_BOUND,
            } and evidence_bound:
                state = RuleCoverageState.SOURCE_BOUND
            else:
                state = RuleCoverageState.UNVERIFIED
                evidence_blockers.append(f"RULE_EVIDENCE_INSUFFICIENT:{dimension.value}")
            assessments.append(
                RuleCoverageAssessment(
                    dimension=dimension,
                    state=state,
                    ruleIds=sorted(node.rule_id for node in nodes),
                )
            )
        return assessments, data_blockers, evidence_blockers

    @staticmethod
    def _capability_assessments(
        rule_graph: RuleGraphReadResponse,
        component_sets: list[Any],
        component_kinds: set[ComponentKind],
    ) -> tuple[list[CapabilityAssessment], list[str]]:
        del component_sets, component_kinds
        required: dict[CapabilityName, set[str]] = defaultdict(set)
        not_required: dict[CapabilityName, set[str]] = defaultdict(set)
        blockers: list[str] = []

        for node in rule_graph.nodes:
            if node.verification_status not in {
                RuleVerificationStatus.SOURCE_BOUND,
                RuleVerificationStatus.VERIFIED,
            } or not node.evidence_ref:
                continue
            explicit = node.metadata.get("vrchat_capabilities")
            if not isinstance(explicit, dict):
                continue
            for raw_name, raw_state in explicit.items():
                try:
                    capability = CapabilityName(str(raw_name))
                except ValueError:
                    blockers.append(f"UNKNOWN_CAPABILITY_METADATA:{raw_name}")
                    continue
                if raw_state in {True, "required"}:
                    required[capability].add(node.rule_id)
                elif raw_state in {False, "not-required", "not_required"}:
                    not_required[capability].add(node.rule_id)
                else:
                    blockers.append(f"INVALID_CAPABILITY_METADATA:{capability.value}")

        assessments: list[CapabilityAssessment] = []
        for capability in CapabilityName:
            required_refs = required.get(capability, set())
            not_required_refs = not_required.get(capability, set())
            if required_refs and not_required_refs:
                requirement = RequirementState.UNKNOWN
                reason_code = "STRUCTURED_CAPABILITY_EVIDENCE_CONFLICT"
                evidence_refs = sorted(required_refs | not_required_refs)
                blockers.append(f"CAPABILITY_EVIDENCE_CONFLICT:{capability.value}")
            elif required_refs:
                requirement = RequirementState.REQUIRED
                reason_code = "EXPLICIT_VERIFIED_CAPABILITY_REQUIRED"
                evidence_refs = sorted(required_refs)
            elif not_required_refs:
                requirement = RequirementState.NOT_REQUIRED
                reason_code = "EXPLICIT_VERIFIED_CAPABILITY_NOT_REQUIRED"
                evidence_refs = sorted(not_required_refs)
            else:
                requirement = RequirementState.UNKNOWN
                reason_code = "NO_EXPLICIT_VERIFIED_CAPABILITY_EVIDENCE"
                evidence_refs = []
            assessments.append(
                CapabilityAssessment(
                    capability=capability,
                    requirement=requirement,
                    evidenceRefs=evidence_refs,
                    reasonCode=reason_code,
                )
            )
        return assessments, blockers

    async def _audit_ruleset(self, *args, **kwargs) -> ReadinessAuditRecord:
        record = await super()._audit_ruleset(*args, **kwargs)
        rights_blockers = sorted({*record.rights_blockers, _RIGHTS_BLOCKER})
        readiness_status = record.readiness_status
        if readiness_status == ReadinessStatus.READY:
            readiness_status = ReadinessStatus.REVIEW_REQUIRED
        payload = record.model_dump(mode="python")
        payload.update(
            rights_blockers=rights_blockers,
            readiness_status=readiness_status,
            promotable_to_catalog=readiness_status == ReadinessStatus.READY,
        )
        return ReadinessAuditRecord.model_validate(payload)
