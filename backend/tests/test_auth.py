import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.routers import auth


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    response = FakeResponse(200, {})

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers):
        self.last_url = url
        self.last_headers = headers
        return self.response


@pytest.mark.asyncio
async def test_auth_requires_bearer_token():
    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('VITE_SUPABASE_ANON_KEY', 'sb_publishable_test')
    FakeAsyncClient.response = FakeResponse(401, {'message': 'invalid token'})
    monkeypatch.setattr(auth.httpx, 'AsyncClient', FakeAsyncClient)

    credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials='bad-token')
    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(credentials)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_returns_normalized_verified_user(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('VITE_SUPABASE_ANON_KEY', 'sb_publishable_test')
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            'id': 'user-123',
            'email': 'user@example.com',
            'user_metadata': {
                'full_name': 'Test User',
                'avatar_url': 'https://example.com/avatar.png',
            },
        },
    )
    monkeypatch.setattr(auth.httpx, 'AsyncClient', FakeAsyncClient)

    credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials='valid-token')
    user = await auth.get_current_user(credentials)

    assert user == {
        'id': 'user-123',
        'email': 'user@example.com',
        'display_name': 'Test User',
        'avatar_url': 'https://example.com/avatar.png',
    }


@pytest.mark.asyncio
async def test_catalog_editor_rejects_authenticated_user_without_acl(monkeypatch):
    async def no_role(user_id):
        assert user_id == 'user-123'
        return None

    monkeypatch.setattr(auth.catalog_access, 'get_catalog_editor_role', no_role)
    with pytest.raises(HTTPException) as exc:
        await auth.require_catalog_editor({'id': 'user-123', 'email': 'user@example.com'})

    assert exc.value.status_code == 403
    assert exc.value.detail == 'Catalog editor permission required'


@pytest.mark.asyncio
async def test_catalog_editor_accepts_explicit_editor_acl(monkeypatch):
    async def editor_role(user_id):
        assert user_id == 'user-123'
        return 'editor'

    monkeypatch.setattr(auth.catalog_access, 'get_catalog_editor_role', editor_role)
    user = await auth.require_catalog_editor({'id': 'user-123', 'email': 'user@example.com'})

    assert user['id'] == 'user-123'
    assert user['catalog_role'] == 'editor'
