# 新パラメータ構造ドキュメント

## 概要

CloudFormation Parameter Migration プロジェクトにより、EC2 Auto Scalingテンプレートのパラメータ構造が統一され、より使いやすく保守性の高い形式に更新されました。

## 新パラメータ構造の特徴

### 1. 統一された命名規則

- **一貫性**: すべてのパラメータが統一された命名規則に従います
- **可読性**: パラメータ名から機能が明確に理解できます
- **階層性**: 関連するパラメータがグループ化されています

### 2. 設定パターンベースの構成

#### ConfigurationPattern パラメータ
```yaml
ConfigurationPattern:
  Type: String
  Description: 設定パターン - リソース設定のベースライン決定（必須）
  AllowedValues: [Basic, Advanced, Enterprise]
```

各パターンの特徴：
- **Basic**: 開発・テスト環境向けの最小構成
- **Advanced**: ステージング環境向けの中規模構成
- **Enterprise**: 本番環境向けの高可用性・高性能構成

### 3. オーバーライド可能なパラメータ

設定パターンのデフォルト値を個別にオーバーライドできます：

#### インスタンス設定
```yaml
CustomInstanceType:
  Type: String
  Description: カスタムインスタンスタイプ - ConfigurationPatternのデフォルトをオーバーライド
  Default: ''

CustomMinSize:
  Type: Number
  Description: カスタム最小サイズ - ConfigurationPatternのデフォルトをオーバーライド（0=未設定）
  Default: 0

CustomMaxSize:
  Type: Number
  Description: カスタム最大サイズ - ConfigurationPatternのデフォルトをオーバーライド（0=未設定）
  Default: 0
```

#### ストレージ設定
```yaml
RootVolumeSize:
  Type: Number
  Description: ルートボリュームサイズ（GB） - ConfigurationPatternのデフォルトをオーバーライド（0=未設定）
  Default: 0

RootVolumeType:
  Type: String
  Description: ルートボリュームタイプ - ConfigurationPatternのデフォルトをオーバーライド
  Default: ''
```

### 4. 機能制御パラメータ

#### セキュリティ機能
```yaml
EnableEncryption:
  Type: String
  Description: EBS暗号化を有効にする - Advanced/Enterprise機能
  Default: 'false'
  AllowedValues: ['true', 'false']

KMSKeyId:
  Type: String
  Description: 暗号化用のKMSキーID - EnableEncryption=trueの場合に使用
  Default: ''
```

#### 監視機能
```yaml
EnableDetailedMonitoring:
  Type: String
  Description: 詳細監視を有効にする - Advanced/Enterprise機能
  Default: 'false'
  AllowedValues: ['true', 'false']
```

#### Auto Scaling機能
```yaml
EnableAutoScaling:
  Type: String
  Description: Auto Scalingを有効にする
  Default: 'true'
  AllowedValues: ['true', 'false']

EnableSpotInstances:
  Type: String
  Description: スポットインスタンスを使用する
  Default: 'false'
  AllowedValues: ['true', 'false']
```

## パラメータマッピング

### Basic パターン
```yaml
Basic:
  PrimaryType: t3.micro
  SecondaryType: t3.small
  MinSize: 1
  MaxSize: 3
  DesiredCapacity: 1
  RootVolumeSize: 20
  RootVolumeType: gp3
  EnableEncryption: false
  EnableDetailedMonitoring: false
  EnableSpotInstances: true
```

### Advanced パターン
```yaml
Advanced:
  PrimaryType: t3.medium
  SecondaryType: t3.large
  MinSize: 2
  MaxSize: 6
  DesiredCapacity: 2
  RootVolumeSize: 30
  RootVolumeType: gp3
  EnableEncryption: true
  EnableDetailedMonitoring: true
  EnableSpotInstances: true
```

### Enterprise パターン
```yaml
Enterprise:
  PrimaryType: m5.large
  SecondaryType: m5.xlarge
  MinSize: 3
  MaxSize: 10
  DesiredCapacity: 3
  RootVolumeSize: 50
  RootVolumeType: gp3
  EnableEncryption: true
  EnableDetailedMonitoring: true
  EnableSpotInstances: false
```

## 条件ロジック

新パラメータ構造では、以下の条件が自動的に適用されます：

### パターンベース条件
```yaml
UseBasicPattern: !Equals [!Ref ConfigurationPattern, Basic]
UseAdvancedPattern: !Equals [!Ref ConfigurationPattern, Advanced]
UseEnterprisePattern: !Equals [!Ref ConfigurationPattern, Enterprise]
IsAdvancedOrEnterprise: !Or [!Condition UseAdvancedPattern, !Condition UseEnterprisePattern]
```

