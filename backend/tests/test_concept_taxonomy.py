import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.concept_taxonomy import (
    Concept,
    ConceptDetailResponse,
    ConceptGameBacklink,
    ConceptLabel,
    ConceptRelation,
    GameConceptReference,
    GameConceptsReadResponse,
    GameGlossaryReadResponse,
    GlossaryEntry,
    RuleConceptReference,
    resolve_legacy_terms,
    validate_relation_set,
)
from app.routers import games


def concept(concept_id: str, labels: list[ConceptLabel], **kwargs) -> Concept:
    return Concept(concept_id=concept_id, concept_type="mechanic", labels=labels, **kwargs)


def test_stable_id_is_independent_from_label_rename():
    before = concept(
        "fixture.mechanic.risk-choice",
        [ConceptLabel(language_code="en", label_type="pref", label="Risk Choice")],
    )
    after = concept(
        "fixture.mechanic.risk-choice",
        [ConceptLabel(language_code="en", label_type="pref", label="Pressing Risk")],
    )
    assert before.concept_id == after.concept_id
    assert before.labels[0].label != after.labels[0].label


def test_multilingual_pref_and_alt_labels_normalize_deterministically():
    item = concept(
        "fixture.mechanic.choice",
        [
            ConceptLabel(language_code="en", label_type="pref", label="Risk Choice"),
            ConceptLabel(language_code="en", label_type="alt", label="Press Risk"),
            ConceptLabel(language_code="ja", label_type="pref", label="リスク選択"),
        ],
    )
    assert item.labels[0].normalized_label == "risk choice"
    assert item.labels[1].normalized_label == "press risk"
    assert ConceptLabel(language_code="en", label_type="alt", label="risk-choice").normalized_label == "risk choice"


def test_redundant_alias_after_normalization_is_rejected():
    with pytest.raises(ValidationError):
        concept(
            "fixture.mechanic.choice",
            [
                ConceptLabel(language_code="en", label_type="pref", label="Risk Choice"),
                ConceptLabel(language_code="en", label_type="alt", label="risk-choice"),
            ],
        )


def test_duplicate_preferred_label_per_language_is_rejected():
    with pytest.raises(ValidationError):
        concept(
            "fixture.mechanic.choice",
            [
                ConceptLabel(language_code="en", label_type="pref", label="Choice One"),
                ConceptLabel(language_code="EN", label_type="pref", label="Choice Two"),
            ],
        )


def test_merged_concept_requires_redirect_and_cannot_redirect_to_self():
    merged = concept(
        "fixture.mechanic.old",
        [ConceptLabel(language_code="en", label_type="pref", label="Old")],
        lifecycle_status="merged",
        replaced_by_concept_id="fixture.mechanic.new",
    )
    assert merged.replaced_by_concept_id == "fixture.mechanic.new"

    with pytest.raises(ValidationError):
        concept(
            "fixture.mechanic.old",
            [ConceptLabel(language_code="en", label_type="pref", label="Old")],
            lifecycle_status="merged",
            replaced_by_concept_id="fixture.mechanic.old",
        )


def test_skos_related_cannot_overlap_hierarchical_pair():
    broader = concept(
        "fixture.mechanic.broad",
        [ConceptLabel(language_code="en", label_type="pref", label="Broad")],
    )
    narrow = concept(
        "fixture.mechanic.narrow",
        [ConceptLabel(language_code="en", label_type="pref", label="Narrow")],
    )
    with pytest.raises(ValueError):
        validate_relation_set(
            [broader, narrow],
            [
                ConceptRelation(from_concept_id=narrow.concept_id, to_concept_id=broader.concept_id, relation_type="broader"),
                ConceptRelation(from_concept_id=broader.concept_id, to_concept_id=narrow.concept_id, relation_type="related"),
            ],
        )


def test_legacy_mapping_is_fail_closed_for_ambiguous_and_unknown_labels():
    one = concept(
        "fixture.mechanic.one",
        [ConceptLabel(language_code="en", label_type="pref", label="Shared Term")],
    )
    two = Concept(
        concept_id="fixture.action.two",
        concept_type="player_action",
        labels=[ConceptLabel(language_code="en", label_type="alt", label="shared_term")],
    )
    unique = concept(
        "fixture.mechanic.unique",
        [ConceptLabel(language_code="en", label_type="pref", label="Unique Term")],
    )
    resolution = resolve_legacy_terms(["shared-term", "Unique Term", "Unknown"], [one, two, unique], language_code="en")
    assert resolution.resolved == {"Unique Term": "fixture.mechanic.unique"}
    assert resolution.ambiguous["shared-term"] == ["fixture.action.two", "fixture.mechanic.one"]
    assert resolution.unresolved == ["Unknown"]


