# Components (`frontend/src/components/`)

このディレクトリには、アプリケーション全体で再利用されるReactコンポーネントが含まれています。

## 汎用コンポーネント

#### `ThinkingMeeple.jsx`
- **役割**: ロディング状態を示すコンポーネント。
- **機能**: ミープル（ボードゲームの駒）の画像をアニメーション表示し、ユーザーに待機を促します。

#### `EditGameModal.jsx`
- **役割**: ゲーム情報の編集モーダル。
- **機能**: ユーザー（管理者的な立ち位置）がゲームのタイトル、ルール、YouTube URLなどを手動で修正するためのフォームを提供します。

#### `GameBackground.jsx`
- **役割**: アプリケーション全体の背景描画。
- **機能**: ボードゲームらしい雰囲気を出すための装飾的な背景パターンや画像を管理します。

## ゲーム詳細関連 (`game/`)
`frontend/src/components/game/` ディレクトリには、`GamePage` で使用される特定の機能を持った小さなコンポーネントが配置されています。

- **`ExternalLinks.jsx`**: 公式サイトやBGG、Amazonへの外部リンクをまとめて表示します。
- **`ShareButtons.jsx`**: Twitter (X) やLINEなどでページをシェアするためのボタン群です。
- **`RegenerateButton.jsx`**: AIによる再生成をトリガーするボタン。
- **`TextToSpeech.jsx`**: ルール概要の読み上げ機能を提供します。
