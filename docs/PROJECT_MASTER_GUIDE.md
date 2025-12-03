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
    *   **データエンハンスメント**: データバージョン管理 (`data_version`) により、古いデータを段階的かつ自動的にリッチ化するロジック (`DataEnhancer`) が組み込まれています。

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
*   `backend/app/services/gemini_client.py`: 検索と基本情報抽出のAIロジック。
*   `backend/app/services/data_enhancer.py`: 既存データの段階的強化を行うAIロジック。
*   `backend/app/routers/games.py`: ゲーム一覧・詳細取得エンドポイント。
*   `backend/app/services/amazon_affiliate.py`: Amazon検索URL生成ロジック (Layer 0)。
*   `backend/app/services/amazon_batch.py`: Amazon ASIN取得バッチ処理 (Layer 1)。
*   `frontend/src/index.css`: グローバルスタイルとカラー変数定義。
*   `vercel.json`: デプロイ設定とルーティングルール。
*   `frontend/vite.config.js`: フロントエンドのビルド・開発プロキシ設定。

---

## 3. データベース詳細 (Database Schema)

**Platform**: Supabase (PostgreSQL)

### 3.1 テーブル定義 (`games`)
`backend/init_db.sql` に基づく現在の定義です。

```sql
-- pgvector拡張 (将来的なベクトル検索用)
create extension if not exists vector;

create table if not exists games (
  id bigint primary key generated always as identity,
  slug text unique not null,        -- URL用スラッグ (タイトルから生成)
  title text not null,              -- ゲームタイトル (日/英)
  description text,                 -- 短い概要
  summary text,                     -- AI生成要約
  rules_content text,               -- 詳細ルール (Markdown)
  source_url text unique,           -- 情報源URL (重複排除キー)
  image_url text,                   -- 画像URL
  structured_data jsonb default '{}'::jsonb, -- 構造化データ

  -- Analytics & Logic
  view_count bigint default 0,      -- 閲覧数
  search_count bigint default 0,    -- 検索ヒット数
  data_version integer default 0,   -- データ拡張バージョン (DataEnhancer用)
  is_official boolean default false,-- 公式/検証済みフラグ

  -- Metadata for Sorting/Filtering (#28)
  min_players integer,              -- 最低プレイ人数
  max_players integer,              -- 最高プレイ人数
  play_time integer,                -- プレイ時間 (分)
  min_age integer,                  -- 対象年齢
  published_year integer,           -- 発行年

  -- Titles (#28)
  title_ja text,                    -- 日本語タイトル
  title_en text,                    -- 英語タイトル

  -- External Links (#31, #33)
  official_url text,                -- 公式サイトURL
  bgg_url text,                     -- BoardGameGeek URL
  bga_url text,                     -- Board Game Arena URL
  amazon_url text,                  -- Amazon URL (Search/Affiliate)

  -- Media/Content (#30, #32)
  audio_url text,                   -- 音声解説URL (Voicevox/Zundamon)

  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create index if not exists idx_games_slug on games(slug);
create index if not exists idx_games_title on games(title);
```

### 3.2 トリガー (Triggers)
`extensions.moddatetime` を使用して信頼性の高い更新日時管理を行います。

```sql
create extension if not exists moddatetime schema extensions;

create trigger handle_updated_at before update on games
  for each row execute procedure moddatetime (updated_at);
```

**更新履歴:**
*   `backend/migrate_schema_v2.sql`: 上記カラムの追加とトリガー修正を含むマイグレーションスクリプト。

---

## 4. 設定値・環境変数 (Settings & Configurations)

### 4.1 環境変数 (`backend/app/core/settings.py`)
システムが依存する全ての環境変数です。Vercel環境では `NEXT_PUBLIC_` プレフィックス付きの変数も自動的に読み込まれます（フォールバック）。

| 変数名 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `None` (Required) | Google AI Studio APIキー。 |
| `GEMINI_MODEL` | `models/gemini-2.5-flash` | 使用するAIモデル名。 |
| `SUPABASE_URL` | `None` (Required) | Supabase プロジェクトURL。 |
| `NEXT_PUBLIC_SUPABASE_URL` | - | `SUPABASE_URL` のフォールバック。 |
| `SUPABASE_SERVICE_ROLE_KEY`| `None` | Supabase 管理者キー (優先)。 |
| `SUPABASE_KEY` | `None` | Supabase APIキー。 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | - | `SUPABASE_KEY` のフォールバック。 |
| `AMAZON_TRACKING_ID` | `None` | AmazonアソシエイトのトラッキングID。 |
| `AMAZON_ACCESS_KEY` | `None` | Amazon PA-API アクセスキー (Batch用)。 |
| `AMAZON_SECRET_KEY` | `None` | Amazon PA-API シークレットキー (Batch用)。 |
| `AMAZON_PARTNER_TAG` | `None` | Amazon PA-API パートナータグ (Batch用)。 |

