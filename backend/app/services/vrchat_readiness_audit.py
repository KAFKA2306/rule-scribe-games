from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models import GameDetail
from app.models.component_catalog import (
    ComponentCatalog,
    ComponentKind,
    ComponentVerificationStatus,
)
from app.models.rule_graph import (
    RuleGraphReadResponse,
    RuleNode,
    RuleNodeType,
    RuleVerificationStatus,
)
from app.models.ruleset import RuleSet, RuleSetStatus, RuleSetVerificationStatus
from app.models.vrchat_catalog import (
    BindingRegistryEntry,
    BindingRegistryFile,
    PublicationStatus,
)
from app.models.vrchat_manifest import CapabilityName, CapabilityState
from app.models.vrchat_readiness import (
    CapabilityAssessment,
    ReadinessAuditRecord,
    ReadinessAuditReport,
    ReadinessStatus,
    RequirementState,
    RuleCoverageAssessment,
    RuleCoverageDimension,
    RuleCoverageState,
)
from app.services.component_catalog import ComponentCatalogService
from app.services.game_service import GameService
from app.services.rule_graph import RuleGraphService
from app.services.rulesets import RuleSetService
from app.services.vrchat_manifest_catalog import DEFAULT_REGISTRY_PATH
from app.services.vrchat_manifest_projection import project_board_game_module_manifest

_PAGE_SIZE = 100

_COVERAGE_TYPES: dict[RuleCoverageDimension, set[RuleNodeType]] = {
    RuleCoverageDimension.SETUP: {RuleNodeType.SETUP},
    RuleCoverageDimension.LOOP: {RuleNodeType.PHASE, RuleNodeType.TURN},
    RuleCoverageDimension.ACTION: {RuleNodeType.ACTION},
    RuleCoverageDimension.RESOLUTION: {RuleNodeType.EFFECT, RuleNodeType.CONFLICT_RESOLUTION},
    RuleCoverageDimension.END: {RuleNodeType.GAME_END},
    RuleCoverageDimension.WIN: {RuleNodeType.VICTORY},
}

_COMPONENT_CAPABILITIES: dict[ComponentKind, set[CapabilityName]] = {
    ComponentKind.CARD: {CapabilityName.DECK},
    ComponentKind.TILE: {CapabilityName.BOARD},
    ComponentKind.TOKEN: {CapabilityName.TOKENS},
    ComponentKind.DIE: {CapabilityName.DICE},
    ComponentKind.BOARD: {CapabilityName.BOARD},
    ComponentKind.FIGURE: {CapabilityName.TOKENS},
    ComponentKind.MARKER: {CapabilityName.TOKENS},
}


