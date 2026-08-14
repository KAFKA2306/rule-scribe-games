from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

EVIDENCE_SCHEMA_VERSION = "1.0"
STABLE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:-]{2,191}$"
FIELD_PATH_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9_.\[\]-]{0,255}$"


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceTargetType(StrEnum):
    RULE_NODE = "rule_node"
    COMPONENT_PROPERTY = "component_property"
    ABILITY_PRINTED_TEXT = "ability_printed_text"
    ABILITY_NORMALIZED = "ability_normalized"
    GAME_METADATA = "game_metadata"


class EvidenceRelation(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"
    UNRESOLVED = "unresolved"


class ClaimLifecycleStatus(StrEnum):
    UNKNOWN = "unknown"
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ClaimSupportStatus(StrEnum):
    UNRESOLVED = "unresolved"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    CONTRADICTED = "contradicted"


class EvidenceSource(EvidenceModel):
    source_id: str = Field(pattern=STABLE_ID_PATTERN)
    url: HttpUrl | None = None
    document_identity: str | None = None
    source_type: str = Field(min_length=1, max_length=80)
    publisher_name: str | None = None
    platform: str | None = None
    language_code: str | None = Field(default=None, min_length=2, max_length=35)
    revision_label: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    trust_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_document_identity(self):
        if self.url is None and not self.document_identity:
            raise ValueError("source requires url or document_identity")
        return self


class SourceLocator(EvidenceModel):
    locator_id: str = Field(pattern=STABLE_ID_PATTERN)
    source_id: str = Field(pattern=STABLE_ID_PATTERN)
    page_number: int | None = Field(default=None, ge=1)
    section_heading: str | None = None
    anchor: str | None = None
    selector: str | None = None
    structured_path: str | None = None
    external_reference: str | None = None

    @model_validator(mode="after")
    def require_real_locator(self):
        concrete = (
            self.page_number,
            self.section_heading,
            self.anchor,
            self.selector,
            self.structured_path,
            self.external_reference,
        )
        if not any(value is not None and value != "" for value in concrete):
            raise ValueError("locator requires at least one concrete source position")
        return self


class ClaimTarget(EvidenceModel):
    target_type: EvidenceTargetType
    rule_id: str | None = None
    component_id: str | None = None
    property_key: str | None = None
    ordinal: int | None = Field(default=None, ge=0)
    ability_id: str | None = None
    field_path: str | None = Field(default=None, pattern=FIELD_PATH_PATTERN)

    @model_validator(mode="after")
    def validate_target(self):
        if self.target_type == EvidenceTargetType.RULE_NODE:
            if not self.rule_id or any(value is not None for value in (self.component_id, self.property_key, self.ordinal, self.ability_id, self.field_path)):
                raise ValueError("rule_node target requires only rule_id")
        elif self.target_type == EvidenceTargetType.COMPONENT_PROPERTY:
            if not self.component_id or not self.property_key or self.ordinal is None:
                raise ValueError("component_property target requires component_id, property_key and ordinal")
            if any(value is not None for value in (self.rule_id, self.ability_id, self.field_path)):
                raise ValueError("component_property target contains unrelated target fields")
        elif self.target_type in {EvidenceTargetType.ABILITY_PRINTED_TEXT, EvidenceTargetType.ABILITY_NORMALIZED}:
            if not self.ability_id or any(value is not None for value in (self.rule_id, self.component_id, self.property_key, self.ordinal, self.field_path)):
                raise ValueError("ability target requires only ability_id")
        elif self.target_type == EvidenceTargetType.GAME_METADATA:
            if not self.field_path or any(value is not None for value in (self.rule_id, self.component_id, self.property_key, self.ordinal, self.ability_id)):
                raise ValueError("game_metadata target requires only field_path")
        return self


class Claim(EvidenceModel):
    claim_id: str = Field(pattern=STABLE_ID_PATTERN)
    ruleset_id: str = Field(min_length=1)
    claim_type: str = Field(min_length=1, max_length=80)
    normalized_payload: dict[str, Any]
    target: ClaimTarget
    lifecycle_status: ClaimLifecycleStatus = ClaimLifecycleStatus.UNKNOWN
    generator_provenance: dict[str, Any] = Field(default_factory=dict)


class EvidenceBinding(EvidenceModel):
    binding_id: str = Field(pattern=STABLE_ID_PATTERN)
    claim_id: str = Field(pattern=STABLE_ID_PATTERN)
    source_id: str = Field(pattern=STABLE_ID_PATTERN)
    locator_id: str | None = Field(default=None, pattern=STABLE_ID_PATTERN)
    relation: EvidenceRelation
    reviewer_provenance: dict[str, Any] = Field(default_factory=dict)
    generator_provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    verified_at: datetime | None = None


class EvidenceBindingDetail(EvidenceModel):
    binding: EvidenceBinding
    source: EvidenceSource
    locator: SourceLocator | None = None

    @model_validator(mode="after")
    def validate_binding_detail(self):
        if self.binding.source_id != self.source.source_id:
            raise ValueError("binding source does not match embedded source")
        if self.binding.locator_id is None:
            if self.locator is not None:
                raise ValueError("locator must be absent when binding has no locator_id")
        else:
            if self.locator is None or self.locator.locator_id != self.binding.locator_id:
                raise ValueError("binding locator does not match embedded locator")
            if self.locator.source_id != self.source.source_id:
                raise ValueError("locator belongs to a different source")
        return self


class ClaimTrace(EvidenceModel):
    claim: Claim
    support_status: ClaimSupportStatus
    projection_eligible: bool
    bindings: list[EvidenceBindingDetail] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_derived_status(self):
        expected = derive_claim_support_status([item.binding for item in self.bindings])
        if self.support_status != expected:
            raise ValueError("support_status must be derived from evidence relations")
        if self.projection_eligible != (expected == ClaimSupportStatus.SUPPORTED):
            raise ValueError("projection_eligible is true only for uncontradicted supported claims")
        return self


class EvidenceTraceResponse(EvidenceModel):
    schema_version: Literal["1.0"] = EVIDENCE_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    ruleset_id: str
    target: ClaimTarget
    claims: list[ClaimTrace] = Field(default_factory=list)


class ClaimDetailResponse(EvidenceModel):
    schema_version: Literal["1.0"] = EVIDENCE_SCHEMA_VERSION
    status: Literal["available"] = "available"
    game_id: str
    slug: str
    ruleset_id: str
    trace: ClaimTrace


def derive_claim_support_status(bindings: list[EvidenceBinding]) -> ClaimSupportStatus:
    relations = {binding.relation for binding in bindings}
    has_support = EvidenceRelation.SUPPORTS in relations
    has_contradiction = EvidenceRelation.CONTRADICTS in relations
    if has_support and has_contradiction:
        return ClaimSupportStatus.CONTESTED
    if has_support:
        return ClaimSupportStatus.SUPPORTED
    if has_contradiction:
        return ClaimSupportStatus.CONTRADICTED
    return ClaimSupportStatus.UNRESOLVED


def build_claim_trace(claim: Claim, bindings: list[EvidenceBindingDetail]) -> ClaimTrace:
    support_status = derive_claim_support_status([item.binding for item in bindings])
    return ClaimTrace(
        claim=claim,
        support_status=support_status,
        projection_eligible=support_status == ClaimSupportStatus.SUPPORTED,
        bindings=bindings,
    )
