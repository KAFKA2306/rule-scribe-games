# Examples: Infographics Deployment

## Example 1: Deploy Infographics for One Game (Splendor)

**Scenario**: You have 5 PNG images for Splendor and want them to display in the carousel.

**Step 1**: Upload images to Cloudinary
```
- splendor-turn-flow.png → https://res.cloudinary.com/.../splendor-turn-flow.png
- splendor-setup.png → https://res.cloudinary.com/.../splendor-setup.png
- splendor-actions.png → https://res.cloudinary.com/.../splendor-actions.png
- splendor-winning.png → https://res.cloudinary.com/.../splendor-winning.png
- splendor-components.png → https://res.cloudinary.com/.../splendor-components.png
```

**Step 2**: PATCH the game record
```bash
curl -X PATCH http://localhost:8000/api/games/splendor \
  -H "Content-Type: application/json" \
  -d '{
    "infographics": {
      "turn_flow": "https://res.cloudinary.com/.../splendor-turn-flow.png",
      "setup": "https://res.cloudinary.com/.../splendor-setup.png",
      "actions": "https://res.cloudinary.com/.../splendor-actions.png",
      "winning": "https://res.cloudinary.com/.../splendor-winning.png",
      "components": "https://res.cloudinary.com/.../splendor-components.png"
    }
  }'

# Response:
# {
#   "id": "...",
#   "slug": "splendor",
#   "infographics": {
#     "turn_flow": "https://...",
#     ...
#   },
#   "updated_at": "2026-03-15T..."
# }
```

**Step 3**: Verify in UI
- Go to `http://localhost:5173/games/splendor`
- Click 📊 図解 tab
- See carousel with 5 images
- Click ← → to navigate

---

## Example 2: Partial Update (Only 2 Infographics)

**Scenario**: You only have setup and actions images ready.

```bash
curl -X PATCH http://localhost:8000/api/games/catan \
  -H "Content-Type: application/json" \
  -d '{
    "infographics": {
      "setup": "https://...",
      "actions": "https://..."
    }
  }'
```

**Result**:
- Tab appears with 2 images only
- Carousel shows "1 / 2", "2 / 2"
- Other keys (turn_flow, winning, components) not present

---

## Example 3: Bulk Upload via Python Script

**Scenario**: Deploy infographics for 10 games at once.

```python
# scripts/deploy_infographics.py
import asyncio
from app.core.supabase import supabase

GAMES_DATA = {
    "splendor": {
        "turn_flow": "https://example.com/splendor-turn-flow.png",
        "setup": "https://example.com/splendor-setup.png",
        "actions": "https://example.com/splendor-actions.png",
        "winning": "https://example.com/splendor-winning.png",
        "components": "https://example.com/splendor-components.png",
    },
    "catan": {
        "setup": "https://example.com/catan-setup.png",
        "actions": "https://example.com/catan-actions.png",
    },
    # ... more games
}

async def deploy_all():
    for slug, infographics in GAMES_DATA.items():
        result = supabase.table("games").update(
            {"infographics": infographics}
        ).eq("slug", slug).execute()
        
        if result.data:
            print(f"✓ {slug}: {len(infographics)} infographics deployed")
        else:
            print(f"✗ {slug}: Update failed")

if __name__ == "__main__":
    asyncio.run(deploy_all())
```

**Run**:
```bash
cd backend
python scripts/deploy_infographics.py
```

---

## Example 4: Fix Missing Database Column

**Scenario**: You get error "Could not find column 'infographics' in games table".

**Action**: Run migration in Supabase
1. Go to `https://app.supabase.com`
2. Select your project
3. SQL Editor → New Query
4. Paste:
```sql
BEGIN;
ALTER TABLE games ADD COLUMN IF NOT EXISTS infographics JSONB;
CREATE INDEX IF NOT EXISTS idx_games_infographics ON games USING gin (infographics);
COMMIT;
```
5. Click "Run"

**Verify**:
```bash
# In Supabase dashboard:
# - Go to Tables → games
# - Scroll right to see new "infographics" column
# - Type should show "jsonb"
```

---

## Example 5: Test Carousel Edge Cases

**Test 1: Missing image URL (404)**
```bash
curl -X PATCH http://localhost:8000/api/games/test-game \
  -d '{
    "infographics": {
      "turn_flow": "https://example.com/nonexistent.png"
    }
  }'
```
- Browser should show: "画像を読み込めませんでした"
- No console errors
- Console shows onError handler triggered

**Test 2: Invalid image URL (malformed)**
```bash
"turn_flow": "not-a-url"
```
- Same error handling as 404
- Graceful UI state

**Test 3: Mixed valid/invalid**
```bash
{
  "turn_flow": "https://valid.com/image.png",
  "setup": "https://invalid-domain/image.png",
  "actions": "https://valid.com/actions.png"
}
```
- Only broken image shows error
- Other 2 navigate normally
- Counter shows "3 total"

---

## Example 6: Deployment to Production

**After local verification**:

```bash
# 1. Commit infographics data
git add backend/app/db/migrations/
git add -A  # Include any game updates
git commit -m "feat: Add infographics for Splendor, Catan, Ticket to Ride"

# 2. Push to main
git push origin main

# 3. Vercel auto-deploys
# Wait 2-3 minutes for build completion

# 4. Test production
curl https://bodoge-no-mikata.vercel.app/api/games/splendor | jq '.infographics'

# Result should show all 5 URLs
```

---

## Example 7: Update CLAUDE.md to Track Infographics Status

After deploying infographics for a game, update the project guide:

```markdown
## Games with Infographics (Deployed)

| Game | Turn Flow | Setup | Actions | Winning | Components | Last Updated |
|------|-----------|-------|---------|---------|------------|--------------|
| Splendor | ✓ | ✓ | ✓ | ✓ | ✓ | 2026-03-15 |
| Catan | ✗ | ✓ | ✓ | ✗ | ✗ | 2026-03-15 |
```

This helps the team track coverage and plan generation priorities.
