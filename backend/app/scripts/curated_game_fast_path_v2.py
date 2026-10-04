from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
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
    require_publishable,
)

DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
CURATED_GENERATOR_PATH = REPO_ROOT / "frontend" / "scripts" / "generate-curated-game-artifacts.mjs"
DEPLOYMENT_MANIFEST_PATH = REPO_ROOT / "frontend" / "public" / "curated-guides-manifest.json"
LEGACY_RULE_FIELDS = (
    "rules_content",
    "setup_summary",
    "gameplay_summary",
    "end_game_summary",
)


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
    require_publishable(spec)
    assert spec.source is not None
    headers = {"User-Agent": "BodogeNoMikataSourceVerifier/2.0 (+https://bodoge-no-mikata.vercel.app/)"}
    with httpx.Client(follow_redirects=True, timeout=20, headers=headers) as client:
        with client.stream("GET", spec.source.url) as response:
            status = response.status_code
            if 200 <= status < 400:
                return
            trusted = str(spec.game.get("source_trust") or "") in {
                "official_publisher",
                "authorized_partner",
            }
            if trusted and status in {401, 403, 429}:
                print(
                    f"Primary source automated fetch restricted: HTTP {status} "
                    f"{spec.source.url}; trusted provenance retained"
                )
                return
            raise WorkflowError(
                f"primary source is not reachable: HTTP {status} {spec.source.url}"
            )


