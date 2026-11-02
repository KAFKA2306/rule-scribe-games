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
        # A glossary is a single read projection. Fetching every label, relation,
        # rule set and RuleNode separately caused dozens of serial HTTP requests
        # and production browser timeouts on a cold serverless invocation.
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

        concept_ids = sorted({link["concept_id"] for link in links})
        concept_rows = (
            client.table("concepts").select("*").in_("concept_id", concept_ids).execute().data
        )
        label_rows = (
            client.table("concept_labels")
            .select("concept_id,language_code,label_type,label,normalized_label")
            .in_("concept_id", concept_ids).execute().data
        )
        outgoing = (
            client.table("concept_relations").select("*")
            .in_("from_concept_id", concept_ids).execute().data
        )
        incoming = (
            client.table("concept_relations").select("*")
            .in_("to_concept_id", concept_ids).execute().data
        )

        concepts_by_id = {row["concept_id"]: row for row in concept_rows}
        labels_by_id: dict[str, list[ConceptLabel]] = {}
        for row in label_rows:
            labels_by_id.setdefault(row["concept_id"], []).append(
                ConceptLabel.model_validate({key: value for key, value in row.items() if key != "concept_id"})
            )
        relations_by_id = {
            str(row["id"]): row for row in [*outgoing, *incoming]
        }
        relations_by_concept: dict[str, list[ConceptRelation]] = {}
        for row in relations_by_id.values():
            relation = ConceptRelation(
                from_concept_id=row["from_concept_id"],
                to_concept_id=row["to_concept_id"],
                relation_type=row["relation_type"],
                verification_status=row.get("verification_status", "unknown"),
                source_url=row.get("source_url"),
                source_locator=row.get("source_locator"),
            )
            for concept_id in {relation.from_concept_id, relation.to_concept_id}:
                if concept_id in concepts_by_id:
                    relations_by_concept.setdefault(concept_id, []).append(relation)

        rule_set_id, rule_links_by_concept, nodes_by_id = cls._load_game_rule_nodes(
            client, str(game["id"]), concept_ids
        )

        references: list[GameConceptReference] = []
        for link in links:
            row = concepts_by_id.get(link["concept_id"])
            if row is None:
                continue
            concept = Concept(
                concept_id=row["concept_id"],
                concept_type=row["concept_type"],
                lifecycle_status=row.get("lifecycle_status", "active"),
                replaced_by_concept_id=row.get("replaced_by_concept_id"),
                definition=row.get("definition"),
                verification_status=row.get("verification_status", "unknown"),
                source_url=row.get("source_url"),
                source_locator=row.get("source_locator"),
                labels=labels_by_id.get(link["concept_id"], []),
            )
            preferred_labels = {
                label.language_code: label.label for label in concept.labels
                if label.label_type.value == "pref"
            }
            alternate_labels: dict[str, list[str]] = {}
            for label in concept.labels:
                if label.label_type.value == "alt":
                    alternate_labels.setdefault(label.language_code, []).append(label.label)
            related_ids = sorted({
                relation.to_concept_id
                if relation.from_concept_id == concept.concept_id
                else relation.from_concept_id
                for relation in relations_by_concept.get(concept.concept_id, [])
                if relation.relation_type.value == "related"
            })
            rule_references = cls._project_rule_references(
                rule_links_by_concept.get(concept.concept_id, []),
                nodes_by_id,
                rule_set_id,
            )
            references.append(
                GameConceptReference(
                    concept_id=concept.concept_id,
                    concept_type=concept.concept_type,
                    usage_role=link["usage_role"],
                    verification_status=link.get("verification_status", "unknown"),
                    preferred_labels=preferred_labels,
                    alternate_labels=alternate_labels,
                    definition=concept.definition,
                    related_concept_ids=related_ids,
                    rule_references=rule_references,
                )
            )
        if not references:
            return GameConceptsReadResponse(status="not_available", **base)
        return GameConceptsReadResponse(status="available", concepts=references, **base)

    @staticmethod
    def _load_game_rule_nodes(
        client, game_id: str, concept_ids: list[str]
    ) -> tuple[str | None, dict[str, list[dict]], dict[str, dict]]:
        rule_sets = (
            client.table("rule_sets").select("id")
            .eq("game_id", game_id).eq("is_active", True)
            .limit(1).execute().data
        )
        if not rule_sets:
            return None, {}, {}
        rule_set_id = str(rule_sets[0]["id"])
        rule_links = (
            client.table("rule_node_concepts")
            .select("concept_id,rule_id,reference_kind,verification_status")
            .eq("rule_set_id", rule_set_id)
            .in_("concept_id", concept_ids).execute().data
        )
        links_by_concept: dict[str, list[dict]] = {}
        for row in rule_links:
            links_by_concept.setdefault(row["concept_id"], []).append(row)
        rule_ids = sorted({row["rule_id"] for row in rule_links})
        if not rule_ids:
            return rule_set_id, links_by_concept, {}
        nodes = (
            client.table("rule_nodes")
            .select("rule_id,node_type,normalized_statement,source_url,source_locator,metadata")
            .eq("rule_set_id", rule_set_id)
            .in_("rule_id", rule_ids).execute().data
        )
        return rule_set_id, links_by_concept, {row["rule_id"]: row for row in nodes}

    @staticmethod
    def _project_rule_references(
        rule_links: list[dict],
        nodes_by_id: dict[str, dict],
        rule_set_id: str | None,
    ) -> list[RuleConceptReference]:
        references: list[RuleConceptReference] = []
        for rule_link in rule_links:
            node = nodes_by_id.get(rule_link["rule_id"])
            if node is None:
                continue
            metadata = node.get("metadata") or {}
            condition = metadata.get("condition") if isinstance(metadata, dict) else None
            player_count = condition.get("player_count") if isinstance(condition, dict) else None
            references.append(
                RuleConceptReference(
                    rule_id=node["rule_id"],
                    node_type=node["node_type"],
                    normalized_statement=node["normalized_statement"],
                    reference_kind=rule_link["reference_kind"],
                    verification_status=rule_link.get("verification_status", "unknown"),
                    rule_set_id=rule_set_id,
                    player_count=player_count
                    if isinstance(player_count, int) and not isinstance(player_count, bool)
                    else None,
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
        if not by_game:
            return []

        # The detail endpoint must not issue one game/rule query per backlink.
        games = (
            client.table("games")
            .select("id,slug,title")
            .in_("id", sorted(by_game))
            .execute()
            .data
        )
        if not games:
            return []
        game_ids = {str(game["id"]) for game in games}
        active_rule_sets = (
            client.table("rule_sets")
            .select("id,game_id")
            .in_("game_id", sorted(game_ids))
            .eq("is_active", True)
            .execute()
            .data
        )
        selected_rule_set_by_game: dict[str, str] = {}
        for row in active_rule_sets:
            game_id = str(row["game_id"])
            if game_id in game_ids:
                # Match the existing one-active-RuleSet-per-game projection.
                selected_rule_set_by_game.setdefault(game_id, str(row["id"]))

        rule_set_ids = sorted(set(selected_rule_set_by_game.values()))
        links_by_rule_set: dict[str, list[dict]] = {}
        nodes_by_rule_set: dict[str, dict[str, dict]] = {}
        if rule_set_ids:
            rule_links = (
                client.table("rule_node_concepts")
                .select("rule_set_id,rule_id,reference_kind,verification_status")
                .in_("rule_set_id", rule_set_ids)
                .eq("concept_id", concept_id)
                .execute()
                .data
            )
            for link in rule_links:
                links_by_rule_set.setdefault(str(link["rule_set_id"]), []).append(link)
            rule_ids = sorted({link["rule_id"] for link in rule_links})
            if rule_ids:
                nodes = (
                    client.table("rule_nodes")
                    .select("rule_set_id,rule_id,node_type,normalized_statement,source_url,source_locator,metadata")
                    .in_("rule_set_id", rule_set_ids)
                    .in_("rule_id", rule_ids)
                    .execute()
                    .data
                )
                for node in nodes:
                    nodes_by_rule_set.setdefault(str(node["rule_set_id"]), {})[node["rule_id"]] = node

        backlinks: list[ConceptGameBacklink] = []
        for game in games:
            game_id = str(game["id"])
            rule_set_id = selected_rule_set_by_game.get(game_id)
            rule_references = (
                cls._project_rule_references(
                    links_by_rule_set.get(rule_set_id, []),
                    nodes_by_rule_set.get(rule_set_id, {}),
                    rule_set_id,
                )
                if rule_set_id else []
            )
            backlinks.append(
                ConceptGameBacklink(
                    game_id=game_id,
                    slug=str(game["slug"]),
                    title=game.get("title"),
                    usage_roles=sorted(set(by_game[game_id])),
                    rule_references=rule_references,
                )
            )
        return sorted(backlinks, key=lambda item: item.slug)
