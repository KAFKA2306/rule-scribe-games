from __future__ import annotations

from datetime import datetime

from app.models import GameDetail
from app.models.component_catalog import COMPONENT_CATALOG_SCHEMA_VERSION, ComponentCatalog
from app.models.rule_graph import (
    RULE_GRAPH_SCHEMA_VERSION,
    RuleGraphReadResponse,
    RuleNode,
    RuleNodeType,
    RuleVerificationStatus,
)
from app.models.ruleset import RULESET_SCHEMA_VERSION, RuleSet
from app.models.vrchat_manifest import (
    BoardGameModuleManifest,
    CapabilityMatrix,
    CapabilityName,
    CapabilityState,
    EvidenceSummary,
    ModuleBinding,
    PlayerCount,
    RuleReferences,
    SourceSchemaVersions,
)


_RULE_BUCKETS: dict[RuleNodeType, str] = {
    RuleNodeType.SETUP: "setup",
    RuleNodeType.PHASE: "phases",
    RuleNodeType.TURN: "turns",
    RuleNodeType.ACTION: "actions",
    RuleNodeType.CONDITION: "conditions",
    RuleNodeType.EFFECT: "effects",
    RuleNodeType.SCORING: "scoring",
    RuleNodeType.ROUND_END: "round_ends",
    RuleNodeType.GAME_END: "end_conditions",
    RuleNodeType.VICTORY: "victory",
    RuleNodeType.EXCEPTION: "exceptions",
    RuleNodeType.TARGETING: "targeting",
    RuleNodeType.CONFLICT_RESOLUTION: "conflict_resolution",
    RuleNodeType.VARIANT: "variants",
}


def _canonical_game_id(game: GameDetail) -> str:
    game_id = str(game.id).strip()
    if not game_id:
        raise ValueError("game.id is required for VRChat manifest projection")
    return game_id


def _validate_projection_identity(
    game: GameDetail,
    ruleset: RuleSet,
    rule_graph: RuleGraphReadResponse,
    component_catalog: ComponentCatalog | None,
) -> tuple[str, str]:
    game_id = _canonical_game_id(game)
    slug = (game.slug or "").strip()
    if not slug:
        raise ValueError("game.slug is required for VRChat manifest projection")
    if ruleset.game_id != game_id:
        raise ValueError("ruleset belongs to a different canonical game")
    if rule_graph.status != "available":
        raise ValueError("an available canonical rule graph is required for VRChat manifest projection")
    if rule_graph.game_id != game_id:
        raise ValueError("rule graph belongs to a different canonical game")
    if rule_graph.slug != slug:
        raise ValueError("rule graph slug does not match the canonical game")
    if rule_graph.rule_set_id != ruleset.ruleset_id:
        raise ValueError("rule graph and ruleset identities do not match")
    if (
        rule_graph.language_code
        and ruleset.language_code
        and rule_graph.language_code != ruleset.language_code
    ):
        raise ValueError("rule graph and ruleset language identities do not match")
    if (
        rule_graph.edition_label
        and ruleset.edition_label
        and rule_graph.edition_label != ruleset.edition_label
    ):
        raise ValueError("rule graph and ruleset edition identities do not match")
    if (
        rule_graph.source_revision
        and ruleset.source_revision
        and rule_graph.source_revision != ruleset.source_revision
    ):
        raise ValueError("rule graph and ruleset source revisions do not match")
    if component_catalog is not None and component_catalog.ruleset_id != ruleset.ruleset_id:
        raise ValueError("component catalog belongs to a different ruleset")
    return game_id, slug


def _player_count(game: GameDetail) -> PlayerCount:
    minimum = game.min_players
    maximum = game.max_players
    if minimum is not None and minimum < 1:
        raise ValueError("game.min_players must be positive")
    if maximum is not None and maximum < 1:
        raise ValueError("game.max_players must be positive")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("game.min_players cannot exceed game.max_players")
    status = (
        "known"
        if minimum is not None and maximum is not None
        else "partial"
        if minimum is not None or maximum is not None
        else "unknown"
    )
    return PlayerCount(min=minimum, max=maximum, status=status)


def _sorted_nodes(nodes: list[RuleNode]) -> list[RuleNode]:
    return sorted(
        nodes,
        key=lambda node: (
            node.sequence is None,
            node.sequence if node.sequence is not None else 0,
            node.rule_id,
        ),
    )


