# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

All operations are executed via `Taskfile.yml`. **Never** run `uv run`, `npm run`, or `python` directly—use `task` instead.

```bash
# Setup
task setup              # Install backend (uv sync) + frontend (npm install)
task setup:backend      # Backend only
task setup:frontend     # Frontend only

# Development
task dev                # Run FastAPI (8000) + Vite (5173) simultaneously
task dev:backend        # FastAPI dev server only
task dev:frontend       # Vite dev server only

# Quality & Linting
task lint               # Ruff (Python) + Prettier/ESLint (frontend)
task format             # Format and fix Python code

# Building & Preview
task build              # Frontend production build
task preview            # Preview production build locally

# Utilities
task clean              # Remove caches (__pycache__, .ruff_cache, dist/)
task kill               # Force-free ports 8000 & 5173
task validate-urls      # Validate all game URLs in DB
task validate-urls:recent  # Validate games updated in last 24h

# Development Loop
task issues             # List top 20 GitHub issues
task issues:critical    # List critical issues only
```

## Architecture Overview

### High-Level Flow

**Backend Pipeline** (FastAPI + Supabase + Gemini):
1. `POST /api/search` with `generate=true` → `GameService.search_games` queries Supabase by title/description
2. If generation enabled → `generate_metadata` calls Gemini 3.0 Flash, validates required fields, derives slug (kebab-case)
3. `supabase.upsert` writes by `source_url` or `slug` (conflict key); timestamps `updated_at`
4. `get_game_by_slug` increments `view_count` on detail fetch
5. `PATCH /api/games/{slug}?regenerate=true` runs background regeneration; bumps `data_version`

**Frontend** (React 18 + Vite):
- `App.jsx` loads recent games, supports live search and full search with generation trigger
- Selecting a game renders `GamePage` (markdown display, stats, external links) or `DataPage` (raw dataset)
- Optional Supabase Auth via `frontend/src/lib/supabase.js`

**Data Layer**:
- Supabase PostgreSQL with `games` table (schema in `docs/PROJECT_MASTER_GUIDE.md`)
- Synchronous Supabase client wrapped in `anyio.to_thread` for FastAPI async compatibility
- All rules/summaries must be **Japanese**; URLs nullable if unverified

### Directory Structure

```
app/
├── main.py                      # FastAPI app entry, CORS setup, router includes
├── routers/games.py             # REST endpoints: search, list, detail, update
├── services/game_service.py     # Orchestrates Supabase, Gemini, background tasks
├── core/
│   ├── settings.py              # Env loader (GEMINI_API_KEY, Supabase keys)
│   ├── gemini.py                # Google Generative Language API client
│   ├── supabase.py              # Supabase wrapper with anyio threading
│   └── logger.py                # Logging setup
├── utils/
│   ├── slugify.py               # Kebab-case slug generation
│   ├── affiliate.py             # Amazon search URL helper
│   └── logger.py                # Utility logging
└── prompts/prompts.yaml         # Generator, critic, link-resolve templates (Japanese)

api/
└── index.py                      # Vercel serverless handler → app.main.app

frontend/
├── src/
│   ├── App.jsx                  # Main entry, game list, search
│   ├── pages/GamePage.jsx        # Detail view + markdown rendering
│   ├── components/               # UI components (LoginButton, RegenerateButton, etc.)
│   ├── lib/
│   │   ├── api.js               # Fetch wrapper (search, list, detail, update)
│   │   └── supabase.js          # Supabase client from NEXT_PUBLIC_* env vars
│   └── index.css                # CSS variables, neon palette
└── vite.config.js, package.json, eslint.config.js

docs/
├── PROJECT_MASTER_GUIDE.md      # Single source of truth (schema, rules, UX standards)
├── SEO.md, CONTENT_GUIDELINES.md
└── other strategy docs

tests/
└── test_llm_flow.py             # Gemini flow harness; logs to tests/logs/
```

## Critical Patterns & Gotchas

