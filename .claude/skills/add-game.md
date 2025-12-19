# Skill: Add New Board Game

Add a new board game to the bodoge-no-mikata site.

## When to Use

- User requests adding a new board game
- User provides a game name (Japanese or English)

## Workflow (SEQUENTIAL)

### 1. Research (MUST COMPLETE FIRST)

```
search_web(query: "[game name] ボードゲーム ルール 概要")
```

Gather:
- Title (Japanese + English)
- Theme/visual style (for image)
- Player count, play time, age, year
- Core mechanics
- BGG ID (for link)

### 2. Generate Image (after research)

Use ACTUAL theme from research:
```
generate_image(
  Prompt: "[theme from research], board game box art style, vibrant",
  ImageName: "[slug]"
)
```

### 3. Process Image

```bash
uv run --with pillow python -c "
from PIL import Image
img = Image.open('[source]')
img.save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)
"
```

### 4. Insert to Database

Project ID: `wazgoplarevypdfbgeau`

```sql
INSERT INTO games (
  slug, title, title_ja, summary, description,
  min_players, max_players, play_time, min_age, published_year,
  image_url, rules_content, is_official, structured_data,
  bgg_url, amazon_url
) VALUES (
  '[slug]', '[title_en]', '[title_ja]',
  '[3-line summary]', '[description]',
  [min], [max], [time], [age], [year],
  '/assets/games/[slug].webp',
  E'[DETAILED rules - see format below]',
  true, '[structured_data]'::jsonb,
  'https://boardgamegeek.com/boardgame/[id]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22'
);
```

### 5. Deploy

```bash
git add . && git commit -m "feat: add [game]" && git push
```

### 6. Verify

```
browser_subagent: check https://bodoge-no-mikata.vercel.app/games/[slug]
```

## Rules Content Format (DETAILED)

Must include sections:
```markdown
## 準備
1. [setup steps]

## ゲームの流れ
### [phase name]
- [actions]

## 勝利条件
[how to win]

## 戦略ヒント
- [tips]
```

Minimum 500+ characters. Must be playable for first-time players.

## Data Rules

- `slug`: lowercase, hyphen-separated
- Use `E'...'` for newlines in SQL
- Always add BGG + Amazon links
