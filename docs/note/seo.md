# 最も基本的な技術の手引き

**― なぜ検索に出ないのか／何を直せば出るのか ―**

---

## 1. SEO（Search Engine Optimization：検索エンジン最適化）とは何か

**定義**
SEOとは、Googleなどの**検索エンジン（Search Engine）**に

* ページを正しく理解してもらい
* 検索結果に表示（インデックス）され
* 適切な順位で露出させる
  ための技術・設計の総称。

**今回の文脈**
「ボドゲのミカタ」のページが

* サイトマップには載っている
* しかし検索結果に出てこない
  という問題を解決することがSEOの目的。

---

## 2. クローラとインデックスの基本構造

### 2-1. クローラ（Crawler / Googlebot）

**定義**
クローラとは、検索エンジンがWebページを取得するための自動プログラム。
Googleの場合は **Googlebot** と呼ばれる。

**役割**

* URLにアクセスする
* HTMLを取得する
* 次に辿るリンクを収集する

---

### 2-2. インデックス（Index）

**定義**
インデックスとは、
「このページは検索結果に載せてよい」とGoogleが判断し、
検索用データベースに登録すること。

**重要な事実**

* **サイトマップに載る ≠ インデックスされる**
* **クロールされた ≠ インデックスされる**

---

## 3. HTML（HyperText Markup Language）と初期HTML

### 3-1. HTMLとは

**定義**
Webページの構造を表すテキスト形式の文書。
ブラウザや検索エンジンは、まずHTMLを読む。

---

### 3-2. 初期HTML（Initial HTML）

**定義**
JavaScriptが一切実行される前に、
サーバーから返される**生のHTML**。

**確認方法**

* `curl https://example.com/page`
* `view-source:https://example.com/page`

---

### 3-3. `<body>` と「本文」

**定義**
`<body>` タグは、

* ユーザーに見せる内容
* 検索エンジンが「中身」と認識する内容
  が入る場所。

**今回の問題**

```html
<body>
  <div id="root"></div>
</body>
```

これは

* 本文テキストが存在しない
* 見出し（H1）も説明文も無い

＝ **検索エンジンから見ると「中身が空のページ」**

---

## 4. SPA（Single Page Application：単一ページアプリケーション）

### 4-1. SPAの定義

**定義**
SPAとは、

* 最初に1つのHTMLだけを読み込み
* ページ遷移や本文表示をJavaScriptで行う
  Webアプリ構造。

ReactはSPAを作る代表的なライブラリ。

---

### 4-2. SPAのSEO上の弱点

**構造**

* 初期HTML：ほぼ空
* 本文：JavaScript実行後に生成

**問題**

* GoogleはJavaScriptを実行できるが
* 実行は「後回し」になる
* 評価が遅れる／スキップされることがある

→ **小規模・新規サイトでは特に不利**

---

## 5. CSR / SSR / SSG の違い（超重要）

### 5-1. CSR（Client-Side Rendering：クライアントサイド描画）

**定義**

* HTMLは空
* ブラウザ（クライアント）でJavaScriptがHTMLを作る

**現状の構成**

* React + Vite の標準SPA
* **今回の失敗パターン**

---

### 5-2. SSR（Server-Side Rendering：サーバーサイド描画）

**定義**

* リクエストごとに
* サーバーがHTMLを生成して返す

**特徴**

* 初期HTMLに本文あり
* 実装・運用がやや複雑

---

### 5-3. SSG（Static Site Generation：静的サイト生成）

**定義**

* ビルド時に
* すべてのページのHTMLを事前生成
* CDNから配信

**今回の最適解**

* `/games/catan` などは記事ページ
* 更新頻度が低い
  → **SSGが最もシンプルかつ堅牢**

---

## 6. Vite と React と vite-react-ssg

### 6-1. Vite（ビート）

**定義**
高速なフロントエンド開発・ビルドツール。

---

### 6-2. React

**定義**
ユーザーインターフェース（UI）を構築するJavaScriptライブラリ。

---

### 6-3. vite-react-ssg

**正式名称**
Vite React Static Site Generation

**定義**

* Vite + React 用の
* **SSG（静的HTML生成）プラグイン**

**役割**

* React Routerで定義されたページを
* ビルド時にHTMLとして出力

---

## 7. 動的ルートと getStaticPaths

### 7-1. 動的ルート（Dynamic Route）

**定義**
URLの一部が変数になっているルート。

例：

* `/games/catan`
* `/games/chess`

→ `/games/:slug`

---

### 7-2. getStaticPaths

**定義**
SSGで
「どのURLをHTMLとして生成するか」を
**ビルド時に列挙する関数**

**役割**

* `/games/catan`
* `/games/chess`
* `/games/go`

などを明示的に返す。

---

## 8. Supabase

**定義**
データベース・認証・APIを提供するBackend as a Service。

**今回の役割**

* ゲーム一覧
* `slug`（URL識別子）を保存

**重要**

* ビルド時に
* **読み取り専用・公開安全な方法**で
  `slug`一覧を取得する

---

## 9. サイトマップ（sitemap.xml）

**定義**
検索エンジンに
「このサイトにはこれらのURLがあります」と知らせるXML。

**注意**

* サイトマップは「案内」
* **インデックス保証ではない**

---

## 10. Google Search Console（GSC）

**定義**
Googleが提供する検索管理ツール。

**主な機能**

* URL検査
* インデックス状況確認
* サイトマップ送信

---

## 11. URL検査（URL Inspection）

**定義**
GSCで
「GoogleがこのURLをどう見ているか」を確認する機能。

**見るべき点**

* クロールされたHTML
* レンダリング結果
* インデックス可否

---

## 12. 今回の結論（技術的に一行）

> **初期HTML（JavaScript実行前）に本文が無いSPAは、
> 小規模サイトではインデックスされにくい。
> SSGでHTMLに本文を事前生成すれば、構造的に解決する。**

---

## 次にやるべき最小ステップ（用語理解済み前提）

1. SSG（Static Site Generation）を採用
2. vite-react-ssg を導入
3. getStaticPaths で全 `/games/{slug}` を列挙
4. 初期HTMLに

   * `<h1>`
   * ルール要約本文
     が含まれることを確認
5. GSCのURL検査で再確認