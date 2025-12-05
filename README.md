# RuleScribe Games

[![Vercel](https://therealsujitk-vercel-badge.vercel.app/?app=rule-scribe-games)](https://rule-scribe-games.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![React](https://img.shields.io/badge/react-18.x-61dafb.svg)](https://reactjs.org/)

**AI-Powered Board Game Rule Wiki & Summarizer**

「世界中のあらゆるボードゲームのルールを、瞬時に、正確に、母国語で理解できる "Living Wiki"」

---

## 🚀 Demo

**[Live Demo (Vercel)](https://rule-scribe-games.vercel.app)**

---

## 📖 About

RuleScribe Games (ボドゲのミカタ) は、AI (Gemini 2.5 Flash) を活用してボードゲームの情報を整理・構造化するデータベースアプリケーションです。

AIがゲームのルールを「準備」「進行」「勝利条件」の3点に整理し、さらに「ゲームの魅力（人気のカード・要素）」や「重要キーワード」も抽出してWikiページを生成します。

検索されたゲーム情報はデータベース (Supabase) に保存され、次回以降のアクセスでは高速に表示されます。ユーザーの利用に伴い、データベースの情報が充実していく仕組みです。

### Key Features
- **🔍 AIによる情報生成**: 未登録のゲームも、AIが知識ベースから情報を検索・要約してページを作成。
- **� 構造化されたガイド**: マニュアルの内容を「インストラクション」「魅力」「キーワード」に整理して提示。
- **🚀 プレイ補助**: ルールの要点がまとまっているため、ゲームの準備や確認をスムーズに行えます。
- **🌏 信頼性の向上**: 公式サイトやAmazonなどのリンクをバックグラウンドで検証・収集し、正確な情報源へのアクセスを提供。

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | React, Vite, Tailwind CSS |
| **Backend** | Python (FastAPI), UV (Package Manager) |
| **AI Model** | Google Gemini 2.5 Flash |
| **Search** | Google Search Grounding (via Gemini) |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Deployment** | Vercel |
| **Tooling** | Taskfile, Ruff, Prettier |

## 💻 Getting Started (Local Development)

### Prerequisites
- **Python 3.11+** (Manage with `uv` recommended)
- **Node.js 18+**
- **Supabase Account** & Project
- **Google Gemini API Key** (via Google AI Studio)
- **Task** (Taskfile runner) - Optional but recommended

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd rule-scribe-games
    ```

2.  **Environment Setup**
    ```bash
    cp .env.example .env
    # .env ファイルを開き、Supabase URL/Key と Google API Key を入力してください
    ```

3.  **Install Dependencies**
    ```bash
    task setup
    # Or manually:
    # cd backend && uv sync
    # cd frontend && npm install
    ```

4.  **Database Initialization**
    SupabaseのSQLエディタで `backend/init_db.sql` の内容を実行し、テーブルを作成してください。
    ```bash
    # SQLの内容を表示
    task db:init
    ```

5.  **Run Development Server**
    ```bash
    task dev
    ```
    - Frontend: [http://localhost:5173](http://localhost:5173)
    - Backend: [http://localhost:8000](http://localhost:8000)

## 📜 Available Commands

このプロジェクトでは `Taskfile` を使用してコマンドを管理しています。

| Command | Description |
|---------|-------------|
| `task dev` | フロントエンドとバックエンドを同時に起動 (Hot Reload有効) |
| `task setup` | 依存関係のインストール (`uv sync`, `npm install`) |
| `task lint` | コードのLintとフォーマット (`ruff`, `prettier`, `eslint`) |
| `task db:init` | DB初期化用SQLを表示 |
| `task kill` | 開発サーバーのポート(8000, 5173)を強制解放 |
| `task issues` | GitHub Issue一覧を表示 |

## 🔄 Development Loop

私たちは **"Issue Driven Development"** と **"Concrete Proof"** を重視しています。

1.  **Check Issues**: `task issues` でタスクを確認。
    *   **Critical**: バグ、SEO、パフォーマンス問題 (最優先)
    *   **Easy**: UI微修正、テキスト変更 (隙間時間に消化)
2.  **Implement & Verify**: コードを修正し、ローカルで動作確認。
3.  **Concrete Comment**: GitHub Issue に「具体的な証拠」と共にコメントする。
    *   ✅ スクリーンショット via chrome browser extension or playwright
    *   ✅ ログ出力 / curl結果
    *   ✅ 修正したファイルパス
4.  **Close**: 証拠を残してから Issue をクローズする。
5.  **Loop**: Go to 1. Check Issues 

## 📂 Project Structure

```
rule-scribe-games/
├── backend/            # FastAPI Backend
│   ├── app/
│   │   ├── main.py     # Entry point
│   │   ├── routers/    # API Routes
│   │   ├── services/   # Business Logic (Gemini Client etc.)
│   │   ├── core/       # Config & DB connection
│   │   └── models.py   # Shared Pydantic Models
│   ├── experiments/    # Experimental Code (CrewAI etc.)
│   └── init_db.sql     # Database schema
├── frontend/           # React Frontend
│   ├── src/
│   │   ├── App.jsx     # Main component
│   │   └── ...
│   └── vite.config.js
├── Taskfile.yml        # Task runner configuration
└── vercel.json         # Vercel deployment config
```
