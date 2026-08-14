import logging

import anyio

from app.core import supabase
from app.models.evidence import (
    Claim,
    ClaimDetailResponse,
    ClaimTarget,
    EvidenceBinding,
    EvidenceBindingDetail,
    EvidenceSource,
    EvidenceTraceResponse,
    SourceLocator,
    build_claim_trace,
)

logger = logging.getLogger("services.evidence")


class EvidenceReadError(RuntimeError):
    """Raised when canonical evidence exists behind an unreadable backend path."""


class EvidenceService:
    async def get_trace(self, slug: str, ruleset_id: str, target: ClaimTarget) -> EvidenceTraceResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None
        base = {
            "game_id": str(game["id"]),
            "slug": str(game["slug"]),
            "ruleset_id": ruleset_id,
            "target": target,
        }
        if supabase.is_local():
            return EvidenceTraceResponse(status="not_available", **base)
        try:
            return await anyio.to_thread.run_sync(self._load_trace, game, ruleset_id, target, base)
        except Exception as exc:
            logger.exception("Evidence trace read failed for %s/%s", slug, ruleset_id)
            raise EvidenceReadError(f"evidence trace backend failure for {slug}/{ruleset_id}") from exc

    async def get_claim(self, slug: str, ruleset_id: str, claim_id: str) -> ClaimDetailResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game or supabase.is_local():
            return None
        try:
            return await anyio.to_thread.run_sync(self._load_claim_detail, game, ruleset_id, claim_id)
        except Exception as exc:
            logger.exception("Claim detail read failed for %s/%s/%s", slug, ruleset_id, claim_id)
            raise EvidenceReadError(f"claim evidence backend failure for {slug}/{ruleset_id}/{claim_id}") from exc

    @staticmethod
    def _validate_ruleset(client, game: dict, ruleset_id: str) -> bool:
        rows = (
            client.table("rule_sets")
            .select("id")
            .eq("id", ruleset_id)
            .eq("game_id", game["id"])
            .limit(1)
            .execute()
            .data
        )
        return bool(rows)

    @classmethod
    def _load_trace(cls, game: dict, ruleset_id: str, target: ClaimTarget, base: dict) -> EvidenceTraceResponse:
        client = supabase._get_client()
        if not cls._validate_ruleset(client, game, ruleset_id):
            return EvidenceTraceResponse(status="not_available", **base)

        query = (
            client.table("claims")
            .select("*")
            .eq("rule_set_id", ruleset_id)
            .eq("target_type", target.target_type.value)
        )
        if target.rule_id is not None:
            query = query.eq("rule_id", target.rule_id)
        if target.component_id is not None:
            query = query.eq("component_id", target.component_id)
        if target.property_key is not None:
            query = query.eq("property_key", target.property_key)
        if target.ordinal is not None:
            query = query.eq("ordinal", target.ordinal)
        if target.ability_id is not None:
            query = query.eq("ability_id", target.ability_id)
        if target.field_path is not None:
            query = query.eq("field_path", target.field_path)

        claim_rows = query.order("created_at").execute().data
        if not claim_rows:
            return EvidenceTraceResponse(status="not_available", **base)

        traces = [cls._build_trace(client, row) for row in claim_rows]
        return EvidenceTraceResponse(status="available", claims=traces, **base)

    @classmethod
    def _load_claim_detail(cls, game: dict, ruleset_id: str, claim_id: str) -> ClaimDetailResponse | None:
        client = supabase._get_client()
        if not cls._validate_ruleset(client, game, ruleset_id):
            return None
        rows = (
            client.table("claims")
            .select("*")
            .eq("rule_set_id", ruleset_id)
            .eq("claim_id", claim_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        return ClaimDetailResponse(
            game_id=str(game["id"]),
            slug=str(game["slug"]),
            ruleset_id=ruleset_id,
            trace=cls._build_trace(client, rows[0]),
        )

    @classmethod
    def _build_trace(cls, client, claim_row: dict):
        claim = cls._claim_model(claim_row)
        binding_rows = (
            client.table("evidence_bindings")
            .select("*")
            .eq("claim_id", claim.claim_id)
            .order("created_at")
            .execute()
            .data
        )
        details = [cls._binding_detail(client, row) for row in binding_rows]
        return build_claim_trace(claim, details)

    @classmethod
    def _binding_detail(cls, client, row: dict) -> EvidenceBindingDetail:
        source_rows = (
            client.table("evidence_sources")
            .select("*")
            .eq("source_id", row["source_id"])
            .limit(1)
            .execute()
            .data
        )
        if not source_rows:
            raise ValueError(f"missing evidence source {row['source_id']}")
        locator = None
        if row.get("locator_id"):
            locator_rows = (
                client.table("source_locators")
                .select("*")
                .eq("source_id", row["source_id"])
                .eq("locator_id", row["locator_id"])
                .limit(1)
                .execute()
                .data
            )
            if not locator_rows:
                raise ValueError(f"missing source locator {row['locator_id']}")
            locator = cls._locator_model(locator_rows[0])
        return EvidenceBindingDetail(
            binding=cls._binding_model(row),
            source=cls._source_model(source_rows[0]),
            locator=locator,
        )

    @staticmethod
    def _claim_model(row: dict) -> Claim:
        target = ClaimTarget(
            target_type=row["target_type"],
            rule_id=row.get("rule_id"),
            component_id=row.get("component_id"),
            property_key=row.get("property_key"),
            ordinal=row.get("ordinal"),
            ability_id=row.get("ability_id"),
            field_path=row.get("field_path"),
        )
        return Claim(
            claim_id=row["claim_id"],
            ruleset_id=str(row["rule_set_id"]),
            claim_type=row["claim_type"],
            normalized_payload=row.get("normalized_payload") or {},
            target=target,
            lifecycle_status=row.get("lifecycle_status", "unknown"),
            generator_provenance=row.get("generator_provenance") or {},
        )

    @staticmethod
    def _source_model(row: dict) -> EvidenceSource:
        return EvidenceSource(
            source_id=row["source_id"],
            url=row.get("url"),
            document_identity=row.get("document_identity"),
            source_type=row["source_type"],
            publisher_name=row.get("publisher_name"),
            platform=row.get("platform"),
            language_code=row.get("language_code"),
            revision_label=row.get("revision_label"),
            published_at=row.get("published_at"),
            retrieved_at=row.get("retrieved_at"),
            trust_metadata=row.get("trust_metadata") or {},
        )

    @staticmethod
    def _locator_model(row: dict) -> SourceLocator:
        return SourceLocator(
            locator_id=row["locator_id"],
            source_id=row["source_id"],
            page_number=row.get("page_number"),
            section_heading=row.get("section_heading"),
            anchor=row.get("anchor"),
            selector=row.get("selector"),
            structured_path=row.get("structured_path"),
            external_reference=row.get("external_reference"),
        )

    @staticmethod
    def _binding_model(row: dict) -> EvidenceBinding:
        return EvidenceBinding(
            binding_id=row["binding_id"],
            claim_id=row["claim_id"],
            source_id=row["source_id"],
            locator_id=row.get("locator_id"),
            relation=row["relation"],
            reviewer_provenance=row.get("reviewer_provenance") or {},
            generator_provenance=row.get("generator_provenance") or {},
            created_at=row.get("created_at"),
            verified_at=row.get("verified_at"),
        )
