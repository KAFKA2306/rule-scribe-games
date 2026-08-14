from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.component_catalog import (
    Component,
    ComponentProperty,
    ComponentSet,
    EnumPropertyValue,
    IntegerPropertyValue,
    PropertyDefinition,
)
from app.models.component_catalog_view import (
    ComponentCatalogAvailabilityResponse,
    ComponentCatalogPageItem,
    ComponentCatalogPageResponse,
)
from app.routers import component_catalog_view
from app.services.component_catalog_view import summarize_property_evidence


def test_property_evidence_requires_all_current_ordinals_and_preserves_conflict():
    rows = [
        {"ordinal": 0, "value_type": "enum", "enum_value": "sun"},
        {"ordinal": 1, "value_type": "enum", "enum_value": "moon"},
    ]
    claims = [
        {
            "claim_id": "claim.0",
            "ordinal": 0,
            "lifecycle_status": "accepted",
            "normalized_payload": {"value": "sun"},
        },
        {
            "claim_id": "claim.1",
            "ordinal": 1,
            "lifecycle_status": "accepted",
            "normalized_payload": {"value": "moon"},
        },
    ]
    bindings = {
        "claim.0": [{"source_id": "source.rules", "relation": "supports"}],
        "claim.1": [{"source_id": "source.rules", "relation": "supports"}],
    }
    verified = summarize_property_evidence(rows, claims, bindings)
    assert verified.status == "verified"
    assert verified.source_ids == ["source.rules"]

    bindings["claim.1"].append({"source_id": "source.errata", "relation": "contradicts"})
    contested = summarize_property_evidence(rows, claims, bindings)
    assert contested.status == "contested"


def test_property_evidence_rejects_stale_candidate_and_partial_support():
    rows = [{"ordinal": 0, "value_type": "integer", "integer_value": 3}]
    claims = [
        {
            "claim_id": "claim.stale",
            "ordinal": 0,
            "lifecycle_status": "accepted",
            "normalized_payload": {"value": 2},
        },
        {
            "claim_id": "claim.candidate",
            "ordinal": 0,
            "lifecycle_status": "candidate",
            "normalized_payload": {"value": 3},
        },
    ]
    bindings = {
        "claim.stale": [{"source_id": "source.old", "relation": "supports"}],
        "claim.candidate": [{"source_id": "source.current", "relation": "supports"}],
    }
    summary = summarize_property_evidence(rows, claims, bindings)
    assert summary.status == "unknown"
    assert summary.source_ids == []


class FakeComponentCatalogViewService:
    async def get_availability(self, slug):
        if slug == "missing":
            return None
        if slug == "without-catalog":
            return ComponentCatalogAvailabilityResponse(
                status="not_available",
                game_id="game-1",
                slug=slug,
            )
        return ComponentCatalogAvailabilityResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rule_set_ids=["ruleset-1"],
        )

    async def get_page(self, slug, rule_set_id, **kwargs):
        if slug == "missing":
            return None
        component = Component(
            component_id="card.scout",
            ruleset_id=rule_set_id,
            component_set_id="cards",
            canonical_name="Scout",
            kind="card",
            properties=[
                ComponentProperty(
                    property_key="faction",
                    values=[EnumPropertyValue(value="sun")],
                ),
                ComponentProperty(
                    property_key="combat_value",
                    values=[IntegerPropertyValue(value=3)],
                ),
            ],
        )
        return ComponentCatalogPageResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rule_set_id=rule_set_id,
            component_sets=[
                ComponentSet(
                    component_set_id="cards",
                    ruleset_id=rule_set_id,
                    canonical_name="Cards",
                    kind="card",
                )
            ],
            property_definitions=[
                PropertyDefinition(
                    property_key="faction",
                    labels={"ja": "派閥"},
                    value_type="enum",
                    enum_values=["sun", "moon"],
                    filterable=True,
                ),
                PropertyDefinition(
                    property_key="combat_value",
                    labels={"ja": "戦力"},
                    value_type="integer",
                    sortable=True,
                ),
            ],
            items=[ComponentCatalogPageItem(component=component)],
            total=1,
            limit=kwargs.get("limit", 50),
            offset=kwargs.get("offset", 0),
        )


def _app():
    app = FastAPI()
    app.include_router(component_catalog_view.router, prefix="/api")
    app.dependency_overrides[component_catalog_view.get_component_catalog_view_service] = (
        lambda: FakeComponentCatalogViewService()
    )
    return app


def test_availability_is_lightweight_and_missing_catalog_is_explicit():
    client = TestClient(_app())
    available = client.get("/api/games/example/component-catalog-availability")
    unavailable = client.get("/api/games/without-catalog/component-catalog-availability")

    assert available.status_code == 200
    assert available.json()["rule_set_ids"] == ["ruleset-1"]
    assert unavailable.status_code == 200
    assert unavailable.json()["status"] == "not_available"
    assert unavailable.json()["rule_set_ids"] == []


def test_catalog_page_returns_full_generic_component_data_and_requires_ruleset():
    client = TestClient(_app())
    response = client.get(
        "/api/games/example/component-catalog",
        params={"rule_set_id": "ruleset-1", "limit": 50, "offset": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["component_sets"][0]["kind"] == "card"
    assert payload["property_definitions"][0]["property_key"] == "faction"
    assert payload["items"][0]["component"]["properties"][1]["values"][0]["value"] == 3

    missing_identity = client.get("/api/games/example/component-catalog")
    assert missing_identity.status_code == 422


def test_component_catalog_view_keeps_missing_game_distinct():
    client = TestClient(_app())
    response = client.get("/api/games/missing/component-catalog-availability")
    assert response.status_code == 404
