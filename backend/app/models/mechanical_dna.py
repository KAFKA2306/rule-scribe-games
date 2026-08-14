from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MECHANICAL_DNA_SCHEMA_VERSION = "1.0"
MECHANICAL_DNA_ALGORITHM_VERSION = "mechanical-dna-concept-v1"


class MechanicalDNAModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SharedConcept(MechanicalDNAModel):
    concept_id: str
    label: str | None = None
    language_code: str | None = None


class HierarchyMatch(MechanicalDNAModel):
    source_concept_id: str
    candidate_concept_id: str
    relation_type: Literal["broader", "narrower"]


class MechanicalDNAConnection(MechanicalDNAModel):
    game_id: str
    slug: str
    title: str | None = None
    image_url: str | None = None
    rank: int = Field(ge=1)
    similarity_score: float = Field(ge=0.0, le=1.0)
    shared_concept_ids: list[str] = Field(default_factory=list)
    shared_concepts: list[SharedConcept] = Field(default_factory=list)
    hierarchy_matches: list[HierarchyMatch] = Field(default_factory=list)


class MechanicalDNAResponse(MechanicalDNAModel):
    schema_version: Literal["1.0"] = MECHANICAL_DNA_SCHEMA_VERSION
    algorithm_version: Literal["mechanical-dna-concept-v1"] = MECHANICAL_DNA_ALGORITHM_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    connections: list[MechanicalDNAConnection] = Field(default_factory=list)
