# Scripts (`scripts/`)

このディレクトリには、アプリケーションのデプロイ、データ保守、検証に使用するユーティリティスクリプトが含まれています。

## [`deploy_images.py`](./deploy_images.py)
ローカルのアセット画像をSupabase Storageにアップロードし、データベースを更新するスクリプトです。

- **対象**: `frontend/public/assets/games/*.png`
- **動作**:
    1. Supabase Storageの `game-images` バケットを作成（存在しない場合）。
    2. 画像ファイルをアップロード（Upsert）。
    3. 公開URLを取得。
    4. `games` テーブルの該当レコード (`slug` がファイル名と一致するもの) の `image_url` カラムを更新。

- **使用法**:
  ```bash
  uv run python scripts/deploy_images.py
  ```

## その他のスクリプト
- **`verify_gemini_model.sh`**: Geminiモデルが利用可能か、APIキーが有効かを確認するシェルスクリプト（存在する場合）。
