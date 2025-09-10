# GitHub Actions CI/CD セットアップガイド

## 概要

このドキュメントでは、CloudFormation テンプレートの CI/CD パイプラインを動作させるために必要な GitHub Actions の設定について説明します。

**重要**: このプロジェクトでは、マルチアカウント方式と単一アカウント方式の2つのワークフローを提供しています。適切なワークフローの選択については、[ワークフロー選択ガイド](workflow-selection-guide.md)を参照してください。

## 必要なSecrets設定

### 1. AWS認証情報

設定するSecretsは選択したワークフローによって異なります。

#### マルチアカウント方式のSecrets

**中央管理用認証情報:**

| Secret名 | 説明 | 例 |
|---------|------|---|
| `AWS_ACCESS_KEY_ID` | 中央管理用AWS アクセスキーID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | 中央管理用AWS シークレットアクセスキー | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

**環境別ロールARN:**

| Secret名 | 説明 | 例 |
|---------|------|---|
| `AWS_DEPLOYMENT_ROLE_ARN_PROD` | 本番環境用IAMロールのARN | `arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole` |
| `AWS_DEPLOYMENT_ROLE_ARN_STAGING` | ステージング環境用IAMロールのARN | `arn:aws:iam::987654321098:role/GitHubActionsDeploymentRole` |
| `AWS_DEPLOYMENT_ROLE_ARN_DEV` | 開発環境用IAMロールのARN | `arn:aws:iam::456789012345:role/GitHubActionsDeploymentRole` |

#### 単一アカウント方式のSecrets

| Secret名 | 説明 | 例 |
|---------|------|---|
| `AWS_ACCESS_KEY_ID` | AWS アクセスキーID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS シークレットアクセスキー | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEPLOYMENT_ROLE_ARN` | デプロイ用IAMロールのARN | `arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole` |

#### アカウント固有認証情報

各AWSアカウントに対して以下の形式でSecretsを設定してください：

**本番アカウント (123456789012) の例:**

| Secret名 | 説明 | 例 |
|---------|------|---|
| `AWS_ACCESS_KEY_ID_123456789012` | 本番アカウント用アクセスキーID | `AKIAIOSFODNN7PROD123` |
| `AWS_SECRET_ACCESS_KEY_123456789012` | 本番アカウント用シークレットアクセスキー | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYPROD123` |
| `AWS_DEPLOYMENT_ROLE_ARN_123456789012` | 本番アカウント用デプロイロールARN | `arn:aws:iam::123456789012:role/ProdDeploymentRole` |

**ステージングアカウント (987654321098) の例:**

| Secret名 | 説明 | 例 |
|---------|------|---|
| `AWS_ACCESS_KEY_ID_987654321098` | ステージングアカウント用アクセスキーID | `AKIAIOSFODNN7STAG098` |
| `AWS_SECRET_ACCESS_KEY_987654321098` | ステージングアカウント用シークレットアクセスキー | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYSTAG098` |
| `AWS_DEPLOYMENT_ROLE_ARN_987654321098` | ステージングアカウント用デプロイロールARN | `arn:aws:iam::987654321098:role/StagingDeploymentRole` |

#### 認証情報の命名規則

```
AWS_ACCESS_KEY_ID_{ACCOUNT_ID}
AWS_SECRET_ACCESS_KEY_{ACCOUNT_ID}
AWS_DEPLOYMENT_ROLE_ARN_{ACCOUNT_ID}
```

**重要**: アカウントIDは12桁の数字で、ハイフンやスペースは含めません。

### 2. 通知設定（オプション）

| Secret名 | 説明 | 例 |
|---------|------|---|
| `SLACK_WEBHOOK_URL` | Slack通知用WebhookURL | `https://hooks.slack.com/services/...` |
| `TEAMS_WEBHOOK_URL` | Microsoft Teams通知用URL | `https://outlook.office.com/webhook/...` |
| `EMAIL_SMTP_PASSWORD` | メール通知用SMTPパスワード | `your-smtp-password` |

## AWS IAM設定

### 1. GitHub Actions用IAMユーザーの作成

