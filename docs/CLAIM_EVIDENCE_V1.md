# Claim / Evidence Binding v1

## Purpose

Ontology v2のRule / Component / metadataを、source URL単位ではなく**claim/field単位**で根拠へ結び付けるcanonical provenance contractです。

```text
RuleSet
  └─ Claim -> concrete target
       └─ EvidenceBinding
            ├─ EvidenceSource
            └─ optional SourceLocator
```

Sourceがpublisher公式であることと、特定claimがそのsourceに支持されていることを同一状態として扱いません。

## Canonical entities

### EvidenceSource

Source document / endpoint / replay等のidentityです。

- stable `source_id`
- URL または document identity
- source type
- optional publisher/platform/language/revision/date
- retrieval metadata
- `trust_metadata`

`trust_metadata`は#139のsource-trust semanticsを保持・接続するための別境界です。EvidenceBindingの`supports`と混同しません。公式sourceというmetadataだけで全fieldをverifiedへ昇格させません。

### SourceLocator

Source内部の具体的位置を確認できる場合だけ作成します。

候補:

- page number
- section heading
- anchor
- selector
- structured endpoint path
- external table/replay reference

位置を確認できない場合はlocatorを作らず、EvidenceBindingの`locator_id=NULL`を正準とします。架空のpage/sectionを補完しません。

### Claim

Sourceから評価する最小の事実単位です。

- stable `claim_id`
- `ruleset_id`
- claim type
- normalized payload
- concrete target
- lifecycle status
- generator provenance

Claim lifecycle (`unknown / candidate / accepted / rejected`) と Evidence support status は別概念です。Evidenceが支持していても、review lifecycleが`accepted`になるまではpresentation truthへ昇格させません。

### EvidenceBinding

ClaimとSourceを明示的に関連付けます。

Relations:

- `supports`
- `contradicts`
- `contextualizes`
- `unresolved`

1 Source -> 複数Claim、複数Source -> 1 Claimを許可します。相反するSourceを上書きで消さず、`supports`と`contradicts`を同じClaimに保持できます。

同一 `(claim, source, locator, relation)` の重複bindingは拒否します。locatorが取得できず`NULL`の場合も、partial unique indexにより同一`(claim, source, relation)`の重複を許可しません。

## Target contract

Claimは必ず1つの具体targetを持ちます。Component Catalogに対する根拠も`game_metadata`へ代用せず、catalog entityそのものをtargetにします。

### RuleNode

```text
target_type = rule_node
rule_id = ...
```

Composite FK `(rule_set_id, rule_id)` により別RuleSetのRuleNodeへ接続できません。

### Component

Component identity / canonical name / quantity等、component entity自体についてのclaimです。

```text
target_type = component
component_id = ...
```

Composite FK `(rule_set_id, component_id)` により別RuleSetのComponentへ接続できません。

### ComponentSet

ComponentSetの存在・identity・分類についてのclaimです。

```text
target_type = component_set
component_set_id = ...
```

Composite FK `(rule_set_id, component_set_id)` により別RuleSetのComponentSetへ接続できません。

### PropertyDefinition

Property key / value type / cardinality等、PropertyDefinition自体についてのclaimです。

```text
target_type = property_definition
property_key = ...
```

Composite FK `(rule_set_id, property_key)` により別RuleSetのPropertyDefinitionへ接続できません。

### ComponentProperty

```text
target_type = component_property
component_id = ...
property_key = ...
ordinal = ...
```

#173のcanonical property identity `(rule_set_id, component_id, property_key, ordinal)` を直接利用します。opaqueなDB UUIDをUI contractにしません。同一Component内でcostはsupported、factionはunresolvedのようなmixed evidence stateを表現できます。

### Ability

printed component textとnormalized interpretationを別Claimにします。

```text
target_type = ability_printed_text
ability_id = ...
```

または:

```text
target_type = ability_normalized
ability_id = ...
```

同じability IDでも、印刷文の転記根拠と、それをRuleとして正規化した解釈の根拠を独立評価できます。

### Game metadata

```text
target_type = game_metadata
field_path = min_age
```

