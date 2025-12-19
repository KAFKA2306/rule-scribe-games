# Frontend Source (`frontend/src/`)

フロントエンドのアプリケーションロジックの実装ディレクトリです。

## エントリーポイント
- **[`main.jsx`](./main.jsx)**: Reactアプリケーションのルートレンダリングを行います。`React.StrictMode` や `HelmetProvider` の設定が含まれます。
- **[`App.jsx`](./App.jsx)**: アプリケーションのメインコンポーネント。ルーティング定義（`BrowserRouter`）と全体レイアウトを管理します。

## グローバル設定
- **[`index.css`](./index.css)**: グローバルスタイル定義。CSS Variables (`:root`) によるカラーパレット、フォント、リセットCSSが定義されています。

## サブディレクトリ
- **[`components/`](./components/README.md)**: 再利用可能なUIコンポーネント。
- **[`pages/`](./pages/README.md)**: ルーティングに対応するページコンポーネント。
- **[`lib/`](./lib/README.md)**: ユーティリティ関数やAPIラッパー。
- **[`presentation/`](./presentation/README.md)**: スタイルやプレゼンテーション層のリソース。
