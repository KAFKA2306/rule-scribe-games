# Routers (`app/routers/`)

`app/routers` は、APIのエンドポイント（URLパスとHTTPメソッド）を定義し、リクエストを受け取って適切なサービス関数を呼び出す層です。

## [`games.py`](./games.py)
ゲーム情報に関するAPIエンドポイントを提供します。

### エンドポイント一覧

#### `GET /api/search`
- **目的**: ゲームの検索（キャッシュ検索のみ）。
- **パラメータ**: `q` (検索クエリ)
- **動作**: `GameService.search_games` を呼び出し、Supabaseからタイトルまたはキーワードに一致するゲームを返します。

#### `POST /api/search`
- **目的**: ゲームの検索および新規生成。
- **ボディ**: `{ "query": "...", "generate": true }`
- **動作**:
    - `generate=true` の場合、検索で見つからなければ `GameService.create_game_from_query` を呼び出し、AIを使用して新規データを作成・保存します。
    - 生成された、または見つかったゲームリストを返します。

#### `GET /api/games`
- **目的**: 最近更新されたゲームの一覧取得。
- **パラメータ**: `limit`, `offset`
- **動作**: トップページのフィードなどで使用されます。

#### `GET /api/games/{slug}`
- **目的**: 個別のゲーム詳細情報の取得。
- **パラメータ**: `slug` (URLフレンドリーなID)
- **動作**: 詳細情報の返却と同時に、`view_count` をインクリメントします。

#### `PATCH /api/games/{slug}`
- **目的**: ゲーム情報の更新または再生成。
- **パラメータ**:
    - `regenerate=true` (Query): AIによる情報の再生成を行います。
    - `fill_missing_only=true` (Query): 再生成時、既存の空フィールドのみを埋め、既存データは上書きしません。
    - Body (JSON): 手動での部分更新用データ。
- **動作**: バックグラウンドでのデータ補完や、管理機能としての手動修正に使用されます。

## 依存関係
- `app.services.game_service.GameService`: ビジネスロジックの実装。
- `app.models`: リクエスト/レスポンスの型定義。
