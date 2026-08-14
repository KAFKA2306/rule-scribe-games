from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from app.scripts.curated_game_workflow import (
    CURATED_DIR,
    REPO_ROOT,
    CuratedGameSpec,
    IdentityPlan,
    WorkflowError,
    load_all_specs,
    load_spec,
    preflight_identity,
    validate_assertions,
    validate_runtime_guide,
)

DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
CURATED_GENERATOR_PATH = REPO_ROOT / "frontend" / "scripts" / "generate-curated-game-artifacts.mjs"
DEPLOYMENT_MANIFEST_PATH = REPO_ROOT / "frontend" / "public" / "curated-guides-manifest.json"


def resolve_spec_path(game: str) -> Path:
    candidate = CURATED_DIR / f"{game}.json"
    if not candidate.is_file():
        raise WorkflowError(f"curated game spec not found: {candidate.relative_to(REPO_ROOT)}")
    spec = load_spec(candidate)
    if candidate.stem != spec.slug or game != spec.slug:
        raise WorkflowError("spec filename, GAME, and canonical slug must match")
    return candidate


def load_named_spec(game: str, specs: list[CuratedGameSpec]) -> CuratedGameSpec:
    path = resolve_spec_path(game)
    selected = load_spec(path)
    matches = [spec for spec in specs if spec.slug == selected.slug]
    if len(matches) != 1:
        raise WorkflowError(f"expected exactly one structured spec for {selected.slug}")
    return matches[0]


def verify_source_reachable_streamed(spec: CuratedGameSpec) -> None:
    headers = {"User-Agent": "BodogeNoMikataSourceVerifier/2.0 (+https://bodoge-no-mikata.vercel.app/)"}
    with httpx.Client(follow_redirects=True, timeout=20, headers=headers) as client:
        with client.stream("GET", spec.source.url) as response:
            if response.status_code < 200 or response.status_code >= 400:
                raise WorkflowError(
                    f"primary source is not reachable: HTTP {response.status_code} {spec.source.url}"
                )


