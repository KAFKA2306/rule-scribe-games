---
description: SEO最適化とGoogle Search Console操作
---

# SEO Skill

## URL検査

1. https://search.google.com/search-console にアクセス
2. 左メニュー「URL検査」→ URLを入力
3. 未登録なら「インデックス登録をリクエスト」

## サイトマップ再送信

1. https://search.google.com/search-console/sitemaps にアクセス
2. `sitemap.xml` を入力 → 「送信」

## 新規ゲーム追加後

1. デプロイ完了確認
2. URL検査で `https://bodoge-no-mikata.vercel.app/games/{slug}` をチェック
3. 「インデックス登録をリクエスト」

## 関連ファイル

- `app/services/sitemap.py` - サイトマップ生成
- `app/services/seo_renderer.py` - SSRメタタグ
- `docs/SEO.md` - SEO戦略
