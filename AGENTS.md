# AGENTS.md

Improve **ボドゲのミカタ** with small, evidence-backed changes that preserve production behavior unless the task requires a product change.

Before changing anything:

- fetch the current `main` branch;
- read open Issues and pull requests related to the task;
- inspect relevant CI, data, and production state;
- continue existing work when it already covers the same task.

Use existing repository commands and structures before adding code, configuration, dependencies, or documentation. `Taskfile.yml` is the preferred command interface when it already provides the required operation.

For externally verifiable game facts:

- prefer current publisher or designer sources;
- record the source URL and revision or version evidence in structured data;
- inspect relevant PDF pages when the source is a PDF;
- do not infer missing facts or substitute community summaries when suitable primary sources exist;
- keep generated summaries, translations, interpretations, and recommendations distinct from verified facts.

For curated game data:

- store game-specific source data in `data/curated-games/<slug>.json` when the existing schema supports it;
- use `task game:add GAME=<slug>` and the existing validation commands;
- keep the filename, `GAME`, and canonical slug consistent;
- put game-specific regression facts in the structured `assertions` data instead of adding a game-specific importer or test when the generic schema can express them;
- do not hand-edit or commit generated curated-game output;
- do not write production data from a pull request.

Prefer the smallest coherent change. Do not redesign unrelated schemas or UI, create duplicate helpers or workflows, commit reproducible generated output, or silently delete production data because a source file is absent.

Run the narrowest meaningful tests first, then the broader checks required by the affected code or repository CI. Do not weaken or skip checks to make a change pass.

Treat **PR merge** and **product release** as separate decisions. Merge checks run on the pull request and must not require production credentials, production writes, or production deployment. Release checks run only after the change reaches `main` and cover production publication, deployment, exact-main-SHA verification, and production read-back. A release failure means the merged change is not yet released; do not retroactively redefine a passed PR merge check as failed.

When safe, complete work through implementation, tests, pull request, exact-head merge checks, merge, post-merge release, cleanup, and production verification. Do not claim CI, deployment, production state, or cleanup unless directly verified. If release is blocked after merge, report the product as **UNRELEASED/UNVERIFIED** and preserve the successful merge evidence separately.

After merge, remove temporary files and superseded work when the available GitHub operations allow it. Report the repository, Issue or PR, commit, measurable change, merge-check evidence, release evidence, files and lines changed, dependency or configuration changes, production verification, and remaining unverified items.
