# ボドゲのミカタ (Bodoge no Mikata) - 完全統合マスターガイド

> **重要な免責事項**: このドキュメントは、プロジェクトの**唯一の真実（Single Source of Truth）**です。コードや設定に関する疑問が生じた場合、まずここを参照してください。このファイルは、プロジェクトの「ロジック」「設定」「スキーマ」「ユーザー体験」「コーディングスタイル」「デプロイ」のすべてを網羅しています。

---

## 1. プロジェクト憲章 (Project Charter)

### 1.1 サービス名
*   **日本語**: ボドゲのミカタ
*   **英語 (Repo)**: RuleScribe Games
*   **略称**: Bodoge no Mikata / RSG

### 1.2 コアコンセプト & 哲学 (Core Concepts & Philosophy)

1.  **Living Wiki (生きているWiki)**
    *   静的なデータベースではありません。ユーザーが「知らないゲーム」を検索した瞬間、AIが世界中から情報を収集し、Wikiページをリアルタイムで生成します。
    *   **自己進化**: 検索されるたびにデータベースが成長し、次回以降のユーザーはその恩恵（高速表示）を受けます。

2.  **Minimal Code & High Speed (最小コード・最高速度)**
    *   **"No Boilerplate"**: 不要なレイヤー（複雑なORMラッパー、過剰な抽象化）を排除します。
    *   **Direct & Raw**: Supabaseへのアクセスはシンプルに保ち、AIのプロンプトも直感的です。
    *   **Destructive Reconstruction**: 過去のレガシーコード (`backend-v2` 等) はすべて削除されました。現在の `backend/` と `frontend/` が全てです。

3.  **Modern & Cool UI (モダンでクールなUI)**
    *   **Dark Mode First**: ボードゲームの夜会をイメージした、ダークテーマ基調のデザイン。
    *   **Neon Accents**: `Zen Maru Gothic` (丸ゴシック) と `Space Grotesk` を組み合わせ、未来的かつ親しみやすい印象。
    *   **User Centric**: 専門用語を避け、「セットアップ」「勝ち方」など、初心者が知りたい情報にフォーカスします。

### 1.3 ターゲットユーザー
*   **インスト時間を短縮したいゲーマー**: 説明書を読むのが苦手、または時間がない人。
*   **輸入ゲーム愛好家**: 英語やドイツ語のルールブックしか手元になく、日本語の要約が欲しい人。
*   **プレイ中の確認**: 「このカードの効果なんだっけ？」を瞬時に解決したいプレイヤー。

---

## 2. システムアーキテクチャ (System Architecture)

### 2.1 全体構成図 (Overview Diagram)
```mermaid
graph TD
    subgraph Client [User Environment]
        Browser[Web Browser]
    end

    subgraph Vercel [Vercel Platform]
        CDN[Edge Network / CDN]
        FE[Static Frontend (React/Vite)]
        BE[Serverless Function (Python/FastAPI)]
    end

    subgraph External [External Services]
        Supabase[(Supabase PostgreSQL)]
        Gemini[Google Gemini 2.5 Flash]
    end

    Browser --> |HTTPS| CDN
    CDN --> |/| FE
    CDN --> |/api/*| BE

    BE --> |Read/Write| Supabase
    BE --> |Generate| Gemini
    Gemini --> |Grounding (Search)| Internet[World Wide Web]
```

### 2.2 ディレクトリ構造 (Directory Structure)
```text
.
├── backend/                # Python FastAPI Application
│   ├── app/
│   │   ├── core/           # Config, DB Connection
│   │   ├── routers/        # API Endpoints (search, games)
│   │   ├── services/       # External Logic (Gemini)
│   │   └── main.py         # App Entry Point
│   ├── init_db.sql         # Database Schema Definition
│   └── pyproject.toml      # Backend Dependencies (uv)
├── frontend/               # React Vite Application
│   ├── src/
│   │   ├── components/     # (Minimal usage, mostly in pages)
│   │   ├── pages/          # Route Components
│   │   ├── App.jsx         # Main Logic & Layout
│   │   └── index.css       # Global Styles & Tailwind
│   └── package.json        # Frontend Dependencies
├── api/                    # Vercel Serverless Entry Point
│   └── index.py            # Python Path Shim
└── vercel.json             # Deployment Configuration
```

---

## 3. データベース詳細 (Database Schema)

