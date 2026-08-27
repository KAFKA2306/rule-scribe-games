from collections import defaultdict
from typing import Any

from app.core import supabase

SUPPORTED_METADATA_FIELDS = {"min_players", "max_players", "play_time", "structured_data.mechanics"}


def project_metadata_evidence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach field-level metadata evidence without inferring trust from game-level state."""
    if not rows or supabase.is_local():
        return rows

    client = supabase._get_client()
    game_ids = [str(row["id"]) for row in rows if row.get("id")]
    if not game_ids:
        return rows

    ruleset_rows = (
        client.table("rule_sets")
        .select("id,game_id")
        .in_("game_id", game_ids)
        .eq("is_active", True)
        .eq("verification_status", "source_bound")
        .execute()
        .data
    )
    rulesets_by_game: dict[str, list[str]] = defaultdict(list)
    for item in ruleset_rows:
        rulesets_by_game[str(item["game_id"])].append(str(item["id"]))

    unique_rulesets = {
        game_id: ruleset_ids[0]
        for game_id, ruleset_ids in rulesets_by_game.items()
        if len(ruleset_ids) == 1
    }
    if not unique_rulesets:
        return rows

    ruleset_to_game = {ruleset_id: game_id for game_id, ruleset_id in unique_rulesets.items()}
    claim_rows = (
        client.table("claims")
        .select("claim_id,rule_set_id,field_path,normalized_payload")
        .in_("rule_set_id", list(ruleset_to_game))
        .eq("target_type", "game_metadata")
        .eq("lifecycle_status", "accepted")
        .execute()
        .data
    )
    claim_rows = [item for item in claim_rows if item.get("field_path") in SUPPORTED_METADATA_FIELDS]
    if not claim_rows:
        return rows

    claim_ids = [str(item["claim_id"]) for item in claim_rows]
    binding_rows = (
        client.table("evidence_bindings")
        .select("claim_id,source_id,relation")
        .in_("claim_id", claim_ids)
        .in_("relation", ["supports", "contradicts"])
        .execute()
        .data
    )

    relations_by_claim: dict[str, set[str]] = defaultdict(set)
    supporting_sources_by_claim: dict[str, set[str]] = defaultdict(set)
    for item in binding_rows:
        claim_id = str(item["claim_id"])
        relation = str(item["relation"])
        relations_by_claim[claim_id].add(relation)
        if relation == "supports":
            supporting_sources_by_claim[claim_id].add(str(item["source_id"]))

    eligible_claims: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_source_ids: set[str] = set()
    for claim in claim_rows:
        claim_id = str(claim["claim_id"])
        relations = relations_by_claim[claim_id]
        if "supports" not in relations or "contradicts" in relations:
            continue
        game_id = ruleset_to_game[str(claim["rule_set_id"])]
        field_path = str(claim["field_path"])
        sources = supporting_sources_by_claim[claim_id]
        all_source_ids.update(sources)
        eligible_claims[(game_id, field_path)].append(
            {
                "claim_id": claim_id,
                "payload": claim.get("normalized_payload") or {},
                "source_ids": sorted(sources),
            }
        )

    source_urls: dict[str, str | None] = {}
    if all_source_ids:
        source_rows = (
            client.table("evidence_sources")
            .select("source_id,url")
            .in_("source_id", sorted(all_source_ids))
            .execute()
            .data
        )
        source_urls = {str(item["source_id"]): item.get("url") for item in source_rows}

    projected: list[dict[str, Any]] = []
    for row in rows:
        game_id = str(row.get("id") or "")
        metadata_evidence: dict[str, Any] = {}
        for field_path in sorted(SUPPORTED_METADATA_FIELDS):
            candidates = eligible_claims.get((game_id, field_path), [])
            if len(candidates) != 1:
                continue
            candidate = candidates[0]
            source_ids = candidate["source_ids"]
            metadata_evidence[field_path] = {
                "status": "supported",
                "claim_id": candidate["claim_id"],
                "payload": candidate["payload"],
                "sources": [
                    {"source_id": source_id, "url": source_urls.get(source_id)}
                    for source_id in source_ids
                ],
            }
        projected.append({**row, "metadata_evidence": metadata_evidence})
    return projected
