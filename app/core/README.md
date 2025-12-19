# Core Module (`app/core/`)

`app/core` は、アプリケーション全体で共有される設定やシングルトンインスタンスを管理します。

## 構成ファイル

### [`settings.py`](./settings.py)
アプリケーションの設定と環境変数のロードを担当します。
- `Settings` クラス: 環境変数 (`GEMINI_API_KEY`, `SUPABASE_URL` 等) を読み込み、検証します。
- `CANONICAL_GEMINI_MODEL`: 使用するGeminiモデル名（`models/gemini-3-flash-preview`）を厳格に定義しています。config.yamlまたは環境変数で異なるモデルが指定された場合、エラーを発生させて意図しないモデル利用を防ぎます。
- `_config`: プロジェクトルートの `config.yaml` をロードします。

### [`gemini.py`](./gemini.py)
Google Gemini API との通信を行うクライアントラッパーです。
- シングルトンとして管理されることが推奨されます。
- `generate_structured_json`: プロンプトを受け取り、Geminiから構造化されたJSONレスポンスを取得します。

### [`supabase.py`](./supabase.py)
Supabase (PostgreSQL) との非同期通信を担当します。
- `games` テーブルへのCRUD操作（検索、取得、更新、作成）を抽象化しています。
- RPC呼び出しやフィルタリングロジックを含みます。

### [`logger.py`](./logger.py)
アプリケーションのロギング設定を行います。
- ログレベルやフォーマットの統一を管理します。

## 設計思想
- **Fail Fast**: 設定の不備（必須環境変数の欠落や誤ったモデル名など）がある場合、アプリケーション起動時に即座に例外を発生させ、不安定な状態での稼働を防ぎます。
- **Singleton**: データベース接続やAPIクライアントは、リクエストごとに生成せず再利用することでパフォーマンスを最適化します。
