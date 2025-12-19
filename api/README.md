# API Directory (`api/`)

このディレクトリは、Vercel Serverless Functionのエントリーポイントを含んでいます。

## 概要

`api` ディレクトリは、Vercelがデプロイ時にPythonのサーバーレス関数として認識・実行するためのエントリーポイントを提供することを唯一の目的としています。実際のアプリケーションロジックはここには含まれず、すべて `../app` ディレクトリ内のFastAPIアプリケーションからインポートされます。

## ファイル構成

### `index.py`
VercelのPythonランタイムのエントリーポイントです。

- **役割**:
  1. プロジェクトルートを `sys.path` に追加し、`app` モジュールへのパスを通します。
  2. `app.main` からFastAPIのインスタンス `app` をインポートし、Vercelに公開します。

- **コードの構造**:
  ```python
  import sys
  import os

  # プロジェクトルートをパスに追加（モジュール解決のため）
  root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  sys.path.append(root_path)

  # FastAPIインスタンスをインポート
  from app.main import app
  ```

## デプロイ設定 (vercel.json)

このディレクトリの扱いは `vercel.json` によって制御されます。通常、以下のような設定により、`/api/*` へのリクエストがこの `index.py` にルーティングされます。

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" }
  ]
}
```
