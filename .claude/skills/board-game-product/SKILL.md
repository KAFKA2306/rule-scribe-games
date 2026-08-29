---
name: board-game-product
description: ボドゲのミカタを、正しいルール・使いやすさ・検索流入・購入導線・production reliabilityの観点で改善する。
---

# Board Game Product

共通の実行手順は `AGENTS.md` を正本とする。このSkillではボードゲーム固有の判断だけを追加する。

## 優先順位

次の期待効果が大きいplayer-facing問題を優先する。

1. acquisition / discovery / search
2. rule correctness / trust
3. setup / play clarity
4. retention
5. 既存affiliate等のmonetizable flow
6. production reliability / operating cost

同じ問題を扱うcurrent Issue/PRが有効なら続ける。過去の作業履歴を再構築するために大量のコメントを読む必要はない。current main、production、一次資料から状態を確認する。

## ルールと版の扱い

- publisher / designer等の公式一次資料を優先する。
- product、edition、language、platform、revision、expansion、FAQ、errataを明示的に分ける。
- 公式ルールと要約・翻訳・解釈を別物として保持する。
- 公式根拠が不足する項目は埋めない。model memoryやcommunity summaryで再構築しない。
- living rulesはrevisionを上書きせず、どのrevisionを表示しているか保持する。

## 捏造を通さない実装制約

- networking pathを増やさず、repositoryの既存正準経路を使う。
- broad `try-except`、silent fallback、default substitutionでmissing/invalid evidenceを成功へ変換しない。
- unknown、source mismatch、edition ambiguity、invalid production stateは明示的なfailureまたはblocked stateにする。
- authoritative schema/runtimeで検証できる値にmanual shadow mappingを作らない。
- resilienceは、確認済みのproduction要件を満たし、失敗を隠さない場合だけ許可する。

## ゲームデータ変更

既存のstructured model、RuleSet、RuleNode、Claim、EvidenceBinding、metadata evidence、RuleOps等を再利用する。複数ゲームを同じgeneric pipelineで扱えるならbatch化し、個別ゲーム専用script/test/workflowを残さない。

既存のaffiliate/purchase pathは意図した変更でない限り保持する。売上やconversionの改善は実測なしに主張しない。

## 完了判定

`AGENTS.md` の検証経路に従い、最後にplayer-facing成功条件をproductionで確認する。確認できなければ `UNVERIFIED` とする。

報告は、Before→After、trusted evidence、根拠のあるmonetization path、PR/CI/merge/production、削除した重複・手作業、残るUNVERIFIED、次の最大価値問題だけに絞る。
