# ボドゲのミカタ (Bodoge no Mikata) - 完全統合マスターガイド

> **重要な免責事項**: このドキュメントは、プロジェクトの**唯一の真実（Single Source of Truth）**です。コードや設定に関する疑問が生じた場合、まずここを参照してください。このファイルは、プロジェクトの「ロジック」「設定」「スキーマ」「ユーザー体験」「コーディングスタイル」「デプロイ」のすべてを網羅しています。

---

## 1. プロジェクト憲章 (Project Charter)

### 1.1 サービス名
*   **日本語**: ボドゲのミカタ
*   **英語 (Repo)**: Bodoge no Mikata
*   **略称**: Bodoge no Mikata

### 1.2 コアコンセプト & 哲学 (Core Concepts & Philosophy)

1.  **Living Wiki (生きているWiki)**
    *   静的なデータベースではありません。ユーザーが「知らないゲーム」を検索した瞬間、AIが世界中から情報を収集し、Wikiページをリアルタイムで生成します。
    *   **自己進化**: 検索されるたびにデータベースが成長し、次回以降のユーザーはその恩恵（高速表示）を受けます。

2.  **Minimal Code & High Speed (最小コード・最高速度)**
    *   **"No Boilerplate"**: 不要なレイヤー（複雑なORMラッパー、過剰な抽象化）を排除します。
    *   **Direct & Raw**: Supabaseへのアクセスはシンプルに保ち、AIのプロンプトも直感的です。

3.  **Modern & Cool UI (モダンでクールなUI)**
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

### 2.2 ファイル構成 (Detailed File Manifest)
*   `backend/init_db.sql`: データベーススキーマとトリガー定義。
*   `backend/app/main.py`: バックエンドのエントリーポイント、ミドルウェア設定。
*   `backend/app/core/settings.py`: 環境変数読み込みとフォールバック設定。
*   `backend/app/services/gemini_client.py`: AIプロンプトと連携ロジック。
*   `frontend/src/index.css`: グローバルスタイルとカラー変数定義。
*   `vercel.json`: デプロイ設定とルーティングルール。

---

## 3. データベース詳細 (Database Schema)

**Platform**: Supabase (PostgreSQL)

### 3.1 テーブル定義 (`games`)
`backend/init_db.sql` に基づく現在の定義です。要最適化。

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
  structured_data jsonb,            -- 構造化データ (キーワード、カード等)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### 3.2 トリガー (Triggers)
更新日時を自動更新するためのトリガーが設定されていますが、動作不良が報告されています。デバッグが必要です。

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

---

## 4. AI & ロジック詳細 (AI Logic & Prompts)

**Model**: Google Gemini 2.5 Flash
**Library**: `google-generativeai` via `GeminiClient`

### 4.1 プロンプト設計 (Prompt Design)
`backend/app/services/gemini_client.py` で使用されている現在のプロンプトです。日本語のニュアンスや構造化の精度について要検討・要改善です。

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
1.  **Mock禁止**: 本番環境ではモックデータの使用は禁止されています。
2.  **Gemini Failures**: API制限やタイムアウトの場合、`search.py` はエラーを標準エラー出力にログし、空のリストを返します。フロントエンド側では検索結果ゼロ（またはエラーメッセージ）として扱われます。

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
    "structured_data": {
      "keywords": [{"term": "交渉", "description": "資源交換"}],
      "popular_cards": []
    }
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

### 6.1 デザインシステム (Design System)
`frontend/src/index.css` で定義されている現在のCSS変数です。

```css
:root {
  --bg-dark: #0b1221;
  --bg-card: rgba(255, 255, 255, 0.05);
  --bg-card-hover: rgba(255, 255, 255, 0.08);
  --border: rgba(255, 255, 255, 0.1);
  --accent: #4ef0c7;
  --accent-glow: rgba(78, 240, 199, 0.2);
  --text-main: #eef2ff;
  --text-muted: #94a3b8;
  --font-main: 'Zen Maru Gothic', sans-serif;
  --font-head: 'Space Grotesk', sans-serif;
}
```

### 6.2 状態管理 (State Management)
`frontend/src/App.jsx` 内で管理される主要な State です。

| State名 | 型 | 説明 |
| :--- | :--- | :--- |
| `games` | `Array` | 現在表示中のゲームリスト（検索結果または初期リスト）。 |
| `initialGames` | `Array` | 起動時に読み込んだ「最近のゲーム」キャッシュ。 |
| `selectedSlug` | `String` | 現在選択されているゲームのSlug。 |
| `loading` | `Boolean` | 通信中フラグ。 |
| `query` | `String` | 検索入力値。 |

---

## 7. 開発・デプロイガイド (Development & Deployment)

### 7.1 ローカル開発環境の構築

**依存関係 (Dependencies)**:
*   **Backend**: `fastapi>=0.123.0`, `google-generativeai>=0.8.5`, `supabase>=2.24.0`
*   **Frontend**: `react^18.2.0`, `react-markdown^10.1.0`

**環境変数 (Environment Variables)**:
`backend/app/core/settings.py` で定義されています。
*   `GEMINI_API_KEY`: 必須。
*   `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`: 必須。
*   `SUPABASE_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`: 必須。
*   `GEMINI_MODEL`: 任意 (デフォルト: `models/gemini-2.5-flash`)。

### 7.2 Vercel デプロイの仕組み
`vercel.json` によるハイブリッド構成です。要検討。

1.  **Frontend**: `@vercel/static-build` で `dist` を配信。
2.  **Backend**: `@vercel/python` で `api/index.py` を実行。

### 7.3 コーディング規約 (Coding Standards)

**General**:
*   **KISS (Keep It Simple, Stupid)**: 複雑な継承や過剰な分割を避ける。
*   **No Comments**: コード自体がドキュメントとなるように記述し、不要なコメントは残さない。
*   **Japanese Content**: ユーザーに見えるテキストはすべて日本語（ターゲット層重視）。

**Backend (Python)**:
*   **Type Hints**: すべての関数引数と戻り値に型ヒントをつける。
*   **Async/Await**: I/O処理（DB, API）は必ず非同期で書く。
*   **Pydantic**: バリデーションに利用。

---

このガイドラインを参考にして、シンプルかつ高速な「ボドゲのミカタ」を開発し続けましょう。
