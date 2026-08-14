from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MANIFEST_SCHEMA_VERSION = "1.0"
MODULE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:-]{2,127}$"


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VrchatPlatform(StrEnum):
    PC = "vrchat-pc"
    ANDROID = "vrchat-android"


class InteractionProfile(StrEnum):
    UNKNOWN = "unknown"
    DESKTOP = "desktop"
    VR = "vr"
    DESKTOP_AND_VR = "desktop-and-vr"


class CapabilityName(StrEnum):
    TURN_BASED = "turn-based"
    SIMULTANEOUS = "simultaneous"
    HIDDEN_INFORMATION = "hidden-information"
    DECK = "deck"
    DICE = "dice"
    TOKENS = "tokens"
    BOARD = "board"
    SCORE = "score"
    TIMER = "timer"
    REALTIME = "realtime"
    DEXTERITY = "dexterity"


class CapabilityState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


_CAPABILITY_FIELDS: dict[CapabilityName, str] = {
    CapabilityName.TURN_BASED: "turn_based",
    CapabilityName.SIMULTANEOUS: "simultaneous",
    CapabilityName.HIDDEN_INFORMATION: "hidden_information",
    CapabilityName.DECK: "deck",
    CapabilityName.DICE: "dice",
    CapabilityName.TOKENS: "tokens",
    CapabilityName.BOARD: "board",
    CapabilityName.SCORE: "score",
    CapabilityName.TIMER: "timer",
    CapabilityName.REALTIME: "realtime",
    CapabilityName.DEXTERITY: "dexterity",
}


class CapabilityMatrix(ManifestModel):
    turn_based: CapabilityState = Field(alias="turn-based")
    simultaneous: CapabilityState
    hidden_information: CapabilityState = Field(alias="hidden-information")
    deck: CapabilityState
    dice: CapabilityState
    tokens: CapabilityState
    board: CapabilityState
    score: CapabilityState
    timer: CapabilityState
    realtime: CapabilityState
    dexterity: CapabilityState

    def state_for(self, capability: CapabilityName) -> CapabilityState:
        return getattr(self, _CAPABILITY_FIELDS[capability])


class PlayerCount(ManifestModel):
    minimum: int | None = Field(default=None, alias="min", ge=1)
    maximum: int | None = Field(default=None, alias="max", ge=1)
    status: Literal["known", "partial", "unknown"]

    @model_validator(mode="after")
    def validate_range(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("playerCount.min cannot exceed playerCount.max")
        expected = (
            "known"
            if self.minimum is not None and self.maximum is not None
            else "partial"
            if self.minimum is not None or self.maximum is not None
            else "unknown"
        )
        if self.status != expected:
            raise ValueError(f"playerCount.status must be {expected}")
        return self


class RuleReferences(ManifestModel):
    setup: list[str] = Field(default_factory=list)
    phases: list[str] = Field(default_factory=list)
    turns: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    scoring: list[str] = Field(default_factory=list)
    round_ends: list[str] = Field(default_factory=list, alias="roundEnds")
    end_conditions: list[str] = Field(default_factory=list, alias="endConditions")
    victory: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    targeting: list[str] = Field(default_factory=list)
    conflict_resolution: list[str] = Field(default_factory=list, alias="conflictResolution")
    variants: list[str] = Field(default_factory=list)


class EvidenceSummary(ManifestModel):
    source_ids: list[str] = Field(default_factory=list, alias="sourceIds")
    claim_refs: list[str] = Field(default_factory=list, alias="claimRefs")
    evidence_refs: list[str] = Field(default_factory=list, alias="evidenceRefs")
    verified_rule_ids: list[str] = Field(default_factory=list, alias="verifiedRuleIds")
    source_bound_rule_ids: list[str] = Field(default_factory=list, alias="sourceBoundRuleIds")
    unverified_rule_ids: list[str] = Field(default_factory=list, alias="unverifiedRuleIds")
    rejected_rule_ids: list[str] = Field(default_factory=list, alias="rejectedRuleIds")


class SourceSchemaVersions(ManifestModel):
    ruleset: str
    rule_graph: str = Field(alias="ruleGraph")
    component_catalog: str | None = Field(default=None, alias="componentCatalog")


class ModuleBinding(ManifestModel):
    """Explicit runtime declaration; missing capabilities stay unknown rather than being inferred."""

    module_id: str = Field(alias="moduleId", pattern=MODULE_ID_PATTERN)
    module_version_range: str = Field(alias="moduleVersionRange", min_length=1)
    supported_platforms: list[VrchatPlatform] = Field(default_factory=list, alias="supportedPlatforms")
    interaction_profile: InteractionProfile = Field(
        default=InteractionProfile.UNKNOWN,
        alias="interactionProfile",
    )
    capabilities: dict[CapabilityName, CapabilityState] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_platforms(self):
        if len(self.supported_platforms) != len(set(self.supported_platforms)):
            raise ValueError("supportedPlatforms must be unique")
        return self


class BoardGameModuleManifest(ManifestModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://github.com/KAFKA2306/rule-scribe-games/"
                "schemas/vrchat/board-game-module-manifest-v1.schema.json"
            ),
        },
    )

    schema_version: Literal["1.0"] = Field(default=MANIFEST_SCHEMA_VERSION, alias="schemaVersion")
    game_id: str = Field(alias="gameId", min_length=1)
    slug: str = Field(min_length=1)
    ruleset_id: str = Field(alias="rulesetId", min_length=1)
    module_id: str = Field(alias="moduleId", pattern=MODULE_ID_PATTERN)
    module_version_range: str = Field(alias="moduleVersionRange", min_length=1)
    player_count: PlayerCount = Field(alias="playerCount")
    supported_platforms: list[VrchatPlatform] = Field(default_factory=list, alias="supportedPlatforms")
    interaction_profile: InteractionProfile = Field(
        default=InteractionProfile.UNKNOWN,
        alias="interactionProfile",
    )
    capabilities: CapabilityMatrix
    rules: RuleReferences
    component_set_refs: list[str] = Field(default_factory=list, alias="componentSetRefs")
    evidence: EvidenceSummary
    source_schemas: SourceSchemaVersions = Field(alias="sourceSchemas")
    locale: str | None = None
    revision: str | None = None
    generated_at: datetime = Field(alias="generatedAt")

    @model_validator(mode="after")
    def validate_contract(self):
        if len(self.component_set_refs) != len(set(self.component_set_refs)):
            raise ValueError("componentSetRefs must be unique")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generatedAt must include a timezone offset")
        return self

    def canonical_json(self) -> str:
        """Stable serialization. The projector never reads the wall clock."""

        return json.dumps(
            self.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
