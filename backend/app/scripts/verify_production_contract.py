from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.request import Request, urlopen

MECHANICAL_DNA_PATH = "/api/games/skull-king/connections?limit=8"


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
    print(
        "Mechanical DNA production contract: OK "
        f"(algorithm=mechanical-dna-concept-v1, status=available, connections={connection_count})"
    )


if __name__ == "__main__":
    main()
