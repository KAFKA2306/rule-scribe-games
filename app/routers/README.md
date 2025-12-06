# Routers

FastAPI エンドポイント定義。

## ファイル

| ファイル | 役割 |
|---------|------|
| `games.py` | ゲーム関連API |

## エンドポイント

| メソッド | パス | 機能 |
|---------|------|------|
| `GET` | `/search` | ゲーム検索 |
| `POST` | `/search` | 検索 + 新規生成 |
| `GET` | `/games` | 一覧取得 |
| `GET` | `/games/{slug}` | 詳細取得 |
| `PATCH` | `/games/{slug}` | 更新 |
