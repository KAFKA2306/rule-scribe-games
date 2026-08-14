# Curated Game Fast Path

Status: canonical operator workflow for source-grounded game additions.

## Goal

Add one verified game to ボドゲのミカタ with one canonical source file, fail-closed evidence/identity checks, and production writes only after reviewed source reaches `main`.

## Routine operator path

Create or update exactly one Git-tracked source file:

`data/curated-games/<slug>.json`

Then run:

```bash
task game:add GAME=<slug>
```

`GAME` is the only routine operator input. `game:add` is prepare-only: it validates the source contract, reaches the official source, performs a read-only live identity preflight, regenerates local runtime artifacts, and validates the runtime guide. It never writes the production catalog.

Filename, `GAME`, and `spec.slug` must match exactly.

## Final lifecycle

1. create/update `data/curated-games/<slug>.json`;
2. run `task game:add GAME=<slug>`;
3. open one JSON-only PR;
4. `Curated game fast path` validates the PR without production-write credentials;
5. merge to `main`;
6. the same focused workflow completes its validation on the `main` push;
7. `publish-catalog` derives only added/modified curated JSON files from the push event;
8. only when such files exist, it pulls the production environment from Vercel, exports the trusted Supabase server variables, and invokes the internal `publish` mode for those slugs;
9. `publish` rechecks the primary source and live identity, performs one idempotent catalog write, then verifies the production API/page fixed point once;
10. Vercel deployment remains independent; after a successful production deploy, `Curated game release verification` checks the deployed revision manifest.

Production therefore cannot get ahead of canonical Git source through the normal game-add path.

## Prepare gate order

`task game:add GAME=<slug>` executes:

1. load the one canonical structured spec;
2. validate schema/cross-field invariants and focused assertions;
3. verify the primary source HTTP status with a streamed request without consuming the full body;
4. preflight production `slug -> work -> edition/language` identity read-only;
5. only after preflight succeeds, run the single Node artifact generator;
6. verify the Node-generated deployment manifest against the Python revision contract;
7. validate the runtime guide returned by `getCuratedRuleGuide(slug)`;
8. report the one-file routine PR set and stop without a DB write.

## Main-only publish gate

The internal CLI mode is:

`curated_game_fast_path_v2.py publish --game <slug>`

It is not exposed as the routine Taskfile command. The main workflow is its canonical caller.

Before every write it repeats source reachability, live identity preflight, artifact/runtime validation, then uses the resolved identity plan for the idempotent catalog write. A changed production identity between PR preparation and merge therefore fails closed instead of writing to another work/edition.

The publish job:

- runs only for a `push` to `refs/heads/main`;
- requires the focused validation job to succeed first;
- derives changed curated games from the GitHub push event rather than rewriting every curated game;
- ignores schema-only changes;
- refuses curated-game source deletion; deletion requires an explicit deprecation workflow;
- skips uv/Vercel/environment setup entirely when no game spec changed;
- uses `vercel pull --environment=production` only as the established credential retrieval route;
- never invokes a Vercel deploy request.

## Credential boundary

Pull-request validation has no production DB write step. Trusted server credentials are consumed only by the main-only `publish-catalog` job after focused validation.

The required server variables are:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

They are loaded from Vercel's production environment and are never replaced by browser-safe anon/publishable keys.

## Routine PR shape

A normal game addition changes exactly one source file:

`data/curated-games/<slug>.json`

Do not commit game-specific generated JavaScript, deployment manifests, importer scripts, or test files. Game-specific regression facts belong in the structured `assertions` array; generic CI evaluates those assertions for every curated game.

## Structured input contract

`data/curated-games/schema-v1.json` defines the external contract. Each file contains:

- `work`: canonical work title and identity status;
- `source`: explicit HTTPS primary source, rule version, and source revision;
- `game`: production catalog payload including source provenance;
- `guide`: reviewed Quick Rules/scoring/flow object;
- `assertions`: game-specific facts that must remain true.

The workflow additionally enforces cross-field invariants such as slug equality, source URL equality, source revision equality, and guide/source rule-version equality.

## Single generated-artifact boundary

`frontend/scripts/generate-curated-game-artifacts.mjs` is the only artifact generator. It derives both runtime artifacts from structured source:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

Both outputs are gitignored and must never be committed or hand-edited.

Generation happens automatically through:

- `npm run dev` via `predev`;
- `npm run build` via `prebuild`;
- Vercel production/preview builds;
- prepare/publish/check/release verification through the same Node generator.

The Python fast path does not implement a second guide generator. It invokes Node and checks that the resulting deployment manifest exactly matches the Python revision-contract calculation.

## Two production fixed points

### Catalog fixed point

The main-only publish job verifies the production API and `/games/<slug>` immediately after the idempotent DB write. Database-backed content can become live independently of a frontend deployment.

### Frontend release fixed point

After a successful Vercel production deployment, `Curated game release verification` checks the deployed `curated-guides-manifest.json` against the deployed commit.

Manual diagnostics remain available:

```bash
task game:verify GAME=<slug>
task game:release-check
```

A generic deployment failure is a separate infrastructure blocker; it does not roll back an already-verified catalog publication or trigger deployment repair inside the game-add branch.

## CI

`Curated game fast path` is path-scoped and browser-free. From a clean checkout it:

- runs generic workflow tests;
- validates every structured assertion;
- regenerates JS + manifest from source;
- verifies Node/Python revision-contract agreement;
- validates runtime guide integration.

On pull requests it stops there. On `main`, and only after that validation succeeds, the separate `publish-catalog` job may obtain production credentials and publish changed game specs.

Do not make the full UI suite or generic Vercel deploy request a prerequisite for catalog publication.

## Minimal completion evidence

A curated game is fully released when:

- exactly one canonical JSON source is merged to `main`;
- source/identity/runtime focused CI passes;
- main-only publish rechecks live source and identity;
- production contains exactly one intended canonical work/edition identity;
- catalog API/page fixed point is verified;
- generated artifacts are reproducible from source;
- post-deploy manifest verification confirms the frontend release fixed point.

## Scope guard

During a game-add task, do not:

- write the production DB before merge;
- repeat source research after the primary source/revision is locked unless contradictory evidence appears;
- repeat repository-wide searches once canonical paths are known;
- provide `SLUG`, `SOURCE_URL`, or `DATA` separately when they are already in the spec;
- commit or hand-edit generated artifacts;
- create a game-specific regression test when structured assertions can express the contract;
- publish unchanged games on every main push;
- silently delete a production game because its source JSON disappeared;
- repair unrelated Vercel/CI infrastructure inside the game-add branch;
- create replacement branches/PRs for the same task;
- retry a failed job more than once without new evidence.

## Success retrospective

After a successful addition, review only the steps that affected the outcome. Remove repeated deterministic work from the next run, but keep source, identity, semantic, merge, catalog, and release fixed-point gates fail-closed. Stop once there is no reusable reduction left.
