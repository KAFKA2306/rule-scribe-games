import json
import subprocess
from pathlib import Path

import pytest

import app.scripts.curated_game_fast_path_v2 as v2
from app.scripts.curated_game_workflow import WorkflowError, load_all_specs, load_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
SKULL_KING = REPO_ROOT / "data" / "curated-games" / "skull-king.json"
GENERATED_GUIDES = REPO_ROOT / "frontend" / "src" / "lib" / "generatedCuratedRuleGuides.js"
PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"


def test_single_input_resolves_canonical_spec():
    specs = load_all_specs()
    spec = v2.load_named_spec("skull-king", specs)

    assert spec.slug == "skull-king"
    assert v2.resolve_spec_path("skull-king") == SKULL_KING


def test_filename_game_and_slug_must_match(tmp_path, monkeypatch):
    source = SKULL_KING.read_text(encoding="utf-8")
    fake_dir = tmp_path / "curated-games"
    fake_dir.mkdir()
    (fake_dir / "wrong-name.json").write_text(source, encoding="utf-8")
    monkeypatch.setattr(v2, "CURATED_DIR", fake_dir)

    with pytest.raises(WorkflowError, match="filename, GAME, and canonical slug"):
        v2.resolve_spec_path("wrong-name")


def test_deployment_manifest_is_deterministic_and_revision_bound():
    specs = load_all_specs()
    first = v2.render_deployment_manifest(specs)
    second = v2.render_deployment_manifest(list(reversed(specs)))

    assert first == second
    payload = v2.deployment_manifest_payload(specs)
    assert len(payload["revision_contract_sha256"]) == 64
    assert payload["games"]["skull-king"] == {
        "rule_version": "grandpa-becks-current-2026-08-14",
        "source_revision": "grandpa-becks-current-rulebook-accessed-2026-08-14",
    }


def test_node_generator_matches_python_contract_from_source():
    specs = load_all_specs()

    v2.generate_artifacts(specs)

    assert v2.DEPLOYMENT_MANIFEST_PATH.read_text(encoding="utf-8") == v2.render_deployment_manifest(specs)
    assert GENERATED_GUIDES.is_file()


def test_npm_dev_and_build_generate_curated_artifacts():
    scripts = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["scripts"]

    assert scripts["curated:generate"] == "node scripts/generate-curated-game-artifacts.mjs"
    assert scripts["predev"] == "npm run curated:generate"
    assert scripts["prebuild"] == "npm run curated:generate"


def test_git_tracks_curated_sources_but_ignores_generated_artifacts():
    future_source = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "data/curated-games/future-game.json"],
        cwd=REPO_ROOT,
        check=False,
    )
    generated_guide = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "frontend/src/lib/generatedCuratedRuleGuides.js"],
        cwd=REPO_ROOT,
        check=False,
    )
    generated_manifest = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "frontend/public/curated-guides-manifest.json"],
        cwd=REPO_ROOT,
        check=False,
    )

    assert future_source.returncode == 1
    assert generated_guide.returncode == 0
    assert generated_manifest.returncode == 0


def test_prepare_add_preflights_before_generation(monkeypatch):
    spec = load_spec(SKULL_KING)
    specs = [spec]
    events = []
    plan = object()
    client = object()

    monkeypatch.setattr(v2, "validate_assertions", lambda value: events.append("assertions"))
    monkeypatch.setattr(v2, "verify_source_reachable_streamed", lambda value: events.append("source"))

    def fake_preflight(value):
        events.append("preflight")
        return client, plan

    monkeypatch.setattr(v2, "preflight_catalog", fake_preflight)
    monkeypatch.setattr(v2, "generate_artifacts", lambda values: events.append("generate"))
    monkeypatch.setattr(v2, "validate_runtime_guide", lambda value: events.append("runtime"))

    actual_client, actual_plan = v2.prepare_add(spec, specs)

    assert actual_client is client
    assert actual_plan is plan
    assert events == ["assertions", "source", "preflight", "generate", "runtime"]


def test_release_manifest_digest_mismatch_fails():
    specs = load_all_specs()
    expected = v2.deployment_manifest_payload(specs)
    deployed = dict(expected)
    deployed["revision_contract_sha256"] = "0" * 64

    with pytest.raises(WorkflowError, match="revision contract"):
        v2.validate_release_manifest(expected, deployed, game="skull-king")


def test_routine_pr_contains_only_structured_source():
    spec = load_spec(SKULL_KING)

    assert v2.routine_files(spec) == ["data/curated-games/skull-king.json"]
