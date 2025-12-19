# Backend Application (`app/`)

`app` ディレクトリは、FastAPIベースのアプリケーションロジックの中核です。

## 概要

このディレクトリには、APIのエンドポイント定義、ビジネスロジック、データベース操作、外部API連携（Gemini, Supabase）など、バックエンドのすべての機能が含まれています。

## ファイル構成

- **[`main.py`](./main.py)**: アプリケーションのエントリーポイント。
    - `FastAPI` インスタンスの作成。
    - CORSミドルウェアの設定。
    - ルーター (`api` prefix) の登録。
    - ヘルスチェックおよびSEO用ページ (`/games/{slug}`) のハンドラ。

- **[`models.py`](./models.py)**: Pydanticモデルによるデータスキーマ定義。
    - `GameDetail`: ゲーム詳細情報のレスポンスモデル（`games` テーブルの構造に対応）。
    - `GameUpdate`: ゲーム更新用リクエストボディ。

## サブディレクトリ

- **[`core/`](./core/README.md)**: アプリケーションの設定、データベースクライアント、AIクライアントなどのコアモジュール。
- **[`routers/`](./routers/README.md)**: APIのエンドポイント（パス操作関数）の定義。
- **[`services/`](./services/README.md)**: ビジネスロジック。ルーティング層とデータベース層の中間に位置し、具体的な処理（検索、AI生成など）を担当。
- **[`prompts/`](./prompts/README.md)**: Geminiへの指示（プロンプト）の管理。
- **[`utils/`](./utils/README.md)**: 汎用ユーティリティ関数。
- **[`scripts/`](../scripts/README.md)**: (参考) データ検証やシード投入などのスクリプトはルートの `app/scripts` ではなく、プロジェクトルートの `scripts` ディレクトリまたは `app` 内に配置されますが、ロジックの一部として機能します。

## 依存関係
- **FastAPI**: Webフレームワーク。
- **Pydantic**: データバリデーション。
- **Supabase**: データベースおよびストレージ。
- **Google Generative AI SDK**: AIモデル連携。
