# Suggested Commands

## Setup
```bash
task setup            # uv sync backend deps + npm install frontend
cp .env.example .env  # then fill GEMINI_API_KEY + Supabase keys
```

## Development
```bash
task dev              # run FastAPI (8000) + Vite (5173) together
task dev:backend      # uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
task dev:frontend     # npm run dev -- --host
```

## Lint/Format
```bash
task lint             # Ruff check/format + Prettier + ESLint --fix
task lint:backend     # uv run ruff check --fix app && uv run ruff format app
task lint:frontend    # npm run format && npm run lint:fix
```

## Build/Preview
```bash
task build            # frontend production build
task preview          # serve built frontend locally
```

## Database & Utilities
```bash
task db:init          # print Supabase schema SQL
task kill             # free ports 8000/5173
```

## Tests
```bash
uv run pytest tests/test_llm_flow.py --api-key "$GEMINI_API_KEY" --query "カタン"
# Playwright E2E (run from frontend/):
cd frontend && npx playwright test
```
