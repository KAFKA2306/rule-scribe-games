# Skill: Add New Board Game

## Trigger
User requests adding a board game by name.

## Project ID
`wazgoplarevypdfbgeau`

## Workflow

### Step 1: Research
```
search_web(query: "[game] ボードゲーム ルール 遊び方 プレイ人数")
```
Required info: title_ja, min/max players, play time, mechanics, theme, components.

### Step 2: Insert Data (without image)
```sql
INSERT INTO games (slug, title, summary, min_players, max_players, play_time, bgg_url, amazon_url, rules_content, structured_data)
VALUES (
  '[slug]',
  '[title]',
  E'[1行サマリー]',
  [min], [max], [play_time],
  'https://boardgamegeek.com/boardgame/[bgg_id]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22',
  E'## はじめに\n[概要]\n\n## コンポーネント\n[内容物]\n\n## セットアップ（[X]分）\n[手順]\n\n## ゲームの流れ\n[詳細]\n\n## 勝利条件\n[条件]\n\n## 初心者向けヒント\n[アドバイス]',
  '{"keywords": [{"term": "用語1", "description": "説明"}, {"term": "用語2", "description": "説明"}, {"term": "用語3", "description": "説明"}, {"term": "用語4", "description": "説明"}, {"term": "用語5", "description": "説明"}], "key_elements": [{"name": "要素1", "type": "component", "reason": "理由"}, {"name": "要素2", "type": "mechanic", "reason": "理由"}, {"name": "要素3", "type": "component", "reason": "理由"}, {"name": "要素4", "type": "mechanic", "reason": "理由"}]}'::jsonb
);
```

### Step 3: Generate Image
```
generate_image(Prompt: "[theme] board game box art, vibrant colors", ImageName: "[slug]")
```

### Step 4: Process Image
```bash
uv run --with pillow python -c "from PIL import Image; Image.open('[generated_path]').save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)"
```

### Step 5: Update Image URL
```sql
UPDATE games SET image_url = '/assets/games/[slug].webp' WHERE slug = '[slug]';
```

### Step 6: Deploy
```bash
git add frontend/public/assets/games/*.webp && git commit -m "feat: add [game]" && git push
```

### Step 7: Verify
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug]

## rules_content Template
```
## はじめに
[ゲームの概要と魅力]

## コンポーネント
- [カード/ボード/トークン等]

## セットアップ（[X]分）
1. [手順1]
2. [手順2]

## ゲームの流れ
### [フェーズ1名]
[詳細説明]

### [フェーズ2名]
[詳細説明]

## 勝利条件
[明確な条件]

## 初心者向けヒント
- [ヒント1]
- [ヒント2]
- [ヒント3]
```

## Notes
- Image generation is done LAST to ensure data is ready first
- If image fails, game data is still available (just without image)
- Batch adding: insert all data first, then generate images together
