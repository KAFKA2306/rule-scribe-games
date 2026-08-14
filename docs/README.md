# Documentation (`docs/`)

プロジェクトのドキュメントセットです。

## ドキュメント一覧

- **[`PROJECT_MASTER_GUIDE.md`](./PROJECT_MASTER_GUIDE.md)**
    - プロジェクトの「Single Source of Truth（信頼できる唯一の情報源）」です。要件、アーキテクチャ、データモデル、開発フロー、コーディング規約などが網羅されています。開発者が最初に読むべきドキュメントです。

- **[`CURATED_GAME_FAST_PATH.md`](./CURATED_GAME_FAST_PATH.md)**
    - 一次情報に基づくゲーム追加の最短運用契約です。1ゲーム=1branch/1PR、対象CI優先、無関係なインフラ障害の分離、成功後の短い効率化レビューを定義します。

- **[`RULESET_IDENTITY_V1.md`](./RULESET_IDENTITY_V1.md)**
    - Ontology v2 の RuleSet identity contract。Gameとは別にedition / language / platform / revision / variantを保持し、Rule Graph・Component Catalogのtruth boundaryを定義します。

- **[`RULE_GRAPH_V1.md`](./RULE_GRAPH_V1.md)**
    - Ontology v2 の canonical Rule Graph v1。RuleSet / RuleNode / RuleEdge、provenance境界、API、legacy migration mappingを定義します。

- **[`CONCEPT_TAXONOMY_V1.md`](./CONCEPT_TAXONOMY_V1.md)**
    - stable concept ID、多言語label、SKOS型relation、Rule Graph backlinks、linked glossary projectionを定義します。

- **[`COMPONENT_CATALOG_V1.md`](./COMPONENT_CATALOG_V1.md)**
    - Ontology v2 のgame-content instance layer。cards / tiles / tokens / diceを同じgeneric schemaで扱い、PropertyDefinition・typed values・RuleSet/Concept/RuleNode境界を定義します。

- **[`CLAIM_EVIDENCE_V1.md`](./CLAIM_EVIDENCE_V1.md)**
    - RuleNode / ComponentProperty / Ability / metadata fieldごとのClaimとSource/Locator/EvidenceBindingを分離し、support・contradiction・projection eligibilityを決定論的に追跡するprovenance contractです。

- **[`diagrams.md`](./diagrams.md)**
    - システムアーキテクチャ、シーケンス図、ER図などの視覚的な資料が含まれています。

- **[`prompts_strategy.md`](./prompts_strategy.md)**
    - AIプロンプトの設計思想、改善履歴、評価基準などがまとめられています。

- **[`画像生成AI.md`](./画像生成AI.md)**
    - 画像生成に関する調査や設計メモです。

## ドキュメントの更新について
コードやアーキテクチャに変更があった場合、必ず `PROJECT_MASTER_GUIDE.md` を更新し、実態との乖離を防いでください。Ontology v2 の詳細契約は専用versioned documentを正準として参照し、Master Guideからリンクします。
