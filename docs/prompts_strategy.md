# Prompt & Regeneration Strategy (ありたい姿)

## 背景
- `PATCH /api/games/{slug}?regenerate=true&fill_missing_only=` を何度も改修したが、期待どおりに動かないケースが頻発。
- 目的は「既存データを壊さずに不足を補う」「誤りを自動修正する」を両立させること。

## ゴール
1. **安全な再生成**: 既存フィールドを守りつつ欠損だけを埋められる（fill_missing_only=true）。
2. **完全再生成**: 全フィールドを刷新しつつ、ID/slug/バージョン・ビジネス制約は維持（fill_missing_only=false）。
3. **予測可能な挙動**: APIレスポンスと副作用が明確で、フロント・オペレーションが迷わない。

## API 期待仕様（理想）
- エンドポイント: `PATCH /api/games/{slug}`
- クエリ:
  - `regenerate=true|false` (必須: true のときだけ再生成タスク投入)
  - `fill_missing_only=true|false` (省略時 false)
- レスポンス:
  - 即時: `{"status":"accepted","mode":"fill-missing|full","task_id": "<uuid>"}`
  - 失敗: 404 (slugなし) / 422 (パラメータ不正) / 503 (Gemini/queue障害)
- 非同期結果確認手段:
  - （将来）`GET /api/tasks/{task_id}` で状態確認できるようにしたい
  - それまではログ & Supabase レコード確認が前提

## プロンプト方針（生成・改善）
1. **Generator (metadata_generator)**  
   - 日本語 summary/rules_content は必須。  
   - URL 信頼度は低めに設定し、曖昧なら null。  
   - `structured_data.keywords` は 5–10 件。  
2. **Critic (metadata_critic)**  
   - `protected_fields` を尊重し、低信頼のみを修正。  
   - `fill_missing_only=true` の場合は「欠損のみ埋める」モードのプロンプトバリアントを用意する。  
3. **Link Resolver**  
   - 別ジョブに切り出し、生成本体の失敗要因にしない。  

## マージ方針（fill_missing_only の理想挙動）
- 既存値が None / "" / {} のときのみ上書き。
- 数値 0 や False は有効値として扱い、保持する。
- `structured_data` はトップレベルで shallow merge。将来的にはフィールド単位マージを検討。
- `id`, `slug`, `created_at` は常に既存を優先。
- `data_version` は +1 して履歴を示す。

## バリデーション & フェイルセーフ
- 必須フィールド: `title`, `summary`, `rules_content`, `slug`.
- 文字列長・JSON 形の基本チェックを追加（422 を返す）。
- Gemini 429/5xx 時は DB 書き込みをスキップし、`task_id` に失敗ステータスを残す。
- Supabase upsert 前にフィールドホワイトリストを適用。

## ロギング / オブザーバビリティ
- 背景タスク開始/完了/失敗を構造化ログで記録: `event=regenerate`, `slug`, `mode`, `task_id`, `duration_ms`.
- 429/5xx はリトライせず明示的に失敗ログを残す（将来は指数バックオフを検討）。

## ロールアウト案
1. **短期**: 現行実装にバリデーションとログ強化を追加。`fill_missing_only` プロンプトバリアントを先に作成。  
2. **中期**: `task_id` 付きのタスクテーブル or インメモリキューを導入し、結果確認 API を追加。  
3. **長期**: Link Resolver を非同期キュー化し、URL検証の安定性を上げる。  

## 未決定・要議論
- タスク永続化の方式（Supabase テーブル vs SQS 等）。
- 同時実行上限とキューイング戦略（rate limit とのバランス）。
- `structured_data` の深いマージポリシー（配列の結合 or 置換）。
- 失敗時のユーザー通知方法（WebSocket/SSE/ポーリング）。  

このドキュメントは「ありたい姿」のメモ。実装のたたき台として随時更新する。***