def deployment_manifest_payload(specs: list[CuratedGameSpec]) -> dict[str, Any]:
    games = {
        spec.slug: {
            "rule_version": spec.source.rule_version,
            "source_revision": spec.source.revision,
        }
        for spec in sorted(specs, key=lambda item: item.slug)
    }
    revision_contract = json.dumps(games, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(revision_contract.encode("utf-8")).hexdigest()
    return {
        "schema_version": 1,
        "revision_contract_sha256": digest,
        "games": games,
    }


def render_deployment_manifest(specs: list[CuratedGameSpec]) -> str:
    return json.dumps(
        deployment_manifest_payload(specs),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def generate_artifacts(specs: list[CuratedGameSpec]) -> None:
    subprocess.run(
        ["node", str(CURATED_GENERATOR_PATH)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if not DEPLOYMENT_MANIFEST_PATH.is_file():
        raise WorkflowError("curated artifact generator did not create deployment manifest")
    actual_manifest = DEPLOYMENT_MANIFEST_PATH.read_text(encoding="utf-8")
    expected_manifest = render_deployment_manifest(specs)
    if actual_manifest != expected_manifest:
        raise WorkflowError("Node/Python curated revision manifest contract mismatch")


def preflight_catalog(spec: CuratedGameSpec) -> tuple[Any, IdentityPlan]:
    from app.core import supabase

    client = supabase._get_client()
    plan = preflight_identity(client, spec)
    return client, plan


def write_catalog_with_plan(client: Any, spec: CuratedGameSpec, plan: IdentityPlan) -> dict[str, Any]:
    created_work_id: str | None = None
    work_id = plan.work_id

    if plan.create_work:
        rows = (
            client.table("game_works")
            .insert(
                {
                    "canonical_title": spec.work.canonical_title,
                    "identity_status": spec.work.identity_status,
                }
            )
            .execute()
            .data
        )
        if not rows:
            raise WorkflowError("failed to create canonical game work")
        created_work_id = str(rows[0]["id"])
        work_id = created_work_id

    payload = dict(spec.game)
    payload["work_id"] = work_id

    try:
        if plan.game_id:
            rows = client.table("games").update(payload).eq("id", plan.game_id).execute().data
        else:
            rows = client.table("games").insert(payload).execute().data
    except Exception:
        if created_work_id:
            client.table("game_works").delete().eq("id", created_work_id).execute()
        raise

    if not rows:
        raise WorkflowError("catalog write returned no game row")
    row = rows[0]
    if row.get("slug") != spec.slug:
        raise WorkflowError("catalog write returned unexpected slug")
    return row


def verify_catalog_live(spec: CuratedGameSpec, base_url: str) -> None:
    base = base_url.rstrip("/")
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        api_response = client.get(f"{base}/api/games/{spec.slug}")
        if api_response.status_code != 200:
            raise WorkflowError(f"production API failed: HTTP {api_response.status_code}")
        payload = api_response.json()
        if payload.get("slug") != spec.slug:
            raise WorkflowError("production API returned the wrong slug")
        if payload.get("source_url") != spec.source.url:
            raise WorkflowError("production API source provenance does not match structured input")
        if not payload.get("work_id"):
            raise WorkflowError("production API record has no canonical work_id")

        page_response = client.get(f"{base}/games/{spec.slug}")
        if page_response.status_code != 200:
            raise WorkflowError(f"production page failed: HTTP {page_response.status_code}")
        expected_title = str(spec.game.get("title_ja") or spec.game["title"])
        if expected_title not in page_response.text:
            raise WorkflowError("production page does not contain the expected title")


def validate_release_manifest(
    expected: dict[str, Any],
    deployed: dict[str, Any],
    game: str | None = None,
) -> None:
    if deployed.get("schema_version") != expected.get("schema_version"):
        raise WorkflowError("deployed curated manifest schema version mismatch")
    if deployed.get("revision_contract_sha256") != expected.get("revision_contract_sha256"):
        raise WorkflowError("deployed curated revision contract does not match main")
    if game is not None:
        expected_game = (expected.get("games") or {}).get(game)
        deployed_game = (deployed.get("games") or {}).get(game)
        if expected_game is None:
            raise WorkflowError(f"local deployment manifest has no game {game}")
        if deployed_game != expected_game:
            raise WorkflowError(f"deployed curated manifest revision mismatch for {game}")


def verify_frontend_release(
    specs: list[CuratedGameSpec],
    base_url: str,
    game: str | None = None,
) -> None:
    expected = deployment_manifest_payload(specs)
    url = f"{base_url.rstrip('/')}/curated-guides-manifest.json"
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        response = client.get(url)
    if response.status_code != 200:
        raise WorkflowError(f"production curated manifest failed: HTTP {response.status_code}")
    validate_release_manifest(expected, response.json(), game=game)


def routine_files(spec: CuratedGameSpec) -> list[str]:
    return [f"data/curated-games/{spec.slug}.json"]


def print_routine_files(spec: CuratedGameSpec) -> None:
    print("Routine PR files:")
    for path in routine_files(spec):
        print(f"- {path}")


def prepare_game(
    spec: CuratedGameSpec,
    specs: list[CuratedGameSpec],
) -> tuple[Any, IdentityPlan]:
    validate_assertions(spec)
    verify_source_reachable_streamed(spec)
    client, plan = preflight_catalog(spec)
    generate_artifacts(specs)
    validate_runtime_guide(spec)
    return client, plan


def add_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec]) -> None:
    prepare_game(spec, specs)
    print_routine_files(spec)
    print("Prepare fixed point: verified; production catalog unchanged until merge")


def publish_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec], base_url: str) -> None:
    client, plan = prepare_game(spec, specs)
    write_catalog_with_plan(client, spec, plan)
    verify_catalog_live(spec, base_url)
    print(f"Catalog publish fixed point: verified for {spec.slug}")


def check_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec]) -> None:
    validate_assertions(spec)
    generate_artifacts(specs)
    validate_runtime_guide(spec)
    print_routine_files(spec)


def verify_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec], base_url: str) -> None:
    validate_assertions(spec)
    verify_source_reachable_streamed(spec)
    generate_artifacts(specs)
    validate_runtime_guide(spec)
    verify_catalog_live(spec, base_url)
    verify_frontend_release(specs, base_url, game=spec.slug)
    print("Catalog fixed point: verified")
    print("Frontend release fixed point: verified")


def check_all(specs: list[CuratedGameSpec]) -> None:
    for spec in specs:
        validate_assertions(spec)
    generate_artifacts(specs)
    for spec in specs:
        validate_runtime_guide(spec)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("add", "publish", "check", "verify", "check-all", "release-check"))
    parser.add_argument("--game")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = load_all_specs()

    if args.mode in {"add", "publish", "check", "verify"}:
        if not args.game:
            raise WorkflowError(f"{args.mode} requires --game")
        spec = load_named_spec(args.game, specs)
        if args.mode == "add":
            add_game(spec, specs)
        elif args.mode == "publish":
            publish_game(spec, specs, args.base_url)
        elif args.mode == "check":
            check_game(spec, specs)
        else:
            verify_game(spec, specs, args.base_url)
        return

    if args.game:
        raise WorkflowError(f"{args.mode} does not accept --game")

    if args.mode == "check-all":
        check_all(specs)
    else:
        generate_artifacts(specs)
        verify_frontend_release(specs, args.base_url)


if __name__ == "__main__":
    main()
