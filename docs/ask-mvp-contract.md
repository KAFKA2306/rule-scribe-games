# Evidence-backed Rule Ask MVP

## User task

ゲーム中の具体的な疑問を、そのゲームに紐付いた確認済みルール根拠だけで解決する。

## Product boundary

これは汎用チャットではない。入力された質問に対して、canonical game identityを固定したまま、そのゲームのreviewed curated rule guideだけを検索する。

根拠が十分でなければ回答を生成せず、未解決として返す。表示する回答は登録済み要約であり、公式本文そのものとは区別する。

## Response contract

- `game_slug`: canonical game identity
- `question`: user input
- `status`: `answered` or `unresolved`
- `answer`: evidenceから導出した登録済み要約。`unresolved`ではnull
- `evidence`: answerを支持する1件以上のevidence target
- evidenceごとにsource URL / source type / locator / revision evidenceを可能な範囲で保持する
- verified fact、公式本文、要約・説明をUIで混同しない

## Implemented vertical slice

`frontend/src/lib/ruleAsk.js` が既存 `curatedRuleGuides` を唯一の回答authorityとして利用し、質問意図を決定的に分類する。外部LLM/APIは使わない。

`frontend/src/components/game/RuleAskPanel.jsx` を `/games/:slug` に表示し、回答には公式source URL・rule version・evidence locatorを付ける。

最初の実動対象は `splendor`。以下を回帰対象にする。

1. turn action → answered
2. scoring → answered
3. end condition → answered
4. exception / tie / token limit → answered
5. setup → reviewed setup evidenceが現在ないため `unresolved`

別slugではSplendorのguideを再利用しないcross-game contamination testを持つ。

## Fail-closed cases

- reviewed curated guideが存在しない
- evidence targetが存在しない
- questionに対応する十分なevidenceがない

上記では推測回答を返さない。

## UI critical path

`/games/:slug` → 「ルールを質問」 → 質問入力 → 回答または「確認できません」 → 公式ルール根拠を開く。

mobile viewportでもこの順序をregression testする。

## Current completion state

実装と回帰テストはPR branchに存在する。完了には exact-head CI、preview/deployed critical-path read-back、merge後のproduction read-back が必要。
