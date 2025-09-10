# Well-Architected統合パターンテンプレート

このディレクトリには、Well-Architected Framework準拠の統合パターンテンプレートが含まれています。各パターンは、複数のAWSサービスを組み合わせて、一般的なアーキテクチャパターンを実装します。

## 利用可能なパターン

### 1. Webアプリケーションパターン (`web-application/`)

**概要**: 典型的な3層Webアプリケーション構成

**含まれるコンポーネント**:
- Application Load Balancer (ALB)
- Auto Scaling Group with EC2 instances
- RDS MySQL database
- S3 bucket for static assets
- CloudFront distribution
- CloudWatch monitoring

**適用シナリオ**:
- 企業Webサイト
- Eコマースサイト
- コンテンツ管理システム
- 社内アプリケーション

**依存関係**:
- `networking-vpc`: VPCとサブネット
- `foundation-iam`: IAMロールとポリシー
- `foundation-kms`: 暗号化キー
- `integration-cloudwatch`: 監視とアラート

### 2. マイクロサービスパターン (`microservices/`)

**概要**: サーバーレスマイクロサービス構成

**含まれるコンポーネント**:
- API Gateway
- Lambda functions (User Service, Order Service, Order Processing)
- DynamoDB tables
- SQS queues
- SNS topics
- X-Ray tracing

**適用シナリオ**:
- RESTful API
- イベント駆動アーキテクチャ
- サーバーレスアプリケーション
- マイクロサービス分散システム

**依存関係**:
- `networking-vpc`: VPCとサブネット（Lambda VPC設定用）
- `foundation-iam`: IAMロールとポリシー
- `foundation-kms`: 暗号化キー
- `integration-cloudwatch`: 監視とアラート

### 3. データ処理パターン (`data-processing/`)

**概要**: リアルタイムデータ処理とバッチ分析構成

**含まれるコンポーネント**:
- Kinesis Data Streams
- Lambda functions (Stream Processor, Data Processor)
- S3 buckets (Raw, Processed, Data Lake)
- AWS Glue (Database, Table)
- Kinesis Analytics (オプション)

**適用シナリオ**:
- リアルタイムデータ分析
- ログ処理パイプライン
- IoTデータ処理
- データレイク構築
- ETL処理

**依存関係**:
- `networking-vpc`: VPCとサブネット（Lambda VPC設定用）
- `foundation-iam`: IAMロールとポリシー
- `foundation-kms`: 暗号化キー
- `integration-cloudwatch`: 監視とアラート

## 使用方法

### 1. 前提条件の確認

各パターンを使用する前に、以下の基盤スタックがデプロイされている必要があります：

```bash
# 1. 基盤スタック
aws cloudformation deploy --template-file cf-templates/foundation/iam/iam-roles-policies.yaml --stack-name foundation-iam --capabilities CAPABILITY_NAMED_IAM
aws cloudformation deploy --template-file cf-templates/foundation/kms/kms-keys.yaml --stack-name foundation-kms

# 2. ネットワークスタック
aws cloudformation deploy --template-file cf-templates/networking/vpc/vpc-template.yaml --stack-name networking-vpc

# 3. 監視スタック
aws cloudformation deploy --template-file cf-templates/integration/cloudwatch/cloudwatch-template.yaml --stack-name integration-cloudwatch
```

### 2. パターンのデプロイ

#### Webアプリケーションパターン

```bash
aws cloudformation deploy \
  --template-file cf-templates/patterns/web-application/web-app-pattern.yaml \
  --stack-name web-app-pattern \
  --parameter-overrides file://cf-templates/patterns/web-application/web-app-config-basic.json \
  --capabilities CAPABILITY_IAM
```

#### マイクロサービスパターン

```bash
aws cloudformation deploy \
  --template-file cf-templates/patterns/microservices/microservices-pattern.yaml \
  --stack-name microservices-pattern \
  --parameter-overrides file://cf-templates/patterns/microservices/microservices-config-basic.json \
  --capabilities CAPABILITY_IAM
```

#### データ処理パターン

```bash
aws cloudformation deploy \
  --template-file cf-templates/patterns/data-processing/data-processing-pattern.yaml \
  --stack-name data-processing-pattern \
  --parameter-overrides file://cf-templates/patterns/data-processing/data-processing-config-basic.json \
  --capabilities CAPABILITY_IAM
```

### 3. 設定のカスタマイズ

各パターンには設定ファイルが用意されています：

- `*-config-basic.json`: 基本設定（開発環境向け）
- `*-config-advanced.json`: 高度設定（ステージング環境向け）
- `*-config-enterprise.json`: エンタープライズ設定（本番環境向け）

設定ファイルをコピーして、プロジェクトに合わせてカスタマイズしてください：

```bash
cp cf-templates/patterns/web-application/web-app-config-basic.json my-web-app-config.json
# my-web-app-config.jsonを編集
```

## パターン固有の設定オプション

### Webアプリケーションパターン