def deployment_manifest_payload(specs: list[CuratedGameSpec]) -> dict[str, Any]:
    publishable = [
        spec for spec in specs
        if spec.is_publishable and spec.source is not None and spec.game is not None
    ]
    games = {
        spec.slug: {
            "rule_version": spec.source.rule_version,
            "source_revision": spec.source.revision,
        }
        for spec in sorted(publishable, key=lambda item: item.slug)
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
    require_publishable(spec)
    from app.core import supabase

    client = supabase._get_client()
    plan = preflight_identity(client, spec)
    return client, plan


def catalog_write_payload(spec: CuratedGameSpec, work_id: str | None) -> dict[str, Any]:
    require_publishable(spec)
    assert spec.game is not None
    payload = dict(spec.game)
    for field in LEGACY_RULE_FIELDS:
        payload[field] = None
    # Legacy trust/identity columns were retired by migration 009. They may
    # remain in canonical JSON as display/provenance metadata, but are never
    # written back to the production games table.
    payload.pop("official_url", None)
    payload.pop("is_official", None)
    payload["work_id"] = work_id
    return payload


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

    payload = catalog_write_payload(spec, work_id)

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


def _one_or_none(rows: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    if len(rows) > 1:
        raise WorkflowError(f"multiple rows match canonical {label}")
    return rows[0] if rows else None


def _source_id(spec: CuratedGameSpec) -> str:
    assert spec.ruleset is not None
    return spec.ruleset.source_id or f"curated:{spec.slug}:rulebook"


def write_ruleset_projection(client: Any, spec: CuratedGameSpec, game_row: dict[str, Any]) -> str | None:
    if spec.ruleset is None:
        return None
    require_publishable(spec)
    assert spec.source is not None
    assert spec.game is not None

    ruleset = spec.ruleset
    source_id = _source_id(spec)
    now = datetime.now(UTC).isoformat()

    source_rows = (
        client.table("evidence_sources")
        .select("*")
        .eq("source_id", source_id)
        .limit(2)
        .execute()
        .data
    )
    existing_source = _one_or_none(source_rows, f"evidence source {source_id}")
    trust = dict((existing_source or {}).get("trust_metadata") or {})
    trust.update(
        {
            "authority": ruleset.authority,
            "canonical_source": "data/curated-games",
            "coverage": ruleset.coverage,
        }
    )
    source_payload = {
        "source_id": source_id,
        "url": ruleset.source_url or spec.source.url,
        "document_identity": f"{spec.work.canonical_title} rule source",
        "source_type": ruleset.source_type,
        "publisher_name": ruleset.publisher_name,
        "platform": ruleset.platform,
        "language_code": ruleset.language_code,
        "revision_label": ruleset.revision_label,
        "retrieved_at": now,
        "trust_metadata": trust,
        "updated_at": now,
    }
    if existing_source:
        client.table("evidence_sources").update(source_payload).eq("source_id", source_id).execute()
    else:
        client.table("evidence_sources").insert(source_payload).execute()

    game_id = str(game_row["id"])
    work_id = str(game_row.get("work_id") or "")
    if not work_id:
        raise WorkflowError(f"published game {spec.slug} has no canonical work_id")

    all_rule_sets = client.table("rule_sets").select("*").eq("game_id", game_id).execute().data
    identity_rows = [
        row
        for row in all_rule_sets
        if (row.get("language_code") or "") == ruleset.language_code
        and (row.get("edition_label") or "") == ruleset.edition_label
        and (row.get("platform") or "") == ruleset.platform
        and (row.get("revision_label") or "") == ruleset.revision_label
        and (row.get("variant_label") or "") == ""
        and int(row.get("version") or 1) == ruleset.version
    ]
    existing_ruleset = _one_or_none(identity_rows, f"ruleset identity for {spec.slug}")
    existing_source_ids = set((existing_ruleset or {}).get("source_ids") or [])
    existing_source_ids.add(source_id)
    ruleset_payload = {
        "game_id": game_id,
        "work_id": work_id,
        "version": ruleset.version,
        "schema_version": "1.0",
        "language_code": ruleset.language_code,
        "edition_label": ruleset.edition_label,
        "source_revision": spec.source.revision,
        "is_active": True,
        "revision_label": ruleset.revision_label,
        "platform": ruleset.platform,
        "publisher_name": ruleset.publisher_name,
        "status": "active",
        "verification_status": "source_bound",
        "source_ids": sorted(existing_source_ids),
        "updated_at": now,
    }
    if existing_ruleset:
        rows = (
            client.table("rule_sets")
            .update(ruleset_payload)
            .eq("id", existing_ruleset["id"])
            .execute()
            .data
        )
    else:
        rows = client.table("rule_sets").insert(ruleset_payload).execute().data
    if not rows:
        raise WorkflowError(f"ruleset write returned no row for {spec.slug}")
    ruleset_id = str(rows[0]["id"])

    for node in ruleset.nodes:
        locator_id = node.locator_id or f"{spec.slug}:rulebook:{node.rule_id}"
        locator_rows = (
            client.table("source_locators")
            .select("*")
            .eq("locator_id", locator_id)
            .limit(2)
            .execute()
            .data
        )
        existing_locator = _one_or_none(locator_rows, f"source locator {locator_id}")
        locator_payload: dict[str, Any] = {
            "locator_id": locator_id,
            "source_id": source_id,
        }
        if node.page_number is not None:
            locator_payload["page_number"] = node.page_number
        if node.section_heading:
            locator_payload["section_heading"] = node.section_heading
        if node.external_reference:
            locator_payload["external_reference"] = node.external_reference
        if existing_locator:
            client.table("source_locators").update(locator_payload).eq("locator_id", locator_id).execute()
        else:
            client.table("source_locators").insert(locator_payload).execute()

        claim_id = f"{spec.slug}:rule:{node.rule_id}"
        binding_id = f"{spec.slug}:binding:{node.rule_id}"
        node_rows = (
            client.table("rule_nodes")
            .select("*")
            .eq("rule_set_id", ruleset_id)
            .eq("rule_id", node.rule_id)
            .limit(2)
            .execute()
            .data
        )
        existing_node = _one_or_none(node_rows, f"rule node {spec.slug}:{node.rule_id}")
        metadata = dict((existing_node or {}).get("metadata") or {})
        metadata.update(
            {
                "canonical_source": "data/curated-games",
                "coverage": ruleset.coverage,
            }
        )
        node_payload = {
            "rule_set_id": ruleset_id,
            "rule_id": node.rule_id,
            "node_type": node.node_type,
            "normalized_statement": node.normalized_statement,
            "sequence": node.sequence,
            "verification_status": "source_bound",
            "source_claim_ref": claim_id,
            "evidence_ref": binding_id,
            "source_url": ruleset.source_url or spec.source.url,
            "source_locator": locator_id,
            "metadata": metadata,
            "updated_at": now,
        }
        if existing_node:
            client.table("rule_nodes").update(node_payload).eq("id", existing_node["id"]).execute()
        else:
            client.table("rule_nodes").insert(node_payload).execute()

        claim_rows = (
            client.table("claims")
            .select("*")
            .eq("claim_id", claim_id)
            .limit(2)
            .execute()
            .data
        )
        existing_claim = _one_or_none(claim_rows, f"claim {claim_id}")
        provenance = dict((existing_claim or {}).get("generator_provenance") or {})
        provenance.update(
            {
                "method": "curated_game_projection",
                "coverage": ruleset.coverage,
                "source_revision": spec.source.revision,
            }
        )
        claim_payload = {
            "claim_id": claim_id,
            "rule_set_id": ruleset_id,
            "claim_type": "normalized_rule_statement",
            "normalized_payload": {"statement": node.normalized_statement},
            "target_type": "rule_node",
            "rule_id": node.rule_id,
            "lifecycle_status": "accepted",
            "generator_provenance": provenance,
            "updated_at": now,
        }
        if existing_claim:
            client.table("claims").update(claim_payload).eq("claim_id", claim_id).execute()
        else:
            client.table("claims").insert(claim_payload).execute()

        binding_rows = (
            client.table("evidence_bindings")
            .select("*")
            .eq("binding_id", binding_id)
            .limit(2)
            .execute()
            .data
        )
        existing_binding = _one_or_none(binding_rows, f"evidence binding {binding_id}")
        reviewer = dict((existing_binding or {}).get("reviewer_provenance") or {})
        reviewer.update({"review": ruleset.authority, "canonical_source": "data/curated-games"})
        generator = dict((existing_binding or {}).get("generator_provenance") or {})
        generator.update({"method": "curated_game_projection"})
        binding_payload = {
            "binding_id": binding_id,
            "claim_id": claim_id,
            "source_id": source_id,
            "locator_id": locator_id,
            "relation": "supports",
            "reviewer_provenance": reviewer,
            "generator_provenance": generator,
            "verified_at": now,
        }
        if existing_binding:
            client.table("evidence_bindings").update(binding_payload).eq("binding_id", binding_id).execute()
        else:
            client.table("evidence_bindings").insert(binding_payload).execute()

    return ruleset_id


def verify_ruleset_live(spec: CuratedGameSpec, base_url: str) -> None:
    if spec.ruleset is None:
        return
    base = base_url.rstrip("/")
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        rulesets_response = client.get(f"{base}/api/games/{spec.slug}/rule-sets")
        if rulesets_response.status_code != 200:
            raise WorkflowError(
                f"production ruleset API failed: HTTP {rulesets_response.status_code} for {spec.slug}"
            )
        rulesets_payload = rulesets_response.json()
        matches = [
            row
            for row in (rulesets_payload.get("rulesets") or [])
            if row.get("revision_label") == spec.ruleset.revision_label
            and row.get("edition_label") == spec.ruleset.edition_label
            and row.get("language_code") == spec.ruleset.language_code
            and row.get("platform") == spec.ruleset.platform
        ]
        if len(matches) != 1:
            raise WorkflowError(f"production ruleset identity mismatch for {spec.slug}")
        ruleset_id = str(matches[0]["ruleset_id"])

        graph_response = client.get(
            f"{base}/api/games/{spec.slug}/rule-graph",
            params={"rule_set_id": ruleset_id},
        )
        if graph_response.status_code != 200:
            raise WorkflowError(
                f"production rule graph failed: HTTP {graph_response.status_code} for {spec.slug}"
            )
        graph = graph_response.json()
        actual = {
            node.get("rule_id"): node.get("normalized_statement")
            for node in (graph.get("nodes") or [])
        }
        for node in spec.ruleset.nodes:
            if actual.get(node.rule_id) != node.normalized_statement:
                raise WorkflowError(
                    f"production rule graph mismatch at {spec.slug}:{node.rule_id}"
                )


def validate_exposed_catalog_fields(expected: Any, actual: Any, path: str = "game") -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise WorkflowError(f"production catalog mismatch at {path}")
        for key, expected_value in expected.items():
            if key not in actual:
                continue
            validate_exposed_catalog_fields(expected_value, actual[key], f"{path}.{key}")
        return
    if expected != actual:
        raise WorkflowError(f"production catalog mismatch at {path}")


def verify_catalog_live(spec: CuratedGameSpec, base_url: str) -> None:
    require_publishable(spec)
    assert spec.source is not None
    assert spec.game is not None
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

        expected_public = dict(spec.game)
        review_status = str(spec.game.get("content_review_status") or "unknown")
        if review_status not in {"human_reviewed", "publisher_reviewed"}:
            expected_public.pop("summary", None)
            expected_public.pop("description", None)
        validate_exposed_catalog_fields(expected_public, payload)

        if review_status not in {"human_reviewed", "publisher_reviewed"}:
            title = str(spec.game.get("title_ja") or spec.game["title"])
            neutral = f"「{title}」の出典付きルール要約と出典情報を確認できます。"
            if payload.get("summary") != neutral or payload.get("description") != neutral:
                raise WorkflowError(
                    f"production player-summary projection mismatch for {spec.slug}"
                )

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


def verify_release(specs: list[CuratedGameSpec], base_url: str) -> None:
    generate_artifacts(specs)
    verify_frontend_release(specs, base_url)
    for spec in specs:
        if spec.is_publishable:
            verify_catalog_live(spec, base_url)
            verify_ruleset_live(spec, base_url)


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
    require_publishable(spec)
    verify_source_reachable_streamed(spec)
    client, plan = preflight_catalog(spec)
    generate_artifacts(specs)
    return client, plan


def add_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec]) -> None:
    if not spec.is_publishable:
        generate_artifacts(specs)
        print_routine_files(spec)
        print("Candidate fixed point: validated; production catalog unchanged")
        return
    prepare_game(spec, specs)
    print_routine_files(spec)
    print("Prepare fixed point: verified; production catalog unchanged until merge")


def publish_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec], base_url: str) -> None:
    if not spec.is_publishable:
        print(f"Catalog publish skipped for candidate {spec.slug}")
        return
    client, plan = prepare_game(spec, specs)
    game_row = write_catalog_with_plan(client, spec, plan)
    write_ruleset_projection(client, spec, game_row)
    verify_catalog_live(spec, base_url)
    verify_ruleset_live(spec, base_url)
    print(f"Catalog/ruleset publish fixed point: verified for {spec.slug}")


def check_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec]) -> None:
    generate_artifacts(specs)
    print_routine_files(spec)


def verify_game(spec: CuratedGameSpec, specs: list[CuratedGameSpec], base_url: str) -> None:
    require_publishable(spec)
    verify_source_reachable_streamed(spec)
    generate_artifacts(specs)
    verify_catalog_live(spec, base_url)
    verify_ruleset_live(spec, base_url)
    verify_frontend_release(specs, base_url, game=spec.slug)
    print("Catalog fixed point: verified")
    print("Frontend release fixed point: verified")


def check_all(specs: list[CuratedGameSpec]) -> None:
    generate_artifacts(specs)


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
        verify_release(specs, args.base_url)


if __name__ == "__main__":
    main()
