from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from app.models.component_ingestion import ComponentSourceManifest
from app.services.component_ingestion import ComponentIngestionDryRun, ExistingComponentSnapshot


def _load_manifest(path: Path) -> ComponentSourceManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ComponentSourceManifest.model_validate(payload)


def _existing_snapshot(path: Path, ruleset_id: str) -> ExistingComponentSnapshot:
    manifest = _load_manifest(path)
    return ExistingComponentSnapshot(
        ruleset_id=ruleset_id,
        component_sets=manifest.component_sets,
        property_definitions=[definition.model_dump(mode="json") for definition in manifest.property_definitions],
        components=manifest.components,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and dry-run a Component Source Manifest v1.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--resolved-ruleset-id",
        help="Exact RuleSet ID resolved by the caller. Required when the manifest uses a natural-key selector.",
    )
    parser.add_argument(
        "--existing-manifest",
        type=Path,
        help="Optional current-state fixture for deterministic diff testing. Production adapters may supply DB state instead.",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print the generated JSON Schema for Component Source Manifest v1 and exit.",
    )
    args = parser.parse_args()

    if args.schema:
        print(json.dumps(ComponentSourceManifest.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    manifest = _load_manifest(args.manifest)
    resolved_ruleset_id = args.resolved_ruleset_id or manifest.ruleset.ruleset_id
    existing = None
    if args.existing_manifest:
        if not resolved_ruleset_id:
            raise SystemExit("--existing-manifest requires --resolved-ruleset-id or manifest.ruleset.ruleset_id")
        existing = _existing_snapshot(args.existing_manifest, resolved_ruleset_id)

    report = ComponentIngestionDryRun().run(
        manifest,
        resolved_ruleset_id=resolved_ruleset_id,
        existing=existing,
    )
    print(report.model_dump_json(indent=2))
    return 2 if report.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