### オーバーライド条件
```yaml
UseCustomInstanceType: !Not [!Equals [!Ref CustomInstanceType, '']]
HasCustomMinSize: !Not [!Equals [!Ref CustomMinSize, 0]]
HasCustomMaxSize: !Not [!Equals [!Ref CustomMaxSize, 0]]
```

### 機能制御条件
```yaml
EnableMonitoring: !Equals [!Ref EnableDetailedMonitoring, 'true']
EnableEBSEncryption: !Equals [!Ref EnableEncryption, 'true']
CreateAutoScalingGroup: !Equals [!Ref EnableAutoScaling, 'true']
```

## 使用例

### Basic環境での設定例
```json
{
  "Parameters": {
    "ProjectName": "my-project",
    "Environment": "dev",
    "ConfigurationPattern": "Basic",
    "VpcId": "vpc-12345678",
    "SubnetIds": ["subnet-12345678", "subnet-87654321"],
    "KeyPairName": "my-keypair"
  }
}
```

### Advanced環境でのカスタマイズ例
```json
{
  "Parameters": {
    "ProjectName": "my-project",
    "Environment": "staging",
    "ConfigurationPattern": "Advanced",
    "VpcId": "vpc-12345678",
    "SubnetIds": ["subnet-12345678", "subnet-87654321"],
    "CustomInstanceType": "m5.large",
    "CustomMinSize": 3,
    "CustomMaxSize": 8,
    "EnableEncryption": "true",
    "KMSKeyId": "arn:aws:kms:ap-northeast-1:123456789012:key/12345678-1234-1234-1234-123456789012"
  }
}
```

### Enterprise環境での完全設定例
```json
{
  "Parameters": {
    "ProjectName": "my-project",
    "Environment": "prod",
    "ConfigurationPattern": "Enterprise",
    "VpcId": "vpc-12345678",
    "SubnetIds": ["subnet-12345678", "subnet-87654321", "subnet-11111111"],
    "CustomInstanceType": "m5.2xlarge",
    "RootVolumeSize": 100,
    "EnableEncryption": "true",
    "EnableDetailedMonitoring": "true",
    "EnableNitroEnclave": "true",
    "KMSKeyId": "arn:aws:kms:ap-northeast-1:123456789012:key/12345678-1234-1234-1234-123456789012"
  }
}
```

## 監視とアラート

新パラメータ構造では、以下の監視リソースが自動的に作成されます：

### CloudWatchアラーム
- **HighCPUAlarm**: CPU使用率80%超過時のスケールアップトリガー
- **LowCPUAlarm**: CPU使用率20%未満時のスケールダウントリガー

### Auto Scalingポリシー
- **ScaleUpPolicy**: インスタンス数を1つ増加
- **ScaleDownPolicy**: インスタンス数を1つ減少

### CloudWatchダッシュボード
Advanced/Enterpriseパターンでは、以下のメトリクスを表示するダッシュボードが作成されます：
- EC2メトリクス（CPU、ネットワーク）
- Auto Scalingメトリクス（インスタンス数、容量）

## セキュリティ機能

### EBS暗号化
- Advanced/Enterpriseパターンでデフォルト有効
- カスタムKMSキーの指定可能
- 削除時の自動削除設定

### IAMロール
- CloudWatchエージェント用の権限
- SSM管理用の権限
- 最小権限の原則に基づく設計

### セキュリティグループ
- EC2インスタンス用セキュリティグループ
- ALB用セキュリティグループ
- 必要最小限のポート開放

## 出力値

テンプレートは以下の出力値を提供します：

### Auto Scaling関連
- `AutoScalingGroupName`: Auto Scaling Group名
- `AutoScalingGroupArn`: Auto Scaling Group ARN

### Launch Template関連
- `LaunchTemplateId`: Launch Template ID
- `LaunchTemplateVersion`: Launch Template最新バージョン

### セキュリティ関連
- `EC2SecurityGroupId`: EC2セキュリティグループID
- `ALBSecurityGroupId`: ALBセキュリティグループID

### IAM関連
- `IAMRoleArn`: EC2 IAMロールARN
- `InstanceProfileArn`: EC2インスタンスプロファイルARN

### ログ関連
- `EC2LogGroupName`: EC2ロググループ名

これらの出力値は、他のCloudFormationスタックから参照可能です。