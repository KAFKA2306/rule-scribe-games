# Bodoge-no-Mikata Skills

## Constants

- **Project ID**: `wazgoplarevypdfbgeau`
- **Affiliate Tag**: `bodogemikata-22`
- **Production**: <https://bodoge-no-mikata.vercel.app>

## Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `add-game` | "add [game]" | research → insert → image → deploy |
| `fix-data` | "fix [issue]" | diagnose → update → verify |
| `deploy` | "deploy" | git push → verify |

## Content Guidelines

### rules_content (600-800 chars)

```markdown
## はじめに
## コンポーネント
## セットアップ（X分）
## ゲームの流れ
## 勝利条件
## 初心者向けヒント
```

### structured_data

| Field | Count | Description |
|-------|-------|-------------|
| keywords | 5-8 | 専門用語・ルール名 |
| key_elements | 4-6 | カード・トークン・メカニクス |
| mechanics | 2-4 | BGG風ジャンル名 |
| best_player_count | 1 | おすすめ人数 |

## Database Schema

| Column | Type | Notes |
|--------|------|-------|
| slug | text | URL識別子 |
| title | text | ゲーム名 |
| summary | text | 1行要約 |
| min_players | int | 最小人数 |
| max_players | int | 最大人数 |
| play_time | int | 分 |
| rules_content | text | ルール説明 |
| structured_data | jsonb | keywords + key_elements |
| image_url | text | /assets/games/[slug].webp |
| bgg_url | text | BoardGameGeek |
| amazon_url | text | アフィリエイト |

## Quality Targets

- rules_content: 600-800 characters
- keywords: 5-8 items
- key_elements: 4-6 items
- First-time player can understand and play
