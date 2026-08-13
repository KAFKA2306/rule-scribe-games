#!/usr/bin/env python3
"""Fail-close check that Supabase can initiate Google OAuth without leaking config."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def safe_error_detail(payload: bytes) -> tuple[str, str]:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "unknown", "non-JSON response"
    code = str(data.get("error_code") or data.get("code") or "unknown")[:80]
    message = str(data.get("msg") or data.get("message") or data.get("error_description") or "unknown")[:200]
    return code, message


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_google_oauth.py <vercel-env-file>")
        return 2

    values = load_env(Path(sys.argv[1]))
    base = values.get("SUPABASE_URL", "").rstrip("/")
    if not base:
        print("Google OAuth provider redirect check failed: SUPABASE_URL missing")
        return 1

    query = urllib.parse.urlencode(
        {
            "provider": "google",
            "redirect_to": "https://bodoge-no-mikata.vercel.app",
        }
    )
    url = f"{base}/auth/v1/authorize?{query}"
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "rule-scribe-games-auth-contract/1.0"},
    )

    payload = b""
    try:
        response = opener.open(request, timeout=10)
        status = response.status
        location = response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        status = exc.code
        location = exc.headers.get("Location", "")
        payload = exc.read()
    except urllib.error.URLError as exc:
        print(f"Google OAuth provider redirect check failed: network={type(exc.reason).__name__}")
        return 1

    host = urllib.parse.urlparse(location).hostname
    if status in (301, 302, 303, 307, 308) and host == "accounts.google.com":
        print("Google OAuth provider redirect contract: OK")
        return 0

    code, message = safe_error_detail(payload)
    print(
        "Google OAuth provider redirect check failed: "
        f"status={status}, host={host or 'none'}, error_code={code}, message={message}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
