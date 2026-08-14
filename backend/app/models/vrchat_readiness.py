from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.component_catalog import ComponentKind
from app.models.vrchat_manifest import CapabilityName

READINESS_SCHEMA_VERSION = "1.0"


class ReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ReadinessStatus(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review-required"
    UNSUPPORTED = "unsupported"


class RequirementState(StrEnum):
    REQUIRED = "required"
    NOT_REQUIRED = "not-required"
    UNKNOWN = "unknown"


class RuleCoverageDimension(StrEnum):
    SETUP = "setup"
    LOOP = "loop"
    ACTION = "action"
    RESOLUTION = "resolution"
    END = "end"
    WIN = "win"


class RuleCoverageState(StrEnum):
    VERIFIED = "verified"
    SOURCE_BOUND = "source-bound"
    UNVERIFIED = "unverified"
    MISSING = "missing"


class AssetPolicy(StrEnum):
    GENERIC_ONLY = "generic-only"


class CapabilityAssessment(ReadinessModel):
    capability: CapabilityName
    requirement: RequirementState
    evidence_refs: list[str] = Field(default_factory=list, alias="evidenceRefs")
    reason_code: str = Field(alias="reasonCode", min_length=1)


class RuleCoverageAssessment(ReadinessModel):
    dimension: RuleCoverageDimension
    state: RuleCoverageState
    rule_ids: list[str] = Field(default_factory=list, alias="ruleIds")


class ReadinessAuditRecord(ReadinessModel):
    schema_version: Literal["1.0"] = Field(default=READINESS_SCHEMA_VERSION, alias="schemaVersion")
    game_id: str = Field(alias="gameId", min_length=1)
    slug: str | None = None
    title: str = Field(min_length=1)
    ruleset_id: str | None = Field(default=None, alias="rulesetId")
    ruleset_language: str | None = Field(default=None, alias="rulesetLanguage")
    ruleset_edition: str | None = Field(default=None, alias="rulesetEdition")
    ruleset_platform: str | None = Field(default=None, alias="rulesetPlatform")
    readiness_status: ReadinessStatus = Field(alias="readinessStatus")
    player_count_status: Literal["known", "partial", "unknown"] = Field(alias="playerCountStatus")
    rule_coverage: list[RuleCoverageAssessment] = Field(default_factory=list, alias="ruleCoverage")
    capability_assessments: list[CapabilityAssessment] = Field(default_factory=list, alias="capabilityAssessments")
    required_capabilities: list[CapabilityName] = Field(default_factory=list, alias="requiredCapabilities")
    unknown_capabilities: list[CapabilityName] = Field(default_factory=list, alias="unknownCapabilities")
    missing_capabilities: list[CapabilityName] = Field(default_factory=list, alias="missingCapabilities")
    component_kinds: list[ComponentKind] = Field(default_factory=list, alias="componentKinds")
    component_count: int | None = Field(default=None, alias="componentCount", ge=0)
    data_blockers: list[str] = Field(default_factory=list, alias="dataBlockers")
    evidence_blockers: list[str] = Field(default_factory=list, alias="evidenceBlockers")
    rights_blockers: list[str] = Field(default_factory=list, alias="rightsBlockers")
    runtime_blockers: list[str] = Field(default_factory=list, alias="runtimeBlockers")
    asset_policy: Literal["generic-only"] = Field(default=AssetPolicy.GENERIC_ONLY, alias="assetPolicy")
    recommended_module_class: str = Field(alias="recommendedModuleClass", min_length=1)
    manifest_projectable: bool = Field(alias="manifestProjectable")
    module_id: str | None = Field(default=None, alias="moduleId")
    module_version_range: str | None = Field(default=None, alias="moduleVersionRange")
    promotable_to_catalog: bool = Field(alias="promotableToCatalog")
    audited_at: datetime = Field(alias="auditedAt")

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.required_capabilities, "requiredCapabilities"),
            (self.unknown_capabilities, "unknownCapabilities"),
            (self.missing_capabilities, "missingCapabilities"),
            (self.component_kinds, "componentKinds"),
            (self.data_blockers, "dataBlockers"),
            (self.evidence_blockers, "evidenceBlockers"),
            (self.rights_blockers, "rightsBlockers"),
            (self.runtime_blockers, "runtimeBlockers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.audited_at.tzinfo is None or self.audited_at.utcoffset() is None:
            raise ValueError("auditedAt must include a timezone offset")
        if self.promotable_to_catalog != (self.readiness_status == ReadinessStatus.READY):
            raise ValueError("promotableToCatalog must be true only for ready records")
        return self


class ReadinessAuditReport(ReadinessModel):
    schema_version: Literal["1.0"] = Field(default=READINESS_SCHEMA_VERSION, alias="schemaVersion")
    audited_at: datetime = Field(alias="auditedAt")
    total_games: int = Field(alias="totalGames", ge=0)
    total_records: int = Field(alias="totalRecords", ge=0)
    promotable_count: int = Field(alias="promotableCount", ge=0)
    status_counts: dict[ReadinessStatus, int] = Field(alias="statusCounts")
    records: list[ReadinessAuditRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self):
        if self.audited_at.tzinfo is None or self.audited_at.utcoffset() is None:
            raise ValueError("auditedAt must include a timezone offset")
        if self.total_records != len(self.records):
            raise ValueError("totalRecords must equal records length")
        game_ids = {record.game_id for record in self.records}
        if self.total_games != len(game_ids):
            raise ValueError("totalGames must equal unique audited game IDs")
        if self.promotable_count != sum(record.promotable_to_catalog for record in self.records):
            raise ValueError("promotableCount must match ready records")
        expected_counts = {status: 0 for status in ReadinessStatus}
        for record in self.records:
            expected_counts[record.readiness_status] += 1
        if self.status_counts != expected_counts:
            raise ValueError("statusCounts must match records")
        return self
