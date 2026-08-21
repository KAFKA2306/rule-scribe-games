# Adding a Curated Game

This is the supported procedure for adding or updating a source-backed game in ボドゲのミカタ.

## Canonical source

Create or update:

`data/curated-games/<slug>.json`

The filename, `spec.slug`, and routine `GAME` argument must match. The structured file owns repository-specific game identity, source provenance, catalog fields, reviewed guide data, and regression assertions. Do not copy official rulebooks or FAQ text into separate repository documents.

Run:

```bash
task game:add GAME=<slug>
```

This validates the source, checks the official source and live identity read-only, regenerates local generated artifacts, validates the runtime guide, and stops without a production write.

## PR merge conditions

PR merge and product release are separate decisions.

The pull request is evaluated only with checks that can run safely before merge:

- `Frontend PR build` builds the frontend without production secrets;
- `Curated game PR checks` runs when curated-game paths change;
- curated checks validate schema, assertions, source reachability, production identity read-only, generated artifacts, and runtime guide integration;
- no PR job publishes catalog data, writes production data, or deploys production.

A curated source change is merge-ready when its applicable PR checks pass on the exact head and review requirements are satisfied. Production deployment state is not a PR merge condition.

## Product release conditions

Release begins only after the change reaches `main`.

Two release paths may run independently:

1. `Curated game release` revalidates the merged source and publishes only changed curated games to the production catalog.
2. `Vercel Deployment` builds/verifies the production application and ensures production reaches the intended `main` SHA when deployment capacity permits.

`Curated game release verification` runs after successful completion of either release workflow and checks the actual production curated registry/catalog state. For a curated change, an early verification may fail while the other release path is still pending; the later release workflow triggers verification again.

A merged change is **released** only when the production state required by that change is directly verified. If publication, deployment, quota, credentials, or production read-back fails after merge, the code remains merged but the product is **UNRELEASED/UNVERIFIED**. Do not reinterpret that as a failed PR merge check.

## Validation performed before merge

`task game:add GAME=<slug>` and `Curated game PR checks` cover the reusable pre-merge contract:

1. load and validate the structured source;
2. validate cross-field requirements and assertions;
3. verify primary-source reachability;
4. check live `slug -> work -> edition/language` identity without writing;
5. regenerate generated files;
6. validate generated revision consistency;
7. validate `getCuratedRuleGuide(slug)` integration.

Pull-request validation has no production database write step and does not require production deployment credentials.

## Publishing from `main`

The internal publish command is:

`curated_game_fast_path_v2.py publish --game <slug>`

`Curated game release` is the supported caller. It:

- runs only after a push to `main` on relevant paths;
- re-runs focused source/runtime validation on the merged commit;
- identifies added or modified `data/curated-games/<slug>.json` files from the main push;
- rejects source deletion because removal requires an explicit deprecation change;
- skips production environment setup when no game source changed;
- loads trusted production Supabase credentials from the established Vercel production environment;
- publishes only changed games;
- rechecks source reachability and live identity before writing;
- verifies catalog fixed points after publication;
- does not itself request a Vercel deployment.

The production publication job uses `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Browser-safe anonymous/publishable keys are not substitutes.

## Generated artifacts

`frontend/scripts/generate-curated-game-artifacts.mjs` generates:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

Both are gitignored. Do not commit or hand-edit them. The Python workflow calls the Node generator rather than maintaining a second generator.

A normal game addition should therefore contain the canonical source JSON, not game-specific generated JavaScript, deployment manifests, importers, or duplicate test files. Put game-specific regression facts in the structured `assertions` array when the generic schema can express them.

## Production verification

After catalog publication, verify the production API and `/games/<slug>`.

After application deployment, verify the deployed revision and `curated-guides-manifest.json`. Release verification also compares live API-visible curated fields with the canonical specs so a current frontend deployment cannot hide stale production game data.

Manual diagnostics:

```bash
task game:verify GAME=<slug>
task game:release-check
```

A generic deployment failure does not undo a verified catalog publication. Conversely, a successful deployment does not prove catalog publication succeeded. Keep those release facts separate.

## Completion

A curated game change is complete when:

- applicable exact-head PR merge checks passed before merge;
- the canonical source is merged to `main`;
- main-only publication revalidated the live source and identity;
- production contains the intended work and edition;
- production API/page behavior is verified;
- generated artifacts are reproducible from source;
- deployed revision verification passes when deployment is part of the change.

During this workflow, do not write production before merge, commit generated artifacts, create duplicate game-specific authorities, publish unchanged games on every push, silently delete production games, or repair unrelated release infrastructure inside a game-content change.
