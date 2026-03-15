---
name: troubleshoot-and-extract
description: |
  Diagnose and fix frontend communication issues, extract game content from official PDFs, and generate Japanese visuals for the rule-scribe-games project.

  Use this skill when: (1) frontend API calls are failing (search not working, game detail won't load, regenerate button errors), (2) you need to extract game rules/setup/gameplay from official PDFs and structure them, (3) you need to generate Japanese game cover images or visual materials, (4) you're tracking or documenting game content issues.

  This is a project-specific troubleshooting skill for rule-scribe-games that combines network debugging, content extraction, and asset generation.
---

## Overview

This skill walks through a structured troubleshooting and content extraction workflow for rule-scribe-games:

1. **Diagnose Frontend Issues** — Check network logs, validate API responses, verify environment configuration
2. **Extract PDF Content** — Parse official game PDFs to get structured rules/setup/gameplay/end-game
3. **Generate Japanese Visuals** — Create cover images and visual assets with Japanese text
4. **Document & Track** — Record findings in GitHub issues or project tracking

## Part 1: Frontend Communication Troubleshooting

### Symptom: API calls failing (network errors, 500s, timeouts, CORS)

**Checklist:**

1. **Verify environment setup**
   - Is `GEMINI_API_KEY` set? → `echo $GEMINI_API_KEY`
   - Are Supabase keys present? → `echo $NEXT_PUBLIC_SUPABASE_URL`, `echo $SUPABASE_SERVICE_ROLE_KEY`
   - Are `.env` files in place? (`.env` for backend, `.env.local` in `frontend/` for frontend)

2. **Check backend is running**
   - Open `http://localhost:8000/health` in browser or `curl -s http://localhost:8000/health | jq`
   - If no response: `task kill` then `task dev:backend`

3. **Check frontend is running & connected**
   - Browser console (`F12` → Console tab) — any red errors?
   - Network tab (`F12` → Network) — watch for failed requests
   - Check `frontend/src/lib/api.js` — is the base URL correct? (should be `http://localhost:8000` in dev)

4. **Test API directly**
   ```bash
   # Test search endpoint (no generation)
   curl -X GET "http://localhost:8000/api/search?query=catan"

   # Test search with generation
   curl -X POST "http://localhost:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "test game", "generate": true}'

   # Test detail fetch
   curl -X GET "http://localhost:8000/api/games/catan"
   ```

5. **Check Supabase connection**
   - Can you reach Supabase URL? → `curl -I $NEXT_PUBLIC_SUPABASE_URL`
   - Is service role key valid? → Try `uv run python -c "from app.core.supabase import supabase_client; print(supabase_client)"`

6. **Check Gemini API**
   - `uv run python -m scripts/verify_gemini_model.sh` (or run the Bash test manually)
   - Gemini 401? → Check `GEMINI_API_KEY` format (should start with `AIzaSy...`)

7. **Clear caches & restart**
   - Frontend: `task clean` then `task dev:frontend`
   - Backend: `task kill` then `task dev:backend`
   - Browser: Hard refresh (`Cmd+Shift+R` or `Ctrl+Shift+R`)

### If still broken:

- **Check logs**: Backend logs appear in terminal where `task dev:backend` runs; frontend logs in browser Console
- **Isolate the problem**: Does the issue happen on `GET /api/search` (read-only) or only on `POST /api/search` (with generation)?
  - If generation fails, it's Gemini; if reads fail, it's Supabase
- **Read the stack trace**: Don't wrap the error in try-catch — the full trace tells you the root cause

---

## Part 2: Extract Content from Official Game PDFs

### Workflow: PDF → Structured Game Data

**Input**: Official game PDF (e.g., rulebook from publisher website or BGG)
**Output**: Structured JSON with `rules_summary`, `setup_summary`, `gameplay_summary`, `end_game_summary` (all in Japanese if translating)

**Steps:**

1. **Obtain the PDF**
   - Download from official publisher, BGG, or game website
   - Save to a temp location (e.g., `/tmp/game-rules.pdf`)

2. **Extract text from PDF**
   - Use Python with `PyPDF2` or `pdfplumber` (installed via `uv sync`)
   ```python
   import pdfplumber
   with pdfplumber.open('/tmp/game-rules.pdf') as pdf:
       full_text = ''.join([page.extract_text() for page in pdf.pages])
       print(full_text)
   ```

3. **Parse into sections**
   - Identify: Setup/Components → Gameplay Flow → End Condition → Special Rules
   - Look for headers like "セットアップ", "ゲームプレイ", "終了条件", "リソース"
   - Extract relevant paragraphs

4. **Call Gemini to structure & translate (if needed)**
   - If PDF is in English, ask Gemini to translate to Japanese
   - Use the `generate_metadata` prompt from `app/prompts/prompts.yaml`
   - Ensure output includes all four fields: `setup_summary`, `gameplay_summary`, `end_game_summary`, `rules_summary`

5. **Validate & create record**
   - Check all 4 fields are present and non-empty
   - Derive `slug` from title (kebab-case)
   - Create game record via `POST /api/search` with `generate=true`, or insert directly to Supabase

**Example script:**
```python
# scripts/extract_pdf_and_create_game.py
import pdfplumber
from app.core.gemini import generate_metadata
from app.core.supabase import supabase_client

pdf_path = "path/to/rules.pdf"
game_title = "Game Title"

with pdfplumber.open(pdf_path) as pdf:
    pdf_text = ''.join([p.extract_text() for p in pdf.pages])

# Call Gemini
metadata = generate_metadata(title=game_title, context=pdf_text)

# Insert to Supabase
supabase_client.table('games').upsert({
    'title': game_title,
    'slug': slugify(game_title),
    'rules_summary': metadata.get('rules_summary'),
    'setup_summary': metadata.get('setup_summary'),
    'gameplay_summary': metadata.get('gameplay_summary'),
    'end_game_summary': metadata.get('end_game_summary'),
    'source_url': 'pdf',
}).execute()
```

---

## Part 3: Generate Japanese Game Visuals

### Workflow: Game Title/Description → Japanese Cover Image

**Available commands:**

```bash
# Generate AI image with Japanese text
task image:gen:ai PROMPT="ボードゲーム『カタン』の壮大な島の風景、カラフルな鉱物、プレイヤーの駒。日本語タイトル付き。" OUTPUT="assets/catan-cover.png"

# Create composite header (for multiple images)
task image:gen:composite OUTPUT="assets/header.png" INPUTS="img1.png img2.png img3.png"
```

**Tips for prompts:**
- Include game theme keywords (e.g., 戦略, 協力, 冒険)
- Request Japanese text overlay if desired
- Specify dimensions (default 1280x670)
- Be specific about color palette, art style

**Integration:**
- After generating, upload image to Supabase Storage (or embed in game record as URL)
- Store path in game's `metadata` JSON field

---

## Part 4: Document Issues & Track

### Create a GitHub Issue for recurring problems

```bash
# Format: Clear title, full context, reproduction steps
gh issue create \
  --title "Frontend: POST /api/search returns 500 on generation" \
  --body "
- **Environment**: Local dev, Python 3.11, Node 18
- **Steps to reproduce**:
  1. Open http://localhost:5173
  2. Search for 'new game'
  3. Click 'Generate'
- **Expected**: Game metadata generated, record created
- **Actual**: 500 error in backend, no record
- **Error log**: [paste stack trace here]
- **Root cause** (if found): Gemini API key missing or invalid
"
```

### Document findings in a memory or notes file

Create `docs/TROUBLESHOOTING.md` with common issues:
```markdown
## Frontend API Errors

### 500 on POST /api/search with generate=true
- Check `GEMINI_API_KEY` is set
- Verify Gemini model is available
- Look at stack trace in backend logs

### CORS errors on frontend
- Ensure backend is running with `--host 0.0.0.0`
- Check frontend is sending correct Origin header

### View count not incrementing
- This is intentional — only increments on GET /api/games/{slug}
- Not a bug, expected behavior
```

---

## Workflow Summary

When facing any of the original issues:

1. **Frontend error?** → Run Part 1 checklist, isolate the layer (frontend/backend/Gemini/Supabase)
2. **Need game content from PDF?** → Follow Part 2, extract + structure + validate
3. **Need visuals?** → Use Part 3 commands, generate cover images with Japanese text
4. **Recurring problem?** → Document in Part 4 (GitHub issues + troubleshooting wiki)

---

## Notes

- **Zero-Fat Rule**: Don't add defensive try-catch blocks; let errors surface the stack trace
- **Env-first**: Most issues are env configuration; verify keys before debugging code
- **Test in isolation**: Use `curl` to test backend without frontend noise
- **Keep it Japanese**: When generating or translating content, ensure Japanese output quality
