# RuleScribe Games

![ボドゲのミカタ](assets/02_ボドゲのミカタ.jpg)

[![Vercel](https://therealsujitk-vercel-badge.vercel.app/?app=rule-scribe-games)](https://rule-scribe-games.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![React](https://img.shields.io/badge/react-18.x-61dafb.svg)](https://reactjs.org/)

AI-Powered board game rule wiki & summarizer — 「世界中のボードゲームのルールを、瞬時に正確に日本語で」。

---

## Quick Links
- Single Source of Truth: `docs/PROJECT_MASTER_GUIDE.md`
- Live Demo: <https://rule-scribe-games.vercel.app>
- API Health (local): `http://localhost:8000/health`
- Taskfile command list: `task --list`

## What It Does
- 🔍 Searches Supabase first; on cache miss, prompts Gemini 2.5 Flash (Google Search Grounding) to generate Japanese summaries.
- 📚 Structures rules into setup / gameplay / end-game, plus keywords and verified outbound links (official, BGG, Amazon, image).
- ⚡ Caches generated results back to Supabase so subsequent requests are instant.
- 🖥️ React/Vite frontend with Supabase Auth optional; serverless-ready via Vercel (`api/index.py` mounts the same FastAPI app).

## Architecture at a Glance
- Frontend: React 18 + Vite + Vanilla CSS variables (`frontend/src`).
- Backend: FastAPI (`app/main.py`) with async Supabase client and Gemini HTTP client (`app/core/gemini.py`).
- Database: Supabase Postgres `games` table (schema in `backend/init_db.sql` and master guide).
- Deployment: Vercel serverless (Python), wide-open CORS for the app.

## Prerequisites
- Python 3.11+, Node.js 18+
- Supabase project (URL + anon key, service role key recommended)
- Google Gemini API key (Google AI Studio)
- `uv` and `task` installed

## Setup (3 Steps)
```bash
cp .env.example .env            # 填入 GEMINI_API_KEY, Supabase keys
task setup                      # uv sync + npm install
task dev                        # starts FastAPI :8000 and Vite :5173
```

## Environment Variables (必須)
| Key | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Google Generative Language API key |
| `GEMINI_MODEL` (optional) | defaults to `gemini-2.5-flash` |
| `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` (preferred) or `SUPABASE_KEY` | writes/reads for backend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend Auth + client queries |

Defaults in `app/core/settings.py`; missing keys will break requests.

## Run & Develop
- `task dev` — run both servers with hot reload (backend 8000, frontend 5173).
- `task dev:backend` / `task dev:frontend` — run individually.
- `task build` → `task preview` — production build & preview frontend.
- `task lint` — Ruff + Prettier + ESLint (`lint:backend`, `lint:frontend` available).

## API Surface
- `GET /api/health` — liveness.
- `GET /api/games?limit=50&offset=0` — recent games.
- `GET /api/games/{slug}` — details (increments `view_count`).
- `GET /api/search?q=...` — Supabase search only.
- `POST /api/search` `{ "query": "...", "generate": true|false }` — when `generate=true`, triggers Gemini + Supabase upsert and returns the new record.
- `PATCH /api/games/{slug}?regenerate=true&fill_missing_only=false` — background refresh via Gemini; when `fill_missing_only=true`, only fills blank fields and keeps existing data.

## Testing
- Backend LLM harness: `uv run pytest tests/test_llm_flow.py --api-key "$GEMINI_API_KEY" --query "カタン"` (writes logs to `tests/logs/`).
- Frontend E2E (optional): `cd frontend && npx playwright test`.

## Troubleshooting
- Gemini 401/404 → `GEMINI_API_KEY` 未設定 or typo。`.env` を再読み込みして `task dev` を再起動。
- Gemini 429 (rate limit) → 数分待つ / 呼び出し頻度を下げる。追加キーを `GEMINI_API_KEY_2` などで用意し、将来のキー・ローテーション実装に備える。まず GET/POST検索のみでキャッシュを確認し、必要なときだけ `generate=true` を叩く。
- Supabase 401/403 → `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_KEY` が不足または誤り。`NEXT_PUBLIC_SUPABASE_URL` も合わせて確認。
- Duplicate or missing rows → `title` が揺れると `slug` が変わり upsert が別行扱いに。`source_url` を安定キーにすると衝突が減る。
- `PATCH ...?regenerate=true` で結果が反映されない → バックグラウンド実行のため即時反映されない。ログを確認し、必要なら `fill_missing_only=true` で安全補完に切替。
- Frontend リストが空 → `NEXT_PUBLIC_SUPABASE_*` 未設定で `supabase` クライアントが `null`。環境変数をセットして再ビルド。
- 画面が真っ白 / 表示されない → `npm install` 忘れ / `task dev` でフロントが起動していない / ブラウザコンソールのJSエラー。開発時は `http://localhost:5173` にアクセスし、`/api` が 8000 へ届くように相対パスのまま fetch する（別ポート直指定だとCORSで失敗）。環境変数変更後はフロントを再起動。
- Supabase スキーマ不一致 → `backend/init_db.sql` を Supabase SQL エディタで再実行し、足りないカラムやインデックスを反映。RLS/ポリシーを有効にしている場合は適宜見直す。既存データがある場合はバックアップを取ってから適用。
- Ports busy (8000/5173) → `task kill` で解放。
- Vercel 502/timeout → コールドスタートや env 未設定が原因。Vercel の環境変数にも `.env` の内容を反映。

## Project Structure
```
rule-scribe-games/
├── app/                # FastAPI backend (core, routers, services, prompts, utils)
├── api/index.py        # Vercel serverless entry
├── frontend/           # React/Vite client (pages, components, lib, styles)
├── docs/PROJECT_MASTER_GUIDE.md
├── Taskfile.yml        # canonical commands
└── tests/              # LLM flow harness logs
```

## License
MIT © RuleScribe Games contributors
