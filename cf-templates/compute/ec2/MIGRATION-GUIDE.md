# CloudFormation パラメータ移行ガイド

## 概要

このガイドは、CloudFormationテンプレートのパラメータ構造の変更に伴う設定ファイルの移行方法を説明します。
Phase 3の完了により、レガシーパラメータのサポートが終了し、新しい統一されたパラメータ構造のみがサポートされます。

## 移行が必要なパラメータ

### 削除されたレガシーパラメータ

以下のパラメータは削除され、新しいパラメータに置き換えられました：

| 旧パラメータ名 | 新パラメータ名 | 説明 |
|---|---|---|
| `InstancePattern` | `ConfigurationPattern` | 設定パターンの指定 |
| `AMIId` | `InstanceAMI` | AMI IDの指定 |
| `InstanceType` | `CustomInstanceType` | インスタンスタイプのオーバーライド |
| `MinSize` | `CustomMinSize` | Auto Scaling Group最小サイズのオーバーライド |
| `MaxSize` | `CustomMaxSize` | Auto Scaling Group最大サイズのオーバーライド |
| `DesiredCapacity` | `CustomDesiredCapacity` | Auto Scaling Group希望サイズのオーバーライド |
| `TargetGroupArn` | `TargetGroupArns` | ターゲットグループARN（複数対応） |
| `EnableEBSOptimization` | （削除） | パターンベースで自動設定 |

## 設定ファイル移行例

### Basic設定の移行

**旧設定（Phase 1/2）:**
```json
{
  "Parameters": {
    "InstancePattern": "Basic",
    "ProjectName": "MyApp",
    "Environment": "dev",
    "InstanceType": "t3.micro",
    "AMIId": "ami-0228232d282f16465",
    "KeyPairName": "my-dev-keypair",
    "VpcId": "vpc-0eaf2cdc55cae20d5",
    "SubnetIds": ["subnet-04590383ce70d10ad", "subnet-062d1f6a49865334a"],
    "EnableDetailedMonitoring": "false",
    "EnableAutoScaling": "false",
    "MinSize": 1,
    "MaxSize": 1,
    "DesiredCapacity": 1
  }
}
```

**新設定（Phase 3）:**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Basic",
    "ProjectName": "MyApp",
    "Environment": "dev",
    "CustomInstanceType": "t3.micro",
    "InstanceAMI": "ami-0228232d282f16465",
    "KeyPairName": "my-dev-keypair",
    "VpcId": "vpc-0eaf2cdc55cae20d5",
    "SubnetIds": ["subnet-04590383ce70d10ad", "subnet-062d1f6a49865334a"],
    "EnableDetailedMonitoring": "false",
    "EnableAutoScaling": "false",
    "CustomMinSize": 1,
    "CustomMaxSize": 1,
    "CustomDesiredCapacity": 1
  }
}
```

### Advanced設定の移行

**旧設定（Phase 1/2）:**
```json
{
  "Parameters": {
    "InstancePattern": "Advanced",
    "ProjectName": "MyWebApp",
    "Environment": "staging",
    "InstanceType": "t3.medium",
    "AMIId": "ami-0abcdef1234567890",
    "MinSize": 2,
    "MaxSize": 6,
    "DesiredCapacity": 2,
    "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/1234567890123456",
    "EnableEBSOptimization": "true"
  }
}
```

**新設定（Phase 3）:**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Advanced",
    "ProjectName": "MyWebApp",
    "Environment": "staging",
    "CustomInstanceType": "t3.medium",
    "InstanceAMI": "ami-0abcdef1234567890",
    "CustomMinSize": 2,
    "CustomMaxSize": 6,
    "CustomDesiredCapacity": 2,
    "TargetGroupArns": ["arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/1234567890123456"]
  }
}
```

### Enterprise設定の移行

**旧設定（Phase 1/2）:**
```json
{
  "Parameters": {
    "InstancePattern": "Enterprise",
    "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/web-targets/1234567890123456"
  }
}
```

**新設定（Phase 3）:**
```json
{
  "Parameters": {
    "ConfigurationPattern": "Enterprise",
    "TargetGroupArns": [
      "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/web-targets/1234567890123456",
      "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/api-targets/1234567890123457"
    ]
  }
}
```