### Environment Configuration
- **Required**: `GEMINI_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
- **Fallback**: `app/core/settings.py` defaults to `PLACEHOLDER`; missing keys break API calls at runtime
- Copy `.env.example` → `.env` and populate

### Generation Trigger
- `POST /api/search` with `generate=true` → calls Gemini, upserts record
- `GET /api/search` → no generation, read-only
- Ensure `GEMINI_API_KEY` is set before testing

### Upsert Conflict Resolution
- `supabase.upsert` uses `source_url` as conflict key if present; otherwise `slug`
- Title must be stable to avoid duplicate rows
- Amazon URL auto-filled with generic search; replace with verified link when available

### View Counter Side-Effect
- `get_game_by_slug` increments `view_count` on every fetch
- Bypass if you need read-only semantics

### Background Regeneration
- `update_game_content` uses FastAPI `BackgroundTasks`
- Response is immediate (`"status":"accepted"`); Gemini runs async
- No retry/backoff beyond single execution

### Frontend Auth (Optional)
- Supabase client returns `null` if `NEXT_PUBLIC_SUPABASE_*` missing
- Login button no-ops when auth unavailable
- Set env vars before testing auth flows

## Code Style & Architecture Rules

### Python (FastAPI)
- Target **Python 3.11+**
- Use async endpoints; prefer type hints; minimal abstractions
- Direct Supabase + Gemini calls (no heavy ORMs)
- Logging via `app/core/logger.setup_logging()`
- Package manager: `uv` (via `task setup:backend`)
- Linting: `task lint:backend` runs Ruff (check + fix + format)

### Prompts (YAML)
- Keep all generation/critic/link text in `app/prompts/prompts.yaml`
- Output must be **Japanese** for summaries/rules
- URLs conservative: confidence ≤0.5 unless verified

### Frontend (React/Vite)
- Prettier + ESLint (`task lint:frontend`)
- Components/pages: PascalCase; hooks: camelCase
- CSS variables in `frontend/src/index.css` (neon accent palette)
- Vite hot-reload enabled in dev mode

### Zero-Fat Philosophy (from `.claude/rules/`)
- **No try-catch/try-except** in business logic—let crashes surface full stack traces
- **No retry logic** in code—handle at infra level (Taskfile, systemd, Kubernetes)
- **No comments** (unless TODO/FIXME)—refactor naming instead
- **No docstrings**—use strict type hints
- **No boilerplate**—delete unused code immediately

## Database & Schema

Supabase PostgreSQL `games` table:
- `id`, `slug` (unique, kebab-case), `title`, `source_url` (nullable, conflict key)
- `rules_summary`, `setup_summary`, `gameplay_summary`, `end_game_summary` (Japanese text)
- `metadata` (JSON), `view_count`, `data_version`, `created_at`, `updated_at`

Full schema: `docs/PROJECT_MASTER_GUIDE.md`

## Deployment

- **Frontend**: Deployed to Vercel; builds on `main` branch
- **Backend**: Serverless via Vercel (`api/index.py`); same FastAPI app as local dev
- **CORS**: Wide open in dev/serverless (adjust `app/main.py` for production)

## Testing & Verification

```bash
task test                  # If defined in Taskfile (currently minimal)
task validate-urls         # Health check for game URLs
task gemini:verify         # Smoke test Gemini model access
```

## Troubleshooting & Content Extraction Skill

**Available**: `troubleshoot-and-extract` (Claude AI skill for rule-scribe-games)

### When to Invoke

Use this skill when you encounter **any** of these situations:

1. **Frontend Communication Issues**
   - API calls failing (500 errors, timeouts, CORS problems)
   - Search/generate feature broken
   - Connection errors after server restart
   - **Invoke**: "Frontend API is returning 500 errors when users click Generate..."

2. **PDF Content Extraction & Japanese Translation**
   - Need to extract rules from official game PDFs
   - Convert English rules to Japanese summaries
   - Create structured game records in database
   - **Invoke**: "I have official PDF rulebooks and need to extract content and create Japanese game records..."

3. **Japanese Visual Asset Generation**
   - Create cover images with Japanese text
   - Generate game artwork with AI
   - Produce multilingual marketing materials
   - **Invoke**: "I need Japanese cover images for board games with specific themes..."

4. **Issue Documentation & Root Cause Analysis**
   - Intermittent bugs that need systematic documentation
   - Track recurring problems (like dev server startup races)
   - Create GitHub issues with diagnostic data
   - **Invoke**: "This connection issue happens sometimes. How do I document it and find the root cause?"

### What the Skill Covers

| Part | Coverage | Output |
|------|----------|--------|
| **1** | Frontend API Debugging | 8-phase diagnostic with probability-ranked hypotheses |
| **2** | PDF Extraction Workflow | Complete step-by-step guide with production Python scripts |
| **3** | Japanese Image Generation | Exact task commands + optimized prompts |
| **4** | Issue Documentation | Root cause analysis + GitHub templates + diagnostic scripts |

### Quick Reference

**Typical Workflow:**
```
Problem identified
    ↓
Invoke troubleshoot-and-extract skill
    ↓
Skill returns: structured diagnostic/workflow/command/documentation
    ↓
Follow exact steps provided
    ↓
Problem solved (estimated 50% faster than generic approaches)
```

### Examples

**Example 1: Frontend API Error**
```
You: "When I click Generate on game search, I get a 500 error about Gemini"
Skill returns: 8-phase diagnostic → Root cause ranked → Specific fixes → Verification steps
```

**Example 2: PDF Extraction**
```
You: "I have Ticket to Ride rulebook PDF. Need to extract, translate to Japanese, and create game record"
Skill returns: 10-part workflow → Working Python script → Gemini integration → Validation checklist
```

**Example 3: Japanese Image**
```
You: "Need Splendor cover image in Japanese with Renaissance gem trading visuals"
Skill returns: Exact task command → 8-component optimized prompt → Quality dimensions
```

**Example 4: Issue Documentation**
```
You: "Dev server startup fails intermittently. Should I create an issue? How?"
Skill returns: Root cause identified → GitHub issue template → Diagnostic script → Fix recommendations
```

### Integration with Development

- **Do NOT** try to debug API issues without first invoking this skill
- **Do invoke** before creating GitHub issues for recurring problems
- **Reference** generated diagnostic scripts for team documentation
- **Use** generated GitHub templates for consistent issue tracking
- **Run** diagnostic scripts (`scripts/diagnose_dev_connection.sh`) before reporting issues

### Known Limitations

- Skill assumes `.env` file exists with required keys
- Assumes FastAPI/Supabase/Gemini stack (project-specific)
- Image generation requires GPU/proper environment setup
- Does not cover production deployment diagnostics (see Vercel docs)

---

## Project Philosophy & Resources

- **Single Source of Truth**: `docs/PROJECT_MASTER_GUIDE.md` contains all product/architecture/UX rules
- **Architectural Rules**: `.claude/rules/` (style.md, architecture.md, protocols.md, communication.md)
- **Zero-Fat Discipline**: Ruthlessly delete unused code, comments, boilerplate
- **Task-Driven Workflow**: All operations orchestrated via Taskfile; no direct CLI invocations
- **Troubleshooting**: Use `troubleshoot-and-extract` skill for debugging and content extraction

---

**Refer to** `docs/PROJECT_MASTER_GUIDE.md` **as the authoritative source for schema, API contracts, and UX standards.**
