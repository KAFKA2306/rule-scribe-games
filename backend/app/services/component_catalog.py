import logging
from collections import defaultdict

import anyio

from app.core import supabase
from app.models.component_catalog import (
    Ability,
    BooleanPropertyValue,
    Component,
    ComponentDetailResponse,
    ComponentListItem,
    ComponentListResponse,
    ComponentProperty,
    ComponentRefPropertyValue,
    ComponentSet,
    ComponentSetListResponse,
    ConceptRefPropertyValue,
    EnumPropertyValue,
    IntegerPropertyValue,
    NumberPropertyValue,
    PropertyDefinition,
    TextPropertyValue,
)

logger = logging.getLogger("services.component_catalog")


class ComponentCatalogService:
    async def get_sets(self, slug: str, rule_set_id: str) -> ComponentSetListResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"]), "ruleset_id": rule_set_id}
        if supabase.is_local():
            return ComponentSetListResponse(status="not_available", **base)
        try:
            return await anyio.to_thread.run_sync(self._load_sets, game, rule_set_id, base)
        except Exception as exc:
            logger.warning("Component catalog sets unavailable for %s/%s: %s", slug, rule_set_id, exc)
            return ComponentSetListResponse(status="not_available", **base)

    async def list_components(
        self,
        slug: str,
        rule_set_id: str,
        component_set_id: str | None = None,
        kind: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ComponentListResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {"game_id": str(game["id"]), "slug": str(game["slug"]), "ruleset_id": rule_set_id}
        if supabase.is_local():
            return ComponentListResponse(status="not_available", limit=limit, offset=offset, **base)
        try:
            return await anyio.to_thread.run_sync(
                self._load_component_list,
                game,
                rule_set_id,
                component_set_id,
                kind,
                limit,
                offset,
                base,
            )
        except Exception as exc:
            logger.warning("Component list unavailable for %s/%s: %s", slug, rule_set_id, exc)
            return ComponentListResponse(status="not_available", limit=limit, offset=offset, **base)

    async def get_component(self, slug: str, rule_set_id: str, component_id: str) -> ComponentDetailResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        if supabase.is_local():
            return None
        try:
            return await anyio.to_thread.run_sync(self._load_component_detail, game, rule_set_id, component_id)
        except Exception as exc:
            logger.warning("Component detail unavailable for %s/%s/%s: %s", slug, rule_set_id, component_id, exc)
            return None

    @staticmethod
    def _context(client, game: dict, rule_set_id: str) -> dict | None:
        rule_sets = (
            client.table("rule_sets")
            .select("id,game_id")
            .eq("id", rule_set_id)
            .eq("game_id", game["id"])
            .limit(1)
            .execute()
            .data
        )
        if not rule_sets:
            return None
        catalogs = client.table("component_catalogs").select("id").eq("rule_set_id", rule_set_id).limit(1).execute().data
        if not catalogs:
            return None
        return {"catalog_id": catalogs[0]["id"], "rule_set_id": rule_set_id}

    @classmethod
    def _load_sets(cls, game: dict, rule_set_id: str, base: dict) -> ComponentSetListResponse:
        client = supabase._get_client()
        context = cls._context(client, game, rule_set_id)
        if context is None:
            return ComponentSetListResponse(status="not_available", **base)
        set_rows = (
            client.table("component_sets")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .order("canonical_name")
            .execute()
            .data
        )
        definition_rows = (
            client.table("component_property_definitions")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .order("property_key")
            .execute()
            .data
        )
        return ComponentSetListResponse(
            status="available",
            component_sets=[cls._set_model(row) for row in set_rows],
            property_definitions=[cls._definition_model(row) for row in definition_rows],
            **base,
        )

    @classmethod
    def _load_component_list(
        cls,
        game: dict,
        rule_set_id: str,
        component_set_id: str | None,
        kind: str | None,
        limit: int,
        offset: int,
        base: dict,
    ) -> ComponentListResponse:
        client = supabase._get_client()
        context = cls._context(client, game, rule_set_id)
        if context is None:
            return ComponentListResponse(status="not_available", limit=limit, offset=offset, **base)
        query = client.table("components").select("*", count="exact").eq("rule_set_id", rule_set_id)
        if component_set_id:
            query = query.eq("component_set_id", component_set_id)
        if kind:
            query = query.eq("kind", kind)
        response = query.order("canonical_name").range(offset, offset + limit - 1).execute()
        items = [
            ComponentListItem(
                component_id=row["component_id"],
                component_set_id=row.get("component_set_id"),
                canonical_name=row["canonical_name"],
                kind=row["kind"],
                quantity=row.get("quantity"),
                verification_status=row.get("verification_status", "unknown"),
            )
            for row in response.data
        ]
        return ComponentListResponse(
            status="available",
            components=items,
            total=response.count if response.count is not None else len(items),
            limit=limit,
            offset=offset,
            **base,
        )

    @classmethod
    def _load_component_detail(cls, game: dict, rule_set_id: str, component_id: str) -> ComponentDetailResponse | None:
        client = supabase._get_client()
        context = cls._context(client, game, rule_set_id)
        if context is None:
            return None
        rows = (
            client.table("components")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .eq("component_id", component_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        row = rows[0]
        definitions = {
            item["property_key"]: cls._definition_model(item)
            for item in client.table("component_property_definitions").select("*").eq("rule_set_id", rule_set_id).execute().data
        }
        property_rows = (
            client.table("component_properties")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .eq("component_id", component_id)
            .order("property_key")
            .order("ordinal")
            .execute()
            .data
        )
        grouped: dict[str, list[dict]] = defaultdict(list)
        for prop_row in property_rows:
            grouped[prop_row["property_key"]].append(prop_row)
        properties: list[ComponentProperty] = []
        for property_key, values in grouped.items():
            definition = definitions[property_key]
            if definition.cardinality.value == "one" and len(values) != 1:
                raise ValueError(f"invalid cardinality for {property_key}")
            typed_values = [cls._property_value(value) for value in values]
            if any(value.value_type != definition.value_type.value for value in typed_values):
                raise ValueError(f"invalid property type for {property_key}")
            if definition.value_type.value == "enum" and any(value.value not in definition.enum_values for value in typed_values):
                raise ValueError(f"invalid enum value for {property_key}")
            source_ids = sorted({source for value in values for source in (value.get("source_ids") or [])})
            statuses = {value.get("verification_status", "unknown") for value in values}
            status = statuses.pop() if len(statuses) == 1 else "unknown"
            properties.append(
                ComponentProperty(
                    property_key=property_key,
                    values=typed_values,
                    verification_status=status,
                    source_ids=source_ids,
                )
            )

        abilities = cls._load_abilities(client, rule_set_id, component_id)
        concept_ids = [
            item["concept_id"]
            for item in client.table("component_concepts").select("concept_id").eq("rule_set_id", rule_set_id).eq("component_id", component_id).execute().data
        ]
        rule_ids = [
            item["rule_id"]
            for item in client.table("component_rule_nodes").select("rule_id").eq("rule_set_id", rule_set_id).eq("component_id", component_id).execute().data
        ]
        component = Component(
            component_id=row["component_id"],
            ruleset_id=rule_set_id,
            component_set_id=row.get("component_set_id"),
            canonical_name=row["canonical_name"],
            kind=row["kind"],
            quantity=row.get("quantity"),
            properties=properties,
            abilities=abilities,
            concept_ids=sorted(set(concept_ids)),
            rule_ids=sorted(set(rule_ids)),
            verification_status=row.get("verification_status", "unknown"),
            source_ids=row.get("source_ids") or [],
        )
        return ComponentDetailResponse(
            game_id=str(game["id"]),
            slug=str(game["slug"]),
            ruleset_id=rule_set_id,
            component=component,
        )

    @classmethod
    def _load_abilities(cls, client, rule_set_id: str, component_id: str) -> list[Ability]:
        rows = (
            client.table("component_abilities")
            .select("*")
            .eq("rule_set_id", rule_set_id)
            .eq("component_id", component_id)
            .order("ability_id")
            .execute()
            .data
        )
        abilities: list[Ability] = []
        for row in rows:
            concept_ids = [
                item["concept_id"]
                for item in client.table("component_ability_concepts").select("concept_id").eq("rule_set_id", rule_set_id).eq("ability_id", row["ability_id"]).execute().data
            ]
            rule_ids = [
                item["rule_id"]
                for item in client.table("component_ability_rule_nodes").select("rule_id").eq("rule_set_id", rule_set_id).eq("ability_id", row["ability_id"]).execute().data
            ]
            abilities.append(
                Ability(
                    ability_id=row["ability_id"],
                    printed_text=row.get("printed_text"),
                    normalized_label=row.get("normalized_label"),
                    concept_ids=sorted(set(concept_ids)),
                    rule_ids=sorted(set(rule_ids)),
                    verification_status=row.get("verification_status", "unknown"),
                    source_ids=row.get("source_ids") or [],
                )
            )
        return abilities

    @staticmethod
    def _set_model(row: dict) -> ComponentSet:
        return ComponentSet(
            component_set_id=row["component_set_id"],
            ruleset_id=str(row["rule_set_id"]),
            canonical_name=row["canonical_name"],
            kind=row.get("kind"),
            parent_component_set_id=row.get("parent_component_set_id"),
            verification_status=row.get("verification_status", "unknown"),
            source_ids=row.get("source_ids") or [],
        )

    @staticmethod
    def _definition_model(row: dict) -> PropertyDefinition:
        return PropertyDefinition(
            property_key=row["property_key"],
            labels=row.get("labels") or {},
            value_type=row["value_type"],
            cardinality=row.get("cardinality", "one"),
            unit=row.get("unit"),
            enum_values=row.get("enum_values") or [],
            filterable=row.get("filterable", False),
            sortable=row.get("sortable", False),
            verification_status=row.get("verification_status", "unknown"),
            source_ids=row.get("source_ids") or [],
        )

    @staticmethod
    def _property_value(row: dict):
        value_type = row["value_type"]
        if value_type == "text":
            return TextPropertyValue(value=row["text_value"])
        if value_type == "integer":
            return IntegerPropertyValue(value=row["integer_value"])
        if value_type == "number":
            return NumberPropertyValue(value=row["number_value"])
        if value_type == "boolean":
            return BooleanPropertyValue(value=row["boolean_value"])
        if value_type == "enum":
            return EnumPropertyValue(value=row["enum_value"])
        if value_type == "concept_ref":
            return ConceptRefPropertyValue(value=row["concept_ref_id"])
        if value_type == "component_ref":
            return ComponentRefPropertyValue(value=row["component_ref_id"])
        raise ValueError(f"unsupported component property value_type: {value_type}")
