# デプロイメント設定ガイド

## 概要

このガイドでは、CloudFormationテンプレートのCI/CDパイプラインにおけるデプロイメント先の設定方法について説明します。パイプラインは**環境ベース**のアプローチを採用しており、JSONパラメータファイルの`Environment`パラメータに基づいてデプロイ先を自動判定します。

## 基本的な設定方法

### 1. 環境パラメータの指定

JSONパラメータファイルに`Environment`パラメータを含めてください：

```json
{
  "Parameters": {
    "Environment": "staging",
    "ProjectName": "MyWebApp",
    "InstanceType": "t3.medium"
  },
  "Tags": {
    "Owner": "DevOps Team",
    "Environment": "Staging"
  }
}
```

### 2. サポートされる環境値

| 設定値 | 正規化された環境 | 用途 |
|-------|---------------|------|
| `production`, `prod` | `prod` | 本番環境 |
| `staging`, `stage` | `staging` | ステージング環境 |
| `development`, `dev`, `test` | `dev` | 開発・テスト環境 |

## デプロイメントフロー

### 1. 環境判定

パイプラインは以下の順序で環境を判定します：

1. `Parameters.Environment`
2. `Tags.Environment`
3. デフォルト: `dev`

### 2. GitHub Environment選択

判定された環境に基づいて、対応するGitHub Environmentが選択されます：

- `prod` → `prod-environment`
- `staging` → `staging-environment`  
- `dev` → `dev-environment`

### 3. AWS認証情報の選択

環境に対応するGitHub Secretsが使用されます：

```
AWS_ACCESS_KEY_ID_{ENVIRONMENT}
AWS_SECRET_ACCESS_KEY_{ENVIRONMENT}
AWS_DEPLOYMENT_ROLE_ARN_{ENVIRONMENT}
```

例：
- 本番環境: `AWS_ACCESS_KEY_ID_PROD`
- ステージング環境: `AWS_ACCESS_KEY_ID_STAGING`
- 開発環境: `AWS_ACCESS_KEY_ID_DEV`

## 設定例

### 本番環境デプロイ

```json
{
  "Parameters": {
    "Environment": "production",
    "ProjectName": "ProductionApp",
    "InstanceType": "m5.large",
    "EnableDetailedMonitoring": "true",
    "EnableAutoScaling": "true"
  },
  "Tags": {
    "Owner": "Production Team",
    "CostCenter": "Engineering",
    "Environment": "Production"
  },
  "Description": "本番環境用の設定"
}
```

**結果:**
- GitHub Environment: `prod-environment`
- AWS認証情報: `AWS_*_PROD`
- 承認要件: 2名以上の承認が必要

### ステージング環境デプロイ

```json
{
  "Parameters": {
    "Environment": "staging",
    "ProjectName": "StagingApp", 
    "InstanceType": "t3.medium",
    "EnableDetailedMonitoring": "true"
  },
  "Tags": {
    "Owner": "QA Team",
    "Environment": "Staging"
  },
  "Description": "ステージング環境用の設定"
}
```

**結果:**
- GitHub Environment: `staging-environment`
- AWS認証情報: `AWS_*_STAGING`
- 承認要件: 1名以上の承認が必要

### 開発環境デプロイ

```json
{
  "Parameters": {
    "Environment": "dev",
    "ProjectName": "DevApp",
    "InstanceType": "t3.micro"
  },
  "Tags": {
    "Owner": "Development Team",
    "Environment": "Development"
  },
  "Description": "開発環境用の設定"
}
```

**結果:**
- GitHub Environment: `dev-environment`
- AWS認証情報: `AWS_*_DEV`
- 承認要件: 最小限の承認

## 高度な設定

### 明示的なAWSアカウント指定

特定のAWSアカウントを指定したい場合は、オプションとして以下のパラメータを追加できます：

```json
{
  "Parameters": {
    "Environment": "production",
    "AWSAccount": "123456789012",
    "ProjectName": "SpecialApp"
  }
}
```

この場合：
- GitHub Environment: `aws-account-123456789012`
- AWS認証情報: アカウント固有のSecrets
- IAMロール: `arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole`

### リージョンの指定

デプロイ先リージョンは以下の方法で指定できます：

#### 1. 明示的なRegionパラメータ

```json
{
  "Parameters": {
    "Environment": "production",
    "Region": "ap-northeast-1",
    "ProjectName": "TokyoApp"
  }
}
```

#### 2. ARNからの自動推定

```json
{
  "Parameters": {
    "Environment": "production",
    "TargetGroupArn": "arn:aws:elasticloadbalancing:eu-west-1:123456789012:targetgroup/my-targets/1234567890123456"
  }
}
```

この場合、ARNから`eu-west-1`リージョンが自動的に推定されます。

## ブランチ戦略との連携

### ブランチと環境のマッピング

| ブランチ | 推奨環境 | 自動デプロイ | 承認要件 |
|---------|---------|------------|---------|
| `main` | `production` | 手動承認後 | 厳格（2名以上） |
| `develop` | `staging` | 手動承認後 | 標準（1名以上） |
| `feature/*` | `dev` | テストのみ | なし |
| `hotfix/*` | `production` | 緊急承認後 | 迅速承認 |

### ワークフロー例

#### 1. 機能開発

```bash
# feature ブランチで開発
git checkout -b feature/new-lambda-function

# 開発環境用の設定ファイルを作成/更新
vim cf-templates/compute/lambda/lambda-config-dev.json
```

