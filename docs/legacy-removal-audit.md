---
title: Legacy removal audit
status: active
updated: 2026-08-22
---

# Legacy removal audit

This file is temporary audit evidence for the legacy-removal change and must be deleted before merge.

## Live legacy paths found on main

- public `SearchRequest.generate` compatibility flag and POST `/api/search` branch
- `GameService.generate_with_notebooklm()` and NotebookLM/PDF pipeline placeholders
- one-off direct catalog writers (`add_manual_game.py`, `add_new_games.py`, `populate_manual_games.py`, `seed_coup_official.py`)
- broken `db:init` Taskfile entry referencing absent `backend/init_db.sql`
- committed historical test logs
- typo duplicate `carcssonne.webp` identical to canonical `carcassonne.webp`

## Boundary

Already-applied SQL migrations whose filenames contain `legacy` are database history, not live compatibility code. They are not deleted in-place because production and greenfield migration replay depend on ordered history. They become removable only through an explicit migration baseline/squash that proves both fresh-schema and existing-production upgrade equivalence.

Runtime rule-row authority is a separate live migration: GamePage still renders `games.rules_content` and summary columns for catalog-wide records, while source-bound RuleSets currently cover only part of the catalog. It must be removed only after RuleSet projection coverage is complete or the unsupported path fails closed; silently deleting user-visible rules is not acceptable.
