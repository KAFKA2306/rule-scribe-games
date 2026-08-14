import hashlib
import json

from fastapi import APIRouter, Depends, Request, Response

from app.models.vrchat_catalog import CatalogModel
from app.services.vrchat_manifest_catalog import VrchatManifestCatalogService

router = APIRouter()
_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=3600"


def get_vrchat_manifest_catalog_service():
    return VrchatManifestCatalogService()


def _conditional_json_response(request: Request, payload: CatalogModel) -> Response:
    content = json.dumps(
        payload.model_dump(mode="json", by_alias=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    etag = f'"{hashlib.sha256(content).hexdigest()}"'
    headers = {
        "Cache-Control": _CACHE_CONTROL,
        "ETag": etag,
        "X-Content-Type-Options": "nosniff",
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=content, media_type="application/json; charset=utf-8", headers=headers)


@router.get("/catalog")
async def get_vrchat_manifest_catalog(
    request: Request,
    service: VrchatManifestCatalogService = Depends(get_vrchat_manifest_catalog_service),
):
    return _conditional_json_response(request, await service.get_catalog())


@router.get("/manifests/{slug}/{ruleset_id}")
async def get_vrchat_manifest(
    slug: str,
    ruleset_id: str,
    request: Request,
    service: VrchatManifestCatalogService = Depends(get_vrchat_manifest_catalog_service),
):
    return _conditional_json_response(request, await service.get_manifest(slug, ruleset_id))
