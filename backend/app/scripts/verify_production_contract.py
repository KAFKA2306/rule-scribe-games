from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MECHANICAL_DNA_PATH = "/api/games/skull-king/connections?limit=8"
CATALOG_AUTH_PATH = "/api/games/splendor"


def validate_mechanical_dna_payload(payload: Any) -> int:
    if not isinstance(payload, dict):
        raise ValueError("Mechanical DNA response must be a JSON object")

    expected = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"unexpected {key}: {payload.get(key)!r}; expected {value!r}")

    connections = payload.get("connections")
    if not isinstance(connections, list):
        raise ValueError("connections must be a JSON array")

    return len(connections)


def validate_anonymous_catalog_patch_status(status_code: int) -> None:
    if status_code not in {401, 403}:
        raise ValueError(
            "anonymous catalog PATCH must fail with HTTP 401 or 403; "
            f"received {status_code}"
        )


def verify_anonymous_catalog_patch(base_url: str, timeout_seconds: float = 20.0) -> int:
    """Verify the production catalog mutation boundary without changing data.

    The empty JSON object intentionally contains no update fields. Even if the
    authorization dependency regressed, this request cannot change a game row;
    the verification still fails unless production rejects the anonymous PATCH
    before reaching the no-op update branch.
    """

    url = f"{base_url.rstrip('/')}{CATALOG_AUTH_PATH}"
    request = Request(
        url,
        data=b"{}",
        method="PATCH",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "rule-scribe-games-production-contract/1.0",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            status_code = response.status
    except HTTPError as exc:
        status_code = exc.code

    validate_anonymous_catalog_patch_status(status_code)
    return status_code


def verify_production(base_url: str, timeout_seconds: float = 20.0) -> int:
    url = f"{base_url.rstrip('/')}{MECHANICAL_DNA_PATH}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "rule-scribe-games-production-contract/1.0",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError(f"Mechanical DNA production endpoint returned HTTP {response.status}")
        payload = json.load(response)

    return validate_mechanical_dna_payload(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify canonical production API contracts")
    parser.add_argument(
        "--base-url",
        default="https://bodoge-no-mikata.vercel.app",
        help="Canonical production origin",
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    args = parser.parse_args()

    connection_count = verify_production(args.base_url, args.timeout_seconds)
    auth_status = verify_anonymous_catalog_patch(args.base_url, args.timeout_seconds)
    print(
        "Production API contracts: OK "
        f"(mechanical_dna_connections={connection_count}, anonymous_catalog_patch={auth_status})"
    )


if __name__ == "__main__":
    main()
