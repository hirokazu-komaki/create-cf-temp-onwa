# 使用方法ガイド

## 目次
1. [基本的な使用方法](#基本的な使用方法)
2. [設定ファイルのカスタマイズ](#設定ファイルのカスタマイズ)
3. [テンプレートのデプロイ](#テンプレートのデプロイ)
4. [クロススタック統合](#クロススタック統合)
5. [監視とメンテナンス](#監視とメンテナンス)

## 基本的な使用方法

### ステップ1: 適切なパターンの選択

環境と要件に応じてパターンを選択します：

```bash
# 開発環境の場合
cp cf-templates/networking/vpc/vpc-config-basic.json my-config.json

# ステージング環境の場合
cp cf-templates/networking/vpc/vpc-config-advanced.json my-config.json

# 本番環境の場合
cp cf-templates/networking/vpc/vpc-config-enterprise.json my-config.json
```

### ステップ2: 設定のカスタマイズ

```json
{
  "Parameters": {
    "ProjectName": "MyWebApp",           # プロジェクト名を変更
    "Environment": "dev",               # 環境を指定
    "VpcCidr": "10.1.0.0/16",          # CIDR範囲を調整
    "SubnetPattern": "Basic"            # サブネットパターンを選択
  }
}
```

### ステップ3: 設定の検証

```bash
# 設定ファイルの妥当性を検証
python cf-templates/utilities/validate-config.py \
  --config my-config.json \
  --template cf-templates/networking/vpc/vpc-template.yaml
```

### ステップ4: デプロイメント

```bash
# CloudFormationスタックを作成
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://cf-templates/networking/vpc/vpc-template.yaml \
  --parameters file://my-config.json \
  --capabilities CAPABILITY_IAM
```

## 設定ファイルのカスタマイズ

### 基本パラメータ

すべての設定ファイルに共通するパラメータ：

```json
{
  "Parameters": {
    "ProjectName": "string",      # プロジェクト名（必須）
    "Environment": "dev|staging|prod",  # 環境（必須）
    "Region": "us-east-1",        # AWSリージョン
    "AvailabilityZones": [        # 使用するAZ
      "us-east-1a",
      "us-east-1b"
    ]
  },
  "Tags": {                       # リソースタグ
    "Owner": "Team Name",
    "CostCenter": "Department",
    "Environment": "Development"
  }
}
```

### サービス固有パラメータ

#### VPC設定例
```json
{
  "Parameters": {
    "VpcCidr": "10.0.0.0/16",           # VPCのCIDR範囲
    "SubnetPattern": "Basic",            # サブネットパターン
    "EnableDnsHostnames": "true",        # DNS hostname有効化
    "EnableDnsSupport": "true",          # DNS support有効化
    "EnableNatGateway": "true",          # NAT Gateway有効化
    "SingleNatGateway": "false"          # 単一NAT Gateway使用
  }
}
```

#### EC2設定例
```json
{
  "Parameters": {
    "InstanceType": "t3.medium",         # インスタンスタイプ
    "KeyPairName": "my-keypair",         # キーペア名
    "EnableAutoScaling": "true",         # オートスケーリング有効化
    "MinSize": 2,                        # 最小インスタンス数
    "MaxSize": 6,                        # 最大インスタンス数
    "DesiredCapacity": 2                 # 希望インスタンス数
  }
}
```

#### Lambda設定例
```json
{
  "Parameters": {
    "Runtime": "python3.9",             # ランタイム
    "MemorySize": 512,                   # メモリサイズ（MB）
    "Timeout": 300,                      # タイムアウト（秒）
    "EnableVPC": "true",                 # VPC統合有効化
    "EnableXRayTracing": "true"          # X-Rayトレーシング有効化
  }
}
```

### パターン別設定の違い

#### Basic パターン
- 最小限の設定
- コスト最適化重視
- 開発・テスト環境向け

```json
{
  "Parameters": {
    "InstanceType": "t3.micro",
    "EnableDetailedMonitoring": "false",
    "EnableAutoScaling": "false"
  }
}
```

#### Advanced パターン
- 高可用性設定
- 監視・ログ記録強化
- ステージング環境向け

```json
{
  "Parameters": {
    "InstanceType": "t3.medium",
    "EnableDetailedMonitoring": "true",
    "EnableAutoScaling": "true",
    "EnableXRayTracing": "true"
  }
}
```

#### Enterprise パターン
- 最高レベルのセキュリティ
- 完全なコンプライアンス対応
- 本番環境向け

```json
{
  "Parameters": {
    "InstanceType": "m5.large",
    "EnableDetailedMonitoring": "true",
    "EnableAutoScaling": "true",
    "EnableXRayTracing": "true",
    "EnableEncryption": "true",
    "EnableWAF": "true"
  }
}
```

## テンプレートのデプロイ

### AWS CLIを使用したデプロイ

#### 新規スタック作成
```bash
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters file://config.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --tags Key=Environment,Value=dev Key=Owner,Value=MyTeam
```

#### スタック更新
```bash
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters file://config.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

#### スタック削除
```bash
aws cloudformation delete-stack --stack-name my-stack
```

### パラメータ処理ユーティリティの使用

```bash
# JSON設定をCloudFormationパラメータ形式に変換
python cf-templates/utilities/parameter-processor/parameter-processor.py \
  --input my-config.json \
  --output cf-parameters.json \
  --template cf-templates/networking/vpc/vpc-template.yaml

# 変換されたパラメータでデプロイ
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters file://cf-parameters.json
```

### デプロイメント戦略

#### 段階的デプロイメント
```bash
# 1. 基盤インフラ（VPC、IAM）
aws cloudformation create-stack --stack-name foundation-stack ...

# 2. ネットワーク（ELB、Route53）
aws cloudformation create-stack --stack-name network-stack ...

# 3. コンピューティング（EC2、Lambda）
aws cloudformation create-stack --stack-name compute-stack ...

# 4. 統合サービス（API Gateway、CloudWatch）
aws cloudformation create-stack --stack-name integration-stack ...
```

#### ブルーグリーンデプロイメント
```bash
# グリーン環境を作成
aws cloudformation create-stack \
  --stack-name my-app-green \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=green

# トラフィックを切り替え後、ブルー環境を削除
aws cloudformation delete-stack --stack-name my-app-blue
```

## クロススタック統合

### Outputs/Imports の使用

#### スタックAでのOutputs定義
```yaml
Outputs:
  VPCId:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub "${AWS::StackName}-VPC-ID"
  
  PrivateSubnetIds:
    Description: Private Subnet IDs
    Value: !Join [",", [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub "${AWS::StackName}-Private-Subnet-IDs"
```

#### スタックBでのImports使用
```yaml
Parameters:
  VPCStackName:
    Type: String
    Description: Name of the VPC stack

Resources:
  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      VpcId: !ImportValue 
        Fn::Sub: "${VPCStackName}-VPC-ID"
```

### クロススタック管理ユーティリティ

```bash
# スタック間依存関係の確認
python cf-templates/utilities/cross-stack-manager.py \
  --action validate \
  --config cross-stack-config.json

# 依存関係に基づく順次デプロイ
python cf-templates/utilities/cross-stack-manager.py \
  --action deploy \
  --config cross-stack-config.json
```

### 統合パターンの使用

#### Webアプリケーションパターン
```json
{
  "PatternType": "WebApplication",
  "VPCConfig": { "CidrBlock": "10.0.0.0/16" },
  "LoadBalancerConfig": { "Type": "ApplicationLoadBalancer" },
  "ComputeConfig": { "InstanceType": "t3.medium" },
  "DatabaseConfig": { "Engine": "mysql" }
}
```

#### マイクロサービスパターン
```json
{
  "PatternType": "Microservices",
  "ContainerConfig": { "Platform": "ECS" },
  "APIGatewayConfig": { "Type": "REST" },
  "MessageQueueConfig": { "EnableSQS": true }
}
```

## 監視とメンテナンス

### CloudWatch監視の設定

```json
{
  "MonitoringConfig": {
    "EnableCloudWatch": "true",
    "EnableDashboard": "true",
    "LogRetentionDays": 30,
    "EnableAlarms": "true",
    "AlarmNotificationEmail": "ops-team@company.com"
  }
}
```

### ログ管理

```bash
# CloudWatchログの確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/my-function"

# ログストリームの表示
aws logs describe-log-streams --log-group-name "/aws/lambda/my-function"

# ログイベントの取得
aws logs get-log-events \
  --log-group-name "/aws/lambda/my-function" \
  --log-stream-name "2024/01/15/[$LATEST]abc123"
```

### パフォーマンス監視

```bash
# CloudWatch メトリクスの取得
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600
```

### コスト監視

```bash
# コスト情報の取得
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

### セキュリティ監視

```bash
# CloudTrail ログの確認
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateStack \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

## ベストプラクティス

### 1. 設定管理
- 設定ファイルをバージョン管理システムで管理
- 環境別の設定ファイルを分離
- 機密情報はAWS Systems Manager Parameter Storeを使用

### 2. デプロイメント
- 本番環境デプロイ前に必ずテスト環境で検証
- 段階的デプロイメントを実施
- ロールバック計画を事前に準備

### 3. 監視
- 重要なメトリクスにアラームを設定
- ログ保持期間を適切に設定
- ダッシュボードで可視化

### 4. セキュリティ
- 最小権限の原則を適用
- 定期的なセキュリティレビューを実施
- 暗号化を適切に設定

### 5. コスト最適化
- 不要なリソースを定期的に削除
- 適切なインスタンスタイプを選択
- ライフサイクルポリシーを設定

---

このガイドを参考に、Well-Architected Framework準拠のインフラストラクチャを効率的にデプロイしてください。