## 重要な変更点

### 1. 必須パラメータ

以下のパラメータは必須になりました（デフォルト値が削除されました）：

- `ProjectName`: プロジェクト名（3-50文字、英字で始まり英数字で終わる）
- `ConfigurationPattern`: 設定パターン（Basic、Advanced、Enterprise）

### 2. パラメータ検証の強化

- **ProjectName**: より厳密な命名規則（3-50文字、英字で始まり英数字で終わる）
- **CustomInstanceType**: EC2インスタンスタイプの形式検証
- **カスタムサイジング**: MinSize、MaxSize、DesiredCapacityの一貫性チェック
- **機能制限**: パターンに応じた機能の制限（例：BasicパターンではスポットインスタンスNG）

### 3. TargetGroupArnsの複数対応

- 旧: `TargetGroupArn` (単一ARN文字列)
- 新: `TargetGroupArns` (ARN配列)

単一のターゲットグループの場合も配列形式で指定してください。

## エラーメッセージと対処法

### よくあるエラーと解決方法

#### 1. レガシーパラメータエラー
```
Template format error: Unrecognized parameter: InstancePattern
```
**対処法**: `InstancePattern` を `ConfigurationPattern` に変更してください。

#### 2. 必須パラメータエラー
```
Parameters: [ProjectName] must have values
```
**対処法**: `ProjectName` パラメータを追加し、有効な値を設定してください。

#### 3. パラメータ形式エラー
```
Parameter 'ProjectName' must match pattern '^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$'
```
**対処法**: プロジェクト名を英字で始まり、英数字で終わる形式に変更してください。

#### 4. サイジング一貫性エラー
```
CustomMinSizeはCustomMaxSize以下である必要があります
```
**対処法**: カスタムサイジングパラメータの値を見直し、MinSize ≤ DesiredCapacity ≤ MaxSize の関係を保ってください。

#### 5. 機能制限エラー
```
スポットインスタンスはAdvanced/Enterpriseパターンでのみ使用可能です
```
**対処法**: Basicパターンでは `EnableSpotInstances` を `false` に設定するか、パターンをAdvanced/Enterpriseに変更してください。

## 移行チェックリスト

### 設定ファイル更新

- [ ] `InstancePattern` → `ConfigurationPattern` に変更
- [ ] `AMIId` → `InstanceAMI` に変更
- [ ] `InstanceType` → `CustomInstanceType` に変更
- [ ] `MinSize` → `CustomMinSize` に変更
- [ ] `MaxSize` → `CustomMaxSize` に変更
- [ ] `DesiredCapacity` → `CustomDesiredCapacity` に変更
- [ ] `TargetGroupArn` → `TargetGroupArns` (配列形式) に変更
- [ ] `EnableEBSOptimization` パラメータを削除
- [ ] `ProjectName` の形式を確認（3-50文字、英字開始、英数字終了）
- [ ] 必須パラメータ（`ProjectName`, `ConfigurationPattern`）を設定

### 検証

- [ ] CloudFormation template validation を実行
- [ ] cfn-lint による検証を実行
- [ ] パラメータの一貫性を確認
- [ ] 機能制限に違反していないことを確認

### テスト

- [ ] 新しい設定でのドライラン実行
- [ ] GitHub Actions ワークフローでのテスト
- [ ] 実際のスタック作成/更新のテスト

## サポート

移行に関する質問や問題が発生した場合は、以下を参照してください：

1. **テンプレート検証**: `aws cloudformation validate-template` コマンドを使用
2. **Lint検証**: `cfn-lint` ツールを使用
3. **ドキュメント**: `cf-templates/compute/ec2/README.md` を参照
4. **サンプル設定**: 更新された設定ファイル例を参照

## 移行完了後の利点

- **一貫性**: 統一されたパラメータ命名規則
- **検証**: 強化されたパラメータ検証とエラーメッセージ
- **柔軟性**: パターンベースのデフォルト値とカスタムオーバーライドの組み合わせ
- **保守性**: クリーンで理解しやすいテンプレート構造
- **拡張性**: 新機能の追加が容易な設計