`ruleset_id`を必須とするため、edition/language/platformが曖昧なmetadataを別RuleSet間で暗黙共有しません。

## Support status

Evidence support statusはEvidenceBinding relationから決定論的に導出します。

- supportsのみ -> `supported`
- supports + contradicts -> `contested`
- contradictsのみ -> `contradicted`
- supporting evidenceなし -> `unresolved`

`projection_eligible=true`となるのは、次の両方を満たすclaimだけです。

1. lifecycleが`accepted`
2. support statusが`SUPPORTED`、すなわちsupportが存在しcontradictionがない

したがって`unknown / candidate / rejected`は、supporting sourceが存在してもprojection対象になりません。

Source trust、publisher identity、URL domain、entity-level `verification_status`から`projection_eligible`を推測しません。

## API

Targetごとのtrace:

```http
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=rule_node&rule_id=...
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=component&component_id=...
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=component_set&component_set_id=...
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=property_definition&property_key=...
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=component_property&component_id=...&property_key=...&ordinal=0
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=ability_printed_text&ability_id=...
GET /api/games/{slug}/evidence?rule_set_id=...&target_type=game_metadata&field_path=min_age
```

個別Claim:

```http
GET /api/games/{slug}/claims/{claim_id}?rule_set_id=...
```

全APIでRuleSetを明示し、別Game/RuleSetからclaimを取り込まないようfail-closedにします。

canonical evidence backendのread自体に失敗した場合は、`not_available`や404へ潰しません。`EvidenceReadError`として失敗させ、利用側が「evidenceが存在しない」と「backend障害」を区別できるようにします。

## Legacy fields

`rule_nodes.source_claim_ref / evidence_ref / source_url / source_locator` は既存互換のlegacy fieldです。v1導入後、claim supportの正準判定には使用しません。

同様にComponent Catalog v1の`source_ids`は移行中の粗いsource linkageであり、「そのComponent全fieldがsupported」という意味にはしません。

#153 migrationでcanonical Claim/Evidenceへの移行完了後、曖昧なlegacy read pathの削除条件を確定します。

## Database

Base migration: `backend/app/db/migrations/015_claim_evidence.sql`

Additive Component Catalog target migration: `backend/app/db/migrations/018_component_evidence_targets.sql`

Tables:

- `evidence_sources`
- `source_locators`
- `claims`
- `evidence_bindings`

TargetはRule Graph / Component Catalogの既存composite identityへFKで接続します。EvidenceSourceは複数RuleSetで再利用できますが、EvidenceBindingは必ず特定RuleSetのClaimを介して明示的に作成します。

`018_component_evidence_targets.sql`は既存の5 target typeを削除せず、`component / component_set / property_definition`をadditiveに追加します。既存Claimを保持した状態で適用できることをPostgreSQL contract testで固定します。

EvidenceBindingの一意性はlocator有無を分けたpartial unique indexで保証し、`locator_id=NULL`でも重複relationを作れないようにします。

全tableでRLSを有効化し、public anonymous write policyは追加しません。

## Projection / release gate

#151 Presentation Projectionは`projection_eligible=true`のClaimだけをrule truthの候補として使います。`unknown / candidate / rejected / contested / contradicted / unresolved`をverified Quick Rulesへ混ぜません。

#71 provenance release gateは少なくとも次を検知可能にします。

- Claimはあるがsupporting EvidenceBindingがない
- Claim lifecycleがacceptedではない
- contradictionを含むclaim
- RuleSet mismatchでbinding/target作成が拒否された
- locatorが無いsourceを架空locator付きとして扱っていない

`claim_evidence_audit_summary.claims_without_support` と `claims_not_accepted` を機械監査入口として利用できます。

## Primary standards

- W3C PROV-O: https://www.w3.org/TR/prov-o/
- W3C SHACL: https://www.w3.org/TR/shacl/

## Related

- #71 provenance release gate
- #139 source trust semantics
- #148 Ontology v2
- #149 Rule Graph
- #151 Presentation Projection
- #173 Component Catalog
- #174 RuleSet identity
- #175 Claim/Evidence Binding
- #178 Component ingestion
