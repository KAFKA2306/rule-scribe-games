from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.models.component_ingestion import CompletenessState, ComponentSourceManifest
from app.services.component_ingestion import ComponentIngestionDryRun, ExistingComponentSnapshot

YRO_MANIFEST = Path("backend/data/component_ingestion/yro-bga-260725-1445.v1.yaml")
RULESET_ID = "00000000-0000-0000-0000-000000000178"
YRO_EVIDENCE_FIELDS = 6
YRO_SOURCE_LOCATORS = 4
FIXTURE_EVIDENCE_FIELDS = 4
FIXTURE_SUPPORTED_WITH_ONE_MISSING = 3


def _payload() -> dict:
    return {
        "schema_version": "1.0",
        "game_slug": "fixture-game",
        "ruleset": {"platform": "Fixture Platform", "revision_label": "r1", "language_code": "en"},
        "sources": [
            {
                "source_id": "source:fixture:1",
                "url": "https://example.com/fixture",
                "source_type": "publisher_component_list",
                "authority": "publisher",
                "revision_label": "r1",
                "observed_date": "2026-08-14",
                "extraction_method": "fixture",
            }
        ],
        "source_locators": [
            {
                "locator_id": "locator:set:cards",
                "source_id": "source:fixture:1",
                "section_heading": "Components",
            },
            {
                "locator_id": "locator:def:rank",
                "source_id": "source:fixture:1",
                "section_heading": "Card fields",
            },
            {
                "locator_id": "locator:component:alpha",
                "source_id": "source:fixture:1",
                "external_reference": "Alpha",
            },
            {
                "locator_id": "locator:component:alpha:rank",
                "source_id": "source:fixture:1",
                "external_reference": "Alpha rank",
            },
        ],
        "component_sets": [
            {
                "component_set_id": "cards",
                "canonical_name": "Cards",
                "kind": "card",
                "verification_status": "source_bound",
                "source_ids": ["source:fixture:1"],
            }
        ],
        "property_definitions": [
            {
                "property_key": "rank",
                "value_type": "integer",
                "cardinality": "one",
                "verification_status": "source_bound",
                "source_ids": ["source:fixture:1"],
            }
        ],
        "components": [
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
                        "values": [{"value_type": "integer", "value": 1}],
                        "verification_status": "source_bound",
                        "source_ids": ["source:fixture:1"],
                    }
                ],
            }
        ],
        "evidence_bindings": [
            {
                "binding_id": "binding:set:cards",
                "target": {"target_type": "component_set", "component_set_id": "cards"},
                "source_id": "source:fixture:1",
                "locator_id": "locator:set:cards",
                "relation": "supports",
            },
            {
                "binding_id": "binding:def:rank",
                "target": {"target_type": "property_definition", "property_key": "rank"},
                "source_id": "source:fixture:1",
                "locator_id": "locator:def:rank",
                "relation": "supports",
            },
            {
                "binding_id": "binding:component:alpha",
                "target": {"target_type": "component", "component_id": "card.alpha"},
                "source_id": "source:fixture:1",
                "locator_id": "locator:component:alpha",
                "relation": "supports",
            },
            {
                "binding_id": "binding:component:alpha:rank:0",
                "target": {
                    "target_type": "component_property",
                    "component_id": "card.alpha",
                    "property_key": "rank",
                    "ordinal": 0,
                },
                "source_id": "source:fixture:1",
                "locator_id": "locator:component:alpha:rank",
                "relation": "supports",
            },
        ],
        "completeness": "complete",
        "expected_count": 1,
        "unresolved_count": 0,
    }


def _manifest(payload: dict | None = None) -> ComponentSourceManifest:
    return ComponentSourceManifest.model_validate(payload or _payload())


def test_yro_manifest_is_source_bound_unknown_and_does_not_fabricate_cards():
    manifest = ComponentSourceManifest.model_validate(yaml.safe_load(YRO_MANIFEST.read_text(encoding="utf-8")))
    report = ComponentIngestionDryRun().run(manifest, resolved_ruleset_id=RULESET_ID)

    assert manifest.game_slug == "yro"
    assert manifest.completeness == CompletenessState.UNKNOWN
    assert manifest.expected_count is None
    assert manifest.components == []
    assert {item.component_set_id for item in manifest.component_sets} == {"adventurers", "quests"}
    assert len(manifest.source_locators) == YRO_SOURCE_LOCATORS
    assert report.blockers == []
    assert report.evidence_coverage.required_fields == YRO_EVIDENCE_FIELDS
    assert report.evidence_coverage.supported_fields == YRO_EVIDENCE_FIELDS
    assert report.evidence_coverage.ratio == 1.0


