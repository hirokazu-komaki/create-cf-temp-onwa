# マルチアカウント設定例

このドキュメントでは、複数のAWSアカウントを使用したCloudFormationテンプレートのデプロイ設定例を示します。

## アカウント構成例

### 典型的なマルチアカウント構成

```
組織構造:
├── 本番アカウント (123456789012)
│   ├── us-east-1 (メインリージョン)
│   └── us-west-2 (DR リージョン)
├── ステージングアカウント (987654321098)
│   └── us-east-1
├── 開発アカウント (555666777888)
│   └── us-east-1
└── セキュリティアカウント (111222333444)
    └── us-east-1 (ログ集約・監査)
```

## 設定ファイル例

### 1. 本番環境用設定

**ファイル名**: `vpc-config-production.json`

```json
{
  "Parameters": {
    "AWSAccount": "123456789012",
    "Region": "us-east-1",
    "ProjectName": "WebApp",
    "Environment": "production",
    "VpcCidr": "10.0.0.0/16",
    "SubnetPattern": "Enterprise",
    "EnableNatGateway": "true",
    "EnableVpcFlowLogs": "true",
    "EnableDnsHostnames": "true",
    "EnableDnsSupport": "true"
  },
  "Tags": {
    "Owner": "Platform Team",
    "CostCenter": "Engineering",
    "Environment": "Production",
    "Compliance": "SOC2",
    "BackupRequired": "true",
    "WellArchitected": "All Pillars"
  },
  "Description": "本番環境用VPC設定 - 高可用性とセキュリティを重視"
}
```

### 2. ステージング環境用設定

**ファイル名**: `vpc-config-staging.json`

```json
{
  "Parameters": {
    "AWSAccount": "987654321098",
    "Region": "us-east-1",
    "ProjectName": "WebApp",
    "Environment": "staging",
    "VpcCidr": "10.1.0.0/16",
    "SubnetPattern": "Advanced",
    "EnableNatGateway": "true",
    "EnableVpcFlowLogs": "false",
    "EnableDnsHostnames": "true",
    "EnableDnsSupport": "true"
  },
  "Tags": {
    "Owner": "Development Team",
    "CostCenter": "Engineering",
    "Environment": "Staging",
    "AutoShutdown": "true",
    "WellArchitected": "Reliability,Security"
  },
  "Description": "ステージング環境用VPC設定 - コスト最適化を重視"
}
```

### 3. 開発環境用設定

**ファイル名**: `vpc-config-development.json`

```json
{
  "Parameters": {
    "AWSAccount": "555666777888",
    "Region": "us-east-1",
    "ProjectName": "WebApp",
    "Environment": "development",
    "VpcCidr": "10.2.0.0/16",
    "SubnetPattern": "Basic",
    "EnableNatGateway": "false",
    "EnableVpcFlowLogs": "false",
    "EnableDnsHostnames": "true",
    "EnableDnsSupport": "true"
  },
  "Tags": {
    "Owner": "Development Team",
    "CostCenter": "Engineering",
    "Environment": "Development",
    "AutoShutdown": "true",
    "WellArchitected": "CostOptimization"
  },
  "Description": "開発環境用VPC設定 - 最小限の構成でコスト重視"
}
```

### 4. クロスアカウント参照設定

**ファイル名**: `lambda-config-with-cross-account.json`

```json
{
  "Parameters": {
    "AWSAccount": "123456789012",
    "Region": "us-east-1",
    "ProjectName": "DataProcessor",
    "Environment": "production",
    "FunctionName": "DataProcessorFunction",
    "Runtime": "python3.12",
    "MemorySize": 512,
    "Timeout": 300,
    "LogRetentionDays": 30,
    "CrossAccountLogDestination": "arn:aws:logs:us-east-1:111222333444:destination:CentralLogging",
    "CrossAccountKmsKeyId": "arn:aws:kms:us-east-1:111222333444:key/12345678-1234-1234-1234-123456789012"
  },
  "Tags": {
    "Owner": "Data Team",
    "CostCenter": "Analytics",
    "Environment": "Production",
    "DataClassification": "Confidential",
    "WellArchitected": "Security,OperationalExcellence"
  },
  "Description": "本番環境用Lambda設定 - セキュリティアカウントとの連携"
}
```

## GitHub Secrets設定例

### 必要なSecrets一覧

