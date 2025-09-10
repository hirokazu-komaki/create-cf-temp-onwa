# GitHub Actions ワークフロー選択ガイド

## 概要

このプロジェクトでは、デプロイメント戦略に応じて2つの異なるGitHub Actionsワークフローを提供しています。プロジェクトの要件に応じて適切なワークフローを選択してください。

## ワークフローの種類

### 1. マルチアカウント方式
**ファイル**: `.github/workflows/ci-cd-pipeline.yml`

**概要**: 環境ごとに異なるAWSアカウントを使用する方式

**適用場面**:
- 大規模組織での運用
- 厳格な環境分離が必要
- コンプライアンス要件が厳しい
- 複数チームでの独立した運用

### 2. 単一アカウント方式
**ファイル**: `.github/workflows/ci-cd-pipeline-single-account.yml`

**概要**: 1つのAWSアカウント内で論理的に環境を分離する方式

**適用場面**:
- 中小規模プロジェクト
- シンプルな運用を重視
- コスト最適化を重視
- 単一チームでの運用

## 詳細比較

### アーキテクチャの違い

#### マルチアカウント方式
```
GitHub Actions
    ↓
Central AWS Account (認証)
    ↓ AssumeRole
┌─────────────────┬─────────────────┬─────────────────┐
│ Production      │ Staging         │ Development     │
│ Account         │ Account         │ Account         │
│ (123456789012)  │ (987654321098)  │ (456789012345)  │
└─────────────────┴─────────────────┴─────────────────┘
```

#### 単一アカウント方式
```
GitHub Actions
    ↓
Single AWS Account (123456789012)
    ├── prod-vpc-stack
    ├── staging-vpc-stack
    ├── dev-vpc-stack
    ├── prod-ec2-stack
    ├── staging-ec2-stack
    └── dev-ec2-stack
```

### 機能比較

| 機能 | マルチアカウント | 単一アカウント |
|------|----------------|---------------|
| **環境分離** | 物理的分離 | 論理的分離 |
| **セキュリティ** | 高（アカウント境界） | 中（IAM境界） |
| **コスト管理** | アカウント別 | タグベース |
| **運用複雑度** | 高 | 低 |
| **初期設定** | 複雑 | シンプル |
| **スケーラビリティ** | 高 | 中 |
| **障害影響範囲** | 限定的 | 全環境に影響可能性 |

### 認証方式の違い

#### マルチアカウント方式
```yaml
# GitHub Secrets設定例
AWS_ACCESS_KEY_ID: AKIA...CENTRAL
AWS_SECRET_ACCESS_KEY: secret...central
AWS_DEPLOYMENT_ROLE_ARN_PROD: arn:aws:iam::123456789012:role/DeployRole
AWS_DEPLOYMENT_ROLE_ARN_STAGING: arn:aws:iam::987654321098:role/DeployRole
AWS_DEPLOYMENT_ROLE_ARN_DEV: arn:aws:iam::456789012345:role/DeployRole
```

#### 単一アカウント方式
```yaml
# GitHub Secrets設定例
AWS_ACCESS_KEY_ID: AKIA...SINGLE
AWS_SECRET_ACCESS_KEY: secret...single
AWS_DEPLOYMENT_ROLE_ARN: arn:aws:iam::123456789012:role/DeployRole
```

### スタック命名規則の違い

#### マルチアカウント方式
```bash
# 各アカウントで同じ名前を使用可能
vpc-main-a1b2c3d4
ec2-main-a1b2c3d4
lambda-main-a1b2c3d4
```

#### 単一アカウント方式
```bash
# 環境プレフィックスで区別
prod-vpc-a1b2c3d4
staging-vpc-a1b2c3d4
dev-vpc-a1b2c3d4
```

## ワークフローの選択方法

### Step 1: 要件の確認

以下の質問に答えて、適切なワークフローを選択してください：

1. **組織の規模は？**
   - 大規模（100名以上）→ マルチアカウント
   - 中小規模（100名未満）→ 単一アカウント

2. **コンプライアンス要件は？**
   - 厳格（金融、医療等）→ マルチアカウント
   - 標準的 → 単一アカウント

3. **運用チーム数は？**
   - 複数チーム → マルチアカウント
   - 単一チーム → 単一アカウント

4. **予算制約は？**
   - 潤沢 → マルチアカウント
   - 限定的 → 単一アカウント

### Step 2: ワークフローの有効化

#### マルチアカウント方式を選択する場合

1. **単一アカウント用ワークフローを無効化**
```bash
# ファイル名を変更して無効化
mv .github/workflows/ci-cd-pipeline-single-account.yml \
   .github/workflows/ci-cd-pipeline-single-account.yml.disabled
```

2. **マルチアカウント用の設定を完了**
   - [マルチアカウント認証戦略ガイド](multi-account-authentication-strategies.md)を参照
   - 各AWSアカウントでIAMロールを設定
   - GitHub Secretsを設定

#### 単一アカウント方式を選択する場合

1. **マルチアカウント用ワークフローを無効化**
```bash
# ファイル名を変更して無効化
mv .github/workflows/ci-cd-pipeline.yml \
   .github/workflows/ci-cd-pipeline.yml.disabled
```

