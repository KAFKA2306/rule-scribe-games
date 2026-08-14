from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
CURATED_DIR = REPO_ROOT / "data" / "curated-games"
GENERATED_GUIDES_PATH = REPO_ROOT / "frontend" / "src" / "lib" / "generatedCuratedRuleGuides.js"
CURATED_GUIDES_PATH = REPO_ROOT / "frontend" / "src" / "lib" / "curatedRuleGuides.js"
DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorkflowError(RuntimeError):
    pass


class WorkSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_title: str = Field(min_length=1)
    identity_status: str = Field(pattern=r"^(verified|needs_review|unverified)$")


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(pattern=r"^https://")
    rule_version: str = Field(min_length=1)
    revision: str = Field(min_length=1)


class AssertionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    equals: Any | None = None
    contains: str | None = None

    @model_validator(mode="after")
    def require_one_operator(self):
        has_equals = "equals" in self.model_fields_set
        has_contains = "contains" in self.model_fields_set
        if has_equals == has_contains:
            raise ValueError("assertion requires exactly one of equals or contains")
        if has_contains and not self.contains:
            raise ValueError("contains must be non-empty")
        return self


class CuratedGameSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    slug: str
    work: WorkSpec
    source: SourceSpec
    game: dict[str, Any]
    guide: dict[str, Any]
    assertions: list[AssertionSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self):
        if self.schema_version != "1":
            raise ValueError("schema_version must be 1")
        if not SLUG_RE.fullmatch(self.slug):
            raise ValueError("slug must be canonical kebab-case")
        required_game = {
            "slug",
            "title",
            "summary",
            "rules_content",
            "source_url",
            "source_revision",
            "generated_from_source_revision",
        }
        missing = sorted(key for key in required_game if not self.game.get(key))
        if missing:
            raise ValueError(f"game fields missing: {', '.join(missing)}")
        if self.game["slug"] != self.slug:
            raise ValueError("game.slug must match slug")
        if self.game["source_url"] != self.source.url:
            raise ValueError("game.source_url must match source.url")
        if self.game["source_revision"] != self.source.revision:
            raise ValueError("game.source_revision must match source.revision")
        if self.game["generated_from_source_revision"] != self.source.revision:
            raise ValueError("generated_from_source_revision must match source.revision")
        if self.guide.get("reviewed") is not True:
            raise ValueError("guide.reviewed must be true")
        if self.guide.get("ruleVersion") != self.source.rule_version:
            raise ValueError("guide.ruleVersion must match source.rule_version")
        guide_source = self.guide.get("source") or {}
        if guide_source.get("url") != self.source.url:
            raise ValueError("guide.source.url must match source.url")
        if guide_source.get("ruleVersion") != self.source.rule_version:
            raise ValueError("guide.source.ruleVersion must match source.rule_version")
        quick = self.guide.get("quick") or {}
        if not quick.get("win") or not quick.get("end"):
            raise ValueError("guide quick win/end are required")
        if not quick.get("turnSteps") or not quick.get("turnEndChecks"):
            raise ValueError("guide turnSteps/turnEndChecks are required")
        if len(self.guide.get("flow") or []) < 2:
            raise ValueError("guide flow requires at least two nodes")
        return self


@dataclass(frozen=True)
class IdentityPlan:
    game_id: str | None
    work_id: str | None
    create_work: bool


def load_spec(path: Path) -> CuratedGameSpec:
    return CuratedGameSpec.model_validate_json(path.read_text(encoding="utf-8"))


def load_all_specs() -> list[CuratedGameSpec]:
    paths = sorted(path for path in CURATED_DIR.glob("*.json") if not path.name.startswith("schema-"))
    specs = [load_spec(path) for path in paths]
    slugs = [spec.slug for spec in specs]
    if len(slugs) != len(set(slugs)):
        raise WorkflowError("duplicate slug in structured curated inputs")
    return specs


def get_path(value: Any, path: str) -> Any:
    current = value
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
            continue
        raise WorkflowError(f"assertion path not found: {path}")
    return current


def validate_assertions(spec: CuratedGameSpec) -> None:
    for assertion in spec.assertions:
        actual = get_path(spec.guide, assertion.path)
        if "equals" in assertion.model_fields_set and actual != assertion.equals:
            raise WorkflowError(f"assertion failed: {assertion.path} != {assertion.equals!r}")
        if "contains" in assertion.model_fields_set:
            expected = assertion.contains or ""
            if isinstance(actual, list):
                matched = any(expected in str(item) for item in actual)
            else:
                matched = expected in str(actual)
            if not matched:
                raise WorkflowError(f"assertion failed: {assertion.path} does not contain {expected!r}")


def render_generated_registry(specs: list[CuratedGameSpec]) -> str:
    registry = {spec.slug: spec.guide for spec in sorted(specs, key=lambda item: item.slug)}
    rendered = json.dumps(registry, ensure_ascii=False, indent=2)
    return f"export const GENERATED_CURATED_RULE_GUIDES = {rendered}\n"


def materialize_registry(specs: list[CuratedGameSpec], check_only: bool) -> None:
    expected = render_generated_registry(specs)
    current = GENERATED_GUIDES_PATH.read_text(encoding="utf-8") if GENERATED_GUIDES_PATH.exists() else ""
    if check_only:
        if current != expected:
            raise WorkflowError("generatedCuratedRuleGuides.js is stale; run task game:add or materialize the registry")
        return
    if current != expected:
        GENERATED_GUIDES_PATH.write_text(expected, encoding="utf-8")


