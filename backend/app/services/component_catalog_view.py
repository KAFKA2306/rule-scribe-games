import logging
from collections import defaultdict

import anyio

from app.core import supabase
from app.models.component_catalog import Ability, Component, ComponentProperty
from app.models.component_catalog_view import (
    AbilityEvidenceSummary,
    ComponentCatalogAvailabilityResponse,
    ComponentCatalogPageItem,
    ComponentCatalogPageResponse,
    FieldEvidenceSummary,
)
from app.services.component_catalog import ComponentCatalogService

logger = logging.getLogger("services.component_catalog_view")


class ComponentCatalogViewReadError(RuntimeError):
    """Raised when canonical component catalog data cannot be read safely."""


def _raw_property_value(row: dict):
    value_type = row["value_type"]
    column = {
        "text": "text_value",
        "integer": "integer_value",
        "number": "number_value",
        "boolean": "boolean_value",
        "enum": "enum_value",
        "concept_ref": "concept_ref_id",
        "component_ref": "component_ref_id",
    }.get(value_type)
    if column is None:
        return None
    return row.get(column)


def _claim_relations(claim: dict, bindings_by_claim: dict[str, list[dict]]) -> set[str]:
    return {row.get("relation") for row in bindings_by_claim.get(claim["claim_id"], [])}


def summarize_property_evidence(
    rows: list[dict],
    claims: list[dict],
    bindings_by_claim: dict[str, list[dict]],
) -> FieldEvidenceSummary:
    """Verify a property only when every current ordinal has accepted supporting evidence."""
    if not rows:
        return FieldEvidenceSummary()

    claim_ids: set[str] = set()
    source_ids: set[str] = set()
    all_verified = True
    any_contested = False

    for row in rows:
        current_value = _raw_property_value(row)
        ordinal = row["ordinal"]
        matching = [
            claim
            for claim in claims
            if claim.get("lifecycle_status") == "accepted"
            and claim.get("ordinal") == ordinal
            and (claim.get("normalized_payload") or {}).get("value") == current_value
        ]
        ordinal_verified = False
        for claim in matching:
            relations = _claim_relations(claim, bindings_by_claim)
            claim_ids.add(claim["claim_id"])
            if "contradicts" in relations:
                any_contested = True
            if "supports" in relations and "contradicts" not in relations:
                ordinal_verified = True
                source_ids.update(
                    str(binding["source_id"])
                    for binding in bindings_by_claim.get(claim["claim_id"], [])
                    if binding.get("relation") == "supports"
                )
        if not ordinal_verified:
            all_verified = False

    status = "contested" if any_contested else "verified" if all_verified else "unknown"
    return FieldEvidenceSummary(
        status=status,
        claim_ids=sorted(claim_ids),
        source_ids=sorted(source_ids),
    )


def summarize_ability_evidence(
    ability: dict,
    claims: list[dict],
    bindings_by_claim: dict[str, list[dict]],
) -> AbilityEvidenceSummary:
    def summary_for(target_type: str, expected_text: str | None) -> FieldEvidenceSummary:
        relevant = [
            claim
            for claim in claims
            if claim.get("target_type") == target_type and claim.get("lifecycle_status") == "accepted"
        ]
        if target_type == "ability_printed_text" and expected_text is not None:
            relevant = [
                claim for claim in relevant if (claim.get("normalized_payload") or {}).get("text") == expected_text
            ]
        claim_ids: set[str] = set()
        source_ids: set[str] = set()
        has_support = False
        has_contradiction = False
        for claim in relevant:
            relations = _claim_relations(claim, bindings_by_claim)
            claim_ids.add(claim["claim_id"])
            has_support = has_support or "supports" in relations
            has_contradiction = has_contradiction or "contradicts" in relations
            source_ids.update(
                str(binding["source_id"])
                for binding in bindings_by_claim.get(claim["claim_id"], [])
                if binding.get("relation") == "supports"
            )
        status = "contested" if has_contradiction else "verified" if has_support else "unknown"
        return FieldEvidenceSummary(status=status, claim_ids=sorted(claim_ids), source_ids=sorted(source_ids))

    return AbilityEvidenceSummary(
        printed_text=summary_for("ability_printed_text", ability.get("printed_text")),
        normalized=summary_for("ability_normalized", ability.get("normalized_label")),
    )


