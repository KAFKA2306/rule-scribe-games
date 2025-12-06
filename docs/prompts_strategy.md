# Prompt & Regeneration Strategy（ありたい姿）

## 背景
- `PATCH /api/games/{slug}?regenerate=true&fill_missing_only=` を何度も改修したが、期待どおりに動かないケースが頻発。
- 目的は「既存データを壊さずに不足を補う」「誤りを自動修正する」を両立させること。
- 失敗要因の可視化が弱く、原因不明のまま再実装を繰り返している。

## ゴール
1) **安全な再生成**: 既存フィールドを守りつつ欠損だけを埋められる（fill_missing_only=true）。  
2) **完全再生成**: 全フィールドを刷新しつつ、ID/slug/バージョン・ビジネス制約は維持（fill_missing_only=false）。  
3) **予測可能な挙動**: APIレスポンスと副作用が明確で、フロント/オペレーションが迷わない。  
4) **原因追跡可能**: 失敗時に「どこで」「なぜ」がログとタスク状態で分かる。  

## API 期待仕様（理想）
- エンドポイント: `PATCH /api/games/{slug}`
- クエリ:
  - `regenerate=true|false`（必須: true のときだけ再生成タスク投入）
  - `fill_missing_only=true|false`（省略時 false）
- レスポンス:
  - 即時: `{"status":"accepted","mode":"fill-missing|full","task_id":"<uuid>"}`  
  - エラー: 404(slugなし) / 422(パラメータ・バリデーション) / 503(Gemini/queue障害)
- 非同期結果確認:
  - 将来: `GET /api/tasks/{task_id}` で状態確認
  - 現状: ログと Supabase レコード確認が前提

## プロンプト方針（生成・改善）
1. **Generator (metadata_generator)**: 日本語 summary/rules_content は必須。URL は曖昧なら null。keywords は 5–10 件。  
2. **Critic (metadata_critic)**: `protected_fields` を尊重し、低信頼のみ修正。`fill_missing_only=true` 用のバリアントを別途用意。  
3. **Link Resolver**: 別ジョブに切り出し、生成本体の失敗要因にしない。  

## マージ方針（fill_missing_only の理想挙動）
- 既存値が None / "" / {} のときのみ上書き。0 や False は有効値として保持。
- `structured_data` は暫定で shallow merge、keywords はユニーク結合を検討。
- `id`, `slug`, `created_at` は常に既存優先。`data_version` は +1。

## バリデーション & フェイルセーフ
- 必須: `title`, `summary`, `rules_content`, `slug`。jsonschema で検証し、欠損は 422 or task failed。
- 文字列長・JSON形もチェック。Gemini 429/5xx 時は DB 書き込みをスキップし task に失敗理由を残す。
- Supabase upsert 前にフィールドホワイトリストを適用。

## ロギング / オブザーバビリティ
- `event=regenerate`, `slug`, `mode`, `task_id`, `status`, `duration_ms`, `error` を構造化ログで残す。
- 429/5xx はリトライせず失敗として記録（将来は指数バックオフを検討）。

## 既知の失敗モード（仮説含む）
- **Gemini応答不正**: JSON崩れ・必須欠損 → `_validate` で無音失敗。  
  対策: jsonschema, 422/failed ステータスで返す。  
- **429/5xx**: rate limit/障害で書き込みなし。  
  対策: throttle + 429 待機、失敗をタスクに記録。  
- **slug衝突/ズレ**: 生成 slug が既存と違い別行 upsert。  
  対策: regen 時は既存 slug を強制使用、title 変更は別 API へ分離。  
- **Supabase権限不足**: service role 不在で 403。  
  対策: 起動時にキー検証、403 を即エラーログ。  
- **BackgroundTasks 例外握りつぶし**: 成功に見えて無変更。  
  対策: try/except で task status=failed + stacktrace。  
- **structured_data の上書き欠落**: 浅いマージで配列が消える。  
  対策: keywords などは union マージを定義。

