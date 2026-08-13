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