### 4.2 フロントエンド設定 (`frontend/vite.config.js`)
*   **Proxy**: `/api` へのリクエストは `http://localhost:8000` (バックエンド) に転送されます。

### 4.3 定数値 (Hardcoded Constants)
*   `gemini_client.py`: タイムアウト `30.0` 秒。
*   `gemini_client.py`: Google Search Tool 使用 (Grounding)。
*   `search.py`: "Simple Search" 判定の文字数制限 `50` 文字。
*   `data_enhancer.py`: データ強化の再実行間隔 `30` 日。

---

## 5. AIプロンプト全集 (Prompt Registry)

システムで使用されている全てのAIプロンプトをここに記載します。修正を行う際は、この定義を参照してください。

### 5.1 新規検索・基本情報抽出 (`gemini_client.py`)
ユーザーが新しいゲームを検索した際に実行されます。

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

### 5.2 データエンハンスメント - Phase 0: 基本構造 (`data_enhancer.py`)
データバージョンが `0` の場合（初期状態）に実行。

```text
ゲーム: {game_title}
説明: {game_description}

このゲームの基本情報をJSON形式で生成してください。

必須フィールド:
- type: ゲームのタイプ（例: "deck-building", "resource-management", "dice-game"）
- overview: ゲームの簡潔な概要（1-2文）

JSON形式で返してください。
```

### 5.3 データエンハンスメント - Phase 1: キーワード追加 (`data_enhancer.py`)
データバージョンが `1` で、文脈が `summarize` または `detail` の場合。

```text
ゲーム: {game_title}
説明: {game_description}

現在のデータ: {current_data}

以下の情報を追加してください:
- keywords: ゲームの重要な用語とその説明のリスト
  形式: [{"term": "用語", "description": "説明"}]

既存のデータと追加情報を統合したJSON形式で返してください。
```

### 5.4 データエンハンスメント - Phase 2: 詳細コンポーネント (`data_enhancer.py`)
データバージョンが `2` 以上で、文脈が `detail` の場合。

```text
ゲーム: {game_title}
説明: {game_description}

現在のデータ: {current_data}

以下の情報を追加してください:
- popular_cards or popular_components: 人気のあるカード/コンポーネント（該当する場合）
- expansions: 拡張セットの情報（該当する場合）

既存のデータと追加情報を統合したJSON形式で返してください。
```

### 5.5 フォールバック (`data_enhancer.py`)
条件に合致しない場合。

```text
ゲーム: {game_title}
説明: {game_description}

現在のデータを返してください。
```

---

## 6. API仕様書 (API Specification)

すべてのAPIは `FastAPI` によって提供され、`/api` プレフィックスを持ちます。

### 6.1 POST `/api/search`
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
    "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "slug": "catan",
    "title": "Catan (カタン)",
    "description": "無人島を開拓する...",
    "rules_content": "**セットアップ**: ...",
    "image_url": "https://...",
    "source_url": "https://boardgamegeek.com/...",
    "structured_data": {
      "keywords": [{"term": "交渉", "description": "資源交換"}],
      "popular_cards": [],
      "affiliate_urls": {
        "amazon": "https://www.amazon.co.jp/..."
      }
    }
  }
]
```

### 6.2 GET `/api/games`
最近更新されたゲームの一覧を取得します。`supabase_repository.list_recent` を使用して取得します。

**Parameters**: `limit` (default: 100)

### 6.3 GET `/api/games/{slug}`
特定のゲーム詳細を取得。Slug または ID でアクセス可能。

---

## 7. フロントエンド詳細 (Frontend Details)

**Framework**: React 18 + Vite
**Styling**: CSS Modules (Variables) + Utility Classes

### 7.1 デザインシステム (Design System)
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

### 7.2 状態管理 (State Management)
`frontend/src/App.jsx` 内で管理される主要な State です。

| State名 | 型 | 説明 |
| :--- | :--- | :--- |
| `games` | `Array` | 現在表示中のゲームリスト（検索結果または初期リスト）。 |
| `initialGames` | `Array` | 起動時に読み込んだ「最近のゲーム」キャッシュ。 |
| `selectedSlug` | `String` | 現在選択されているゲームのSlug。 |
| `loading` | `Boolean` | 通信中フラグ。 |
| `query` | `String` | 検索入力値。 |

---

## 8. 開発・デプロイガイド (Development & Deployment)

### 8.1 ローカル開発環境の構築

**依存関係 (Dependencies)**:
*   **Backend**: `fastapi>=0.123.0`, `google-generativeai>=0.8.5`, `supabase>=2.24.0`, `python-amazon-paapi>=5.0.1`
*   **Frontend**: `react^18.2.0`, `react-markdown^10.1.0`

**環境変数 (Environment Variables)**:
`backend/app/core/settings.py` で定義されています。
*   `GEMINI_API_KEY`: 必須。
*   `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`: 必須。
*   `SUPABASE_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`: 必須。
*   `GEMINI_MODEL`: 任意 (デフォルト: `models/gemini-2.5-flash`)。

### 8.2 Vercel デプロイの仕組み
`vercel.json` によるハイブリッド構成です。要検討。

1.  **Frontend**: `@vercel/static-build` で `dist` を配信。
2.  **Backend**: `@vercel/python` で `api/index.py` を実行。

### 8.3 コーディング規約 (Coding Standards)

**General**:
*   **KISS (Keep It Simple, Stupid)**: 複雑な継承や過剰な分割を避ける。
*   **No Comments**: コード自体がドキュメントとなるように記述し、不要なコメントは残さない。
*   **Japanese Content**: ユーザーに見えるテキストはすべて日本語（ターゲット層重視）。

**Backend (Python)**:
*   **Type Hints**: すべての関数引数と戻り値に型ヒントをつける。
*   **Async/Await**: I/O処理（DB, API）は必ず非同期で書く。
*   **Pydantic**: バリデーションに利用。

---

## 9. 重要トラブルシューティング (Critical Troubleshooting)

最近のインシデントから得られた重要な教訓です。

### 9.1 Vercel環境変数の設定
`echo` コマンドを使用してVercelの環境変数を設定する場合、デフォルトで末尾に改行文字 (`\n`) が追加されます。これによりAPIキーが無効になる問題が発生しました。
**必ず `echo -n` を使用してください。**

```bash
# ❌ 悪い例（改行が入る）
echo "key" | vercel env add GEMINI_API_KEY production

