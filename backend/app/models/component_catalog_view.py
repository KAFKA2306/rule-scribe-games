from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.component_catalog import Component, ComponentSet, PropertyDefinition

COMPONENT_CATALOG_VIEW_SCHEMA_VERSION = "1.0"


class ComponentCatalogViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ComponentCatalogAvailabilityResponse(ComponentCatalogViewModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_VIEW_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    rule_set_ids: list[str] = Field(default_factory=list)


class FieldEvidenceSummary(ComponentCatalogViewModel):
    status: Literal["verified", "unknown", "contested"] = "unknown"
    claim_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class AbilityEvidenceSummary(ComponentCatalogViewModel):
    printed_text: FieldEvidenceSummary = Field(default_factory=FieldEvidenceSummary)
    normalized: FieldEvidenceSummary = Field(default_factory=FieldEvidenceSummary)


class ComponentCatalogPageItem(ComponentCatalogViewModel):
    component: Component
    property_evidence: dict[str, FieldEvidenceSummary] = Field(default_factory=dict)
    ability_evidence: dict[str, AbilityEvidenceSummary] = Field(default_factory=dict)


class ComponentCatalogPageResponse(ComponentCatalogViewModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_VIEW_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    rule_set_id: str
    component_sets: list[ComponentSet] = Field(default_factory=list)
    property_definitions: list[PropertyDefinition] = Field(default_factory=list)
    items: list[ComponentCatalogPageItem] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