```bash
# AWS CLIでIAMユーザーを作成
aws iam create-user --user-name github-actions-cf-deploy

# プログラマティックアクセス用のアクセスキーを作成
aws iam create-access-key --user-name github-actions-cf-deploy
```

### 2. IAMポリシーの作成

#### CloudFormation基本権限ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:ListStacks",
        "cloudformation:GetTemplate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/CloudFormation*"
    }
  ]
}
```

#### サービス固有権限ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "vpc:*",
        "iam:*",
        "lambda:*",
        "apigateway:*",
        "route53:*",
        "elasticloadbalancing:*",
        "cloudwatch:*",
        "logs:*",
        "kms:*",
        "s3:*",
        "organizations:*",
        "config:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. AssumeRole用IAMロールの作成

#### 信頼関係ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/github-actions-cf-deploy"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "github-actions-deployment"
        }
      }
    }
  ]
}
```

#### デプロイメントロールの権限ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

**注意**: 本番環境では最小権限の原則に従い、必要な権限のみを付与してください。

### 4. AWS CLI設定スクリプト

```bash
#!/bin/bash

# 変数設定
ACCOUNT_ID="123456789012"
USER_NAME="github-actions-cf-deploy"
ROLE_NAME="GitHubActionsDeploymentRole"
POLICY_NAME="CloudFormationDeploymentPolicy"

# IAMユーザー作成
aws iam create-user --user-name $USER_NAME

# アクセスキー作成
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name $USER_NAME)
echo "Access Key ID: $(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.AccessKeyId')"
echo "Secret Access Key: $(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.SecretAccessKey')"

# ポリシー作成
aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document file://cloudformation-policy.json

# ユーザーにポリシーをアタッチ
aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

# AssumeRole用のロール作成
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://trust-policy.json

# ロールに管理者権限をアタッチ（本番では制限してください）
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn "arn:aws:iam::aws:policy/AdministratorAccess"

echo "Setup completed!"
echo "Role ARN: arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
```

## GitHub Environment設定

選択したワークフローに応じて、異なるEnvironmentを作成してください。

### マルチアカウント方式のEnvironment

#### 本番環境 (Production)

- **Environment name**: `prod-environment`
- **Protection rules**:
  - Required reviewers: 2名以上
  - Wait timer: 5分
  - Restrict pushes to protected branches: `main` のみ

#### ステージング環境 (Staging)

- **Environment name**: `staging-environment`
- **Protection rules**:
  - Required reviewers: 1名以上
  - Restrict pushes to protected branches: `develop`, `main`

#### 開発環境 (Development)

- **Environment name**: `dev-environment`
- **Protection rules**:
  - Required reviewers: なし
  - Restrict pushes to protected branches: なし

### 単一アカウント方式のEnvironment

#### 本番環境 (Production)

- **Environment name**: `single-account-prod`
- **Protection rules**:
  - Required reviewers: 2名以上
  - Wait timer: 5分
  - Restrict pushes to protected branches: `main` のみ

#### ステージング環境 (Staging)

- **Environment name**: `single-account-staging`
- **Protection rules**:
  - Required reviewers: 1名以上
  - Restrict pushes to protected branches: `develop`, `main`

#### 開発環境 (Development)

- **Environment name**: `single-account-dev`
- **Protection rules**:
  - Required reviewers: なし
  - Restrict pushes to protected branches: なし

### 2. Environment Secrets

各環境に固有のSecretsを設定できます。

#### Production環境のSecrets

| Secret名 | 値 |
|---------|---|
| `AWS_DEPLOYMENT_ROLE_ARN` | `arn:aws:iam::123456789012:role/ProdDeploymentRole` |
| `AWS_REGION` | `us-east-1` |

#### Staging環境のSecrets

| Secret名 | 値 |
|---------|---|
| `AWS_DEPLOYMENT_ROLE_ARN` | `arn:aws:iam::987654321098:role/StagingDeploymentRole` |
| `AWS_REGION` | `us-west-2` |

## Variables設定

### Repository Variables

Settings > Secrets and variables > Actions > Variables で以下を設定:

