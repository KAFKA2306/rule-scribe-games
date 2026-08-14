import logging
from collections import defaultdict

import anyio

from app.core import supabase
from app.models.presentation_projection import (
    GlossaryProjectionSection,
    PresentationProjectionResponse,
    ProjectedGlossaryEntry,
    ProjectedRule,
    ProjectionEvidence,
    ProjectionSectionKind,
    ProjectionSectionStatus,
    RuleProjectionSection,
)

logger = logging.getLogger("services.presentation_projection")

_SETUP_TYPES = {"setup"}
_GAME_FLOW_TYPES = {
    "phase",
    "turn",
    "action",
    "condition",
    "effect",
    "round_end",
    "exception",
    "targeting",
    "conflict_resolution",
}
_END_TYPES = {"game_end", "victory"}
_SCORING_TYPES = {"scoring"}
# Variant rules are deliberately excluded from base presentation until a caller
# selects an explicit variant/derived RuleSet. Never blend optional rules into base truth.
_QUICK_RULE_TYPES = _SETUP_TYPES | _GAME_FLOW_TYPES | _END_TYPES | _SCORING_TYPES


class PresentationProjectionReadError(RuntimeError):
    """Raised when canonical projection inputs cannot be read safely."""


class PresentationProjectionService:
    async def get_by_slug(
        self,
        slug: str,
        rule_set_id: str,
        language_code: str = "ja",
    ) -> PresentationProjectionResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        if supabase.is_local():
            return self._empty_response(game, rule_set_id, language_code)
        try:
            return await anyio.to_thread.run_sync(
                self._load_projection,
                game,
                rule_set_id,
                language_code,
            )
        except Exception as exc:
            logger.exception("Presentation projection read failed for %s/%s", slug, rule_set_id)
            raise PresentationProjectionReadError(
                f"presentation projection backend failure for {slug}/{rule_set_id}"
            ) from exc

    @staticmethod
    def _empty_rule_section(kind: ProjectionSectionKind) -> RuleProjectionSection:
        return RuleProjectionSection(kind=kind, status=ProjectionSectionStatus.NOT_AVAILABLE)

    @classmethod
    def _empty_response(cls, game: dict, rule_set_id: str, language_code: str) -> PresentationProjectionResponse:
        return PresentationProjectionResponse(
            status="not_available",
            game_id=str(game["id"]),
            slug=str(game["slug"]),
            rule_set_id=rule_set_id,
            language_code=language_code,
            synopsis=cls._empty_rule_section(ProjectionSectionKind.SYNOPSIS),
            quick_rules=cls._empty_rule_section(ProjectionSectionKind.QUICK_RULES),
            setup=cls._empty_rule_section(ProjectionSectionKind.SETUP),
            game_flow=cls._empty_rule_section(ProjectionSectionKind.GAME_FLOW),
            end_condition=cls._empty_rule_section(ProjectionSectionKind.END_CONDITION),
            scoring=cls._empty_rule_section(ProjectionSectionKind.SCORING),
            glossary=GlossaryProjectionSection(status=ProjectionSectionStatus.NOT_AVAILABLE),
            common_errors=cls._empty_rule_section(ProjectionSectionKind.COMMON_ERRORS),
            pro_tips=cls._empty_rule_section(ProjectionSectionKind.PRO_TIPS),
        )

    @classmethod
    def _load_projection(cls, game: dict, rule_set_id: str, language_code: str) -> PresentationProjectionResponse:
        client = supabase._get_client()
        rule_sets = (
            client.table("rule_sets")
            .select("id")
            .eq("id", rule_set_id)
            .eq("game_id", game["id"])
            .limit(1)
            .execute()
            .data
        )
        if not rule_sets:
            return cls._empty_response(game, rule_set_id, language_code)

        rule_rows = (
            client.table("rule_nodes")
            .select("rule_id,node_type,normalized_statement,sequence")
            .eq("rule_set_id", rule_set_id)
            .order("sequence")
            .execute()
            .data
        )
        eligible_claims = cls._load_eligible_rule_claims(client, rule_set_id)
        projected_rules: list[ProjectedRule] = []
        for row in rule_rows:
            if row["node_type"] == "variant":
                continue
            evidence = eligible_claims.get(row["rule_id"])
            if evidence is None:
                continue
            claim_statement = evidence["normalized_payload"].get("statement")
            if claim_statement != row["normalized_statement"]:
                # Evidence for a stale statement must not verify a newly edited RuleNode.
                continue
            projected_rules.append(
                ProjectedRule(
                    rule_id=row["rule_id"],
                    node_type=row["node_type"],
                    text=row["normalized_statement"],
                    sequence=row.get("sequence"),
                    evidence=ProjectionEvidence(
                        claim_id=evidence["claim_id"],
                        source_ids=evidence["source_ids"],
                    ),
                )
            )

        glossary_items = cls._load_glossary(client, str(game["id"]), rule_set_id, language_code)

        quick_rules = [item for item in projected_rules if item.node_type in _QUICK_RULE_TYPES]
        setup = [item for item in projected_rules if item.node_type in _SETUP_TYPES]
        game_flow = [item for item in projected_rules if item.node_type in _GAME_FLOW_TYPES]
        end_condition = [item for item in projected_rules if item.node_type in _END_TYPES]
        scoring = [item for item in projected_rules if item.node_type in _SCORING_TYPES]

        sections = {
            "synopsis": cls._empty_rule_section(ProjectionSectionKind.SYNOPSIS),
            "quick_rules": cls._rule_section(ProjectionSectionKind.QUICK_RULES, quick_rules),
            "setup": cls._rule_section(ProjectionSectionKind.SETUP, setup),
            "game_flow": cls._rule_section(ProjectionSectionKind.GAME_FLOW, game_flow),
            "end_condition": cls._rule_section(ProjectionSectionKind.END_CONDITION, end_condition),
            "scoring": cls._rule_section(ProjectionSectionKind.SCORING, scoring),
            "glossary": GlossaryProjectionSection(
                status=(ProjectionSectionStatus.AVAILABLE if glossary_items else ProjectionSectionStatus.NOT_AVAILABLE),
                items=glossary_items,
            ),
            # No canonical Misconception/Advice layer exists yet. Do not read legacy
            # structured_data.rule_mistakes/pro_tips as a second truth source.
            "common_errors": cls._empty_rule_section(ProjectionSectionKind.COMMON_ERRORS),
            "pro_tips": cls._empty_rule_section(ProjectionSectionKind.PRO_TIPS),
        }
        status = "available" if any(
            section.status == ProjectionSectionStatus.AVAILABLE for section in sections.values()
        ) else "not_available"
        return PresentationProjectionResponse(
            status=status,
            game_id=str(game["id"]),
            slug=str(game["slug"]),
            rule_set_id=rule_set_id,
            language_code=language_code,
            **sections,
        )

    @staticmethod
    def _rule_section(kind: ProjectionSectionKind, items: list[ProjectedRule]) -> RuleProjectionSection:
        return RuleProjectionSection(
            kind=kind,
            status=(ProjectionSectionStatus.AVAILABLE if items else ProjectionSectionStatus.NOT_AVAILABLE),
            items=items,
        )

    @staticmethod
    def _load_eligible_rule_claims(client, rule_set_id: str) -> dict[str, dict]:
        claims = (
            client.table("claims")
            .select("claim_id,rule_id,normalized_payload")
            .eq("rule_set_id", rule_set_id)
            .eq("target_type", "rule_node")
            .eq("lifecycle_status", "accepted")
            .order("claim_id")
            .execute()
            .data
        )
        eligible: dict[str, dict] = {}
        for claim in claims:
            bindings = (
                client.table("evidence_bindings")
                .select("source_id,relation")
                .eq("claim_id", claim["claim_id"])
                .execute()
                .data
            )
            relations = {row["relation"] for row in bindings}
            if "supports" not in relations or "contradicts" in relations:
                continue
            source_ids = sorted({row["source_id"] for row in bindings if row["relation"] == "supports"})
            if not source_ids:
                continue
            rule_id = claim.get("rule_id")
            if rule_id and rule_id not in eligible:
                eligible[rule_id] = {**claim, "source_ids": source_ids}
        return eligible

    @staticmethod
    def _load_glossary(client, game_id: str, rule_set_id: str, language_code: str) -> list[ProjectedGlossaryEntry]:
        rule_links = (
            client.table("rule_node_concepts")
            .select("rule_id,concept_id,verification_status")
            .eq("rule_set_id", rule_set_id)
            .eq("verification_status", "verified")
            .execute()
            .data
        )
        rule_ids_by_concept: dict[str, set[str]] = defaultdict(set)
        for link in rule_links:
            rule_ids_by_concept[link["concept_id"]].add(link["rule_id"])
        if not rule_ids_by_concept:
            return []

        game_links = (
            client.table("game_concepts")
            .select("concept_id,usage_role,verification_status")
            .eq("game_id", game_id)
            .eq("verification_status", "verified")
            .execute()
            .data
        )
        allowed_game_concepts = {
            row["concept_id"]
            for row in game_links
            if row["usage_role"] in {"core", "glossary"}
        }
        concept_ids = sorted(set(rule_ids_by_concept) & allowed_game_concepts)
        items: list[ProjectedGlossaryEntry] = []
        for concept_id in concept_ids:
            concept_rows = (
                client.table("concepts")
                .select("concept_id,definition,lifecycle_status,verification_status")
                .eq("concept_id", concept_id)
                .eq("lifecycle_status", "active")
                .eq("verification_status", "verified")
                .limit(1)
                .execute()
                .data
            )
            if not concept_rows:
                continue
            labels = (
                client.table("concept_labels")
                .select("language_code,label_type,label")
                .eq("concept_id", concept_id)
                .execute()
                .data
            )
            preferred = next(
                (row["label"] for row in labels if row["language_code"] == language_code and row["label_type"] == "pref"),
                None,
            )
            if preferred is None:
                preferred = next(
                    (row["label"] for row in labels if row["language_code"] == "en" and row["label_type"] == "pref"),
                    None,
                )
            if preferred is None:
                continue
            aliases = sorted(
                row["label"]
                for row in labels
                if row["language_code"] == language_code and row["label_type"] == "alt"
            )
            relations = (
                client.table("concept_relations")
                .select("from_concept_id,to_concept_id,relation_type,verification_status")
                .eq("verification_status", "verified")
                .execute()
                .data
            )
            related = sorted(
                {
                    row["to_concept_id"] if row["from_concept_id"] == concept_id else row["from_concept_id"]
                    for row in relations
                    if row["relation_type"] == "related"
                    and concept_id in {row["from_concept_id"], row["to_concept_id"]}
                }
            )
            items.append(
                ProjectedGlossaryEntry(
                    concept_id=concept_id,
                    label=preferred,
                    definition=concept_rows[0].get("definition"),
                    aliases=aliases,
                    related_concept_ids=related,
                    rule_ids=sorted(rule_ids_by_concept[concept_id]),
                )
            )
        return items
