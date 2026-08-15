# Scripts (`scripts/`)

このディレクトリには、アプリケーションのデプロイ、データ保守、検証に使用するユーティリティスクリプトが含まれています。

## ゲーム画像の正準配信

Web UI で使用するリポジトリ管理画像は `frontend/public/images/games/*.webp` を正準とし、`/images/games/<slug>.webp` の same-origin URL で Vercel から静的配信します。

Supabase Storage は、静的 WebP へまだ移行できていないことを実証済みの例外だけに限定します。例外は `app/core/supabase.py` の `_STORAGE_IMAGE_OVERRIDES` に明示し、slug から暗黙に推測しません。

アドホックなローカル PNG アップローダーから Storage と `games.image_url` を同時更新する運用は行いません。画像を追加・移行する場合は、WebP アセットと参照先を同じ変更としてレビューし、公開後に実URLを確認します。

## その他のスクリプト

各スクリプトを実行する前に、repository root の `AGENTS.md` と `Taskfile.yml` を確認し、既存の正準タスクがある場合はそちらを使用してください。