# ✅ 正しい例（改行なし）
echo -n "key" | vercel env add GEMINI_API_KEY production
```

### 9.2 IDの型定義
SupabaseのデータベースIDは **UUID (文字列)** です。
Pydanticモデルやフロントエンドの型定義で `int` を使用すると、バリデーションエラーやランタイムエラーが発生します。必ず `str` を使用してください。

### 9.3 環境変数の読み込み順序
`backend/app/core/setup.py` により、以下の順序で `.env` ファイルが読み込まれます：
1. リポジトリルートの `.env` (優先)
2. `backend/.env`

ルートの `.env` に古い値が残っていると、`backend/.env` を更新しても反映されないため注意が必要です。

### 9.4 Vercel環境変数のデバッグ
環境変数が正しく設定されているか確認するには、`vercel env pull` を使用して実際の値をダウンロードし、`cat -A` で非表示文字（改行など）を確認します。

```bash
vercel env pull .env.vercel.production --environment=production
cat -A .env.vercel.production
```

### 9.5 デプロイ状況の確認 (GitHub Actions)
`gh` コマンドを使用して、デプロイワークフローのステータスを素早く確認できます。

```bash
gh run list --limit 5
```

### 9.6 APIルーティングの競合
FastAPIでは、先に登録されたルーターのエンドポイントが優先されます。
例: `search.py` で `/games` を定義し、その後に `games.py` で `/games` を定義した場合、`search.py` の方が優先され、意図しない挙動（バリデーションエラーなど）を引き起こす可能性があります。エンドポイントの重複には十分注意してください。

---

## 10. アフィリエイトシステム (Affiliate System)

収益化の中核となるアフィリエイトリンク生成ロジックです。

### 10.1 Layer 0: 自動検索リンク (Automatic Search Links)
*   **ロジック**: 手動設定されたリンクがない場合、自動的に `https://www.amazon.co.jp/s?k={Title}&tag={TrackingID}` を生成します。
*   **メリット**: 全てのゲームに対して即座にリンクを提供可能。手動運用コストゼロ。
*   **実装**: `backend/app/services/amazon_affiliate.py`

### 10.2 Layer 1: ASIN自動取得バッチ (ASIN Batch)
*   **ロジック**: Amazon Product Advertising API (PA-API) を使用して、正確な商品ページ (ASIN) を検索し、データベース (`structured_data.affiliate_urls.amazon`) に保存します。
*   **実装**: `backend/app/services/amazon_batch.py`
*   **実行**: `uv run python -m app.services.amazon_batch`

### 10.3 優先順位
1.  **手動設定**: `structured_data.affiliate_urls.amazon` に値がある場合、最優先で使用（Layer 1による更新もこれに含まれる）。
2.  **自動生成**: 上記がない場合、Layer 0 の検索リンクを使用。

---

このガイドラインを参考にして、シンプルかつ高速な「ボドゲのミカタ」を開発し続けましょう。
