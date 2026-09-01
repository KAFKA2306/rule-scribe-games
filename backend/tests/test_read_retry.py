import httpx
import pytest

from app.core.read_retry import run_supabase_read


def test_supabase_read_returns_without_retry():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        return "ok"

    assert run_supabase_read(operation, retry_delay_seconds=0) == "ok"
    assert calls == 1


def test_supabase_read_retries_remote_protocol_error_once():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.RemoteProtocolError("Server disconnected")
        return "ok"

    assert run_supabase_read(operation, retry_delay_seconds=0) == "ok"
    assert calls == 2


def test_supabase_read_fails_after_one_retry():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise httpx.RemoteProtocolError("Server disconnected")

    with pytest.raises(httpx.RemoteProtocolError, match="Server disconnected"):
        run_supabase_read(operation, retry_delay_seconds=0)
    assert calls == 2


def test_supabase_read_does_not_retry_unproven_errors():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise ValueError("bad data")

    with pytest.raises(ValueError, match="bad data"):
        run_supabase_read(operation, retry_delay_seconds=0)
    assert calls == 1
