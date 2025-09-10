# CloudWatch テンプレート

## 概要

このテンプレートは、AWS Well-Architected Framework に準拠した包括的な CloudWatch 監視システムを提供します。カスタムメトリクス、アラーム、ダッシュボード、ログ集約機能を含み、システムの可観測性を向上させます。

## 機能

### 監視機能
- **カスタムメトリクス**: アプリケーション固有のメトリクス収集
- **アラーム管理**: しきい値ベースおよび異常検知アラーム
- **複合アラーム**: 複数のメトリクスを組み合わせた高度なアラーム
- **ダッシュボード**: リアルタイム監視ダッシュボード

### ログ管理
- **ログ集約**: 複数のソースからのログ統合
- **メトリクスフィルター**: ログからのメトリクス抽出
- **Log Insights**: 高度なログ分析クエリ
- **ログ保持**: 設定可能な保持期間

### 通知機能
- **SNS 統合**: メール通知
- **Slack 統合**: Slack チャンネルへの通知
- **Lambda 通知**: カスタム通知ロジック

### 異常検知
- **機械学習ベース**: CloudWatch 異常検知
- **自動しきい値調整**: 動的なアラームしきい値
- **トレンド分析**: 長期的なパターン分析

## 設定パターン

### Basic
- 基本的なメトリクスとアラーム
- 標準的なログ保持
- シンプルな通知設定

### Advanced
- カスタムメトリクスフィルター
- 複合アラーム
- インタラクティブダッシュボード
- Log Insights クエリ

### Enterprise
- 高度なダッシュボード
- 異常検知
- クロスアカウント監視
- Container Insights

## パラメータ

| パラメータ名 | 説明 | デフォルト値 | 必須 |
|-------------|------|-------------|------|
| ProjectName | プロジェクト名 | my-project | Yes |
| Environment | 環境名 (dev/staging/prod) | dev | Yes |
| ConfigurationPattern | 設定パターン | Basic | Yes |
| LogRetentionDays | ログ保持期間（日） | 14 | No |
| EnableDetailedMonitoring | 詳細監視の有効化 | false | No |
| EnableContainerInsights | Container Insights | false | No |
| EnableAnomalyDetection | 異常検知の有効化 | false | No |
| NotificationEmail | 通知メールアドレス | "" | No |
| SlackWebhookUrl | Slack Webhook URL | "" | No |
| DashboardTimeRange | ダッシュボード時間範囲 | -PT3H | No |

## 使用例

### 基本的な監視設定

```json
{
  "Parameters": {
    "ProjectName": "my-app",
    "Environment": "dev",
    "ConfigurationPattern": "Basic",
    "NotificationEmail": "dev-team@company.com"
  }
}
```

### 高度な監視設定

```json
{
  "Parameters": {
    "ProjectName": "production-app",
    "Environment": "prod",
    "ConfigurationPattern": "Advanced",
    "LogRetentionDays": 30,
    "EnableDetailedMonitoring": "true",
    "EnableAnomalyDetection": "true",
    "NotificationEmail": "ops-team@company.com",
    "SlackWebhookUrl": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "DashboardTimeRange": "-PT6H"
  }
}
```

### エンタープライズ監視設定

```json
{
  "Parameters": {
    "ProjectName": "enterprise-system",
    "Environment": "prod",
    "ConfigurationPattern": "Enterprise",
    "LogRetentionDays": 90,
    "EnableDetailedMonitoring": "true",
    "EnableContainerInsights": "true",
    "EnableAnomalyDetection": "true",
    "NotificationEmail": "sre-team@company.com",
    "SlackWebhookUrl": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "DashboardTimeRange": "-PT12H"
  }
}
```

## デプロイ方法

```bash
# テンプレートの検証
aws cloudformation validate-template \
  --template-body file://cloudwatch-template.yaml

# スタックのデプロイ
aws cloudformation deploy \
  --template-file cloudwatch-template.yaml \
  --stack-name my-cloudwatch-monitoring \
  --parameter-overrides file://cloudwatch-config-example.json \
  --capabilities CAPABILITY_NAMED_IAM
```

## カスタムメトリクスの送信

### AWS CLI を使用

```bash
# カスタムメトリクスの送信
aws cloudwatch put-metric-data \
  --namespace "my-project/dev" \
  --metric-data MetricName=CustomMetric,Value=123.45,Unit=Count
```

