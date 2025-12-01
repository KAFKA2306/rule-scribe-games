# RuleScribe Games

## 究極の目標
**「世界中のあらゆるボードゲームのルールを、瞬時に、正確に、母国語で理解できる "Living Wiki" を構築する」**

RuleScribe Games は、AIの力でウェブ上の散在する情報を統合し、プレイヤーが直感的に理解できる形式（セットアップ、ゲームフロー、勝利条件）に再構築します。ユーザーが検索するたびにデータベースが充実し、自己進化し続ける「生きたルールブック」を目指します。

## 主要機能

### 1. AI駆動の自動Wiki生成
*   **検索即生成**: データベースにないゲームが検索されると、即座にウェブ（公式サイト、BGG、PDFマニュアル）を探索し、情報を構造化して保存します。
*   **情報の正規化**: 揺れのある表記を統一し、英語と日本語のタイトルを併記。
*   **出典の厳選**: 公式ルールブックや信頼性の高い情報源を優先的に参照し、ハルシネーションを最小化します。

### 2. インテリジェント・サマリー
*   **構造化された要約**: 膨大なルールブックを「準備」「手順」「勝利条件」の3点に絞ってMarkdown形式で出力。
*   **多言語対応**: 英語のソースからでも、流暢な日本語で解説を生成。

### 3. "Living" Database (Supabase + Vector Search)
*   **自己進化**: ユーザーの検索行動自体がWikiを育てます。一度検索されたゲームは永続化され、次回以降は超高速に表示。
*   **画像統合**: ゲームのボックスアートやコンポーネント画像を自動取得し、視覚的なデータベースを構築。

### 4. ミニマルで美しいUI
*   **即応性**: React + Tailwind CSS によるモダンで高速なインターフェース。
*   **集中**: 余計な装飾を排し、プレイヤーが「今すぐ遊び始める」ことだけに集中できるデザイン。

## 技術スタック
*   **Backend**: Python (FastAPI), Gemini 2.5 Flash (Google AI Studio)
*   **Frontend**: React (Vite), Tailwind CSS
*   **Database**: Supabase (PostgreSQL + pgvector)
*   **Search Grounding**: Google Search Grounding (via Gemini)

## セットアップ (Setup)

### 前提条件
*   Python 3.11+
*   Node.js 18+
*   Supabase アカウント & プロジェクト
*   Google Gemini API Key

### インストール
```bash
# 依存関係のインストール
task setup

# 環境変数の設定 (.envを作成し、キーを入力)
cp .env.example .env
```

### データベース初期化
SupabaseのSQLエディタで `backend/init_db.sql` を実行してください。

### 起動
```bash
task dev
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000