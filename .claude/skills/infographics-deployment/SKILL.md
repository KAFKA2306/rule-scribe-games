---
name: infographics-deployment
description: Deploy game infographics (images, JSON storage, carousel display). Use when uploading infographic images to games, testing the carousel UI, applying database migrations, or troubleshooting infographics display in GamePage. Keywords: infographics, 図解, carousel, image gallery, game rules visualization.
---

# Infographics Deployment

Deploy infographic images (turn flow, setup, actions, winning conditions, components) to board games. Guides the complete workflow from database migration through image upload to carousel display verification.

## Architecture Overview

**Frontend**: InfographicsGallery carousel component (React)
**API**: PATCH `/api/games/{slug}` accepts infographics JSON
**Database**: PostgreSQL JSONB column with GIN index
**Data Format**: `{turn_flow: url, setup: url, actions: url, winning: url, components: url}`

## Deployment Checklist

### Phase 1: Database Migration (One-time setup)

1. **Check migration file exists**:
   ```bash
   ls backend/app/db/migrations/002_add_infographics_column.sql
   ```

2. **Apply SQL to Supabase** (requires dashboard access):
   - Go to: `https://app.supabase.com` → Your Project → SQL Editor
   - Create New Query
   - Paste and run:
   ```sql
   BEGIN;
   ALTER TABLE games ADD COLUMN IF NOT EXISTS infographics JSONB;
   CREATE INDEX IF NOT EXISTS idx_games_infographics ON games USING gin (infographics);
   COMMIT;
   ```
   - Verify: Column appears in `games` table schema

3. **Verify backend recognizes column**:
   ```bash
   task dev:backend
   # Check logs for no schema warnings
   ```

**Why migrations are essential**: PostgreSQL won't accept JSONB data without the column defined. Index ensures carousel queries stay fast even with 1000+ games.

### Phase 2: Prepare Infographics Images

Images must be **accessible URLs** (not local files). Options:
- Upload to GitHub (raw.githubusercontent.com)
- Upload to Cloudinary (free tier: 25GB)
- Upload to your CDN
- Use Vercel blob storage

**Format**: PNG or WebP, ~800x600px for carousel

### Phase 3: Upload Images via PATCH API

**Method 1: Direct PATCH request**:
```bash
curl -X PATCH http://localhost:8000/api/games/splendor \
  -H "Content-Type: application/json" \
  -d '{
    "infographics": {
      "turn_flow": "https://example.com/turn-flow.png",
      "setup": "https://example.com/setup.png",
      "actions": "https://example.com/actions.png",
      "winning": "https://example.com/winning.png",
      "components": "https://example.com/components.png"
    }
  }'
```

**Method 2: Frontend EditGameModal**:
- Click ✏️ Edit on game detail page
- Add image URLs to each infographics field
- Click Save

**Method 3: Python script (bulk)**:
```python
import asyncio
from app.core.supabase import supabase

async def upload_infographics(slug, urls_dict):
    result = supabase.table("games").update(
        {"infographics": urls_dict}
    ).eq("slug", slug).execute()
    print(f"✓ Updated {slug}")

# Run
asyncio.run(upload_infographics("splendor", {
    "turn_flow": "https://...",
    "setup": "https://...",
    # ...
}))
```

**Why URLs not files**: JSONB storage is for metadata/references, not binary data. URLs are lightweight and work across all clients.

### Phase 4: Verify Display

1. **Start dev servers**:
   ```bash
   task dev
   ```

2. **Navigate to game detail** (e.g., `http://localhost:5173/games/splendor`)

3. **Check 📊 図解 tab**:
   - Tab appears only if `game.infographics` has data
   - Images load without errors
   - Carousel navigation works (← →, dot buttons)
   - Counter shows "1 / N"

4. **Test edge cases**:
   - Missing images (404): Shows "画像を読み込めませんでした"
   - Partial data (only 2/5 keys): Shows only available images
   - Empty infographics: Tab doesn't appear

**Browser console** (F12):
- No 404 errors for image URLs
- No React warnings about prop types
- Network tab shows images loading with 200 status

### Phase 5: Production Deployment

After local verification:

```bash
# Commit changes
git add -A
git commit -m "feat: Add infographics for [game-names]"

# Deploy frontend
task deploy:frontend

# Deploy backend (serverless)
# (Automatic via Vercel on main branch)
```

**Post-deploy check**:
```bash
# Test production URL
curl https://your-production-domain/api/games/splendor | jq '.infographics'
```

## Common Issues & Fixes

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Tab doesn't appear | `infographics` is null or empty | PATCH endpoint missing or request failed; check DevTools Network |
| Image shows broken | URL is invalid or 404 | Verify URL in browser; use HTTPS; check CORS headers |
| Carousel stuck | Only 1 image; currentIndex logic | Add data for multiple infographic types (min 2) |
| TypeScript error | Model missing `infographics` field | Verify `backend/app/models/__init__.py` has field in GameUpdate |
| Database column error | Migration not applied | Run SQL in Supabase dashboard (Phase 1, step 2) |

## Data Model

**GameDetail model** (response):
```python
infographics: dict[str, str] | None = None
# Example: {
#   "turn_flow": "https://...",
#   "setup": "https://...",
#   "actions": "https://...",
#   "winning": "https://...",
#   "components": "https://..."
# }
```

**GameUpdate model** (PATCH request):
```python
infographics: dict[str, str] | None = None
```

**Component props** (React):
```jsx
<InfographicsGallery infographics={game.infographics} />
// game.infographics must be dict[str, str] or undefined
```

## Rules

**Image hosting**: Always use HTTPS and CORS-enabled URLs. Relative paths won't work in deployed Supabase.

**Data validation**: PATCH endpoint validates via Pydantic; invalid types reject with 422 Unprocessable Entity.

**Index performance**: GIN index on JSONB column ensures queries like `WHERE infographics @> '{"turn_flow": ...}'` stay sub-100ms even with 10k+ games.

**UI fallback**: If `infographics` missing, tab never appears (graceful degradation). No error messages shown to users.

## Out of Scope

- **Image generation**: Use `notebooklm-integration` skill for AI-generated infographics
- **CDN setup**: Cloudinary, Vercel Blob configuration (see CDN docs)
- **Bulk migration**: Data pipeline for importing 1000+ existing games (use custom Python script)
- **Mobile UI refinement**: CSS tweaks beyond base carousel (see `frontend-design` skill)
