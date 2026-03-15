# Tests (`tests/`)

このディレクトリには、アプリケーションのテストスイートが含まれています。

## [`test_llm_flow.py`](./test_llm_flow.py)
実際のGemini APIを使用して、AIエージェントの処理フロー（検索→生成→検証）を通しでテストする統合テストスクリプトです。

### 実行方法
```bash
uv run python tests/test_llm_flow.py --api-key "$GEMINI_API_KEY" --query "カタン"
```

### 仕組み
1. `gemini.py` と `prompts.py` を実際に使用してGemini APIに問い合わせます。
2. 返ってきた構造化JSONが必須フィールド（`title`, `summary`, `rules_content`）を含んでいるか検証します。
3. エラーが発生した場合は即座にクラッシュします（Crash-only設計）。

## `logs/`
`test_llm_flow.py` の実行結果（生成されたJSON全体など）がタイムスタンプ付きのJSONファイルとして保存されるディレクトリです。
- ファイル名形式: `YYYYMMDDHHMM.json`
- CI/CDパイプラインでのアーティファクト保存先としても機能します。

## 注意点
- **APIコスト**: 実際のAPIコールが発生するため、課金対象となります。頻繁な実行には注意してください。
- **環境変数**: `GEMINI_API_KEY` が必須です。
