import logging

from app.core import supabase
from app.core.read_retry import run_supabase_read_async
from app.models.concept_taxonomy import (
    Concept,
    ConceptDetailResponse,
    ConceptGameBacklink,
    ConceptLabel,
    ConceptRelation,
    GameConceptReference,
    GameConceptsReadResponse,
    GameGlossaryReadResponse,
    GlossaryEntry,
    RuleConceptReference,
)

logger = logging.getLogger("services.concept_taxonomy")


class ConceptTaxonomyReadError(RuntimeError):
    """Raised when canonical concept taxonomy data cannot be read safely."""


class ConceptTaxonomyService:
    async def get_concept(self, concept_id: str) -> ConceptDetailResponse | None:
        if supabase.is_local():
            return None
        try:
            return await run_supabase_read_async(self._load_concept, concept_id)
        except Exception as exc:
            logger.exception("Concept taxonomy read failed for %s", concept_id)
            raise ConceptTaxonomyReadError(f"concept taxonomy backend failure for {concept_id}") from exc

    async def get_by_game_slug(self, slug: str) -> GameConceptsReadResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"])}
        if supabase.is_local():
            return GameConceptsReadResponse(status="not_available", **base)
        try:
            return await run_supabase_read_async(self._load_game_concepts, game, base)
        except Exception as exc:
            logger.exception("Concept projection read failed for %s", slug)
            raise ConceptTaxonomyReadError(f"concept projection backend failure for {slug}") from exc

    async def get_glossary_by_game_slug(self, slug: str, language_code: str = "ja") -> GameGlossaryReadResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {
            "game_id": str(game["id"]),
            "slug": str(game["slug"]),
            "language_code": language_code,
        }
        if supabase.is_local():
            return GameGlossaryReadResponse(status="not_available", **base)
        try:
            concepts = await run_supabase_read_async(
                self._load_game_concepts,
                game,
                {"game_id": base["game_id"], "slug": base["slug"]},
            )
        except Exception as exc:
            logger.exception("Glossary projection read failed for %s", slug)
            raise ConceptTaxonomyReadError(f"glossary projection backend failure for {slug}") from exc

        entries: list[GlossaryEntry] = []
        for reference in concepts.concepts:
            if reference.usage_role.value not in {"core", "glossary"}:
                continue
            label = reference.preferred_labels.get(language_code)
            if not label:
                label = reference.preferred_labels.get("en")
            if not label and reference.preferred_labels:
                label = next(iter(reference.preferred_labels.values()))
            if not label:
                continue
            aliases = self._glossary_aliases(reference, language_code, label)
            entries.append(
                GlossaryEntry(
                    concept_id=reference.concept_id,
                    label=label,
                    definition=reference.definition,
                    aliases=aliases,
                    related_concept_ids=reference.related_concept_ids,
                    rule_references=reference.rule_references,
                )
            )
        if not entries:
            return GameGlossaryReadResponse(status="not_available", **base)
        return GameGlossaryReadResponse(status="available", entries=entries, **base)

    @staticmethod
    def _glossary_aliases(reference: GameConceptReference, language_code: str, label: str) -> list[str]:
        languages = [language_code]
        if language_code.lower() != "en":
            languages.append("en")

        aliases: list[str] = []
        for language in languages:
            preferred = reference.preferred_labels.get(language)
            if preferred and preferred != label and preferred not in aliases:
                aliases.append(preferred)
            for alternate in reference.alternate_labels.get(language, []):
                if alternate != label and alternate not in aliases:
                    aliases.append(alternate)
        return aliases

    @classmethod
    def _load_concept(cls, concept_id: str) -> ConceptDetailResponse | None:
        client = supabase._get_client()
        detail = cls._load_concept_core(client, concept_id)
        if detail is None:
            return None
        backlinks = cls._load_game_backlinks(client, concept_id)
        return detail.model_copy(update={"game_backlinks": backlinks})

    @classmethod
    def _load_concept_core(cls, client, concept_id: str) -> ConceptDetailResponse | None:
        rows = client.table("concepts").select("*").eq("concept_id", concept_id).limit(1).execute().data
        if not rows:
            return None
        row = rows[0]
        label_rows = (
            client.table("concept_labels")
            .select("language_code,label_type,label,normalized_label")
            .eq("concept_id", concept_id)
            .execute()
            .data
        )
        outgoing = (
            client.table("concept_relations")
            .select("*")
            .eq("from_concept_id", concept_id)
            .execute()
            .data
        )
        incoming = (
            client.table("concept_relations")
            .select("*")
            .eq("to_concept_id", concept_id)
            .execute()
            .data
        )
        relation_rows = {str(item["id"]): item for item in [*outgoing, *incoming]}.values()
        concept = Concept(
            concept_id=row["concept_id"],
            concept_type=row["concept_type"],
            lifecycle_status=row.get("lifecycle_status", "active"),
            replaced_by_concept_id=row.get("replaced_by_concept_id"),
            definition=row.get("definition"),
            verification_status=row.get("verification_status", "unknown"),
            source_url=row.get("source_url"),
            source_locator=row.get("source_locator"),
            labels=[ConceptLabel.model_validate(label) for label in label_rows],
        )
        relations = [
            ConceptRelation(
                from_concept_id=relation["from_concept_id"],
                to_concept_id=relation["to_concept_id"],
                relation_type=relation["relation_type"],
                verification_status=relation.get("verification_status", "unknown"),
                source_url=relation.get("source_url"),
                source_locator=relation.get("source_locator"),
            )
            for relation in relation_rows
        ]
        return ConceptDetailResponse(concept=concept, relations=relations)

    @classmethod
    def _load_game_concepts(cls, game: dict, base: dict) -> GameConceptsReadResponse:
        client = supabase._get_client()
        links = (
            client.table("game_concepts")
            .select("concept_id,usage_role,verification_status")
            .eq("game_id", game["id"])
            .execute()
            .data
        )
        if not links:
            return GameConceptsReadResponse(status="not_available", **base)

        references: list[GameConceptReference] = []
        for link in links:
            detail = cls._load_concept_core(client, link["concept_id"])
            if detail is None:
                continue
            preferred_labels = {
                label.language_code: label.label
                for label in detail.concept.labels
                if label.label_type.value == "pref"
            }
            alternate_labels: dict[str, list[str]] = {}
            for label in detail.concept.labels:
                if label.label_type.value == "alt":
                    alternate_labels.setdefault(label.language_code, []).append(label.label)
            related_ids = sorted(
                {
                    relation.to_concept_id if relation.from_concept_id == detail.concept.concept_id else relation.from_concept_id
                    for relation in detail.relations
                    if relation.relation_type.value == "related"
                }
            )
            rule_references = cls._load_rule_references(client, str(game["id"]), link["concept_id"])
            references.append(
                GameConceptReference(
                    concept_id=detail.concept.concept_id,
                    concept_type=detail.concept.concept_type,
                    usage_role=link["usage_role"],
                    verification_status=link.get("verification_status", "unknown"),
                    preferred_labels=preferred_labels,
                    alternate_labels=alternate_labels,
                    definition=detail.concept.definition,
                    related_concept_ids=related_ids,
                    rule_references=rule_references,
                )
            )
        if not references:
            return GameConceptsReadResponse(status="not_available", **base)
        return GameConceptsReadResponse(status="available", concepts=references, **base)

    @classmethod
    def _load_rule_references(cls, client, game_id: str, concept_id: str) -> list[RuleConceptReference]:
        rule_sets = (
            client.table("rule_sets")
            .select("id")
            .eq("game_id", game_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
            .data
        )
        if not rule_sets:
            return []
        rule_set_id = rule_sets[0]["id"]
        links = (
            client.table("rule_node_concepts")
            .select("rule_id,reference_kind,verification_status")
            .eq("rule_set_id", rule_set_id)
            .eq("concept_id", concept_id)
            .execute()
            .data
        )
        references: list[RuleConceptReference] = []
        for link in links:
            nodes = (
                client.table("rule_nodes")
                .select("rule_id,node_type,normalized_statement,source_url,source_locator,metadata")
                .eq("rule_set_id", rule_set_id)
                .eq("rule_id", link["rule_id"])
                .limit(1)
                .execute()
                .data
            )
            if not nodes:
                continue
            node = nodes[0]
            metadata = node.get("metadata") or {}
            condition = metadata.get("condition") if isinstance(metadata, dict) else None
            player_count = condition.get("player_count") if isinstance(condition, dict) else None
            references.append(
                RuleConceptReference(
                    rule_id=node["rule_id"],
                    node_type=node["node_type"],
                    normalized_statement=node["normalized_statement"],
                    reference_kind=link["reference_kind"],
                    verification_status=link.get("verification_status", "unknown"),
                    rule_set_id=str(rule_set_id),
                    player_count=player_count if isinstance(player_count, int) and not isinstance(player_count, bool) else None,
                    source_url=node.get("source_url"),
                    source_locator=node.get("source_locator"),
                )
            )
        return references

    @classmethod
    def _load_game_backlinks(cls, client, concept_id: str) -> list[ConceptGameBacklink]:
        links = (
            client.table("game_concepts")
            .select("game_id,usage_role")
            .eq("concept_id", concept_id)
            .execute()
            .data
        )
        by_game: dict[str, list[str]] = {}
        for link in links:
            by_game.setdefault(str(link["game_id"]), []).append(link["usage_role"])

        backlinks: list[ConceptGameBacklink] = []
        for game_id, usage_roles in by_game.items():
            games = client.table("games").select("id,slug,title").eq("id", game_id).limit(1).execute().data
            if not games:
                continue
            game = games[0]
            backlinks.append(
                ConceptGameBacklink(
                    game_id=str(game["id"]),
                    slug=str(game["slug"]),
                    title=game.get("title"),
                    usage_roles=sorted(set(usage_roles)),
                    rule_references=cls._load_rule_references(client, game_id, concept_id),
                )
            )
        return sorted(backlinks, key=lambda item: item.slug)
