from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

COMPONENT_CATALOG_SCHEMA_VERSION = "1.0"
STABLE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:-]{2,127}$"
PROPERTY_KEY_PATTERN = r"^[a-z][a-z0-9_.:-]{1,127}$"


class ComponentKind(StrEnum):
    CARD = "card"
    TILE = "tile"
    TOKEN = "token"
    DIE = "die"
    BOARD = "board"
    FIGURE = "figure"
    SHEET = "sheet"
    ROLE = "role"
    MARKER = "marker"
    TRACK = "track"
    OTHER = "other"


class PropertyValueType(StrEnum):
    TEXT = "text"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    CONCEPT_REF = "concept_ref"
    COMPONENT_REF = "component_ref"


class PropertyCardinality(StrEnum):
    ONE = "one"
    MANY = "many"


class ComponentVerificationStatus(StrEnum):
    UNKNOWN = "unknown"
    SOURCE_BOUND = "source_bound"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ComponentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _require_sources_for_verified(status: ComponentVerificationStatus, source_ids: list[str]) -> None:
    if status in {ComponentVerificationStatus.SOURCE_BOUND, ComponentVerificationStatus.VERIFIED} and not source_ids:
        raise ValueError("source-bound or verified component data requires source_ids")


class TextPropertyValue(ComponentModel):
    value_type: Literal["text"] = "text"
    value: str = Field(min_length=1)


class IntegerPropertyValue(ComponentModel):
    value_type: Literal["integer"] = "integer"
    value: int


class NumberPropertyValue(ComponentModel):
    value_type: Literal["number"] = "number"
    value: float


class BooleanPropertyValue(ComponentModel):
    value_type: Literal["boolean"] = "boolean"
    value: bool


class EnumPropertyValue(ComponentModel):
    value_type: Literal["enum"] = "enum"
    value: str = Field(min_length=1)


class ConceptRefPropertyValue(ComponentModel):
    value_type: Literal["concept_ref"] = "concept_ref"
    value: str = Field(pattern=STABLE_ID_PATTERN)


class ComponentRefPropertyValue(ComponentModel):
    value_type: Literal["component_ref"] = "component_ref"
    value: str = Field(pattern=STABLE_ID_PATTERN)


PropertyValue = Annotated[
    TextPropertyValue
    | IntegerPropertyValue
    | NumberPropertyValue
    | BooleanPropertyValue
    | EnumPropertyValue
    | ConceptRefPropertyValue
    | ComponentRefPropertyValue,
    Field(discriminator="value_type"),
]


class PropertyDefinition(ComponentModel):
    property_key: str = Field(pattern=PROPERTY_KEY_PATTERN)
    labels: dict[str, str] = Field(default_factory=dict)
    value_type: PropertyValueType
    cardinality: PropertyCardinality = PropertyCardinality.ONE
    unit: str | None = None
    enum_values: list[str] = Field(default_factory=list)
    filterable: bool = False
    sortable: bool = False
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_definition(self):
        if self.value_type == PropertyValueType.ENUM:
            if not self.enum_values:
                raise ValueError("enum property definitions require enum_values")
            if len(set(self.enum_values)) != len(self.enum_values):
                raise ValueError("enum_values must be unique")
        elif self.enum_values:
            raise ValueError("enum_values are only valid for enum definitions")
        _require_sources_for_verified(self.verification_status, self.source_ids)
        return self


class ComponentProperty(ComponentModel):
    property_key: str = Field(pattern=PROPERTY_KEY_PATTERN)
    values: list[PropertyValue] = Field(min_length=1)
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_values(self):
        value_types = {value.value_type for value in self.values}
        if len(value_types) != 1:
            raise ValueError("all values for one property must use the same value_type")
        _require_sources_for_verified(self.verification_status, self.source_ids)
        return self


class ComponentSet(ComponentModel):
    component_set_id: str = Field(pattern=STABLE_ID_PATTERN)
    ruleset_id: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)
    kind: ComponentKind | None = None
    parent_component_set_id: str | None = Field(default=None, pattern=STABLE_ID_PATTERN)
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_set(self):
        if self.parent_component_set_id == self.component_set_id:
            raise ValueError("component set cannot be its own parent")
        _require_sources_for_verified(self.verification_status, self.source_ids)
        return self


