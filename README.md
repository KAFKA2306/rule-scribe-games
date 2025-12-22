# RuleScribe Games

![ボドゲのミカタ](assets/02_ボドゲのミカタ.jpg)

[![Vercel](https://therealsujitk-vercel-badge.vercel.app/?app=rule-scribe-games)](https://rule-scribe-games.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![React](https://img.shields.io/badge/react-18.x-61dafb.svg)](https://reactjs.org/)

**AI駆動ボードゲームルール要約 & Wiki — 「世界中のボードゲームのルールを、瞬時に正確に日本語で」。**

---

## 📖 目次

- [RuleScribe Games](#rulescribe-games)
  - [📖 目次](#-目次)
  - [プロジェクト概要](#プロジェクト概要)
    - [主な機能](#主な機能)
  - [アーキテクチャ](#アーキテクチャ)
  - [ディレクトリ構成](#ディレクトリ構成)
  - [環境構築](#環境構築)
    - [前提条件](#前提条件)
    - [セットアップ手順 (3 Steps)](#セットアップ手順-3-steps)
  - [開発ガイド](#開発ガイド)
  - [API仕様](#api仕様)
  - [トラブルシューティング](#トラブルシューティング)

---

## プロジェクト概要

本プロジェクトは、Gemini Pro/Flashを活用してボードゲームのルールを検索・要約し、日本語で提供するWebアプリケーションです。

### 主な機能
- **AI検索 & 要約**: ユーザーの検索クエリに対し、まずSupabase上のキャッシュを確認。存在しない場合はGemini (`models/gemini-3-flash-preview`) を呼び出し、高精度な日本語要約を生成します。
- **構造化データ**: ルールを「準備」「ゲームプレイ」「終了条件」に構造化し、キーワードや外部リンク（公式サイト、BGG、Amazon等）と合わせて提示します。
- **ハイブリッドキャッシュ**: 生成結果はSupabaseに保存され、次回のアクセスを高速化します。
- **モダンなUI**: React/Viteによるレスポンシブなインターフェース。

## アーキテクチャ

システムは以下の技術スタックで構成されています。

- **Frontend**: React 18 + Vite + Vanilla CSS (CSS Variables活用)。`frontend/` 配下。
- **Backend API**: FastAPI。`app/` 配下に実装され、Vercel Serverless Functionとして動作。
- **Database**: Supabase (PostgreSQL)。`games` テーブルに要約データを格納。
- **AI Model**: Google Gemini 3 Flash Preview。
- **Deploy**: Vercel (Frontend & Backend Serverless)。

### パフォーマンス最適化

- **画像**: 全PNG→WebP変換（98%削減）、`loading="lazy"`
- **バンドル分割**: React.lazy + manualChunks（vendor/supabase/markdown）
- **初期ロード**: 525KB→39KB (92%削減)

## ディレクトリ構成

各ディレクトリの詳細な役割とロジックについては、それぞれのREADMEを参照してください。

- **[`api/`](./api/README.md)**: Vercel Serverless Functionのエントリーポイント。
- **[`app/`](./app/README.md)**: FastAPIバックエンドのアプリケーションロジック。
    - [`app/core`](./app/core/README.md): 設定、シングルトンインスタンス。
    - [`app/routers`](./app/routers/README.md): APIエンドポイント定義。
    - [`app/services`](./app/services/README.md): ビジネスロジック、AI連携。
- **[`frontend/`](./frontend/README.md)**: Reactフロントエンドアプリケーション。
    - [`frontend/src`](./frontend/src/README.md): ソースコード詳細。
- **[`scripts/`](./scripts/README.md)**: 運用・保守用スクリプト。
- **[`tests/`](./tests/README.md)**: テストコード。
- **[`docs/`](./docs/README.md)**: プロジェクトドキュメント。
    - [`NOTE_STRATEGY.md`](./docs/NOTE_STRATEGY.md): Note.com運用戦略・プロフィール設定。
    - [`SEO.md`](./docs/SEO.md): SEO戦略。
    - [`CONTENT_GUIDELINES.md`](./docs/CONTENT_GUIDELINES.md): コンテンツガイドライン。

## 環境構築

### 前提条件
- Python 3.11+
- Node.js 18+
- Supabase プロジェクト (URL, keys)
- Google Gemini API Key
- `uv` (Python package manager) および `task` (Taskfile)

### セットアップ手順 (3 Steps)

1. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .env を編集し、GEMINI_API_KEY, SUPABASE_URL などを設定
   ```

2. **依存関係のインストール**
   ```bash
   task setup  # uv sync と npm install を実行
   ```

3. **開発サーバーの起動**
   ```bash
   task dev    # Backend(:8000) と Frontend(:5173) を同時起動
   ```

## 開発ガイド

Taskfileにより、主要な開発コマンドが標準化されています。

- `task dev`: 開発サーバー起動（ホットリロード有効）。
- `task lint`: コードフォーマットと静的解析 (Ruff, Prettier, ESLint)。
- `task build`: フロントエンドのプロダクションビルド。
- `task gemini:verify`: Geminiモデルの動作確認。

## API仕様

主要なエンドポイントは以下の通りです。詳細はコードおよびSwagger UI (`/docs` - ローカル起動時) を参照してください。

- `GET /api/health`: サーバー稼働確認。
- `GET /api/games`: ゲーム一覧取得。
- `GET /api/games/{slug}`: ゲーム詳細取得。
- `POST /api/search`: ゲーム検索およびAI生成トリガー。
    - Body: `{ "query": "カタン", "generate": true }`

## トラブルシューティング

- **Gemini 401/404**: `.env` の `GEMINI_API_KEY` が正しいか確認してください。
- **Supabase 401/403**: RLSポリシーまたはAPIキー (`SUPABASE_SERVICE_ROLE_KEY`) を確認してください。
- **画面が真っ白**: フロントエンドの依存関係 (`npm install`) や環境変数 (`NEXT_PUBLIC_...`) を確認してください。

---

## 🤖 Claude Skills (AI ワークフロー自動化)

本プロジェクトでは、AIアシスタントが自動的に参照・実行するスキル定義を `.claude/skills/` に配置しています。

### 利用可能なスキル

| スキル | 説明 |
|--------|------|
| `add-game` | 新規ボードゲームの追加（画像生成・DB登録） |
| `deploy` | Git コミット・プッシュ・Vercel デプロイ検証 |
| `fix-data` | データベースコンテンツの修正（エスケープ・フォーマット） |
| `search-verify` | ゲーム情報の検索・サイトコンテンツの検証 |

### スキルの動作

- **起動方式**: モデル起動（AIがリクエストを分析して自動判断）
- **配置場所**: `.claude/skills/[skill-name].md`
- **トリガー**: リクエスト内容とスキルの "When to Use" セクションをマッチング

---

**License**: MIT © RuleScribe Games contributors