def test_ruleset_must_resolve_before_dry_run_can_promote():
    report = ComponentIngestionDryRun().run(_manifest(), resolved_ruleset_id=None)
    assert "RULESET_NOT_RESOLVED" in report.blockers


def test_unknown_property_definition_is_rejected_in_report():
    payload = _payload()
    payload["components"][0]["properties"][0]["property_key"] = "mystery"
    payload["evidence_bindings"][3]["target"]["property_key"] = "mystery"
    manifest = _manifest(payload)
    report = ComponentIngestionDryRun().run(manifest, resolved_ruleset_id=RULESET_ID)
    assert report.rejected_unknown_properties == ["card.alpha:mystery"]
    assert "UNKNOWN_PROPERTY_DEFINITION" in report.blockers


def test_property_type_mismatch_is_fail_closed():
    payload = _payload()
    payload["components"][0]["properties"][0]["values"] = [{"value_type": "text", "value": "one"}]
    manifest = _manifest(payload)
    report = ComponentIngestionDryRun().run(manifest, resolved_ruleset_id=RULESET_ID)
    assert "PROPERTY_TYPE_MISMATCH:card.alpha:rank" in report.blockers


def test_field_level_evidence_must_cover_source_bound_property():
    payload = _payload()
    payload["evidence_bindings"] = [
        item for item in payload["evidence_bindings"] if item["binding_id"] != "binding:component:alpha:rank:0"
    ]
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert "FIELD_EVIDENCE_COVERAGE_INCOMPLETE" in report.blockers
    assert report.evidence_coverage.required_fields == FIXTURE_EVIDENCE_FIELDS
    assert report.evidence_coverage.supported_fields == FIXTURE_SUPPORTED_WITH_ONE_MISSING


def test_source_url_does_not_implicitly_verify_a_field():
    payload = _payload()
    payload["sources"].append(
        {
            "source_id": "source:fixture:2",
            "url": "https://example.org/other",
            "source_type": "community_list",
            "authority": "community",
            "extraction_method": "fixture",
        }
    )
    payload["source_locators"].append(
        {
            "locator_id": "locator:other:alpha-rank",
            "source_id": "source:fixture:2",
            "section_heading": "Other",
        }
    )
    binding = next(item for item in payload["evidence_bindings"] if item["binding_id"] == "binding:component:alpha:rank:0")
    binding["source_id"] = "source:fixture:2"
    binding["locator_id"] = "locator:other:alpha-rank"
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert "FIELD_EVIDENCE_COVERAGE_INCOMPLETE" in report.blockers


def test_binding_requires_declared_locator_and_matching_source():
    payload = _payload()
    payload["evidence_bindings"][0]["locator_id"] = "locator:not-declared"
    with pytest.raises(ValidationError, match="references unknown locator"):
        _manifest(payload)

    payload = _payload()
    payload["sources"].append(
        {
            "source_id": "source:fixture:2",
            "url": "https://example.org/other",
            "source_type": "community_list",
            "authority": "community",
            "extraction_method": "fixture",
        }
    )
    payload["evidence_bindings"][0]["source_id"] = "source:fixture:2"
    with pytest.raises(ValidationError, match="source does not match locator source"):
        _manifest(payload)


def test_component_property_evidence_is_ordinal_specific():
    payload = _payload()
    payload["property_definitions"][0]["cardinality"] = "many"
    payload["components"][0]["properties"][0]["values"].append({"value_type": "integer", "value": 2})
    payload["completeness"] = "partial"
    payload["expected_count"] = 2
    payload["unresolved_count"] = 1
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert report.evidence_coverage.required_fields == FIXTURE_EVIDENCE_FIELDS + 1
    assert report.evidence_coverage.supported_fields == FIXTURE_EVIDENCE_FIELDS
    assert "FIELD_EVIDENCE_COVERAGE_INCOMPLETE" in report.blockers


