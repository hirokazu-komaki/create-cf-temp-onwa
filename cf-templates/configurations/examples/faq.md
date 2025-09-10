# よくある質問（FAQ）

## 目次
1. [一般的な質問](#一般的な質問)
2. [テンプレートの選択](#テンプレートの選択)
3. [設定とカスタマイズ](#設定とカスタマイズ)
4. [デプロイメント](#デプロイメント)
5. [セキュリティ](#セキュリティ)
6. [コストと課金](#コストと課金)
7. [パフォーマンス](#パフォーマンス)
8. [トラブルシューティング](#トラブルシューティング)

## 一般的な質問

### Q1: このテンプレート集は何を提供しますか？

**A:** AWS Well-Architected Frameworkの6つの柱（運用の優秀性、セキュリティ、信頼性、パフォーマンス効率、コスト最適化、持続可能性）に準拠したCloudFormationテンプレートの包括的なセットを提供します。各テンプレートは、基本（Basic）、高度（Advanced）、エンタープライズ（Enterprise）の3つのパターンで利用できます。

### Q2: どのようなAWSサービスがサポートされていますか？

**A:** 以下のサービスがサポートされています：

**基盤サービス:**
- IAM (Identity and Access Management)
- KMS (Key Management Service)
- AWS Organizations
- AWS Config

**ネットワークサービス:**
- VPC (Virtual Private Cloud)
- ELB (Elastic Load Balancer)
- Route53

**コンピューティングサービス:**
- EC2 (Elastic Compute Cloud)
- Lambda

**統合サービス:**
- API Gateway
- CloudWatch

**統合パターン:**
- Webアプリケーション
- マイクロサービス
- データ処理

### Q3: このテンプレート集を使用するのに必要な前提知識は？

**A:** 以下の知識があることを推奨します：
- AWS基本サービスの理解
- CloudFormationの基本概念
- JSON/YAML形式の理解
- AWS CLI の基本的な使用方法
- Well-Architected Frameworkの基本理解

### Q4: 商用利用は可能ですか？

**A:** はい、MITライセンスの下で商用利用が可能です。ただし、使用前に必ずライセンス条項を確認してください。

## テンプレートの選択

### Q5: Basic、Advanced、Enterpriseパターンの違いは何ですか？

**A:**

| パターン | 対象環境 | 特徴 | Well-Architected重点 |
|---------|---------|------|-------------------|
| **Basic** | 開発・テスト | 最小限の設定、コスト重視 | CostOptimization |
| **Advanced** | ステージング・中規模本番 | 高可用性、監視強化 | Reliability, PerformanceEfficiency |
| **Enterprise** | 大規模本番・エンタープライズ | 完全なセキュリティ、コンプライアンス | All Pillars |

### Q6: どのパターンを選択すべきですか？

**A:** 以下の基準で選択してください：

**Basic を選ぶべき場合:**
- 開発・テスト環境
- 学習・プロトタイプ目的
- コスト最優先
- シンプルな構成で十分

**Advanced を選ぶべき場合:**
- ステージング環境
- 中規模の本番環境
- 高可用性が必要
- 監視・ログ記録が重要

**Enterprise を選ぶべき場合:**
- 大規模本番環境
- コンプライアンス要件がある
- 最高レベルのセキュリティが必要
- 包括的なガバナンスが必要

### Q7: 複数のテンプレートを組み合わせて使用できますか？

**A:** はい、可能です。テンプレートはクロススタック参照をサポートしており、以下の順序で組み合わせることを推奨します：

1. **基盤** (IAM, KMS, Organizations, Config)
2. **ネットワーク** (VPC, Route53, ELB)
3. **コンピューティング** (EC2, Lambda)
4. **統合** (API Gateway, CloudWatch)

## 設定とカスタマイズ

### Q8: 設定ファイルをカスタマイズする方法は？

**A:** 以下の手順でカスタマイズできます：

```bash
# 1. サンプル設定をコピー
cp cf-templates/networking/vpc/vpc-config-basic.json my-vpc-config.json

# 2. 設定を編集
vim my-vpc-config.json

# 3. 設定を検証
python cf-templates/utilities/validate-config.py \
  --config my-vpc-config.json \
  --template cf-templates/networking/vpc/vpc-template.yaml
```

### Q9: 必須パラメータは何ですか？

**A:** すべてのテンプレートで以下のパラメータが必須です：

```json
{
  "Parameters": {
    "ProjectName": "MyProject",     // プロジェクト名
    "Environment": "dev"            // 環境 (dev/staging/prod)
  }
}
```

サービス固有の必須パラメータは各テンプレートのREADMEを参照してください。

### Q10: 設定ファイルのスキーマ検証はありますか？

**A:** はい、`cf-templates/configurations/schemas/`ディレクトリにJSONスキーマファイルがあります。以下のコマンドで検証できます：

```bash
python cf-templates/utilities/validate-config.py \
  --config your-config.json \
  --schema cf-templates/configurations/schemas/project-config-schema.json
```

## デプロイメント

### Q11: デプロイメントに必要なIAM権限は？

**A:** 最小限必要な権限：

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
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

本番環境では、より制限的な権限を設定することを推奨します。

### Q12: デプロイメント時間はどのくらいかかりますか？

**A:** テンプレートとパターンによって異なります：

| テンプレート | Basic | Advanced | Enterprise |
|-------------|-------|----------|------------|
| VPC | 2-3分 | 5-7分 | 10-15分 |
| EC2 | 3-5分 | 8-12分 | 15-25分 |
| Lambda | 1-2分 | 3-5分 | 5-8分 |
| 統合パターン | 10-15分 | 20-30分 | 45-60分 |

### Q13: 段階的デプロイメントは可能ですか？

**A:** はい、推奨されるデプロイメント順序：

```bash
# 1. 基盤インフラ
aws cloudformation create-stack --stack-name foundation-stack ...

# 2. ネットワーク
aws cloudformation create-stack --stack-name network-stack ...

# 3. コンピューティング
aws cloudformation create-stack --stack-name compute-stack ...

# 4. 統合サービス
aws cloudformation create-stack --stack-name integration-stack ...
```

### Q14: ロールバックはどのように行いますか？

**A:** CloudFormationの自動ロールバック機能を使用：

```bash
# スタック更新の失敗時は自動的にロールバック
aws cloudformation update-stack --stack-name my-stack ...

# 手動でのロールバック
aws cloudformation cancel-update-stack --stack-name my-stack

# 前のバージョンに戻す
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --parameters file://previous-parameters.json
```

## セキュリティ

### Q15: セキュリティのベストプラクティスは実装されていますか？

**A:** はい、以下のセキュリティベストプラクティスが実装されています：

- **暗号化**: 保存時・転送時の暗号化
- **アクセス制御**: IAMロールとポリシーによる最小権限
- **ネットワークセキュリティ**: VPC、セキュリティグループ、NACL
- **監査**: CloudTrail、Config、VPC Flow Logs
- **MFA**: 多要素認証の有効化（Enterpriseパターン）

### Q16: 機密情報はどのように管理すべきですか？

**A:** 以下の方法を推奨します：

```bash
# AWS Systems Manager Parameter Store
aws ssm put-parameter \
  --name "/myapp/database/password" \
  --value "SecurePassword123" \
  --type "SecureString"

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "myapp/database/credentials" \
  --secret-string '{"username":"admin","password":"SecurePassword123"}'
```

設定ファイルには機密情報を直接記載せず、Parameter StoreやSecrets Managerの参照を使用してください。

### Q17: ネットワークセキュリティはどのように設定されていますか？

**A:** 多層防御アプローチを採用：

1. **VPCレベル**: プライベートサブネット、NATゲートウェイ
2. **セキュリティグループ**: ステートフルファイアウォール
3. **NACL**: ステートレスファイアウォール
4. **WAF**: Webアプリケーションファイアウォール（Enterpriseパターン）
5. **VPC Flow Logs**: ネットワークトラフィックの監視

## コストと課金

### Q18: コストを最適化する方法は？

**A:** 以下の機能を活用してください：

**自動スケーリング:**
```json
{
  "Parameters": {
    "EnableAutoScaling": "true",
    "MinSize": 1,
    "MaxSize": 10,
    "TargetCPUUtilization": 70
  }
}
```

**スポットインスタンス:**
```json
{
  "Parameters": {
    "EnableSpotInstances": "true",
    "SpotInstancePercentage": 50
  }
}
```

**スケジュールドスケーリング:**
```json
{
  "Parameters": {
    "EnableScheduledScaling": "true",
    "ScheduledActions": [
      {
        "ScaleDown": "0 18 * * MON-FRI",
        "ScaleUp": "0 8 * * MON-FRI"
      }
    ]
  }
}
```

### Q19: 予想されるコストはどのくらいですか？

**A:** パターンと使用量によって大きく異なりますが、目安：

| パターン | 月額コスト（USD） | 主要コンポーネント |
|---------|-----------------|------------------|
| Basic | $50-200 | t3.micro x1-2, 基本監視 |
| Advanced | $200-800 | t3.medium x2-4, 詳細監視、RDS |
| Enterprise | $800-3000+ | m5.large x3+, 完全監視、冗長化 |

※実際のコストは使用量、リージョン、追加サービスによって変動します。

### Q20: コスト監視はどのように設定しますか？

**A:** CloudWatchとBudgetsを使用：

```bash
# 予算の設定
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json

# コストアラームの設定
aws cloudwatch put-metric-alarm \
  --alarm-name "HighCostAlarm" \
  --alarm-description "Alert when cost exceeds threshold" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold
```

## パフォーマンス

### Q21: パフォーマンスを最適化する方法は？

**A:** 以下の機能を活用：

**オートスケーリング:**
- CPU使用率に基づく自動スケーリング
- 予測スケーリング（Enterpriseパターン）

**キャッシング:**
- ElastiCache（Redis/Memcached）
- CloudFront CDN

**負荷分散:**
- Application Load Balancer
- Network Load Balancer

**監視:**
- CloudWatch詳細監視
- X-Rayトレーシング
- Application Insights

### Q22: データベースのパフォーマンスを向上させるには？

**A:** 以下の設定を調整：

```json
{
  "Parameters": {
    "DBInstanceClass": "db.r5.xlarge",      // メモリ最適化インスタンス
    "EnablePerformanceInsights": "true",     // Performance Insights有効化
    "MonitoringInterval": 60,                // 詳細監視
    "EnableReadReplica": "true",            // 読み取りレプリカ
    "MultiAZ": "true"                       // マルチAZ配置
  }
}
```

### Q23: ネットワークパフォーマンスを向上させるには？

**A:** 以下の設定を使用：

```json
{
  "Parameters": {
    "InstanceType": "c5n.large",            // ネットワーク最適化インスタンス
    "EnableEnhancedNetworking": "true",     // 拡張ネットワーキング
    "EnableSRIOV": "true",                  // SR-IOV有効化
    "PlacementGroupStrategy": "cluster"      // クラスター配置グループ
  }
}
```

## トラブルシューティング

### Q24: デプロイメントが失敗した場合の対処法は？

**A:** 以下の手順で診断：

```bash
# 1. スタックイベントを確認
aws cloudformation describe-stack-events --stack-name my-stack

# 2. 失敗したリソースの詳細を確認
aws cloudformation describe-stack-resources --stack-name my-stack

# 3. CloudTrailでAPI呼び出しを確認
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateStack

# 4. IAM権限を確認
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/username \
  --action-names cloudformation:CreateStack
```

### Q25: パフォーマンスの問題をどのように診断しますか？

**A:** CloudWatchメトリクスを確認：

```bash
# CPU使用率の確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600

# メモリ使用率の確認（CloudWatchエージェント必要）
aws cloudwatch get-metric-statistics \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600
```

### Q26: セキュリティの問題をどのように調査しますか？

**A:** 以下のツールを使用：

```bash
# CloudTrailでアクセス履歴を確認
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=UserName,AttributeValue=suspicious-user

# Configでコンプライアンス状況を確認
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags

# GuardDutyで脅威を確認
aws guardduty list-findings --detector-id detector-id

# Security Hubでセキュリティ状況を確認
aws securityhub get-findings
```

### Q27: サポートが必要な場合はどこに連絡すればよいですか？

**A:** 以下の方法でサポートを受けられます：

1. **GitHub Issues**: バグ報告や機能要求
2. **GitHub Discussions**: 一般的な質問や議論
3. **AWS Support**: AWS関連の技術的な問題
4. **社内チーム**: 組織内のクラウドエンジニアリングチーム

### Q28: 新しいサービスやパターンの追加予定はありますか？

**A:** はい、以下のサービス・パターンの追加を検討中です：

**サービス:**
- ECS/Fargate
- RDS
- DynamoDB
- S3
- CloudFront

**パターン:**
- コンテナベースアプリケーション
- サーバーレスアプリケーション
- 機械学習パイプライン
- IoTデータ処理

最新の更新情報はGitHubリポジトリをご確認ください。

---

その他の質問がある場合は、GitHubのIssuesまたはDiscussionsでお気軽にお問い合わせください。