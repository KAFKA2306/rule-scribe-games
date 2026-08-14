from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RULE_GRAPH_SCHEMA_VERSION = "1.0"


class RuleNodeType(StrEnum):
    PHASE = "phase"
    TURN = "turn"
    ACTION = "action"
    CONDITION = "condition"
    EFFECT = "effect"
    SETUP = "setup"
    SCORING = "scoring"
    ROUND_END = "round_end"
    GAME_END = "game_end"
    VICTORY = "victory"
    EXCEPTION = "exception"
    TARGETING = "targeting"
    CONFLICT_RESOLUTION = "conflict_resolution"
    VARIANT = "variant"


class RuleRelationType(StrEnum):
    CONTAINS = "contains"
    NEXT = "next"
    CONDITION_EFFECT = "condition_effect"
    RESULTS_IN = "results_in"
    OVERRIDES = "overrides"
    TARGETS = "targets"
    VARIANT_OF = "variant_of"
    REQUIRES = "requires"


class RuleVerificationStatus(StrEnum):
    UNKNOWN = "unknown"
    UNVERIFIED = "unverified"
    SOURCE_BOUND = "source_bound"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RuleGraphSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuleNode(RuleGraphSchema):
    rule_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._:-]{2,127}$")
    node_type: RuleNodeType
    normalized_statement: str = Field(min_length=1)
    sequence: int | None = Field(default=None, ge=0)
    phase_rule_id: str | None = None
    verification_status: RuleVerificationStatus = RuleVerificationStatus.UNKNOWN
    source_claim_ref: str | None = None
    evidence_ref: str | None = None
    source_url: str | None = None
    source_locator: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleEdge(RuleGraphSchema):
    from_rule_id: str
    to_rule_id: str
    relation_type: RuleRelationType
    sequence: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleGraphReadResponse(RuleGraphSchema):
    schema_version: Literal["1.0"] = RULE_GRAPH_SCHEMA_VERSION
    status: Literal["available", "not_available"]
    game_id: str
    slug: str
    work_id: str | None = None
    edition_label: str | None = None
    language_code: str | None = None
    source_revision: str | None = None
    rule_set_id: str | None = None
    nodes: list[RuleNode] = Field(default_factory=list)
    edges: list[RuleEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self):
        if self.status == "not_available":
            if self.rule_set_id is not None or self.nodes or self.edges:
                raise ValueError("not_available rule graphs must not contain canonical rules")
            return self

        if self.rule_set_id is None:
            raise ValueError("available rule graphs require rule_set_id")

        node_by_id: dict[str, RuleNode] = {}
        for node in self.nodes:
            if node.rule_id in node_by_id:
                raise ValueError(f"duplicate rule_id: {node.rule_id}")
            node_by_id[node.rule_id] = node

        for edge in self.edges:
            if edge.from_rule_id not in node_by_id or edge.to_rule_id not in node_by_id:
                raise ValueError("rule edge references an unknown node")
            if edge.relation_type == RuleRelationType.CONDITION_EFFECT:
                if node_by_id[edge.from_rule_id].node_type != RuleNodeType.CONDITION:
                    raise ValueError("condition_effect must originate from a condition node")
                if node_by_id[edge.to_rule_id].node_type != RuleNodeType.EFFECT:
                    raise ValueError("condition_effect must point to an effect node")

        return self

    def select_types(self, rule_types: set[RuleNodeType]) -> "RuleGraphReadResponse":
        if not rule_types or self.status == "not_available":
            return self

        selected = [node for node in self.nodes if node.node_type in rule_types]
        selected_ids = {node.rule_id for node in selected}
        selected_edges = [
            edge for edge in self.edges
            if edge.from_rule_id in selected_ids and edge.to_rule_id in selected_ids
        ]
        return self.model_copy(update={"nodes": selected, "edges": selected_edges})
