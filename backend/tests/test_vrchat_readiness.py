import json
from datetime import UTC, datetime

import pytest

from app.models import GameDetail
from app.models.component_catalog import (
    ComponentKind,
    ComponentListItem,
    ComponentListResponse,
    ComponentSet,
    ComponentSetListResponse,
)
from app.models.rule_graph import RuleGraphReadResponse, RuleNode, RuleNodeType
from app.models.ruleset import RuleSet, RuleSetListResponse
from app.models.vrchat_manifest import CapabilityName
from app.models.vrchat_readiness import ReadinessStatus, RequirementState
from app.services.vrchat_readiness_audit import VrchatReadinessAuditService

AUDITED_AT = datetime(2026, 8, 14, tzinfo=UTC)


def _game(game_id: str, slug: str, *, verified: bool = True) -> GameDetail:
    return GameDetail(
        id=game_id,
        slug=slug,
        title=f"Game {game_id}",
        identity_status="verified" if verified else "unverified",
        min_players=2,
        max_players=4,
    )


def _ruleset(game_id: str, ruleset_id: str) -> RuleSet:
    return RuleSet(
        ruleset_id=ruleset_id,
        game_id=game_id,
        language_code="ja",
        edition_label="standard",
        platform="physical",
        source_revision="publisher-v1",
        status="active",
        verification_status="verified",
        source_ids=["source.publisher"],
    )


def _verified_node(
    rule_id: str,
    node_type: RuleNodeType,
    *,
    metadata: dict | None = None,
) -> RuleNode:
    return RuleNode(
        rule_id=rule_id,
        node_type=node_type,
        normalized_statement=rule_id,
        verification_status="verified",
        source_claim_ref=f"claim.{rule_id}",
        evidence_ref=f"evidence.{rule_id}",
        metadata=metadata or {},
    )


def _complete_rule_graph(game_id: str, slug: str, ruleset_id: str) -> RuleGraphReadResponse:
    explicit_non_requirements = {
        "vrchat_capabilities": {
            "simultaneous": "not-required",
            "hidden-information": "not-required",
            "dice": "not-required",
            "tokens": "not-required",
            "board": "not-required",
            "timer": "not-required",
            "realtime": "not-required",
            "dexterity": "not-required",
        }
    }
    return RuleGraphReadResponse(
        status="available",
        game_id=game_id,
        slug=slug,
        rule_set_id=ruleset_id,
        language_code="ja",
        edition_label="standard",
        source_revision="publisher-v1",
        nodes=[
            _verified_node("setup.start", RuleNodeType.SETUP, metadata=explicit_non_requirements),
            _verified_node("phase.main", RuleNodeType.PHASE),
            _verified_node("turn.main", RuleNodeType.TURN),
            _verified_node("action.play", RuleNodeType.ACTION),
            _verified_node("effect.resolve", RuleNodeType.EFFECT),
            _verified_node("score.points", RuleNodeType.SCORING),
            _verified_node("end.game", RuleNodeType.GAME_END),
            _verified_node("victory.highest", RuleNodeType.VICTORY),
        ],
    )


class FakeGameService:
    def __init__(self, games: list[GameDetail]):
        self.games = games

    async def list_recent_games(self, limit: int = 100, offset: int = 0):
        rows = [game.model_dump(mode="json") for game in self.games[offset : offset + limit]]
        return {"data": rows, "total": len(self.games)}


class FakeRuleSetService:
    def __init__(self, by_slug: dict[str, list[RuleSet]]):
        self.by_slug = by_slug

    async def get_by_slug(self, slug: str):
        rulesets = self.by_slug.get(slug, [])
        game_id = rulesets[0].game_id if rulesets else slug
        return RuleSetListResponse(
            status="available" if rulesets else "not_available",
            game_id=game_id,
            slug=slug,
            rulesets=rulesets,
        )


