# AWS認証戦略の比較

## 概要

CloudFormation CI/CDパイプラインでは、AWSアカウント構成に応じて2つの認証戦略を選択できます。このドキュメントでは、それぞれのアプローチの特徴、メリット・デメリット、適用場面について説明します。

## 認証戦略の比較

### 1. 単一AWSアカウント戦略（推奨：シンプルな環境）

#### 概要
1つのAWSアカウント内で環境を分離し、直接認証を使用する方式

#### 認証フロー
```mermaid
graph LR
    A[GitHub Actions] --> B[AWS Account]
    B --> C[CloudFormation]
    C --> D[Dev Environment]
    C --> E[Staging Environment]
    C --> F[Prod Environment]
```

#### 必要な認証情報
- **AWS_ACCESS_KEY_ID**: IAMユーザーのアクセスキー
- **AWS_SECRET_ACCESS_KEY**: IAMユーザーのシークレットキー
- **AssumeRole**: 不要

#### 設定例
```yaml
# GitHub Secrets
AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# GitHub Actions
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

### 2. マルチAWSアカウント戦略（推奨：エンタープライズ環境）

#### 概要
環境ごとに独立したAWSアカウントを使用し、AssumeRoleで認証する方式

#### 認証フロー
```mermaid
graph LR
    A[GitHub Actions] --> B[Base AWS Account]
    B --> C[AssumeRole]
    C --> D[Dev Account]
    C --> E[Staging Account]
    C --> F[Prod Account]
    D --> G[CloudFormation Dev]
    E --> H[CloudFormation Staging]
    F --> I[CloudFormation Prod]
```

#### 必要な認証情報
- **AWS_ACCESS_KEY_ID**: ベースアカウントのアクセスキー
- **AWS_SECRET_ACCESS_KEY**: ベースアカウントのシークレットキー
- **AWS_DEPLOYMENT_ROLE_ARN**: ターゲットアカウントのIAMロールARN

#### 設定例
```yaml
# GitHub Secrets
AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEPLOYMENT_ROLE_ARN_PROD: arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole

# GitHub Actions
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
    role-to-assume: ${{ secrets.AWS_DEPLOYMENT_ROLE_ARN_PROD }}
    role-session-name: GitHubActions-Deploy
```

## 詳細比較

### セキュリティ

| 項目 | 単一アカウント | マルチアカウント |
|------|-------------|----------------|
| **アカウント分離** | タグ・IAMベース | 物理的分離 |
| **権限管理** | IAMポリシー | AssumeRole + IAMポリシー |
| **認証情報の数** | 1セット | 1セット（ベース）+ ロールARN |
| **セキュリティレベル** | 中 | 高 |
| **誤操作リスク** | 中（環境間） | 低（アカウント間分離） |

### 運用性

| 項目 | 単一アカウント | マルチアカウント |
|------|-------------|----------------|
| **設定の複雑さ** | シンプル | 複雑 |
| **デバッグの容易さ** | 容易 | やや困難 |
| **コスト管理** | タグベース | アカウントベース |
| **監査** | CloudTrail統合 | アカウント別CloudTrail |
| **初期セットアップ** | 簡単 | 複雑 |

### スケーラビリティ

| 項目 | 単一アカウント | マルチアカウント |
|------|-------------|----------------|
| **環境追加** | 容易 | 新アカウント作成必要 |
| **チーム分離** | IAMベース | アカウントベース |
| **リソース制限** | アカウント制限共有 | アカウント別制限 |
| **請求分離** | タグベース | 完全分離 |

## 適用場面

### 単一AWSアカウント戦略が適している場合

#### ✅ 推奨シナリオ
- **小〜中規模プロジェクト**
- **開発チームが少数**
- **環境間でのリソース共有が必要**
- **シンプルな運用を重視**
- **コスト最適化を重視**

#### 実装例
```json
// 設定ファイル例
{
  "Parameters": {
    "Environment": "staging",
    "ProjectName": "MyApp",
    "InstanceType": "t3.medium"
  },
  "Tags": {
    "Environment": "Staging",
    "Project": "MyApp",
    "CostCenter": "Engineering"
  }
}
```

#### IAM設定例
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "ec2:*",
        "iam:PassRole"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    }
  ]
}
```

### マルチAWSアカウント戦略が適している場合

#### ✅ 推奨シナリオ
- **大規模エンタープライズ環境**
- **複数チーム・複数プロジェクト**
- **厳格なセキュリティ要件**
- **コンプライアンス要件**
- **完全な環境分離が必要**

#### 実装例
```json
// 設定ファイル例（アカウント指定あり）
{
  "Parameters": {
    "Environment": "production",
    "AWSAccount": "123456789012",
    "ProjectName": "EnterpriseApp",
    "InstanceType": "m5.large"
  },
  "Tags": {
    "Environment": "Production",
    "Project": "EnterpriseApp",
    "BusinessUnit": "Sales"
  }
}
```

