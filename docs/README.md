# Documentation (`docs/`)

プロジェクトのドキュメントセットです。

## ドキュメント一覧

- **[`PROJECT_MASTER_GUIDE.md`](./PROJECT_MASTER_GUIDE.md)**
    - プロジェクトの「Single Source of Truth（信頼できる唯一の情報源）」です。要件、アーキテクチャ、データモデル、開発フロー、コーディング規約などが網羅されています。開発者が最初に読むべきドキュメントです。

- **[`RULE_GRAPH_V1.md`](./RULE_GRAPH_V1.md)**
    - Ontology v2 の canonical Rule Graph v1。RuleSet / RuleNode / RuleEdge、provenance境界、API、legacy migration mappingを定義します。

- **[`diagrams.md`](./diagrams.md)**
    - システムアーキテクチャ、シーケンス図、ER図などの視覚的な資料が含まれています。

- **[`prompts_strategy.md`](./prompts_strategy.md)**
    - AIプロンプトの設計思想、改善履歴、評価基準などがまとめられています。

- **[`画像生成AI.md`](./画像生成AI.md)**
    - 画像生成に関する調査や設計メモです。

## ドキュメントの更新について
コードやアーキテクチャに変更があった場合、必ず `PROJECT_MASTER_GUIDE.md` を更新し、実態との乖離を防いでください。Ontology v2 の詳細契約は専用versioned documentを正準として参照し、Master Guideからリンクします。
