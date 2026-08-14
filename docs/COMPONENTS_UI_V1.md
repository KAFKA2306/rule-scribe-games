# Components UI v1

## Purpose

#173 Component CatalogをGamePageへ表示する汎用UI契約です。ゲームごとのカード列・タイル列・専用JSXは作らず、`ComponentSet / PropertyDefinition / Component`を入力として同じrendererを利用します。

```text
Game
  └─ RuleSet
       └─ Component Catalog
            ├─ ComponentSet
            ├─ PropertyDefinition
            └─ Component + Claim/Evidence
                    ↓
             Components UI
```

## Availability contract

GamePageは最初に次の軽量APIだけを確認します。

```http
GET /api/games/{slug}/component-catalog-availability
```

- catalogが1つ以上存在する場合だけCOMPONENTSタブを表示する。
- catalogが無い場合はタブを表示せず、full component APIを呼ばない。
- 複数RuleSetにcatalogがある場合、RuleSetを暗黙選択しない。ComponentsPanelで明示選択する。

COMPONENTSタブを開いた時だけ次を取得します。

```http
GET /api/games/{slug}/component-catalog?rule_set_id=...&limit=100&offset=...
```

## Catalog page

1ページで以下を返します。

- ComponentSet
- PropertyDefinition
- full Component
- ComponentProperty
- Ability
- Concept / RuleNode references
- property / ability field-level evidence summary
- total / limit / offset

detailごとのN+1 requestを避けるため、backendはpage内のproperty / ability / bridge / evidenceをbulk loadします。

frontendは100件単位で全pageを取得し、filter/sortをcatalog全体に適用します。125件fixtureで2 page取得を固定しています。

## Generic rendering

`PropertyDefinition.value_type`により表示・filterを生成します。

| Type | Display | Filter |
|---|---|---|
| text | text | substring search |
| integer | number + unit | min/max |
| number | number + unit | min/max |
| boolean | YES / NO | tri-state select |
| enum | enum value | enum select |
| concept_ref | stable concept ID | text/ref display |
| component_ref | stable component ID | text/ref display |

未知の将来型はクラッシュさせず、表示・filter対象からfail-closedで除外します。

Sortはcanonical nameに加え、`PropertyDefinition.sortable=true`のfieldだけを候補にします。

## Evidence semantics

Component entity-levelの`source_ids`だけではverified badgeを出しません。

propertyは#175 Claim/Evidenceをcurrent ordinal/valueと照合し、次で表示します。

- `VERIFIED`: current valueの全ordinalがaccepted + supports + no contradiction
- `CONTESTED`: current valueにaccepted contradictionがある
- `UNVERIFIED`: 上記以外

古いvalueを支持するClaim、candidate/unknown/rejected Claimはcurrent fieldをverifiedへ昇格させません。

Abilityはprinted textとnormalized interpretationを別Evidence stateとして保持します。

詳細画面からClaim trace、Concept API、Rule evidence traceへ辿れます。

## UX

- card / tile / token / die等を同じcard rendererで表示
- ComponentSet group filter
- global search
- schema-driven property filters
- schema-driven sort
- quantity表示
- imageは任意。画像無しでも完全に利用可能
- native button/select/inputを使いkeyboard操作可能
- detailは`role=dialog`の非modal region
- 375 / 768 / 1440pxでhorizontal page overflow禁止
- 100+ componentsをpagination取得して全体filter可能

## Tests

- card / tile / token / die generic renderer helper
- enum / integer / boolean / text filter
- sortable property
- unknown property type fail-closed
- 100+ page offsets
- missing catalog -> no tab / no full catalog request
- 125 components -> 2 page load
- keyboard open detail
- field evidence trace link
- no-image detail
- 375 / 768 / 1440 responsive geometry
- CI screenshot artifacts for each responsive project

## Related

- #148 Ontology v2
- #151 Presentation Projection
- #173 Component Catalog
- #174 RuleSet identity
- #175 Claim/Evidence Binding
- #176 Components UI
- #177 YRO pilot
