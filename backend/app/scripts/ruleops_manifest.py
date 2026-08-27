from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0"
REVIEWED = "reviewed"
PRIMARY_SOURCE_TYPES = {
    "publisher_rulebook",
    "publisher_rules_page",
    "publisher_faq",
    "publisher_errata",
    "publisher_product_page",
    "designer_rulebook",
    "creator_rulebook",
    "creator_listing",
}
RULE_SOURCE_TYPES = PRIMARY_SOURCE_TYPES - {"publisher_product_page", "creator_listing"}
CANONICAL_NODE_TYPES = {
    "setup",
    "turn",
    "action",
    "condition",
    "effect",
    "scoring",
    "round_end",
    "victory",
}
PLATFORMS = {"physical", "digital", "vrchat"}
METADATA_UNITS = {
    "min_players": "players",
    "max_players": "players",
    "play_time": "minutes",
    "published_year": "year",
}


@dataclass(frozen=True)
class ValidationError:
    slug: str
    code: str
    path: str
    message: str


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _http_url(value: Any) -> bool:
    if not _nonempty(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _error(errors: list[ValidationError], slug: str, code: str, path: str, message: str) -> None:
    errors.append(ValidationError(slug=slug, code=code, path=path, message=message))


def validate_game_manifest(game: dict[str, Any]) -> list[ValidationError]:
    slug = str(game.get("slug") or "<missing-slug>")
    errors: list[ValidationError] = []

    identity = game.get("identity")
    if not isinstance(identity, dict):
        _error(errors, slug, "missing_identity", "identity", "identity object is required")
        return errors

    for field in ("title", "edition", "language", "platform", "revision"):
        if not _nonempty(identity.get(field)):
            _error(errors, slug, "missing_identity_field", f"identity.{field}", f"{field} is required")

    if identity.get("platform") not in PLATFORMS:
        _error(
            errors,
            slug,
            "invalid_platform",
            "identity.platform",
            f"platform must be one of {sorted(PLATFORMS)}",
        )

    if game.get("review_status") != REVIEWED:
        _error(errors, slug, "game_not_reviewed", "review_status", "game manifest must be reviewed")

    scope = game.get("scope")
    if not isinstance(scope, dict):
        _error(errors, slug, "missing_scope", "scope", "scope object is required")
    else:
        if not _nonempty(scope.get("included_product")):
            _error(errors, slug, "missing_included_product", "scope.included_product", "included product is required")
        excluded = scope.get("excluded_products")
        if not isinstance(excluded, list):
            _error(errors, slug, "missing_excluded_products", "scope.excluded_products", "excluded_products must be a list")
        elif any(not _nonempty(item) for item in excluded):
            _error(errors, slug, "invalid_excluded_product", "scope.excluded_products", "excluded products must be non-empty strings")

    sources = game.get("sources")
    if not isinstance(sources, list) or not sources:
        _error(errors, slug, "missing_primary_source", "sources", "at least one primary source is required")
        sources = []

    source_by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            _error(errors, slug, "invalid_source", path, "source must be an object")
            continue
        source_id = source.get("source_id")
        if not _nonempty(source_id):
            _error(errors, slug, "missing_source_id", f"{path}.source_id", "source_id is required")
            continue
        if source_id in source_by_id:
            _error(errors, slug, "duplicate_source", f"{path}.source_id", f"duplicate source_id {source_id}")
        source_by_id[source_id] = source
        if source.get("source_type") not in PRIMARY_SOURCE_TYPES:
            _error(
                errors,
                slug,
                "invalid_source_type",
                f"{path}.source_type",
                f"source_type must be one of {sorted(PRIMARY_SOURCE_TYPES)}",
            )
        if not _http_url(source.get("url")):
            _error(errors, slug, "invalid_source_url", f"{path}.url", "source URL must be absolute http(s)")
        if source.get("review_status") != REVIEWED:
            _error(errors, slug, "source_not_reviewed", f"{path}.review_status", "source must be reviewed")
        if source.get("applies_to_revision") != identity.get("revision"):
            _error(
                errors,
                slug,
                "revision_mismatch",
                f"{path}.applies_to_revision",
                "source revision binding must exactly match identity.revision",
            )
        if source.get("applies_to_platform") != identity.get("platform"):
            _error(
                errors,
                slug,
                "platform_mismatch",
                f"{path}.applies_to_platform",
                "source platform binding must exactly match identity.platform",
            )

    metadata = game.get("metadata", [])
    if not isinstance(metadata, list):
        _error(errors, slug, "invalid_metadata", "metadata", "metadata must be a list")
        metadata = []

    metadata_fields: set[str] = set()
    metadata_values: dict[str, int] = {}
    for index, item in enumerate(metadata):
        path = f"metadata[{index}]"
        if not isinstance(item, dict):
            _error(errors, slug, "invalid_metadata_item", path, "metadata item must be an object")
            continue

        field = item.get("field")
        if field not in METADATA_UNITS:
            _error(
                errors,
                slug,
                "invalid_metadata_field",
                f"{path}.field",
                f"metadata field must be one of {sorted(METADATA_UNITS)}",
            )
            continue
        if field in metadata_fields:
            _error(errors, slug, "duplicate_metadata_field", f"{path}.field", f"duplicate metadata field {field}")
        metadata_fields.add(field)

        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            _error(errors, slug, "invalid_metadata_value", f"{path}.value", "metadata value must be a positive integer")
        else:
            metadata_values[field] = value

        if not _nonempty(item.get("display")):
            _error(errors, slug, "missing_metadata_display", f"{path}.display", "metadata display is required")

        expected_unit = METADATA_UNITS[field]
        if item.get("unit") != expected_unit:
            _error(
                errors,
                slug,
                "metadata_unit_mismatch",
                f"{path}.unit",
                f"{field} unit must be {expected_unit}",
            )

        if item.get("approximate") and field != "play_time":
            _error(
                errors,
                slug,
                "invalid_metadata_approximation",
                f"{path}.approximate",
                "approximate is only supported for play_time",
            )

        if item.get("review_status") != REVIEWED:
            _error(errors, slug, "metadata_not_reviewed", f"{path}.review_status", "metadata must be reviewed")

        source_id = item.get("source_id")
        if source_by_id.get(str(source_id)) is None:
            _error(errors, slug, "missing_metadata_source", f"{path}.source_id", "metadata must reference a declared source")

        if not _nonempty(item.get("evidence_locator")):
            _error(errors, slug, "missing_metadata_locator", f"{path}.evidence_locator", "metadata evidence locator is required")

    if (
        "min_players" in metadata_values
        and "max_players" in metadata_values
        and metadata_values["min_players"] > metadata_values["max_players"]
    ):
        _error(
            errors,
            slug,
            "invalid_player_range",
            "metadata",
            "min_players cannot exceed max_players",
        )

    rules = game.get("rules")
    if not isinstance(rules, list) or not rules:
        _error(errors, slug, "missing_rules", "rules", "at least one reviewed rule is required")
        rules = []

    rule_ids: set[str] = set()
    claims: set[str] = set()
    binding_keys: set[tuple[str, str, str]] = set()
    for index, rule in enumerate(rules):
        path = f"rules[{index}]"
        if not isinstance(rule, dict):
            _error(errors, slug, "invalid_rule", path, "rule must be an object")
            continue

        rule_id = rule.get("rule_id")
        if not _nonempty(rule_id):
            _error(errors, slug, "missing_rule_id", f"{path}.rule_id", "rule_id is required")
        elif rule_id in rule_ids:
            _error(errors, slug, "duplicate_rule", f"{path}.rule_id", f"duplicate rule_id {rule_id}")
        else:
            rule_ids.add(rule_id)

        node_type = rule.get("node_type")
        if node_type not in CANONICAL_NODE_TYPES:
            _error(
                errors,
                slug,
                "invalid_node_type",
                f"{path}.node_type",
                f"node_type must be one of {sorted(CANONICAL_NODE_TYPES)}",
            )

        claim = rule.get("claim")
        if not _nonempty(claim):
            _error(errors, slug, "missing_claim", f"{path}.claim", "claim text is required")
        elif claim in claims:
            _error(errors, slug, "duplicate_claim", f"{path}.claim", "duplicate claim text")
        else:
            claims.add(claim)

        if rule.get("review_status") != REVIEWED:
            _error(errors, slug, "rule_not_reviewed", f"{path}.review_status", "rule must be reviewed")

        source_id = rule.get("source_id")
        source = source_by_id.get(str(source_id))
        if source is None:
            _error(errors, slug, "missing_rule_source", f"{path}.source_id", "rule must reference a declared source")
        elif source.get("source_type") not in RULE_SOURCE_TYPES:
            _error(
                errors,
                slug,
                "non_rule_source",
                f"{path}.source_id",
                "rule claims require a rulebook/rules page/FAQ/errata/creator rule source, not identity-only evidence",
            )

        locator = rule.get("evidence_locator")
        if not _nonempty(locator):
            _error(errors, slug, "missing_evidence_locator", f"{path}.evidence_locator", "evidence locator is required")

        binding_key = (str(rule_id), str(source_id), str(locator))
        if binding_key in binding_keys:
            _error(errors, slug, "duplicate_binding", path, "duplicate rule/source/locator binding")
        else:
            binding_keys.add(binding_key)

    if bool(game.get("remove_legacy_authority")) and not rules:
        _error(
            errors,
            slug,
            "empty_replacement_coverage",
            "remove_legacy_authority",
            "legacy authority cannot be removed without reviewed source-bound rules",
        )

    return errors


def validate_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    batch_errors: list[ValidationError] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        batch_errors.append(
            ValidationError(
                slug="<batch>",
                code="unsupported_schema_version",
                path="schema_version",
                message=f"schema_version must be {SCHEMA_VERSION}",
            )
        )

    games = payload.get("games")
    if not isinstance(games, list) or not games:
        batch_errors.append(
            ValidationError(
                slug="<batch>", code="missing_games", path="games", message="games must be a non-empty list"
            )
        )
        games = []

    seen_slugs: set[str] = set()
    game_results: list[dict[str, Any]] = []
    for game in games:
        slug = str(game.get("slug") or "<missing-slug>") if isinstance(game, dict) else "<invalid-game>"
        errors = validate_game_manifest(game) if isinstance(game, dict) else [
            ValidationError(slug=slug, code="invalid_game", path="games", message="game must be an object")
        ]
        if slug in seen_slugs:
            errors.append(ValidationError(slug=slug, code="duplicate_game", path="slug", message="duplicate game slug"))
        seen_slugs.add(slug)
        game_results.append({
            "slug": slug,
            "status": "ready" if not errors else "blocked",
            "errors": [asdict(error) for error in errors],
        })

    all_errors = batch_errors + [
        ValidationError(**error)
        for result in game_results
        for error in result["errors"]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not all_errors else "blocked",
        "ready_games": sum(1 for result in game_results if result["status"] == "ready"),
        "blocked_games": sum(1 for result in game_results if result["status"] == "blocked"),
        "batch_errors": [asdict(error) for error in batch_errors],
        "games": game_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate reviewed RuleOps source manifests before SQL generation")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = validate_manifest(payload)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    raise SystemExit(0 if report["status"] == "ready" else 2)


if __name__ == "__main__":
    main()
