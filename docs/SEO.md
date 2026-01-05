# SEO 戦略と実装ガイド

本書は、**ボドゲのミカタ**におけるSEO（検索エンジン最適化）の現状と実装をまとめたドキュメントです。

## 現在のステータス (2025-12-27更新)

### インデックス状況

| 項目 | 数 |
| :--- | :--- |
| サイトマップ送信 | 49ページ |
| 実際のインデックス | 1ページ (トップページのみ) |

### 実装状況

| 機能 | ステータス |
| :--- | :--- |
| SSRメタ注入 | ✅ 動作中 |
| **SSR本文注入** | ✅ **実装済み (NEW)** |
| カノニカルURL | ✅ 正常 |
| OGP | ✅ 正常 |
| JSON-LD | ✅ 正常 |
| XMLサイトマップ | ✅ 正常 |

---

## SSR本文注入の実装 (2025-12-27)

`seo_renderer.py` で `<body>` にゲームコンテンツを注入:

```html
<body>
  <div id="root">
    <article itemscope itemtype="https://schema.org/Game">
      <h1 itemprop="name">カタン</h1>
      <section>
        <h2>3行でわかる要約</h2>
        <p itemprop="description">...</p>
      </section>
      <section>
        <h2>基本情報</h2>
        <p>プレイ人数: 3-4人</p>
        <p>プレイ時間: 75分</p>
      </section>
      <section>
        <h2>ルール</h2>
        <div itemprop="text">...</div>
      </section>
    </article>
  </div>
</body>
```

---

## 次のステップ

1. Vercelにデプロイ
2. 本番環境でHTMLを確認
3. GSC URL検査で再クロールリクエスト
4. インデックス状況を監視

---

## 技術詳細

### SSRファイル

- [seo_renderer.py](file:///home/kafka/projects/rule-scribe-games/app/services/seo_renderer.py)

### サイトマップ・robots.txt

- [sitemap.py](file:///home/kafka/projects/rule-scribe-games/app/services/sitemap.py)
- [robots.txt](file:///home/kafka/projects/rule-scribe-games/frontend/public/robots.txt)

---

## note.com 連携戦略

### 現状

| 項目 | 値 |
| :--- | :--- |
| アカウント | [note.com/bodogenomikata](https://note.com/bodogenomikata) |
| 投稿記事 | 2本 |
| 自社リンク | プロフィール・記事内に設置済み |

### SEO効果

- **高ドメインパワー**: note.comは高DA（ドメインオーソリティ）
- **nofollowリンク**: 直接SEO効果は限定的だが、間接効果あり
- **SNS拡散**: 記事がX等でシェアされることで認知拡大
- **検索流入**: note検索からの流入 → 自社サイト誘導

### 記事一覧

| ファイル | 内容 |
| :--- | :--- |
| [001_splendor.md](file:///home/kafka/projects/rule-scribe-games/articles/note/001_splendor.md) | 宝石の煌き紹介 |
| [002_best3_time_thieves.md](file:///home/kafka/projects/rule-scribe-games/articles/note/002_best3_time_thieves.md) | 週末おすすめ3選 |
