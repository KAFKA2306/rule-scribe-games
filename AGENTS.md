# AGENTS.md

このrepositoryでは、過去チャットや長いIssue履歴を前提にしない。短いコンテキストでも、current stateから安全に再開できることを優先する。

## 最初に確認する順序

1. current `main` のSHAとopen PRを確認する。
2. 同じ問題を扱うopen Issue/PRがあれば本文だけ先に読む。全コメント履歴は、現在状態を確定できない場合だけ読む。
3. ユーザーが実際に見るcanonical productionとreal dataを確認する。
4. ゲームの事実が必要ならpublisher/designer等の公式一次資料を確認する。PDFは必要なページを実際に読む。
5. 変更対象のcode/data/workflowだけを読む。
6. 変更前に、観測可能なユーザー向け成功条件を1つ書く。

状態の正本は用途ごとに分ける。

- code/schema/workflow: current `main`
- 実ユーザー向け状態・利用実績: canonical production / real data
- ゲームのルール・版・商品情報: 公式一次資料
- 作業の調整: current open Issue/PR

過去チャット、closed Issue、古いPR、古いコメントは正本ではない。上記と矛盾する場合は現在状態を優先する。

## 必須ルール

- public Web siteがある場合、`README.md` の先頭行にcanonical production URLを完全な `https://...` の平文で置く。
- 公式ルールと、要約・翻訳・解釈・推薦・生成文を分離する。
- product / edition / language / platform / revision / expansion / FAQ / errataを混ぜない。不明なら推測せず `UNVERIFIED` またはblockedにする。
- fixture/synthetic dataはtest専用。本番の問題数、品質、利用実績の代用にしない。
- 既存実装と標準機能を優先し、`DELETE > MERGE > REPLACE > ADD`。重複helper/workflow/docs、個別ゲーム専用one-off script、生成可能な成果物を増やさない。
- networking pathを増やさない。既存の正準経路を使う。
- broad `try-except`、silent fallback、根拠のないdefault、壊れたデータを成功扱いするretryを追加しない。失敗は明示する。
- 同じ意味のshadow mappingや第二のtruth storeを作らない。

## 実装と検証

`Taskfile.yml` と既存schema/validator/generatorを優先する。ゲーム固有の事実は既存schemaで表現できる限りstructured dataへ入れ、専用処理を作らない。

変更は可能な範囲で次まで完了する。

`validation/test → PR → exact-head CI → merge → main read-back → production release → public read-back`

PRのCI成功とproduction成功は別物。merge後にproductionを直接確認できなければ `UNRELEASED/UNVERIFIED` とする。CIを弱めたりskipして通さない。

## コンテキスト節約

最初からrepository全体、全Issue、全履歴を読まない。上の開始順序で必要最小限を取得し、未解決の曖昧さがある場合だけ範囲を広げる。

同じ修正が繰り返される原因を見つけたら、その場のpatchではなく既存の `AGENTS.md`、CI、schema、test、canonical docsの最小authorityへ統合する。新しい管理層は作らない。
