# RuleSet Identity v1

## Purpose

`Game` identityと、実際に適用されるルールの版・言語・platform・revisionを分離するためのcanonical contractです。

```text
Game
  └─ RuleSet
      ├─ RuleNode / RuleEdge
      └─ ComponentCatalog (Ontology v2 follow-up)
```

同一Gameに物理版、Board Game Arena実装、改訂版、翻訳版、optional variantが存在しても、RuleNodeやComponentを混線させないことを目的とします。

## Identity boundary

`public.rule_sets.id` をstable `ruleset_id`として扱います。表示ラベルや翻訳名をIDとして使用しません。

RuleSet identityの主要軸は独立して保持します。

- `game_id`: canonical Game identity
- `edition_label`: edition名。確認できない場合はNULL
- `language_code`: BCP 47相当のlanguage/locale文字列。確認できない場合はNULL
- `platform`: `physical`, `boardgamearena`等の実装platform。sourceで確認できる場合のみ
- `revision_label`: 人間向けrevision label。確認できない場合はNULL
- `source_revision`: source document/API側のrevision識別子
- `variant_label`: variant名
- `version`: repository/database内でのRuleSet record version

NULLはunknownを意味します。migrationやread pathでGame直下のlegacy値からedition/platform/revisionを推測して埋めません。

## Lifecycle and verification

### status

- `unknown`
- `active`
- `superseded`

`superseded` RuleSetは`is_active=false`でなければなりません。`active` RuleSetは`is_active=true`でなければなりません。既存recordはmigration時に根拠なく`active`へ昇格させず、`status=unknown`を保持します。

### verification_status

- `unknown`
- `source_bound`
- `verified`
- `rejected`

source URLが存在することとRuleSet identityがverifiedであることは別状態です。field/claim-level evidenceは #175 で追加します。

## Relations

RuleSet間の関係は`base_rule_set_id + relation_type`で明示します。

- `derived_from`
- `variant_of`
- `translation_of`
- `supersedes`

`variant_of`は`variant_label`必須です。self relationは禁止します。

PROV-Oのderivation semanticsと整合するよう、派生関係はGame identityの複製ではなくRuleSet間relationとして保持します。

Primary reference: https://www.w3.org/TR/prov-o/

## PostgreSQL constraints

旧schemaの以下を廃止します。

```text
UNIQUE(game_id, version)
UNIQUE active RuleSet per game
```

これらは同一Gameに物理版+BGA版、またはja+enを同時保持できないためです。

v1ではidentity軸ごとに:

- `(game, edition, language, platform, revision, variant, version)` の重複を禁止
- active uniquenessは同じidentity軸の組み合わせ内だけに限定

します。異なるplatform/languageのactive RuleSetは同時に存在できます。

PostgreSQL partial unique index reference: https://www.postgresql.org/docs/current/indexes-partial.html

## Rule Graph selection

`GET /api/games/{slug}/rule-graph` は次の契約です。

- active RuleSetが1件だけ: 後方互換としてそのgraphを返せる
- active RuleSetが複数: 未指定では`not_available`としてfail-closed
- `rule_set_id`を明示: そのGameに属する指定RuleSetだけを読む

版が複数ある状態で「最新版らしいもの」を自動選択しません。

RuleSet候補は次で取得します。

```http
GET /api/games/{slug}/rule-sets
```

## Presentation Projection boundary

#151 Presentation Projection は別truth storeを作らず、必ず選択済みRuleSetのRule Graph / Concept / Evidenceから生成します。

- projection request/outputは対象`rule_set_id`を追跡可能にする
- active RuleSetが複数ある場合、projection側でpublisher/BGAや言語を自動mergeしない
- `rule_set_id`未選択でtruth boundaryが一意でなければfail-closedする
- Quick Rules / setup / scoring / end condition等を別RuleSetから継ぎ合わせない
- source間の矛盾は上書きで消さず、#175のClaim/Evidence BindingでRuleSetごとに保持する

これにより、同じGameのpublisher rulesとplatform implementationで記述が異なっても、表示projectionが暗黙に混合しません。

## API response

`RuleSetListResponse`は:

- `status`
- `game_id`
- `slug`
- `rulesets[]`

を返します。migration未適用、またはcanonical RuleSet未登録の場合は、Gameが存在していても`status=not_available`・空配列を返し、legacy Game fieldからRuleSetを生成しません。

## Component Catalog contract

#173で導入するComponent Catalogは必ず`ruleset_id`へ所属させます。同名カードでも、改訂版・digital implementation・variantで値や能力が異なる場合に上書きしないためです。

## Migration / rollback

Migration: `backend/app/db/migrations/013_ruleset_identity.sql`

- 既存`rule_sets`を破棄しないadditive migration
- edition/language/platform/revisionの自動backfillをしない
- old one-active-per-game indexを削除
- identity-scope uniquenessへ移行
- relation/lifecycle/verification constraintsを追加

Rollbackで旧`one active per game`制約を復元すると複数RuleSetを表現できなくなるため、production dataに複数active identityが入った後は単純rollbackしません。必要時はread pathをfail-closedにし、dataを保持したままapplication側を停止します。

## Related issues

- #148 Ontology v2
- #149 Rule Graph
- #151 Presentation Projection
- #173 Component Catalog
- #174 RuleSet identity
- #175 Claim/Evidence Binding
