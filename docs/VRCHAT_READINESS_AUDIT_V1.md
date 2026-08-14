# VRChat Readiness Audit v1

Issue: https://github.com/KAFKA2306/rule-scribe-games/issues/185

## Purpose

This audit classifies every canonical RuleScribe game/RuleSet for the next VRMine porting step.
It does **not** generate game rules, infer facts from prose, or mark a game playable merely because a
title or component exists.

The machine-readable statuses are:

- `ready`
- `blocked`
- `review-required`
- `unsupported`

The audit produces one record for each canonical RuleSet. A game with no canonical RuleSet still
produces one blocked game-level record, so the catalog cannot disappear from the report simply
because ontology data is incomplete.

## Source-of-truth boundary

The audit reads only existing canonical structures:

- `GameDetail`
- `RuleSet`
- `RuleGraphReadResponse`
- `ComponentCatalog` / component lists
- the versioned #184 `module-bindings-v1.json`
- the #183 deterministic manifest projector

Legacy `structured_data.mechanics`, free-form rule text, title keywords, BGG categories, and LLM
interpretation are not used to promote capabilities.

Production execution uses `StrictVrchatReadinessAuditService`. The underlying traversal service is
kept separate so catalog pagination/binding mechanics do not redefine evidence, runtime capability,
or rights policy.

## Rule coverage

Each RuleSet is independently checked for six runtime-critical dimensions:

1. setup
2. loop (`phase` and/or `turn`)
3. action
4. resolution (`effect` and/or `conflict_resolution`)
5. game end
6. win / victory

Missing dimensions are data blockers. Under the strict production policy, an existing RuleNode only
counts as evidence-backed when its verification state is `source_bound` or `verified` **and it has a
field-level `evidence_ref`**. A `source_url` or claim reference alone is not enough to promote the
node to evidence-backed status.

This intentionally aligns the VRChat release gate with #175: source existence and claim support are
different states. Until the field-level evidence migration is complete, affected records remain
`review-required` rather than being silently promoted.

RuleSets are never merged to fill one another's gaps. Multiple active RuleSets with the same
language/edition/platform identity are reported as `AMBIGUOUS_ACTIVE_RULESET_IDENTITY` until the
identity conflict is resolved.

## Capability requirements

The v1 runtime capabilities are the exact #183 manifest capabilities:

- turn-based
- simultaneous
- hidden-information
- deck
- dice
- tokens
- board
- score
- timer
- realtime
- dexterity

A capability becomes `required` or `not-required` only when a source-bound/verified RuleNode with a
field-level `evidence_ref` explicitly declares it in `metadata.vrchat_capabilities`.

Examples:

```json
{
  "vrchat_capabilities": {
    "deck": "required",
    "hidden-information": "required",
    "dexterity": "not-required"
  }
}
```

Component kind is descriptive evidence about the physical game contents; it is **not** a runtime
requirement by itself. In particular:

- the presence of cards does not prove that VRMine needs deck/shuffle/draw semantics;
- tiles do not automatically imply a board-state engine;
- figures/markers do not automatically imply generic token semantics;
- a victory node does not automatically imply a numeric score system.

Conflicting explicit declarations are not resolved by precedence; they become evidence blockers.
Anything without explicit verified capability evidence remains `unknown`.

## Component completeness

The current Component Catalog v1 has identity, kind, properties, verification and source fields but
no canonical all-items completeness state. Therefore an available catalog currently emits
`COMPONENT_COMPLETENESS_UNKNOWN` instead of assuming that the observed rows are exhaustive.

Issue #178 owns the generic complete/partial/unknown ingestion contract. When that canonical state
exists, this audit should consume it instead of the conservative blocker.

## Runtime reconciliation

The #184 production binding registry is reconciled by exact `(slug, rulesetId)`.

- no binding -> `MODULE_BINDING_NOT_REGISTERED`
- required capability not declared `supported` -> `REQUIRED_RUNTIME_CAPABILITY_MISSING`
- explicit `unsupported` publication state -> `unsupported`
- compatible binding + canonical inputs -> the #183 projector is executed as an additional contract
  check and `manifestProjectable=true` is recorded only when it succeeds

VRMine #32 is expected to make the installed runtime module registry authoritative for executable
module/version/capability availability. Until that cross-repository registry exists, the RuleScribe
binding registry remains the explicit transport-side declaration and missing modules remain blocked.

## Rights policy

The default asset policy is `generic-only`.

The audit does **not** claim that publisher artwork, card scans, icons, rulebook pages, or other
source assets are reusable. Rights are never inferred from `source_url`, source trust, publisher
identity, or public availability.

Because there is not yet a canonical explicit reuse-rights contract, every RuleSet record currently
carries `SOURCE_ASSET_REUSE_UNVERIFIED`. A record that would otherwise be `ready` is therefore held at
`review-required` until the rights boundary is resolved. VRMine may still implement generic geometry,
VRMine-owned UI, and verified factual mechanics without copying source assets.

A future explicit rights contract should distinguish at least:

- source asset reuse explicitly permitted;
- source asset reuse not permitted;
- rights unknown but generic substitution possible;
- asset required and therefore blocking.

## Readiness decision

The decision is fail-closed:

1. inactive/superseded RuleSet or explicitly unsupported runtime -> `unsupported`
2. data blocker, runtime blocker, or missing required runtime capability -> `blocked`
3. evidence blocker, rights blocker, or unknown capability requirement -> `review-required`
4. only a record with none of the above -> `ready`

`promotableToCatalog` is mechanically equal to `readinessStatus == ready`.
No other status may be promoted to #184 `playable`.

## Full-catalog artifact

`scripts/audit_vrchat_readiness.py` reads the configured Supabase catalog in pages of 100 and refuses
a local fallback or a zero-game result. It writes:

- JSON: complete typed report
- CSV: one row per game/RuleSet for triage

The GitHub Actions security boundary is deliberate:

- pull requests run compile, lint, and fixture/contract tests only;
- production credentials are not consumed by the PR job;
- the read-only production catalog audit runs only after a trusted `main` push, by
  `workflow_dispatch`, or by the daily schedule;
- trusted runs pull production environment metadata, execute the full-catalog audit, verify that
  every canonical game is accounted for, and upload the JSON/CSV report as an artifact.

The workflow passes when the audit is complete and internally consistent. It does not require every
game to be ready; blockers are the product of the audit, not CI failures.

## Relationship to #184 production deployment

#184's API implementation is merged, while the Issue remains open. Two verification items remain:

1. live production endpoint smoke once the deployment budget permits canonical production rollout;
2. an explicit JSON Schema/validation gate for the catalog/envelope response, not only the nested
   #183 manifest schema.

Those transport blockers do not change #185's canonical audit inputs: #185 uses the merged
manifest/catalog contracts and canonical Supabase data directly. No #185 result is treated as live
VRChat availability until #184's production verification and the corresponding VRMine runtime gates
are also satisfied.
