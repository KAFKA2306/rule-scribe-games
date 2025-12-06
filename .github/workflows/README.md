# Workflows

GitHub Actions ワークフロー。

## ファイル

| ファイル | トリガー | 動作 |
|---------|---------|------|
| `deploy.yml` | push/PR to main | Vercel デプロイ |

## ジョブ

- **Deploy-Preview**: PR → Preview環境
- **Deploy-Production**: main push → 本番環境
