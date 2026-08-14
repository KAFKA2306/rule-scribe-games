import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.component_catalog import (
    Ability,
    Component,
    ComponentCatalog,
    ComponentDetailResponse,
    ComponentListItem,
    ComponentListResponse,
    ComponentProperty,
    ComponentSet,
    ComponentSetListResponse,
    ConceptRefPropertyValue,
    EnumPropertyValue,
    IntegerPropertyValue,
    NumberPropertyValue,
    PropertyDefinition,
    ComponentRefPropertyValue,
)
from app.routers import games


def test_card_catalog_supports_enum_numeric_and_concept_ref_properties():
    catalog = ComponentCatalog(
        ruleset_id="ruleset-yro",
        component_sets=[ComponentSet(component_set_id="adventurers", ruleset_id="ruleset-yro", canonical_name="Adventurers", kind="card")],
        property_definitions=[
            PropertyDefinition(property_key="faction", labels={"en": "Faction"}, value_type="enum", enum_values=["sun", "moon"], filterable=True),
            PropertyDefinition(property_key="combat_value", labels={"en": "Combat Value"}, value_type="integer", sortable=True),
            PropertyDefinition(property_key="profession", labels={"en": "Profession"}, value_type="concept_ref"),
        ],
        components=[
            Component(
                component_id="adventurer.scout",
                ruleset_id="ruleset-yro",
                component_set_id="adventurers",
                canonical_name="Scout",
                kind="card",
                properties=[
                    ComponentProperty(property_key="faction", values=[EnumPropertyValue(value="sun")]),
                    ComponentProperty(property_key="combat_value", values=[IntegerPropertyValue(value=3)]),
                    ComponentProperty(property_key="profession", values=[ConceptRefPropertyValue(value="profession.scout")]),
                ],
            )
        ],
    )

    assert catalog.components[0].kind.value == "card"
    assert catalog.components[0].properties[1].values[0].value == 3


def test_tile_catalog_uses_same_generic_contract_without_card_columns():
    catalog = ComponentCatalog(
        ruleset_id="ruleset-tile",
        component_sets=[ComponentSet(component_set_id="terrain.tiles", ruleset_id="ruleset-tile", canonical_name="Terrain Tiles", kind="tile")],
        property_definitions=[PropertyDefinition(property_key="movement_cost", value_type="number", sortable=True)],
        components=[
            Component(
                component_id="tile.forest",
                ruleset_id="ruleset-tile",
                component_set_id="terrain.tiles",
                canonical_name="Forest",
                kind="tile",
                properties=[ComponentProperty(property_key="movement_cost", values=[NumberPropertyValue(value=1.5)])],
            )
        ],
    )
    assert catalog.components[0].properties[0].values[0].value == 1.5


def test_dice_token_catalog_supports_component_ref_and_many_cardinality():
    catalog = ComponentCatalog(
        ruleset_id="ruleset-dice",
        component_sets=[
            ComponentSet(component_set_id="dice", ruleset_id="ruleset-dice", canonical_name="Dice", kind="die"),
            ComponentSet(component_set_id="tokens", ruleset_id="ruleset-dice", canonical_name="Tokens", kind="token"),
        ],
        property_definitions=[PropertyDefinition(property_key="spends", value_type="component_ref", cardinality="many")],
        components=[
            Component(component_id="token.energy", ruleset_id="ruleset-dice", component_set_id="tokens", canonical_name="Energy Token", kind="token"),
            Component(
                component_id="die.action",
                ruleset_id="ruleset-dice",
                component_set_id="dice",
                canonical_name="Action Die",
                kind="die",
                properties=[
                    ComponentProperty(
                        property_key="spends",
                        values=[ComponentRefPropertyValue(value="token.energy"), ComponentRefPropertyValue(value="token.energy")],
                    )
                ],
            ),
        ],
    )
    assert len(catalog.components[1].properties[0].values) == 2