```json
{
  "Parameters": {
    "Environment": "dev",
    "FunctionName": "MyTestFunction",
    "Runtime": "python3.9"
  }
}
```

```bash
# コミット・プッシュ
git add .
git commit -m "feat: add new Lambda function for dev environment"
git push origin feature/new-lambda-function
```

**結果**: テストのみ実行、デプロイなし

#### 2. ステージング環境でのテスト

```bash
# develop ブランチにマージ
git checkout develop
git merge feature/new-lambda-function

# ステージング環境用の設定ファイルを更新
vim cf-templates/compute/lambda/lambda-config-staging.json
```

```json
{
  "Parameters": {
    "Environment": "staging",
    "FunctionName": "MyTestFunction",
    "Runtime": "python3.9",
    "MemorySize": 256
  }
}
```

```bash
git add .
git commit -m "feat: configure Lambda for staging environment"
git push origin develop
```

**結果**: テスト実行後、手動承認を経てステージング環境にデプロイ

#### 3. 本番環境へのリリース

```bash
# main ブランチにマージ
git checkout main
git merge develop

# 本番環境用の設定ファイルを更新
vim cf-templates/compute/lambda/lambda-config-prod.json
```

```json
{
  "Parameters": {
    "Environment": "production",
    "FunctionName": "MyProductionFunction",
    "Runtime": "python3.9",
    "MemorySize": 512,
    "ReservedConcurrency": 100
  }
}
```

```bash
git add .
git commit -m "feat: configure Lambda for production environment"
git push origin main
```

**結果**: テスト実行後、厳格な承認プロセスを経て本番環境にデプロイ

## トラブルシューティング

### よくある問題

#### 1. 環境が正しく判定されない

**問題**: 設定ファイルに`Environment`パラメータがない

**解決方法**:
```json
{
  "Parameters": {
    "Environment": "staging",  // この行を追加
    "ProjectName": "MyApp"
  }
}
```

#### 2. AWS認証エラー

**問題**: 環境に対応するSecretsが設定されていない

**解決方法**:
GitHub リポジトリの Settings > Secrets で以下を設定：
- `AWS_ACCESS_KEY_ID_STAGING`
- `AWS_SECRET_ACCESS_KEY_STAGING`
- `AWS_DEPLOYMENT_ROLE_ARN_STAGING`

#### 3. 承認プロセスが動作しない

**問題**: GitHub Environmentが正しく設定されていない

**解決方法**:
1. Settings > Environments で環境を作成
2. 承認者を設定
3. ブランチ制限を設定

### デバッグ方法

#### 1. ローカルテスト

```bash
# 設定ファイルのテスト
python scripts/test-pipeline.py --config cf-templates/compute/ec2/ec2-config-staging.json

# AWS CLI を使用したテスト
python scripts/test-pipeline.py --aws --config cf-templates/compute/ec2/ec2-config-staging.json
```

#### 2. GitHub Actions ログの確認

パイプラインの実行ログで以下を確認：

```
Target Environment: staging
Deployment Region: us-east-1
AWS Account: Environment-based default (staging)
```

#### 3. 設定ファイルの検証

```bash
# JSON構文チェック
python -m json.tool cf-templates/compute/ec2/ec2-config-staging.json

# 設定内容の確認
jq '.Parameters.Environment' cf-templates/compute/ec2/ec2-config-staging.json
```

## ベストプラクティス

### 1. 環境固有の設定

各環境に適した設定を使用してください：

```json
// 開発環境
{
  "Parameters": {
    "Environment": "dev",
    "InstanceType": "t3.micro",
    "EnableDetailedMonitoring": "false"
  }
}

// ステージング環境
{
  "Parameters": {
    "Environment": "staging", 
    "InstanceType": "t3.medium",
    "EnableDetailedMonitoring": "true"
  }
}

// 本番環境
{
  "Parameters": {
    "Environment": "production",
    "InstanceType": "m5.large",
    "EnableDetailedMonitoring": "true",
    "EnableAutoScaling": "true"
  }
}
```

### 2. 一貫した命名規則

設定ファイル名に環境を含めてください：

```
cf-templates/compute/ec2/ec2-config-dev.json
cf-templates/compute/ec2/ec2-config-staging.json
cf-templates/compute/ec2/ec2-config-prod.json
```

### 3. タグの活用

適切なタグを設定してリソースを管理してください：

```json
{
  "Tags": {
    "Environment": "Production",
    "Owner": "DevOps Team",
    "CostCenter": "Engineering",
    "Project": "WebApplication",
    "ManagedBy": "CloudFormation"
  }
}
```

### 4. セキュリティの考慮

- 本番環境では最小権限の原則を適用
- 開発環境でも適切なセキュリティ設定を維持
- 認証情報は環境ごとに分離

## 参考資料

- [ワークフロー選択ガイド](workflow-selection-guide.md) - **最初に読んでください**
- [GitHub Actions ワークフロー（マルチアカウント）](../.github/workflows/ci-cd-pipeline.yml)
- [GitHub Actions ワークフロー（単一アカウント）](../.github/workflows/ci-cd-pipeline-single-account.yml)
- [ブランチ戦略](branching-strategy.md)
- [セットアップガイド](github-actions-setup.md)
- [CI/CDパイプライン概要](ci-cd-pipeline-overview.md)