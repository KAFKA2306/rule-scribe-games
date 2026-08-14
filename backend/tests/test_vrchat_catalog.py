import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.models import GameDetail
from app.models.component_catalog import ComponentKind, ComponentSet, ComponentSetListResponse
from app.models.rule_graph import RuleGraphReadResponse, RuleNode, RuleNodeType
from app.models.ruleset import RuleSet, RuleSetListResponse
from app.models.vrchat_catalog import BindingRegistryFile, ManifestReadStatus, PublicationStatus
from app.routers import vrchat
from app.services.vrchat_manifest_catalog import VrchatManifestCatalogService
from fastapi import FastAPI
from fastapi.testclient import TestClient

HTTP_OK = 200
HTTP_NOT_MODIFIED = 304
SHA256_HEX_LENGTH = 64
SNAPSHOT_AT = datetime(2026, 8, 14, tzinfo=UTC)


def _registry_payload(*, status: str = "playable", reason_code: str | None = None) -> dict:
    entry = {
        "slug": "example-game",
        "rulesetId": "ruleset-ja-v1",
        "binding": {
            "moduleId": "vrmine.example-game",
            "moduleVersionRange": ">=1.0.0,<2.0.0",
            "supportedPlatforms": ["vrchat-pc"],
            "interactionProfile": "desktop-and-vr",
            "capabilities": {
                "turn-based": "supported",
                "deck": "supported",
                "score": "supported",
            },
        },
        "publicationStatus": status,
        "snapshotAt": SNAPSHOT_AT.isoformat().replace("+00:00", "Z"),
    }
    if reason_code is not None:
        entry["reasonCode"] = reason_code
    return {"schemaVersion": "1.0", "entries": [entry]}


def _write_registry(tmp_path, *, status: str = "playable", reason_code: str | None = None):
    path = tmp_path / "module-bindings-v1.json"
    path.write_text(
        json.dumps(_registry_payload(status=status, reason_code=reason_code)),
        encoding="utf-8",
    )
    return path


class FakeGameService:
    async def get_game_by_slug(self, slug: str):
        if slug != "example-game":
            return None
        return GameDetail(
            id="game-1",
            slug=slug,
            title="Example Game",
            min_players=2,
            max_players=4,
        ).model_dump(mode="json")


class FakeRuleSetService:
    async def get_by_slug(self, slug: str):
        return RuleSetListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rulesets=[
                RuleSet(
                    ruleset_id="ruleset-ja-v1",
                    game_id="game-1",
                    language_code="ja",
                    source_revision="publisher-v1",
                    source_ids=["source.publisher"],
                    verification_status="verified",
                    status="active",
                )
            ],
        )


class FakeRuleGraphService:
    def __init__(self, *, available: bool = True):
        self.available = available

    async def get_by_slug(self, slug: str, *, rule_set_id: str | None = None, **_kwargs):
        if not self.available:
            return RuleGraphReadResponse(status="not_available", game_id="game-1", slug=slug)
        return RuleGraphReadResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rule_set_id=rule_set_id,
            language_code="ja",
            source_revision="publisher-v1",
            nodes=[
                RuleNode(
                    rule_id="setup.start",
                    node_type=RuleNodeType.SETUP,
                    normalized_statement="Set up the game.",
                    verification_status="verified",
                    source_claim_ref="claim.setup",
                    evidence_ref="evidence.setup",
                ),
                RuleNode(
                    rule_id="end.game",
                    node_type=RuleNodeType.GAME_END,
                    normalized_statement="End the game.",
                    verification_status="verified",
                    source_claim_ref="claim.end",
                    evidence_ref="evidence.end",
                ),
            ],
        )


class FakeComponentCatalogService:
    async def get_sets(self, slug: str, rule_set_id: str):
        return ComponentSetListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            ruleset_id=rule_set_id,
            component_sets=[
                ComponentSet(
                    component_set_id="set.cards",
                    ruleset_id=rule_set_id,
                    canonical_name="Cards",
                    kind=ComponentKind.CARD,
                    source_ids=["source.components"],
                )
            ],
        )


class ExplodingService:
    def __getattr__(self, name):
        raise AssertionError(f"canonical service must not be read for blocked entry: {name}")


def _service(tmp_path, *, status: str = "playable", reason_code: str | None = None, graph_available: bool = True):
    registry_path = _write_registry(tmp_path, status=status, reason_code=reason_code)
    return VrchatManifestCatalogService(
        registry_path=registry_path,
        game_service=FakeGameService(),
        ruleset_service=FakeRuleSetService(),
        rule_graph_service=FakeRuleGraphService(available=graph_available),
        component_catalog_service=FakeComponentCatalogService(),
    )


