# Architecture Overview

## High-Level
- Vercel serverless entry (`api/index.py`) mounts the same FastAPI app as local dev (`app/main.py`); CORS wide open.
- Backend pipeline per query:
  1) `GameService.search_games` → Supabase `games` table search (`title`/`description` ilike).
  2) If POST `/api/search` and `generate=true`, `generate_metadata` prompts Gemini with DB context, validates required fields, sets slug (kebab-case), timestamps `updated_at`, and injects an Amazon search URL.
  3) `supabase.upsert` writes by `source_url` if present, else `slug`; `get_game_by_slug` increments `view_count`.
  4) `update_game_content` runs regeneration in a FastAPI background task and increments `data_version`.
- Prompt library lives in `app/prompts/prompts.yaml` (generator + critic + link_resolve). Gemini client (`app/core/gemini.py`) enforces JSON output and cleans code fences.

## Frontend Flow
- `frontend/src/App.jsx` loads recent games, supports live search (POST `/api/search` without generation) and full search with generation trigger.
- Selecting a game renders `GamePage` with markdown, stats, and external links; `DataPage` surfaces raw dataset.
- Supabase Auth (`frontend/src/lib/supabase.js`) is optional; UI shows login button when configured.

## Data & Caching
- Supabase helper (`app/core/supabase.py`) uses synchronous client wrapped with `anyio.to_thread` for async FastAPI compatibility.
- Document symbol caches for Serena are stored under `.serena/cache/{python,typescript}`; Taskfile’s `clean` target does not remove them.