def test_property_type_cardinality_and_enum_are_fail_closed():
    base = {
        "ruleset_id": "ruleset-test",
        "component_sets": [ComponentSet(component_set_id="cards", ruleset_id="ruleset-test", canonical_name="Cards", kind="card")],
        "property_definitions": [PropertyDefinition(property_key="rank", value_type="enum", enum_values=["low", "high"])],
    }

    with pytest.raises(ValidationError):
        ComponentCatalog(
            **base,
            components=[
                Component(
                    component_id="card.bad-enum",
                    ruleset_id="ruleset-test",
                    component_set_id="cards",
                    canonical_name="Bad Enum",
                    kind="card",
                    properties=[ComponentProperty(property_key="rank", values=[EnumPropertyValue(value="unknown")])],
                )
            ],
        )

    with pytest.raises(ValidationError):
        ComponentCatalog(
            **base,
            components=[
                Component(
                    component_id="card.bad-cardinality",
                    ruleset_id="ruleset-test",
                    component_set_id="cards",
                    canonical_name="Bad Cardinality",
                    kind="card",
                    properties=[ComponentProperty(property_key="rank", values=[EnumPropertyValue(value="low"), EnumPropertyValue(value="high")])],
                )
            ],
        )


def test_verified_component_field_requires_source_evidence():
    with pytest.raises(ValidationError):
        ComponentProperty(
            property_key="cost",
            values=[IntegerPropertyValue(value=2)],
            verification_status="verified",
            source_ids=[],
        )


def test_ability_keeps_printed_text_separate_from_rule_and_concept_links():
    ability = Ability(
        ability_id="ability.scout.draw",
        printed_text="Draw one card.",
        normalized_label="Draw",
        rule_ids=["rule.draw"],
        concept_ids=["player_action.draw"],
    )
    assert ability.printed_text == "Draw one card."
    assert ability.rule_ids == ["rule.draw"]


def test_same_component_identity_and_name_can_differ_by_ruleset():
    definition = [PropertyDefinition(property_key="cost", value_type="integer")]
    first = ComponentCatalog(
        ruleset_id="ruleset-physical",
        property_definitions=definition,
        components=[Component(component_id="card.scout", ruleset_id="ruleset-physical", canonical_name="Scout", kind="card", properties=[ComponentProperty(property_key="cost", values=[IntegerPropertyValue(value=2)])])],
    )
    second = ComponentCatalog(
        ruleset_id="ruleset-digital",
        property_definitions=definition,
        components=[Component(component_id="card.scout", ruleset_id="ruleset-digital", canonical_name="Scout", kind="card", properties=[ComponentProperty(property_key="cost", values=[IntegerPropertyValue(value=3)])])],
    )
    assert first.components[0].properties[0].values[0].value == 2
    assert second.components[0].properties[0].values[0].value == 3


class FakeComponentCatalogService:
    async def get_sets(self, slug, rule_set_id):
        if slug == "missing":
            return None
        return ComponentSetListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            component_sets=[ComponentSet(component_set_id="cards", ruleset_id=rule_set_id, canonical_name="Cards", kind="card")],
            property_definitions=[PropertyDefinition(property_key="cost", value_type="integer")],
        )

    async def list_components(self, slug, rule_set_id, **kwargs):
        if slug == "missing":
            return None
        return ComponentListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            components=[ComponentListItem(component_id="card.scout", component_set_id="cards", canonical_name="Scout", kind="card")],
            total=1,
            limit=kwargs.get("limit", 100),
            offset=kwargs.get("offset", 0),
        )

    async def get_component(self, slug, rule_set_id, component_id):
        if slug == "missing" or component_id == "missing":
            return None
        return ComponentDetailResponse(
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            component=Component(component_id=component_id, ruleset_id=rule_set_id, component_set_id="cards", canonical_name="Scout", kind="card"),
        )


def _app():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_component_catalog_service] = lambda: FakeComponentCatalogService()
    return app


def test_component_catalog_api_exposes_sets_list_and_detail():
    client = TestClient(_app())
    sets = client.get("/api/games/example/component-sets", params={"rule_set_id": "ruleset-1"})
    listing = client.get("/api/games/example/components", params={"rule_set_id": "ruleset-1", "kind": "card"})
    detail = client.get("/api/games/example/components/card.scout", params={"rule_set_id": "ruleset-1"})

    assert sets.status_code == 200
    assert sets.json()["component_sets"][0]["component_set_id"] == "cards"
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert detail.status_code == 200
    assert detail.json()["component"]["component_id"] == "card.scout"


def test_component_catalog_api_requires_explicit_ruleset_identity():
    client = TestClient(_app())
    response = client.get("/api/games/example/components")
    assert response.status_code == 422