### Python SDK を使用

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='my-project/dev',
    MetricData=[
        {
            'MetricName': 'CustomMetric',
            'Value': 123.45,
            'Unit': 'Count',
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': 'dev'
                }
            ]
        }
    ]
)
```

## Log Insights クエリ例

### エラー分析

```sql
fields @timestamp, level, message, request_id
| filter level = "ERROR"
| stats count() by bin(1h)
| sort @timestamp desc
```

### パフォーマンス分析

```sql
fields @timestamp, response_time, endpoint
| filter ispresent(response_time)
| stats avg(response_time), max(response_time), min(response_time) by endpoint
| sort avg(response_time) desc
```

### ユーザーアクティビティ分析

```sql
fields @timestamp, user_id, action
| filter ispresent(user_id)
| stats count() by user_id, action
| sort count desc
```

## アラーム設定

### CPU 使用率アラーム

```yaml
HighCPUAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: high-cpu-utilization
    MetricName: CPUUtilization
    Namespace: AWS/EC2
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 80
    ComparisonOperator: GreaterThanThreshold
```

### エラー率アラーム

```yaml
HighErrorRateAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: high-error-rate
    MetricName: ErrorCount
    Namespace: my-project/dev
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
```

## ダッシュボード設定

### 基本ダッシュボード

- システムメトリクス（CPU、メモリ、ディスク）
- アプリケーションメトリクス（エラー、警告）
- 最近のログエントリ

### エンタープライズダッシュボード

- 詳細なシステムメトリクス
- ビジネスメトリクス
- SLA 監視
- トレンド分析
- 異常検知結果

## 出力値

| 出力名 | 説明 |
|--------|------|
| AlertTopicArn | アラート用 SNS トピック ARN |
| ApplicationLogGroupName | アプリケーションログ グループ名 |
| SystemLogGroupName | システムログ グループ名 |
| MonitoringDashboardUrl | 監視ダッシュボード URL |
| EnterpriseDashboardUrl | エンタープライズダッシュボード URL |
| SlackNotificationFunctionArn | Slack 通知 Lambda 関数 ARN |

## Well-Architected Framework 準拠

### オペレーショナルエクセレンス
- **OPS04-BP01**: 運用手順の文書化
- **OPS04-BP02**: 運用手順の定期的な見直し
- **OPS07-BP01**: 運用メトリクスの理解
- **OPS08-BP01**: 運用イベントの対応

### セキュリティ
- **SEC04-BP01**: セキュリティイベントの検出
- **SEC04-BP02**: セキュリティイベントの分析
- **SEC10-BP01**: 攻撃の検出と対応

### 信頼性
- **REL06-BP01**: 障害の監視
- **REL06-BP02**: 障害の通知
- **REL11-BP01**: 復旧手順の監視
- **REL11-BP02**: 復旧時間の測定

### パフォーマンス効率
- **PERF04-BP02**: パフォーマンスの監視
- **PERF04-BP03**: パフォーマンスの分析

### コスト最適化
- **COST02-BP05**: 使用量の監視
- **COST03-BP01**: コストの可視化
- **COST03-BP02**: コストの分析

### 持続可能性
- **SUS02-BP01**: 使用パターンの最適化
- **SUS06-BP01**: 効率的なコードの実装

## トラブルシューティング

### よくある問題

1. **メトリクスが表示されない**
   - メトリクスの名前空間を確認
   - IAM 権限を確認
   - リージョン設定を確認

2. **アラームが発火しない**
   - しきい値設定を確認
   - 評価期間を確認
   - メトリクスデータの存在を確認

3. **Slack 通知が届かない**
   - Webhook URL を確認
   - Lambda 関数のログを確認
   - SNS サブスクリプションを確認

### ログの確認

```bash
# CloudWatch ログの確認
aws logs describe-log-groups --log-group-name-prefix "/aws/application"

# 特定のログストリームの確認
aws logs get-log-events \
  --log-group-name "/aws/application/my-project-dev" \
  --log-stream-name "log-stream-name"

# Lambda 関数のログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda"
```

### メトリクスの確認

```bash
# メトリクスの一覧取得
aws cloudwatch list-metrics --namespace "my-project/dev"

# メトリクスデータの取得
aws cloudwatch get-metric-statistics \
  --namespace "my-project/dev" \
  --metric-name "ErrorCount" \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## 関連リソース

- [AWS CloudWatch ドキュメント](https://docs.aws.amazon.com/cloudwatch/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [CloudWatch 異常検知](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Anomaly_Detection.html)
- [Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)