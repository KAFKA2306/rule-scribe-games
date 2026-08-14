# Curated Game Fast Path

Status: canonical operator workflow for source-grounded game additions.

## Goal

Add one verified game to ボドゲのミカタ with the smallest safe change set and no unrelated repair work.

## One-command path

Prepare one structured file under `data/curated-games/<slug>.json`, then run:

```bash
task game:add \
  SLUG=skull-king \
  SOURCE_URL=https://www.grandpabecksgames.com/pages/skull-king \
  DATA=data/curated-games/skull-king.json
```

`game:add` performs the fixed path in one process:

1. validates the structured input and source/revision contract;
2. checks the primary source URL is reachable;
3. validates focused game assertions;
4. materializes `frontend/src/lib/generatedCuratedRuleGuides.js` from every structured curated input;
5. validates the runtime guide returned by `getCuratedRuleGuide(slug)`;
6. checks production `slug -> work` identity before any write;
7. updates the existing canonical edition idempotently, or creates one canonical work+edition when none exists;
8. verifies the production API provenance and `/games/{slug}` page once;
9. prints the exact PR-ready changed-file set.

A slug collision with a different canonical work fails before mutation. A canonical work that already has the same edition/language under another slug also fails before mutation.

## Structured input contract

`data/curated-games/schema-v1.json` defines the versioned external contract. Each file contains:

- `work`: canonical work title and identity status;
- `source`: explicit HTTPS primary source, rule version, and source revision;
- `game`: the production catalog payload, including `source_url`, `source_revision`, and `generated_from_source_revision`;
- `guide`: the reviewed Quick Rules/scoring/flow object;
- `assertions`: focused facts that must remain true for this game.

The workflow also enforces cross-field invariants that JSON Schema alone cannot express: slug equality, source URL equality, source revision equality, and guide/source rule-version equality.

## Generated guide boundary

`frontend/src/lib/generatedCuratedRuleGuides.js` is generated output. Do not hand-edit it.

Structured curated games are merged into the runtime registry by `frontend/src/lib/curatedRuleGuides.js`. Legacy hand-maintained guides may remain there, but migrated games must exist only in the structured input/generated registry. Skull King is the replay fixture for this contract.

## Fast path

1. **Lock one current primary source.** Record the official URL and the source/revision date. Do not keep searching after the primary source is sufficient unless a contradiction appears.
2. **Check canonical identity once.** The command checks the production catalog for the work/slug before any write. If the same canonical edition already exists, update it instead of creating a duplicate.
3. **Prepare one structured file.** Do not hand-edit a large JS guide block or create a game-specific import script.
4. **Run `task game:add` once.** It handles validation, materialization, the idempotent DB write, production verification, and changed-file reporting.
5. **Open one branch and one PR.** Do not create replacement branches/PRs for the same game unless the canonical branch is unusable.
6. **Use the targeted CI gate first.** `Curated game fast path` runs the workflow unit tests plus offline materialization/runtime checks without installing browsers or running the full UI suite.
7. **Retry a flaky CI job at most once.** Re-run the failed job/run directly. If it fails again, preserve the canonical work line and report the blocker.
8. **Separate unrelated infrastructure failures.** If the curated-game gate passes but generic deployment infrastructure fails, open/link a separate infrastructure Issue. Do not repair deployment internals inside the game-add task.
9. **Merge once and stop after the fixed point.** `task game:verify` is available when a post-merge production re-check is required.

## Commands

Offline validation without writes or source/network checks:

```bash
task game:check DATA=data/curated-games/skull-king.json
```

Post-merge production verification without a database write:

```bash
task game:verify \
  SLUG=skull-king \
  SOURCE_URL=https://www.grandpabecksgames.com/pages/skull-king \
  DATA=data/curated-games/skull-king.json
```

## Minimal completion evidence

A game-add task is complete when all of these are true:

- the production catalog contains exactly one canonical game identity for the intended work/edition;
- the current primary source URL/revision is stored;
- the structured guide has focused regression assertions;
- generated guide output is current and runtime-visible;
- the targeted curated-game CI gate passes;
- the production API returns matching source provenance and the production game page returns the expected title.

A general deployment workflow failure does not invalidate an already-live database-backed game page. It becomes a separate infrastructure blocker unless the requested game content itself is unavailable.

## Scope guard

During a game-add task, do not:

- redesign unrelated schemas or UI;
- repair generic deployment infrastructure;
- perform repeated repository-wide searches after canonical paths are known;
- create multiple speculative PRs;
- rerun full CI suites to diagnose a single targeted failure before reading the failed job;
- continue source research after the official source is locked without contradictory evidence;
- hand-edit `generatedCuratedRuleGuides.js`.

## Success retrospective

After a successful addition, spend one short pass on workflow improvement:

1. identify tool calls, searches, retries, branches, or checks that did not change the outcome;
2. remove them from this fast path;
3. automate only repeated deterministic steps;
4. keep evidence/identity/source gates fail-closed;
5. stop when no reusable improvement remains.

Do not turn the retrospective into a second implementation project. Reusable improvements belong in a separate Issue/PR unless they are a trivial documentation/task wrapper change.