```bash
# デフォルト認証情報
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEPLOYMENT_ROLE_ARN=arn:aws:iam::123456789012:role/DefaultDeploymentRole

# 本番アカウント (123456789012)
AWS_ACCESS_KEY_ID_123456789012=AKIAIOSFODNN7PROD123
AWS_SECRET_ACCESS_KEY_123456789012=wJalrXUtnFEMI/K7MDENG/bPxRfiCYPROD123
AWS_DEPLOYMENT_ROLE_ARN_123456789012=arn:aws:iam::123456789012:role/ProdDeploymentRole

# ステージングアカウント (987654321098)
AWS_ACCESS_KEY_ID_987654321098=AKIAIOSFODNN7STAG098
AWS_SECRET_ACCESS_KEY_987654321098=wJalrXUtnFEMI/K7MDENG/bPxRfiCYSTAG098
AWS_DEPLOYMENT_ROLE_ARN_987654321098=arn:aws:iam::987654321098:role/StagingDeploymentRole

# 開発アカウント (555666777888)
AWS_ACCESS_KEY_ID_555666777888=AKIAIOSFODNN7DEV888
AWS_SECRET_ACCESS_KEY_555666777888=wJalrXUtnFEMI/K7MDENG/bPxRfiCYDEV888
AWS_DEPLOYMENT_ROLE_ARN_555666777888=arn:aws:iam::555666777888:role/DevDeploymentRole

# セキュリティアカウント (111222333444)
AWS_ACCESS_KEY_ID_111222333444=AKIAIOSFODNN7SEC444
AWS_SECRET_ACCESS_KEY_111222333444=wJalrXUtnFEMI/K7MDENG/bPxRfiCYSEC444
AWS_DEPLOYMENT_ROLE_ARN_111222333444=arn:aws:iam::111222333444:role/SecurityDeploymentRole
```

## デプロイフロー例

### 1. 開発からステージングへ

```bash
# 1. 開発環境でテスト
git checkout feature/new-vpc-config
git add cf-templates/networking/vpc/vpc-config-development.json
git commit -m "feat: add development VPC configuration"
git push origin feature/new-vpc-config

# 2. developブランチにマージ
# → ステージング環境 (987654321098) に自動デプロイ

# 3. mainブランチにマージ
# → 本番環境 (123456789012) に手動承認後デプロイ
```

### 2. 緊急修正の場合

```bash
# 1. 本番環境で問題発生
git checkout main
git checkout -b hotfix/security-group-fix

# 2. 設定修正
vim cf-templates/networking/vpc/vpc-config-production.json

# 3. 緊急デプロイ
git add .
git commit -m "fix: resolve security group configuration issue"
git push origin hotfix/security-group-fix

# → 本番環境 (123456789012) に緊急承認後デプロイ
```

## 環境別の設定パターン

### 本番環境の特徴

- **セキュリティ**: 最高レベルのセキュリティ設定
- **可用性**: マルチAZ、自動バックアップ
- **監視**: 詳細な監視とアラート
- **コンプライアンス**: 監査ログ、暗号化必須

```json
{
  "Parameters": {
    "SubnetPattern": "Enterprise",
    "EnableEncryption": "true",
    "EnableBackup": "true",
    "EnableDetailedMonitoring": "true",
    "MultiAZ": "true"
  }
}
```

### ステージング環境の特徴

- **テスト**: 本番環境に近い構成
- **コスト**: 適度なコスト最適化
- **自動化**: 自動テストとデプロイ

```json
{
  "Parameters": {
    "SubnetPattern": "Advanced",
    "EnableEncryption": "true",
    "EnableBackup": "false",
    "EnableDetailedMonitoring": "false",
    "MultiAZ": "false"
  }
}
```

### 開発環境の特徴

- **コスト**: 最大限のコスト最適化
- **柔軟性**: 開発者の自由度を重視
- **自動停止**: 非使用時の自動停止

```json
{
  "Parameters": {
    "SubnetPattern": "Basic",
    "EnableEncryption": "false",
    "EnableBackup": "false",
    "EnableDetailedMonitoring": "false",
    "MultiAZ": "false",
    "AutoShutdown": "true"
  }
}
```

## トラブルシューティング

### よくある問題

#### 1. 認証情報が見つからない

**エラー**: `Missing required secrets: AWS_ACCESS_KEY_ID_123456789012`

**解決方法**:
1. GitHub Secretsに該当するアカウントの認証情報が設定されているか確認
2. アカウントIDが正確に12桁で設定されているか確認
3. Secret名の命名規則が正しいか確認

#### 2. アカウントIDの不一致

**エラー**: `Provided account ID (123456789012) doesn't match actual account ID (987654321098)`

**解決方法**:
1. 設定ファイルのAWSAccountパラメータを確認
2. 認証情報が正しいアカウントのものか確認
3. AssumeRoleの設定が正しいか確認

#### 3. 権限不足

**エラー**: `User is not authorized to perform: cloudformation:CreateStack`

**解決方法**:
1. IAMユーザーまたはロールの権限を確認
2. AssumeRoleの信頼関係を確認
3. リソースレベルの権限制限を確認

## セキュリティベストプラクティス

### 1. 認証情報の管理

- **最小権限**: 必要最小限の権限のみ付与
- **ローテーション**: 定期的な認証情報のローテーション
- **監査**: アクセスログの定期的な確認

### 2. アカウント分離

- **環境分離**: 本番、ステージング、開発の完全分離
- **責任分離**: 各アカウントの責任範囲を明確化
- **ネットワーク分離**: VPCレベルでの分離

### 3. 監視とログ

- **CloudTrail**: すべてのAPI呼び出しを記録
- **Config**: リソース設定の変更を追跡
- **GuardDuty**: セキュリティ脅威の検出

## 参考リンク

- [AWS Organizations ベストプラクティス](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices.html)
- [マルチアカウント戦略](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)