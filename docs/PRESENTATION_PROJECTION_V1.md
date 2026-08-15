# Presentation Projection v1

## Purpose

UI用の表示文を第二のtruth storeとして保存せず、Ontology v2のcanonical dataから**read-timeで決定論的に生成**する契約です。

```text
Game
  └─ RuleSet
       ├─ RuleNode <- accepted Claim <- supporting EvidenceBinding
       └─ Concept <- verified RuleNodeConcept / GameConcept
             ↓
      Presentation Projection
             ↓
   UI / SEO / JSON-LD adapter
```

## Core rules

- `rule_set_id` は必須。複数版・BGA版・物理版を暗黙選択しない。
- ProjectionはDBへ保存しない。canonical Rule/Concept更新を次回readへ即反映する。
- Rule truthは `Claim.lifecycle_status=accepted` かつ `supports` が存在し、`contradicts` が無い場合だけ採用する。
- Claimの `normalized_payload.statement` と現在の `RuleNode.normalized_statement` が完全一致しない場合、そのevidenceはstaleとして採用しない。
- 同じRuleNodeに複数のaccepted/supported Claimが存在する場合、claim ID順に現在のRuleNode statementと一致するClaimを選ぶ。古いClaimが先にあっても現行Claimを隠さない。
- `verification_status`、source URL、publisher identityだけではRuleをverified表示へ昇格させない。
- `variant` RuleNodeをbase Quick Rulesへ混ぜない。variantは明示的なderived/variant RuleSetを選択して扱う。
- unknown / unsupported / stale / contested contentを補完生成しない。
- legacy `structured_data` をcanonical Projectionの入力にしない。

## API

```http
GET /api/games/{slug}/presentation?rule_set_id=...&language_code=ja
```

ゲーム自体が存在しない場合は404。ゲームは存在するがcanonical projection inputが不足する場合は200 + `status=not_available` とする。

## Sections

### QUICK RULES

accepted + supported + current statement一致を満たすbase RuleNodeから生成する。

対象:

- setup
- phase / turn / action
- condition / effect
- round_end
- exception / targeting / conflict_resolution
- scoring
- game_end / victory

### SETUP / GAME FLOW / END CONDITION / SCORING

QUICK RULESと同じcanonical ProjectedRuleをtype別に再投影する。同じRuleNodeを別本文へコピーしないため、詳細ルール更新とsummaryの乖離を防ぐ。

### GLOSSARY

次の全条件を満たすConceptだけを表示する。

- selected RuleSetの `rule_node_concepts` にverified linkがある
- game-level `game_concepts` がverifiedかつusage roleが`core`または`glossary`
- Conceptが`active`かつ`verified`
- requested languageのpreferred label、または英語preferred labelが存在する

RuleSetに紐づかないgame-level glossaryだけを推測表示しない。

### SYNOPSIS

v1ではcanonical synopsis claim contractが未定義のため `not_available`。

### COMMON ERRORS

v1ではcanonical misconception relation layerが未実装のため `not_available`。legacy `structured_data.rule_mistakes` をtruthへ昇格しない。

### PRO TIPS

v1ではcanonical Advice/Strategy layerが未実装のため `not_available`。legacy `structured_data.pro_tips` をtruthへ昇格しない。

## Evidence trace

各ProjectedRuleは以下を保持する。

- canonical `rule_id`
- RuleNode type
- current canonical text
- sequence
- accepted `claim_id`
- `claim_lifecycle=accepted`
- `support_status=supported`
- supporting `source_ids`（最低1件）

Source URL等の詳細は#175 Evidence APIでtraceできる。ProjectionはEvidenceの複製storeにならない。

## SEO / JSON-LD

`projection_to_json_ld(projection, title)` がPresentation ProjectionからJSON-LDを決定論的に生成する。

- selected RuleSetは`PropertyValue(propertyID=ruleSet)`としてidentityを保持する
- QUICK RULESは`CreativeWork`として`subjectOf`へ投影する
- GLOSSARYは`DefinedTerm`として`about`へ投影する
- unavailableなCOMMON ERRORS / PRO TIPS等はJSON-LDへ混入しない
- JSON-LD自体はDBへ保存しない

既存SEO rendererは段階移行対象であり、#153のlegacy cleanupまでに同じProjection入力へ寄せる。

## Failure semantics

- Game missing -> 404
- unknown/wrong RuleSet -> `not_available`
- no accepted evidence-backed rules/concepts -> `not_available`
- backend read failure ->例外を`not_available`へ潰さず、server failureとして区別

## Tests

- accepted + supported only
- candidate / unknown / rejected exclusion
- contradiction exclusion
- stale Claim exclusion after RuleNode update
- stale Claimの後ろに現行Claimがある場合の選択
- variant exclusion from base projection
- explicit RuleSet required
- Evidence state / supporting source cardinality
- JSON-LDがcanonical Rule/Conceptだけを含む
- missing projection != missing game
- section status contract

## Related

- #148 Ontology v2
- #149 Rule Graph
- #150 Concept taxonomy
- #151 Presentation Projection
- #175 Claim/Evidence Binding
- #176 Components UI
- #153 legacy migration
