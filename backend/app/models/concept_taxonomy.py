import re
import unicodedata
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.rule_graph import RuleNodeType

CONCEPT_TAXONOMY_SCHEMA_VERSION = "1.0"


def normalize_concept_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\s_-]+", " ", normalized).strip()


class ConceptType(StrEnum):
    MECHANIC = "mechanic"
    COMPONENT = "component"
    RESOURCE = "resource"
    STATE = "state"
    PLAYER_ACTION = "player_action"
    INFORMATION_STRUCTURE = "information_structure"
    INTERACTION_PATTERN = "interaction_pattern"
    RULE_PATTERN = "rule_pattern"


class ConceptLifecycleStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    MERGED = "merged"


class ConceptVerificationStatus(StrEnum):
    UNKNOWN = "unknown"
    SOURCE_BOUND = "source_bound"
    VERIFIED = "verified"


class ConceptLabelType(StrEnum):
    PREF = "pref"
    ALT = "alt"


class ConceptRelationType(StrEnum):
    BROADER = "broader"
    NARROWER = "narrower"
    RELATED = "related"
    REPLACED_BY = "replaced_by"


class GameConceptUsageRole(StrEnum):
    CORE = "core"
    SUPPORTING = "supporting"
    GLOSSARY = "glossary"


class RuleConceptReferenceKind(StrEnum):
    MENTIONS = "mentions"
    DEFINES = "defines"
    REQUIRES = "requires"
    MODIFIES = "modifies"


class TaxonomyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConceptLabel(TaxonomyModel):
    language_code: str = Field(min_length=2, max_length=35)
    label_type: ConceptLabelType
    label: str = Field(min_length=1, max_length=240)
    normalized_label: str | None = None

    @model_validator(mode="after")
    def set_normalized_label(self):
        normalized = normalize_concept_label(self.label)
        if not normalized:
            raise ValueError("concept label must contain visible text")
        if self.normalized_label is not None and self.normalized_label != normalized:
            raise ValueError("normalized_label must match deterministic normalization")
        self.normalized_label = normalized
        return self


class Concept(TaxonomyModel):
    concept_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._:-]{2,127}$")
    concept_type: ConceptType
    lifecycle_status: ConceptLifecycleStatus = ConceptLifecycleStatus.ACTIVE
    replaced_by_concept_id: str | None = None
    definition: str | None = None
    verification_status: ConceptVerificationStatus = ConceptVerificationStatus.UNKNOWN
    source_url: str | None = None
    source_locator: str | None = None
    labels: list[ConceptLabel] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_labels_and_lifecycle(self):
        preferred_languages: set[str] = set()
        seen_labels: set[tuple[str, str]] = set()
        for label in self.labels:
            key = (label.language_code.casefold(), label.normalized_label or "")
            if key in seen_labels:
                raise ValueError("duplicate normalized label within concept/language")
            seen_labels.add(key)
            if label.label_type == ConceptLabelType.PREF:
                language = label.language_code.casefold()
                if language in preferred_languages:
                    raise ValueError("only one preferred label is allowed per language")
                preferred_languages.add(language)

        if self.replaced_by_concept_id == self.concept_id:
            raise ValueError("a concept cannot replace itself")
        if self.lifecycle_status == ConceptLifecycleStatus.MERGED and not self.replaced_by_concept_id:
            raise ValueError("merged concepts require replaced_by_concept_id")
        if self.lifecycle_status != ConceptLifecycleStatus.MERGED and self.replaced_by_concept_id:
            raise ValueError("replaced_by_concept_id is reserved for merged concepts")
        return self


class ConceptRelation(TaxonomyModel):
    from_concept_id: str
    to_concept_id: str
    relation_type: ConceptRelationType
    verification_status: ConceptVerificationStatus = ConceptVerificationStatus.UNKNOWN
    source_url: str | None = None
    source_locator: str | None = None

    @model_validator(mode="after")
    def reject_self_relation(self):
        if self.from_concept_id == self.to_concept_id:
            raise ValueError("concept relations cannot point to self")
        return self


class RuleConceptReference(TaxonomyModel):
    rule_id: str
    node_type: RuleNodeType
    normalized_statement: str
    reference_kind: RuleConceptReferenceKind
    verification_status: ConceptVerificationStatus = ConceptVerificationStatus.UNKNOWN
    rule_set_id: str | None = None
    player_count: int | None = Field(default=None, ge=1)
    source_url: str | None = None
    source_locator: str | None = None