class FakeRuleGraphService:
    def __init__(self, graphs: dict[tuple[str, str], RuleGraphReadResponse]):
        self.graphs = graphs

    async def get_by_slug(self, slug: str, *, rule_set_id: str | None = None, **_kwargs):
        return self.graphs.get((slug, rule_set_id or ""))


class FakeComponentCatalogService:
    def __init__(self, available: set[tuple[str, str]]):
        self.available = available

    async def get_sets(self, slug: str, rule_set_id: str):
        if (slug, rule_set_id) not in self.available:
            return ComponentSetListResponse(
                status="not_available",
                game_id=slug,
                slug=slug,
                ruleset_id=rule_set_id,
            )
        return ComponentSetListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            component_sets=[
                ComponentSet(
                    component_set_id="set.cards",
                    ruleset_id=rule_set_id,
                    canonical_name="Cards",
                    kind=ComponentKind.CARD,
                    verification_status="verified",
                    source_ids=["source.components"],
                )
            ],
        )

    async def list_components(
        self,
        slug: str,
        rule_set_id: str,
        component_set_id=None,
        kind=None,
        limit: int = 100,
        offset: int = 0,
    ):
        if (slug, rule_set_id) not in self.available:
            return ComponentListResponse(
                status="not_available",
                game_id=slug,
                slug=slug,
                ruleset_id=rule_set_id,
                limit=limit,
                offset=offset,
            )
        items = []
        if offset == 0:
            items = [
                ComponentListItem(
                    component_id="card.example",
                    component_set_id="set.cards",
                    canonical_name="Example Card",
                    kind=ComponentKind.CARD,
                    verification_status="verified",
                )
            ]
        return ComponentListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            components=items,
            total=1,
            limit=limit,
            offset=offset,
        )


