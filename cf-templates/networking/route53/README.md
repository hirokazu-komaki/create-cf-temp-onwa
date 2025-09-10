# Route53 CloudFormation テンプレート

## 概要

このテンプレートは、AWS Well-Architected Frameworkの原則に準拠したRoute53 DNS管理システムを作成します。パブリック/プライベートホストゾーン、ヘルスチェック、フェイルオーバー機能、クエリログ記録を含む包括的なDNS管理機能を提供します。

## Well-Architected 準拠項目

### オペレーショナルエクセレンス
- **OPS04-BP01**: ワークロードの監視 - Route53ヘルスチェックとCloudWatchアラーム
- **OPS04-BP02**: メトリクスとログの分析 - クエリログとヘルスチェックメトリクス
- **OPS06-BP01**: 自動化による運用手順の実装 - 自動フェイルオーバー

### セキュリティ
- **SEC05-BP01**: ネットワークレイヤーでの防御 - プライベートホストゾーンによる内部DNS分離
- **SEC05-BP02**: すべてのレイヤーでのトラフィック制御 - DNS レベルでのトラフィック制御

### 信頼性
- **REL08-BP01**: 障害の理解 - ヘルスチェックによる障害検知
- **REL08-BP02**: 障害管理戦略の設計 - 自動フェイルオーバー機能
- **REL11-BP01**: 障害の監視 - 継続的なヘルスチェック
- **REL11-BP02**: 自動復旧の実装 - DNS フェイルオーバーによる自動復旧

### パフォーマンス効率
- **PERF02-BP01**: 利用可能なネットワーク機能の評価 - Route53の地理的ルーティング対応
- **PERF04-BP01**: キャッシングの実装 - DNS TTL設定による効率的なキャッシング

### コスト最適化
- **COST02-BP05**: 動的スケーリングの実装 - 必要に応じたヘルスチェック設定
- **COST07-BP01**: データ転送の最適化 - 効率的なDNSクエリ処理

### 持続可能性
- **SUS02-BP01**: 使用率の高いインスタンスタイプの選択 - 効率的なDNS設計
- **SUS04-BP02**: 最適化されたデータアクセスパターンの実装 - 適切なTTL設定

## 機能

### 設定パターン

#### Basic パターン
- パブリックホストゾーンのみ
- 基本的なDNSレコード（A、CNAME）
- シンプルなDNS解決

#### Advanced パターン
- パブリック + プライベートホストゾーン
- ヘルスチェック機能
- 自動フェイルオーバー
- CloudWatchアラーム

#### Enterprise パターン
- 完全な冗長化設定
- クエリログ記録
- 包括的な監視とアラート
- SNS通知統合

### DNS機能

- **パブリックホストゾーン**: インターネット向けDNS解決
- **プライベートホストゾーン**: VPC内部でのDNS解決
- **ヘルスチェック**: エンドポイントの可用性監視
- **フェイルオーバー**: プライマリ/セカンダリ構成での自動切り替え
- **クエリログ**: DNS クエリの詳細ログ記録

## パラメータ

| パラメータ名 | 説明 | デフォルト値 | 必須 |
|-------------|------|-------------|------|
| ProjectName | プロジェクト名 | MyProject | Yes |
| Environment | 環境名 (dev/staging/prod) | dev | Yes |
| DomainName | 管理するドメイン名 | example.com | Yes |
| ConfigurationPattern | 設定パターン (Basic/Advanced/Enterprise) | Basic | Yes |
| CreatePrivateHostedZone | プライベートホストゾーンの作成 | false | No |
| VPCId | プライベートゾーン用VPC ID | - | Conditional |
| EnableHealthChecks | ヘルスチェックの有効化 | false | No |
| PrimaryEndpoint | プライマリエンドポイント | - | Conditional |
| SecondaryEndpoint | セカンダリエンドポイント | - | Conditional |
| HealthCheckPath | ヘルスチェック用パス | /health | No |
| EnableQueryLogging | クエリログの有効化 | false | No |

## 使用方法

### 1. 基本的なDNS設定

```bash
aws cloudformation create-stack \
  --stack-name my-dns-basic-stack \
  --template-body file://route53-template.yaml \
  --parameters file://route53-config-basic.json
```

### 2. 高度なDNS設定（フェイルオーバー付き）

```bash
aws cloudformation create-stack \
  --stack-name my-dns-advanced-stack \
  --template-body file://route53-template.yaml \
  --parameters file://route53-config-advanced.json
```

### 3. エンタープライズDNS設定

```bash
aws cloudformation create-stack \
  --stack-name my-dns-enterprise-stack \
  --template-body file://route53-template.yaml \
  --parameters file://route53-config-enterprise.json
```

