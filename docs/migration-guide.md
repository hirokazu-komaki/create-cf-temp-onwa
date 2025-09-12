# CloudFormation Parameter Migration Guide

## 概要

このガイドでは、旧パラメータ構造から新パラメータ構造への移行手順を説明します。

## 移行の必要性

### 旧パラメータ構造の問題点
- **一貫性の欠如**: パラメータ命名規則が統一されていない
- **複雑性**: 設定が分散し、管理が困難
- **拡張性の限界**: 新機能追加時の影響範囲が大きい
- **保守性の低下**: 設定変更時のリスクが高い

### 新パラメータ構造の利点
- **統一された命名規則**: 直感的で理解しやすい
- **パターンベース設定**: 環境に応じた最適な設定の自動適用
- **柔軟なオーバーライド**: 必要に応じた個別カスタマイズ
- **拡張性**: 新機能の追加が容易

## 移行手順

### フェーズ1: 準備段階

#### 1.1 現在の設定の確認
既存の設定ファイルを確認し、使用中のパラメータを把握します。

```bash
# 現在の設定ファイルの確認
find . -name "*-config-*.json" -exec echo "=== {} ===" \; -exec cat {} \;
```

#### 1.2 バックアップの作成
移行前に必ず現在の設定をバックアップします。

```bash
# 設定ファイルのバックアップ
mkdir -p backup/$(date +%Y%m%d)
cp *-config-*.json backup/$(date +%Y%m%d)/
```

### フェーズ2: 設定ファイルの更新

#### 2.1 パラメータマッピングの確認

旧パラメータから新パラメータへのマッピング表：

| 旧パラメータ | 新パラメータ | 備考 |
|-------------|-------------|------|
| `InstancePattern` | `ConfigurationPattern` | Basic/Advanced/Enterprise |
| `AMIId` | `InstanceAMI` | SSMパラメータから自動取得 |
| `InstanceType` | `CustomInstanceType` | パターンのオーバーライド |
| `MinSize` | `CustomMinSize` | パターンのオーバーライド |
| `MaxSize` | `CustomMaxSize` | パターンのオーバーライド |
| `DesiredCapacity` | `CustomDesiredCapacity` | パターンのオーバーライド |

#### 2.2 設定パターンの選択

環境に応じて適切な設定パターンを選択します：

**開発環境 → Basic**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Basic"
  }
}
```

**ステージング環境 → Advanced**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Advanced"
  }
}
```

**本番環境 → Enterprise**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Enterprise"
  }
}
```

#### 2.3 移行例

##### 旧設定ファイル例
```json
{
  "Parameters": {
    "ProjectName": "my-project",
    "Environment": "prod",
    "InstancePattern": "production",
    "VpcId": "vpc-12345678",
    "SubnetIds": ["subnet-12345678", "subnet-87654321"],
    "AMIId": "ami-12345678",
    "InstanceType": "m5.large",
    "MinSize": 2,
    "MaxSize": 8,
    "DesiredCapacity": 3,
    "KeyPairName": "my-keypair",
    "EnableAutoScaling": "true"
  }
}
```

##### 新設定ファイル例
```json
{
  "Parameters": {
    "ProjectName": "my-project",
    "Environment": "prod",
    "ConfigurationPattern": "Enterprise",
    "VpcId": "vpc-12345678",
    "SubnetIds": ["subnet-12345678", "subnet-87654321"],
    "KeyPairName": "my-keypair",
    "CustomInstanceType": "m5.large",
    "CustomMinSize": 2,
    "CustomMaxSize": 8,
    "CustomDesiredCapacity": 3,
    "EnableAutoScaling": "true",
    "EnableEncryption": "true",
    "EnableDetailedMonitoring": "true"
  }
}
```

### フェーズ3: 検証とテスト

#### 3.1 構文検証
新しい設定ファイルの構文を検証します。

```bash
# CloudFormationテンプレートの検証
aws cloudformation validate-template \
  --template-body file://cf-templates/compute/ec2/ec2-autoscaling.yaml

# cfn-lintによる詳細検証
cfn-lint cf-templates/compute/ec2/ec2-autoscaling.yaml
```

#### 3.2 ドライラン実行
実際のリソース作成前にドライランを実行します。

```bash
# Change Setの作成（実際のリソースは作成されない）
aws cloudformation create-change-set \
  --stack-name test-migration-stack \
  --template-body file://cf-templates/compute/ec2/ec2-autoscaling.yaml \
  --parameters file://your-new-config.json \
  --change-set-name migration-test \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Change Setの内容確認
aws cloudformation describe-change-set \
  --stack-name test-migration-stack \
  --change-set-name migration-test

# Change Setの削除（テスト後）
aws cloudformation delete-change-set \
  --stack-name test-migration-stack \
  --change-set-name migration-test
