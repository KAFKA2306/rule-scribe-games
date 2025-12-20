# Skill: Add New Board Game

## Trigger

User requests adding a board game by name.

## Project ID

`wazgoplarevypdfbgeau`

## Workflow

### Step 1: Research (Official Sources Priority)

**1.1 Find Official Page First:**
```
search_web(query: "[game] 公式 ルール")
search_web(query: "[game] publisher official rules")
```

**Priority Sources (in order):**
1. 公式メーカーページ (e.g., arclightgames.jp, newgamesorder.jp, gp-inc.jp, gentosha-edu.co.jp)
2. BoardGameGeek (bgg_url)
3. jellyjellycafe.com, hoobby.net (レビュー・ルール解説)
4. YouTube ルール解説動画

**1.2 Collect Game Info:**
- title (日本語タイトル優先)
- min/max players, play time
- mechanics, theme, components
- key terms (専門用語)
- **詳細ルール** (セットアップ、ゲームの流れ、特殊ルール、勝利条件)

**1.3 Rules Content Target:**
- 600-800文字を目標
- 初心者が読んですぐ遊べる詳しさ
- コンポーネント、セットアップ、ゲームの流れ、勝利条件、ヒントを含む

### Step 2: Insert Data

```sql
INSERT INTO games (slug, title, summary, min_players, max_players, play_time, bgg_url, amazon_url, rules_content, structured_data)
VALUES (
  '[slug]',
  '[title]',
  E'[1行サマリー]',
  [min], [max], [play_time],
  'https://boardgamegeek.com/boardgame/[bgg_id]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22',
  E'[rules_content - see template below]',
  '[structured_data - see template below]'::jsonb
);
```

### Step 3: Generate Image

```
generate_image(Prompt: "[theme] board game artwork, vibrant colors, no text, no title, no words, no letters, pure illustration", ImageName: "[slug]")
```

**Image Guidelines:**
- NO text, titles, keywords, or letters in the image
- Pure visual artwork only (illustrations, symbols, game components)
- Focus on theme and atmosphere, not branding

### Step 4: Process & Update Image

```bash
uv run --with pillow python -c "from PIL import Image; Image.open('[path]').save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)"
```

```sql
UPDATE games SET image_url = '/assets/games/[slug].webp' WHERE slug = '[slug]';
```

### Step 5: Deploy

```bash
git add frontend/public/assets/games/*.webp && git commit -m "feat: add [game]" && git push
```

## rules_content Template

```markdown
## はじめに
[ゲームの概要と魅力 2-3文]

## コンポーネント
- [カード X枚]
- [トークン Y個]
- [ボード]

## セットアップ（[X]分）
1. [手順1]
2. [手順2]
3. [手順3]

## ゲームの流れ
### [フェーズ1]
[詳細説明]

### [フェーズ2]
[詳細説明]

## 勝利条件
[明確な終了条件と勝者の決め方]

## 初心者向けヒント
- [ヒント1]
- [ヒント2]
- [ヒント3]
```

## structured_data Template

```json
{
  "keywords": [
    {"term": "用語1", "description": "説明"},
    {"term": "用語2", "description": "説明"},
    {"term": "用語3", "description": "説明"},
    {"term": "用語4", "description": "説明"},
    {"term": "用語5", "description": "説明"}
  ],
  "key_elements": [
    {"name": "要素1", "type": "component", "reason": "理由"},
    {"name": "要素2", "type": "mechanic", "reason": "理由"},
    {"name": "要素3", "type": "card", "reason": "理由"},
    {"name": "要素4", "type": "token", "reason": "理由"}
  ],
  "mechanics": ["Deck Building", "Trick Taking"],
  "best_player_count": "3-4"
}
```

## Notes

- Image generation is LAST (data first, image later)
- Batch adding: insert all data → generate images together
- keywords: 5-8 important game terms
- key_elements: 4-6 fun components/mechanics