def test_ability_printed_and_normalized_evidence_are_independent_targets():
    payload = _payload()
    payload["components"][0]["abilities"] = [
        {
            "ability_id": "ability.alpha",
            "printed_text": "Printed ability text",
            "normalized_label": "Normalized effect",
            "verification_status": "source_bound",
            "source_ids": ["source:fixture:1"],
        }
    ]
    payload["source_locators"].append(
        {
            "locator_id": "locator:ability:alpha",
            "source_id": "source:fixture:1",
            "external_reference": "Alpha ability",
        }
    )
    payload["evidence_bindings"].append(
        {
            "binding_id": "binding:ability:alpha:printed",
            "target": {"target_type": "ability_printed_text", "ability_id": "ability.alpha"},
            "source_id": "source:fixture:1",
            "locator_id": "locator:ability:alpha",
            "relation": "supports",
        }
    )
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert report.evidence_coverage.required_fields == FIXTURE_EVIDENCE_FIELDS + 2
    assert report.evidence_coverage.supported_fields == FIXTURE_EVIDENCE_FIELDS + 1
    assert "FIELD_EVIDENCE_COVERAGE_INCOMPLETE" in report.blockers


def test_structured_target_must_resolve_to_manifest_entity():
    payload = _payload()
    payload["evidence_bindings"][0]["target"]["component_set_id"] = "missing"
    with pytest.raises(ValidationError, match="unknown component set"):
        _manifest(payload)

    payload = _payload()
    payload["evidence_bindings"][3]["target"]["ordinal"] = 1
    with pytest.raises(ValidationError, match="ordinal is out of range"):
        _manifest(payload)


def test_duplicate_stable_identity_candidate_is_reported_even_with_distinct_ids():
    payload = _payload()
    duplicate = deepcopy(payload["components"][0])
    duplicate["component_id"] = "card.alpha-alt"
    duplicate["canonical_name"] = "Ａｌｐｈａ"
    payload["components"].append(duplicate)
    payload["completeness"] = "partial"
    payload["expected_count"] = 3
    payload["unresolved_count"] = 1
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert ["card.alpha", "card.alpha-alt"] in report.duplicate_candidates
    assert "DUPLICATE_COMPONENT_IDENTITY_CANDIDATE" in report.blockers


def test_duplicate_component_id_is_invalid_manifest():
    payload = _payload()
    payload["components"].append(deepcopy(payload["components"][0]))
    payload["expected_count"] = 2
    with pytest.raises(ValidationError, match="duplicate component_id"):
        _manifest(payload)


def test_complete_requires_source_backed_expected_count_equal_to_observed():
    payload = _payload()
    payload["expected_count"] = 2
    with pytest.raises(ValidationError, match="expected_count must equal observed"):
        _manifest(payload)


def test_unknown_completeness_cannot_claim_expected_count():
    payload = _payload()
    payload["completeness"] = "unknown"
    with pytest.raises(ValidationError, match="unknown completeness cannot claim"):
        _manifest(payload)


def test_partial_source_is_never_promoted_to_complete_by_dry_run():
    payload = _payload()
    payload["completeness"] = "partial"
    payload["expected_count"] = 2
    payload["unresolved_count"] = 1
    report = ComponentIngestionDryRun().run(_manifest(payload), resolved_ruleset_id=RULESET_ID)
    assert report.completeness == CompletenessState.PARTIAL


def test_identical_second_run_is_unchanged_not_duplicate_create():
    manifest = _manifest()
    existing = ExistingComponentSnapshot(
        ruleset_id=RULESET_ID,
        component_sets=manifest.component_sets,
        property_definitions=[definition.model_dump(mode="json") for definition in manifest.property_definitions],
        components=manifest.components,
    )
    report = ComponentIngestionDryRun().run(
        manifest,
        resolved_ruleset_id=RULESET_ID,
        existing=existing,
    )
    assert report.creates == []
    assert report.updates == []
    assert report.unchanged == ["card.alpha"]


def test_same_game_different_ruleset_snapshot_is_not_merged():
    manifest = _manifest()
    existing = ExistingComponentSnapshot(
        ruleset_id="00000000-0000-0000-0000-000000000999",
        components=manifest.components,
    )
    report = ComponentIngestionDryRun().run(
        manifest,
        resolved_ruleset_id=RULESET_ID,
        existing=existing,
    )
    assert "EXISTING_SNAPSHOT_RULESET_MISMATCH" in report.blockers


def test_manifest_cannot_reference_undeclared_source():
    payload = _payload()
    payload["component_sets"][0]["source_ids"] = ["source:not-declared"]
    with pytest.raises(ValidationError, match="references unknown sources"):
        _manifest(payload)
