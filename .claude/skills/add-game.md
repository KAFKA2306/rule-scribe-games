# Skill: Add New Board Game

## Trigger
User requests adding a board game by name.

## Workflow (STRICT ORDER)

### Step 1: Research FIRST
```
search_web(query: "[game] ボードゲーム ルール 詳細")
```
Get: title_ja, theme, player count, mechanics, BGG ID.

**STOP. DO NOT generate image until research complete.**

### Step 2: Generate Image
Use researched theme:
```
generate_image(Prompt: "[actual theme], box art", ImageName: "[slug]")
```

### Step 3: Process Image
```bash
uv run --with pillow python -c "from PIL import Image; Image.open('[src]').save('frontend/public/assets/games/[slug].webp', 'WEBP', quality=90)"
```

### Step 4: Insert Data
Project: `wazgoplarevypdfbgeau`

Required fields:
- `slug`: lowercase-hyphen
- `title`, `title_ja`
- `summary`: 3行で要約
- `rules_content`: 500+文字、準備/流れ/勝利条件を含む（E''使用）
- `structured_data`: keywords + key_elements
- `bgg_url`, `amazon_url`

### Step 5: Deploy
```bash
git add . && git commit -m "feat: add [game]" && git push
```

### Step 6: Verify
browser_subagent → hard refresh → screenshot

## Rules Content Template
```
## 準備
[セットアップ手順]

## ゲームの流れ
[ターン構造、アクション]

## 勝利条件
[勝ち方]

## 戦略ヒント
[初心者向けアドバイス]
```

## structured_data Template
```json
{
  "keywords": [{"term": "...", "description": "..."}],
  "key_elements": [{"name": "...", "type": "...", "reason": "..."}]
}
```