## 出力値

このテンプレートは以下の値をエクスポートします：

- **PublicHostedZone-ID**: パブリックホストゾーンのID
- **PublicHostedZone-Name**: パブリックホストゾーンの名前
- **PublicHostedZone-NameServers**: ネームサーバーのリスト
- **PrivateHostedZone-ID**: プライベートホストゾーンのID
- **PrivateHostedZone-Name**: プライベートホストゾーンの名前
- **PrimaryHealthCheck-ID**: プライマリヘルスチェックのID
- **SecondaryHealthCheck-ID**: セカンダリヘルスチェックのID
- **HealthCheckTopic-ARN**: ヘルスチェック通知用SNSトピックのARN
- **Route53QueryLogGroup-Name**: クエリログ用CloudWatchロググループ名
- **DomainName**: 設定されたドメイン名
- **WWWDomainName**: WWWサブドメイン名

## 依存関係

### 必要なリソース
- **VPC**: プライベートホストゾーン作成時に必要
- **エンドポイント**: ヘルスチェック設定時に必要

### 統合可能なテンプレート
- VPCテンプレート（プライベートゾーン用）
- ELBテンプレート（ロードバランサーとの統合）
- CloudFrontテンプレート（CDNとの統合）

## ヘルスチェック設定

### サポートされるエンドポイントタイプ
- **IPアドレス**: 直接IPアドレスを指定
- **ドメイン名**: FQDNを指定

### ヘルスチェック設定
- **チェック間隔**: 30秒
- **失敗しきい値**: 3回連続失敗で異常判定
- **プロトコル**: HTTP（ポート80）
- **パス**: 設定可能（デフォルト: /health）

## フェイルオーバー設定

### 動作仕様
1. **正常時**: プライマリエンドポイントにトラフィックを送信
2. **プライマリ障害時**: セカンダリエンドポイントに自動切り替え
3. **プライマリ復旧時**: プライマリエンドポイントに自動復帰

### TTL設定
- **フェイルオーバー有効時**: 60秒（高速切り替え）
- **通常時**: 300秒（効率的なキャッシング）

## 監視とアラート

### CloudWatchメトリクス
- **HealthCheckStatus**: ヘルスチェックの状態
- **HealthCheckPercentHealthy**: ヘルスチェックの成功率

### アラーム設定
- **評価期間**: 2分間
- **しきい値**: ヘルスチェック失敗
- **通知**: SNSトピック経由

## クエリログ

### ログ内容
- クエリ時刻
- クエリ元IPアドレス
- クエリ対象ドメイン
- レコードタイプ
- 応答コード

### ログ保持期間
- **デフォルト**: 30日間
- **場所**: CloudWatch Logs

## コスト考慮事項

### 課金要素
- **ホストゾーン**: 月額固定料金
- **DNSクエリ**: クエリ数に応じた従量課金
- **ヘルスチェック**: ヘルスチェック数に応じた月額料金
- **クエリログ**: CloudWatch Logsの保存料金

### コスト最適化
- 不要なヘルスチェックの無効化
- 適切なTTL設定によるクエリ数削減
- ログ保持期間の最適化

## トラブルシューティング

### よくある問題

1. **ドメイン名の形式エラー**
   - 有効なドメイン名形式を使用しているか確認

2. **プライベートゾーンの作成失敗**
   - VPC IDが正しく指定されているか確認
   - VPCが存在するか確認

3. **ヘルスチェックの失敗**
   - エンドポイントが正しく応答しているか確認
   - ヘルスチェックパスが存在するか確認
   - セキュリティグループでポート80が開放されているか確認

4. **フェイルオーバーが動作しない**
   - 両方のヘルスチェックが正しく設定されているか確認
   - DNSキャッシュのTTLを考慮した待機時間

### ログの確認

#### ヘルスチェックログ
```
CloudWatch > メトリクス > Route53 > HealthCheckId
```

#### クエリログ
```
CloudWatch Logs > /aws/route53/{ProjectName}-{Environment}
```

## セキュリティ考慮事項

### プライベートホストゾーン
- VPC内部でのみ解決可能
- 外部からのアクセス不可

### ヘルスチェック
- パブリックIPからのアクセスが必要
- セキュリティグループでの適切な制限

### クエリログ
- 機密情報が含まれる可能性
- 適切なアクセス制御の実装

## 更新履歴

- v1.0: 初期リリース
  - Basic, Advanced, Enterprise パターンの実装
  - ヘルスチェックとフェイルオーバー対応
  - クエリログ機能
  - Well-Architected Framework準拠