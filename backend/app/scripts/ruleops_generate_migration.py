from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.scripts.ruleops_manifest import validate_manifest


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def sql_text_array(values: list[str]) -> str:
    return "ARRAY[" + ",".join(sql_literal(value) for value in values) + "]::text[]"


def safe_identifier(value: str) -> str:
    rendered = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return rendered or "batch"


def source_trust(source_type: str) -> str:
    if source_type.startswith("publisher_"):
        return "official_publisher"
    if source_type.startswith(("designer_", "creator_")):
        return "authorized_partner"
    raise ValueError(f"unsupported primary source type: {source_type}")


def _render_source_rows(game: dict[str, Any]) -> str:
    identity = game["identity"]
    rows = []
    for source in game["sources"]:
        revision_label = source.get("revision_label") or identity["revision"]
        trust = json.dumps(
            {
                "authority": source["source_type"],
                "ruleops": True,
                "scope": game["scope"]["included_product"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        rows.append(
            "(" + ",".join(
                [
                    sql_literal(source["source_id"]),
                    sql_literal(source["url"]),
                    sql_literal(f"{identity['title']} — {source['source_type']}"),
                    sql_literal(source["source_type"]),
                    "NULL",
                    sql_literal(identity["platform"]),
                    sql_literal(identity["language"]),
                    sql_literal(revision_label),
                    sql_literal(trust) + "::jsonb",
                ]
            ) + ")"
        )
    return ",\n".join(rows)


def _render_locator_rows(game: dict[str, Any]) -> str:
    rows = []
    slug = game["slug"]
    for rule in game["rules"]:
        locator_id = f"{slug}:locator:{rule['rule_id']}"
        rows.append(
            "(" + ",".join(
                [
                    sql_literal(locator_id),
                    sql_literal(rule["source_id"]),
                    sql_literal(rule["evidence_locator"]),
                    sql_literal(rule["evidence_locator"]),
                ]
            ) + ")"
        )
    for item in game.get("metadata", []):
        locator_id = f"{slug}:locator:metadata:{item['field']}"
        rows.append(
            "(" + ",".join(
                [
                    sql_literal(locator_id),
                    sql_literal(item["source_id"]),
                    sql_literal(item["evidence_locator"]),
                    sql_literal(item["display"]),
                ]
            ) + ")"
        )
    return ",\n".join(rows)


def _render_rule_rows(game: dict[str, Any]) -> str:
    source_by_id = {source["source_id"]: source for source in game["sources"]}
    rows = []
    slug = game["slug"]
    for index, rule in enumerate(game["rules"], start=1):
        source = source_by_id[rule["source_id"]]
        metadata = json.dumps({"ruleops_batch": True}, separators=(",", ":"))
        rows.append(
            "(" + ",".join(
                [
                    "v_ruleset_id",
                    sql_literal(rule["rule_id"]),
                    sql_literal(rule["node_type"]),
                    sql_literal(rule["claim"]),
                    str(index * 10),
                    sql_literal("source_bound"),
                    sql_literal(f"{slug}:rule:{rule['rule_id']}"),
                    sql_literal(f"{slug}:binding:{rule['rule_id']}"),
                    sql_literal(source["url"]),
                    sql_literal(f"{slug}:locator:{rule['rule_id']}"),
                    sql_literal(metadata) + "::jsonb",
                ]
            ) + ")"
        )
    return ",\n".join(rows)


def _metadata_payload(item: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "value": item["value"],
        "display": item["display"],
        "unit": item["unit"],
    }
    if "approximate" in item:
        payload["approximate"] = item["approximate"]
    return payload


def _render_metadata_game_assignments(game: dict[str, Any]) -> str:
    return "".join(f", {item['field']}={item['value']}" for item in game.get("metadata", []))


def _render_metadata_claim_rows(game: dict[str, Any], batch_id: str) -> str:
    slug = game["slug"]
    rows = []
    provenance = json.dumps(
        {"method": "ruleops_reviewed_manifest", "batch_id": batch_id},
        separators=(",", ":"),
    )
    for item in game.get("metadata", []):
        payload = json.dumps(_metadata_payload(item), ensure_ascii=False, separators=(",", ":"))
        rows.append(
            "(" + ",".join(
                [
                    sql_literal(f"{slug}:metadata:{item['field']}"),
                    "v_ruleset_id",
                    sql_literal("game_metadata_value"),
                    sql_literal(payload) + "::jsonb",
                    sql_literal("game_metadata"),
                    sql_literal(item["field"]),
                    sql_literal("accepted"),
                    sql_literal(provenance) + "::jsonb",
                ]
            ) + ")"
        )
    return ",\n".join(rows)


def _render_metadata_binding_rows(game: dict[str, Any], batch_id: str) -> str:
    slug = game["slug"]
    rows = []
    generator = json.dumps({"batch_id": batch_id}, separators=(",", ":"))
    for item in game.get("metadata", []):
        rows.append(
            "(" + ",".join(
                [
                    sql_literal(f"{slug}:binding:metadata:{item['field']}"),
                    sql_literal(f"{slug}:metadata:{item['field']}"),
                    sql_literal(item["source_id"]),
                    sql_literal(f"{slug}:locator:metadata:{item['field']}"),
                    sql_literal("supports"),
                    sql_literal('{"review":"ruleops_reviewed_manifest"}') + "::jsonb",
                    sql_literal(generator) + "::jsonb",
                    "now()",
                ]
            ) + ")"
        )
    return ",\n".join(rows)


def _render_metadata_sql(game: dict[str, Any], batch_id: str) -> str:
    metadata = game.get("metadata", [])
    if not metadata:
        return ""

    slug = game["slug"]
    claim_rows = _render_metadata_claim_rows(game, batch_id)
    binding_rows = _render_metadata_binding_rows(game, batch_id)
    assertions = []
    for item in metadata:
        field = item["field"]
        value = item["value"]
        assertions.append(
            f"  IF (SELECT {field} FROM public.games WHERE id=v_game_id) IS DISTINCT FROM {value}\n"
            f"    THEN RAISE EXCEPTION 'RuleOps {slug} canonical {field} must equal reviewed metadata value {value}'; END IF;"
        )
        assertions.append(
            f"  IF (SELECT count(*) FROM public.claims WHERE claim_id={sql_literal(f'{slug}:metadata:{field}')} "
            "AND rule_set_id=v_ruleset_id AND target_type='game_metadata' AND lifecycle_status='accepted') <> 1\n"
            f"    THEN RAISE EXCEPTION 'RuleOps {slug} metadata claim {field} must exist exactly once'; END IF;"
        )
        assertions.append(
            "  IF (SELECT count(*) FROM public.evidence_bindings eb "
            f"WHERE eb.claim_id={sql_literal(f'{slug}:metadata:{field}')} AND eb.relation='supports') <> 1\n"
            f"    THEN RAISE EXCEPTION 'RuleOps {slug} metadata evidence {field} must exist exactly once'; END IF;"
        )

    return f"""
  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,field_path,lifecycle_status,generator_provenance
  ) VALUES
{claim_rows}
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,field_path=EXCLUDED.field_path,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
{binding_rows}
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

{chr(10).join(assertions)}
""".rstrip()


def render_game_sql(game: dict[str, Any], batch_id: str) -> str:
    slug = game["slug"]
    identity = game["identity"]
    first_source = game["sources"][0]
    source_ids = [source["source_id"] for source in game["sources"]]
    count = len(game["rules"])
    legacy_reset = ""
    if game.get("remove_legacy_authority"):
        legacy_reset = (
            ", rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, "
            "setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL"
        )

    binding_values = []
    for rule in game["rules"]:
        binding_values.append(
            "(" + ",".join(
                [
                    sql_literal(f"{slug}:binding:{rule['rule_id']}"),
                    sql_literal(f"{slug}:rule:{rule['rule_id']}"),
                    sql_literal(rule["source_id"]),
                    sql_literal(f"{slug}:locator:{rule['rule_id']}"),
                    sql_literal("supports"),
                    sql_literal('{"review":"ruleops_reviewed_manifest"}') + "::jsonb",
                    sql_literal(json.dumps({"batch_id": batch_id}, separators=(",", ":"))) + "::jsonb",
                    "now()",
                ]
            ) + ")"
        )

    source_revision = identity["revision"]
    trust = source_trust(first_source["source_type"])
    metadata_assignments = _render_metadata_game_assignments(game)
    metadata_sql = _render_metadata_sql(game, batch_id)
    return f"""
-- RuleOps game: {slug} / {identity['edition']} / {identity['revision']}
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
{_render_source_rows(game)}
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
{_render_locator_rows(game)}
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug={sql_literal(slug)} LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game {slug} absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for {slug}'; END IF;

  UPDATE public.games SET
    title={sql_literal(identity['title'])},
    identity_status='verified', identity_source={sql_literal(first_source['url'])},
    source_url={sql_literal(first_source['url'])}, source_trust={sql_literal(trust)},
    content_review_status='review_required', is_official=true,
    edition_label={sql_literal(identity['edition'])}, language_code={sql_literal(identity['language'])},
    source_revision={sql_literal(source_revision)}, updated_at=now(){metadata_assignments}{legacy_reset}
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')={sql_literal(identity['language'])}
    AND COALESCE(edition_label,'')={sql_literal(identity['edition'])}
    AND COALESCE(platform,'')={sql_literal(identity['platform'])}
    AND COALESCE(revision_label,'')={sql_literal(identity['revision'])}
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0',{sql_literal(identity['language'])},{sql_literal(identity['edition'])},
      {sql_literal(source_revision)},true,{sql_literal(identity['revision'])},{sql_literal(identity['platform'])},NULL,
      'active','source_bound',{sql_text_array(source_ids)}
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision={sql_literal(source_revision)},source_ids={sql_text_array(source_ids)},updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
{_render_rule_rows(game)}
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT {sql_literal(slug + ':rule:')}||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    {sql_literal(json.dumps({'method': 'ruleops_reviewed_manifest', 'batch_id': batch_id}, separators=(',', ':')))}::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
{','.join(chr(10) + value for value in binding_values).lstrip()}
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

{metadata_sql}

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> {count}
    THEN RAISE EXCEPTION 'RuleOps {slug} RuleNode count must be {count}'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> {count}
    THEN RAISE EXCEPTION 'RuleOps {slug} Claim count must be {count}'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports' AND c.target_type='rule_node') <> {count}
    THEN RAISE EXCEPTION 'RuleOps {slug} EvidenceBinding count must be {count}'; END IF;
END $$;
""".strip()


def generate_migration(payload: dict[str, Any], migration_number: str) -> tuple[str, dict[str, Any]]:
    validation = validate_manifest(payload)
    result_by_slug = {result["slug"]: result for result in validation["games"]}
    ready_games = [game for game in payload.get("games", []) if result_by_slug.get(game.get("slug"), {}).get("status") == "ready"]
    blocked_games = [result for result in validation["games"] if result["status"] == "blocked"]
    if not ready_games:
        raise ValueError("manifest has no ready games; migration was not generated")

    batch_id = payload["batch_id"]
    sections = [render_game_sql(game, batch_id) for game in ready_games]
    sql = "BEGIN;\n\n" + "\n\n".join(sections) + "\n\nCOMMIT;\n"
    report = {
        "schema_version": payload.get("schema_version"),
        "batch_id": batch_id,
        "migration_number": migration_number,
        "generated_games": [game["slug"] for game in ready_games],
        "blocked_games": blocked_games,
        "status": "generated_with_blocks" if blocked_games else "generated",
    }
    return sql, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reviewed RuleOps source-bound SQL without writing to production")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--migration-number", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("backend/app/db/migrations"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    sql, report = generate_migration(payload, args.migration_number)
    filename = f"{args.migration_number}_ruleops_{safe_identifier(payload['batch_id'])}.sql"
    output = args.output_dir / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(sql, encoding="utf-8")
    report["output"] = str(output)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
