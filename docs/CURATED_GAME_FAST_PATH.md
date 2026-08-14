# Curated Game Fast Path

Status: canonical operator workflow for source-grounded game additions.

## Goal

Add one verified game to ボドゲのミカタ with the smallest safe routine change set and no unrelated repair work.

## Routine path

Prepare exactly one structured source file:

`data/curated-games/<slug>.json`

Then run only:

```bash
task game:add GAME=<slug>
```

`GAME` is the only routine operator input. The command derives the spec path, canonical slug, primary source URL, rule version, source revision, assertions, and production expectations from the structured file. Filename, `GAME`, and `spec.slug` must match exactly.

## Ordered gates

`game:add` executes these gates in this order:

1. load the one canonical structured spec;
2. validate schema/cross-field invariants and focused assertions;
3. verify the primary source HTTP status with a streamed request, without consuming the full response body;
4. preflight production `slug -> work -> edition/language` identity;
5. only after preflight succeeds, materialize generated frontend artifacts;
6. validate the runtime guide returned by `getCuratedRuleGuide(slug)`;
7. perform one idempotent catalog write using the already-resolved identity plan;
8. verify the catalog fixed point once through the production API and game page;
9. print the deterministic three-file routine PR set.

A slug/work/edition collision therefore fails before generated files or production catalog rows are changed.

## Routine PR shape

For a normal new curated game, the routine change set is fixed to:

1. `data/curated-games/<slug>.json`
2. `frontend/src/lib/generatedCuratedRuleGuides.js`
3. `frontend/public/curated-guides-manifest.json`

Do not add a game-specific Python importer or game-specific test file. Assertions belong inside the structured spec and the generic focused CI evaluates them for every curated game.

## Structured input contract

`data/curated-games/schema-v1.json` defines the external contract. Each file contains:

- `work`: canonical work title and identity status;
- `source`: explicit HTTPS primary source, rule version, and source revision;
- `game`: production catalog payload including source provenance;
- `guide`: reviewed Quick Rules/scoring/flow object;
- `assertions`: game-specific facts that must remain true.

The workflow additionally enforces cross-field invariants such as slug equality, source URL equality, source revision equality, and guide/source rule-version equality.

## Generated artifact boundary

Never hand-edit either generated artifact:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

The deployment manifest contains a deterministic digest of the curated revision contract plus each game's rule/source revision. It provides a cheap production proof that the deployed frontend corresponds to the expected curated registry revision without Playwright or bundle scraping.

## Two fixed points

Catalog publication and frontend release are deliberately separate.

### Catalog fixed point

`task game:add GAME=<slug>` completes when the production API and `/games/<slug>` expose the intended canonical game/source provenance. This can become live immediately for database-backed content.

### Frontend release fixed point

After a successful Vercel production deployment, `Curated game release verification` automatically checks the deployed `curated-guides-manifest.json` against the commit that was deployed.

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

Offline structured/generated-artifact validation:

```bash
task game:check GAME=<slug>
```

Full game fixed-point verification after deployment:

```bash
task game:verify GAME=<slug>
```

## CI

`Curated game fast path` is path-scoped and browser-free. It runs:

- generic v1/v2 workflow tests;
- all structured assertions;
- generated-guide freshness;
- deployment-manifest freshness;
- runtime guide integration.

Do not make the full UI suite a prerequisite for routine curated-game changes.

## Minimal completion evidence

A curated game is fully released when:

- production contains exactly one intended canonical work/edition identity;
- the current primary source URL and revision are stored;
- structured assertions pass;
- generated artifacts are current;
- targeted curated-game CI passes;
- catalog fixed point is verified;
- the post-deploy manifest verification confirms the frontend release fixed point.

## Scope guard

During a game-add task, do not:

- repeat source research after the primary source/revision is locked unless contradictory evidence appears;
- repeat repository-wide searches once canonical paths are known;
- provide `SLUG`, `SOURCE_URL`, or `DATA` separately when they are already in the spec;
- mutate generated files before identity preflight succeeds;
- hand-edit generated artifacts;
- create a game-specific regression test when the structured assertions can express the contract;
- repair unrelated Vercel/CI infrastructure inside the game-add branch;
- create replacement branches/PRs for the same task;
- retry a failed job more than once without new evidence.

## Success retrospective

After a successful addition, review only the steps that affected the outcome. Remove repeated deterministic work from the next run, but keep source, identity, semantic, and production fixed-point gates fail-closed. Stop once there is no reusable reduction left.
