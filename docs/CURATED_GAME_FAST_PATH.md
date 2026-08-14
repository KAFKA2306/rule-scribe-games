# Curated Game Fast Path

Status: canonical operator workflow for source-grounded game additions.

## Goal

Add one verified game to ボドゲのミカタ with one canonical source file, fail-closed evidence/identity checks, and no committed generated artifacts.

## Routine path

Create or update exactly one Git-tracked source file:

`data/curated-games/<slug>.json`

Then run:

```bash
task game:add GAME=<slug>
```

`GAME` is the only routine operator input. The command derives the spec path, canonical slug, primary source URL, rule version, source revision, assertions, and production expectations from the structured file. Filename, `GAME`, and `spec.slug` must match exactly.

## Ordered gates

`game:add` executes these gates in this order:

1. load the one canonical structured spec;
2. validate schema/cross-field invariants and focused assertions;
3. verify the primary source HTTP status with a streamed request without consuming the full body;
4. preflight production `slug -> work -> edition/language` identity;
5. only after preflight succeeds, run the single Node artifact generator;
6. verify the Node-generated deployment manifest against the Python revision contract;
7. validate the runtime guide returned by `getCuratedRuleGuide(slug)`;
8. perform one idempotent catalog write using the already-resolved identity plan;
9. verify the catalog fixed point once through the production API and game page.

A slug/work/edition collision therefore fails before generated files or production catalog rows are changed.

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
- Vercel production/preview builds, because Vercel runs the frontend build command;
- `task game:add`, `task game:check`, and focused CI through the same Node generator.

The Python fast path does not implement a second guide generator. It invokes Node and checks that the resulting deployment manifest exactly matches the Python revision-contract calculation.

## Deployment manifest

`curated-guides-manifest.json` contains each curated game's rule/source revision and a deterministic `revision_contract_sha256`. It is a cheap release proof that the deployed frontend corresponds to the intended curated revision contract without browser automation or bundle scraping.

## Two fixed points

Catalog publication and frontend release remain deliberately separate.

### Catalog fixed point

`task game:add GAME=<slug>` completes when the production API and `/games/<slug>` expose the intended canonical game/source provenance. Database-backed content can become live independently of a frontend deployment.

### Frontend release fixed point

After a successful Vercel production deployment, `Curated game release verification` automatically checks the deployed manifest against the commit that was deployed.

Manual fallback:

```bash
task game:verify GAME=<slug>
```

Global deployed-registry check:

```bash
task game:release-check
```

A generic deployment failure is a separate infrastructure blocker; it does not cause the game-add workflow to branch into deployment repair.

## Other commands

Source/runtime validation without a catalog write:

```bash
task game:check GAME=<slug>
```

Full game fixed-point verification after deployment:

```bash
task game:verify GAME=<slug>
```

## CI

`Curated game fast path` is path-scoped and browser-free. From a clean checkout where generated artifacts do not exist, it:

- runs generic workflow tests;
- validates every structured assertion;
- regenerates JS + manifest from source;
- verifies Node/Python revision-contract agreement;
- validates runtime guide integration.

Do not make the full UI suite a prerequisite for routine curated-game changes.

## Minimal completion evidence

A curated game is fully released when:

- production contains exactly one intended canonical work/edition identity;
- the current primary source URL and revision are stored in the structured source;
- structured assertions pass;
- generated artifacts are reproducible from source;
- targeted curated-game CI passes;
- catalog fixed point is verified;
- post-deploy manifest verification confirms the frontend release fixed point.

## Scope guard

During a game-add task, do not:

- repeat source research after the primary source/revision is locked unless contradictory evidence appears;
- repeat repository-wide searches once canonical paths are known;
- provide `SLUG`, `SOURCE_URL`, or `DATA` separately when they are already in the spec;
- mutate generated files before identity preflight succeeds;
- commit or hand-edit generated artifacts;
- create a game-specific regression test when structured assertions can express the contract;
- repair unrelated Vercel/CI infrastructure inside the game-add branch;
- create replacement branches/PRs for the same task;
- retry a failed job more than once without new evidence.

## Success retrospective

After a successful addition, review only the steps that affected the outcome. Remove repeated deterministic work from the next run, but keep source, identity, semantic, and production fixed-point gates fail-closed. Stop once there is no reusable reduction left.
