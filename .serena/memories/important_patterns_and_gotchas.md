# Important Patterns and Gotchas

- **Env placeholders break runtime**: `app/core/settings.py` falls back to `PLACEHOLDER`; missing `GEMINI_API_KEY` causes httpx 401/404 from Gemini; missing Supabase URL/key crashes client creation.
- **Generation trigger**: POST `/api/search` sets `generate=true` to call Gemini; GET `/api/search` and POST without `generate` never create records.
- **Upsert rules**: `supabase.upsert` uses `source_url` as conflict key when present, otherwise `slug` (derived from title). Ensure title is stable to avoid duplicate rows.
- **Background regeneration**: `update_game_content` uses FastAPI `BackgroundTasks`; response is immediate `"status":"accepted"` while Gemini runs. No retry/backoff beyond single run.
- **Amazon URL auto-fill**: `generate_metadata` always sets `amazon_url` to a generic Amazon search URL for the title; replace with verified link when available.
- **View counter side-effect**: `get_game_by_slug` increments `view_count` on every fetch; bypass if you don’t want reads to mutate state.
- **Front-end auth optional**: Supabase client returns `null` if `NEXT_PUBLIC_SUPABASE_*` env vars are missing; login button then no-ops—set keys before testing auth flows.
- **Ports and hosts**: Dev servers bind to `0.0.0.0` (`uvicorn --host 0.0.0.0 --port 8000`, Vite `--host` 5173); Taskfile `kill` force frees both ports.
