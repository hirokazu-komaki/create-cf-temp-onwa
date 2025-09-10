# Well-Architected CloudFormation テンプレート集

## 概要

このプロジェクトは、AWS Well-Architected Frameworkの原則に準拠した再利用可能なCloudFormationテンプレートの包括的なセットを提供します。各テンプレートは、セキュリティ、信頼性、パフォーマンス効率、コスト最適化、運用の優秀性、持続可能性の6つの柱に基づいて設計されています。

## 🏗️ アーキテクチャ概要

```
cf-templates/
├── foundation/          # 基盤サービス (IAM, KMS, Organizations, Config)
├── networking/          # ネットワークサービス (VPC, ELB, Route53)
├── compute/            # コンピューティングサービス (EC2, Lambda)
├── integration/        # 統合サービス (API Gateway, CloudWatch)
├── patterns/           # 統合パターン (Web App, Microservices, Data Processing)
├── configurations/     # 設定例とスキーマ
└── utilities/          # ユーティリティスクリプト
```

## 🚀 クイックスタート

### 1. 基本的な使用方法

```bash
# 1. 設定ファイルを選択
cp cf-templates/networking/vpc/vpc-config-basic.json my-vpc-config.json

# 2. 設定をカスタマイズ
vim my-vpc-config.json

# 3. テンプレートをデプロイ
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://cf-templates/networking/vpc/vpc-template.yaml \
  --parameters file://my-vpc-config.json
```

### 2. パラメータ処理ユーティリティの使用

```bash
# JSON設定をCloudFormationパラメータに変換
python cf-templates/utilities/parameter-processor/parameter-processor.py \
  --config my-vpc-config.json \
  --output cf-parameters.json

# 設定の検証
python cf-templates/utilities/validate-config.py \
  --config my-vpc-config.json \
  --template cf-templates/networking/vpc/vpc-template.yaml
```

## 📋 利用可能なテンプレート

### 基盤サービス

| サービス | 説明 | パターン | Well-Architected準拠 |
|---------|------|---------|-------------------|
| **IAM** | Identity and Access Management | Basic, Advanced, Enterprise | Security, OperationalExcellence |
| **KMS** | Key Management Service | Basic, Advanced, Enterprise | Security, Reliability |
| **Organizations** | AWS Organizations | Basic, Advanced, Enterprise | OperationalExcellence, Security |
| **Config** | AWS Config | Basic, Advanced, Enterprise | OperationalExcellence, Security |

### ネットワークサービス

| サービス | 説明 | パターン | Well-Architected準拠 |
|---------|------|---------|-------------------|
| **VPC** | Virtual Private Cloud | Basic, Advanced, Enterprise | Security, Reliability |
| **ELB** | Elastic Load Balancer | Basic, Advanced, Enterprise | Reliability, PerformanceEfficiency |
| **Route53** | DNS Service | Basic, Advanced, Enterprise | Reliability, PerformanceEfficiency |

### コンピューティングサービス

| サービス | 説明 | パターン | Well-Architected準拠 |
|---------|------|---------|-------------------|
| **EC2** | Elastic Compute Cloud | Basic, Advanced, Enterprise | All Pillars |
| **Lambda** | Serverless Functions | Basic, Advanced, Enterprise | CostOptimization, PerformanceEfficiency |

### 統合サービス

| サービス | 説明 | パターン | Well-Architected準拠 |
|---------|------|---------|-------------------|
| **API Gateway** | API Management | Basic, Advanced, Enterprise | PerformanceEfficiency, Security |
| **CloudWatch** | Monitoring & Logging | Basic, Advanced, Enterprise | OperationalExcellence, Reliability |

### 統合パターン

| パターン | 説明 | 複雑度 | 適用場面 |
|---------|------|-------|--------|
| **Web Application** | 従来のWebアプリケーション | Basic → Enterprise | Webサイト、Webアプリ |
| **Microservices** | マイクロサービスアーキテクチャ | Basic → Enterprise | API、分散システム |
| **Data Processing** | データ処理パイプライン | Basic → Enterprise | ETL、分析、ML |

## 🎯 パターン選択ガイド

### Basic パターン
- **対象**: 開発・テスト環境、学習目的、プロトタイプ
- **特徴**: 最小限の設定、コスト最適化重視
- **Well-Architected**: 主にCostOptimization

