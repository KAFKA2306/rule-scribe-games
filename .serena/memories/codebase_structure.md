# Codebase Structure

- `app/main.py`: FastAPI app, CORS, includes `/api` router + `/health` mirror.
- `app/routers/games.py`: REST endpoints for search/list/detail/update; POST search accepts `{query, generate}`.
- `app/services/game_service.py`: Orchestrates Supabase reads/writes, Gemini generation/critique, background regeneration, slugging, Amazon URL fill.
- `app/core/`: settings loader (`settings.py`), Gemini HTTP client (`gemini.py`), Supabase wrapper (`supabase.py`), logging setup (`logger.py`).
- `app/utils/`: `slugify.py` (kebab-case), `affiliate.py` (Amazon search URL helper), `logger.py`.
- `app/prompts/prompts.yaml`: Generator, critic, and link-resolve prompt templates; all expect Japanese content.
- `api/index.py`: Vercel handler that imports `app.main.app`.
- `frontend/src/`: React app (App.jsx, pages, components, lib, styles). `lib/api.js` is a thin fetch wrapper; `lib/supabase.js` builds a client from `NEXT_PUBLIC_` env vars.
- `Taskfile.yml`: canonical dev commands (setup, dev, lint, db:init, clean, kill, issues).
- `docs/PROJECT_MASTER_GUIDE.md`: single source of truth for product/architecture/design rules; contains DB schema and UX standards.
- `tests/test_llm_flow.py`: Gemini flow harness; writes JSON logs under `tests/logs/`.