2. **単一アカウント用の設定を完了**
   - 単一AWSアカウントでIAMロールを設定
   - GitHub Secretsを設定

### Step 3: GitHub Environment設定

#### マルチアカウント方式

```yaml
# GitHub Environments
prod-environment:
  - 承認者: 2名以上
  - ブランチ制限: main のみ
  
staging-environment:
  - 承認者: 1名以上
  - ブランチ制限: main, develop

dev-environment:
  - 承認者: なし
  - ブランチ制限: なし
```

#### 単一アカウント方式

```yaml
# GitHub Environments
single-account-prod:
  - 承認者: 2名以上
  - ブランチ制限: main のみ
  
single-account-staging:
  - 承認者: 1名以上
  - ブランチ制限: main, develop

single-account-dev:
  - 承認者: なし
  - ブランチ制限: なし
```

## 設定例

### マルチアカウント方式の設定

#### 1. AWS IAM設定

```bash
# 各アカウントでロール作成
# Production Account (123456789012)
aws iam create-role \
  --role-name GitHubActionsDeploymentRole \
  --assume-role-policy-document file://trust-policy.json

# Staging Account (987654321098)
aws iam create-role \
  --role-name GitHubActionsDeploymentRole \
  --assume-role-policy-document file://trust-policy.json

# Development Account (456789012345)
aws iam create-role \
  --role-name GitHubActionsDeploymentRole \
  --assume-role-policy-document file://trust-policy.json
```

#### 2. GitHub Secrets設定

```yaml
AWS_ACCESS_KEY_ID: AKIA...CENTRAL
AWS_SECRET_ACCESS_KEY: secret...central
AWS_DEPLOYMENT_ROLE_ARN_PROD: arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole
AWS_DEPLOYMENT_ROLE_ARN_STAGING: arn:aws:iam::987654321098:role/GitHubActionsDeploymentRole
AWS_DEPLOYMENT_ROLE_ARN_DEV: arn:aws:iam::456789012345:role/GitHubActionsDeploymentRole
```

### 単一アカウント方式の設定

#### 1. AWS IAM設定

```bash
# 単一アカウントでロール作成
aws iam create-role \
  --role-name GitHubActionsDeploymentRole \
  --assume-role-policy-document file://trust-policy.json

# 環境別のポリシーを作成（オプション）
aws iam create-policy \
  --policy-name EnvironmentBasedPolicy \
  --policy-document file://environment-policy.json
```

#### 2. GitHub Secrets設定

```yaml
AWS_ACCESS_KEY_ID: AKIA...SINGLE
AWS_SECRET_ACCESS_KEY: secret...single
AWS_DEPLOYMENT_ROLE_ARN: arn:aws:iam::123456789012:role/GitHubActionsDeploymentRole
```

## 移行ガイド

### 単一アカウント → マルチアカウント

1. **新しいAWSアカウントの準備**
2. **IAMロールの設定**
3. **GitHub Secretsの更新**
4. **ワークフローファイルの切り替え**
5. **既存リソースの移行**

### マルチアカウント → 単一アカウント

1. **統合先アカウントの決定**
2. **リソースの統合計画**
3. **命名規則の変更**
4. **ワークフローファイルの切り替え**
5. **段階的な移行実行**

## トラブルシューティング

### よくある問題

#### 1. ワークフローが実行されない

**原因**: 複数のワークフローファイルが有効になっている

**解決方法**:
```bash
# 使用しないワークフローを無効化
mv .github/workflows/ci-cd-pipeline.yml \
   .github/workflows/ci-cd-pipeline.yml.disabled
```

#### 2. 認証エラー

**マルチアカウント方式**:
- AssumeRole権限の確認
- 信頼関係ポリシーの確認
- 外部IDの確認

**単一アカウント方式**:
- IAMユーザー/ロールの権限確認
- アクセスキーの有効性確認

#### 3. 環境の混在

**問題**: 異なる方式のリソースが混在している

**解決方法**:
1. 現在のリソース状況を調査
2. 統一する方式を決定
3. 段階的な移行計画を作成
4. 移行の実行

## ベストプラクティス

### 1. ワークフロー選択の原則

- **セキュリティ要件を最優先**
- **運用負荷を考慮**
- **将来の拡張性を検討**
- **チームのスキルレベルに合わせる**

### 2. 設定管理

- **Infrastructure as Code**の徹底
- **設定の文書化**
- **変更履歴の管理**
- **定期的な見直し**

### 3. 監視とメンテナンス

- **デプロイメント成功率の監視**
- **認証情報の定期ローテーション**
- **セキュリティ設定の定期監査**
- **パフォーマンスの最適化**

## 参考資料

- [GitHub Actions ワークフロー（マルチアカウント）](.github/workflows/ci-cd-pipeline.yml)
- [GitHub Actions ワークフロー（単一アカウント）](.github/workflows/ci-cd-pipeline-single-account.yml)
- [マルチアカウント認証戦略](multi-account-authentication-strategies.md)
- [GitHub Actions セットアップガイド](github-actions-setup.md)
- [ブランチ戦略](branching-strategy.md)