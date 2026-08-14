from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.component_catalog import (
    Ability,
    ComponentKind,
    ComponentProperty,
    ComponentVerificationStatus,
    PropertyDefinition,
    STABLE_ID_PATTERN,
)

COMPONENT_SOURCE_MANIFEST_SCHEMA_VERSION = "1.0"


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompletenessState(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class SourceAuthority(StrEnum):
    PUBLISHER = "publisher"
    PLATFORM = "platform"
    COMMUNITY = "community"
    REPLAY = "replay"
    LOG = "log"
    OTHER = "other"


class EvidenceRelation(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"
    UNRESOLVED = "unresolved"


class RuleSetSelector(ManifestModel):
    ruleset_id: str | None = None
    platform: str | None = None
    revision_label: str | None = None
    language_code: str | None = None
    edition_label: str | None = None

    @model_validator(mode="after")
    def require_exact_selector(self):
        if self.ruleset_id:
            return self
        if not self.platform or not self.revision_label:
            raise ValueError("ruleset selector requires ruleset_id or platform + revision_label")
        return self


class ComponentManifestSource(ManifestModel):
    source_id: str = Field(pattern=STABLE_ID_PATTERN)
    url: HttpUrl
    source_type: str = Field(min_length=1)
    authority: SourceAuthority
    revision_label: str | None = None
    observed_date: str | None = None
    extraction_method: str = Field(min_length=1)


class ManifestComponentSet(ManifestModel):
    component_set_id: str = Field(pattern=STABLE_ID_PATTERN)
    canonical_name: str = Field(min_length=1)
    kind: ComponentKind | None = None
    parent_component_set_id: str | None = Field(default=None, pattern=STABLE_ID_PATTERN)
    verification_status: ComponentVerificationStatus = ComponentVerificationStatus.UNKNOWN
    source_ids: list[str] = Field(default_factory=list)


class ManifestComponent(ManifestModel):
    component_id: str = Field(pattern=STABLE_ID_PATTERN)
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


class ManifestEvidenceBinding(ManifestModel):
    binding_id: str = Field(pattern=STABLE_ID_PATTERN)
    target_path: str = Field(min_length=1)
    source_id: str = Field(pattern=STABLE_ID_PATTERN)
    locator_id: str = Field(pattern=STABLE_ID_PATTERN)
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS


class ComponentSourceManifest(ManifestModel):
    schema_version: Literal["1.0"] = COMPONENT_SOURCE_MANIFEST_SCHEMA_VERSION
    game_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,127}$")
    ruleset: RuleSetSelector
    sources: list[ComponentManifestSource] = Field(min_length=1)
    component_sets: list[ManifestComponentSet] = Field(default_factory=list)
    property_definitions: list[PropertyDefinition] = Field(default_factory=list)
    components: list[ManifestComponent] = Field(default_factory=list)
    evidence_bindings: list[ManifestEvidenceBinding] = Field(default_factory=list)
    completeness: CompletenessState
    expected_count: int | None = Field(default=None, ge=0)
    unresolved_count: int | None = Field(default=None, ge=0)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self):  # noqa: PLR0912 - fail-closed contract is intentionally explicit
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("duplicate source_id")
        known_sources = set(source_ids)

        set_ids = [item.component_set_id for item in self.component_sets]
        if len(set_ids) != len(set(set_ids)):
            raise ValueError("duplicate component_set_id")
        known_sets = set(set_ids)
        for item in self.component_sets:
            if item.parent_component_set_id and item.parent_component_set_id not in known_sets:
                raise ValueError("parent component set is not present in manifest")
            self._require_known_sources(item.source_ids, known_sources, f"component_set:{item.component_set_id}")

        definition_keys = [item.property_key for item in self.property_definitions]
        if len(definition_keys) != len(set(definition_keys)):
            raise ValueError("duplicate property_key")
        for definition in self.property_definitions:
            self._require_known_sources(definition.source_ids, known_sources, f"property_definition:{definition.property_key}")

        component_ids = [item.component_id for item in self.components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("duplicate component_id")
        for component in self.components:
            if component.component_set_id and component.component_set_id not in known_sets:
                raise ValueError(f"component {component.component_id} references unknown component set")
            self._require_known_sources(component.source_ids, known_sources, f"component:{component.component_id}")
            for prop in component.properties:
                self._require_known_sources(
                    prop.source_ids,
                    known_sources,
                    f"component:{component.component_id}:property:{prop.property_key}",
                )
            for ability in component.abilities:
                self._require_known_sources(
                    ability.source_ids,
                    known_sources,
                    f"component:{component.component_id}:ability:{ability.ability_id}",
                )

        binding_ids = [binding.binding_id for binding in self.evidence_bindings]
        if len(binding_ids) != len(set(binding_ids)):
            raise ValueError("duplicate evidence binding_id")
        for binding in self.evidence_bindings:
            if binding.source_id not in known_sources:
                raise ValueError(f"evidence binding {binding.binding_id} references unknown source")

        if self.completeness == CompletenessState.COMPLETE:
            if self.expected_count is None:
                raise ValueError("complete manifest requires source-backed expected_count")
            if self.expected_count != len(self.components):
                raise ValueError("complete manifest expected_count must equal observed component count")
            if self.unresolved_count not in {None, 0}:
                raise ValueError("complete manifest cannot have unresolved components")
        elif self.completeness == CompletenessState.UNKNOWN and self.expected_count is not None:
            raise ValueError("unknown completeness cannot claim an expected_count")
        return self

    @staticmethod
    def _require_known_sources(source_ids: list[str], known_sources: set[str], target: str) -> None:
        unknown = sorted(set(source_ids) - known_sources)
        if unknown:
            raise ValueError(f"{target} references unknown sources: {', '.join(unknown)}")


class EvidenceCoverage(ManifestModel):
    required_fields: int = Field(ge=0)
    supported_fields: int = Field(ge=0)
    ratio: float = Field(ge=0, le=1)


class ComponentIngestAuditReport(ManifestModel):
    schema_version: Literal["1.0"] = COMPONENT_SOURCE_MANIFEST_SCHEMA_VERSION
    game_slug: str
    resolved_ruleset_id: str | None = None
    completeness: CompletenessState
    creates: list[str] = Field(default_factory=list)
    updates: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)
    duplicate_candidates: list[list[str]] = Field(default_factory=list)
    rejected_unknown_properties: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence_coverage: EvidenceCoverage
    affected_records: dict[str, int] = Field(default_factory=dict)
