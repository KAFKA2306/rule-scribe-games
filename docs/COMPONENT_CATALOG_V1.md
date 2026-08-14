# Component Catalog v1

## Purpose

Ontology v2で、意味概念とゲーム内実体を分離する正準component layerです。

```text
Game
  └─ RuleSet
      ├─ Rule Graph
      ├─ Concept Taxonomy
      └─ Component Catalog
          ├─ ComponentSet
          ├─ PropertyDefinition
          └─ Component
              ├─ ComponentProperty
              └─ Ability
```

`Concept` は「冒険者カード」「資源トークン」「ドロー」のような意味・分類を表します。`Component` は特定RuleSetに実在する個々のカード種類、タイル種類、トークン、ダイス等を表します。個々のComponentを`ConceptType.COMPONENT`へ大量登録しません。

## RuleSet boundary

Component Catalogは必ず#174の`ruleset_id`に所属します。同じ`component_id` / canonical nameを物理版とdigital版で保持しても、property/abilityを上書きしません。

Game直下へcomponent truthを保存せず、APIも`rule_set_id`を明示必須とします。

## Component kinds

v1:

- card
- tile
- token
- die
- board
- figure
- sheet
- role
- marker
- track
- other

これは表示カテゴリであり、ゲーム固有の属性列ではありません。

## ComponentSet

Componentを意味のある集合へまとめます。

- stable `component_set_id`
- `ruleset_id`
- canonical name
- optional kind
- optional parent set
- verification/source linkage

例: `adventurers`, `quest-cards`, `terrain.tiles`, `resource.tokens`。

## PropertyDefinition

YROの`faction`や`combat_value`のようなgame-specific propertyをglobal `components` tableのnullable columnにはしません。RuleSetごとのPropertyDefinitionで宣言します。

Fields:

- stable `property_key`
- localized `labels`
- `value_type`
- `cardinality`
- optional `unit`
- optional enum values
- `filterable`
- `sortable`
- verification/source linkage

Value types:

- text
- integer
- number
- boolean
- enum
- concept_ref
- component_ref

Cardinality:

- one
- many

Pydantic contractとPostgreSQLのgeneric typed-value columnsの両方で型を表現します。YRO専用、IPSO専用などのproperty columnは追加しません。

## Typed property storage

`component_properties` はゲーム固有列ではなく型ごとのstorage columnを持ちます。

```text
text_value
integer_value
number_value
boolean_value
enum_value
concept_ref_id
component_ref_id
```

1 rowではexactly one typed valueだけを許可します。`value_type` / `cardinality` はPropertyDefinitionへの複合FKで一致させ、`cardinality=one`はpartial unique indexで1値に制限します。`component_ref`は同じRuleSet内のComponentへだけ参照できます。

## Component

- stable `component_id` within RuleSet
- `component_set_id`
- canonical name
- kind
- optional quantity
- typed properties
- abilities
- Concept links
- RuleNode links
- verification/source linkage

表示名はidentityではありません。同名componentでもRuleSetが異なれば別versionのproperty/abilityを保持できます。

## Ability

printed component textとnormalized rule truthを分離します。

Abilityは:

- stable `ability_id`
- optional printed/source text
- optional normalized label
- Concept backlinks
- RuleNode backlinks
- verification/source linkage

を持ちます。printed text自体をRuleNode statementの代替truthとして扱いません。

## Concept / Rule bridges

Canonical bridge:

```text
Component -> component_concepts -> Concept
Component -> component_rule_nodes -> RuleNode
Ability -> component_ability_concepts -> Concept
Ability -> component_ability_rule_nodes -> RuleNode
```

Concept definitionとComponent instance dataを同じrowへ押し込みません。

## Evidence semantics

#175導入前のv1でも`verification_status`と`source_ids`を保持します。

- unknown
- source_bound
- verified
- rejected

`source_bound` / `verified` は空の`source_ids`では保存・model validationできません。source不明propertyをverifiedへ昇格させません。

#175ではこの粗いsource bindingをfield/claim-level EvidenceBindingへ拡張します。v1の`source_ids`を「entity全体が正しい」という意味にはしません。

## API

全routeでRuleSetを明示します。

```http
GET /api/games/{slug}/component-sets?rule_set_id=...
GET /api/games/{slug}/components?rule_set_id=...&component_set_id=...&kind=...
GET /api/games/{slug}/components/{component_id}?rule_set_id=...
```

Catalog未登録時はlist/set APIを`not_available`でfail-closedにし、legacy keywordやLLMからcomponentを推測生成しません。

## Required generic fixtures

v1 contract testは最低限:

1. card-centric: enum + integer + concept_ref
2. tile-centric: numeric property
3. dice/token-centric: component_ref + many cardinality

を同じmodelで検証します。

## PostgreSQL

Migration: `backend/app/db/migrations/014_component_catalog.sql`

主要tables:

- component_catalogs
- component_sets
- component_property_definitions
- components
- component_properties
- component_abilities
- component_concepts
- component_rule_nodes
- component_ability_concepts
- component_ability_rule_nodes

全tableはRLSを有効化し、server-side service pathから読みます。public clientへ暗黙read policyを追加しません。

## Migration / cleanup

014はadditive migrationです。既存Game / Rule Graph / Concept / UIを変更せず導入できます。

- legacy `structured_data.mechanics`へComponentをdual-writeしない
- game-specific component tableを増やさない
- component data未登録ゲームは既存UIを変更しない
- UIは#176でComponent Catalog availabilityを見て段階導入する
- data ingestionは#178でevidence-gated workflowへ一般化する

## Standards

- W3C SKOS Reference: https://www.w3.org/TR/skos-reference/
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- W3C SHACL: https://www.w3.org/TR/shacl/

## Related

- #148 Ontology v2
- #149 Rule Graph
- #150 Concept taxonomy
- #173 Component Catalog
- #174 RuleSet identity
- #175 Claim/Evidence Binding
- #176 Components UI
- #178 component ingestion
