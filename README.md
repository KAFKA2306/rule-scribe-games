# rule-scribe-games：Google Gemini 版 - フルコード一式

これは "ボードゲーム公式ルール検索＆要約サービス" を **Google Gemini API** で動かすミニマル・モノリシック実装です。
フロントエンドとバックエンドが含まれており、`docker-compose up --build` で一括起動できます。

## 1. ディレクトリ構成

```text
.
├── frontend/     # フロントエンド (React + TypeScript)
└── rule-scribe-games/ # バックエンド (Python + FastAPI)
    ├─ rsg/
    ├─ worker.py
    ├─ requirements.txt
    ├─ Dockerfile
    └─ docker-compose.yml
```

## 2. 起動手順

```bash
# 1. APIキーを .env に設定
echo "GEMINI_API_KEY=xxxxxxxxxxxxxxxx" > ./rule-scribe-games/.env

# 2. 一括起動
docker-compose -f ./rule-scribe-games/docker-compose.yml up --build
```

## 3. 使い方

1.  ブラウザで `http://localhost:3000` を開きます。
2.  検索バーにボードゲームの名前を入力して、ルールを検索します。
3.  まだインデックスに登録されていないゲームの場合は、ルールテキストを送信して要約を生成できます。

### API エンドポイント

*   `POST /request`: ルールの要約をリクエストします。
    ```json
    {
      "title": "カタン",
      "raw_text": "## セットアップ ... (公式 PDF を抽出したテキスト)"
    }
    ```
*   `GET /search?q={query}`: 指定されたクエリでゲームを検索します。
*   `GET /games/{game_id}`: 特定のゲームの詳細を取得します。
