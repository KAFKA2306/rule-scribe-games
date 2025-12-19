# Bodoge-no-Mikata Skills

## Constants
- **Project ID**: `wazgoplarevypdfbgeau`
- **Affiliate Tag**: `bodogemikata-22`
- **Production**: https://bodoge-no-mikata.vercel.app

## Essential Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `add-game` | "add [game]" | research → image → insert → deploy |
| `fix-data` | "fix [issue]" | diagnose → update → verify |
| `deploy` | "deploy" | git push → verify production |

## rules_content Standard Format
```
## はじめに
[ゲーム概要]

## コンポーネント
[内容物]

## セットアップ（[X]分）
[準備手順]

## ゲームの流れ
[ステップ別説明]

## 勝利条件
[終了条件]

## 初心者向けヒント
[戦略アドバイス]
```

## Database Schema (games)
| Column | Type | Description |
|--------|------|-------------|
| slug | text | URL識別子 |
| title | text | ゲーム名 |
| summary | text | 1行要約 |
| min_players | int | 最小人数 |
| max_players | int | 最大人数 |
| play_time | int | プレイ時間(分) |
| rules_content | text | ルール説明 |
| image_url | text | 画像パス |
| bgg_url | text | BoardGameGeek URL |
| amazon_url | text | Amazonアフィリエイト |
| structured_data | jsonb | SEO用キーワード |
