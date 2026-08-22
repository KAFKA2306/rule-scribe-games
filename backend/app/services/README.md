# Services (`app/services/`)

`app/services` は、canonical dataを読み書き・投影するapplication service層です。

## 正準経路

- `directory_query.py`: directoryのsearch/filter/sort/pagination。
- `game_service.py`: game rowのreadと、認証済みeditorによるidentity-safe manual metadata update。
- `rulesets.py`: work/edition/platform/versionを分離したRuleSet read。
- `presentation_projection.py`: accepted claim + supporting evidence + RuleNodeからユーザー向けルール表示を導出。
- `concept_taxonomy.py`: canonical Concept/glossary。
- `rule_graph.py`: RuleSet-bound rule graph。
- `evidence.py`: claim/evidence trace。
- `component_catalog.py`: RuleSet-bound components。
- `catalog_access.py`: catalog mutation audit。

## 書き込み境界

ゲーム固有ルールをruntimeでAI生成してproductionへ追加・再生成するserviceは持ちません。source-backed game contentは `data/curated-games/<slug>.json` を正準入力とし、PR merge後のrelease workflowがproduction publicationを担当します。

ユーザー向けルール表示は `games.rules_content` 等の互換本文へfallbackせず、選択されたRuleSetのpresentation projectionが利用可能な場合だけ表示します。未整備は未整備として返します。
