# Adding a Curated Game

This document describes the supported procedure for adding a source-backed game to ボドゲのミカタ.

## Source file

Create or update one Git-tracked source file:

`data/curated-games/<slug>.json`

Then run:

```bash
task game:add GAME=<slug>
```

`GAME` is the routine input. `game:add` validates the structured source, checks the official source, performs a read-only production identity check, regenerates local generated files, and validates the runtime guide. It does not write the production catalog.

The filename, `GAME`, and `spec.slug` must match.

## Pull request and publication

1. Create or update `data/curated-games/<slug>.json`.
2. Run `task game:add GAME=<slug>`.
3. Open one pull request containing the source JSON.
4. GitHub Actions validates the pull request without production-write credentials.
5. Merge to `main`.
6. The same validation runs on the `main` push.
7. `publish-catalog` identifies added or modified curated JSON files from the push.
8. When a curated source changed, it obtains the production environment from Vercel and runs the internal publish command for those slugs.
9. The publish command rechecks the primary source and live identity, performs an idempotent catalog write, and verifies the production API and page.
10. After a successful Vercel deployment, release verification checks the deployed revision manifest.

Production catalog data therefore cannot be published through this procedure before its source reaches `main`.

## Validation order

`task game:add GAME=<slug>`:

1. loads the structured source;
2. validates schema, cross-field requirements, and assertions;
3. verifies primary-source reachability;
4. checks production `slug -> work -> edition/language` identity without writing;
5. regenerates generated files;
6. checks the generated deployment manifest against the source revision;
7. validates the runtime guide returned by `getCuratedRuleGuide(slug)`;
8. reports the expected pull-request files and stops without a database write.

## Publishing from `main`

The internal command is:

`curated_game_fast_path_v2.py publish --game <slug>`

The GitHub Actions workflow is the supported caller. It is intentionally not exposed as the normal Taskfile command.

Before writing, it repeats source reachability, production identity, generated-file validation, and runtime validation. If production identity changed between pull-request preparation and merge, publication stops rather than writing to a different work or edition.

`publish-catalog`:

- runs only on pushes to `main`;
- waits for curated-game validation;
- publishes only changed curated source files;
- ignores schema-only changes;
- refuses source deletion because removal requires an explicit deprecation change;
- skips environment setup when no game source changed;
- uses `vercel pull --environment=production` for the established production environment;
- does not request a Vercel deployment.

## Credentials

Pull-request validation has no production database write step.

The main-only publication job uses:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

They are loaded from Vercel's production environment. Browser-safe anonymous or publishable keys are not substitutes for server credentials.

## Pull request contents

A normal game addition changes exactly one source file:

`data/curated-games/<slug>.json`

Do not commit game-specific generated JavaScript, deployment manifests, importer scripts, or separate test files. Put game-specific regression facts in the structured `assertions` array so generic tests can evaluate them.

## Structured input

`data/curated-games/schema-v1.json` defines the file format. Each game source contains:

- `work`: work title and identity status;
- `source`: HTTPS primary source, rule version, and source revision;
- `game`: catalog fields including provenance;
- `guide`: reviewed quick rules, scoring, and flow;
- `assertions`: facts that generic validation must preserve.

Validation also checks slug, source URL, source revision, and guide rule-version consistency.

## Generated files

`frontend/scripts/generate-curated-game-artifacts.mjs` generates:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

Both outputs are gitignored. Do not commit or hand-edit them.

Generation runs through:

- `npm run dev` via `predev`;
- `npm run build` via `prebuild`;
- Vercel production and preview builds;
- curated-game prepare, publish, check, and release verification.

The Python command calls the Node generator rather than maintaining a second generator.

## Production verification

After catalog publication, verify the production API and `/games/<slug>`.

After Vercel deployment, verify `curated-guides-manifest.json` against the deployed commit and expected source revision.

Manual diagnostics:

```bash
task game:verify GAME=<slug>
task game:release-check
```

A generic deployment failure does not undo a verified catalog publication and should not be repaired inside an unrelated game-content pull request.

## CI

The curated-game GitHub Actions workflow is path-scoped and does not require a browser for source-only changes. From a clean checkout it:

- runs generic curated-game tests;
- validates structured assertions;
- regenerates generated files from source;
- checks revision consistency;
- validates runtime guide integration.

On pull requests it stops after validation. On `main`, `publish-catalog` may obtain production credentials and publish changed game sources after validation succeeds.

Do not make the full UI suite or an unrelated deployment request a prerequisite for a source-only catalog publication.

## Completion

A curated game is released when:

- its structured source is merged to `main`;
- focused source, identity, and runtime checks pass;
- publication rechecks the live source and identity;
- production contains the intended work and edition;
- the production API and page are verified;
- generated files are reproducible from source;
- after deployment, the revision manifest matches the expected source revision.

## Scope

During a game-addition task, do not:

- write production data before merge;
- repeat source research after a primary source and revision are established unless contradictory evidence appears;
- repeat repository-wide searches after the relevant paths are known;
- provide `SLUG`, `SOURCE_URL`, or `DATA` separately when they are already in the source file;
- commit or hand-edit generated files;
- create a game-specific regression test when structured assertions can express the requirement;
- publish unchanged games on every `main` push;
- silently delete a production game because its source JSON disappeared;
- repair unrelated Vercel or CI infrastructure in the game-content branch;
- create replacement branches or pull requests for the same task;
- retry a failed job more than once without new evidence.

After completion, remove repeatable deterministic work when doing so does not weaken source, identity, semantic, CI, merge, production, or cleanup checks.
