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

### Step 2: Generate Image
```
generate_image(Prompt: "[theme] board game box art, vibrant colors", ImageName: "[slug]")
```

### Step 3: Process Image
```bash
uv run --with pillow python -c "from PIL import Image; Image.open('[generated_path]').save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)"
```

### Step 4: Insert Data (Enriched Format)
```sql
INSERT INTO games (slug, title, summary, min_players, max_players, play_time, bgg_url, amazon_url, image_url, rules_content, structured_data)
VALUES (
  '[slug]',
  '[title]',
  E'[1行サマリー]',
  [min], [max], [play_time],
  'https://boardgamegeek.com/boardgame/[bgg_id]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22',
  '/assets/games/[slug].webp',
  E'## はじめに\n[ゲーム概要・魅力を2-3文で]\n\n## コンポーネント\n- [内容物リスト]\n\n## セットアップ（[X]分）\n1. [準備手順]\n\n## ゲームの流れ\n### [フェーズ名]\n[詳細な手順]\n\n## 勝利条件\n[明確な終了条件]\n\n## 初心者向けヒント\n- [戦略アドバイス3つ]',
  '{"keywords": [{"term": "...", "description": "..."}], "key_elements": [{"name": "...", "type": "component/mechanic", "reason": "..."}]}'::jsonb
);
```

### Step 5: Deploy
```bash
git add frontend/public/assets/games/*.webp && git commit -m "feat: add [game]" && git push
```

### Step 6: Verify
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