| Variable名 | 値 | 説明 |
|-----------|---|------|
| `DEFAULT_AWS_REGION` | `us-east-1` | デフォルトのAWSリージョン |
| `PYTHON_VERSION` | `3.12` | 使用するPythonバージョン |
| `CF_LINT_VERSION` | `latest` | cfn-lintのバージョン |

### Environment Variables

各環境で以下の変数を設定:

| Variable名 | Production | Staging | 説明 |
|-----------|-----------|---------|------|
| `ENVIRONMENT_NAME` | `production` | `staging` | 環境名 |
| `STACK_PREFIX` | `prod` | `staging` | スタック名のプレフィックス |
| `NOTIFICATION_CHANNEL` | `#prod-alerts` | `#staging-alerts` | 通知チャンネル |

## セキュリティ設定

### 1. ブランチ保護ルール

Settings > Branches で以下のルールを設定:

#### mainブランチ

- **Require a pull request before merging**: ✅
- **Require approvals**: 2
- **Dismiss stale PR approvals when new commits are pushed**: ✅
- **Require review from code owners**: ✅
- **Require status checks to pass before merging**: ✅
  - `validate-and-map`
  - `test-templates`
- **Require branches to be up to date before merging**: ✅
- **Require conversation resolution before merging**: ✅
- **Include administrators**: ✅

#### developブランチ

- **Require a pull request before merging**: ✅
- **Require approvals**: 1
- **Require status checks to pass before merging**: ✅
  - `validate-and-map`
  - `test-templates`

### 2. Actions権限設定

Settings > Actions > General で以下を設定:

- **Actions permissions**: Allow select actions and reusable workflows
- **Allow actions created by GitHub**: ✅
- **Allow actions by Marketplace verified creators**: ✅
- **Allow specified actions and reusable workflows**:
  - `aws-actions/configure-aws-credentials@v4`
  - `actions/checkout@v4`
  - `actions/setup-python@v4`

### 3. Workflow権限

```yaml
permissions:
  contents: read
  id-token: write  # OIDC用
  pull-requests: write  # PR コメント用
  actions: read
  checks: write
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. AWS認証エラー

**エラー**: `Unable to locate credentials`

**解決方法**:
1. GitHub SecretsにAWS認証情報が正しく設定されているか確認
2. Secret名のスペルミスがないか確認
3. IAMユーザーが有効で、必要な権限があるか確認

#### 2. AssumeRoleエラー

**エラー**: `User is not authorized to perform: sts:AssumeRole`

**解決方法**:
1. IAMロールの信頼関係ポリシーを確認
2. AssumeRole権限がIAMユーザーに付与されているか確認
3. ロールARNが正しいか確認

#### 3. CloudFormation権限エラー

**エラー**: `User is not authorized to perform: cloudformation:CreateStack`

**解決方法**:
1. IAMポリシーにCloudFormation権限が含まれているか確認
2. リソース制限がないか確認
3. PassRole権限が適切に設定されているか確認

#### 4. Environment承認エラー

**エラー**: `Environment protection rules not met`

**解決方法**:
1. Environment設定で承認者が正しく設定されているか確認
2. 承認者がリポジトリへのアクセス権限を持っているか確認
3. ブランチ制限が適切に設定されているか確認

## セットアップチェックリスト

### 初期設定

- [ ] GitHub Secretsの設定
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `AWS_DEPLOYMENT_ROLE_ARN`
- [ ] AWS IAM設定
  - [ ] IAMユーザー作成
  - [ ] IAMポリシー作成・アタッチ
  - [ ] AssumeRole用ロール作成
- [ ] GitHub Environment設定
  - [ ] Production環境作成
  - [ ] Staging環境作成
  - [ ] 承認ルール設定
- [ ] ブランチ保護ルール設定
  - [ ] mainブランチ保護
  - [ ] developブランチ保護

### テスト実行

- [ ] 機能ブランチでのテスト実行確認
- [ ] developブランチでのデプロイテスト
- [ ] mainブランチでの本番デプロイテスト
- [ ] 承認フローの動作確認
- [ ] 通知機能の動作確認

### 運用準備

- [ ] チームメンバーへの権限付与
- [ ] ドキュメントの共有
- [ ] 緊急時の連絡先設定
- [ ] モニタリング・アラート設定

## 参考リンク

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)