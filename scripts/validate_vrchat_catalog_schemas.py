#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "vrchat"
MANIFEST_SCHEMA_PATH = SCHEMA_DIR / "board-game-module-manifest-v1.schema.json"
CATALOG_SCHEMA_PATH = SCHEMA_DIR / "manifest-catalog-v1.schema.json"
READ_SCHEMA_PATH = SCHEMA_DIR / "manifest-read-response-v1.schema.json"
MANIFEST_FIXTURES_PATH = ROOT / "evaluation" / "vrchat" / "manifest-v1-fixtures.json"
REVISION = "a" * 64


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema: dict, manifest_schema: dict) -> Draft202012Validator:
    registry = Registry().with_resource(
        manifest_schema["$id"],
        Resource.from_contents(manifest_schema),
    )
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def _expect_invalid(validator: Draft202012Validator, payload: dict, label: str) -> None:
    try:
        validator.validate(payload)
    except ValidationError:
        return
    raise AssertionError(f"expected schema rejection: {label}")


def main() -> int:
    manifest_schema = _load(MANIFEST_SCHEMA_PATH)
    catalog_schema = _load(CATALOG_SCHEMA_PATH)
    read_schema = _load(READ_SCHEMA_PATH)

    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator.check_schema(catalog_schema)
    Draft202012Validator.check_schema(read_schema)

    fixtures = _load(MANIFEST_FIXTURES_PATH)
    manifest = fixtures["cases"][0]["manifest"]

    catalog_validator = _validator(catalog_schema, manifest_schema)
    read_validator = _validator(read_schema, manifest_schema)

    catalog = {
        "schemaVersion": "1.0",
        "catalogRevision": REVISION,
        "manifestSchemaVersion": "1.0",
        "entries": [
            {
                "slug": manifest["slug"],
                "rulesetId": manifest["rulesetId"],
                "moduleId": manifest["moduleId"],
                "moduleVersionRange": manifest["moduleVersionRange"],
                "status": "playable",
                "reasonCode": None,
                "manifestPath": (
                    f"/api/vrchat/v1/manifests/{manifest['slug']}/{manifest['rulesetId']}"
                ),
                "manifestSchemaVersion": "1.0",
            },
            {
                "slug": "unsupported-example",
                "rulesetId": "ruleset-unsupported",
                "moduleId": "vrmine.unsupported-example",
                "moduleVersionRange": ">=1.0.0,<2.0.0",
                "status": "unsupported",
                "reasonCode": "DEXTERITY_UNSUPPORTED",
                "manifestPath": (
                    "/api/vrchat/v1/manifests/unsupported-example/ruleset-unsupported"
                ),
                "manifestSchemaVersion": "1.0",
            },
        ],
    }
    catalog_validator.validate(catalog)

    available = {
        "schemaVersion": "1.0",
        "status": "available",
        "slug": manifest["slug"],
        "rulesetId": manifest["rulesetId"],
        "reasonCode": None,
        "manifest": manifest,
    }
    unavailable = {
        "schemaVersion": "1.0",
        "status": "not_registered",
        "slug": "missing-example",
        "rulesetId": "ruleset-missing",
        "reasonCode": "MODULE_BINDING_NOT_REGISTERED",
        "manifest": None,
    }
    read_validator.validate(available)
    read_validator.validate(unavailable)

    bad_revision = copy.deepcopy(catalog)
    bad_revision["catalogRevision"] = "not-a-sha256"
    _expect_invalid(catalog_validator, bad_revision, "catalog revision")

    bad_catalog_reason = copy.deepcopy(catalog)
    bad_catalog_reason["entries"][1]["reasonCode"] = None
    _expect_invalid(catalog_validator, bad_catalog_reason, "blocked catalog reasonCode")

    missing_manifest = copy.deepcopy(available)
    missing_manifest["manifest"] = None
    _expect_invalid(read_validator, missing_manifest, "available response without manifest")

    leaked_manifest = copy.deepcopy(unavailable)
    leaked_manifest["manifest"] = manifest
    _expect_invalid(read_validator, leaked_manifest, "blocked response with manifest")

    print("VRChat catalog/read-response Draft 2020-12 schemas: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())