# Evidence-backed Rule Ask MVP

## User task

ゲーム中の具体的な疑問を、そのゲームに紐付いた確認済みルール根拠だけで解決する。

## Product boundary

これは汎用チャットではない。入力された質問に対して、canonical game identityを固定したまま、そのゲームのrule / FAQ / errata evidenceだけを検索する。

根拠が十分でなければ回答を生成せず、未解決として返す。

## Response contract

- `game_slug`: canonical game identity
- `question`: user input
- `status`: `answered` or `unresolved`
- `answer`: evidenceから導出した短い説明。`unresolved`ではnull
- `evidence`: answerを支持する1件以上のevidence target
- evidenceごとにsource URL / source type / locator / revision evidenceを可能な範囲で保持する
- verified fact、公式本文、要約・説明をUIで混同しない

## First vertical slice

既存curated gameのうち、一次sourceとstructured rule evidenceが十分な1作品を選ぶ。以下の5カテゴリを固定fixtureとして持つ。

1. setup
2. turn flow
3. legal action
4. scoring or end condition
5. exception / tie / edge case

各fixtureは expected evidence target を持つ。文字列一致だけでなく、別ゲームのevidenceが混入しないことをassertする。

## Fail-closed cases

- game identityがunverified
- sourceが対象gameへ結び付いていない
- evidence targetが存在しない
- questionに対応する十分なevidenceがない
- conflicting evidenceが解消されていない

上記では推測回答を返さない。

## UI critical path

`/games/:slug` → 「ルールを質問」 → 質問入力 → 回答または「確認できません」 → 根拠箇所を開く。

mobile viewportでもこの順序で完了できること。

## Completion

- API/selector contract test
- 5カテゴリのgame-specific regression
- cross-game contamination regression
- unresolved regression
- game page UI regression
- exact-head CI
- production read-back