## なぜ失敗し続けてきたか（振り返り）
- **非同期タスクのブラックボックス化**: BackgroundTasks の例外・失敗がレスポンスに見えず、「成功したようで無変更」ケースが多発。  
- **観測ポイント不足**: task_id・状態管理・構造化ログが無く、どのフェーズで落ちたか追えない。  
- **入力バリデーションの欠如**: Gemini応答の必須欠損/JSON崩れを検知せず、黙って捨てる挙動。  
- **slug安定性の軽視**: title 変動で slug が変わり、upsert が別行になって「更新されない」と誤認。  
- **rate limit/権限エラーの無視**: 429/403 がログだけで終わり、再試行やオペレーションへのフィードバックが無かった。  
- **マージ仕様の曖昧さ**: fill_missing_only の意図と実装（浅いマージ）がずれ、配列/構造体が消える。  

## ベストプラクティス（当面の指針）
- **観測可能性**: すべての再生成タスクに task_id を払い、`status`, `error`, `slug`, `mode`, `duration_ms` を構造化ログ＆（将来）タスクAPIで確認可能にする。  
- **入力ガード**: Gemini応答は jsonschema で検証。必須欠損・型不正は 422/failed とし、DB 書き込みしない。  
- **slug固定とキー設計**: regen では既存 slug を強制。title 更新は専用エンドポイントを別途用意する。`source_url` を持つ場合はそれを衝突キーに。  
- **マージポリシーの明文化**: fill_missing_only は「欠損のみ上書き + keywords union」。full は上書き。ただし id/slug/created_at は不変。  
- **レートリミット耐性**: 429 を検知し、短時間スロットルやバックオフを入れる。連続 generate を避け、まずキャッシュ検索する運用を徹底。  
- **権限チェックの早期化**: 起動時に GEMINI/Supabase キーを検証し、欠落なら即失敗させる。  
- **分離とリスク低減**: Link Resolver を別キューに分け、URL検証失敗で本体がロールバックしないようにする。  
- **テストの整備**: モックで 429, JSON崩れ, slugズレ, fill_missing_only マージを再現するユニットテストを追加。  

## すぐやるアクション（優先順）
1. タスクID導入（インメモリでも可）＋構造化ログで status/error を可視化。  
2. Gemini応答の jsonschema バリデーションと必須欠損の明示エラー化。  
3. regen 時の slug 固定と `fill_missing_only` プロンプトバリアント追加。  
4. 429 簡易スロットル（短時間の連続呼び出しを間引き or sleep）。  
5. structured_data のマージ方針を keywords union に決める。  

## 実装バックログ（ファイル対応表）
- `app/services/game_service.py`  
  - タスクID生成・状態管理（暫定: インメモリ dict / 将来: Supabase tasks テーブル）。  
  - try/except で task status と error を記録。slug 強制固定。structured_data keywords union マージ。  
  - jsonschema バリデーション導入ポイント（Gemini出力直後）。  
- `app/core/gemini.py`  
  - 429/5xx ハンドリングとリトライ/スリープ（短期はリトライなしで明示失敗）。  
  - JSON整形/クレンジング強化（フェンス検出、先頭`{}`抽出失敗時のエラー化）。  
- `app/prompts/prompts.yaml`  
  - `metadata_generator_fill_missing` / `metadata_critic_fill_missing` バリアント追加。  
  - URL信頼度の上限設定と required フィールド指定を再確認。  
- `app/core/logger.py`  
  - 構造化ログ（json formatter） or key/value 形式を追加。task_id/slug/mode/status を必ず出す。  
- `app/core/settings.py`  
  - 必須 env の起動時検証。None のままなら早期に例外を投げる。  
- `tests/`  
  - Geminiレスポンスをモックしたユニットテスト（成功・必須欠損・429・JSON崩れ）。  
  - `_merge_fields` の挙動テスト（fill_missing_only true/false、structured_data merge）。  

## ロールアウト案
1. **短期**: ログ＋バリデーション＋slug固定＋fill-missingプロンプト実装。  
2. **中期**: `task_id` 付き結果確認 API / タスク永続化（Supabase テーブル or キャッシュ）。  
3. **長期**: Link Resolver のキュー化とエラー分離、通知チャネル（WebSocket/SSE/ポーリング）の検討。  

## 未決定・要議論
- タスク永続化の方式（Supabase テーブル vs SQS 等）。
- 同時実行上限とキューイング戦略（rate limit とのバランス）。
- `structured_data` の深いマージポリシー（配列の結合 or 置換）。
- 失敗時のユーザー通知方法（WebSocket/SSE/ポーリング）。

このドキュメントは「ありたい姿」のメモ。実装のたたき台として随時更新する。