def _client(service: VrchatManifestCatalogService) -> TestClient:
    app = FastAPI()
    app.include_router(vrchat.router, prefix="/api/vrchat/v1")
    app.dependency_overrides[vrchat.get_vrchat_manifest_catalog_service] = lambda: service
    return TestClient(app)


def test_production_registry_is_valid_and_starts_fail_closed():
    registry_path = Path(__file__).parents[2] / "data" / "vrchat" / "module-bindings-v1.json"
    registry = BindingRegistryFile.model_validate_json(registry_path.read_text(encoding="utf-8"))
    assert registry.entries == []


@pytest.mark.asyncio
async def test_playable_entry_projects_one_selected_manifest(tmp_path):
    result = await _service(tmp_path).get_manifest("example-game", "ruleset-ja-v1")

    assert result.status == ManifestReadStatus.AVAILABLE
    assert result.manifest is not None
    assert result.manifest.schema_version == "1.0"
    assert result.manifest.game_id == "game-1"
    assert result.manifest.ruleset_id == "ruleset-ja-v1"
    assert result.manifest.module_id == "vrmine.example-game"
    assert result.manifest.component_set_refs == ["set.cards"]
    assert result.manifest.generated_at == SNAPSHOT_AT


@pytest.mark.asyncio
async def test_unregistered_manifest_is_explicit_and_has_no_payload(tmp_path):
    result = await _service(tmp_path).get_manifest("other-game", "ruleset-other")

    assert result.status == ManifestReadStatus.NOT_REGISTERED
    assert result.reason_code == "MODULE_BINDING_NOT_REGISTERED"
    assert result.manifest is None


@pytest.mark.asyncio
async def test_known_unsupported_entry_never_reads_canonical_services(tmp_path):
    registry_path = _write_registry(tmp_path, status="unsupported", reason_code="DEXTERITY_UNSUPPORTED")
    exploding = ExplodingService()
    service = VrchatManifestCatalogService(
        registry_path=registry_path,
        game_service=exploding,
        ruleset_service=exploding,
        rule_graph_service=exploding,
        component_catalog_service=exploding,
    )

    result = await service.get_manifest("example-game", "ruleset-ja-v1")

    assert result.status == ManifestReadStatus.UNSUPPORTED
    assert result.reason_code == "DEXTERITY_UNSUPPORTED"
    assert result.manifest is None


@pytest.mark.asyncio
async def test_playable_registry_entry_is_downgraded_when_canonical_projection_is_invalid(tmp_path):
    service = _service(tmp_path, graph_available=False)

    result = await service.get_manifest("example-game", "ruleset-ja-v1")
    catalog = await service.get_catalog()

    assert result.status == ManifestReadStatus.INVALID
    assert result.reason_code == "RULE_GRAPH_NOT_AVAILABLE"
    assert result.manifest is None
    assert catalog.entries[0].status == PublicationStatus.INVALID
    assert catalog.entries[0].reason_code == "RULE_GRAPH_NOT_AVAILABLE"


def test_catalog_and_manifest_routes_are_read_only():
    assert all(route.methods <= {"GET", "HEAD"} for route in vrchat.router.routes)


def test_catalog_api_is_cacheable_and_supports_conditional_get(tmp_path):
    client = _client(_service(tmp_path))

    first = client.get("/api/vrchat/v1/catalog")
    assert first.status_code == HTTP_OK
    assert first.headers["cache-control"] == "public, max-age=300, stale-while-revalidate=3600"
    etag = first.headers["etag"]
    payload = first.json()
    assert payload["schemaVersion"] == "1.0"
    assert payload["manifestSchemaVersion"] == "1.0"
    assert len(payload["catalogRevision"]) == SHA256_HEX_LENGTH
    assert payload["entries"][0]["status"] == "playable"

    second = client.get("/api/vrchat/v1/catalog", headers={"If-None-Match": etag})
    assert second.status_code == HTTP_NOT_MODIFIED
    assert second.content == b""
    assert second.headers["etag"] == etag


def test_selected_manifest_api_returns_valid_manifest_in_one_fetch(tmp_path):
    client = _client(_service(tmp_path))

    response = client.get("/api/vrchat/v1/manifests/example-game/ruleset-ja-v1")
    assert response.status_code == HTTP_OK
    payload = response.json()
    assert payload["status"] == "available"
    assert payload["manifest"]["schemaVersion"] == "1.0"
    assert payload["manifest"]["moduleId"] == "vrmine.example-game"
    assert payload["manifest"]["componentSetRefs"] == ["set.cards"]
    assert response.headers["etag"].startswith('"')
