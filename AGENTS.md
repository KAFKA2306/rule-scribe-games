# AGENTS.md

This is the canonical operating contract for any coding or repository agent working in `KAFKA2306/rule-scribe-games`.

Keep this file short, stable, and operational. Do not duplicate mutable architecture, model versions, schemas, or vendor details here. Use the referenced project docs and the code as the source of truth for those details.

## 1. Mission

Improve **ボドゲのミカタ** through small, evidence-backed, production-safe changes.

Optimize for:

1. correctness and provenance;
2. one canonical work line;
3. the smallest safe change set;
4. targeted verification before broad verification;
5. merge-to-fixed-point completion;
6. no stale branches, PRs, temporary files, or superseded work;
7. a short post-success retrospective that removes repeatable waste without removing safety gates.

## 2. Source-of-truth order

When instructions or implementation details conflict, use this order:

1. current repository code and tests;
2. `Taskfile.yml` for established operator commands;
3. `docs/CURATED_GAME_FAST_PATH.md` for curated-game additions;
4. `docs/PROJECT_MASTER_GUIDE.md` for product, schema, API, and UX architecture;
5. other current docs adjacent to the subsystem being changed.

Do not copy mutable facts from those documents into this file unless they are stable operating rules.

## 3. Start every task from current state

Before creating work:

- fetch current `main`;
- inspect open PRs and relevant branches/issues;
- continue the existing canonical PR/branch if one already represents the task;
- do not create a replacement branch or PR merely because the existing work is imperfect;
- keep the task to one issue or one clearly bounded outcome at a time.

If `main` moves during the task, reconcile with the latest `main` before opening or merging the PR. Prefer a clean canonical history over speculative parallel branches.

## 4. Command policy

Use `Taskfile.yml` for established workflows.

Common entry points include:

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

Do not invent a second script or manual sequence when a Taskfile path already owns that operation.

Direct `uv`, `npm`, `node`, `python`, or shell commands are acceptable only for narrowly scoped diagnostics or when no canonical task exists. If a direct command becomes repeated deterministic work, promote it into the Taskfile or the owning workflow instead of repeating it manually.

## 5. Evidence and provenance

For rules, editions, product facts, and other externally verifiable game data:

- prefer current first-party publisher/designer documentation;
- record source URL and revision/version evidence in the canonical structured source;
- stop searching once a sufficient primary source is locked unless contradictory evidence appears;
- do not substitute community summaries for available primary sources;
- fail closed when canonical identity or source provenance is ambiguous.

For PDFs, inspect the actual relevant pages; do not rely only on search snippets or metadata.

## 6. Curated-game fast path

For a normal curated game addition, the only Git-tracked game-specific source should be:

`data/curated-games/<slug>.json`

Routine operator command:

```bash
task game:add GAME=<slug>
```

`game:add` is **prepare-only**. It must not write production. Its job is to validate the structured source, source reachability, canonical identity, generated runtime artifacts, and assertions so the JSON is PR-ready.

The normal lifecycle is:

`official source -> one structured JSON -> prepare-only check -> one PR -> focused CI -> merge to main -> main-only catalog publish -> catalog fixed point -> independent frontend deploy -> release-manifest fixed point`

### Curated source contract

- filename, `GAME`, and canonical slug must match;
- game-specific regression facts belong in the structured `assertions` data;
- do not create game-specific importer scripts or test files when the generic contract can express the requirement;
- generated curated artifacts are build outputs, not source files.

Never hand-edit or commit:

- `frontend/src/lib/generatedCuratedRuleGuides.js`
- `frontend/public/curated-guides-manifest.json`

They are regenerated from structured source by the canonical generator.

### Production write boundary

Pull requests must not write the production catalog.

Production publication belongs to the main-only curated workflow after focused validation. The internal publish path rechecks live source and canonical identity immediately before the idempotent write and verifies the catalog fixed point afterward.

Do not bypass this boundary for convenience.

## 7. Change-set discipline

Prefer the minimum change that satisfies the acceptance criteria.

During a focused task, do not:

- redesign unrelated schemas or UI;
- repair unrelated deployment infrastructure;
- broaden a content addition into a platform refactor;
- repeatedly search repository-wide after canonical paths are known;
- create duplicate helpers, importers, workflows, or abstractions;
- commit generated output when reproducible source exists;
- silently delete or deprecate production data through absence of a source file.

If an unrelated blocker is discovered, create or link a separate issue and keep the current work line intact.

## 8. Test and CI policy

Run the narrowest meaningful verification first.

Order of preference:

1. subsystem/unit contract tests;
2. path-scoped workflow or focused integration test;
3. build/lint relevant to changed code;
4. broader regression suites only when the change can affect them or repository gates require them.

For curated-game changes, the `Curated game fast path` workflow is the primary gate. Do not make the full browser/UI suite a prerequisite for a source-only curated-game change unless frontend behavior itself changed.

A flaky failed CI job may be rerun once after checking the failure. If it fails again without new evidence, stop retrying and preserve the canonical branch/PR with the blocker recorded.

For host-side GitHub write/safety rejection:

1. refetch the current canonical state;
2. retry the same canonical action once;
3. if it is rejected again, do not create duplicate branches/PRs or loop retries; record the blocker and stop that write path.

## 9. Merge and completion fixed point

Do not equate "code written" with completion.

For a normal issue, complete as far as safely possible through:

`implementation -> targeted tests -> PR -> CI -> merge -> issue close -> cleanup -> production verification when applicable`

For curated games, distinguish two production fixed points:

- **catalog fixed point**: canonical production record/source provenance is live and verified;
- **frontend release fixed point**: the deployed curated revision manifest matches the expected source revision contract.

A Vercel deployment failure is a separate infrastructure blocker unless the requested catalog content itself is unavailable.

## 10. Cleanup is part of done

After merge:

- confirm the issue is closed when appropriate;
- remove the merged work branch;
- close superseded or duplicate PRs created by the task;
- remove temporary files/artifacts introduced by the task;
- verify no task-specific stale branch or PR remains;
- do not claim cleanup occurred unless it was checked.

## 11. Success retrospective

After a successful task, perform one short efficiency review.

Identify searches, tool calls, retries, branches, checks, or manual edits that did not affect the outcome. Remove repeatable deterministic waste from the next run by improving the canonical workflow.

Do **not** remove source, identity, semantic, CI, merge, production, or cleanup gates merely to make the path shorter.

If the improvement is reusable but not trivial, make it a separate issue/PR rather than expanding the completed task indefinitely.

Stop when there is no further reusable reduction.

## 12. Communication

Report concrete state, not activity theater.

A completion report should state, as applicable:

- issue/PR URL;
- what changed;
- tests and CI result;
- merge commit;
- production fixed-point result;
- cleanup result;
- blocker only if something remains incomplete.

Do not claim a deployment, production write, branch deletion, CI success, or other fixed point unless it was actually verified.
