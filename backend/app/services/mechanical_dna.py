import logging

import anyio

from app.core import supabase
from app.models.mechanical_dna import (
    HierarchyMatch,
    MechanicalDNAConnection,
    MechanicalDNAResponse,
    SharedConcept,
)

logger = logging.getLogger("services.mechanical_dna")

ACCEPTED_VERIFICATION = {"source_bound", "verified"}
HIERARCHICAL_RELATIONS = {"broader", "narrower"}


def jaccard_score(source_ids: set[str], candidate_ids: set[str]) -> float:
    if not source_ids or not candidate_ids:
        return 0.0
    union = source_ids | candidate_ids
    if not union:
        return 0.0
    return len(source_ids & candidate_ids) / len(union)


def invert_hierarchy(relation_type: str) -> str:
    return "narrower" if relation_type == "broader" else "broader"


class MechanicalDNAService:
    async def get_connections(self, slug: str, *, limit: int = 8) -> MechanicalDNAResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"])}
        if supabase.is_local():
            return MechanicalDNAResponse(status="not_available", **base)
        try:
            return await anyio.to_thread.run_sync(self._load_connections, game, base, limit)
        except Exception as exc:
            logger.warning("Mechanical DNA unavailable for %s: %s", slug, exc)
            return MechanicalDNAResponse(status="not_available", **base)

    @classmethod
    def _load_connections(cls, game: dict, base: dict, limit: int) -> MechanicalDNAResponse:
        client = supabase._get_client()
        source_links = (
            client.table("game_concepts")
            .select("concept_id,verification_status")
            .eq("game_id", game["id"])
            .execute()
            .data
        )
        source_ids = {
            str(link["concept_id"])
            for link in source_links
            if link.get("verification_status") in ACCEPTED_VERIFICATION
        }
        if not source_ids:
            return MechanicalDNAResponse(status="not_available", **base)

        hierarchy_neighbors = cls._load_hierarchy_neighbors(client, source_ids)
        search_ids = source_ids | {
            neighbor_id
            for neighbors in hierarchy_neighbors.values()
            for neighbor_id, _relation_type in neighbors
        }

        overlapping_links = (
            client.table("game_concepts")
            .select("game_id,concept_id,verification_status")
            .in_("concept_id", sorted(search_ids))
            .execute()
            .data
        )
        candidate_ids = sorted(
            {
                str(link["game_id"])
                for link in overlapping_links
                if str(link["game_id"]) != str(game["id"])
                and link.get("verification_status") in ACCEPTED_VERIFICATION
            }
        )
        if not candidate_ids:
            return MechanicalDNAResponse(status="available", **base)

        all_candidate_links = (
            client.table("game_concepts")
            .select("game_id,concept_id,verification_status")
            .in_("game_id", candidate_ids)
            .execute()
            .data
        )
        candidate_concepts: dict[str, set[str]] = {game_id: set() for game_id in candidate_ids}
        for link in all_candidate_links:
            if link.get("verification_status") not in ACCEPTED_VERIFICATION:
                continue
            candidate_concepts.setdefault(str(link["game_id"]), set()).add(str(link["concept_id"]))

        game_rows = (
            client.table("games")
            .select("id,slug,title,image_url")
            .in_("id", candidate_ids)
            .execute()
            .data
        )
        games_by_id = {str(row["id"]): row for row in game_rows}
        labels = cls._load_preferred_labels(client, source_ids)

        unranked: list[dict] = []
        for candidate_id in candidate_ids:
            candidate_ids_set = candidate_concepts.get(candidate_id, set())
            shared_ids = sorted(source_ids & candidate_ids_set)
            hierarchy_matches = cls._hierarchy_matches(hierarchy_neighbors, candidate_ids_set)
            if not shared_ids and not hierarchy_matches:
                continue
            row = games_by_id.get(candidate_id)
            if not row:
                continue
            score = round(jaccard_score(source_ids, candidate_ids_set), 6)
            unranked.append(
                {
                    "game_id": candidate_id,
                    "slug": str(row["slug"]),
                    "title": row.get("title"),
                    "image_url": row.get("image_url"),
                    "similarity_score": score,
                    "shared_concept_ids": shared_ids,
                    "shared_concepts": [
                        SharedConcept(
                            concept_id=concept_id,
                            label=labels.get(concept_id, {}).get("label"),
                            language_code=labels.get(concept_id, {}).get("language_code"),
                        )
                        for concept_id in shared_ids
                    ],
                    "hierarchy_matches": hierarchy_matches,
                }
            )

        unranked.sort(
            key=lambda item: (
                -item["similarity_score"],
                -len(item["shared_concept_ids"]),
                item["slug"],
            )
        )
        connections = [
            MechanicalDNAConnection(rank=index, **item)
            for index, item in enumerate(unranked[:limit], start=1)
        ]
        return MechanicalDNAResponse(status="available", connections=connections, **base)

    @staticmethod
    def _load_hierarchy_neighbors(client, source_ids: set[str]) -> dict[str, list[tuple[str, str]]]:
        outgoing = (
            client.table("concept_relations")
            .select("from_concept_id,to_concept_id,relation_type,verification_status")
            .in_("from_concept_id", sorted(source_ids))
            .execute()
            .data
        )
        incoming = (
            client.table("concept_relations")
            .select("from_concept_id,to_concept_id,relation_type,verification_status")
            .in_("to_concept_id", sorted(source_ids))
            .execute()
            .data
        )
        neighbors: dict[str, set[tuple[str, str]]] = {concept_id: set() for concept_id in source_ids}
        for row in outgoing:
            relation_type = row.get("relation_type")
            if relation_type not in HIERARCHICAL_RELATIONS or row.get("verification_status") not in ACCEPTED_VERIFICATION:
                continue
            source_id = str(row["from_concept_id"])
            neighbors.setdefault(source_id, set()).add((str(row["to_concept_id"]), relation_type))
        for row in incoming:
            relation_type = row.get("relation_type")
            if relation_type not in HIERARCHICAL_RELATIONS or row.get("verification_status") not in ACCEPTED_VERIFICATION:
                continue
            source_id = str(row["to_concept_id"])
            neighbors.setdefault(source_id, set()).add(
                (str(row["from_concept_id"]), invert_hierarchy(relation_type))
            )
        return {concept_id: sorted(values) for concept_id, values in neighbors.items()}

    @staticmethod
    def _hierarchy_matches(
        hierarchy_neighbors: dict[str, list[tuple[str, str]]], candidate_ids: set[str]
    ) -> list[HierarchyMatch]:
        matches: list[HierarchyMatch] = []
        for source_id, neighbors in hierarchy_neighbors.items():
            for candidate_id, relation_type in neighbors:
                if candidate_id in candidate_ids:
                    matches.append(
                        HierarchyMatch(
                            source_concept_id=source_id,
                            candidate_concept_id=candidate_id,
                            relation_type=relation_type,
                        )
                    )
        return sorted(
            matches,
            key=lambda item: (item.source_concept_id, item.candidate_concept_id, item.relation_type),
        )

    @staticmethod
    def _load_preferred_labels(client, concept_ids: set[str]) -> dict[str, dict[str, str]]:
        rows = (
            client.table("concept_labels")
            .select("concept_id,language_code,label")
            .in_("concept_id", sorted(concept_ids))
            .eq("label_type", "pref")
            .execute()
            .data
        )
        grouped: dict[str, dict[str, str]] = {}
        for row in rows:
            concept_id = str(row["concept_id"])
            language_code = str(row["language_code"])
            current = grouped.get(concept_id)
            if current is None or language_code == "ja" or (current["language_code"] != "ja" and language_code == "en"):
                grouped[concept_id] = {"label": str(row["label"]), "language_code": language_code}
        return grouped
