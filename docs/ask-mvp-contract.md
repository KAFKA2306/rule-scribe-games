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

- `frontend/src/lib/ruleAsk.js`: reviewed curated guideだけを検索するdeterministic selector
- `frontend/src/components/game/RuleAskPanel.jsx`: `/games/:slug` の質問UI
- `frontend/src/main.jsx`: game routeへのmount
- `frontend/tests/rule_ask.spec.js`: answered / unresolved / cross-game / mobile regression

外部LLM/API、dependency、backend serviceは追加しない。

最初の実動対象は `splendor`。turn action、scoring、end condition、tie/token limitを回答し、reviewed setup evidenceがない質問は`unresolved`にする。

## Completion gates

- exact-head CI PASS
- preview/deployed critical-path read-back
- merge
- production read-back