def _registry_file(tmp_path, *, include_binding: bool = True):
    path = tmp_path / "module-bindings-v1.json"
    entries = []
    if include_binding:
        entries.append(
            {
                "slug": "game-one",
                "rulesetId": "ruleset-1",
                "binding": {
                    "moduleId": "vrmine.game-one",
                    "moduleVersionRange": ">=1.0.0,<2.0.0",
                    "supportedPlatforms": ["vrchat-pc"],
                    "interactionProfile": "desktop-and-vr",
                    "capabilities": {
                        "turn-based": "supported",
                        "deck": "supported",
                        "score": "supported",
                    },
                },
                "publicationStatus": "playable",
                "snapshotAt": "2026-08-14T00:00:00Z",
            }
        )
    path.write_text(json.dumps({"schemaVersion": "1.0", "entries": entries), encoding="utf-8")
    return path


def _service(tmp_path, *, include_binding: bool = True):
    game_one = _game("game-1", "game-one")
    game_two = _game("game-2", "game-two", verified=False)
    ruleset = _ruleset("game-1", "ruleset-1")
    return VrchatReadinessAuditService(
        registry_path=_registry_file(tmp_path, include_binding=include_binding),
        game_service=FakeGameService([game_one, game_two]),
        ruleset_service=FakeRuleSetService({"game-one": [ruleset]}),
        rule_graph_service=FakeRuleGraphService(
            {("game-one", "ruleset-1"): _complete_rule_graph("game-1", "game-one", "ruleset-1")}
        ),
        component_catalog_service=FakeComponentCatalogService({("game-one", "ruleset-1")}),
    )


@pytest.mark.asyncio
async def test_full_catalog_audit_accounts_for_every_canonical_game(tmp_path):
    report = await _service(tmp_path).audit_all(audited_at=AUDITED_AT)

    assert report.total_games == 2
    assert report.total_records == 2
    assert {record.game_id for record in report.records} == {"game-1", "game-2"}
    assert sum(report.status_counts.values()) == 2


@pytest.mark.asyncio
async def test_structured_capabilities_are_explicit_and_free_text_is_not_inferred(tmp_path):
    report = await _service(tmp_path).audit_all(audited_at=AUDITED_AT)
    record = next(item for item in report.records if item.game_id == "game-1")
    assessments = {item.capability: item for item in record.capability_assessments}

    assert assessments[CapabilityName.TURN_BASED].requirement == RequirementState.REQUIRED
    assert assessments[CapabilityName.DECK].requirement == RequirementState.REQUIRED
    assert assessments[CapabilityName.SCORE].requirement == RequirementState.REQUIRED
    assert assessments[CapabilityName.HIDDEN_INFORMATION].requirement == RequirementState.NOT_REQUIRED
    assert assessments[CapabilityName.REALTIME].requirement == RequirementState.NOT_REQUIRED
    assert record.unknown_capabilities == []


@pytest.mark.asyncio
async def test_manifest_projectability_is_connected_to_183_without_promoting_incomplete_components(tmp_path):
    report = await _service(tmp_path).audit_all(audited_at=AUDITED_AT)
    record = next(item for item in report.records if item.game_id == "game-1")

    assert record.manifest_projectable is True
    assert record.module_id == "vrmine.game-one"
    assert record.missing_capabilities == []
    assert record.runtime_blockers == []
    assert "COMPONENT_COMPLETENESS_UNKNOWN" in record.evidence_blockers
    assert record.readiness_status == ReadinessStatus.REVIEW_REQUIRED
    assert record.promotable_to_catalog is False


@pytest.mark.asyncio
async def test_missing_module_binding_is_runtime_blocker_not_evidence_blocker(tmp_path):
    report = await _service(tmp_path, include_binding=False).audit_all(audited_at=AUDITED_AT)
    record = next(item for item in report.records if item.game_id == "game-1")

    assert record.readiness_status == ReadinessStatus.BLOCKED
    assert record.runtime_blockers == ["MODULE_BINDING_NOT_REGISTERED"]
    assert record.missing_capabilities == [
        CapabilityName.DECK,
        CapabilityName.SCORE,
        CapabilityName.TURN_BASED,
    ]
    assert record.manifest_projectable is False


@pytest.mark.asyncio
async def test_no_ruleset_game_is_preserved_as_blocked_record(tmp_path):
    report = await _service(tmp_path).audit_all(audited_at=AUDITED_AT)
    record = next(item for item in report.records if item.game_id == "game-2")

    assert record.ruleset_id is None
    assert record.readiness_status == ReadinessStatus.BLOCKED
    assert "RULESETS_NOT_AVAILABLE" in record.data_blockers
    assert "GAME_IDENTITY_NOT_VERIFIED" in record.data_blockers
    assert all(item.requirement == RequirementState.UNKNOWN for item in record.capability_assessments)


@pytest.mark.asyncio
async def test_audit_paginates_past_first_hundred_games(tmp_path):
    games = [_game(f"game-{index}", f"game-{index}") for index in range(105)]
    service = VrchatReadinessAuditService(
        registry_path=_registry_file(tmp_path, include_binding=False),
        game_service=FakeGameService(games),
        ruleset_service=FakeRuleSetService({}),
        rule_graph_service=FakeRuleGraphService({}),
        component_catalog_service=FakeComponentCatalogService(set()),
    )

    report = await service.audit_all(audited_at=AUDITED_AT)

    assert report.total_games == 105
    assert report.total_records == 105
    assert all(record.readiness_status == ReadinessStatus.BLOCKED for record in report.records)


def test_only_clean_active_record_can_be_ready_and_promotable():
    ruleset = _ruleset("game-1", "ruleset-1")
    status = VrchatReadinessAuditService._readiness_status(
        ruleset=ruleset,
        explicit_runtime_unsupported=False,
        data_blockers=[],
        evidence_blockers=[],
        rights_blockers=[],
        runtime_blockers=[],
        unknown_capabilities=[],
        missing_capabilities=[],
    )

    assert status == ReadinessStatus.READY
