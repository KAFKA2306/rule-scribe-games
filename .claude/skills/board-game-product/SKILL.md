---
name: board-game-product
description: Improve ボドゲのミカタ as a trustworthy, useful, revenue-producing board-game product. Use for game rules, discovery/search, setup/play clarity, monetization flows, repository changes, CI, release, and production verification.
---

# Board Game Product

## Goal

Maximize durable player value and revenue while reducing repeated manual work, duplicated code, dependencies, and operational complexity.

## Before changing anything

Follow `AGENTS.md` as the repository-wide authority. Inspect the current `main`, related Issues/PRs, relevant code/data/workflows, CI, deployment, production state, usage/conversion evidence, and official game sources needed for the active workline.

Define one observable player-facing success condition before implementation.

## Product priority

Choose work by expected impact on:

1. acquisition and discovery/search;
2. rule correctness and trust;
3. setup and play clarity;
4. retention and repeat use;
5. monetizable flows such as existing affiliate paths;
6. production reliability and operating cost.

Continue the canonical Issue/PR when it remains valuable. Do not create parallel worklines for the same player problem.

## Rule authority

For externally verifiable game facts:

- prefer current publisher or designer sources;
- preserve product, edition, language, platform, revision, expansion, FAQ, and errata boundaries;
- inspect relevant PDF pages when the source is a PDF;
- store source URL plus version/revision evidence in the existing structured model;
- keep official rules separate from summaries, translations, interpretations, recommendations, and generated text;
- never reconstruct missing official rules from model memory when a suitable primary source is required;
- do not silently mix base games, expansions, sequels, editions, or regional variants.

If primary authority is insufficient, mark the item blocked rather than filling gaps with guesses.

## Implementation

Use existing repository structures and `Taskfile.yml` before adding helpers, workflows, schemas, dependencies, or documents.

Prefer generic structured data and shared validation over game-specific scripts or tests. For repeated migrations or publication work, batch multiple reviewed games through the existing shared pipeline when edition/source review remains independently verifiable.

Do not impose implementation dogma such as a mandatory HTTP client, mandatory crash behavior, mandatory AI provider, or mandatory external content tool. Choose the smallest reliable implementation supported by current code and production requirements.

## Verification loop

For code or data changes:

1. run the narrowest meaningful local/repository validation;
2. run the affected shared CI without weakening checks;
3. verify the exact PR head before merge;
4. treat merge and release as separate states;
5. after merge, verify exact-main deployment/release state;
6. read back the public API/page and relevant production data/runtime state;
7. verify that the observable player-facing success condition actually holds.

A green PR is not proof of production success. A merged but unverified release is `UNRELEASED/UNVERIFIED`.

## Revenue and efficiency

Use real usage/conversion evidence where available. Prefer high-demand, monetizable, source-verifiable games over low-impact maintenance.

Preserve existing affiliate or purchase flows unless the task intentionally changes them. Do not claim revenue lift without observed conversion or revenue evidence.

Reduce repeated agent work by consolidating shared candidate selection, source manifests, validation, generation, CI, and production readback. Keep human/agent review focused on product identity, edition boundaries, official sources, claims, and evidence.

## Completion report

Report only what was directly verified: player/revenue Before→After, trusted evidence, monetization path when grounded, PR/CI/merge/release/production state, removed duplication/manual work, and the next highest-value games problem.