**Platform**: Supabase (PostgreSQL)

### 3.1 テーブル定義 (`games`)
`backend/init_db.sql` に基づく正確な定義です。

```sql
-- pgvector拡張 (将来的なベクトル検索用)
create extension if not exists vector;

create table if not exists games (
  id bigint primary key generated always as identity,
  title text not null,              -- ゲームタイトル (日/英)
  description text,                 -- 短い概要
  rules_content text,               -- 詳細ルール (Markdown)
  source_url text unique,           -- 情報源URL (重複排除キー)
  image_url text,                   -- 画像URL
  structured_data jsonb,            -- 構造化データ (後述)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### 3.2 トリガー (Triggers)
更新日時を自動更新するためのトリガーが設定されています。

```sql
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_games_updated_at
before update on games
for each row
execute function update_updated_at_column();
```

### 3.3 `structured_data` (JSONB) スキーマ
AIによって生成され、JSONBカラムに格納されるオブジェクトの構造です。

```json
{
  "keywords": [
    { "term": "ワーカープレイスメント", "description": "駒を置いてアクションを実行する仕組み" }
  ],
  "popular_cards": [
    { "name": "騎士", "type": "発展カード", "cost": "羊1鉄1麦1", "reason": "盗賊を移動できるため強力" }
  ]
}
```

---

## 4. AI & ロジック詳細 (AI Logic & Prompts)

**Model**: Google Gemini 2.5 Flash
**Library**: `google-generativeai` via `GeminiClient`

### 4.1 プロンプト設計 (Prompt Design)
`backend/app/services/gemini_client.py` で定義されている実際のプロンプトです。Geminiはこの指示に従い、ウェブ検索結果をJSONに変換します。

```text
User Query: '{query}'

Task: Search for official board game info or update existing game data based on the query.
If the query implies updating (e.g. 'add card list', 'update rules'), find the game and apply changes.
Prioritize official/BGG sources.

Return JSON:
- title: Unique name (English+Japanese e.g. 'Catan (カタン)').
- description: Japanese summary.
- rules_content: Detailed Japanese rules (Setup, Flow, Victory) as Markdown.
- image_url: Official image URL.
- structured_data: JSON object with:
  - keywords: List of {term, description} (key mechanics/terms).
  - popular_cards: List of {name, type, cost, reason} (key cards/components).
```

### 4.2 エラーハンドリング (Fallbacks)
1.  **Mock Mode**: 環境変数 (`SUPABASE_URL` 等) が不足している場合、`app.core.supabase` は `NoopGameRepository` に切り替わり、エラーで落ちるのではなく「空の結果」を返すことで起動を維持します。
2.  **Gemini Failures**: API制限やタイムアウトの場合、`search.py` はエラーをログ出力し、空リストを返します。フロントエンドはこれを「結果なし」として扱います。

---

## 5. API仕様書 (API Specification)

すべてのAPIは `FastAPI` によって提供され、`/api` プレフィックスを持ちます。

### 5.1 POST `/api/search`
検索と生成のメインエンドポイント。

**Request**:
```json
{
  "query": "カタン"
}
```

**Response (List[SearchResult])**:
```json
[
  {
    "id": 123,
    "slug": "catan",
    "title": "Catan (カタン)",
    "description": "無人島を開拓する...",
    "rules_content": "**セットアップ**: ...",
    "image_url": "https://...",
    "source_url": "https://boardgamegeek.com/...",
    "structured_data": { ... }
  }
]
```

### 5.2 GET `/api/games`
最近更新されたゲームの一覧を取得。

**Parameters**: `limit` (default: 100)

### 5.3 GET `/api/games/{slug}`
特定のゲーム詳細を取得。Slug または ID でアクセス可能。

---

## 6. フロントエンド詳細 (Frontend Details)

**Framework**: React 18 + Vite
**Styling**: CSS Modules (Variables) + Utility Classes

### 6.1 状態管理 (State Management)
`frontend/src/App.jsx` 内で管理される主要な State です。

| State名 | 型 | 説明 |
| :--- | :--- | :--- |
| `games` | `Array` | 現在表示中のゲームリスト（検索結果または初期リスト）。 |
| `initialGames` | `Array` | 起動時に読み込んだ「最近のゲーム」キャッシュ。検索クリア時に復帰するために保持。 |
| `selectedSlug` | `String` | 現在右ペインに詳細を表示しているゲームのSlug。 |
| `loading` | `Boolean` | API通信中のローディング表示フラグ。 |
| `query` | `String` | 検索窓の入力値。 |

### 6.2 デザインシステム (Design System)
`frontend/src/index.css` で定義された CSS 変数を使用します。

*   **Colors**:
    *   `--bg-dark`: `#0b1221` (メイン背景)
    *   `--accent`: `#4ef0c7` (ミントグリーン的なアクセント)
    *   `--text-main`: `#eef2ff` (白に近い青白)
