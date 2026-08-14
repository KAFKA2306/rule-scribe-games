from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"
FORMS = [
    TEMPLATE_DIR / "01-feature.yml",
    TEMPLATE_DIR / "02-ai-data-quality.yml",
    TEMPLATE_DIR / "03-ops-bug.yml",
]
COMMON_IDS = {"problem", "evidence", "acceptance", "tests", "production_verification", "cleanup_rollback"}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_issue_forms_are_valid_structured_contracts():
    for path in FORMS:
        form = load_yaml(path)
        assert isinstance(form.get("name"), str) and len(form["name"]) > 3
        assert isinstance(form.get("description"), str) and form["description"].strip()
        assert isinstance(form.get("body"), list) and form["body"]

        fields = [item for item in form["body"] if item.get("type") != "markdown"]
        ids = [item.get("id") for item in fields]
        labels = [item.get("attributes", {}).get("label") for item in fields]

        assert None not in ids
        assert None not in labels
        assert len(ids) == len(set(ids)), f"duplicate ids in {path}"
        assert len(labels) == len(set(labels)), f"duplicate labels in {path}"
        assert COMMON_IDS <= set(ids), f"missing common completion fields in {path}"
        assert all(item.get("validations", {}).get("required") is True for item in fields if item["id"] in COMMON_IDS)


def test_specialized_forms_capture_domain_specific_evidence():
    ai_form = load_yaml(TEMPLATE_DIR / "02-ai-data-quality.yml")
    ai_ids = {item.get("id") for item in ai_form["body"]}
    assert {"source_contract", "evaluation", "dependencies"} <= ai_ids

    ops_form = load_yaml(TEMPLATE_DIR / "03-ops-bug.yml")
    ops_ids = {item.get("id") for item in ops_form["body"]}
    assert {"reproduction", "actual", "expected", "dependencies"} <= ops_ids

    feature_form = load_yaml(TEMPLATE_DIR / "01-feature.yml")
    feature_ids = {item.get("id") for item in feature_form["body"]}
    assert {"scope", "non_scope", "dependencies", "blockers"} <= feature_ids


def test_template_chooser_and_documentation_enforce_the_contract():
    config = load_yaml(TEMPLATE_DIR / "config.yml")
    assert config["blank_issues_enabled"] is False

    guide = (ROOT / "docs" / "ISSUE_GUIDE.md").read_text(encoding="utf-8")
    for heading in (
        "Acceptance Criteria",
        "Tests",
        "Production verification",
        "Cleanup / rollback condition",
        "Dependencies / blockers",
    ):
        assert heading in guide

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/ISSUE_GUIDE.md" in readme