def test_global_definition_and_game_rule_reference_remain_separate():
    detail = ConceptDetailResponse(
        concept=Concept(
            concept_id="fixture.mechanic.trick",
            concept_type="mechanic",
            definition="A generic play unit shared by multiple games.",
            labels=[ConceptLabel(language_code="ja", label_type="pref", label="トリック")],
        ),
        game_backlinks=[
            ConceptGameBacklink(
                game_id="game-1",
                slug="example",
                usage_roles=["glossary"],
                rule_references=[
                    RuleConceptReference(
                        rule_id="example.rule.turn.1",
                        node_type="turn",
                        normalized_statement="このゲーム固有のトリック進行。",
                        reference_kind="mentions",
                    )
                ],
            )
        ],
    )
    assert detail.concept.definition != detail.game_backlinks[0].rule_references[0].normalized_statement


def test_versioned_structural_fixtures_validate_without_seeding_production_taxonomy():
    path = Path(__file__).parents[2] / "evaluation" / "taxonomy" / "concept-taxonomy-v1-fixtures.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == "concept-taxonomy-fixtures-v1"
    assert "do not seed" in payload["note"].lower()
    concepts = [Concept.model_validate(case) for case in payload["cases"]]
    assert {item.concept_type.value for item in concepts} == {"mechanic", "player_action"}


def test_migration_declares_rule_node_concept_backlinks():
    path = Path(__file__).parents[1] / "app" / "db" / "migrations" / "011_concept_taxonomy.sql"
    sql = path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.rule_node_concepts" in sql
    assert "FOREIGN KEY (rule_set_id, rule_id)" in sql
    assert "concept_labels_unique_normalized_per_language" in sql


class FakeConceptService:
    async def get_concept(self, concept_id: str):
        if concept_id == "missing":
            return None
        return ConceptDetailResponse(
            concept=Concept(
                concept_id=concept_id,
                concept_type="mechanic",
                definition="Generic definition",
                labels=[ConceptLabel(language_code="ja", label_type="pref", label="トリック")],
            ),
            game_backlinks=[ConceptGameBacklink(game_id="game-1", slug="example", usage_roles=["glossary"])],
        )

    async def get_by_game_slug(self, slug: str):
        if slug == "missing":
            return None
        return GameConceptsReadResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            concepts=[
                GameConceptReference(
                    concept_id="fixture.mechanic.trick",
                    concept_type="mechanic",
                    usage_role="glossary",
                    preferred_labels={"ja": "トリック"},
                    definition="Generic definition",
                )
            ],
        )

    async def get_glossary_by_game_slug(self, slug: str, language_code: str = "ja"):
        if slug == "missing":
            return None
        return GameGlossaryReadResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            language_code=language_code,
            entries=[
                GlossaryEntry(
                    concept_id="fixture.mechanic.trick",
                    label="トリック",
                    definition="Generic definition",
                    rule_references=[
                        RuleConceptReference(
                            rule_id="example.rule.turn.1",
                            node_type="turn",
                            normalized_statement="Game-specific rule reference",
                            reference_kind="mentions",
                        )
                    ],
                )
            ],
        )


def app():
    instance = FastAPI()
    instance.include_router(games.router, prefix="/api")
    instance.dependency_overrides[games.get_concept_taxonomy_service] = lambda: FakeConceptService()
    return instance


def test_game_concepts_api_uses_stable_concept_ids():
    response = TestClient(app()).get("/api/games/example/concepts")
    assert response.status_code == 200
    assert response.json()["concepts"][0]["concept_id"] == "fixture.mechanic.trick"


def test_linked_glossary_api_exposes_concept_and_rule_reference():
    response = TestClient(app()).get("/api/games/example/glossary?language_code=ja")
    assert response.status_code == 200
    payload = response.json()
    assert payload["entries"][0]["concept_id"] == "fixture.mechanic.trick"
    assert payload["entries"][0]["rule_references"][0]["rule_id"] == "example.rule.turn.1"


def test_concept_detail_api_exposes_backlinks_and_missing_boundary():
    client = TestClient(app())
    response = client.get("/api/concepts/fixture.mechanic.trick")
    assert response.status_code == 200
    assert response.json()["game_backlinks"][0]["slug"] == "example"
    assert client.get("/api/concepts/missing").status_code == 404
