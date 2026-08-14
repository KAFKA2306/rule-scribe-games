from copy import deepcopy
from pathlib import Path

import yaml

from app.models.component_ingestion import ComponentSourceManifest
from app.services.component_ingestion_repository import ComponentIngestionPlanBuilder, ResolvedRuleSet

YRO_MANIFEST = Path("backend/data/component_ingestion/yro-bga-260725-1445.v1.yaml")
RULESET = ResolvedRuleSet(
    game_id="00000000-0000-0000-0000-000000000001",
    ruleset_id="00000000-0000-0000-0000-000000000178",
    game_slug="yro",
)
YRO_SOURCE_COUNT = 2
YRO_LOCATOR_COUNT = 4
YRO_COMPONENT_SET_COUNT = 2
YRO_PROPERTY_DEFINITION_COUNT = 4
YRO_INGESTION_CLAIM_COUNT = 6
FIXTURE_PROPERTY_VALUE_COUNT = 2
FIXTURE_INGESTION_CLAIM_COUNT = 7


def _yro_manifest() -> ComponentSourceManifest:
    return ComponentSourceManifest.model_validate(yaml.safe_load(YRO_MANIFEST.read_text(encoding="utf-8")))


def _component_manifest() -> ComponentSourceManifest:
    payload = yaml.safe_load(YRO_MANIFEST.read_text(encoding="utf-8"))
    payload["game_slug"] = "fixture-game"
    payload["ruleset"] = {"ruleset_id": RULESET.ruleset_id}
    payload["sources"] = [
        {
            "source_id": "source:fixture:1",
            "url": "https://example.com/components",
            "source_type": "publisher_component_list",
            "authority": "publisher",
            "observed_date": "2026-08-14",
            "extraction_method": "fixture",
        }
    ]
    payload["source_locators"] = [
        {
            "locator_id": "locator:fixture:component",
            "source_id": "source:fixture:1",
            "section_heading": "Components",
        },
        {
            "locator_id": "locator:fixture:ability",
            "source_id": "source:fixture:1",
            "section_heading": "Ability",
        },
    ]
    payload["component_sets"] = [
        {
            "component_set_id": "cards",
            "canonical_name": "Cards",
            "kind": "card",
            "verification_status": "source_bound",
            "source_ids": ["source:fixture:1"],
        }
    ]
    payload["property_definitions"] = [
        {
            "property_key": "rank",
            "value_type": "integer",
            "cardinality": "many",
            "verification_status": "source_bound",
            "source_ids": ["source:fixture:1"],
        }
    ]
    payload["components"] = [
        {
            "component_id": "card.alpha",
            "component_set_id": "cards",
            "canonical_name": "Alpha",
            "kind": "card",
            "quantity": 1,
            "verification_status": "source_bound",
            "source_ids": ["source:fixture:1"],
            "properties": [
                {
                    "property_key": "rank",
                    "values": [
                        {"value_type": "integer", "value": 1},
                        {"value_type": "integer", "value": 2},
                    ],
                    "verification_status": "source_bound",
                    "source_ids": ["source:fixture:1"],
                }
            ],
            "abilities": [
                {
                    "ability_id": "ability.alpha",
                    "printed_text": "Printed text",
                    "normalized_label": "Normalized effect",
                    "verification_status": "source_bound",
                    "source_ids": ["source:fixture:1"],
                }
            ],
        }
    ]
    payload["evidence_bindings"] = []
    targets = [
        ("set", {"target_type": "component_set", "component_set_id": "cards"}),
        ("definition", {"target_type": "property_definition", "property_key": "rank"}),
        ("component", {"target_type": "component", "component_id": "card.alpha"}),
        (
            "rank-0",
            {
                "target_type": "component_property",
                "component_id": "card.alpha",
                "property_key": "rank",
                "ordinal": 0,
            },
        ),
        (
            "rank-1",
            {
                "target_type": "component_property",
                "component_id": "card.alpha",
                "property_key": "rank",
                "ordinal": 1,
            },
        ),
        ("printed", {"target_type": "ability_printed_text", "ability_id": "ability.alpha"}),
        ("normalized", {"target_type": "ability_normalized", "ability_id": "ability.alpha"}),
    ]
    for name, target in targets:
        locator_id = "locator:fixture:ability" if name in {"printed", "normalized"} else "locator:fixture:component"
        payload["evidence_bindings"].append(
            {
                "binding_id": f"binding:fixture:{name}",
                "target": target,
                "source_id": "source:fixture:1",
                "locator_id": locator_id,
                "relation": "supports",
            }
        )
    payload["completeness"] = "complete"
    payload["expected_count"] = 1
    payload["unresolved_count"] = 0
    return ComponentSourceManifest.model_validate(payload)


def test_yro_plan_preserves_zero_component_fail_closed_state():
    plan = ComponentIngestionPlanBuilder().build(_yro_manifest(), RULESET)
    assert len(plan["sources"]) == YRO_SOURCE_COUNT
    assert len(plan["source_locators"]) == YRO_LOCATOR_COUNT
    assert len(plan["component_sets"]) == YRO_COMPONENT_SET_COUNT
    assert len(plan["property_definitions"]) == YRO_PROPERTY_DEFINITION_COUNT
    assert plan["components"] == []
    assert plan["component_properties"] == []
    assert len(plan["claims"]) == YRO_INGESTION_CLAIM_COUNT
    assert len(plan["evidence_bindings"]) == YRO_INGESTION_CLAIM_COUNT
    assert plan["catalog_metadata"]["component_ingestion"]["completeness"] == "unknown"


def test_plan_flattens_multi_value_property_and_two_ability_claim_targets():
    resolved = RULESET.model_copy(update={"game_slug": "fixture-game"})
    plan = ComponentIngestionPlanBuilder().build(_component_manifest(), resolved)
    assert [row["ordinal"] for row in plan["component_properties"]] == list(range(FIXTURE_PROPERTY_VALUE_COUNT))
    assert [row["integer_value"] for row in plan["component_properties"]] == [1, 2]
    assert len(plan["component_abilities"]) == 1
    target_types = {row["target_type"] for row in plan["claims"]}
    assert {"component", "component_set", "property_definition", "component_property"}.issubset(target_types)
    assert "ability_printed_text" in target_types
    assert "ability_normalized" in target_types
    assert len(plan["claims"]) == FIXTURE_INGESTION_CLAIM_COUNT


def test_claim_and_binding_ids_are_deterministic_across_reruns():
    manifest = _component_manifest()
    builder = ComponentIngestionPlanBuilder()
    resolved = RULESET.model_copy(update={"game_slug": "fixture-game"})
    first = builder.build(manifest, resolved)
    second = builder.build(deepcopy(manifest), resolved)
    assert [row["claim_id"] for row in first["claims"]] == [row["claim_id"] for row in second["claims"]]
    assert [row["binding_id"] for row in first["evidence_bindings"]] == [
        row["binding_id"] for row in second["evidence_bindings"]
    ]


def test_manifest_binding_id_is_kept_in_generator_provenance():
    plan = ComponentIngestionPlanBuilder().build(_yro_manifest(), RULESET)
    binding = plan["evidence_bindings"][0]
    assert binding["manifest_binding_id"].startswith("yro:")
    assert binding["generator_provenance"]["manifest_binding_id"] == binding["manifest_binding_id"]