def validate_runtime_guide(spec: CuratedGameSpec) -> None:
    module_uri = CURATED_GUIDES_PATH.resolve().as_uri()
    expression = (
        f"import {{ getCuratedRuleGuide }} from {json.dumps(module_uri)}; "
        f"process.stdout.write(JSON.stringify(getCuratedRuleGuide({json.dumps(spec.slug)})));"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", expression],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    runtime_guide = json.loads(result.stdout or "null")
    if runtime_guide != spec.guide:
        raise WorkflowError(f"runtime curated guide differs from structured input: {spec.slug}")


def verify_source_reachable(spec: CuratedGameSpec) -> None:
    headers = {"User-Agent": "BodogeNoMikataSourceVerifier/1.0 (+https://bodoge-no-mikata.vercel.app/)"}
    with httpx.Client(follow_redirects=True, timeout=20, headers=headers) as client:
        response = client.get(spec.source.url)
    if response.status_code < 200 or response.status_code >= 400:
        raise WorkflowError(f"primary source is not reachable: HTTP {response.status_code} {spec.source.url}")


def plan_identity(
    spec: CuratedGameSpec,
    slug_rows: list[dict[str, Any]],
    work_rows: list[dict[str, Any]],
    edition_rows: list[dict[str, Any]],
) -> IdentityPlan:
    if len(slug_rows) > 1:
        raise WorkflowError(f"multiple games already use slug {spec.slug}")
    if len(work_rows) > 1:
        raise WorkflowError(f"multiple canonical works match {spec.work.canonical_title}")

    slug_row = slug_rows[0] if slug_rows else None
    work_row = work_rows[0] if work_rows else None

    if slug_row:
        slug_work_id = str(slug_row.get("work_id") or "") or None
        if not slug_work_id:
            raise WorkflowError(f"existing slug {spec.slug} has no canonical work_id")
        if work_row and slug_work_id != str(work_row["id"]):
            raise WorkflowError(f"slug {spec.slug} belongs to a different canonical work")
        return IdentityPlan(game_id=str(slug_row["id"]), work_id=slug_work_id, create_work=False)

    if work_row:
        edition_label = spec.game.get("edition_label")
        language_code = spec.game.get("language_code")
        for row in edition_rows:
            if row.get("edition_label") == edition_label and row.get("language_code") == language_code:
                raise WorkflowError(
                    f"canonical work already has this edition/language under slug {row.get('slug')}; refusing duplicate"
                )
        return IdentityPlan(game_id=None, work_id=str(work_row["id"]), create_work=False)

    return IdentityPlan(game_id=None, work_id=None, create_work=True)


def preflight_identity(client: Any, spec: CuratedGameSpec) -> IdentityPlan:
    slug_rows = (
        client.table("games")
        .select("id,slug,work_id,edition_label,language_code,source_url,source_revision")
        .eq("slug", spec.slug)
        .execute()
        .data
    )
    work_rows = (
        client.table("game_works")
        .select("id,canonical_title,identity_status")
        .eq("canonical_title", spec.work.canonical_title)
        .execute()
        .data
    )

    if slug_rows and not work_rows:
        slug_work_id = slug_rows[0].get("work_id")
        if slug_work_id:
            actual_work = client.table("game_works").select("id,canonical_title,identity_status").eq("id", slug_work_id).execute().data
            if not actual_work or actual_work[0].get("canonical_title") != spec.work.canonical_title:
                raise WorkflowError(f"slug {spec.slug} resolves to a different canonical work")
            work_rows = actual_work

    edition_rows: list[dict[str, Any]] = []
    if work_rows:
        edition_rows = (
            client.table("games")
            .select("id,slug,work_id,edition_label,language_code,source_url,source_revision")
            .eq("work_id", work_rows[0]["id"])
            .execute()
            .data
        )

    return plan_identity(spec, slug_rows, work_rows, edition_rows)


def write_catalog(spec: CuratedGameSpec) -> dict[str, Any]:
    from app.core import supabase

    client = supabase._get_client()
    plan = preflight_identity(client, spec)
    created_work_id: str | None = None
    work_id = plan.work_id

    if plan.create_work:
        rows = (
            client.table("game_works")
            .insert({"canonical_title": spec.work.canonical_title, "identity_status": spec.work.identity_status})
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
    return rows[0]


def verify_production(spec: CuratedGameSpec, base_url: str) -> None:
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


def validate_expectations(spec: CuratedGameSpec, expected_slug: str | None, expected_source_url: str | None) -> None:
    if expected_slug is not None and spec.slug != expected_slug:
        raise WorkflowError(f"expected slug {expected_slug}, got {spec.slug}")
    if expected_source_url is not None and spec.source.url != expected_source_url:
        raise WorkflowError("SOURCE_URL does not match the structured primary source")


def print_pr_ready_files() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    print("PR-ready changed files:")
    for path in sorted(set(paths)):
        print(f"- {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--expected-slug")
    parser.add_argument("--expected-source-url")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--check-materialization", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-production", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.all == bool(args.file):
        raise WorkflowError("provide exactly one of --file or --all")

    specs = load_all_specs() if args.all else [load_spec(Path(args.file).resolve())]
    all_specs = load_all_specs()

    for spec in specs:
        validate_expectations(spec, args.expected_slug, args.expected_source_url)
        validate_assertions(spec)
        if not args.offline:
            verify_source_reachable(spec)

    materialize_registry(all_specs, args.check_materialization)

    for spec in specs:
        validate_runtime_guide(spec)
        if args.write:
            row = write_catalog(spec)
            if row.get("slug") != spec.slug:
                raise WorkflowError("catalog write returned unexpected slug")
        if args.verify_production:
            verify_production(spec, args.base_url)

    print_pr_ready_files()


if __name__ == "__main__":
    main()