class ConceptGameBacklink(TaxonomyModel):
    game_id: str
    slug: str
    title: str | None = None
    usage_roles: list[GameConceptUsageRole] = Field(default_factory=list)
    rule_references: list[RuleConceptReference] = Field(default_factory=list)


class ConceptDetailResponse(TaxonomyModel):
    schema_version: Literal["1.0"] = CONCEPT_TAXONOMY_SCHEMA_VERSION
    concept: Concept
    relations: list[ConceptRelation] = Field(default_factory=list)
    game_backlinks: list[ConceptGameBacklink] = Field(default_factory=list)


class GameConceptReference(TaxonomyModel):
    concept_id: str
    concept_type: ConceptType
    usage_role: GameConceptUsageRole
    verification_status: ConceptVerificationStatus = ConceptVerificationStatus.UNKNOWN
    preferred_labels: dict[str, str] = Field(default_factory=dict)
    alternate_labels: dict[str, list[str]] = Field(default_factory=dict)
    definition: str | None = None
    related_concept_ids: list[str] = Field(default_factory=list)
    rule_references: list[RuleConceptReference] = Field(default_factory=list)


class GameConceptsReadResponse(TaxonomyModel):
    schema_version: Literal["1.0"] = CONCEPT_TAXONOMY_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    concepts: list[GameConceptReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_availability(self):
        if self.status == "not_available" and self.concepts:
            raise ValueError("not_available concept projections must be empty")
        return self


class GlossaryEntry(TaxonomyModel):
    concept_id: str
    label: str
    definition: str | None = None
    aliases: list[str] = Field(default_factory=list)
    related_concept_ids: list[str] = Field(default_factory=list)
    rule_references: list[RuleConceptReference] = Field(default_factory=list)


class GameGlossaryReadResponse(TaxonomyModel):
    schema_version: Literal["1.0"] = CONCEPT_TAXONOMY_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    language_code: str
    entries: list[GlossaryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_availability(self):
        if self.status == "not_available" and self.entries:
            raise ValueError("not_available glossary projections must be empty")
        return self


class LegacyConceptResolution(TaxonomyModel):
    resolved: dict[str, str] = Field(default_factory=dict)
    ambiguous: dict[str, list[str]] = Field(default_factory=dict)
    unresolved: list[str] = Field(default_factory=list)


def validate_relation_set(concepts: list[Concept], relations: list[ConceptRelation]) -> None:
    concept_ids = {concept.concept_id for concept in concepts}
    if len(concept_ids) != len(concepts):
        raise ValueError("duplicate concept_id")

    seen: set[tuple[str, str, ConceptRelationType]] = set()
    hierarchical_pairs: set[frozenset[str]] = set()
    related_pairs: set[frozenset[str]] = set()
    for relation in relations:
        if relation.from_concept_id not in concept_ids or relation.to_concept_id not in concept_ids:
            raise ValueError("concept relation references an unknown concept")
        key = (relation.from_concept_id, relation.to_concept_id, relation.relation_type)
        if key in seen:
            raise ValueError("duplicate concept relation")
        seen.add(key)
        pair = frozenset((relation.from_concept_id, relation.to_concept_id))
        if relation.relation_type in {ConceptRelationType.BROADER, ConceptRelationType.NARROWER}:
            hierarchical_pairs.add(pair)
        elif relation.relation_type == ConceptRelationType.RELATED:
            related_pairs.add(pair)

    if hierarchical_pairs & related_pairs:
        raise ValueError("related cannot overlap a broader/narrower pair")


def resolve_legacy_terms(
    terms: list[str],
    concepts: list[Concept],
    language_code: str | None = None,
) -> LegacyConceptResolution:
    index: dict[str, set[str]] = {}
    for concept in concepts:
        if concept.lifecycle_status == ConceptLifecycleStatus.MERGED:
            continue
        for label in concept.labels:
            if language_code and label.language_code.casefold() != language_code.casefold():
                continue
            key = label.normalized_label or normalize_concept_label(label.label)
            index.setdefault(key, set()).add(concept.concept_id)

    resolved: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    unresolved: list[str] = []
    for term in terms:
        matches = sorted(index.get(normalize_concept_label(term), set()))
        if len(matches) == 1:
            resolved[term] = matches[0]
        elif len(matches) > 1:
            ambiguous[term] = matches
        else:
            unresolved.append(term)
    return LegacyConceptResolution(resolved=resolved, ambiguous=ambiguous, unresolved=unresolved)
