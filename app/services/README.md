# Services (`app/services/`)

`app/services` は、アプリケーションのビジネスロジックを集約する層です。ルーターから呼び出され、データベースや外部API（Gemini）と連携して具体的な処理を実行します。

## [`game_service.py`](./game_service.py)
ゲームデータの検索、生成、更新に関する主要なロジックを提供します。

### 主な関数・メソッド

#### `generate_metadata(query: str, context: Optional[str]) -> Dict`
- **役割**: Gemini APIを使用して、ゲームのタイトルから詳細なメタデータ（要約、ルール概要、スペックなど）を生成します。
- **ロジック**:
    1. コンテキスト（既存の検索結果など）がない場合、Supabaseを検索して類似情報を取得し、重複生成を防ぐためのコンテキストとして利用します。
    2. `app.prompts` からプロンプトを取得し、`GeminiClient` に構造化JSONの生成を依頼します。
    3. 生成されたJSONに対し、許可されたフィールドのみをフィルタリングします。
    4. 補助的に `amazon_search_url` などを生成して付与します。

#### `GameService` クラス
- **`search_games`**: 単純なデータベース検索。
- **`create_game_from_query`**: 未登録のゲームが検索された際の処理フロー。`generate_metadata` を呼び出し、結果をSupabaseに `upsert` します。
- **`update_game_content`**: 既存のゲーム情報の再生成。
    - **`fill_missing_only` モード**: 既存のデータ（ユーザーが手動修正したものなど）を保護しつつ、空のフィールド（例: ルール詳細や画像URLのみ欠けている場合）だけをAI生成結果で埋めるマージロジック (`_merge_fields`) が実装されています。

## その他のサービス
- **`seo_renderer.py`**: サーバーサイドでのSEOタグ生成ロジック。OGPタグなどを含むHTMLを動的に構築します。
- **`sitemap.py`**: サイトマップXMLの生成ロジック。全ゲームのSlugを取得してXMLを構築します。

## ロジックのポイント
- **構造化データ**: AI出力は常にJSON形式で受け取り、Pydanticモデルと整合させます。
- **安全なマージ**: AIによる再生成が既存の良質なデータを破壊しないよう、マージ戦略が制御されています。