### Advanced パターン
- **対象**: ステージング環境、中規模本番環境
- **特徴**: 高可用性、監視、セキュリティ強化
- **Well-Architected**: Reliability, PerformanceEfficiency, Security

### Enterprise パターン
- **対象**: 大規模本番環境、エンタープライズ環境
- **特徴**: 完全なセキュリティ、コンプライアンス、ガバナンス
- **Well-Architected**: All Pillars

## 🔧 設定ファイルの構造

### 基本構造
```json
{
  "Parameters": {
    "ProjectName": "MyProject",
    "Environment": "dev|staging|prod",
    "PatternType": "Basic|Advanced|Enterprise"
  },
  "Tags": {
    "Owner": "Team Name",
    "CostCenter": "Department",
    "WellArchitected": "Applicable Pillars"
  },
  "Description": "設定の説明"
}
```

### サービス固有設定
各サービスには固有の設定パラメータがあります：

```json
{
  "Parameters": {
    "VpcCidr": "10.0.0.0/16",
    "SubnetPattern": "Basic|Advanced|Enterprise",
    "EnableNatGateway": "true|false",
    "InstanceType": "t3.micro|t3.medium|m5.large"
  }
}
```

## 🔐 セキュリティベストプラクティス

### 1. 暗号化
- すべてのデータは保存時・転送時に暗号化
- KMSキーによる暗号化キー管理
- SSL/TLS証明書の適切な設定

### 2. アクセス制御
- 最小権限の原則
- IAMロールとポリシーの適切な設定
- MFA（多要素認証）の有効化

### 3. ネットワークセキュリティ
- VPCとセキュリティグループによる多層防御
- プライベートサブネットの使用
- NACLによる追加制御

### 4. 監視とログ記録
- CloudTrailによる API 呼び出しの記録
- VPC Flow Logsによるネットワーク監視
- CloudWatchによる包括的な監視

## 📊 Well-Architected Framework準拠

### 運用の優秀性 (Operational Excellence)
- **監視**: CloudWatch、X-Ray、Application Insights
- **自動化**: Infrastructure as Code、自動スケーリング
- **変更管理**: GitOps、段階的デプロイメント

### セキュリティ (Security)
- **暗号化**: KMS、SSL/TLS、EBS暗号化
- **アクセス制御**: IAM、MFA、最小権限
- **ネットワーク**: VPC、セキュリティグループ、WAF

### 信頼性 (Reliability)
- **高可用性**: マルチAZ、オートスケーリング
- **バックアップ**: 自動バックアップ、スナップショット
- **障害回復**: ヘルスチェック、自動復旧

### パフォーマンス効率 (Performance Efficiency)
- **スケーリング**: オートスケーリング、Elastic Load Balancing
- **キャッシング**: ElastiCache、CloudFront
- **最適化**: 適切なインスタンスタイプ選択

### コスト最適化 (Cost Optimization)
- **リソース効率**: 適切なサイジング、スポットインスタンス
- **ライフサイクル**: S3ライフサイクルポリシー
- **監視**: Cost Explorer、予算アラート

### 持続可能性 (Sustainability)
- **効率性**: 必要最小限のリソース使用
- **リージョン選択**: 再生可能エネルギー使用率の高いリージョン
- **自動化**: 非使用時の自動停止

## 🛠️ ユーティリティツール

### パラメータ処理
```bash
# JSON設定をCloudFormationパラメータに変換
python utilities/parameter-processor/parameter-processor.py
```

### 設定検証
```bash
# 設定ファイルの妥当性検証
python utilities/validate-config.py
```

### Well-Architected準拠チェック
```bash
# Well-Architected Framework準拠チェック
python utilities/validation/well-architected-validator.py
```

### クロススタック管理
```bash
# スタック間依存関係の管理
python utilities/cross-stack-manager.py
```

## 📚 詳細ドキュメント

- [使用方法ガイド](configurations/examples/usage-guide.md)
- [Well-Architected準拠ガイド](configurations/examples/well-architected-guide.md)
- [トラブルシューティング](configurations/examples/troubleshooting-guide.md)
- [FAQ](configurations/examples/faq.md)
- [設定例インデックス](configurations/examples/configuration-index.json)

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-org/well-architected-cf-templates/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/well-architected-cf-templates/discussions)
- **Email**: support@your-org.com

---

**注意**: このテンプレート集を使用する前に、必ず設定を確認し、本番環境での使用前に十分なテストを実施してください。