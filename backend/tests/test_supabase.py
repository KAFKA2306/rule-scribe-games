
import pytest
from unittest.mock import MagicMock, patch
from app.core.supabase import (
    _client,
    _repo,
    SupabaseGameRepository,
    NoopGameRepository,
)

# --- Test _client factory ---

def test_client_returns_none_missing_url():
    with patch("app.core.supabase.settings") as mock_settings:
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = "some_key"
        assert _client() is None

def test_client_returns_none_missing_key():
    with patch("app.core.supabase.settings") as mock_settings:
        mock_settings.supabase_url = "some_url"
        mock_settings.supabase_key = ""
        assert _client() is None

def test_client_returns_none_create_client_failure():
    with patch("app.core.supabase.settings") as mock_settings, \
         patch("app.core.supabase.create_client", side_effect=Exception("Connection error")):
        mock_settings.supabase_url = "some_url"
        mock_settings.supabase_key = "some_key"
        assert _client() is None

def test_client_success():
    with patch("app.core.supabase.settings") as mock_settings, \
         patch("app.core.supabase.create_client") as mock_create_client:
        mock_settings.supabase_url = "https://example.supabase.co"
        mock_settings.supabase_key = "secret_key"
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = _client()
        assert client == mock_client
        mock_create_client.assert_called_once_with("https://example.supabase.co", "secret_key")

# --- Test SupabaseGameRepository ---

@pytest.mark.asyncio
async def test_supabase_repo_search_success():
    mock_client = MagicMock()
    # Mock chain: client.table("games").select("*").or_(...).execute().data
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_or = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.or_.return_value = mock_or
    mock_or.execute.return_value = mock_execute
    mock_execute.data = [{"id": 1, "title": "Chess"}]

    repo = SupabaseGameRepository(mock_client)
    result = await repo.search("chess")

    assert result == [{"id": 1, "title": "Chess"}]
    mock_client.table.assert_called_with("games")
    mock_table.select.assert_called_with("*")
    # Verify the query string construction if possible, or just that it was called
    args, _ = mock_select.or_.call_args
    assert "chess" in args[0]

@pytest.mark.asyncio
async def test_supabase_repo_search_exception():
    mock_client = MagicMock()
    mock_client.table.side_effect = Exception("DB Error")

    repo = SupabaseGameRepository(mock_client)
    result = await repo.search("chess")
    assert result == []

@pytest.mark.asyncio
async def test_supabase_repo_upsert_success():
    mock_client = MagicMock()
    # Mock chain: client.table("games").upsert(...).execute().data
    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute.return_value = mock_execute
    mock_execute.data = [{"id": 1, "title": "Go"}]

    repo = SupabaseGameRepository(mock_client)
    data = {"title": "Go", "description": "Strategy game"}
    result = await repo.upsert(data)

    assert result == [{"id": 1, "title": "Go"}]
    mock_client.table.assert_called_with("games")
    # key defaults to "title" if source_url not present
    mock_table.upsert.assert_called_with(data, on_conflict="title")

@pytest.mark.asyncio
async def test_supabase_repo_upsert_source_url_key():
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute.return_value = mock_execute
    mock_execute.data = []

    repo = SupabaseGameRepository(mock_client)
    data = {"title": "Go", "source_url": "http://example.com"}
    await repo.upsert(data)

    mock_table.upsert.assert_called_with(data, on_conflict="source_url")

@pytest.mark.asyncio
async def test_supabase_repo_upsert_exception():
    mock_client = MagicMock()
    mock_client.table.side_effect = Exception("DB Error")

    repo = SupabaseGameRepository(mock_client)
    result = await repo.upsert({"title": "Test"})
    assert result == []

# --- Test NoopGameRepository ---

@pytest.mark.asyncio
async def test_noop_repo():
    repo = NoopGameRepository()
    assert await repo.search("anything") == []
    assert await repo.upsert({"any": "thing"}) == []

# --- Test _repo factory ---

def test_repo_factory_with_client():
    with patch("app.core.supabase._client") as mock_get_client:
        mock_client_instance = MagicMock()
        mock_get_client.return_value = mock_client_instance

        repo_instance = _repo()
        assert isinstance(repo_instance, SupabaseGameRepository)
        assert repo_instance.client == mock_client_instance

def test_repo_factory_no_client():
    with patch("app.core.supabase._client") as mock_get_client:
        mock_get_client.return_value = None

        repo_instance = _repo()
        assert isinstance(repo_instance, NoopGameRepository)
