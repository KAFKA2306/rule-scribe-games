# Curated Game Fast Path

Status: canonical operator workflow for source-grounded game additions.

## Goal

Add one verified game to ボドゲのミカタ with the smallest safe change set and no unrelated repair work.

## Fast path

1. **Lock one current primary source.** Record the official URL and the source/revision date. Do not keep searching after the primary source is sufficient unless a contradiction appears.
2. **Check canonical identity once.** Search the production catalog for the work/slug before any write. If the game already exists, update that record instead of creating a duplicate.
3. **Prepare only two content changes.** Add/update the curated guide entry and one focused regression assertion for the game-specific facts that are easiest to regress.
4. **Run targeted validation first.** Build/lint only what the changed paths require and run the focused rule-guide/source-quality gate. Do not run repository-wide diagnostics before a targeted gate fails.
5. **Perform the idempotent data upsert once.** Use the existing canonical import path. Re-read the resulting record once; do not repeatedly poll it.
6. **Use one branch and one PR.** Do not create replacement branches/PRs for the same game unless the canonical branch is unusable.
7. **Retry a flaky CI job at most once.** Re-run the failed job/run directly. If it fails again, preserve the canonical work line and report the blocker.
8. **Separate unrelated infrastructure failures.** If game-specific build/rule/source gates pass but deployment infrastructure fails, open/link a separate infrastructure Issue. Do not repair deployment internals inside the game-add task.
9. **Verify production once.** Check `/games/{slug}` for HTTP success and the expected title/source-bound content. Stop after the fixed point is established.

## Minimal completion evidence

A game-add task is complete when all of these are true:

- the production catalog contains exactly one canonical game identity for the intended work/edition;
- the current primary source URL/revision is stored;
- the curated guide has focused regression coverage;
- the game-specific CI gates pass;
- the production game URL returns the expected game content.

A general deployment workflow failure does not invalidate an already-live database-backed game page. It becomes a separate infrastructure blocker unless the requested game content itself is unavailable.

## Scope guard

During a game-add task, do not:

- redesign unrelated schemas or UI;
- repair generic deployment infrastructure;
- perform repeated repository-wide searches after canonical paths are known;
- create multiple speculative PRs;
- rerun full CI suites to diagnose a single targeted failure before reading the failed job;
- continue source research after the official source is locked without contradictory evidence.

## Success retrospective

After a successful addition, spend one short pass on workflow improvement:

1. identify tool calls, searches, retries, branches, or checks that did not change the outcome;
2. remove them from this fast path;
3. automate only repeated deterministic steps;
4. keep evidence/identity/source gates fail-closed;
5. stop when no reusable improvement remains.

Do not turn the retrospective into a second implementation project. Reusable improvements belong in a separate Issue/PR unless they are a trivial documentation/task wrapper change.

## Current automation target

Issue #163 tracks the next step: structured per-game input plus a one-command evidence-gated materialization/validation workflow.
