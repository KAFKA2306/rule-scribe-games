import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.models import GameDetail
from app.models.component_catalog import ComponentCatalog, ComponentKind, ComponentSet
from app.models.rule_graph import RuleGraphReadResponse, RuleNode, RuleNodeType
from app.models.ruleset import RuleSet
from app.models.vrchat_manifest import (
    BoardGameModuleManifest,
    CapabilityName,
    CapabilityState,
    ModuleBinding,
)
from app.services.vrchat_manifest_projection import project_board_game_module_manifest
from pydantic import ValidationError


GENERATED_AT = datetime(2026, 8, 14, tzinfo=UTC)


def _node(
    rule_id: str,
    node_type: RuleNodeType,
    *,
    sequence: int | None = None,
    verification_status: str = "verified",
) -> RuleNode:
    return RuleNode(
        rule_id=rule_id,
        node_type=node_type,
        normalized_statement=rule_id,
        sequence=sequence,
        verification_status=verification_status,
        source_claim_ref=f"claim.{rule_id}",
        evidence_ref=f"evidence.{rule_id}",
    )


def _canonical_inputs():
    game = GameDetail(
        id="game-1",
        slug="example-game",
        title="Example Game",
        min_players=2,
        max_players=4,
    )
    ruleset = RuleSet(
        ruleset_id="ruleset-ja-v1",
        game_id="game-1",
        language_code="ja",
        edition_label="standard",
        source_revision="publisher-v1",
        source_ids=["source.publisher"],
        verification_status="verified",
        status="active",
    )
    rule_graph = RuleGraphReadResponse(
        status="available",
        game_id="game-1",
        slug="example-game",
        rule_set_id="ruleset-ja-v1",
        language_code="ja",
        edition_label="standard",
        source_revision="publisher-v1",
        nodes=[
            _node("setup.start", RuleNodeType.SETUP, sequence=0),
            _node("phase.main", RuleNodeType.PHASE, sequence=1),
            _node("action.play", RuleNodeType.ACTION, sequence=2, verification_status="source_bound"),
            _node("score.points", RuleNodeType.SCORING, sequence=3),
            _node("end.game", RuleNodeType.GAME_END, sequence=4),
            _node("victory.highest", RuleNodeType.VICTORY, sequence=5),
            _node("target.player", RuleNodeType.TARGETING, sequence=6, verification_status="unverified"),
        ],
    )
    component_catalog = ComponentCatalog(
        ruleset_id="ruleset-ja-v1",
        component_sets=[
            ComponentSet(
                component_set_id="set.cards",
                ruleset_id="ruleset-ja-v1",
                canonical_name="Cards",
                kind=ComponentKind.CARD,
                source_ids=["source.components"],
            )
        ],
    )
    binding = ModuleBinding(
        moduleId="vrmine.example-game",
        moduleVersionRange=">=1.0.0,<2.0.0",
        supportedPlatforms=["vrchat-pc"],
        interactionProfile="desktop-and-vr",
        capabilities={
            "turn-based": "supported",
            "deck": "supported",
            "score": "supported",
        },
    )
    return game, ruleset, rule_graph, component_catalog, binding


def _project():
    game, ruleset, rule_graph, component_catalog, binding = _canonical_inputs()
    return project_board_game_module_manifest(
        game=game,
        ruleset=ruleset,
        rule_graph=rule_graph,
        component_catalog=component_catalog,
        binding=binding,
        generated_at=GENERATED_AT,
    )


def test_projection_is_deterministic_and_preserves_canonical_ids():
    first = _project()
    second = _project()

    assert first.canonical_json() == second.canonical_json()
    assert first.game_id == "game-1"
    assert first.ruleset_id == "ruleset-ja-v1"
    assert first.module_id == "vrmine.example-game"
    assert first.component_set_refs == ["set.cards"]
    assert first.rules.setup == ["setup.start"]
    assert first.rules.phases == ["phase.main"]
    assert first.rules.actions == ["action.play"]
    assert first.rules.scoring == ["score.points"]
    assert first.rules.end_conditions == ["end.game"]
    assert first.rules.victory == ["victory.highest"]
    assert first.rules.targeting == ["target.player"]


def test_projection_never_infers_undeclared_runtime_capabilities():
    manifest = _project()

    assert manifest.capabilities.state_for(CapabilityName.DECK) == CapabilityState.SUPPORTED
    assert manifest.capabilities.state_for(CapabilityName.DICE) == CapabilityState.UNKNOWN
    assert manifest.capabilities.state_for(CapabilityName.HIDDEN_INFORMATION) == CapabilityState.UNKNOWN
    assert set(manifest.capabilities.model_dump(mode="json", by_alias=True)) == {
        capability.value for capability in CapabilityName
    }


