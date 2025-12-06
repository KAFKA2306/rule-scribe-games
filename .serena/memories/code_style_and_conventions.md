# Code Style and Conventions

- **Python (FastAPI)**: Target Python 3.11+; async endpoints; prefer type hints; minimal abstractions (direct Supabase + Gemini calls). Logging via `app/core/logger.setup_logging()`. Use `uv` as package manager; Ruff handles lint + format (`task lint:backend`).
- **Prompts**: Keep all generation/critic/link text in `app/prompts/prompts.yaml`. Output must stay Japanese for summaries/rules; URLs conservative (confidence ≤0.5 unless verified).
- **Frontend (React/Vite)**: Prettier + ESLint (`task lint:frontend`); components/pages in PascalCase; hooks camelCase. CSS variables defined in `frontend/src/index.css` (neon accent palette).
- **Env/Config**: Copy `.env.example` → `.env`; required keys: `GEMINI_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`), `NEXT_PUBLIC_SUPABASE_ANON_KEY` for frontend auth. Defaults to `PLACEHOLDER` otherwise.
- **Data rules**: Slug must be kebab-case; rules and summary in Japanese; URL fields nullable if unsure; `data_version` increments on regeneration; `view_count` incremented on GET detail.
- **Project etiquette**: Follow docs/PROJECT_MASTER_GUIDE.md as source of truth; avoid heavy frameworks/ORMs; keep experimental work in `experiments/` (not currently present here).