class VrchatReadinessAuditService:
    def __init__(
        self,
        *,
        registry_path: Path = DEFAULT_REGISTRY_PATH,
        game_service: GameService | None = None,
        ruleset_service: RuleSetService | None = None,
        rule_graph_service: RuleGraphService | None = None,
        component_catalog_service: ComponentCatalogService | None = None,
    ):
        self.registry_path = registry_path
        self.game_service = game_service or GameService()
        self.ruleset_service = ruleset_service or RuleSetService()
        self.rule_graph_service = rule_graph_service or RuleGraphService()
        self.component_catalog_service = component_catalog_service or ComponentCatalogService()

    async def audit_all(self, *, audited_at: datetime) -> ReadinessAuditReport:
        games = await self._load_all_games()
        registry = BindingRegistryFile.model_validate_json(self.registry_path.read_text(encoding="utf-8"))
        registry_by_key = {(entry.slug, entry.ruleset_id): entry for entry in registry.entries}
        records: list[ReadinessAuditRecord] = []

        for game, inherited_blockers in games:
            if not game.slug:
                records.append(
                    self._record_without_ruleset(
                        game,
                        audited_at=audited_at,
                        data_blockers=[*inherited_blockers, "GAME_SLUG_MISSING"],
                    )
                )
                continue

            try:
                rulesets_response = await self.ruleset_service.get_by_slug(game.slug)
            except Exception:  # pragma: no cover - connector/network clients vary by deployment
                rulesets_response = None

            if (
                rulesets_response is None
                or rulesets_response.status != "available"
                or not rulesets_response.rulesets
            ):
                records.append(
                    self._record_without_ruleset(
                        game,
                        audited_at=audited_at,
                        data_blockers=[*inherited_blockers, "RULESETS_NOT_AVAILABLE"],
                    )
                )
                continue

            ambiguous_ids = self._ambiguous_active_ruleset_ids(rulesets_response.rulesets)
            for ruleset in sorted(rulesets_response.rulesets, key=lambda item: item.ruleset_id):
                records.append(
                    await self._audit_ruleset(
                        game,
                        ruleset,
                        audited_at=audited_at,
                        binding=registry_by_key.get((game.slug, ruleset.ruleset_id)),
                        inherited_blockers=inherited_blockers,
                        ambiguous_ruleset=ruleset.ruleset_id in ambiguous_ids,
                    )
                )

        records.sort(key=lambda item: (item.slug or "", item.ruleset_id or "", item.game_id))
        status_counts = {status: 0 for status in ReadinessStatus}
        for record in records:
            status_counts[record.readiness_status] += 1
        return ReadinessAuditReport(
            auditedAt=audited_at,
            totalGames=len({record.game_id for record in records}),
            totalRecords=len(records),
            promotableCount=sum(record.promotable_to_catalog for record in records),
            statusCounts=status_counts,
            records=records,
        )

    async def _load_all_games(self) -> list[tuple[GameDetail, list[str]]]:
        output: list[tuple[GameDetail, list[str]]] = []
        offset = 0
        expected_total: int | None = None

        while True:
            page = await self.game_service.list_recent_games(limit=_PAGE_SIZE, offset=offset)
            rows = list(page.get("data") or [])
            if expected_total is None:
                raw_total = page.get("total")
                expected_total = int(raw_total) if raw_total is not None else None
            if not rows:
                break

            for row in rows:
                blockers: list[str] = []
                try:
                    game = GameDetail.model_validate(row)
                except ValidationError:
                    game_id = str(row.get("id") or "").strip()
                    if not game_id:
                        raise ValueError("canonical game row without id cannot be audited") from None
                    game = GameDetail(
                        id=game_id,
                        slug=row.get("slug"),
                        title=str(row.get("title") or game_id),
                        identity_status="needs_review",
                    )
                    blockers.append("GAME_RECORD_INVALID")
                output.append((game, blockers))

            offset += len(rows)
            if expected_total is not None and offset >= expected_total:
                break
            if len(rows) < _PAGE_SIZE and expected_total is None:
                break

        if expected_total is not None and len(output) != expected_total:
            raise RuntimeError(
                f"full-catalog audit pagination mismatch: expected {expected_total}, loaded {len(output)}"
            )
        if not output:
            raise RuntimeError("full-catalog audit returned zero canonical games")
        return output

    async def _audit_ruleset(
        self,
        game: GameDetail,
        ruleset: RuleSet,
        *,
        audited_at: datetime,
        binding: BindingRegistryEntry | None,
        inherited_blockers: list[str],
        ambiguous_ruleset: bool,
    ) -> ReadinessAuditRecord:
        data_blockers = list(inherited_blockers)
        evidence_blockers: list[str] = []
        rights_blockers: list[str] = []
        runtime_blockers: list[str] = []

        if game.identity_status != "verified":
            data_blockers.append("GAME_IDENTITY_NOT_VERIFIED")
        player_count_status = self._player_count_status(game)
        if player_count_status != "known":
            data_blockers.append("PLAYER_COUNT_NOT_VERIFIED")
        if ambiguous_ruleset:
            data_blockers.append("AMBIGUOUS_ACTIVE_RULESET_IDENTITY")
        if ruleset.verification_status not in {
            RuleSetVerificationStatus.SOURCE_BOUND,
            RuleSetVerificationStatus.VERIFIED,
        } or not ruleset.source_ids:
            evidence_blockers.append("RULESET_EVIDENCE_INSUFFICIENT")

        try:
            rule_graph = await self.rule_graph_service.get_by_slug(
                game.slug or "",
                rule_set_id=ruleset.ruleset_id,
            )
        except Exception:  # pragma: no cover - external client behavior
            rule_graph = None
        if rule_graph is None or rule_graph.status != "available":
            data_blockers.append("RULE_GRAPH_NOT_AVAILABLE")
            rule_graph = RuleGraphReadResponse(
                status="not_available",
                game_id=str(game.id),
                slug=game.slug or "",
            )

        coverage, coverage_data_blockers, coverage_evidence_blockers = self._rule_coverage(rule_graph)
        data_blockers.extend(coverage_data_blockers)
        evidence_blockers.extend(coverage_evidence_blockers)

        component_sets = []
        property_definitions = []
        component_kinds: set[ComponentKind] = set()
        component_count: int | None = None
        try:
            component_sets_response = await self.component_catalog_service.get_sets(
                game.slug or "",
                ruleset.ruleset_id,
            )
        except Exception:  # pragma: no cover - external client behavior
            component_sets_response = None

        if component_sets_response is None or component_sets_response.status != "available":
            data_blockers.append("COMPONENT_CATALOG_NOT_AVAILABLE")
        else:
            component_sets = component_sets_response.component_sets
            property_definitions = component_sets_response.property_definitions
            component_kinds.update(item.kind for item in component_sets if item.kind is not None)
            if any(
                item.verification_status not in {
                    ComponentVerificationStatus.SOURCE_BOUND,
                    ComponentVerificationStatus.VERIFIED,
                }
                for item in component_sets
            ):
                evidence_blockers.append("COMPONENT_SET_EVIDENCE_INSUFFICIENT")
            evidence_blockers.append("COMPONENT_COMPLETENESS_UNKNOWN")
            component_count, listed_kinds, list_evidence_incomplete = await self._component_summary(
                game.slug or "",
                ruleset.ruleset_id,
            )
            component_kinds.update(listed_kinds)
            if list_evidence_incomplete:
                evidence_blockers.append("COMPONENT_RECORD_EVIDENCE_INSUFFICIENT")

        assessments, capability_evidence_blockers = self._capability_assessments(
            rule_graph,
            component_sets,
            component_kinds,
        )
        evidence_blockers.extend(capability_evidence_blockers)
        required_capabilities = sorted(
            (
                item.capability
                for item in assessments
                if item.requirement == RequirementState.REQUIRED
            ),
            key=lambda item: item.value,
        )
        unknown_capabilities = sorted(
            (
                item.capability
                for item in assessments
                if item.requirement == RequirementState.UNKNOWN
            ),
            key=lambda item: item.value,
        )

        missing_capabilities: list[CapabilityName] = []
        module_id: str | None = None
        module_version_range: str | None = None
        manifest_projectable = False
        explicit_runtime_unsupported = False

        if binding is None:
            runtime_blockers.append("MODULE_BINDING_NOT_REGISTERED")
            missing_capabilities.extend(required_capabilities)
        else:
            module_id = binding.binding.module_id
            module_version_range = binding.binding.module_version_range
            if binding.publication_status != PublicationStatus.PLAYABLE:
                runtime_blockers.append(f"MODULE_BINDING_STATUS:{binding.publication_status.value}")
                explicit_runtime_unsupported = binding.publication_status == PublicationStatus.UNSUPPORTED
            for capability in required_capabilities:
                if binding.binding.capabilities.get(capability, CapabilityState.UNKNOWN) != CapabilityState.SUPPORTED:
                    missing_capabilities.append(capability)
            if missing_capabilities:
                runtime_blockers.append("REQUIRED_RUNTIME_CAPABILITY_MISSING")

            if rule_graph.status == "available":
                try:
                    project_board_game_module_manifest(
                        game=game,
                        ruleset=ruleset,
                        rule_graph=rule_graph,
                        component_catalog=ComponentCatalog(
                            ruleset_id=ruleset.ruleset_id,
                            component_sets=component_sets,
                            property_definitions=property_definitions,
                        ),
                        binding=binding.binding,
                        generated_at=audited_at,
                    )
                    manifest_projectable = True
                except (ValueError, ValidationError):
                    data_blockers.append("MANIFEST_PROJECTION_INVALID")

        data_blockers = sorted(set(data_blockers))
        evidence_blockers = sorted(set(evidence_blockers))
        rights_blockers = sorted(set(rights_blockers))
        runtime_blockers = sorted(set(runtime_blockers))
        missing_capabilities = sorted(set(missing_capabilities), key=lambda item: item.value)

        readiness_status = self._readiness_status(
            ruleset=ruleset,
            explicit_runtime_unsupported=explicit_runtime_unsupported,
            data_blockers=data_blockers,
            evidence_blockers=evidence_blockers,
            rights_blockers=rights_blockers,
            runtime_blockers=runtime_blockers,
            unknown_capabilities=unknown_capabilities,
            missing_capabilities=missing_capabilities,
        )

        return ReadinessAuditRecord(
            gameId=str(game.id),
            slug=game.slug,
            title=game.title,
            rulesetId=ruleset.ruleset_id,
            rulesetLanguage=ruleset.language_code,
            rulesetEdition=ruleset.edition_label,
            rulesetPlatform=ruleset.platform,
            readinessStatus=readiness_status,
            playerCountStatus=player_count_status,
            ruleCoverage=coverage,
            capabilityAssessments=assessments,
            requiredCapabilities=required_capabilities,
            unknownCapabilities=unknown_capabilities,
            missingCapabilities=missing_capabilities,
            componentKinds=sorted(component_kinds, key=lambda item: item.value),
            componentCount=component_count,
            dataBlockers=data_blockers,
            evidenceBlockers=evidence_blockers,
            rightsBlockers=rights_blockers,
            runtimeBlockers=runtime_blockers,
            assetPolicy="generic-only",
            recommendedModuleClass=self._recommended_module_class(required_capabilities),
            manifestProjectable=manifest_projectable,
            moduleId=module_id,
            moduleVersionRange=module_version_range,
            promotableToCatalog=readiness_status == ReadinessStatus.READY,
            auditedAt=audited_at,
        )

    async def _component_summary(
        self,
        slug: str,
        ruleset_id: str,
    ) -> tuple[int | None, set[ComponentKind], bool]:
        offset = 0
        kinds: set[ComponentKind] = set()
        total: int | None = None
        evidence_incomplete = False

        while True:
            try:
                response = await self.component_catalog_service.list_components(
                    slug,
                    ruleset_id,
                    limit=_PAGE_SIZE,
                    offset=offset,
                )
            except Exception:  # pragma: no cover - external client behavior
                return None, kinds, True
            if response is None or response.status != "available":
                return None, kinds, True
            if total is None:
                total = response.total
            for item in response.components:
                kinds.add(item.kind)
                if item.verification_status not in {
                    ComponentVerificationStatus.SOURCE_BOUND,
                    ComponentVerificationStatus.VERIFIED,
                }:
                    evidence_incomplete = True
            offset += len(response.components)
            if total is not None and offset >= total:
                break
            if not response.components or len(response.components) < _PAGE_SIZE:
                break
        return total if total is not None else 0, kinds, evidence_incomplete

    def _record_without_ruleset(
        self,
        game: GameDetail,
        *,
        audited_at: datetime,
        data_blockers: list[str],
    ) -> ReadinessAuditRecord:
        blockers = list(data_blockers)
        if game.identity_status != "verified":
            blockers.append("GAME_IDENTITY_NOT_VERIFIED")
        player_count_status = self._player_count_status(game)
        if player_count_status != "known":
            blockers.append("PLAYER_COUNT_NOT_VERIFIED")
        assessments = [
            CapabilityAssessment(
                capability=capability,
                requirement=RequirementState.UNKNOWN,
                reasonCode="RULESET_REQUIRED_FOR_ASSESSMENT",
            )
            for capability in CapabilityName
        ]
        return ReadinessAuditRecord(
            gameId=str(game.id),
            slug=game.slug,
            title=game.title,
            readinessStatus=ReadinessStatus.BLOCKED,
            playerCountStatus=player_count_status,
            ruleCoverage=[
                RuleCoverageAssessment(
                    dimension=dimension,
                    state=RuleCoverageState.MISSING,
                )
                for dimension in RuleCoverageDimension
            ],
            capabilityAssessments=assessments,
            unknownCapabilities=sorted(CapabilityName, key=lambda item: item.value),
            dataBlockers=sorted(set(blockers)),
            runtimeBlockers=["MODULE_BINDING_NOT_REGISTERED"],
            assetPolicy="generic-only",
            recommendedModuleClass="review-required",
            manifestProjectable=False,
            promotableToCatalog=False,
            auditedAt=audited_at,
        )

    @staticmethod
    def _player_count_status(game: GameDetail) -> str:
        minimum = game.min_players
        maximum = game.max_players
        if minimum is not None and maximum is not None and minimum >= 1 and minimum <= maximum:
            return "known"
        if minimum is not None or maximum is not None:
            return "partial"
        return "unknown"

    @staticmethod
    def _ambiguous_active_ruleset_ids(rulesets: list[RuleSet]) -> set[str]:
        groups: dict[tuple[str | None, str | None, str | None], list[str]] = defaultdict(list)
        for ruleset in rulesets:
            if not ruleset.is_active or ruleset.status == RuleSetStatus.SUPERSEDED:
                continue
            groups[(ruleset.language_code, ruleset.edition_label, ruleset.platform)].append(ruleset.ruleset_id)
        return {
            ruleset_id
            for ruleset_ids in groups.values()
            if len(ruleset_ids) > 1
            for ruleset_id in ruleset_ids
        }

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
            traceable = all(VrchatReadinessAuditService._rule_node_traceable(node) for node in nodes)
            if states == {RuleVerificationStatus.VERIFIED} and traceable:
                state = RuleCoverageState.VERIFIED
            elif states <= {
                RuleVerificationStatus.VERIFIED,
                RuleVerificationStatus.SOURCE_BOUND,
            } and traceable:
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
    def _rule_node_traceable(node: RuleNode) -> bool:
        return bool(node.evidence_ref or node.source_claim_ref or node.source_url)

    @staticmethod
    def _capability_assessments(
        rule_graph: RuleGraphReadResponse,
        component_sets: list[Any],
        component_kinds: set[ComponentKind],
    ) -> tuple[list[CapabilityAssessment], list[str]]:
        required: dict[CapabilityName, set[str]] = defaultdict(set)
        not_required: dict[CapabilityName, set[str]] = defaultdict(set)
        blockers: list[str] = []

        if any(node.node_type == RuleNodeType.TURN for node in rule_graph.nodes):
            required[CapabilityName.TURN_BASED].update(
                node.rule_id for node in rule_graph.nodes if node.node_type == RuleNodeType.TURN
            )
        if any(node.node_type in {RuleNodeType.SCORING, RuleNodeType.VICTORY} for node in rule_graph.nodes):
            required[CapabilityName.SCORE].update(
                node.rule_id
                for node in rule_graph.nodes
                if node.node_type in {RuleNodeType.SCORING, RuleNodeType.VICTORY}
            )

        for kind in component_kinds:
            for capability in _COMPONENT_CAPABILITIES.get(kind, set()):
                required[capability].add(f"component-kind:{kind.value}")
        for component_set in component_sets:
            if component_set.kind is None:
                continue
            for capability in _COMPONENT_CAPABILITIES.get(component_set.kind, set()):
                required[capability].update(component_set.source_ids or [f"component-set:{component_set.component_set_id}"])

        for node in rule_graph.nodes:
            if node.verification_status not in {
                RuleVerificationStatus.SOURCE_BOUND,
                RuleVerificationStatus.VERIFIED,
            } or not VrchatReadinessAuditService._rule_node_traceable(node):
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
                reason_code = "STRUCTURED_REQUIREMENT_PRESENT"
                evidence_refs = sorted(required_refs)
            elif not_required_refs:
                requirement = RequirementState.NOT_REQUIRED
                reason_code = "STRUCTURED_NON_REQUIREMENT_PRESENT"
                evidence_refs = sorted(not_required_refs)
            else:
                requirement = RequirementState.UNKNOWN
                reason_code = "NO_VERIFIED_STRUCTURED_CAPABILITY_EVIDENCE"
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

    @staticmethod
    def _readiness_status(
        *,
        ruleset: RuleSet,
        explicit_runtime_unsupported: bool,
        data_blockers: list[str],
        evidence_blockers: list[str],
        rights_blockers: list[str],
        runtime_blockers: list[str],
        unknown_capabilities: list[CapabilityName],
        missing_capabilities: list[CapabilityName],
    ) -> ReadinessStatus:
        if (
            not ruleset.is_active
            or ruleset.status == RuleSetStatus.SUPERSEDED
            or explicit_runtime_unsupported
        ):
            return ReadinessStatus.UNSUPPORTED
        if data_blockers or runtime_blockers or missing_capabilities:
            return ReadinessStatus.BLOCKED
        if evidence_blockers or rights_blockers or unknown_capabilities:
            return ReadinessStatus.REVIEW_REQUIRED
        return ReadinessStatus.READY

    @staticmethod
    def _recommended_module_class(required_capabilities: list[CapabilityName]) -> str:
        required = set(required_capabilities)
        if CapabilityName.DEXTERITY in required:
            return "dexterity-specialized"
        if CapabilityName.HIDDEN_INFORMATION in required:
            return "hidden-information"
        if CapabilityName.DECK in required:
            return "card"
        if required & {CapabilityName.DICE, CapabilityName.TOKENS}:
            return "dice-token"
        if CapabilityName.BOARD in required:
            return "board-state"
        return "generic-state-machine"