| パラメータ | 説明 | デフォルト値 | 選択肢 |
|-----------|------|-------------|--------|
| ApplicationPattern | アプリケーションパターン | Basic | Basic, Advanced, Enterprise |
| InstanceType | EC2インスタンスタイプ | t3.medium | t3.micro, t3.small, t3.medium, t3.large, m5.large, m5.xlarge |
| MinSize | Auto Scaling最小サイズ | 2 | 1-10 |
| MaxSize | Auto Scaling最大サイズ | 6 | 1-20 |
| DBInstanceClass | RDSインスタンスクラス | db.t3.micro | db.t3.micro, db.t3.small, db.t3.medium, db.r5.large, db.r5.xlarge |
| EnableMultiAZ | RDS Multi-AZ | false | true, false |

### マイクロサービスパターン

| パラメータ | 説明 | デフォルト値 | 選択肢 |
|-----------|------|-------------|--------|
| ServicePattern | サービスパターン | Basic | Basic, Advanced, Enterprise |
| LambdaRuntime | Lambda Runtime | python3.9 | python3.9, python3.10, python3.11, nodejs18.x, nodejs20.x |
| LambdaMemorySize | Lambda Memory Size (MB) | 256 | 128-3008 |
| DynamoDBBillingMode | DynamoDB課金モード | PAY_PER_REQUEST | PAY_PER_REQUEST, PROVISIONED |
| EnableXRayTracing | X-Rayトレーシング | true | true, false |

### データ処理パターン

| パラメータ | 説明 | デフォルト値 | 選択肢 |
|-----------|------|-------------|--------|
| ProcessingPattern | 処理パターン | Basic | Basic, Advanced, Enterprise |
| KinesisShardCount | Kinesisシャード数 | 2 | 1-100 |
| KinesisRetentionHours | データ保持時間 | 24 | 24-8760 |
| EnableDataLake | Data Lake機能 | true | true, false |
| EnableRealTimeAnalytics | リアルタイム分析 | true | true, false |

## Well-Architected準拠

すべてのパターンは、AWS Well-Architected Frameworkの6つの柱に準拠しています：

### 運用上の優秀性 (Operational Excellence)
- Infrastructure as Code
- 自動化されたデプロイメント
- 監視とログ記録
- 設定管理

### セキュリティ (Security)
- 最小権限の原則
- 保存時・転送時暗号化
- ネットワーク分離
- セキュリティグループ設定

### 信頼性 (Reliability)
- マルチAZ配置
- 自動復旧機能
- バックアップとリストア
- 障害分離

### パフォーマンス効率 (Performance Efficiency)
- 適切なリソースサイジング
- Auto Scaling
- キャッシュ戦略
- 監視とメトリクス

### コスト最適化 (Cost Optimization)
- リソースの適正サイジング
- 使用量ベースの課金
- ライフサイクル管理
- 予約インスタンス対応

### 持続可能性 (Sustainability)
- 効率的なリソース使用
- サーバーレス技術の活用
- 自動スケーリング
- 環境負荷の最小化

## トラブルシューティング

### 一般的な問題

1. **依存スタックが見つからない**
   ```
   Error: Export MyProject-dev-VPC-ID cannot be imported
   ```
   解決策: 依存する基盤スタックが正しくデプロイされているか確認

2. **IAM権限不足**
   ```
   Error: User is not authorized to perform: iam:CreateRole
   ```
   解決策: `--capabilities CAPABILITY_IAM`または`CAPABILITY_NAMED_IAM`を追加

3. **リソース名の重複**
   ```
   Error: Bucket already exists
   ```
   解決策: ProjectNameパラメータを変更してユニークな名前を使用

### デバッグ方法

1. **CloudFormationイベントの確認**
   ```bash
   aws cloudformation describe-stack-events --stack-name your-stack-name
   ```

2. **スタック出力の確認**
   ```bash
   aws cloudformation describe-stacks --stack-name your-stack-name --query 'Stacks[0].Outputs'
   ```

3. **リソースの確認**
   ```bash
   aws cloudformation list-stack-resources --stack-name your-stack-name
   ```

## カスタマイズとベストプラクティス

### 1. 環境別設定

環境ごとに異なる設定ファイルを作成：

```
configs/
├── dev-web-app.json
├── staging-web-app.json
└── prod-web-app.json
```

### 2. パラメータストア連携

機密情報はAWS Systems Manager Parameter Storeを使用：

```json
{
  "DBMasterUsername": "{{resolve:ssm:/myapp/db/username}}",
  "DBMasterPassword": "{{resolve:ssm-secure:/myapp/db/password}}"
}
```

### 3. タグ戦略

一貫したタグ戦略を実装：

```json
{
  "ProjectName": "MyProject",
  "Environment": "prod",
  "Owner": "team@company.com",
  "CostCenter": "engineering",
  "Backup": "required"
}
```

### 4. 監視とアラート

各パターンには基本的なCloudWatchアラームが含まれていますが、プロジェクトの要件に応じて追加のメトリクスとアラームを設定してください。

## サポートとコントリビューション

問題や改善提案がある場合は、以下の情報を含めて報告してください：

1. 使用しているパターン名
2. 設定ファイルの内容
3. エラーメッセージ
4. 期待される動作
5. 実際の動作

テンプレートの改善や新しいパターンの追加も歓迎します。