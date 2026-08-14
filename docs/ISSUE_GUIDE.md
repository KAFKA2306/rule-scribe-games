# Issue contract

RuleScribe GamesのIssueは、**実装 → テスト → 必要な本番検証 → cleanup → close**まで1本の証拠線で完遂できることを基準にする。

## Template selection

- **Feature / product change**: ユーザー価値や製品挙動を追加・変更する。
- **AI / data quality change**: source、provenance、evaluation、data-quality gateが主題になる。
- **Ops / bug / production incident**: 再現可能な障害、回帰、deploy/runtime問題を扱う。
- 既存のAPI connection専用templateは、その障害種別に限定して利用する。

GitHub Issue Formsは `.github/ISSUE_TEMPLATE/*.yml` を正準とする。blank issueは通常のcontributor経路では無効化し、既存Issueの編集やmaintainer作業を妨げない。

## Required completion contract

Issueは最低限、次を分離して記載する。

1. **Problem / user value or impact** — 何を見極め、何を変えるか。
2. **Evidence / current behavior** — 再現、code/data location、sanitized log、一次source URLなど。
3. **Scope / non-scope** — 今回変える範囲と変えない範囲。
4. **Dependencies / blockers** — code blockerと外部設定・権限blockerを分ける。
5. **Acceptance Criteria** — close判定できる結果。実装手段そのものだけを完了条件にしない。
6. **Tests** — unit / integration / E2E / security / data contract / regressionの必要範囲。
7. **Production verification** — 本番確認が必要ならURL、deployment、HTTP/browser/API/data evidenceまで指定する。不要なら理由を書く。
8. **Cleanup / rollback condition** — branch、superseded PR、一時artifact、暫定override、失敗時rollback条件を明示する。

## AI / data-quality additions

AI・データ品質Issueでは、さらに以下を固定する。

- authoritative / canonical sourceとsource locator
- edition / language / revisionなど、意味を変えるversion情報
- golden fixture、baseline、metric、thresholdまたは判定可能なinvariant
- `FAIL` と `UNKNOWN / NOT_RUN` の区別
- sourceで確認できない値を推測で補完しない契約
- provenance/schema validationに失敗した結果を正準データへ昇格させない条件

## Ops / bug additions

障害Issueでは、少なくとも以下を分ける。

- reproduction
- actual behavior
- expected behavior
- production/deployment evidence
- retry/fallback/rollbackを含むfailure-path test

CIがgreenでも本番Acceptance Criteriaが未達ならIssueはcloseしない。

## Blockers

外部設定やrepository administrationが必要で、現在のagent権限では実行できない場合は、コード側を偽装してcloseしない。Issueへ次を残す。

- 実施済み内容
- 実行できない操作と必要権限
- 現在のproduction state
- unblock後の具体的な次手

## Superseded work

同じAcceptance Criteriaを別PRが先に満たした場合、古いPRをmergeして新しい実装を巻き戻さない。最新mainを検証し、満たしていれば古いPRを`superseded`としてcloseし、不要branch/artifactを削除可能な範囲で整理する。

## Secrets and private data

Issue本文、ログ、fixture、screenshot、repository sourceへtoken、API key、cookie、private credential、private user dataを貼らない。必要なsecretはproviderのsecret/environment機構へ保存し、存在だけを検証する。
