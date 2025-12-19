# Skill: Add New Board Game

## Trigger
User requests adding a board game by name.

## Project ID
`wazgoplarevypdfbgeau`

## Workflow

### Step 1: Research
```
search_web(query: "[game] ボードゲーム ルール 遊び方")
```
Required info: title_ja, player count, play time, mechanics, theme.

### Step 2: Generate Image
```
generate_image(Prompt: "[theme from research] board game box art, vibrant colors", ImageName: "[slug]")
```

### Step 3: Process Image
```bash
uv run --with pillow python -c "from PIL import Image; Image.open('[generated_path]').save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)"
```

### Step 4: Insert Data
```sql
INSERT INTO games (slug, title, title_ja, summary, rules_content, structured_data, bgg_url, amazon_url, image_url)
VALUES (
  '[slug]',
  '[title]',
  '[title_ja]',
  E'[3行要約]',
  E'## 準備\n[内容]\n\n## ゲームの流れ\n[内容]\n\n## 勝利条件\n[内容]\n\n## 戦略ヒント\n[内容]',
  '{"keywords": [{"term": "...", "description": "..."}], "key_elements": [{"name": "...", "type": "component/mechanic", "reason": "..."}]}'::jsonb,
  'https://boardgamegeek.com/boardgame/[bgg_id]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22',
  '/assets/games/[slug].webp'
);
```

### Step 5: Deploy
```bash
git add . && git commit -m "feat: add [game]" && git push
```

### Step 6: Verify
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug] → Ctrl+Shift+R → screenshot
