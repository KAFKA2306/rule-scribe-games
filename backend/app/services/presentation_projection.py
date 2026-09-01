import logging
from collections import defaultdict

from app.core import supabase
from app.core.read_retry import run_supabase_read_async
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


def accepted_supported_claim(claim: dict, bindings: list[dict]) -> dict | None:
    """Return projection evidence only when lifecycle and evidence gates both pass."""
    if claim.get("lifecycle_status") != "accepted":
        return None
    relations = {row.get("relation") for row in bindings}
    if "supports" not in relations or "contradicts" in relations:
        return None
    source_ids = sorted({str(row["source_id"]) for row in bindings if row.get("relation") == "supports"})
    if not source_ids:
        return None
    return {**claim, "source_ids": source_ids}


def project_rule_rows(rule_rows: list[dict], eligible_claims: dict[str, list[dict]]) -> list[ProjectedRule]:
    """Project only current, evidence-backed base RuleNodes; stale claims fail closed."""
    projected: list[ProjectedRule] = []
    for row in rule_rows:
        if row["node_type"] == "variant":
            continue
        candidates = eligible_claims.get(row["rule_id"], [])
        evidence = next(
            (
                candidate
                for candidate in candidates
                if (candidate.get("normalized_payload") or {}).get("statement") == row["normalized_statement"]
            ),
            None,
        )
        if evidence is None:
            continue
        projected.append(
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
    return projected


def projection_to_json_ld(projection: PresentationProjectionResponse, title: str) -> dict[str, object]:
    """Build JSON-LD from the canonical projection without introducing a second truth store."""
    data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Game",
        "name": title,
        "identifier": [
            {"@type": "PropertyValue", "propertyID": "slug", "value": projection.slug},
            {"@type": "PropertyValue", "propertyID": "ruleSet", "value": projection.rule_set_id},
        ],
    }
    if projection.quick_rules.status == ProjectionSectionStatus.AVAILABLE:
        data["subjectOf"] = [
            {
                "@type": "CreativeWork",
                "identifier": item.rule_id,
                "text": item.text,
            }
            for item in projection.quick_rules.items
        ]
    if projection.glossary.status == ProjectionSectionStatus.AVAILABLE:
        data["about"] = [
            {
                "@type": "DefinedTerm",
                "termCode": item.concept_id,
                "name": item.label,
                **({"description": item.definition} if item.definition else {}),
            }
            for item in projection.glossary.items
        ]
    return data


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
            return await run_supabase_read_async(
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
        projected_rules = project_rule_rows(rule_rows, eligible_claims)
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
            # Canonical misconception/advice layers do not exist yet. Keep these
            # sections unavailable instead of promoting compatibility presentation data.
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
    def _load_eligible_rule_claims(client, rule_set_id: str) -> dict[str, list[dict]]:
        claims = (
            client.table("claims")
            .select("claim_id,rule_id,normalized_payload,lifecycle_status")
            .eq("rule_set_id", rule_set_id)
            .eq("target_type", "rule_node")
            .order("claim_id")
            .execute()
            .data
        )
        if not claims:
            return {}

        claim_ids = [claim["claim_id"] for claim in claims]
        binding_rows = (
            client.table("evidence_bindings")
            .select("claim_id,source_id,relation")
            .in_("claim_id", claim_ids)
            .execute()
            .data
        )
        bindings_by_claim: dict[str, list[dict]] = defaultdict(list)
        for binding in binding_rows:
            claim_id = binding.get("claim_id")
            if claim_id:
                bindings_by_claim[str(claim_id)].append(binding)

        eligible: dict[str, list[dict]] = defaultdict(list)
        for claim in claims:
            evidence = accepted_supported_claim(
                claim,
                bindings_by_claim.get(str(claim["claim_id"]), []),
            )
            rule_id = claim.get("rule_id")
            if evidence is not None and rule_id:
                eligible[rule_id].append(evidence)
        return dict(eligible)

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