#### AssumeRole設定例
```json
// ベースアカウントのIAMユーザーポリシー
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole",
        "arn:aws:iam::987654321098:role/GitHubActionsDeploymentRole"
      ]
    }
  ]
}

// ターゲットアカウントの信頼関係
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::BASE-ACCOUNT:user/github-actions-user"
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

## 実装ガイド

### 単一アカウント戦略の実装

#### 1. GitHub Secretsの設定
```bash
# 必要なSecrets（最小限）
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

#### 2. ワークフローファイル
```yaml
# .github/workflows/ci-cd-pipeline-single-account.yml を使用
```

#### 3. IAMユーザーの作成
```bash
# AWS CLI での設定例
aws iam create-user --user-name github-actions-cf-deploy
aws iam create-access-key --user-name github-actions-cf-deploy
aws iam attach-user-policy --user-name github-actions-cf-deploy \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### マルチアカウント戦略の実装

#### 1. GitHub Secretsの設定
```bash
# ベース認証情報
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# 環境別ロールARN
AWS_DEPLOYMENT_ROLE_ARN_PROD
AWS_DEPLOYMENT_ROLE_ARN_STAGING
AWS_DEPLOYMENT_ROLE_ARN_DEV
```

#### 2. ワークフローファイル
```yaml
# .github/workflows/ci-cd-pipeline.yml を使用（既存）
```

#### 3. クロスアカウントIAMロールの設定
```bash
# 各ターゲットアカウントでロール作成
aws iam create-role --role-name GitHubActionsDeploymentRole \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy --role-name GitHubActionsDeploymentRole \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

## 移行ガイド

### 単一アカウントからマルチアカウントへの移行

#### ステップ1: 新しいAWSアカウントの準備
1. 環境別AWSアカウントの作成
2. AWS Organizationsでの管理設定
3. 請求統合の設定

#### ステップ2: IAMロールの設定
1. 各アカウントでデプロイメントロール作成
2. クロスアカウント信頼関係の設定
3. 必要な権限の付与

#### ステップ3: GitHub設定の更新
1. 新しいSecretsの追加
2. ワークフローファイルの切り替え
3. Environment設定の更新

#### ステップ4: 段階的移行
1. 開発環境から開始
2. ステージング環境の移行
3. 本番環境の移行（最後）

### マルチアカウントから単一アカウントへの移行

#### ステップ1: 統合アカウントの準備
1. 統合先アカウントの選定
2. リソースの棚卸し
3. 移行計画の策定

#### ステップ2: リソースの移行
1. CloudFormationテンプレートの調整
2. データの移行
3. DNS・ネットワーク設定の更新

#### ステップ3: GitHub設定の簡素化
1. 不要なSecretsの削除
2. ワークフローファイルの簡素化
3. Environment設定の統合

## トラブルシューティング

### 単一アカウント戦略での問題

#### 権限エラー
```bash
# 問題: CloudFormation権限不足
# 解決: IAMポリシーの確認と更新
aws iam list-attached-user-policies --user-name github-actions-cf-deploy
```

#### 環境分離の問題
```bash
# 問題: 環境間でのリソース競合
# 解決: タグとネーミング規則の徹底
```

### マルチアカウント戦略での問題

#### AssumeRoleエラー
```bash
# 問題: AssumeRole権限不足
# 解決: 信頼関係とポリシーの確認
aws sts assume-role --role-arn arn:aws:iam::TARGET:role/DeploymentRole \
  --role-session-name test
```

#### クロスアカウント設定エラー
```bash
# 問題: 外部IDの不一致
# 解決: 信頼関係ポリシーの確認
```

## 推奨事項

### 新規プロジェクトの場合

1. **小規模プロジェクト**: 単一アカウント戦略から開始
2. **大規模プロジェクト**: 最初からマルチアカウント戦略を採用
3. **成長予定**: 単一アカウントで開始し、必要に応じて移行

### 既存プロジェクトの場合

1. **現在の課題を評価**
2. **移行コストと利益を比較**
3. **段階的移行計画を策定**

### セキュリティ強化

1. **最小権限の原則を適用**
2. **定期的な権限レビュー**
3. **CloudTrailでの監査ログ確保**
4. **MFAの有効化（可能な場合）**

## 参考資料

- [単一アカウント用ワークフロー](.github/workflows/ci-cd-pipeline-single-account.yml)
- [マルチアカウント用ワークフロー](.github/workflows/ci-cd-pipeline.yml)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Organizations User Guide](https://docs.aws.amazon.com/organizations/latest/userguide/)
- [GitHub Actions AWS認証](https://github.com/aws-actions/configure-aws-credentials)