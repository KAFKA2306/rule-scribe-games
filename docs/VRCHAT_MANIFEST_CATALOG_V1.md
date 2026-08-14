# VRChat Manifest Catalog v1

Issue: https://github.com/KAFKA2306/rule-scribe-games/issues/184

## Public read contract

RuleScribe exposes two read-only endpoints:

- `GET /api/vrchat/v1/catalog`
- `GET /api/vrchat/v1/manifests/{slug}/{ruleset_id}`

Both responses are JSON, include `ETag`, and advertise:

`Cache-Control: public, max-age=300, stale-while-revalidate=3600`

Clients should cache the catalog and selected manifest instead of fetching on every interaction.
If the client sends the current `If-None-Match`, the API returns `304 Not Modified` with no body.

## Versioned external schemas

The transport boundary is published as checked-in JSON Schema Draft 2020-12 documents:

- `schemas/vrchat/manifest-catalog-v1.schema.json`
- `schemas/vrchat/manifest-read-response-v1.schema.json`
- nested manifest: `schemas/vrchat/board-game-module-manifest-v1.schema.json`

The read-response schema references the #183 BoardGameModule schema rather than copying its fields.
This keeps the API envelope and the game manifest as separate versioned contracts.

The schema gate validates both positive and fail-closed cases. It rejects, among other things:

- malformed catalog SHA-256 revisions;
- a non-playable catalog entry without `reasonCode`;
- an `available` read response without a manifest;
- a non-available read response that leaks a manifest payload.

`scripts/validate_vrchat_catalog_schemas.py` validates the checked-in schemas themselves and exercises
those cases using the existing #183 card-centric manifest fixture. CI installs `jsonschema` only for
this contract step, so the application dependency/lockfile surface is unchanged.

## Publication registry

`data/vrchat/module-bindings-v1.json` is the only production publication registry.
It is deployment metadata, not a second source of board-game rules.

Each entry binds one canonical `(slug, rulesetId)` to the explicit `ModuleBinding` introduced by
BoardGameModule Manifest v1 and declares one publication state:

- `playable`
- `unavailable`
- `unsupported`
- `retired`

Non-playable records require a machine-readable `reasonCode`.

The initial production registry is intentionally empty. Issue #185 owns full-catalog readiness,
rights, and blocker auditing and may only promote audited games into this registry. VRMine #32 owns
runtime module compatibility.

## Fail-closed behavior

A registry entry marked `playable` is still not trusted blindly. Before it is returned as playable,
the service reloads and validates:

1. canonical `GameDetail`;
2. the exact canonical `RuleSet`;
3. the exact Rule Graph for that RuleSet;
4. the available Component Set/Property Definition catalog;
5. the deterministic #183 manifest projection.

If any required identity or Rule Graph is missing, mismatched, or invalid, the manifest response is
`invalid` and the catalog entry is downgraded to `invalid`. The API never substitutes another
edition, language, platform, or RuleSet.

Known `unavailable`, `unsupported`, and `retired` entries are returned as such without reading the
canonical services. An unknown `(slug, rulesetId)` returns `not_registered`.

## Manifest response states

`GET /api/vrchat/v1/manifests/{slug}/{ruleset_id}` returns one envelope with:

- `available` — `manifest` contains one BoardGameModule Manifest v1;
- `not_registered` — no publication binding exists;
- `unavailable` — binding exists but is not publishable yet;
- `unsupported` — current runtime contract cannot support the game;
- `retired` — binding was intentionally retired;
- `invalid` — a binding claimed playable but canonical projection validation failed.

Only `available` contains a manifest payload. The external read-response JSON Schema enforces this
rather than relying on client convention.

## Revisions and compatibility

The catalog contains:

- `schemaVersion` — catalog transport schema version;
- `manifestSchemaVersion` — expected BoardGameModule Manifest version;
- `catalogRevision` — SHA-256 of the validated public catalog entries;
- per-entry `moduleId`, `moduleVersionRange`, status, reason, and manifest path.

The manifest itself carries its canonical RuleSet revision and explicit `generatedAt` snapshot.
A changed catalog or manifest payload produces a different HTTP ETag.

## Security boundary

This API has no POST/PATCH/PUT/DELETE route, accepts no credentials or service-role secret, and
cannot mutate canonical game data. Runtime module binding is server-side versioned metadata; a
client cannot supply an arbitrary `moduleId` or capability declaration to make a game playable.

## Verification

`backend/tests/test_vrchat_catalog.py` verifies:

- production registry schema and empty fail-closed baseline;
- one-fetch selected manifest projection;
- `not_registered` and `unsupported` states;
- downgrade from claimed `playable` to `invalid` when canonical Rule Graph is unavailable;
- GET-only route surface;
- catalog revision, cache headers, ETag, and conditional `304`;
- manifest schema version and component-set references.

The dedicated CI gate also:

- runs the #183 manifest contract tests so transport changes cannot drift from the versioned
  BoardGameModule Manifest JSON Schema;
- validates the catalog/read-response Draft 2020-12 schemas as actual external-consumer contracts;
- exercises positive and negative envelope fixtures without network access.

## Production verification state

The merge commit for PR #195 (`3458ccfe8e2c64aee67b3c3965a9b61781237de4`) passed the production
Vercel build and environment checks on 2026-08-14. The repository's deployment-budget gate reported
`quota_saturated`, so the canonical Vercel Git production deployment verification was deliberately
skipped and no deployment was created by GitHub Actions.

Issue #184 therefore remains open until a canonical production deployment is available and both live
endpoints pass a schema/cache smoke check. The checked-in catalog/read-response JSON Schema CI gate
is independent of that deployment quota and is required before the transport contract is considered
complete in source control.
