# Skill: Add New Board Game

## Trigger

User requests adding a board game by name.

## Project ID

`wazgoplarevypdfbgeau`

## Workflow

### Step 1: Find Official Page FIRST

**1.1 Search for Official Page:**

```text
search_web(query: "[game] 日本語版 公式")
search_web(query: "[game] BoardGameGeek")
```

**1.2 Set official_url:**

- Find the official publisher/distributor page
- If no official Japanese page exists, set to NULL

**1.3 Collect Rules (600-800 chars):**

- web search again for "[game] rules"
- コンポーネント
- セットアップ手順
- ゲームの流れ
- 勝利条件
- 初心者ヒント

### Step 2: Insert Data

```sql
INSERT INTO games (slug, title, summary, min_players, max_players, play_time, official_url, bgg_url, amazon_url, rules_content, structured_data)
VALUES (
  '[slug]',
  '[title]',
  E'[1行サマリー]',
  [min], [max], [play_time],
  '[official_url or NULL]',
  'https://boardgamegeek.com/boardgame/[bgg_id]/[name]',
  'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22',
  E'[rules_content]',
  '[structured_data]'::jsonb
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

## 💎 ゲームの目的
[2-3文で概要とテーマを説明]
**[勝利条件]** を満たしたプレイヤーの勝利です。

## 📦 セットアップ

### 1. [コンポーネント名]
- **[サブ項目]**: [説明]
- **[サブ項目]**: [説明]

### 2. [コンポーネント名]
[プレイ人数などによる分岐がある場合は箇条書きで明確に]
- 4人プレイ: X個
- 3人プレイ: Y個

---

## 🔄 ゲームの流れ
[ゲームの進行形式に合わせて適切な構造を選択してください]

### パターンA: 手番制（アクション選択）
手番プレイヤーは、以下の **[数字]つのアクションから1つだけ** を選び実行します。

#### A. [アクション名]
- [詳細な手順]
- **注意**: [重要な制限事項]

#### B. [アクション名]
- [詳細な手順]

### パターンB: フェーズ制
ラウンドごとに以下のフェーズを順番に行います。

#### 1. [フェーズ名]
- [全員同時に行う処理など]

#### 2. [フェーズ名]
- [スタートプレイヤーから順に行う処理など]

---

## ⚠️ 重要なルール
[間違いやすいルールや制約を個別にピックアップ]

### [ルール名]
[説明]

## 🏆 ゲームの終了
[終了フラグの条件]
[最終的な勝敗判定方法]
- 同点の場合：[タイブレーク条件]

## 🛠 初心者向けヒント (Essential)
[必ず含めること]
- **[コツ1]**: [アドバイス]
- **[もっと楽しむために]**: [アドバイス]

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
