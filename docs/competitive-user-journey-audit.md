# 競合ユーザージャーニー監査

更新日: 2026-08-21

## 目的

ボドゲのミカタを「情報量の多いボードゲームDB」にするのではなく、ユーザーが **Find → Decide → Learn → Ask** を短時間で完了できるプロダクトとして改善するための監査基準。

## 競争相手はサービスではなくユーザーの用事で定義する

| Journey | ユーザーの用事 | 代表的な代替 | 現在のボドゲのミカタ | Gap |
| --- | --- | --- | --- | --- |
| Find | 人数・時間・名前などから候補を探す | BoardGameGeek等のcatalog/search | `q`, players, time, tier, sort のserver-side directory検索 | 小 |
| Decide | 候補を並べて今遊ぶ1本を決める | catalog/recommendation tools | 最大3件の比較、人数・時間・概要・mechanics | 中 |
| Learn | 選んだゲームを実際に始められる状態になる | 公式rulebook、tutorial services | 30秒概要、QuickRules、準備・流れ・終了、詳細ルール、図解 | 中 |
| Ask | プレイ中の具体的な疑問を、そのゲームの根拠付き回答へ解決する | 公式FAQ/errata、rulebook検索、Web検索 | PR #362でevidence-backed Rule Askの最初のvertical sliceを実装中 | **実装中** |

## 現在確認できる実装

Directory (`frontend/src/App.jsx`) は検索、人数、時間、戦略tier、sortをURL stateと同期し、APIへserver-side queryとして送る。最大3ゲームを選び比較画面へ進める。

Game page (`frontend/src/pages/GamePage.jsx`) は基本情報、30秒概要、QuickRules、詳細ルール、準備・流れ・終了、戦略、レビュー、関連ゲーム、図解、source/trust情報を持つ。

AskはPR #362で、reviewed curated rule guideを回答authorityとするfail-closedな最初のvertical sliceを実装中。外部LLM/APIは追加しない。

## 最優先の未完了journey: Ask

### Job

プレイ中のユーザーが、例えば次のような疑問を持ったときにゲームページから離れず解決できること。

- このカード/効果はいつ発動するか
- 同点ならどう処理するか
- 4人時だけ変わる処理は何か
- 終了条件を満たしたのはいつ判定するか
- FAQ/errataで本文から裁定が変わっていないか

### 必須trust contract

Askは自由生成チャットを先に置かない。回答可能範囲はcanonical game identityと、そのゲームへ紐付いた確認済みsource/evidenceに限定する。

最低限、回答には以下を保持する。

- game slug / canonical identity
- answer text（公式本文と要約を区別）
- evidence target（rule/FAQ/errataの該当箇所）
- source URL
- source type
- source revision/version/date（取得可能な場合）
- review/verification state

十分な根拠がない場合は推測せず「確認できない」と返す。

### MVP acceptance criteria

1. verified curated gameを1作品以上選び、ゲームページから自然言語または定型質問でrule questionを入力できる。
2. 回答はそのゲームのcanonical evidenceだけから取得される。他ゲームのrecordを横断混入しない。
3. 回答から該当するrule/FAQ/errata evidenceへ直接辿れる。
4. evidence不足時はfail-closedする。
5. 少なくとも setup / turn flow / legal action / scoring-or-end / exception の代表質問をregression testする。
6. mobileでゲームページ→質問→回答→根拠確認まで完了できる。
7. productionで同じcritical pathをread-backする。

## 今は作らないもの

- BGG規模の百科事典・community
- オンライン対戦基盤
- collection / play logging / score statistics の全面実装
- source evidenceを持たない汎用AIチャット
- recommendationのためだけの新しい独立サービス

これらはFind → Decide → Learn → Askの完了率を直接改善する証拠が出るまで優先しない。

## 計測

閲覧数だけで評価しない。将来のjourney telemetryでは、少なくとも directory result → game detail、compare → selected game、game detail → Learn interaction、Ask submitted → evidence-backed answer / unresolved を区別する。Visitors/Pageviewsの正準履歴は Issue #361 のworklineと接続し、request countをVisitorsとして扱わない。