*   **Fonts**:
    *   `Zen Maru Gothic`: 親しみやすさのための丸ゴシック。
    *   `Space Grotesk`: タイトルや英語部分に使用する未来的フォント。

---

## 7. 開発・デプロイガイド (Development & Deployment)

### 7.1 ローカル開発環境の構築

**依存関係バージョン (Dependencies)**:
*   **Python**: `3.11+` (Requires `uv`)
*   **Node.js**: `18+` (Requires `npm`)
*   **Libraries**:
    *   Backend: `fastapi>=0.123.0`, `google-generativeai>=0.8.5`, `supabase>=2.24.0`
    *   Frontend: `react^18.2.0`, `react-markdown^10.1.0`

**セットアップ手順**:
```bash
# 1. Clone
git clone <repo>
cd rule-scribe-games

# 2. Env Vars
cp .env.example .env
# .env に SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY を設定

# 3. Install
task setup
# (内部で `cd backend && uv sync` と `cd frontend && npm install` を実行)

# 4. Run
task dev
```

### 7.2 Vercel デプロイの仕組み
`vercel.json` によるハイブリッド構成です。

1.  **Frontend**: `@vercel/static-build` を使用し、`frontend/package.json` のビルドコマンドを実行。`dist` ディレクトリが配信されます。
2.  **Backend**: `@vercel/python` を使用。`api/index.py` がエントリーポイントとなり、ここから `backend/app/main.py` を呼び出します。
    *   **重要**: Vercel上ではファイル構造がフラット化される場合があるため、`sys.path.append` でパスを調整しています。

### 7.3 コーディング規約 (Coding Standards)

**General**:
*   **KISS (Keep It Simple, Stupid)**: 複雑な継承や過剰な分割を避ける。
*   **English Comments**: コード内のコメントは原則英語（グローバルスタンダード）。
*   **Japanese Content**: ユーザーに見えるテキストは日本語（ターゲット層重視）。

**Backend (Python)**:
*   **Type Hints**: すべての関数引数と戻り値に型ヒントをつける。
*   **Async/Await**: I/O処理（DB, API）は必ず非同期で書く。
*   **Pydantic**: データのバリデーションには Pydantic モデルを使用する。
*   **Linter**: `ruff` を使用。`E402` (Module level import not at top of file) は `main.py` でのみ許容。

**Frontend (React)**:
*   **Functional Components**: クラスコンポーネントは使用しない。
*   **Hooks**: `useEffect`, `useState` を適切に使用。カスタムフックは必要になるまで作らない。
*   **Prop Types**: 原則使用せず、シンプルなProps渡しで済ませる（TypeScript化の際はInterface定義）。

---

## 8. トラブルシューティング (Troubleshooting)

### Q1. 検索しても「結果が見つかりません」と出る。
*   **原因A**: `GEMINI_API_KEY` が設定されていない、または無効。
*   **原因B**: Gemini API のクオータ制限（無料枠の上限到達）。
*   **原因C**: 検索ワードが抽象的すぎて、Geminiがボードゲームと認識できなかった。

### Q2. データベースエラーが出る。
*   **原因**: `backend/init_db.sql` が Supabase で実行されていない。テーブルが存在しない。
*   **対策**: Supabase の SQL Editor で `init_db.sql` の内容を実行してください。

### Q3. デプロイ時に Backend が動かない。
*   **原因**: `requirements.txt` に必要なライブラリが含まれていない。
*   **対策**: `backend/requirements.txt` を確認し、`uv pip compile pyproject.toml -o requirements.txt` で再生成してください。Vercel は `pyproject.toml` ではなく `requirements.txt` を見ます。

---

このガイドラインに従い、シンプルかつ高速な「ボドゲのミカタ」を開発し続けましょう。
