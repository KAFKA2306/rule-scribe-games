# Frontend Application (`frontend/`)

このディレクトリには、React + Vite で構築されたシングルページアプリケーション (SPA) のフロントエンドコードが含まれています。

## 概要

RuleScribe Games のユーザーインターフェースを提供します。ユーザーはここでゲームを検索し、AIによって生成されたルール要約を閲覧します。

## 技術スタック
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **Styling**: Vanilla CSS (CSS Variables)
- **State Management**: React Hooks (`useState`, `useEffect`)
- **API Client**: Native `fetch` API

## ディレクトリ構成

- **[`src/`](./src/README.md)**: ソースコードのルート。
- **[`public/`](./public/)**: 静的アセット（画像、アイコンなど）。
- **[`index.html`](./index.html)**: アプリケーションのエントリーポイントHTML。
- **[`vite.config.js`](./vite.config.js)**: Viteの設定ファイル。

## 開発サーバーの動作
開発時 (`task dev` 実行時)、Viteはポート `5173` で起動します。
APIリクエスト (`/api/...`) は `vite.config.js` のプロキシ設定により、バックエンド (`localhost:8000`) に転送されます。これにより、CORSの問題を回避しながら開発を進めることができます。
