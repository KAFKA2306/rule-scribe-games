# トラブルシューティングガイド

Vercel デプロイと本番環境のデバッグ手順。

---

## 目次

1. [本番環境で「Loading」のまま / 白い画面](#1-本番環境でloadingのまま--白い画面)
2. [静的アセットが HTML として配信される](#2-静的アセットが-html-として配信される)
3. [API エンドポイントが 500 エラー](#3-api-エンドポイントが-500-エラー)
4. [環境変数の確認方法](#4-環境変数の確認方法)
5. [デバッグ手順チェックリスト](#5-デバッグ手順チェックリスト)

---

## 1. 本番環境で「Loading」のまま / 白い画面

### 症状

- トップページにアクセスすると背景色のみ表示
- `#root` div が空
- ゲーム一覧が表示されない

### 原因と解決策

#### 1-1. Supabase 環境変数の未設定

**原因**: `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` が Vercel で未設定の場合、`createClient(undefined, undefined)` がクラッシュし、React アプリ全体が起動しない。

**確認方法**:
```bash
# ブラウザ DevTools Console で確認
# エラーがない場合でも #root が空なら環境変数を疑う
```

**解決策**:
1. Vercel Dashboard → Project → Settings → Environment Variables
2. 以下を **Production** 環境に追加:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. **Redeploy** (キャッシュなし)

#### 1-2. JavaScript ランタイムエラー

**確認方法**:
```javascript
// DevTools Console で確認
// 赤いエラーメッセージを探す
```

**よくあるエラー**:
| エラー | 原因 | 解決策 |
|-------|------|-------|
| `Cannot read properties of null` | 初期化前のオブジェクト参照 | null チェック追加 |
| `Uncaught TypeError` | 型の不一致 | API レスポンス形式を確認 |

---

## 2. 静的アセットが HTML として配信される

### 症状

- Console に `Failed to load module script: Expected a JavaScript module script but the server responded with a MIME type of "text/html"` が表示される
- `/assets/index-XXX.js` にアクセスすると HTML が返る

### 原因

`vercel.json` の rewrite 設定で、静的アセットまで `/index.html` に書き換えられている。

**問題のある設定**:
```json
{
  "rewrites": [
    { "source": "/:path*", "destination": "/index.html" }
  ]
}
```

### 解決策

**正しい `vercel.json`**:
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/index.py"
    }
  ]
}
```

SPA フォールバックは **書かない**。Vercel は `outputDirectory` 内の静的ファイルを自動的に配信する。

---

## 3. API エンドポイントが 500 エラー

### 症状

- `/api/games` が 500 Internal Server Error を返す
- `FUNCTION_INVOCATION_FAILED` が Vercel ログに出る

### 確認手順

```bash
# ブラウザで直接確認
https://bodoge-no-mikata.vercel.app/api/games
```

### よくある原因

| 原因 | 確認方法 | 解決策 |
|------|---------|-------|
| 環境変数未設定 | Vercel Dashboard で確認 | `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` を設定 |
| Python import エラー | Vercel Function Logs を確認 | `api/index.py` のパスを修正 |
| 依存パッケージ不足 | `requirements.txt` を確認 | 必要なパッケージを追加 |

---

## 4. 環境変数の確認方法

### ローカル

```bash
# .env ファイルの存在確認
cat .env

# Vite で使う環境変数 (VITE_ または NEXT_ プレフィックス)
cat frontend/.env
```

### Vercel

1. Dashboard → Project → Settings → Environment Variables
2. **Production / Preview / Development** 環境ごとに設定を確認
3. 変更後は **必ず Redeploy**

### 必要な環境変数一覧

| 変数名 | 用途 | 必須 |
|-------|------|------|
| `GEMINI_API_KEY` | バックエンド LLM 呼び出し | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | バックエンド DB 操作 | ✅ |
| `NEXT_PUBLIC_SUPABASE_URL` | フロントエンド Supabase 接続 | ✅ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | フロントエンド Supabase 認証 | ✅ |

---

## 5. デバッグ手順チェックリスト

本番環境で問題が発生した場合の切り分け手順:

### Step 1: アセット配信の確認

```
□ https://bodoge-no-mikata.vercel.app/ にアクセス
□ DevTools → Network → index-XXX.js の Response Headers を確認
□ Content-Type が application/javascript であること
```

**NG の場合**: `vercel.json` の rewrite を修正

### Step 2: API の確認

```
□ https://bodoge-no-mikata.vercel.app/api/games にアクセス
□ JSON が返ってくること
□ ステータスコードが 200 であること
```

**NG の場合**: バックエンド環境変数と Python コードを確認

### Step 3: フロントエンド初期化の確認

```
□ DevTools → Console でエラーを確認
□ DevTools → Elements → #root の中身を確認
□ #root が空なら JavaScript 初期化でクラッシュしている
```

**NG の場合**: Supabase 環境変数とフロントエンドコードを確認

### Step 4: キャッシュクリア

```
□ Vercel Dashboard → Deployments → Redeploy (キャッシュなし)
□ ブラウザで Ctrl+Shift+R (ハードリロード)
```

---

## 参考: 過去に発生した問題と解決策

### 2024-12-06: React アプリが起動しない

**症状**: `#root` が空、白い画面

**原因**: `createClient(undefined, undefined)` でクラッシュ

**解決策**:
```javascript
// frontend/src/lib/supabase.js
export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null
```

### 2024-12-06: 静的アセットが HTML として配信

**症状**: `Failed to load module script: MIME type of "text/html"`

**原因**: `vercel.json` の SPA fallback rewrite

**解決策**: `/:path*` → `/index.html` の rewrite を削除
