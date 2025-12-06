# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI backend. Core config in `app/core/`, HTTP routers in `app/routers/`, business logic in `app/services/`, prompts in `app/prompts/`, shared models in `app/models.py`.
- `api/index.py`: Vercel entry point that mounts `app.main.app` for serverless deployment.
- `frontend/`: React + Vite client (`src/` for pages/components, `public/` for static assets).
- `tests/`: Integration/LLM harness in `tests/test_llm_flow.py`; Playwright E2E specs live in `frontend/tests/`.
- `docs/PROJECT_MASTER_GUIDE.md`: Single source of truth for architecture and UX rules. Consult this first.
- `Taskfile.yml`: Canonical command shortcuts; prefer `task <name>` over ad-hoc scripts.

## Build, Test, and Development Commands
- Install deps: `task setup` (runs `uv sync` for Python and `npm install` in `frontend/`).
- Dev servers: `task dev` (starts FastAPI on `:8000` and Vite on `:5173`; CORS already open).
- Lint/format: `task lint` (Ruff check+format for backend; Prettier + ESLint `--fix` for frontend).
- Frontend build/preview: `task build`, `task preview`.
- DB schema reference: `task db:init` (prints `backend/init_db.sql` contents).
- Free stuck ports: `task kill`.

## Coding Style & Naming Conventions
- Python: 4-space indent, type hints encouraged; module/function names in `snake_case`, Pydantic models in `PascalCase`. Ruff enforces imports/spacing—run via `task lint:backend`.
- JavaScript/React: Prettier defaults (2-space indent, single quotes allowed), components/pages `PascalCase`, hooks `useCamelCase`, files under `frontend/src/` follow folder-based grouping (`components/`, `pages/`, `lib/`).
 - Favor straightforward Supabase + Gemini integrations; add abstractions only when they clearly cut duplication or improve ownership (see `app/services/game_service.py`).

## Testing Guidelines
- Frontend E2E: from `frontend/`, run `npx playwright test` (requires `npm install`). Use when changing routing/search/UI flows.
- LLM flow check: `uv run python tests/test_llm_flow.py --api-key <GEMINI_KEY> --query "カタン"` writes a JSON log under `tests/logs/`. Keep it optional for CI; use it when touching prompt or generation logic.
- Add small, deterministic unit tests near new logic when feasible; prefer async-friendly patterns for FastAPI services.

## Commit & Pull Request Guidelines
- Commit style mirrors history: `feat: ...`, `fix: ...`, `refactor: ...`. Keep messages imperative and concise.
- Reference the GitHub issue in the PR body; summarize what changed and why. Include evidence for user-facing updates (screenshots of pages or curl logs for APIs).
- Ensure `task lint` passes before opening a PR; mention any intentionally skipped tests with rationale.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; populate `GEMINI_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, and keys before running the backend or Playwright tests.
- Never commit secrets or generated logs under `logs/`. Prefer `.env` + environment variables in deployment.
- Supabase service role keys (`SUPABASE_SERVICE_ROLE_KEY`) stay server-side only; frontend uses the public anon key from `.env`.
