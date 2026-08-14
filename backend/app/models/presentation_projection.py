from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PRESENTATION_PROJECTION_SCHEMA_VERSION = "1.0"


class ProjectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectionSectionKind(StrEnum):
    SYNOPSIS = "synopsis"
    QUICK_RULES = "quick_rules"
    SETUP = "setup"
    GAME_FLOW = "game_flow"
    END_CONDITION = "end_condition"
    SCORING = "scoring"
    GLOSSARY = "glossary"
    COMMON_ERRORS = "common_errors"
    PRO_TIPS = "pro_tips"


class ProjectionSectionStatus(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"


class ProjectionEvidence(ProjectionModel):
    claim_id: str
    claim_lifecycle: Literal["accepted"] = "accepted"
    support_status: Literal["supported"] = "supported"
    source_ids: list[str] = Field(default_factory=list, min_length=1)


class ProjectedRule(ProjectionModel):
    rule_id: str
    node_type: str
    text: str = Field(min_length=1)
    sequence: int | None = Field(default=None, ge=0)
    evidence: ProjectionEvidence


class ProjectedGlossaryEntry(ProjectionModel):
    concept_id: str
    label: str = Field(min_length=1)
    definition: str | None = None
    aliases: list[str] = Field(default_factory=list)
    related_concept_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list, min_length=1)


class RuleProjectionSection(ProjectionModel):
    kind: ProjectionSectionKind
    status: ProjectionSectionStatus
    items: list[ProjectedRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self):
        if self.status == ProjectionSectionStatus.NOT_AVAILABLE and self.items:
            raise ValueError("not_available rule projection sections must be empty")
        if self.status == ProjectionSectionStatus.AVAILABLE and not self.items:
            raise ValueError("available rule projection sections require items")
        return self


class GlossaryProjectionSection(ProjectionModel):
    kind: Literal[ProjectionSectionKind.GLOSSARY] = ProjectionSectionKind.GLOSSARY
    status: ProjectionSectionStatus
    items: list[ProjectedGlossaryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self):
        if self.status == ProjectionSectionStatus.NOT_AVAILABLE and self.items:
            raise ValueError("not_available glossary projection must be empty")
        if self.status == ProjectionSectionStatus.AVAILABLE and not self.items:
            raise ValueError("available glossary projection requires items")
        return self


class PresentationProjectionResponse(ProjectionModel):
    schema_version: Literal["1.0"] = PRESENTATION_PROJECTION_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    rule_set_id: str
    language_code: str
    synopsis: RuleProjectionSection
    quick_rules: RuleProjectionSection
    setup: RuleProjectionSection
    game_flow: RuleProjectionSection
    end_condition: RuleProjectionSection
    scoring: RuleProjectionSection
    glossary: GlossaryProjectionSection
    common_errors: RuleProjectionSection
    pro_tips: RuleProjectionSection

    @model_validator(mode="after")
    def validate_response(self):
        sections = (
            self.synopsis,
            self.quick_rules,
            self.setup,
            self.game_flow,
            self.end_condition,
            self.scoring,
            self.glossary,
            self.common_errors,
            self.pro_tips,
        )
        any_available = any(section.status == ProjectionSectionStatus.AVAILABLE for section in sections)
        if self.status == "available" and not any_available:
            raise ValueError("available presentation projections require at least one available section")
        if self.status == "not_available" and any_available:
            raise ValueError("not_available presentation projections cannot contain available sections")
        return self