class Ability(ComponentModel):
    ability_id: str = Field(pattern=STABLE_ID_PATTERN)
    printed_text: str | None = None
    normalized_label: str | None = None
    rule_ids: list[str] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ability(self):
        if not self.printed_text and not self.normalized_label:
            raise ValueError("ability requires printed_text or normalized_label")
        _require_sources_for_verified(self.verification_status, self.source_ids)
        return self


class Component(ComponentModel):
    component_id: str = Field(pattern=STABLE_ID_PATTERN)
    ruleset_id: str = Field(min_length=1)
    component_set_id: str | None = Field(default=None, pattern=STABLE_ID_PATTERN)
    canonical_name: str = Field(min_length=1)
    kind: ComponentKind
    quantity: int | None = Field(default=None, ge=1)
    properties: list[ComponentProperty] = Field(default_factory=list)
    abilities: list[Ability] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_component(self):
        keys = [prop.property_key for prop in self.properties]
        if len(keys) != len(set(keys)):
            raise ValueError("component properties must have unique property_key values")
        ability_ids = [ability.ability_id for ability in self.abilities]
        if len(ability_ids) != len(set(ability_ids)):
            raise ValueError("component ability_id values must be unique")
        _require_sources_for_verified(self.verification_status, self.source_ids)
        return self


class ComponentCatalog(ComponentModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_SCHEMA_VERSION
    ruleset_id: str = Field(min_length=1)
    component_sets: list[ComponentSet] = Field(default_factory=list)
    property_definitions: list[PropertyDefinition] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_catalog(self):
        set_ids = {item.component_set_id for item in self.component_sets}
        if len(set_ids) != len(self.component_sets):
            raise ValueError("duplicate component_set_id")
        definition_by_key = {item.property_key: item for item in self.property_definitions}
        if len(definition_by_key) != len(self.property_definitions):
            raise ValueError("duplicate property_key")
        component_ids = {item.component_id for item in self.components}
        if len(component_ids) != len(self.components):
            raise ValueError("duplicate component_id within ruleset")

        for item in self.component_sets:
            if item.ruleset_id != self.ruleset_id:
                raise ValueError("component set belongs to a different ruleset")
            if item.parent_component_set_id and item.parent_component_set_id not in set_ids:
                raise ValueError("parent component set is not present in catalog")

        for component in self.components:
            if component.ruleset_id != self.ruleset_id:
                raise ValueError("component belongs to a different ruleset")
            if component.component_set_id and component.component_set_id not in set_ids:
                raise ValueError("component references an unknown component set")
            for prop in component.properties:
                definition = definition_by_key.get(prop.property_key)
                if definition is None:
                    raise ValueError(f"unknown property definition: {prop.property_key}")
                if definition.cardinality == PropertyCardinality.ONE and len(prop.values) != 1:
                    raise ValueError(f"property {prop.property_key} requires cardinality one")
                actual_type = prop.values[0].value_type
                if actual_type != definition.value_type.value:
                    raise ValueError(f"property {prop.property_key} has the wrong value type")
                if definition.value_type == PropertyValueType.ENUM:
                    invalid = [value.value for value in prop.values if value.value not in definition.enum_values]
                    if invalid:
                        raise ValueError(f"property {prop.property_key} contains an unknown enum value")
                if definition.value_type == PropertyValueType.COMPONENT_REF:
                    unknown = [value.value for value in prop.values if value.value not in component_ids]
                    if unknown:
                        raise ValueError(f"property {prop.property_key} references an unknown component")
        return self


class ComponentSetListResponse(ComponentModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    ruleset_id: str
    component_sets: list[ComponentSet] = Field(default_factory=list)
    property_definitions: list[PropertyDefinition] = Field(default_factory=list)


class ComponentListItem(ComponentModel):
    component_id: str
    component_set_id: str | None = None
    canonical_name: str
    kind: ComponentKind
    quantity: int | None = None
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN


class ComponentListResponse(ComponentModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    ruleset_id: str
    components: list[ComponentListItem] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ComponentDetailResponse(ComponentModel):
    schema_version: Literal["1.0"] = COMPONENT_CATALOG_SCHEMA_VERSION
    status: Literal["available"] = "available"
    game_id: str
    slug: str
    ruleset_id: str
    component: Component
