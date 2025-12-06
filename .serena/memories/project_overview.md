# Project Overview

## Purpose
- AI powered board-game wiki that can search Supabase, fall back to Gemini 2.5 Flash, and store structured rule summaries for fast re-use.
- Focus: Japanese-language summaries with setup/gameplay/end-game guidance plus verified outbound links (official/Amazon/image).

## Tech Stack
- Backend: FastAPI (`app/main.py`), async Supabase client, httpx to Google Generative Language API.
- Frontend: React 18 + Vite + Vanilla CSS (`frontend/src`), Supabase Auth optional.
- Database: Supabase Postgres (`games` table defined in `docs/PROJECT_MASTER_GUIDE.md` & `backend/init_db.sql` copy in docs).
- Tooling: `uv` for Python deps, Taskfile for orchestration, Ruff for lint/format, Prettier + ESLint for frontend, Vercel serverless entry at `api/index.py`.

## Core Flows
- GET `/api/search`: Supabase search only (no generation) via `GameService.search_games`.
- POST `/api/search` with `generate=true`: Gemini metadata generation (`generate_metadata`) then Supabase `upsert`; slug auto-derived; Amazon search URL filled for convenience.
- GET `/api/games{?limit,offset}`: recent games sorted by `updated_at`.
- GET `/api/games/{slug}`: fetch + view counter increment.
- PATCH `/api/games/{slug}?regenerate=true`: background refresh of a game’s content via Gemini + Supabase upsert (bumps `data_version`).

## Environment
- Required: `GEMINI_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, and either `SUPABASE_SERVICE_ROLE_KEY` (preferred) or `SUPABASE_KEY`/`NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Defaults in `app/core/settings.py` fall back to `PLACEHOLDER`; missing keys will break API calls at runtime.
