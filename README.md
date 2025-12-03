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

RuleScribe Games は、AI (Gemini 2.5 Flash) を活用してウェブ上の情報を統合し、ボードゲームのルールを「セットアップ」「ゲームフロー」「勝利条件」の3点に絞って構造化・要約するアプリケーションです。

ユーザーが検索するたびにデータベース (Supabase) が更新され、未知のゲームも即座にウェブ検索を行ってWikiページを生成する「自己進化型」データベースです。

### Key Features
- **🔍 検索即生成**: DB未登録のゲームもリアルタイムでウェブ検索・要約・保存。
- **📝 インテリジェント・サマリー**: 膨大なマニュアルを短時間で読める形式に構造化。
- **🌏 多言語対応**: 英語の情報源からでも日本語で要約を生成。
- **⚡ 高速なレスポンス**: 一度生成された情報はDBにキャッシュされ、次回以降は瞬時に表示。

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
