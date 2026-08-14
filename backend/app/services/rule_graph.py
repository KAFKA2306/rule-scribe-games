import logging
from collections.abc import Iterable

import anyio

from app.core import supabase
from app.models.rule_graph import (
    RuleEdge,
    RuleGraphReadResponse,
    RuleNode,
    RuleNodeType,
)

logger = logging.getLogger("services.rule_graph")


class RuleGraphService:
    async def get_by_slug(
        self,
        slug: str,
        rule_types: Iterable[RuleNodeType] | None = None,
        rule_set_id: str | None = None,
    ) -> RuleGraphReadResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None

        base = {
            "game_id": str(game["id"]),
            "slug": str(game["slug"]),
            "work_id": str(game["work_id"]) if game.get("work_id") else None,
        }

        if supabase.is_local():
            return RuleGraphReadResponse(status="not_available", **base)

        try:
            graph = await anyio.to_thread.run_sync(self._load_graph, game, base, rule_set_id)
        except Exception as exc:
            # Deploying application code before the database migration must fail closed.
            logger.warning("Rule graph unavailable for %s: %s", slug, exc)
            graph = RuleGraphReadResponse(status="not_available", **base)

        if rule_types:
            return graph.select_types(set(rule_types))
        return graph

    @staticmethod
    def _load_graph(game: dict, base: dict, rule_set_id: str | None) -> RuleGraphReadResponse:
        client = supabase._get_client()

        if rule_set_id:
            rule_sets = (
                client.table("rule_sets")
                .select("*")
                .eq("game_id", game["id"])
                .eq("id", rule_set_id)
                .limit(1)
                .execute()
                .data
            )
        else:
            # Multiple simultaneously active RuleSets are valid after migration 013
            # (for example physical publisher rules + BGA implementation). Never
            # guess which truth boundary the caller intended.
            rule_sets = (
                client.table("rule_sets")
                .select("*")
                .eq("game_id", game["id"])
                .eq("is_active", True)
                .order("version", desc=True)
                .limit(2)
                .execute()
                .data
            )
            if len(rule_sets) > 1:
                logger.info("RuleSet selection required for game %s", game.get("slug"))
                return RuleGraphReadResponse(status="not_available", **base)

        if not rule_sets:
            return RuleGraphReadResponse(status="not_available", **base)

        rule_set = rule_sets[0]
        node_rows = (
            client.table("rule_nodes")
            .select("*")
            .eq("rule_set_id", rule_set["id"])
            .order("sequence")
            .execute()
            .data
        )
        edge_rows = (
            client.table("rule_edges")
            .select("*")
            .eq("rule_set_id", rule_set["id"])
            .order("sequence")
            .execute()
            .data
        )

        nodes = [
            RuleNode(
                rule_id=row["rule_id"],
                node_type=row["node_type"],
                normalized_statement=row["normalized_statement"],
                sequence=row.get("sequence"),
                phase_rule_id=row.get("phase_rule_id"),
                verification_status=row.get("verification_status", "unknown"),
                source_claim_ref=row.get("source_claim_ref"),
                evidence_ref=row.get("evidence_ref"),
                source_url=row.get("source_url"),
                source_locator=row.get("source_locator"),
                metadata=row.get("metadata") or {},
            )
            for row in node_rows
        ]
        edges = [
            RuleEdge(
                from_rule_id=row["from_rule_id"],
                to_rule_id=row["to_rule_id"],
                relation_type=row["relation_type"],
                sequence=row.get("sequence"),
                metadata=row.get("metadata") or {},
            )
            for row in edge_rows
        ]

        return RuleGraphReadResponse(
            status="available",
            rule_set_id=str(rule_set["id"]),
            edition_label=rule_set.get("edition_label"),
            language_code=rule_set.get("language_code"),
            source_revision=rule_set.get("source_revision"),
            nodes=nodes,
            edges=edges,
            **base,
        )
