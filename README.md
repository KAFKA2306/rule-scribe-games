https://bodoge-no-mikata.vercel.app/

# RuleScribe Games

[![Vercel Deployment](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/deploy.yml/badge.svg)](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/deploy.yml)
[![Rule quality gate](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/rule-quality.yml/badge.svg)](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/rule-quality.yml)
[![Curated game release verification](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/curated-game-release-verification.yml/badge.svg)](https://github.com/KAFKA2306/rule-scribe-games/actions/workflows/curated-game-release-verification.yml)

<div align="center">
  <img src="assets/02_ボドゲのミカタ.jpg" alt="RuleScribe Games Header" width="100%" style="border-radius: 12px; border: 1px solid rgba(0, 92, 185, 0.3);">

  **版や出典の違いを区別しながら、ボードゲームのルールを確認できる公開Webサービスです。**

  [![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://bodoge-no-mikata.vercel.app/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-005CB9?style=for-the-badge&logo=github)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
</div>

---

## 設計方針

本プロジェクトは、ゲーム固有の事実を複数の手書き経路へ複製せず、出典に結び付いた正準データから必要な表示を導出します。

- ゲーム本体、別名、版、プラットフォーム、言語を分けて管理する。
- ルールは `RuleSet`、`Claim`、`Evidence`、`RuleNode` を使い、根拠と表示内容を結び付ける。
- GamePageは、選択中のRuleSetに対応する確認済みの情報を表示する。古いルール本文へ黙って戻さない。
- curated gameは `data/curated-games/<slug>.json` と既存のvalidation / release workflowから追加・更新する。
- PRの検証成功とproduction releaseは別に確認し、mergeだけで公開成功と扱わない。

## 主要機能

- 日本語・英語の別名を含むゲーム検索、絞り込み、並び替え、ページ分割
- RuleSetと版差の表示
- supporting evidenceがあるaccepted claimに基づくルール表示
- glossary、concept、rule graph、component catalog
- ゲームごとのURL、server-side rendering、structured metadata

## Architecture

```mermaid
graph TD
    User([User]) <--> Frontend[React/Vite]
    Frontend <--> API[FastAPI - Vercel Serverless]
    API <--> Catalog[(Supabase)]
    Catalog --> RuleSet[RuleSet]
    RuleSet --> Claim[Claim]
    Claim --> Evidence[Evidence]
    Claim --> RuleNode[RuleNode]
    RuleNode --> Projection[Presentation Projection]
    Projection --> Frontend
```

## Quick start

```bash
task setup
task dev
task lint
```

curated gameの追加・更新:

```bash
task game:add GAME=<slug>
```

このコマンドはPR準備用のvalidationとread-only preflightを実行し、productionへ直接writeしません。production publicationはmerge後のrelease workflowが担当します。

## Repository

- `backend/app/`: FastAPI、正準データのread/write、RuleSet/evidence/projection service
- `api/`: Vercel Serverless entrypoint
- `frontend/`: React/Vite UI
- `data/curated-games/`: 出典付きcurated game input
- `docs/`: 仕様と運用文書

## Issue workflow

新規Issueは、Acceptance Criteria、tests、必要なproduction verificationまでを完遂可能な契約として扱います。運用規約は `docs/ISSUE_GUIDE.md` を参照してください。

---

MIT © 2026 RuleScribe Games contributors
