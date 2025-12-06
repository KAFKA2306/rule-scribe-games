# Frontend

React + Vite SPA。

## 構成

```
frontend/
├── src/
│   ├── App.jsx          # メインコンポーネント
│   ├── main.jsx         # エントリポイント
│   ├── index.css        # グローバルスタイル
│   ├── components/      # UIコンポーネント
│   ├── pages/           # ページコンポーネント
│   └── lib/             # API・Supabaseクライアント
├── public/              # 静的ファイル
└── tests/               # Playwright E2Eテスト
```

## コマンド

```bash
npm run dev      # 開発サーバー
npm run build    # 本番ビルド
npm run test     # E2Eテスト
```
