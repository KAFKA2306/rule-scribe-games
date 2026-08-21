# 競合ユーザージャーニー監査

更新日: 2026-08-21

## 目的

ボドゲのミカタを「情報量の多いボードゲームDB」にするのではなく、ユーザーが **Find → Decide → Learn → Ask** を短時間で完了できるプロダクトとして改善するための監査基準。

## 競争相手はサービスではなくユーザーの用事で定義する

| Journey | ユーザーの用事 | 現在のボドゲのミカタ | Gap |
| --- | --- | --- | --- |
| Find | 人数・時間・名前などから候補を探す | `q`, players, time, tier, sort のserver-side directory検索 | 小 |
| Decide | 候補を並べて今遊ぶ1本を決める | 最大3件の比較、人数・時間・概要・mechanics | 中 |
| Learn | 選んだゲームを実際に始められる状態になる | 30秒概要、QuickRules、準備・流れ・終了、詳細ルール、図解 | 中 |
| Ask | プレイ中の具体的な疑問を、そのゲームの根拠付き回答へ解決する | PR #362でevidence-backed Rule Askの最初のvertical sliceを実装中 | **実装中** |

## 現在確認できる実装

Directory (`frontend/src/App.jsx`) は検索、人数、時間、戦略tier、sortをURL stateと同期し、APIへserver-side queryとして送る。最大3ゲームを選び比較画面へ進める。

Game page (`frontend/src/pages/GamePage.jsx`) は基本情報、30秒概要、QuickRules、詳細ルール、準備・流れ・終了、戦略、レビュー、関連ゲーム、図解、source/trust情報を持つ。

AskはPR #362で、reviewed curated rule guideを回答authorityとするfail-closedな最初のvertical sliceを実装中。外部LLM/APIは追加しない。

## 最優先の未完了journey: Ask

プレイ中のユーザーが、例えば同点処理、手番中の行動、終了条件、上限などをゲームページから離れず確認できることを目標とする。

### 必須trust contract

Askは自由生成チャットを先に置かない。回答可能範囲はcanonical game identityと、そのゲームへ紐付いたreviewed curated guideに限定する。

- answer textは公式本文ではなく登録済み要約として表示する
- source URL
- source type
- rule version
- evidence locator
- game slug

十分な根拠がない場合は推測せず未解決として返す。

### MVP acceptance criteria

1. curated gameを1作品以上選び、ゲームページから質問できる。
2. 回答はそのゲームのguideだけから取得され、他ゲームのguideを横断混入しない。
3. 回答から公式sourceへ辿れる。
4. evidence不足時はfail-closedする。
5. turn action / scoring / end condition / exception / unresolved setupをregression testする。
6. mobileでゲームページ→質問→回答→根拠確認まで完了できる。
7. productionで同じcritical pathをread-backする。

## 今は作らないもの

- BGG規模の百科事典・community
- オンライン対戦基盤
- collection / play logging / score statistics の全面実装
- source evidenceを持たない汎用AIチャット
- recommendationのためだけの新しい独立サービス

## 計測

閲覧数だけで評価しない。将来のjourney telemetryでは、directory result → game detail、compare → selected game、game detail → Learn interaction、Ask submitted → evidence-backed answer / unresolved を区別する。Visitors/Pageviewsの正準履歴は Issue #361 のworklineと接続し、request countをVisitorsとして扱わない。
