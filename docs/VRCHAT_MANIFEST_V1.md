# BoardGameModule Manifest v1

Issue: https://github.com/KAFKA2306/rule-scribe-games/issues/183

## Purpose

`BoardGameModule Manifest v1` is a deterministic, read-only projection from the canonical
`Game / RuleSet / RuleGraph / ComponentCatalog` data into the declarative contract consumed
by `KAFKA2306/vrmine`.

It is **not** a second rule source and it never contains executable Udon/UdonSharp code.
The runtime implementation remains a prebuilt, validated VRMine module selected by `moduleId`.

## Source boundary

The projector accepts:

1. canonical `GameDetail`;
2. one explicit canonical `RuleSet`;
3. the `RuleGraphReadResponse` for exactly that RuleSet;
4. an optional `ComponentCatalog` for exactly that RuleSet;
5. an explicit `ModuleBinding` describing runtime support;
6. an explicit timezone-aware `generatedAt`.

The projector reads no wall clock, network, database, LLM, or remote source. With the same
inputs it produces the same `canonical_json()` output.

`ModuleBinding` is deliberately separate from board-game truth. It declares which validated
VRMine module is expected to execute the manifest. Capability values omitted from the binding
are emitted as `unknown`; the projector must not infer support from rule text, mechanics labels,
component names, or game title.

## Identity isolation

Projection fails closed when any of these identities conflict:

- `GameDetail.id` vs `RuleSet.game_id`;
- game slug vs `RuleGraphReadResponse.slug`;
- `RuleSet.ruleset_id` vs `RuleGraphReadResponse.rule_set_id`;
- available language / edition / source revision fields disagree;
- `ComponentCatalog.ruleset_id` differs from the selected RuleSet.

Platform-specific rules therefore remain isolated by RuleSet identity. A BGA/physical/mobile
ruleset must not be silently merged into another ruleset before projection.

## Contract

Machine-readable schema:

`schemas/vrchat/board-game-module-manifest-v1.schema.json`

The JSON representation uses camelCase keys for VRChat transport. Important fields are:

- `schemaVersion`
- `gameId`, `slug`, `rulesetId`
- `moduleId`, `moduleVersionRange`
- `playerCount`
- `supportedPlatforms`, `interactionProfile`
- complete v1 `capabilities` map (`supported | unsupported | unknown`)
- typed RuleGraph ID references under `rules`
- `componentSetRefs`
- source / claim / evidence / verification references under `evidence`
- canonical source schema versions
- `locale`, `revision`, `generatedAt`

`generatedAt` is supplied by the caller and must contain a timezone offset. The projection
layer does not call `now()`, which keeps generation reproducible for a fixed canonical snapshot.

## Rule references

Every current RuleGraph node type has a manifest bucket:

- setup
- phase
- turn
- action
- condition
- effect
- scoring
- round end
- game end
- victory
- exception
- targeting
- conflict resolution
- variant

Only stable `rule_id` references are projected. Full rulebook text, source artwork, arbitrary
HTML, and executable expressions are outside this contract.

## Compatibility

v1 module compatibility is explicit:

- `schemaVersion` is the manifest schema version.
- `moduleId` is a stable runtime identity independent of display title.
- `moduleVersionRange` is an opaque compatibility range interpreted by VRMine.
- `sourceSchemas` records the canonical RuleSet / RuleGraph / ComponentCatalog schema versions
  used to create the manifest.

VRMine must fail closed when it does not understand the manifest schema or cannot resolve a
compatible installed module.

## Verification fixtures

`evaluation/vrchat/manifest-v1-fixtures.json` contains three structurally different fixtures:

- card-centric;
- tile-centric;
- dice/token-centric.

`backend/tests/test_vrchat_manifest.py` verifies deterministic output, identity isolation,
fail-closed behavior, explicit unknown capability states, evidence traceability, schema parity,
and fixture validation.

## Next work

This issue only establishes the projection contract.

- #184 owns publication/catalog transport.
- #185 owns full-catalog VRChat readiness and rights auditing.
- VRMine #32 owns executable module contract/registry behavior.
