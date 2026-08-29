#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import importlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
_QUOTED_VALUE_MIN_LENGTH = 2


def _load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if (
            len(value) >= _QUOTED_VALUE_MIN_LENGTH
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]
        os.environ[key] = value.replace("\\n", "\n")


def _write_csv(report, path: Path) -> None:
    fieldnames = [
        "gameId",
        "slug",
        "title",
        "rulesetId",
        "readinessStatus",
        "requiredCapabilities",
        "unknownCapabilities",
        "missingCapabilities",
        "dataBlockers",
        "evidenceBlockers",
        "rightsBlockers",
        "runtimeBlockers",
        "recommendedModuleClass",
        "manifestProjectable",
        "moduleId",
        "promotableToCatalog",
        "auditedAt",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in report.records:
            payload = record.model_dump(mode="json", by_alias=True)
            row = {}
            for field in fieldnames:
                value = payload.get(field)
                row[field] = (
                    json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    if isinstance(value, (list, dict))
                    else value
                )
            writer.writerow(row)


async def _run(args: argparse.Namespace) -> int:
    if args.env_file:
        _load_env_file(args.env_file)
    sys.path.insert(0, str(BACKEND))
    audit_module = importlib.import_module("app.services.vrchat_readiness_policy")
    service = audit_module.StrictVrchatReadinessAuditService()
    if getattr(service.game_service, "use_local", False):
        raise RuntimeError(
            "production readiness audit requires configured Supabase; local fallback is not accepted"
        )

    audited_at = datetime.now(UTC)
    report = await service.audit_all(audited_at=audited_at)

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(
            report.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_csv(report, args.csv_output)

    summary = {
        "schemaVersion": report.schema_version,
        "auditedAt": report.audited_at.isoformat(),
        "totalGames": report.total_games,
        "totalRecords": report.total_records,
        "promotableCount": report.promotable_count,
        "statusCounts": {
            status.value: count for status, count in report.status_counts.items()
        },
        "jsonOutput": str(args.json_output),
        "csvOutput": str(args.csv_output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit every canonical game for VRChat port readiness.")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "artifacts" / "vrchat-readiness" / "readiness.json",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=ROOT / "artifacts" / "vrchat-readiness" / "readiness.csv",
    )
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
