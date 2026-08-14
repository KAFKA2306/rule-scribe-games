from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RULESET_SCHEMA_VERSION = "1.0"


class RuleSetStatus(StrEnum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class RuleSetVerificationStatus(StrEnum):
    UNKNOWN = "unknown"
    SOURCE_BOUND = "source_bound"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RuleSetRelationType(StrEnum):
    DERIVED_FROM = "derived_from"
    VARIANT_OF = "variant_of"
    TRANSLATION_OF = "translation_of"
    SUPERSEDES = "supersedes"


class RuleSetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuleSet(RuleSetSchema):
    ruleset_id: str = Field(min_length=1)
    game_id: str = Field(min_length=1)
    work_id: str | None = None
    version: int = Field(default=1, ge=1)
    schema_version: str = "1.0"

    language_code: str | None = Field(default=None, min_length=2, max_length=35)
    edition_label: str | None = None
    revision_label: str | None = None
    source_revision: str | None = None
    platform: str | None = None
    publisher_name: str | None = None
    publication_date: date | None = None
    effective_date: date | None = None

    status: RuleSetStatus = RuleSetStatus.UNKNOWN
    verification_status: RuleSetVerificationStatus = RuleSetVerificationStatus.UNKNOWN
    is_active: bool = True

    base_rule_set_id: str | None = None
    relation_type: RuleSetRelationType | None = None
    variant_label: str | None = None
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity_and_relation(self):
        if self.base_rule_set_id == self.ruleset_id:
            raise ValueError("a ruleset cannot derive from itself")
        if (self.base_rule_set_id is None) != (self.relation_type is None):
            raise ValueError("base_rule_set_id and relation_type must be provided together")
        if self.relation_type == RuleSetRelationType.VARIANT_OF and not self.variant_label:
            raise ValueError("variant_of rulesets require variant_label")
        if self.status == RuleSetStatus.SUPERSEDED and self.is_active:
            raise ValueError("superseded rulesets cannot be active")
        if self.status == RuleSetStatus.ACTIVE and not self.is_active:
            raise ValueError("active rulesets must be active")
        return self


class RuleSetListResponse(RuleSetSchema):
    schema_version: Literal["1.0"] = RULESET_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    rulesets: list[RuleSet] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_availability(self):
        if self.status == "not_available" and self.rulesets:
            raise ValueError("not_available ruleset responses must be empty")
        for ruleset in self.rulesets:
            if ruleset.game_id != self.game_id:
                raise ValueError("ruleset belongs to a different game")
        return self
