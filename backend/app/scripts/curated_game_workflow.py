from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
CURATED_DIR = REPO_ROOT / "data" / "curated-games"
DEFAULT_BASE_URL = "https://bodoge-no-mikata.vercel.app"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGACY_RULE_FIELDS = (
    "rules_content",
    "setup_summary",
    "gameplay_summary",
    "end_game_summary",
)


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


class CuratedGameSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    slug: str
    work: WorkSpec
    source: SourceSpec
    game: dict[str, Any]

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
            "source_url",
            "source_revision",
            "generated_from_source_revision",
        }
        missing = sorted(key for key in required_game if not self.game.get(key))
        if missing:
            raise ValueError(f"game fields missing: {', '.join(missing)}")
        forbidden = sorted(field for field in LEGACY_RULE_FIELDS if field in self.game)
        if forbidden:
            raise ValueError(
                "curated input must not contain RuleSet-owned fields: " + ", ".join(forbidden)
            )
        if self.game["slug"] != self.slug:
            raise ValueError("game.slug must match slug")
        if self.game["source_url"] != self.source.url:
            raise ValueError("game.source_url must match source.url")
        if self.game["source_revision"] != self.source.revision:
            raise ValueError("game.source_revision must match source.revision")
        if self.game["generated_from_source_revision"] != self.source.revision:
            raise ValueError("generated_from_source_revision must match source.revision")
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

    slug_row = slug_rows[0] if slug_rows else None
    if slug_row:
        slug_work_id = str(slug_row.get("work_id") or "") or None
        if not slug_work_id:
            raise WorkflowError(f"existing slug {spec.slug} has no canonical work_id")
        matching_work_rows = [row for row in work_rows if str(row.get("id")) == slug_work_id]
        if work_rows and len(matching_work_rows) != 1:
            raise WorkflowError(f"slug {spec.slug} belongs to a different canonical work")
        return IdentityPlan(game_id=str(slug_row["id"]), work_id=slug_work_id, create_work=False)

    if len(work_rows) > 1:
        raise WorkflowError(f"multiple canonical works match {spec.work.canonical_title}")

    work_row = work_rows[0] if work_rows else None
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
            actual_work = (
                client.table("game_works")
                .select("id,canonical_title,identity_status")
                .eq("id", slug_work_id)
                .execute()
                .data
            )
            if not actual_work or actual_work[0].get("canonical_title") != spec.work.canonical_title:
                raise WorkflowError(f"slug {spec.slug} resolves to a different canonical work")
            work_rows = actual_work

    edition_rows: list[dict[str, Any]] = []
    if len(work_rows) == 1:
        edition_rows = (
            client.table("games")
            .select("id,slug,work_id,edition_label,language_code,source_url,source_revision")
            .eq("work_id", work_rows[0]["id"])
            .execute()
            .data
        )

    return plan_identity(spec, slug_rows, work_rows, edition_rows)


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
