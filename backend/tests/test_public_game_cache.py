import pytest
from fastapi import Request, Response

from app.main import (
    PUBLIC_GAME_BROWSER_CACHE,
    PUBLIC_GAME_CDN_CACHE,
    cache_public_game_reads,
)


def make_request(method: str, path: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


async def ok_response(_request: Request) -> Response:
    return Response(status_code=200)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/games",
        "/api/games/skull-king",
        "/games/skull-king",
    ],
)
async def test_public_game_get_uses_browser_and_cdn_cache_headers(path):
    response = await cache_public_game_reads(make_request("GET", path), ok_response)

    assert response.headers["Cache-Control"] == PUBLIC_GAME_BROWSER_CACHE
    assert response.headers["CDN-Cache-Control"] == PUBLIC_GAME_CDN_CACHE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "status_code"),
    [
        ("PATCH", "/api/games/skull-king", 200),
        ("GET", "/api/lists", 200),
        ("GET", "/api/games/skull-king", 404),
        ("GET", "/games/not-found", 404),
    ],
)
async def test_non_cacheable_response_does_not_receive_shared_cache_headers(method, path, status_code):
    async def response_with_status(_request: Request) -> Response:
        return Response(status_code=status_code)

    response = await cache_public_game_reads(make_request(method, path), response_with_status)

    assert "Cache-Control" not in response.headers
    assert "CDN-Cache-Control" not in response.headers