```

#### 3.3 統合テストの実行
プロジェクトの統合テストを実行して、すべての機能が正常に動作することを確認します。

```bash
# 統合テストの実行
python scripts/master-integration-test.py --verbose
```

### フェーズ4: 本番適用

#### 4.1 段階的デプロイメント
開発環境から順次適用していきます。

1. **開発環境での適用**
```bash
# 開発環境用設定での適用
aws cloudformation deploy \
  --template-file cf-templates/compute/ec2/ec2-autoscaling.yaml \
  --stack-name dev-my-project-ec2 \
  --parameter-overrides file://dev-config-new.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

2. **ステージング環境での適用**
```bash
# ステージング環境用設定での適用
aws cloudformation deploy \
  --template-file cf-templates/compute/ec2/ec2-autoscaling.yaml \
  --stack-name staging-my-project-ec2 \
  --parameter-overrides file://staging-config-new.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

3. **本番環境での適用**
```bash
# 本番環境用設定での適用（要承認）
aws cloudformation deploy \
  --template-file cf-templates/compute/ec2/ec2-autoscaling.yaml \
  --stack-name prod-my-project-ec2 \
  --parameter-overrides file://prod-config-new.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

#### 4.2 動作確認
各環境での動作確認を実施します。

```bash
# スタック状態の確認
aws cloudformation describe-stacks --stack-name your-stack-name

# リソースの確認
aws cloudformation list-stack-resources --stack-name your-stack-name

# Auto Scaling Groupの確認
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names your-asg-name
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. パラメータ不足エラー
**エラー**: `Parameters: [XXX] must have values`

**解決方法**: 必須パラメータが設定されているか確認
```json
{
  "Parameters": {
    "ProjectName": "必須",
    "Environment": "必須", 
    "ConfigurationPattern": "必須",
    "VpcId": "必須",
    "SubnetIds": "必須"
  }
}
```

#### 2. 不正なパラメータ値エラー
**エラー**: `Value (XXX) for parameter YYY is invalid`

**解決方法**: AllowedValuesを確認して正しい値を設定
```json
{
  "ConfigurationPattern": "Basic", // Basic, Advanced, Enterprise のみ
  "EnableAutoScaling": "true",     // true, false のみ
  "EnableEncryption": "false"      // true, false のみ
}
```

#### 3. リソース依存関係エラー
**エラー**: `Resource XXX depends on YYY`

**解決方法**: 条件付きリソースの依存関係を確認
- Auto Scaling Groupは `EnableAutoScaling: "true"` の場合のみ作成
- 監視ダッシュボードは Advanced/Enterprise パターンの場合のみ作成

#### 4. IAM権限エラー
**エラー**: `User: XXX is not authorized to perform: YYY`

**解決方法**: 必要なIAM権限を確認
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "ec2:*",
        "autoscaling:*",
        "iam:*",
        "logs:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## ロールバック手順

移行に問題が発生した場合のロールバック手順：

### 1. 緊急ロールバック
```bash
# 前のバージョンに戻す
aws cloudformation cancel-update-stack --stack-name your-stack-name

# または前のテンプレートで更新
aws cloudformation deploy \
  --template-file backup/old-template.yaml \
  --stack-name your-stack-name \
  --parameter-overrides file://backup/old-config.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

### 2. 段階的ロールバック
1. 本番環境を旧設定に戻す
2. ステージング環境を旧設定に戻す  
3. 開発環境で問題を修正
4. 再度段階的に適用

## 移行チェックリスト

### 移行前チェック
- [ ] 現在の設定ファイルをバックアップ済み
- [ ] 新パラメータ構造を理解済み
- [ ] 適切な設定パターンを選択済み
- [ ] 必要なカスタマイズを特定済み
- [ ] IAM権限を確認済み

### 移行中チェック
- [ ] 構文検証が成功
- [ ] ドライランが成功
- [ ] 統合テストが成功
- [ ] 開発環境での動作確認が成功
- [ ] ステージング環境での動作確認が成功

### 移行後チェック
- [ ] 本番環境での動作確認が成功
- [ ] 監視アラートが正常に動作
- [ ] ログ出力が正常
- [ ] Auto Scalingが正常に動作
- [ ] セキュリティ設定が正常

## サポート

移行に関する質問や問題が発生した場合：

1. **ドキュメント確認**: [新パラメータ構造ドキュメント](./new-parameter-structure.md)
2. **ログ確認**: CloudFormationイベントとCloudWatchログを確認
3. **テスト実行**: 統合テストスクリプトで問題を特定
4. **段階的適用**: 問題のある環境のみロールバックして修正

移行は慎重に段階的に実施し、各段階で十分な検証を行うことが重要です。