def _rule_references(rule_graph: RuleGraphReadResponse) -> RuleReferences:
    buckets: dict[str, list[str]] = {field: [] for field in _RULE_BUCKETS.values()}
    for node in _sorted_nodes(rule_graph.nodes):
        buckets[_RULE_BUCKETS[node.node_type]].append(node.rule_id)
    return RuleReferences(**buckets)


def _component_source_ids(component_catalog: ComponentCatalog | None) -> set[str]:
    if component_catalog is None:
        return set()
    source_ids: set[str] = set()
    for item in component_catalog.component_sets:
        source_ids.update(item.source_ids)
    for definition in component_catalog.property_definitions:
        source_ids.update(definition.source_ids)
    for component in component_catalog.components:
        source_ids.update(component.source_ids)
        for prop in component.properties:
            source_ids.update(prop.source_ids)
        for ability in component.abilities:
            source_ids.update(ability.source_ids)
    return source_ids


def _evidence_summary(
    ruleset: RuleSet,
    rule_graph: RuleGraphReadResponse,
    component_catalog: ComponentCatalog | None,
) -> EvidenceSummary:
    source_ids = set(ruleset.source_ids)
    source_ids.update(_component_source_ids(component_catalog))
    claim_refs = {node.source_claim_ref for node in rule_graph.nodes if node.source_claim_ref}
    evidence_refs = {node.evidence_ref for node in rule_graph.nodes if node.evidence_ref}

    verified: list[str] = []
    source_bound: list[str] = []
    unverified: list[str] = []
    rejected: list[str] = []

    for node in _sorted_nodes(rule_graph.nodes):
        if node.verification_status == RuleVerificationStatus.VERIFIED:
            verified.append(node.rule_id)
        elif node.verification_status == RuleVerificationStatus.SOURCE_BOUND:
            source_bound.append(node.rule_id)
        elif node.verification_status == RuleVerificationStatus.REJECTED:
            rejected.append(node.rule_id)
        else:
            unverified.append(node.rule_id)

    return EvidenceSummary(
        sourceIds=sorted(source_ids),
        claimRefs=sorted(claim_refs),
        evidenceRefs=sorted(evidence_refs),
        verifiedRuleIds=verified,
        sourceBoundRuleIds=source_bound,
        unverifiedRuleIds=unverified,
        rejectedRuleIds=rejected,
    )


def project_board_game_module_manifest(  # noqa: PLR0913 - explicit source boundaries are part of the contract
    *,
    game: GameDetail,
    ruleset: RuleSet,
    rule_graph: RuleGraphReadResponse,
    component_catalog: ComponentCatalog | None,
    binding: ModuleBinding,
    generated_at: datetime,
) -> BoardGameModuleManifest:
    """Project canonical game data plus an explicit runtime binding into Manifest v1.

    The function is intentionally pure: it does not read the wall clock, fetch remote
    data, or infer runtime capabilities. Missing capability declarations become
    ``unknown``.
    """

    game_id, slug = _validate_projection_identity(game, ruleset, rule_graph, component_catalog)
    capabilities = CapabilityMatrix.model_validate(
        {
            capability.value: binding.capabilities.get(capability, CapabilityState.UNKNOWN).value
            for capability in CapabilityName
        }
    )
    component_set_refs = (
        sorted(item.component_set_id for item in component_catalog.component_sets)
        if component_catalog is not None
        else []
    )

    return BoardGameModuleManifest(
        gameId=game_id,
        slug=slug,
        rulesetId=ruleset.ruleset_id,
        moduleId=binding.module_id,
        moduleVersionRange=binding.module_version_range,
        playerCount=_player_count(game),
        supportedPlatforms=sorted(binding.supported_platforms, key=lambda item: item.value),
        interactionProfile=binding.interaction_profile,
        capabilities=capabilities,
        rules=_rule_references(rule_graph),
        componentSetRefs=component_set_refs,
        evidence=_evidence_summary(ruleset, rule_graph, component_catalog),
        sourceSchemas=SourceSchemaVersions(
            ruleset=RULESET_SCHEMA_VERSION,
            ruleGraph=RULE_GRAPH_SCHEMA_VERSION,
            componentCatalog=COMPONENT_CATALOG_SCHEMA_VERSION if component_catalog is not None else None,
        ),
        locale=ruleset.language_code,
        revision=ruleset.source_revision or ruleset.revision_label,
        generatedAt=generated_at,
    )