def test_projection_preserves_field_level_evidence_summary_without_promoting_unknowns():
    manifest = _project()

    assert manifest.evidence.source_ids == ["source.components", "source.publisher"]
    assert "setup.start" in manifest.evidence.verified_rule_ids
    assert manifest.evidence.source_bound_rule_ids == ["action.play"]
    assert manifest.evidence.unverified_rule_ids == ["target.player"]
    assert "claim.setup.start" in manifest.evidence.claim_refs
    assert "evidence.setup.start" in manifest.evidence.evidence_refs


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda game, ruleset, graph, catalog: (
                game,
                ruleset.model_copy(update={"game_id": "other-game"}),
                graph,
                catalog,
            ),
            "different canonical game",
        ),
        (
            lambda game, ruleset, graph, catalog: (
                game,
                ruleset,
                graph.model_copy(update={"rule_set_id": "other-ruleset"}),
                catalog,
            ),
            "identities do not match",
        ),
        (
            lambda game, ruleset, graph, catalog: (
                game,
                ruleset,
                graph.model_copy(update={"language_code": "en"}),
                catalog,
            ),
            "language identities do not match",
        ),
        (
            lambda game, ruleset, graph, catalog: (
                game,
                ruleset,
                graph.model_copy(update={"edition_label": "other-edition"}),
                catalog,
            ),
            "edition identities do not match",
        ),
        (
            lambda game, ruleset, graph, catalog: (
                game,
                ruleset,
                graph,
                catalog.model_copy(update={"ruleset_id": "other-ruleset"}),
            ),
            "different ruleset",
        ),
    ],
)
def test_projection_rejects_cross_ruleset_or_identity_mixing(mutator, message):
    game, ruleset, graph, catalog, binding = _canonical_inputs()
    game, ruleset, graph, catalog = mutator(game, ruleset, graph, catalog)

    with pytest.raises(ValueError, match=message):
        project_board_game_module_manifest(
            game=game,
            ruleset=ruleset,
            rule_graph=graph,
            component_catalog=catalog,
            binding=binding,
            generated_at=GENERATED_AT,
        )


def test_projection_fails_closed_when_canonical_rule_graph_is_unavailable():
    game, ruleset, graph, catalog, binding = _canonical_inputs()
    unavailable = graph.model_copy(
        update={"status": "not_available", "rule_set_id": None, "nodes": [], "edges": []}
    )

    with pytest.raises(ValueError, match="available canonical rule graph"):
        project_board_game_module_manifest(
            game=game,
            ruleset=ruleset,
            rule_graph=unavailable,
            component_catalog=catalog,
            binding=binding,
            generated_at=GENERATED_AT,
        )


def test_manifest_requires_explicit_unknown_state_for_every_v1_capability():
    payload = _project().model_dump(mode="json", by_alias=True)
    payload["capabilities"].pop("dice")

    with pytest.raises(ValidationError, match="dice"):
        BoardGameModuleManifest.model_validate(payload)


def test_versioned_json_schema_matches_manifest_contract_surface():
    schema_path = (
        Path(__file__).parents[2]
        / "schemas"
        / "vrchat"
        / "board-game-module-manifest-v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    generated = BoardGameModuleManifest.model_json_schema(by_alias=True)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/schemas/vrchat/board-game-module-manifest-v1.schema.json")
    assert schema["properties"] == generated["properties"]
    assert schema["required"] == generated["required"]
    assert schema["$defs"] == generated["$defs"]


def test_card_tile_and_dice_token_fixtures_validate_against_manifest_v1():
    fixture_path = (
        Path(__file__).parents[2]
        / "evaluation"
        / "vrchat"
        / "manifest-v1-fixtures.json"
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert payload["version"] == "board-game-module-manifest-fixtures-v1"
    assert {case["name"] for case in payload["cases"]} == {
        "card-centric",
        "tile-centric",
        "dice-token-centric",
    }
    for case in payload["cases"]:
        manifest = BoardGameModuleManifest.model_validate(case["manifest"])
        assert manifest.schema_version == "1.0"
        assert set(manifest.capabilities.model_dump(mode="json", by_alias=True)) == {
            capability.value for capability in CapabilityName
        }
