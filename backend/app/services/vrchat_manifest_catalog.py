from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from urllib.parse import quote

from app.models import GameDetail
from app.models.component_catalog import ComponentCatalog
from app.models.vrchat_catalog import (
    BindingRegistryEntry,
    BindingRegistryFile,
    ManifestCatalog,
    ManifestCatalogEntry,
    ManifestReadResponse,
    ManifestReadStatus,
    PublicationStatus,
)
from app.services.component_catalog import ComponentCatalogService
from app.services.game_service import GameService
from app.services.rule_graph import RuleGraphService
from app.services.rulesets import RuleSetService
from app.services.vrchat_manifest_projection import project_board_game_module_manifest

logger = logging.getLogger("services.vrchat_manifest_catalog")
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "vrchat" / "module-bindings-v1.json"

_STATUS_TO_READ_STATUS = {
    PublicationStatus.UNAVAILABLE: ManifestReadStatus.UNAVAILABLE,
    PublicationStatus.UNSUPPORTED: ManifestReadStatus.UNSUPPORTED,
    PublicationStatus.RETIRED: ManifestReadStatus.RETIRED,
    PublicationStatus.INVALID: ManifestReadStatus.INVALID,
}


class VrchatManifestCatalogService:
    def __init__(
        self,
        *,
        registry_path: Path = DEFAULT_REGISTRY_PATH,
        game_service: GameService | None = None,
        ruleset_service: RuleSetService | None = None,
        rule_graph_service: RuleGraphService | None = None,
        component_catalog_service: ComponentCatalogService | None = None,
    ):
        self.registry_path = registry_path
        self.game_service = game_service or GameService()
        self.ruleset_service = ruleset_service or RuleSetService()
        self.rule_graph_service = rule_graph_service or RuleGraphService()
        self.component_catalog_service = component_catalog_service or ComponentCatalogService()

    def load_registry(self) -> BindingRegistryFile:
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return BindingRegistryFile.model_validate(payload)

    async def get_catalog(self) -> ManifestCatalog:
        registry = self.load_registry()
        entries: list[ManifestCatalogEntry] = []
        for registry_entry in sorted(registry.entries, key=lambda item: (item.slug, item.ruleset_id)):
            status = registry_entry.publication_status
            reason_code = registry_entry.reason_code
            if status == PublicationStatus.PLAYABLE:
                result = await self._project_registry_entry(registry_entry)
                if result.status != ManifestReadStatus.AVAILABLE:
                    status = PublicationStatus.INVALID
                    reason_code = result.reason_code or "CANONICAL_PROJECTION_INVALID"

            entries.append(
                ManifestCatalogEntry(
                    slug=registry_entry.slug,
                    rulesetId=registry_entry.ruleset_id,
                    moduleId=registry_entry.binding.module_id,
                    moduleVersionRange=registry_entry.binding.module_version_range,
                    status=status,
                    reasonCode=reason_code,
                    manifestPath=self._manifest_path(registry_entry.slug, registry_entry.ruleset_id),
                )
            )

        revision_payload = [entry.model_dump(mode="json", by_alias=True) for entry in entries]
        revision = hashlib.sha256(
            json.dumps(revision_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return ManifestCatalog(catalogRevision=revision, entries=entries)

    async def get_manifest(self, slug: str, ruleset_id: str) -> ManifestReadResponse:
        registry = self.load_registry()
        entry = next(
            (
                candidate
                for candidate in registry.entries
                if candidate.slug == slug and candidate.ruleset_id == ruleset_id
            ),
            None,
        )
        if entry is None:
            return ManifestReadResponse(
                status=ManifestReadStatus.NOT_REGISTERED,
                slug=slug,
                rulesetId=ruleset_id,
                reasonCode="MODULE_BINDING_NOT_REGISTERED",
            )
        if entry.publication_status != PublicationStatus.PLAYABLE:
            return ManifestReadResponse(
                status=_STATUS_TO_READ_STATUS[entry.publication_status],
                slug=slug,
                rulesetId=ruleset_id,
                reasonCode=entry.reason_code,
            )
        return await self._project_registry_entry(entry)

    async def _project_registry_entry(self, entry: BindingRegistryEntry) -> ManifestReadResponse:
        try:
            game_row = await self.game_service.get_game_by_slug(entry.slug)
            if not game_row:
                return self._invalid(entry, "CANONICAL_GAME_NOT_FOUND")
            game = GameDetail.model_validate(game_row)

            rulesets = await self.ruleset_service.get_by_slug(entry.slug)
            if rulesets is None or rulesets.status != "available":
                return self._invalid(entry, "RULESETS_NOT_AVAILABLE")
            ruleset = next(
                (candidate for candidate in rulesets.rulesets if candidate.ruleset_id == entry.ruleset_id),
                None,
            )
            if ruleset is None:
                return self._invalid(entry, "RULESET_NOT_FOUND")

            rule_graph = await self.rule_graph_service.get_by_slug(entry.slug, rule_set_id=entry.ruleset_id)
            if rule_graph is None or rule_graph.status != "available":
                return self._invalid(entry, "RULE_GRAPH_NOT_AVAILABLE")

            component_catalog = await self._component_catalog(entry)
            manifest = project_board_game_module_manifest(
                game=game,
                ruleset=ruleset,
                rule_graph=rule_graph,
                component_catalog=component_catalog,
                binding=entry.binding,
                generated_at=entry.snapshot_at,
            )
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning(
                "VRChat manifest projection rejected %s/%s: %s",
                entry.slug,
                entry.ruleset_id,
                exc,
            )
            return self._invalid(entry, "CANONICAL_PROJECTION_INVALID")

        return ManifestReadResponse(
            status=ManifestReadStatus.AVAILABLE,
            slug=entry.slug,
            rulesetId=entry.ruleset_id,
            manifest=manifest,
        )

    async def _component_catalog(self, entry: BindingRegistryEntry) -> ComponentCatalog | None:
        response = await self.component_catalog_service.get_sets(entry.slug, entry.ruleset_id)
        if response is None or response.status != "available":
            return None
        return ComponentCatalog(
            ruleset_id=entry.ruleset_id,
            component_sets=response.component_sets,
            property_definitions=response.property_definitions,
        )

    @staticmethod
    def _invalid(entry: BindingRegistryEntry, reason_code: str) -> ManifestReadResponse:
        return ManifestReadResponse(
            status=ManifestReadStatus.INVALID,
            slug=entry.slug,
            rulesetId=entry.ruleset_id,
            reasonCode=reason_code,
        )

    @staticmethod
    def _manifest_path(slug: str, ruleset_id: str) -> str:
        return f"/api/vrchat/v1/manifests/{quote(slug, safe='')}/{quote(ruleset_id, safe='')}"
