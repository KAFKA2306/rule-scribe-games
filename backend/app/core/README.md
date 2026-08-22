# Core Module (`app/core/`)

`app/core` は、アプリケーション全体で共有するruntime設定とデータアクセス基盤を管理します。

## 現行構成

- `settings.py`: `.env` を読み、server-side Supabase接続に必要な設定だけを保持します。
- `supabase.py`: PostgreSQL/Supabaseへのcanonical catalog read/writeを提供します。
- `local_db.py`: Supabase未設定時のローカル開発用データストアです。
- `logger.py`: logging設定です。
- `task_manager.py`: runtime task状態の管理です。
- `rate_limiter.py`: rate-limitが必要なendpoint向けの共通実装です。

## 境界

ゲーム内容をLLMで生成してcatalogへ書くruntime経路はありません。ゲーム固有のsource-backed変更は `data/curated-games/<slug>.json` とcurated-game workflowを正準入口にします。

Backendのproduction DB接続は `SUPABASE_SERVICE_ROLE_KEY` を要求し、browser-safe keyへfallbackしません。
