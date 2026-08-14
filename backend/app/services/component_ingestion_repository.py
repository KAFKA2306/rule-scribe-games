from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core import supabase
from app.models.component_catalog import ComponentVerificationStatus
from app.models.component_ingestion import ComponentSourceManifest
from app.models.evidence import ClaimTarget, EvidenceTargetType
from app.services.component_ingestion import ComponentIngestionDryRun


class ComponentIngestionResolutionError(RuntimeError):
    pass


class ComponentIngestionBlockedError(RuntimeError):
    pass


class ComponentIngestionReadbackError(RuntimeError):
    pass


class ResolvedRuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_id: str
    ruleset_id: str
    game_slug: str


class ComponentIngestionApplyResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    ruleset_id: str
    catalog_id: str
    persisted: dict[str, int] = Field(default_factory=dict)


def _stable_id(prefix: str, game_slug: str, identity: str) -> str:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"ci:{game_slug}:{prefix}:{digest}"


def _target_identity(manifest: ComponentSourceManifest, target: ClaimTarget) -> str:
    selector = manifest.ruleset.model_dump(mode="json", exclude_none=True)
    target_payload = target.model_dump(mode="json", exclude_none=True)
    return json.dumps(
        {"selector": selector, "target": target_payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _target_claim_id(manifest: ComponentSourceManifest, target: ClaimTarget) -> str:
    return _stable_id("claim", manifest.game_slug, _target_identity(manifest, target))


def _binding_id(manifest: ComponentSourceManifest, manifest_binding_id: str) -> str:
    identity = json.dumps(
        {"selector": manifest.ruleset.model_dump(mode="json", exclude_none=True), "binding": manifest_binding_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return _stable_id("binding", manifest.game_slug, identity)


def _target_payload(manifest: ComponentSourceManifest, target: ClaimTarget) -> tuple[dict[str, Any], ComponentVerificationStatus]:
    if target.target_type == EvidenceTargetType.COMPONENT_SET:
        item = next(item for item in manifest.component_sets if item.component_set_id == target.component_set_id)
        return item.model_dump(mode="json", exclude_none=True), item.verification_status
    if target.target_type == EvidenceTargetType.PROPERTY_DEFINITION:
        item = next(item for item in manifest.property_definitions if item.property_key == target.property_key)
        return item.model_dump(mode="json", exclude_none=True), item.verification_status
    if target.target_type == EvidenceTargetType.COMPONENT:
        item = next(item for item in manifest.components if item.component_id == target.component_id)
        payload = item.model_dump(mode="json", exclude_none=True, exclude={"properties", "abilities"})
        return payload, item.verification_status
    if target.target_type == EvidenceTargetType.COMPONENT_PROPERTY:
        component = next(item for item in manifest.components if item.component_id == target.component_id)
        prop = next(item for item in component.properties if item.property_key == target.property_key)
        value = prop.values[target.ordinal or 0]
        return {
            "component_id": component.component_id,
            "property_key": prop.property_key,
            "ordinal": target.ordinal,
            "value": value.model_dump(mode="json"),
        }, prop.verification_status
    if target.target_type in {EvidenceTargetType.ABILITY_PRINTED_TEXT, EvidenceTargetType.ABILITY_NORMALIZED}:
        ability = next(
            ability
            for component in manifest.components
            for ability in component.abilities
            if ability.ability_id == target.ability_id
        )
        value = ability.printed_text if target.target_type == EvidenceTargetType.ABILITY_PRINTED_TEXT else ability.normalized_label
        return {"ability_id": ability.ability_id, "value": value}, ability.verification_status
    raise ValueError(f"unsupported component ingestion target: {target.target_type}")


def _claim_lifecycle(status: ComponentVerificationStatus) -> str:
    if status in {ComponentVerificationStatus.SOURCE_BOUND, ComponentVerificationStatus.VERIFIED}:
        return "accepted"
    if status == ComponentVerificationStatus.REJECTED:
        return "rejected"
    return "candidate"


def _property_row(  # noqa: PLR0913
    *,
    ruleset_id: str,
    component_id: str,
    prop,
    definition,
    ordinal: int,
    value,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "rule_set_id": ruleset_id,
        "component_id": component_id,
        "property_key": prop.property_key,
        "value_type": value.value_type,
        "cardinality": definition.cardinality.value,
        "ordinal": ordinal,
        "verification_status": prop.verification_status.value,
        "source_ids": prop.source_ids,
        "metadata": {},
        "text_value": None,
        "integer_value": None,
        "number_value": None,
        "boolean_value": None,
        "enum_value": None,
        "concept_ref_id": None,
        "component_ref_id": None,
    }
    field_by_type = {
        "text": "text_value",
        "integer": "integer_value",
        "number": "number_value",
        "boolean": "boolean_value",
        "enum": "enum_value",
        "concept_ref": "concept_ref_id",
        "component_ref": "component_ref_id",
    }
    row[field_by_type[value.value_type]] = value.value
    return row


class ComponentIngestionPlanBuilder:
    def build(self, manifest: ComponentSourceManifest, resolved: ResolvedRuleSet) -> dict[str, Any]:
        definitions = {item.property_key: item for item in manifest.property_definitions}
        claims: dict[str, dict[str, Any]] = {}
        bindings: list[dict[str, Any]] = []

        for binding in manifest.evidence_bindings:
            claim_id = _target_claim_id(manifest, binding.target)
            normalized_payload, status = _target_payload(manifest, binding.target)
            target_fields = binding.target.model_dump(mode="json", exclude_none=True)
            target_type = target_fields.pop("target_type")
            claims[claim_id] = {
                "claim_id": claim_id,
                "rule_set_id": resolved.ruleset_id,
                "claim_type": f"component_ingestion_{target_type}",
                "normalized_payload": normalized_payload,
                "target_type": target_type,
                "lifecycle_status": _claim_lifecycle(status),
                "generator_provenance": {
                    "component_source_manifest_schema": manifest.schema_version,
                    "game_slug": manifest.game_slug,
                },
                **target_fields,
            }
            bindings.append(
                {
                    "binding_id": _binding_id(manifest, binding.binding_id),
                    "manifest_binding_id": binding.binding_id,
                    "claim_id": claim_id,
                    "source_id": binding.source_id,
                    "locator_id": binding.locator_id,
                    "relation": binding.relation.value,
                    "reviewer_provenance": {},
                    "generator_provenance": {
                        "component_source_manifest_schema": manifest.schema_version,
                        "manifest_binding_id": binding.binding_id,
                    },
                }
            )

        component_properties: list[dict[str, Any]] = []
        component_abilities: list[dict[str, Any]] = []
        component_concepts: list[dict[str, Any]] = []
        component_rule_nodes: list[dict[str, Any]] = []
        ability_concepts: list[dict[str, Any]] = []
        ability_rule_nodes: list[dict[str, Any]] = []
        for component in manifest.components:
            for prop in component.properties:
                definition = definitions[prop.property_key]
                for ordinal, value in enumerate(prop.values):
                    component_properties.append(
                        _property_row(
                            ruleset_id=resolved.ruleset_id,
                            component_id=component.component_id,
                            prop=prop,
                            definition=definition,
                            ordinal=ordinal,
                            value=value,
                        )
                    )
            for ability in component.abilities:
                component_abilities.append(
                    {
                        "rule_set_id": resolved.ruleset_id,
                        "component_id": component.component_id,
                        "ability_id": ability.ability_id,
                        "printed_text": ability.printed_text,
                        "normalized_label": ability.normalized_label,
                        "verification_status": ability.verification_status.value,
                        "source_ids": ability.source_ids,
                        "metadata": {},
                    }
                )
                ability_concepts.extend(
                    {
                        "rule_set_id": resolved.ruleset_id,
                        "ability_id": ability.ability_id,
                        "concept_id": concept_id,
                    }
                    for concept_id in ability.concept_ids
                )
                ability_rule_nodes.extend(
                    {
                        "rule_set_id": resolved.ruleset_id,
                        "ability_id": ability.ability_id,
                        "rule_id": rule_id,
                    }
                    for rule_id in ability.rule_ids
                )
            component_concepts.extend(
                {
                    "rule_set_id": resolved.ruleset_id,
                    "component_id": component.component_id,
                    "concept_id": concept_id,
                    "reference_kind": "classifies",
                }
                for concept_id in component.concept_ids
            )
            component_rule_nodes.extend(
                {
                    "rule_set_id": resolved.ruleset_id,
                    "component_id": component.component_id,
                    "rule_id": rule_id,
                    "reference_kind": "governed_by",
                }
                for rule_id in component.rule_ids
            )

        return {
            "schema_version": manifest.schema_version,
            "game_slug": manifest.game_slug,
            "game_id": resolved.game_id,
            "ruleset_id": resolved.ruleset_id,
            "completeness": manifest.completeness.value,
            "expected_count": manifest.expected_count,
            "unresolved_count": manifest.unresolved_count,
            "sources": [
                {
                    "source_id": item.source_id,
                    "url": str(item.url),
                    "source_type": item.source_type,
                    "revision_label": item.revision_label,
                    "trust_metadata": {
                        "authority": item.authority.value,
                        "observed_date": item.observed_date,
                        "extraction_method": item.extraction_method,
                        "component_source_manifest_schema": manifest.schema_version,
                    },
                }
                for item in manifest.sources
            ],
            "source_locators": [item.model_dump(mode="json", exclude_none=True) for item in manifest.source_locators],
            "component_sets": [
                {
                    "rule_set_id": resolved.ruleset_id,
                    **item.model_dump(mode="json", exclude_none=True),
                    "metadata": {},
                }
                for item in manifest.component_sets
            ],
            "property_definitions": [
                {
                    "rule_set_id": resolved.ruleset_id,
                    **item.model_dump(mode="json", exclude_none=True),
                    "metadata": {},
                }
                for item in manifest.property_definitions
            ],
            "components": [
                {
                    "rule_set_id": resolved.ruleset_id,
                    **item.model_dump(mode="json", exclude_none=True, exclude={"properties", "abilities", "concept_ids", "rule_ids"}),
                    "metadata": {},
                }
                for item in manifest.components
            ],
            "component_properties": component_properties,
            "component_abilities": component_abilities,
            "component_concepts": component_concepts,
            "component_rule_nodes": component_rule_nodes,
            "ability_concepts": ability_concepts,
            "ability_rule_nodes": ability_rule_nodes,
            "claims": list(claims.values()),
            "evidence_bindings": bindings,
            "catalog_metadata": {
                "component_ingestion": {
                    "schema_version": manifest.schema_version,
                    "completeness": manifest.completeness.value,
                    "expected_count": manifest.expected_count,
                    "unresolved_count": manifest.unresolved_count,
                }
            },
        }


class ComponentIngestionRepository:
    def __init__(self, client=None):
        self.client = client or supabase._get_client()
        self.plan_builder = ComponentIngestionPlanBuilder()

    def resolve_ruleset(self, manifest: ComponentSourceManifest) -> ResolvedRuleSet:
        games = (
            self.client.table("games")
            .select("id,slug,identity_status")
            .eq("slug", manifest.game_slug)
            .limit(2)
            .execute()
            .data
        )
        if len(games) != 1 or games[0].get("identity_status") != "verified":
            raise ComponentIngestionResolutionError("canonical verified Game identity did not resolve exactly once")
        game = games[0]

        query = self.client.table("rule_sets").select(
            "id,game_id,platform,revision_label,language_code,edition_label,is_active"
        ).eq("game_id", game["id"])
        selector = manifest.ruleset
        if selector.ruleset_id:
            query = query.eq("id", selector.ruleset_id)
        else:
            query = query.eq("platform", selector.platform).eq("revision_label", selector.revision_label).eq("is_active", True)
            if selector.language_code:
                query = query.eq("language_code", selector.language_code)
            if selector.edition_label:
                query = query.eq("edition_label", selector.edition_label)
        rows = query.limit(2).execute().data
        if len(rows) != 1:
            raise ComponentIngestionResolutionError("RuleSet selector did not resolve exactly once")
        return ResolvedRuleSet(game_id=str(game["id"]), ruleset_id=str(rows[0]["id"]), game_slug=manifest.game_slug)

    def read_component_ids(self, ruleset_id: str) -> list[str]:
        rows = self.client.table("components").select("component_id").eq("rule_set_id", ruleset_id).execute().data
        return sorted(str(row["component_id"]) for row in rows)

    def apply(self, manifest: ComponentSourceManifest) -> ComponentIngestionApplyResult:
        resolved = self.resolve_ruleset(manifest)
        existing_ids = self.read_component_ids(resolved.ruleset_id)
        dry_run = ComponentIngestionDryRun().run(manifest, resolved_ruleset_id=resolved.ruleset_id)
        if dry_run.blockers:
            raise ComponentIngestionBlockedError(",".join(dry_run.blockers))
        if manifest.completeness.value == "complete":
            manifest_ids = {item.component_id for item in manifest.components}
            stale_ids = sorted(set(existing_ids) - manifest_ids)
            if stale_ids:
                raise ComponentIngestionBlockedError("COMPLETE_RECONCILIATION_REQUIRES_EXPLICIT_DELETE_POLICY")

        payload = self.plan_builder.build(manifest, resolved)
        response = self.client.rpc("apply_component_ingestion_v1", {"payload": payload}).execute().data
        if not isinstance(response, dict):
            raise ComponentIngestionReadbackError("component ingestion RPC returned an invalid response")
        result = ComponentIngestionApplyResult.model_validate(response)
        self.verify_readback(manifest, resolved, payload)
        return result

    def verify_readback(
        self,
        manifest: ComponentSourceManifest,
        resolved: ResolvedRuleSet,
        payload: dict[str, Any],
    ) -> None:
        checks: list[tuple[str, str, list[str]]] = [
            ("component_sets", "component_set_id", [item.component_set_id for item in manifest.component_sets]),
            ("component_property_definitions", "property_key", [item.property_key for item in manifest.property_definitions]),
            ("components", "component_id", [item.component_id for item in manifest.components]),
            ("claims", "claim_id", [item["claim_id"] for item in payload["claims"]]),
            ("evidence_bindings", "binding_id", [item["binding_id"] for item in payload["evidence_bindings"]]),
        ]
        for table, key, expected in checks:
            if not expected:
                continue
            query = self.client.table(table).select(key).in_(key, expected)
            if table in {"component_sets", "component_property_definitions", "components", "claims"}:
                query = query.eq("rule_set_id", resolved.ruleset_id)
            actual = {str(row[key]) for row in query.execute().data}
            if actual != set(expected):
                raise ComponentIngestionReadbackError(f"read-back mismatch for {table}")
