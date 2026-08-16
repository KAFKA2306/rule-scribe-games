# AGENTS.md

This is the operating contract for coding and repository agents working in `KAFKA2306/rule-scribe-games`.

Keep this file short, stable, and operational. Do not duplicate mutable architecture, schemas, model versions, or vendor details here. Use the referenced project documentation and code for those details.

## 1. Mission

Improve **ボドゲのミカタ** through small, evidence-backed, production-safe changes.

Priorities:

1. correctness and provenance;
2. one existing issue, pull request, or branch per task;
3. the smallest safe change;
4. focused verification before broad verification;
5. completion through merge and production verification when applicable;
6. cleanup of stale branches, pull requests, temporary files, and superseded work.

## 2. Sources of truth

When implementation details conflict, use this order:

1. current repository code and tests;
2. `Taskfile.yml` for established commands;
3. `docs/CURATED_GAME_FAST_PATH.md` for curated-game additions;
4. `docs/PROJECT_MASTER_GUIDE.md` for product, schema, API, and UX architecture;
5. other current documentation next to the subsystem being changed.

## 3. Start from current state

Before creating work:

- fetch current `main`;
- read this file;
- inspect open pull requests, relevant issues, branches, CI, data, and production state;
- continue an existing pull request or branch when it already represents the task;
- do not create a replacement branch or pull request just because existing work is imperfect;
- keep one task to one issue or one clearly bounded outcome.

If `main` moves, reconcile with the latest `main` before opening or merging a pull request.

## 4. Commands

Use `Taskfile.yml` when it already provides the operation.

Common commands:

```bash
task setup
task dev
task build
task lint
task test
task game:add GAME=<slug>
task game:check GAME=<slug>
task game:verify GAME=<slug>
task game:release-check
```

Direct `uv`, `npm`, `node`, `python`, or shell commands are appropriate for focused diagnostics or when no Taskfile command exists. If a direct command becomes repeated deterministic work, add it to the existing command interface instead of maintaining a second procedure.

## 5. Evidence and provenance

For rules, editions, product facts, and other externally verifiable game data:

- prefer current first-party publisher or designer documentation;
- record source URL and revision or version evidence in the structured source;
- inspect relevant PDF pages rather than relying on snippets or metadata;
- do not substitute community summaries when a suitable primary source exists;
- do not infer missing facts;
- stop a write when game identity, edition, source, or revision is ambiguous.

Keep official facts distinct from generated summaries, translations, interpretations, and recommendations.

## 6. Adding a curated game

For a normal curated-game addition, the only game-specific Git source should be:

`data/curated-games/<slug>.json`

Use:

```bash
task game:add GAME=<slug>
```

`game:add` prepares and validates the source. It must not write production data.

The expected sequence is:

`official source -> structured JSON -> validation -> pull request -> merge -> catalog publication -> production verification`

The source filename, `GAME`, and canonical slug must match.

Game-specific regression facts belong in the structured `assertions` data. Do not create game-specific importer scripts or test files when the generic schema and tests can express the requirement.

Generated files must not be hand-edited or committed:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

Production catalog writes occur only after the reviewed source reaches `main`. Pull requests must not contain production database write steps.

## 7. Change discipline

Prefer the minimum change that satisfies the completion conditions.

Do not:

- redesign unrelated schemas or UI;
- repair unrelated deployment infrastructure;
- broaden a content change into a platform refactor;
- create duplicate helpers, importers, workflows, or abstractions;
- commit generated output when reproducible source exists;
- silently delete or deprecate production data because a source file is absent.

Record unrelated problems separately and keep the current change focused.

## 8. Tests and CI

Run the narrowest meaningful verification first:

1. subsystem or unit tests;
2. focused integration or path-scoped workflow;
3. build, lint, or type checks relevant to changed code;
4. broader regression suites when the change can affect them or repository CI requires them.

For curated-game source changes, use the existing path-scoped validation rather than making the full browser suite a prerequisite unless frontend behavior changed.

A flaky failed CI job may be rerun once after inspecting the failure. If it fails again without new evidence, stop retrying and record the blocker.

For a GitHub write or host-side safety rejection:

1. refetch the current state;
2. retry the same action once;
3. if it is rejected again, do not create alternate branches or repeat the write.

## 9. Merge and production verification

Do not treat code written or a green local test as completion.

Complete as far as safely possible through:

`implementation -> focused tests -> pull request -> CI -> merge -> issue close -> cleanup -> production verification`

For curated games, verify both:

- the intended catalog record and source provenance are live;
- after deployment, the generated revision manifest matches the deployed source revision.

A deployment failure is an infrastructure problem unless the requested catalog content itself is unavailable.

## 10. Cleanup

After merge:

- close the issue when appropriate;
- remove merged task branches;
- close superseded or duplicate pull requests created by the task;
- remove temporary files or artifacts introduced by the task;
- verify the cleanup rather than assuming it occurred.

## 11. Communication

Report concrete state:

- issue or pull request URL;
- what changed;
- tests and CI;
- merge commit when merged;
- production verification when applicable;
- files, lines, dependencies, or configuration changed when material;
- only real remaining blockers or risks.

Do not claim a deployment, production write, branch deletion, CI success, or other external state unless it was directly verified.
