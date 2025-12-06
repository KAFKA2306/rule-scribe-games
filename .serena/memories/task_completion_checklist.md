# Task Completion Checklist

- [ ] Create `.env` from `.env.example`; set `GEMINI_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [ ] Install deps (`task setup`) and verify `uv run uvicorn app.main:app --reload` boots without missing-key errors.
- [ ] Run `task dev` and confirm:
  - Backend: `GET /api/health` returns `{"status":"ok"}`.
  - Frontend: home page loads game list; search works; generation banner shows when creating new entry.
- [ ] Lint/format: `task lint` (or backend/frontend subtasks) succeeds.
- [ ] Run optional tests relevant to changes (e.g., `pytest tests/test_llm_flow.py ...`, Playwright for UI changes).
- [ ] Capture evidence for issue/PR: API logs or curl output for backend changes; screenshots/video for UI changes.
- [ ] Avoid committing secrets or `logs/`; keep modifications within scope of requested task.
