# Lib (`frontend/src/lib/`)

フロントエンドで使用されるユーティリティ関数やAPIクライアントラッパーです。

## [`api.js`](./api.js)
バックエンドAPIとの通信を抽象化したシンプルなラッパーです。
- **`api.get(path)`**: GETリクエストを送信し、JSONレスポンスを返します。
- **`api.post(path, body)`**: JSONボディを含むPOSTリクエストを送信します。

## [`supabase.js`](./supabase.js)
FrontendからSupabaseへ直接アクセスする場合に使用するクライアント初期化コードです。
- `createClient(SUPABASE_URL, SUPABASE_ANON_KEY)` を使用してインスタンスを作成します。
- **注意**: バックエンドを介さずにデータベースにアクセスする場合（例: リアルタイム購読や認証など）に使用されますが、主要なデータ取得ロジックはバックエンドAPI (`/api/...`) に寄せることが推奨されます。
