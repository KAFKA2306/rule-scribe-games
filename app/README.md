# App

FastAPI バックエンドアプリケーション。

## 構成

```
app/
├── main.py       # FastAPI アプリ定義
├── models.py     # Pydantic モデル
├── core/         # 設定・クライアント
├── routers/      # APIエンドポイント
├── services/     # ビジネスロジック
├── prompts/      # LLMプロンプト
└── utils/        # ユーティリティ
```

## エントリポイント

```python
# main.py
app = FastAPI()
app.include_router(router, prefix="/api")
```
