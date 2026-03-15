# Infographics Deployment Guide

Complete step-by-step guide to deploy the infographics carousel feature.

## Prerequisites

- ✅ Frontend: InfographicsGallery component implemented
- ✅ Backend: GameUpdate model supports infographics
- ⏳ Database: Migration SQL created, needs Supabase application
- ✅ Scripts: Migration and test suite ready

## Step 1: Apply Database Migration (Supabase Dashboard)

**Critical**: This step must be completed first.

1. Go to: **https://app.supabase.com**
2. Select your project
3. Click **SQL Editor** (left sidebar)
4. Click **New Query**
5. Copy and paste this SQL:

```sql
BEGIN;
ALTER TABLE games ADD COLUMN IF NOT EXISTS infographics JSONB;
CREATE INDEX IF NOT EXISTS idx_games_infographics ON games USING gin (infographics);
COMMIT;
```

6. Click **Run** (or Ctrl+Enter)
7. You should see: `✓ Query successful - 2 rows affected`

**Verify**: Go to **Tables** → **games** → scroll right and confirm `infographics` column exists (type: `jsonb`)

---

## Step 2: Verify Migration & Upload Sample Data

**After Supabase migration is applied:**

```bash
cd /home/kafka/projects/rule-scribe-games

# Run migration checker and sample data uploader
python backend/scripts/migrate_infographics.py
```

**Expected output**:
```
🎨 Infographics Migration & Deployment
======================================================================
✓ Migration already applied - infographics column exists

📤 Uploading sample infographics...
✓ splendor: 5 infographics uploaded
✓ catan: 2 infographics uploaded

🎠 Verification checklist:
  1. Start dev servers: task dev
  2. Navigate to: http://localhost:5173/games/splendor
  3. Check 📊 図解 tab appears
  4. Test carousel navigation (← →, dot buttons)
  5. Counter should show '1 / 5' for splendor, '1 / 2' for catan

✅ Infographics deployment ready!
```

---

## Step 3: Test Carousel Locally

```bash
# Start both dev servers
task dev

# Wait 10 seconds for startup, then visit:
# http://localhost:5173/games/splendor
```

**Visual checklist**:
- [ ] Page loads without errors
- [ ] 📊 図解 tab appears (between 📖 and 📋)
- [ ] Tab shows carousel with 5 images
- [ ] ← Previous button works (disabled on first image)
- [ ] Dot buttons navigate to each image
- [ ] Next → button works (disabled on last image)
- [ ] Counter shows "1 / 5"
- [ ] F12 console shows no errors

**Test edge case**: Click on Catan game
- [ ] 📊 図解 tab shows only 2 images (partial data)
- [ ] Counter shows "1 / 2"

---

## Step 4: Run Automated Tests

```bash
# Test API endpoints
pytest tests/test_infographics.py -v

# Expected output:
# test_api_health PASSED
# test_get_game_with_infographics PASSED
# test_patch_infographics PASSED
# test_patch_partial_infographics PASSED
# test_carousel_key_types PASSED
# ... (all tests should pass)
```

---

## Step 5: Upload Real Infographics (Optional)

Once migration is applied, you can upload real game infographics:

### Method 1: CLI (Single Game)

```bash
curl -X PATCH http://localhost:8000/api/games/splendor \
  -H "Content-Type: application/json" \
  -d '{
    "infographics": {
      "turn_flow": "https://your-cdn.com/splendor-turn-flow.png",
      "setup": "https://your-cdn.com/splendor-setup.png",
      "actions": "https://your-cdn.com/splendor-actions.png",
      "winning": "https://your-cdn.com/splendor-winning.png",
      "components": "https://your-cdn.com/splendor-components.png"
    }
  }'
```

### Method 2: Frontend UI

1. Navigate to game detail (e.g., http://localhost:5173/games/splendor)
2. Click ✏️ **Edit** button
3. Scroll to "Infographics" section
4. Paste image URLs for each type
5. Click **Save**

### Method 3: Python Script (Bulk)

Create `scripts/upload_my_infographics.py`:

```python
import asyncio
from app.core.supabase import supabase

GAMES = {
    "splendor": {
        "turn_flow": "https://...",
        "setup": "https://...",
        # ... fill in your URLs
    },
    "catan": {
        # ...
    },
}

async def upload_all():
    for slug, infographics in GAMES.items():
        supabase.table("games").update(
            {"infographics": infographics}
        ).eq("slug", slug).execute()
        print(f"✓ {slug}")

asyncio.run(upload_all())
```

Then run:
```bash
python scripts/upload_my_infographics.py
```

---

## Step 6: Commit & Deploy

```bash
# Commit migration and test files
git add backend/scripts/migrate_infographics.py
git add tests/test_infographics.py
git add docs/INFOGRAPHICS_DEPLOYMENT.md
git add backend/app/db/migrations/002_add_infographics_column.sql
git commit -m "feat: Implement infographics carousel with migration and tests"

# Push to main (triggers Vercel deployment)
git push origin main
```

**Deployment verification**:
- Frontend builds successfully on Vercel
- Backend serverless function deploys
- Test in production: https://your-app.vercel.app/games/splendor

---

## Troubleshooting

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| "Could not find column 'infographics'" | Migration not applied | Re-check Supabase SQL Editor, click Run |
| 📊 Tab doesn't appear | infographics is null | PATCH the game with image URLs |
| Images show broken | Invalid URL or 404 | Verify URL in browser, use HTTPS |
| Carousel stuck | Only 1 image | Add at least 2 infographics |
| Test failures | API not responding | Verify `task dev` running on ports 8000, 5173 |

---

## Data Format Reference

### JSONB Storage
```json
{
  "turn_flow": "https://cdn.example.com/turn-flow.png",
  "setup": "https://cdn.example.com/setup.png",
  "actions": "https://cdn.example.com/actions.png",
  "winning": "https://cdn.example.com/winning.png",
  "components": "https://cdn.example.com/components.png"
}
```

### Valid Carousel Keys
- `turn_flow` 🔄 - Turn sequence visualization
- `setup` ⚙️ - Game setup diagram
- `actions` 🎲 - Available actions/moves
- `winning` 🏆 - Win condition visualization
- `components` 🧩 - Game pieces and components

### API Contract

**PATCH /api/games/{slug}**
```json
{
  "infographics": {
    "turn_flow": "https://...",
    "setup": "https://...",
    "actions": "https://...",
    "winning": "https://...",
    "components": "https://..."
  }
}
```

Response:
```json
{
  "id": "...",
  "slug": "splendor",
  "infographics": {
    "turn_flow": "https://...",
    ...
  },
  "updated_at": "2026-03-15T..."
}
```

---

## Next Steps

After deployment:

1. **Generate real infographics**: Use `notebooklm-integration` skill for AI-generated images
2. **Bulk migrate games**: Upload infographics for 50+ games
3. **SEO optimization**: Update game metadata with infographics count
4. **Analytics**: Track which infographics are most viewed

---

## Reference

- Skill: `.claude/skills/infographics-deployment/`
- Frontend: `frontend/src/components/game/InfographicsGallery.jsx`
- Backend: `backend/app/models/__init__.py` (GameUpdate)
- Migration: `backend/app/db/migrations/002_add_infographics_column.sql`
- Tests: `tests/test_infographics.py`
