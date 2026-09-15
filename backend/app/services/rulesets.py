import logging

from app.core import supabase
from app.core.read_retry import run_supabase_read_async
from app.models.ruleset import RuleSet, RuleSetListResponse

logger = logging.getLogger("services.rulesets")


class RuleSetReadError(RuntimeError):
    """Raised when canonical RuleSet data cannot be read safely."""


class RuleSetService:
    async def get_by_slug(self, slug: str) -> RuleSetListResponse | None:
        game = await supabase.get_by_slug(slug)
        if not game:
            return None

        base = {
            "game_id": str(game["id"]),
            "slug": str(game["slug"]),
        }

        if supabase.is_local():
            return RuleSetListResponse(status="not_available", **base)

        try:
            rows = await run_supabase_read_async(self._load_rulesets, game)
        except Exception as exc:
            logger.exception("RuleSet read failed for %s", slug)
            raise RuleSetReadError(f"ruleset backend failure for {slug}") from exc

        if not rows:
            return RuleSetListResponse(status="not_available", **base)

        return RuleSetListResponse(
            status="available",
            rulesets=[self._to_model(row) for row in rows],
            **base,
        )

    @staticmethod
    def _load_rulesets(game: dict) -> list[dict]:
        return (
            supabase._get_client()
            .table("rule_sets")
            .select("*")
            .eq("game_id", game["id"])
            .order("is_active", desc=True)
            .order("version", desc=True)
            .execute()
            .data
        )

    @staticmethod
    def _to_model(row: dict) -> RuleSet:
        return RuleSet(
            ruleset_id=str(row["id"]),
            game_id=str(row["game_id"]),
            work_id=str(row["work_id"]) if row.get("work_id") else None,
            version=row.get("version", 1),
            schema_version=row.get("schema_version") or "1.0",
            language_code=row.get("language_code"),
            edition_label=row.get("edition_label"),
            revision_label=row.get("revision_label"),
            source_revision=row.get("source_revision"),
            platform=row.get("platform"),
            publisher_name=row.get("publisher_name"),
            publication_date=row.get("publication_date"),
            effective_date=row.get("effective_date"),
            status=row.get("status", "unknown"),
            verification_status=row.get("verification_status", "unknown"),
            is_active=row.get("is_active", True),
            base_rule_set_id=(str(row["base_rule_set_id"]) if row.get("base_rule_set_id") else None),
            relation_type=row.get("relation_type"),
            variant_label=row.get("variant_label"),
            source_ids=[str(value) for value in (row.get("source_ids") or [])],
        )
