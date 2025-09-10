# トラブルシューティングガイド

## 目次
1. [一般的な問題と解決方法](#一般的な問題と解決方法)
2. [デプロイメント関連の問題](#デプロイメント関連の問題)
3. [設定関連の問題](#設定関連の問題)
4. [パフォーマンス関連の問題](#パフォーマンス関連の問題)
5. [セキュリティ関連の問題](#セキュリティ関連の問題)
6. [コスト関連の問題](#コスト関連の問題)
7. [診断ツールとコマンド](#診断ツールとコマンド)

## 一般的な問題と解決方法

### 問題1: CloudFormationスタックの作成が失敗する

#### 症状
```
CREATE_FAILED: The following resource(s) failed to create: [ResourceName]
```

#### 原因と解決方法

**原因1: IAM権限不足**
```bash
# 現在のIAM権限を確認
aws sts get-caller-identity
aws iam get-user --user-name your-username

# 必要な権限を確認
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/your-username \
  --action-names cloudformation:CreateStack \
  --resource-arns "*"
```

**解決方法**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "ec2:*",
        "iam:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**原因2: リソース制限の超過**
```bash
# サービス制限を確認
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A  # Running On-Demand EC2 instances
```

**解決方法**: サービス制限の引き上げを申請

**原因3: 依存関係の問題**
```yaml
# 正しい依存関係の設定
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    DependsOn: MySecurityGroup
    Properties:
      SecurityGroupIds:
        - !Ref MySecurityGroup
```

### 問題2: パラメータ検証エラー

#### 症状
```
Parameter validation failed: Invalid value for parameter
```

#### 解決方法
```bash
# パラメータファイルの検証
python cf-templates/utilities/validate-config.py \
  --config my-config.json \
  --template template.yaml

# JSONスキーマによる検証
python -c "
import json
import jsonschema
with open('config.json') as f:
    config = json.load(f)
with open('schema.json') as f:
    schema = json.load(f)
jsonschema.validate(config, schema)
"
```

### 問題3: クロススタック参照の失敗

#### 症状
```
Export [ExportName] cannot be deleted as it is in use by [StackName]
```

#### 解決方法
```bash
# エクスポートの使用状況を確認
aws cloudformation list-imports --export-name MyExport

# 依存関係の順序でスタックを削除
aws cloudformation delete-stack --stack-name dependent-stack
aws cloudformation wait stack-delete-complete --stack-name dependent-stack
aws cloudformation delete-stack --stack-name base-stack
```

## デプロイメント関連の問題

### 問題1: スタック更新時のロールバック

#### 症状
```
UPDATE_ROLLBACK_COMPLETE: Stack update failed and has been rolled back
```

#### 診断方法
```bash
# スタックイベントを確認
aws cloudformation describe-stack-events --stack-name my-stack

# 失敗したリソースの詳細を確認
aws cloudformation describe-stack-resources \
  --stack-name my-stack \
  --logical-resource-id FailedResourceId
```

#### 解決方法
```bash
# 変更セットを使用した安全な更新
aws cloudformation create-change-set \
  --stack-name my-stack \
  --change-set-name my-changeset \
  --template-body file://template.yaml \
  --parameters file://parameters.json

# 変更セットの内容を確認
aws cloudformation describe-change-set \
  --stack-name my-stack \
  --change-set-name my-changeset

# 変更セットを実行
aws cloudformation execute-change-set \
  --stack-name my-stack \
  --change-set-name my-changeset
```

### 問題2: リソースの削除保護

#### 症状
```
DELETE_FAILED: Resource cannot be deleted due to termination protection
```

#### 解決方法
```bash
# 削除保護を無効化
aws cloudformation update-termination-protection \
  --stack-name my-stack \
  --no-enable-termination-protection

# EC2インスタンスの削除保護を無効化
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --no-disable-api-termination
```

### 問題3: タイムアウトエラー

#### 症状
```
CREATE_FAILED: Resource creation cancelled
```

#### 解決方法
```yaml
# タイムアウト値を調整
Resources:
  MyAutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    CreationPolicy:
      ResourceSignal:
        Timeout: PT15M  # 15分に延長
        Count: 2
```

## 設定関連の問題

### 問題1: JSON設定ファイルの構文エラー

#### 症状
```
JSONDecodeError: Expecting ',' delimiter
```

#### 診断と解決
```bash
# JSON構文の検証
python -m json.tool config.json

# より詳細な検証
jq . config.json

# 設定ファイルの自動修正
python cf-templates/utilities/fix-json-config.py --input config.json
```

### 問題2: パラメータの型不一致

#### 症状
```
Parameter validation failed: Invalid type for parameter
```

#### 解決方法
```json
// 正しい型の指定
{
  "Parameters": {
    "InstanceCount": 2,           // 数値型
    "EnableLogging": "true",      // 文字列型（CloudFormationでは）
    "SubnetIds": ["subnet-123", "subnet-456"]  // 配列型
  }
}
```

### 問題3: 必須パラメータの不足

#### 症状
```
Parameters: [ParameterName] must have values
```

#### 解決方法
```bash
# テンプレートの必須パラメータを確認
aws cloudformation get-template-summary \
  --template-body file://template.yaml \
  --query 'Parameters[?DefaultValue==null].ParameterKey'

# 設定ファイルに必須パラメータを追加
python cf-templates/utilities/add-required-parameters.py \
  --template template.yaml \
  --config config.json
```

## パフォーマンス関連の問題

### 問題1: 高いCPU使用率

#### 診断
```bash
# CloudWatchメトリクスの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average,Maximum \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600
```

#### 解決方法
```json
// オートスケーリング設定の調整
{
  "Parameters": {
    "TargetCPUUtilization": 60,    // 70から60に下げる
    "ScaleUpCooldown": 180,        // クールダウン時間を短縮
    "MinSize": 3,                  // 最小インスタンス数を増加
    "MaxSize": 15                  // 最大インスタンス数を増加
  }
}
```

### 問題2: データベースの応答時間が遅い

#### 診断
```bash
# RDS Performance Insightsの確認
aws rds describe-db-instances --db-instance-identifier mydb

# CloudWatchメトリクスの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=mydb \
  --statistics Average,Maximum \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600
```

#### 解決方法
```json
// データベース設定の最適化
{
  "Parameters": {
    "DBInstanceClass": "db.r5.xlarge",  // より高性能なインスタンス
    "EnablePerformanceInsights": "true",
    "MonitoringInterval": 60,
    "AllocatedStorage": 1000,           // ストレージ容量を増加
    "Iops": 3000                        // IOPSを増加
  }
}
```

### 問題3: ネットワークレイテンシが高い

#### 診断
```bash
# VPC Flow Logsの確認
aws ec2 describe-flow-logs

# CloudWatchでネットワークメトリクスを確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkLatency \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600
```

#### 解決方法
```json
// ネットワーク最適化設定
{
  "Parameters": {
    "EnableEnhancedNetworking": "true",
    "EnableSRIOV": "true",
    "PlacementGroupStrategy": "cluster",  // 低レイテンシが必要な場合
    "InstanceType": "c5n.large"           // ネットワーク最適化インスタンス
  }
}
```

## セキュリティ関連の問題

### 問題1: セキュリティグループの設定ミス

#### 症状
```
Connection timeout / Connection refused
```

#### 診断
```bash
# セキュリティグループルールの確認
aws ec2 describe-security-groups --group-ids sg-12345678

# ネットワークACLの確認
aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=subnet-12345678"
```

#### 解決方法
```json
// 適切なセキュリティグループ設定
{
  "Parameters": {
    "AllowedCIDR": "10.0.0.0/16",      // 内部ネットワークのみ許可
    "HTTPSPort": 443,
    "HTTPPort": 80,
    "SSHAccess": "false"               // SSH無効化
  }
}
```

### 問題2: IAM権限の問題

#### 症状
```
AccessDenied: User is not authorized to perform action
```

#### 診断
```bash
# IAMポリシーシミュレーター
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/username \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::mybucket/*

# CloudTrailでアクセス履歴を確認
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

#### 解決方法
```json
// 最小権限の原則に基づくポリシー
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mybucket/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

### 問題3: SSL/TLS証明書の問題

#### 症状
```
SSL certificate verification failed
```

#### 診断
```bash
# ACM証明書の状態確認
aws acm list-certificates
aws acm describe-certificate --certificate-arn arn:aws:acm:region:account:certificate/cert-id

# SSL証明書の検証
openssl s_client -connect example.com:443 -servername example.com
```

#### 解決方法
```json
// 正しい証明書設定
{
  "Parameters": {
    "CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
    "SSLPolicy": "ELBSecurityPolicy-TLS-1-2-2017-01",
    "EnableHTTPSRedirect": "true"
  }
}
```

## コスト関連の問題

### 問題1: 予想以上の高額請求

#### 診断
```bash
# コスト分析
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# 最も高額なリソースの特定
aws ce get-rightsizing-recommendation \
  --service EC2-Instance
```

#### 解決方法
```json
// コスト最適化設定
{
  "Parameters": {
    "EnableSpotInstances": "true",
    "SpotInstancePercentage": 50,
    "InstanceType": "t3.medium",        // より小さなインスタンス
    "EnableScheduledScaling": "true",
    "ScheduledActions": [
      {
        "ScaleDown": "0 18 * * MON-FRI",  // 平日18時にスケールダウン
        "ScaleUp": "0 8 * * MON-FRI"      // 平日8時にスケールアップ
      }
    ]
  }
}
```

### 問題2: 不要なリソースの課金

#### 診断
```bash
# 使用されていないEBSボリュームの確認
aws ec2 describe-volumes --filters "Name=status,Values=available"

# 使用されていないElastic IPの確認
aws ec2 describe-addresses --filters "Name=association-id,Values="

# 使用されていないロードバランサーの確認
aws elbv2 describe-load-balancers --query 'LoadBalancers[?State.Code==`active`]'
```

#### 解決方法
```bash
# 不要なリソースの削除
aws ec2 delete-volume --volume-id vol-12345678
aws ec2 release-address --allocation-id eipalloc-12345678
aws elbv2 delete-load-balancer --load-balancer-arn arn:aws:elasticloadbalancing:...
```

## 診断ツールとコマンド

### CloudFormation診断

```bash
# スタックの状態確認
aws cloudformation describe-stacks --stack-name my-stack

# スタックイベントの確認
aws cloudformation describe-stack-events --stack-name my-stack

# スタックリソースの確認
aws cloudformation describe-stack-resources --stack-name my-stack

# ドリフト検出
aws cloudformation detect-stack-drift --stack-name my-stack
aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id drift-id
```

### ネットワーク診断

```bash
# VPC設定の確認
aws ec2 describe-vpcs
aws ec2 describe-subnets
aws ec2 describe-route-tables
aws ec2 describe-internet-gateways
aws ec2 describe-nat-gateways

# セキュリティグループの確認
aws ec2 describe-security-groups
aws ec2 describe-network-acls

# 接続テスト
aws ec2 describe-vpc-peering-connections
aws ec2 describe-vpn-connections
```

### パフォーマンス診断

```bash
# CloudWatchメトリクス
aws cloudwatch list-metrics --namespace AWS/EC2
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600

# X-Rayトレース
aws xray get-trace-summaries \
  --time-range-type TimeRangeByStartTime \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

### セキュリティ診断

```bash
# IAM分析
aws iam get-account-summary
aws iam generate-credential-report
aws iam get-credential-report

# CloudTrail分析
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z

# Config評価
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags
```

### コスト診断

```bash
# コスト分析
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# 予算確認
aws budgets describe-budgets --account-id 123456789012

# 使用量レポート
aws cur describe-report-definitions
```

## 緊急時対応手順

### 1. サービス停止時の対応

```bash
# 1. 現在の状況確認
aws cloudformation describe-stacks --stack-name production-stack
aws ec2 describe-instances --filters "Name=tag:Environment,Values=production"

# 2. ヘルスチェック
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# 3. 緊急スケールアップ
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name production-asg \
  --desired-capacity 10 \
  --honor-cooldown
```

### 2. セキュリティインシデント時の対応

```bash
# 1. 疑わしいアクティビティの確認
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=UserName,AttributeValue=suspicious-user \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z

# 2. アクセスキーの無効化
aws iam update-access-key \
  --access-key-id AKIAIOSFODNN7EXAMPLE \
  --status Inactive \
  --user-name suspicious-user

# 3. セキュリティグループの緊急変更
aws ec2 revoke-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0
```

### 3. データ損失時の対応

```bash
# 1. 最新バックアップの確認
aws rds describe-db-snapshots \
  --db-instance-identifier production-db \
  --snapshot-type automated \
  --max-records 5

# 2. バックアップからの復元
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier production-db-restored \
  --db-snapshot-identifier rds:production-db-2024-01-15-06-00

# 3. S3オブジェクトの復元
aws s3api restore-object \
  --bucket production-bucket \
  --key important-file.txt \
  --restore-request Days=7,GlacierJobParameters='{Tier=Expedited}'
```

---

このトラブルシューティングガイドを参考に、問題の迅速な特定と解決を行ってください。不明な点がある場合は、AWSサポートまたは社内のクラウドエンジニアリングチームにお問い合わせください。