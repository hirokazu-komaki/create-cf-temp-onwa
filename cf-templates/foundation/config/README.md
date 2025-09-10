# AWS Config Setup Template

## 概要

このテンプレートは、AWS Well-Architected Frameworkに準拠したAWS Config設定を作成します。リソース設定の継続的な監視、コンプライアンスルールの自動評価、設定変更の追跡とアラート機能を提供します。

## Well-Architected準拠項目

- **SEC04-BP01**: セキュリティイベントをキャプチャし分析する
- **SEC04-BP02**: セキュリティ調査機能を開発し実行する
- **SEC01-BP03**: アクセス権限を定期的に確認し削除する
- **OPS04-BP01**: 設定管理システムを実装する
- **OPS04-BP02**: 設定ドリフトを管理する
- **OPS06-BP01**: 運用メトリクスを使用してワークロードの健全性を判断する
- **REL09-BP01**: 障害を特定し分析する

## 設定パターン

### Basic
- **用途**: 開発環境、基本的なコンプライアンス
- **監視対象**: 主要リソース（EC2、S3、IAM等）
- **ルール数**: 3個（基本セキュリティ）
- **自動修復**: なし

### Advanced
- **用途**: 本番環境、詳細なコンプライアンス
- **監視対象**: 包括的なリソース監視
- **ルール数**: 6個（セキュリティ + パスワードポリシー）
- **自動修復**: オプション

### Enterprise
- **用途**: 大規模組織、厳格なガバナンス
- **監視対象**: 全サポートリソース
- **ルール数**: 9個（包括的なセキュリティ統制）
- **自動修復**: 有効

## パラメータ

| パラメータ名 | 型 | デフォルト | 説明 |
|-------------|-----|-----------|------|
| ConfigPattern | String | Basic | Config設定パターン |
| ProjectName | String | MyProject | プロジェクト名 |
| Environment | String | dev | 環境名 |
| EnableAllSupportedResourceTypes | String | true | 全リソースタイプ監視 |
| EnableGlobalResourceTypes | String | true | グローバルリソース監視 |
| DeliveryChannelName | String | default | 配信チャネル名 |
| ConfigSnapshotDeliveryProperties | String | TwentyFour_Hours | スナップショット配信頻度 |
| EnableConfigRules | String | true | Configルール有効化 |
| EnableRemediationActions | String | false | 自動修復有効化 |
| NotificationEmail | String | - | 通知メールアドレス |

## 作成されるリソース

### 基本コンポーネント
- **Configuration Recorder**: リソース設定の記録
- **Delivery Channel**: 設定データの配信
- **S3 Bucket**: 設定データの保存
- **IAM Role**: Config用サービスロール

### 監視とアラート
- **CloudWatch Logs**: 設定変更ログ
- **SNS Topic**: コンプライアンス通知
- **CloudWatch Alarms**: コンプライアンス状況アラート

### コンプライアンスルール

#### Basic Pattern
1. **root-access-key-check**: ルートユーザーアクセスキーチェック
2. **mfa-enabled-for-iam-console-access**: MFA有効化チェック
3. **s3-bucket-public-access-prohibited**: S3パブリックアクセス禁止

#### Advanced Pattern（Basic + 以下）
4. **ec2-security-group-attached-to-eni**: セキュリティグループアタッチメント
5. **rds-instance-public-access-check**: RDSパブリックアクセスチェック
6. **iam-password-policy**: IAMパスワードポリシー

#### Enterprise Pattern（Advanced + 以下）
7. **cloudtrail-enabled**: CloudTrail有効化チェック
8. **guardduty-enabled-centralized**: GuardDuty有効化チェック
9. **securityhub-enabled**: Security Hub有効化チェック

## 使用例

### 基本的な使用方法

```bash
aws cloudformation create-stack \
  --stack-name my-project-config \
  --template-body file://config-setup.yaml \
  --parameters file://sample-config.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### 自動修復有効化

```json
{
  "Parameters": {
    "ConfigPattern": "Enterprise",
    "EnableRemediationActions": "true",
    "NotificationEmail": "security@company.com"
  }
}
```

## 自動修復機能

Enterprise パターンでは以下の自動修復が利用可能：

### S3 Bucket Public Access Remediation
- **対象**: パブリックアクセス可能なS3バケット
- **アクション**: パブリックアクセスブロック設定の適用
- **実行**: 自動（最大3回試行）

## 監視とアラート

### CloudWatch メトリクス
- **ComplianceByConfigRule**: ルール別コンプライアンス状況
- **ComplianceByResourceType**: リソースタイプ別コンプライアンス
- **TotalDiscoveredResources**: 検出されたリソース総数

### 通知設定
- **SNS Topic**: コンプライアンス違反時の通知
- **Email Subscription**: 指定されたメールアドレスへの通知
- **CloudWatch Alarms**: メトリクス閾値に基づくアラート

## セキュリティ考慮事項

1. **データ暗号化**: S3バケットでAES256暗号化を使用
2. **アクセス制御**: 最小権限の原則に基づくIAMロール
3. **ネットワークセキュリティ**: HTTPS通信の強制
4. **データ保持**: 7年間のログ保持（コンプライアンス要件）

## 運用考慮事項

1. **コスト管理**: 
   - 監視対象リソースの選択的設定
   - ライフサイクルポリシーによるストレージコスト最適化
2. **パフォーマンス**: 
   - 配信頻度の調整
   - 必要なリソースタイプのみの監視
3. **スケーラビリティ**: 
   - 大規模環境での設定最適化
   - リージョン別の設定管理

## 出力値

- **ConfigRecorderName**: Configuration Recorder名
- **ConfigBucketName**: 設定データ保存バケット名
- **ConfigRoleArn**: Config用IAMロールARN
- **ConfigNotificationTopicArn**: 通知用SNSトピックARN

## トラブルシューティング

### よくある問題

1. **権限エラー**: IAMロールの権限不足
   ```bash
   aws iam get-role-policy --role-name ConfigRole --policy-name ConfigBucketAccess
   ```

2. **配信エラー**: S3バケットポリシーの設定確認
   ```bash
   aws s3api get-bucket-policy --bucket your-config-bucket
   ```

3. **ルール評価失敗**: リソースタイプの対応状況確認
   ```bash
   aws configservice describe-config-rules --config-rule-names rule-name
   ```

### 確認コマンド

```bash
# Config状況確認
aws configservice describe-configuration-recorders
aws configservice describe-delivery-channels

# コンプライアンス状況確認
aws configservice get-compliance-summary-by-config-rule

# 設定履歴確認
aws configservice get-resource-config-history --resource-type AWS::S3::Bucket --resource-id bucket-name
```

## 注意事項

⚠️ **重要**: Configの有効化により、監視対象リソースに応じてコストが発生します。

⚠️ **警告**: 自動修復機能は慎重に設定してください。予期しないリソース変更が発生する可能性があります。

⚠️ **推奨**: 本番環境では必ず通知設定を有効にし、コンプライアンス状況を継続的に監視してください。