class ComponentCatalogViewService:
    async def get_availability(self, slug: str) -> ComponentCatalogAvailabilityResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"])}
        if supabase.is_local():
            return ComponentCatalogAvailabilityResponse(status="not_available", **base)
        try:
            return await anyio.to_thread.run_sync(self._load_availability, game, base)
        except Exception as exc:
            logger.exception("Component catalog availability read failed for %s", slug)
            raise ComponentCatalogViewReadError(f"component catalog availability backend failure for {slug}") from exc

    async def get_page(
        self,
        slug: str,
        rule_set_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        component_set_id: str | None = None,
        kind: str | None = None,
    ) -> ComponentCatalogPageResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"]), "rule_set_id": rule_set_id}
        if supabase.is_local():
            return ComponentCatalogPageResponse(status="not_available", limit=limit, offset=offset, **base)
        try:
            return await anyio.to_thread.run_sync(
                self._load_page,
                game,
                rule_set_id,
                limit,
                offset,
                component_set_id,
                kind,
                base,
            )
        except Exception as exc:
            logger.exception("Component catalog page read failed for %s/%s", slug, rule_set_id)
            raise ComponentCatalogViewReadError(f"component catalog page backend failure for {slug}/{rule_set_id}") from exc

    @staticmethod
    def _load_availability(game: dict, base: dict) -> ComponentCatalogAvailabilityResponse:
        client = supabase._get_client()
        rule_sets = client.table("rule_sets").select("id").eq("game_id", game["id"]).execute().data
        rule_set_ids = [str(row["id"]) for row in rule_sets]
        if not rule_set_ids:
            return ComponentCatalogAvailabilityResponse(status="not_available", **base)
        catalogs = (
            client.table("component_catalogs")
            .select("rule_set_id")
            .in_("rule_set_id", rule_set_ids)
            .execute()
            .data
        )
        available = sorted({str(row["rule_set_id"]) for row in catalogs})
        return ComponentCatalogAvailabilityResponse(
            status="available" if available else "not_available",
            rule_set_ids=available,
            **base,
        )

    @classmethod
    def _load_page(
        cls,
        game: dict,
        rule_set_id: str,
        limit: int,
        offset: int,
        component_set_id: str | None,
        kind: str | None,
        base: dict,
    ) -> ComponentCatalogPageResponse:
        client = supabase._get_client()
        context = ComponentCatalogService._context(client, game, rule_set_id)
        if context is None:
            return ComponentCatalogPageResponse(status="not_available", limit=limit, offset=offset, **base)

        sets = ComponentCatalogService._load_sets(game, rule_set_id, base)
        definitions = {item.property_key: item for item in sets.property_definitions}

        query = client.table("components").select("*", count="exact").eq("rule_set_id", rule_set_id)
        if component_set_id:
            query = query.eq("component_set_id", component_set_id)
        if kind:
            query = query.eq("kind", kind)
        response = query.order("canonical_name").range(offset, offset + limit - 1).execute()
        component_rows = response.data
        component_ids = [row["component_id"] for row in component_rows]
        if not component_ids:
            return ComponentCatalogPageResponse(
                status="available",
                component_sets=sets.component_sets,
                property_definitions=sets.property_definitions,
                total=response.count or 0,
                limit=limit,
                offset=offset,
                **base,
            )

        property_rows = (
            client.table("component_properties")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .in_("component_id", component_ids)
            .order("component_id")
            .order("property_key")
            .order("ordinal")
            .execute()
            .data
        )
        ability_rows = (
            client.table("component_abilities")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .in_("component_id", component_ids)
            .order("component_id")
            .order("ability_id")
            .execute()
            .data
        )
        concept_rows = (
            client.table("component_concepts")
            .select("component_id,concept_id")
            .eq("rule_set_id", rule_set_id)
            .in_("component_id", component_ids)
            .execute()
            .data
        )
        rule_rows = (
            client.table("component_rule_nodes")
            .select("component_id,rule_id")
            .eq("rule_set_id", rule_set_id)
            .in_("component_id", component_ids)
            .execute()
            .data
        )

        ability_ids = [row["ability_id"] for row in ability_rows]
        ability_concept_rows = []
        ability_rule_rows = []
        ability_claim_rows = []
        if ability_ids:
            ability_concept_rows = (
                client.table("component_ability_concepts")
                .select("ability_id,concept_id")
                .eq("rule_set_id", rule_set_id)
                .in_("ability_id", ability_ids)
                .execute()
                .data
            )
            ability_rule_rows = (
                client.table("component_ability_rule_nodes")
                .select("ability_id,rule_id")
                .eq("rule_set_id", rule_set_id)
                .in_("ability_id", ability_ids)
                .execute()
                .data
            )
            ability_claim_rows = (
                client.table("claims")
                .select("claim_id,ability_id,target_type,normalized_payload,lifecycle_status")
                .eq("rule_set_id", rule_set_id)
                .in_("ability_id", ability_ids)
                .execute()
                .data
            )

        property_claim_rows = (
            client.table("claims")
            .select("claim_id,component_id,property_key,ordinal,target_type,normalized_payload,lifecycle_status")
            .eq("rule_set_id", rule_set_id)
            .eq("target_type", "component_property")
            .in_("component_id", component_ids)
            .execute()
            .data
        )
        all_claim_rows = property_claim_rows + ability_claim_rows
        claim_ids = [row["claim_id"] for row in all_claim_rows]
        binding_rows = []
        if claim_ids:
            binding_rows = (
                client.table("evidence_bindings")
                .select("claim_id,source_id,relation")
                .in_("claim_id", claim_ids)
                .execute()
                .data
            )

        properties_by_component: dict[str, list[dict]] = defaultdict(list)
        property_rows_by_identity: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in property_rows:
            properties_by_component[row["component_id"]].append(row)
            property_rows_by_identity[(row["component_id"], row["property_key"])].append(row)

        abilities_by_component: dict[str, list[dict]] = defaultdict(list)
        for row in ability_rows:
            abilities_by_component[row["component_id"]].append(row)

        concepts_by_component: dict[str, set[str]] = defaultdict(set)
        for row in concept_rows:
            concepts_by_component[row["component_id"]].add(row["concept_id"])
        rules_by_component: dict[str, set[str]] = defaultdict(set)
        for row in rule_rows:
            rules_by_component[row["component_id"]].add(row["rule_id"])

        concepts_by_ability: dict[str, set[str]] = defaultdict(set)
        for row in ability_concept_rows:
            concepts_by_ability[row["ability_id"]].add(row["concept_id"])
        rules_by_ability: dict[str, set[str]] = defaultdict(set)
        for row in ability_rule_rows:
            rules_by_ability[row["ability_id"]].add(row["rule_id"])

        property_claims_by_identity: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in property_claim_rows:
            property_claims_by_identity[(row["component_id"], row["property_key"])].append(row)
        ability_claims_by_id: dict[str, list[dict]] = defaultdict(list)
        for row in ability_claim_rows:
            ability_claims_by_id[row["ability_id"]].append(row)
        bindings_by_claim: dict[str, list[dict]] = defaultdict(list)
        for row in binding_rows:
            bindings_by_claim[row["claim_id"]].append(row)

        items: list[ComponentCatalogPageItem] = []
        for component_row in component_rows:
            component_id = component_row["component_id"]
            grouped_properties: dict[str, list[dict]] = defaultdict(list)
            for row in properties_by_component[component_id]:
                grouped_properties[row["property_key"]].append(row)

            component_properties: list[ComponentProperty] = []
            property_evidence: dict[str, FieldEvidenceSummary] = {}
            for property_key, rows in grouped_properties.items():
                definition = definitions.get(property_key)
                if definition is None:
                    raise ValueError(f"missing property definition for {property_key}")
                typed_values = [ComponentCatalogService._property_value(row) for row in rows]
                if definition.cardinality.value == "one" and len(typed_values) != 1:
                    raise ValueError(f"invalid cardinality for {property_key}")
                if any(value.value_type != definition.value_type.value for value in typed_values):
                    raise ValueError(f"invalid property type for {property_key}")
                statuses = {row.get("verification_status", "unknown") for row in rows}
                source_ids = sorted({source for row in rows for source in (row.get("source_ids") or [])})
                component_properties.append(
                    ComponentProperty(
                        property_key=property_key,
                        values=typed_values,
                        verification_status=statuses.pop() if len(statuses) == 1 else "unknown",
                        source_ids=source_ids,
                    )
                )
                property_evidence[property_key] = summarize_property_evidence(
                    property_rows_by_identity[(component_id, property_key)],
                    property_claims_by_identity[(component_id, property_key)],
                    bindings_by_claim,
                )

            component_abilities: list[Ability] = []
            ability_evidence: dict[str, AbilityEvidenceSummary] = {}
            for row in abilities_by_component[component_id]:
                ability_id = row["ability_id"]
                component_abilities.append(
                    Ability(
                        ability_id=ability_id,
                        printed_text=row.get("printed_text"),
                        normalized_label=row.get("normalized_label"),
                        concept_ids=sorted(concepts_by_ability[ability_id]),
                        rule_ids=sorted(rules_by_ability[ability_id]),
                        verification_status=row.get("verification_status", "unknown"),
                        source_ids=row.get("source_ids") or [],
                    )
                )
                ability_evidence[ability_id] = summarize_ability_evidence(
                    row,
                    ability_claims_by_id[ability_id],
                    bindings_by_claim,
                )

            component = Component(
                component_id=component_id,
                ruleset_id=rule_set_id,
                component_set_id=component_row.get("component_set_id"),
                canonical_name=component_row["canonical_name"],
                kind=component_row["kind"],
                quantity=component_row.get("quantity"),
                properties=component_properties,
                abilities=component_abilities,
                concept_ids=sorted(concepts_by_component[component_id]),
                rule_ids=sorted(rules_by_component[component_id]),
                verification_status=component_row.get("verification_status", "unknown"),
                source_ids=component_row.get("source_ids") or [],
            )
            items.append(
                ComponentCatalogPageItem(
                    component=component,
                    property_evidence=property_evidence,
                    ability_evidence=ability_evidence,
                )
            )

        return ComponentCatalogPageResponse(
            status="available",
            component_sets=sets.component_sets,
            property_definitions=sets.property_definitions,
            items=items,
            total=response.count if response.count is not None else len(items),
            limit=limit,
            offset=offset,
            **base,
        )
