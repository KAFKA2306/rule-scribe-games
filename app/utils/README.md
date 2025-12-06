# Utils

共通ユーティリティ関数。

## ファイル

| ファイル | 役割 |
|---------|------|
| `slugify.py` | タイトル→slug 変換 |
| `affiliate.py` | Amazon アフィリエイトURL生成 |
| `logger.py` | 監査ログ出力 |

## 主要関数

| 関数 | 入力 | 出力 |
|-----|------|------|
| `slugify()` | `"ボードゲーム Title"` | `"title"` |
| `amazon_search_url()` | `"ゲーム名"` | Amazon検索URL |
| `ensure_amazon_tag()` | URL | タグ付きURL |
| `log_audit()` | 操作情報 | JSON監査ログ |
