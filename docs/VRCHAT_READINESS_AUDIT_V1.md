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

## Rule coverage

Each RuleSet is independently checked for six runtime-critical dimensions:

1. setup
2. loop (`phase` and/or `turn`)
3. action
4. resolution (`effect` and/or `conflict_resolution`)
5. game end
6. win / victory

Missing dimensions are data blockers. Existing nodes only count as evidence-backed when their
verification state is `source_bound` or `verified` and the node carries a claim, evidence, or source
reference. Missing provenance is an evidence blocker rather than being silently treated as verified.

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

A capability becomes `required` only from structured evidence:

- a canonical `turn` node -> `turn-based`
- canonical scoring/victory nodes -> `score`
- `card` components -> `deck`
- `die` components -> `dice`
- token/marker/figure components -> `tokens`
- board/tile components -> `board`
- a source-bound/verified RuleNode may explicitly declare `metadata.vrchat_capabilities`

An explicit metadata declaration can be `required` or `not-required`. Conflicting declarations are
not resolved by precedence; they become a review blocker. Anything not established by structured
verified evidence remains `unknown`.

This is deliberate for hidden information, simultaneous play, realtime play, timers, and dexterity:
the audit does not guess those properties from game descriptions.

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

That means the audit does **not** claim that publisher artwork, card scans, icons, rulebook pages, or
other source assets are reusable. A game can be modeled with VRMine-owned generic geometry/UI and
verified factual data without importing source artwork. Rights to source assets are therefore never
inferred from `source_url`, `source_trust`, publisher identity, or the fact that content is public.

If a future module requires source-owned assets, an explicit reuse-rights contract must be added and
this audit must emit a rights blocker until that contract is verified.

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

`.github/workflows/test-vrchat-readiness.yml` runs contract tests first, then pulls the Vercel
production environment metadata read-only, executes the full-catalog audit, verifies that every
canonical game is accounted for, and uploads the JSON/CSV report as a GitHub Actions artifact.

The workflow passes when the audit is complete and internally consistent. It does not require every
game to be ready; blockers are the product of the audit, not CI failures.

## Relationship to #184 production deployment

#184's API implementation is merged, while its live production smoke remains open because the
observed Vercel deployment budget was saturated. That external deployment blocker does not change
the readiness audit inputs: #185 uses the merged manifest/catalog contracts and the canonical
Supabase data directly. No #185 result is treated as live VRChat availability until #184's production
smoke and the corresponding VRMine runtime gates are also satisfied.
