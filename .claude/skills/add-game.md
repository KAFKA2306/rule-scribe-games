# Skill: Add New Board Game

Add a new board game to the bodoge-no-mikata site with AI-generated content and images.

## When to Use
- User requests adding a new board game
- User provides a game name (Japanese or English)
- User wants to populate the database with game data

## Workflow

### 1. Research Game
- Search web for the game's official information
- Gather: title (Japanese/English), player count, play time, age, published year
- Understand core mechanics and rules

### 2. Generate Image
```
generate_image(
  Prompt: "[Game name] board game box art style, [key visual elements], vibrant colors, title [Game name]",
  ImageName: "[slug]"
)
```

### 3. Process Image
Convert PNG to WebP and move to assets:
```bash
uv run --with pillow python -c "
from PIL import Image
img = Image.open('[source_path]')
img.save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)
"
```

### 4. Insert to Database
Use `mcp_execute_sql` with project_id `wazgoplarevypdfbgeau`:
```sql
INSERT INTO games (
    slug, title, title_ja, summary, description,
    min_players, max_players, play_time, min_age, published_year,
    image_url, structured_data, rules_content, is_official
) VALUES (
    '[slug]', '[title_en]', '[title_ja]',
    '[3-line summary in Japanese]',
    '[detailed description in Japanese]',
    [min], [max], [time], [age], [year],
    '/assets/games/[slug].webp',
    '{"keywords": [...], "key_elements": [...]}'::jsonb,
    '[markdown rules content]',
    true
);
```

### 5. Deploy
```bash
git add . && git commit -m "Add game: [title]" && git push
```

### 6. Verify
Use browser_subagent to check `https://bodoge-no-mikata.vercel.app/games/[slug]`

## Data Format Rules
- `slug`: lowercase, hyphen-separated (e.g., `yokohama-duel`)
- `rules_content`: Use actual newlines, NOT escaped `\n`
- `structured_data`: Must include `keywords` and `key_elements` arrays
- All text content in Japanese
