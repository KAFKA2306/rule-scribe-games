# API

Vercel サーバーレス関数エントリポイント。

## ファイル

| ファイル | 役割 |
|---------|------|
| `index.py` | FastAPI アプリケーションのエクスポート |

## 動作

Vercel は `api/index.py` の `app` オブジェクトを自動検出し、`/api/*` へのリクエストを処理する。

```
Vercel Request → api/index.py → app.main.app
```
