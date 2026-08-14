from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from app.models.component_catalog import ComponentVerificationStatus, PropertyCardinality, PropertyValueType
from app.models.component_ingestion import (
    ComponentIngestAuditReport,
    ComponentSourceManifest,
    EvidenceCoverage,
    EvidenceRelation,
    ManifestComponent,
    ManifestComponentSet,
)


class ExistingComponentSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ruleset_id: str
    component_sets: list[ManifestComponentSet] = Field(default_factory=list)
    property_definitions: list[dict] = Field(default_factory=list)
    components: list[ManifestComponent] = Field(default_factory=list)


def _normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"[^\w]+", "", normalized, flags=re.UNICODE)


def _jsonish(model) -> dict:
    return model.model_dump(mode="json", exclude_none=True)


class ComponentIngestionDryRun:
    """Pure fail-closed diff/validation engine for component source manifests.

    Database resolution and writes are intentionally kept outside this class so
    every promotion rule can be exhaustively tested before production access.
    """

    def run(
        self,
        manifest: ComponentSourceManifest,
        *,
        resolved_ruleset_id: str | None,
        existing: ExistingComponentSnapshot | None = None,
    ) -> ComponentIngestAuditReport:
        blockers: list[str] = []
        rejected_unknown_properties = self._unknown_properties(manifest)
        if rejected_unknown_properties:
            blockers.append("UNKNOWN_PROPERTY_DEFINITION")

        blockers.extend(self._property_contract_blockers(manifest))
        duplicate_candidates = self._duplicate_candidates(manifest)
        if duplicate_candidates:
            blockers.append("DUPLICATE_COMPONENT_IDENTITY_CANDIDATE")

        if resolved_ruleset_id is None:
            blockers.append("RULESET_NOT_RESOLVED")
        elif manifest.ruleset.ruleset_id and manifest.ruleset.ruleset_id != resolved_ruleset_id:
            blockers.append("RULESET_SELECTOR_MISMATCH")
        if existing is not None and resolved_ruleset_id is not None and existing.ruleset_id != resolved_ruleset_id:
            blockers.append("EXISTING_SNAPSHOT_RULESET_MISMATCH")

        coverage = self._evidence_coverage(manifest)
        if coverage.required_fields != coverage.supported_fields:
            blockers.append("FIELD_EVIDENCE_COVERAGE_INCOMPLETE")

        creates, updates, unchanged = self._component_diff(manifest, existing)
        affected_records = {
            "sources": len(manifest.sources),
            "component_sets": len(manifest.component_sets),
            "property_definitions": len(manifest.property_definitions),
            "components": len(manifest.components),
            "evidence_bindings": len(manifest.evidence_bindings),
        }
        return ComponentIngestAuditReport(
            game_slug=manifest.game_slug,
            resolved_ruleset_id=resolved_ruleset_id,
            completeness=manifest.completeness,
            creates=creates,
            updates=updates,
            unchanged=unchanged,
            duplicate_candidates=duplicate_candidates,
            rejected_unknown_properties=rejected_unknown_properties,
            blockers=sorted(set(blockers)),
            evidence_coverage=coverage,
            affected_records=affected_records,
        )

    @staticmethod
    def _unknown_properties(manifest: ComponentSourceManifest) -> list[str]:
        known = {definition.property_key for definition in manifest.property_definitions}
        return sorted(
            {
                f"{component.component_id}:{prop.property_key}"
                for component in manifest.components
                for prop in component.properties
                if prop.property_key not in known
            }
        )

    @staticmethod
    def _property_contract_blockers(manifest: ComponentSourceManifest) -> list[str]:
        definitions = {definition.property_key: definition for definition in manifest.property_definitions}
        component_ids = {component.component_id for component in manifest.components}
        blockers: list[str] = []
        for component in manifest.components:
            for prop in component.properties:
                definition = definitions.get(prop.property_key)
                if definition is None:
                    continue
                if definition.cardinality == PropertyCardinality.ONE and len(prop.values) != 1:
                    blockers.append(f"PROPERTY_CARDINALITY_MISMATCH:{component.component_id}:{prop.property_key}")
                    continue
                actual_type = prop.values[0].value_type
                if actual_type != definition.value_type.value:
                    blockers.append(f"PROPERTY_TYPE_MISMATCH:{component.component_id}:{prop.property_key}")
                    continue
                if definition.value_type == PropertyValueType.ENUM:
                    invalid = [value.value for value in prop.values if value.value not in definition.enum_values]
                    if invalid:
                        blockers.append(f"PROPERTY_ENUM_UNKNOWN:{component.component_id}:{prop.property_key}")
                if definition.value_type == PropertyValueType.COMPONENT_REF:
                    unknown = [value.value for value in prop.values if value.value not in component_ids]
                    if unknown:
                        blockers.append(f"PROPERTY_COMPONENT_REF_UNKNOWN:{component.component_id}:{prop.property_key}")
        return blockers

    @staticmethod
    def _duplicate_candidates(manifest: ComponentSourceManifest) -> list[list[str]]:
        buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
        for component in manifest.components:
            buckets[(component.kind.value, _normalized_name(component.canonical_name))].append(component.component_id)
        return sorted(
            sorted(ids)
            for ids in buckets.values()
            if len(set(ids)) > 1
        )

    @staticmethod
    def _required_evidence_targets(manifest: ComponentSourceManifest) -> dict[str, set[str]]:
        targets: dict[str, set[str]] = {}

        def register(target: str, status: ComponentVerificationStatus, source_ids: list[str]) -> None:
            if status in {ComponentVerificationStatus.SOURCE_BOUND, ComponentVerificationStatus.VERIFIED}:
                targets[target] = set(source_ids)

        for item in manifest.component_sets:
            register(f"component_sets.{item.component_set_id}", item.verification_status, item.source_ids)
        for definition in manifest.property_definitions:
            register(
                f"property_definitions.{definition.property_key}",
                definition.verification_status,
                definition.source_ids,
            )
        for component in manifest.components:
            register(f"components.{component.component_id}", component.verification_status, component.source_ids)
            for prop in component.properties:
                register(
                    f"components.{component.component_id}.properties.{prop.property_key}",
                    prop.verification_status,
                    prop.source_ids,
                )
            for ability in component.abilities:
                register(
                    f"components.{component.component_id}.abilities.{ability.ability_id}",
                    ability.verification_status,
                    ability.source_ids,
                )
        return targets

    @classmethod
    def _evidence_coverage(cls, manifest: ComponentSourceManifest) -> EvidenceCoverage:
        required = cls._required_evidence_targets(manifest)
        supporting: dict[str, set[str]] = defaultdict(set)
        for binding in manifest.evidence_bindings:
            if binding.relation == EvidenceRelation.SUPPORTS:
                supporting[binding.target_path].add(binding.source_id)
        supported = sum(
            1
            for target, allowed_sources in required.items()
            if supporting.get(target, set()) & allowed_sources
        )
        total = len(required)
        return EvidenceCoverage(
            required_fields=total,
            supported_fields=supported,
            ratio=1.0 if total == 0 else supported / total,
        )

    @staticmethod
    def _component_diff(
        manifest: ComponentSourceManifest,
        existing: ExistingComponentSnapshot | None,
    ) -> tuple[list[str], list[str], list[str]]:
        if existing is None:
            return sorted(component.component_id for component in manifest.components), [], []
        current = {component.component_id: component for component in existing.components}
        creates: list[str] = []
        updates: list[str] = []
        unchanged: list[str] = []
        for component in manifest.components:
            prior = current.get(component.component_id)
            if prior is None:
                creates.append(component.component_id)
            elif _jsonish(prior) == _jsonish(component):
                unchanged.append(component.component_id)
            else:
                updates.append(component.component_id)
        return sorted(creates), sorted(updates), sorted(unchanged)
