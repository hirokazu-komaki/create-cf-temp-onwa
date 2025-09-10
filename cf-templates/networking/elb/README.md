# ELB CloudFormation テンプレート

## 概要

このテンプレートは、AWS Well-Architected Frameworkの原則に準拠したElastic Load Balancer（ELB）を作成します。Application Load Balancer（ALB）とNetwork Load Balancer（NLB）の両方をサポートし、SSL/TLS終端、WAF統合、ヘルスチェック、自動スケーリング連携を含む包括的な負荷分散機能を提供します。

## Well-Architected 準拠項目

### オペレーショナルエクセレンス
- **OPS04-BP01**: ワークロードの監視 - CloudWatchメトリクスとアラーム
- **OPS04-BP02**: メトリクスとログの分析 - アクセスログとパフォーマンスメトリクス
- **OPS06-BP01**: 自動化による運用手順の実装 - 自動ヘルスチェックとフェイルオーバー

### セキュリティ
- **SEC05-BP01**: ネットワークレイヤーでの防御 - セキュリティグループによる制御
- **SEC05-BP02**: すべてのレイヤーでのトラフィック制御 - WAF統合
- **SEC09-BP01**: 転送時の暗号化 - SSL/TLS終端
- **SEC09-BP02**: 認証された暗号化の実装 - 最新のTLSポリシー

### 信頼性
- **REL08-BP01**: 障害の理解 - ヘルスチェックによる障害検知
- **REL08-BP02**: 障害管理戦略の設計 - 複数AZでの負荷分散
- **REL10-BP01**: 複数の場所へのワークロードのデプロイ - マルチAZ配置
- **REL11-BP01**: 障害の監視 - 継続的なヘルスチェック

### パフォーマンス効率
- **PERF02-BP01**: 利用可能なネットワーク機能の評価 - 最適な負荷分散アルゴリズム
- **PERF03-BP01**: データ転送方法の最適化 - 効率的なトラフィック分散
- **PERF04-BP01**: キャッシングの実装 - 接続の永続化とキープアライブ

### コスト最適化
- **COST02-BP05**: 動的スケーリングの実装 - 需要に応じた自動スケーリング連携
- **COST05-BP01**: コスト効率の高いリソースの選択 - 適切なロードバランサータイプの選択
- **COST07-BP01**: データ転送の最適化 - 効率的なトラフィック処理

### 持続可能性
- **SUS02-BP01**: 使用率の高いインスタンスタイプの選択 - 効率的な負荷分散
- **SUS04-BP02**: 最適化されたデータアクセスパターンの実装 - 適切なルーティング設定

## 機能

### ロードバランサータイプ

#### Application Load Balancer (ALB)
- **レイヤー7負荷分散**: HTTP/HTTPSトラフィックの高度なルーティング
- **SSL/TLS終端**: 証明書管理とSSL処理
- **パスベースルーティング**: URLパスに基づくトラフィック分散
- **WAF統合**: Webアプリケーションファイアウォール
- **WebSocketサポート**: リアルタイム通信対応

#### Network Load Balancer (NLB)
- **レイヤー4負荷分散**: TCP/UDPトラフィックの高性能処理
- **静的IPアドレス**: Elastic IPアドレスの割り当て
- **超低レイテンシ**: 高性能なトラフィック処理
- **クロスゾーン負荷分散**: AZ間での均等な負荷分散
- **クライアントIP保持**: 元のクライアントIPアドレスの保持

### 設定パターン

#### Basic パターン
- 基本的な負荷分散機能
- シンプルなヘルスチェック
- 単一ターゲットグループ

#### Advanced パターン
- SSL/TLS終端
- 複数ターゲットグループ
- パスベースルーティング（ALB）
- WAF統合（ALB）
- CloudWatchアラーム

#### Enterprise パターン
- 完全なセキュリティ設定
- 包括的な監視とログ記録
- CloudWatchダッシュボード
- SNS通知統合

#### NetworkBasic パターン
- 基本的なNLB設定
- TCP/UDP負荷分散
- シンプルなヘルスチェック

#### NetworkAdvanced パターン
- クロスゾーン負荷分散
- クライアントIP保持
- 高度な監視設定

## パラメータ

| パラメータ名 | 説明 | デフォルト値 | 必須 |
|-------------|------|-------------|------|
| ProjectName | プロジェクト名 | MyProject | Yes |
| Environment | 環境名 (dev/staging/prod) | dev | Yes |
| LoadBalancerType | ロードバランサータイプ (application/network) | application | Yes |
| ConfigurationPattern | 設定パターン | Basic | Yes |
| VPCId | VPC ID | - | Yes |
| SubnetIds | サブネットIDリスト | - | Yes |
| Scheme | スキーム (internet-facing/internal) | internet-facing | No |
| EnableAccessLogs | アクセスログの有効化 | false | No |
| AccessLogsBucket | アクセスログ用S3バケット名 | - | Conditional |
| SSLCertificateArn | SSL証明書のARN | - | Conditional |
| EnableWAF | AWS WAFの有効化 | false | No |
| HealthCheckPath | ヘルスチェック用パス | /health | No |
| HealthCheckPort | ヘルスチェック用ポート | 80 | No |
| TargetPort | ターゲットポート | 80 | No |
| EnableCrossZoneLoadBalancing | クロスゾーン負荷分散 | false | No |

## 使用方法

### 1. 基本的なALBデプロイメント

```bash
aws cloudformation create-stack \
  --stack-name my-alb-basic-stack \
  --template-body file://elb-template.yaml \
  --parameters file://elb-config-basic.json \
  --capabilities CAPABILITY_IAM
```

### 2. 高度なALB設定（SSL + WAF）

```bash
aws cloudformation create-stack \
  --stack-name my-alb-advanced-stack \
  --template-body file://elb-template.yaml \
  --parameters file://elb-config-advanced.json \
  --capabilities CAPABILITY_IAM
```

### 3. エンタープライズALB設定

```bash
aws cloudformation create-stack \
  --stack-name my-alb-enterprise-stack \
  --template-body file://elb-template.yaml \
  --parameters file://elb-config-enterprise.json \
  --capabilities CAPABILITY_IAM
```

### 4. Network Load Balancer

```bash
aws cloudformation create-stack \
  --stack-name my-nlb-stack \
  --template-body file://elb-template.yaml \
  --parameters file://elb-config-network-advanced.json \
  --capabilities CAPABILITY_IAM
```

## 出力値

このテンプレートは以下の値をエクスポートします：

- **LoadBalancer-ID**: ロードバランサーのID
- **LoadBalancer-ARN**: ロードバランサーのARN
- **LoadBalancer-DNSName**: ロードバランサーのDNS名
- **LoadBalancer-HostedZoneID**: ロードバランサーのホストゾーンID
- **TargetGroup-ARN**: ターゲットグループのARN
- **SecondaryTargetGroup-ARN**: セカンダリターゲットグループのARN
- **ALB-SecurityGroup-ID**: ALBセキュリティグループのID
- **HTTPListener-ARN**: HTTPリスナーのARN
- **HTTPSListener-ARN**: HTTPSリスナーのARN
- **WebACL-ARN**: WAF WebACLのARN
- **LBAlarmTopic-ARN**: アラーム通知用SNSトピックのARN
- **LoadBalancer-Type**: ロードバランサーのタイプ
- **LoadBalancer-Scheme**: ロードバランサーのスキーム

## 依存関係

### 必要なリソース
- **VPC**: ロードバランサーを配置するVPC
- **サブネット**: 最低2つの異なるAZのサブネット
- **SSL証明書**: HTTPS使用時にACMで管理された証明書
- **S3バケット**: アクセスログ有効時に必要

### 統合可能なテンプレート
- VPCテンプレート（ネットワーク基盤）
- EC2テンプレート（ターゲットインスタンス）
- Auto Scalingテンプレート（自動スケーリング）
- Route53テンプレート（DNS統合）

## セキュリティ機能

### Application Load Balancer
- **セキュリティグループ**: 適切なポート制限
- **SSL/TLS終端**: 最新のセキュリティポリシー
- **WAF統合**: Webアプリケーション保護
- **アクセスログ**: 詳細なアクセス記録

### Network Load Balancer
- **セキュリティグループ**: ターゲットレベルでの制御
- **クライアントIP保持**: 元のIPアドレスの維持
- **TLS終端**: TCP TLSトラフィックの処理

## WAF設定

### 管理ルールセット
- **AWSManagedRulesCommonRuleSet**: 一般的な攻撃パターン
- **AWSManagedRulesKnownBadInputsRuleSet**: 既知の悪意のある入力

### カスタムルール
- **レート制限**: IP単位での接続数制限（2000リクエスト/5分）
- **地理的制限**: 特定地域からのアクセス制御（オプション）

## ヘルスチェック設定

### Application Load Balancer
- **プロトコル**: HTTP/HTTPS
- **パス**: 設定可能（デフォルト: /health）
- **間隔**: 30秒
- **タイムアウト**: 5秒
- **正常しきい値**: 2回連続成功
- **異常しきい値**: 2回連続失敗

### Network Load Balancer
- **プロトコル**: TCP
- **間隔**: 30秒
- **正常しきい値**: 3回連続成功
- **異常しきい値**: 3回連続失敗

## 監視とアラート

### CloudWatchメトリクス
- **RequestCount**: リクエスト数
- **TargetResponseTime**: ターゲット応答時間
- **HealthyHostCount**: 正常なホスト数
- **UnHealthyHostCount**: 異常なホスト数
- **HTTPCode_Target_2XX_Count**: 2XXレスポンス数
- **HTTPCode_Target_4XX_Count**: 4XXレスポンス数
- **HTTPCode_Target_5XX_Count**: 5XXレスポンス数

### アラーム設定
- **応答時間アラーム**: 1秒を超える場合
- **異常ホストアラーム**: 異常ホストが存在する場合
- **5XXエラーアラーム**: 5分間で10回を超える場合

### ダッシュボード（Enterprise）
- リアルタイムメトリクス表示
- ヘルス状況の可視化
- パフォーマンス傾向の分析

## アクセスログ

### ログ形式
- **ALB**: 詳細なHTTP/HTTPSアクセスログ
- **NLB**: TCP/UDPフローログ

### ログ内容
- タイムスタンプ
- クライアントIP
- ターゲットIP
- リクエスト/レスポンス時間
- HTTPステータスコード
- 送受信バイト数

### ログ保存
- **S3バケット**: 指定されたバケットに保存
- **プレフィックス**: プロジェクト名と環境で整理

## パフォーマンス最適化

### Application Load Balancer
- **HTTP/2サポート**: 有効化
- **接続アイドルタイムアウト**: 60秒
- **スティッキーセッション**: 設定可能
- **圧縮**: 自動圧縮対応

### Network Load Balancer
- **クロスゾーン負荷分散**: 均等な負荷分散
- **接続ドレイニング**: 300秒
- **クライアントIP保持**: 有効化

## コスト考慮事項

### 課金要素
- **ロードバランサー時間**: 時間単位の固定料金
- **LCU（Load Balancer Capacity Units）**: 使用量に応じた従量課金
- **データ処理**: 処理されたデータ量
- **WAF**: リクエスト数に応じた課金

### コスト最適化
- **適切なタイプ選択**: ALB vs NLBの使い分け
- **不要な機能の無効化**: WAF、アクセスログの選択的使用
- **ターゲット最適化**: 効率的なターゲット配置

## トラブルシューティング

### よくある問題

1. **ヘルスチェック失敗**
   - ターゲットのヘルスチェックパスが正しく応答しているか確認
   - セキュリティグループでヘルスチェックポートが開放されているか確認
   - ターゲットのファイアウォール設定を確認

2. **SSL証明書エラー**
   - 証明書のARNが正しいか確認
   - 証明書のドメイン名がロードバランサーのDNS名と一致するか確認
   - 証明書の有効期限を確認

3. **WAFブロック**
   - WAFルールが適切に設定されているか確認
   - 正当なトラフィックがブロックされていないか確認
   - WAFログでブロック理由を確認

4. **ターゲット登録失敗**
   - ターゲットグループの設定が正しいか確認
   - ターゲットインスタンスが正常に動作しているか確認
   - ネットワーク接続を確認

### ログの確認

#### CloudWatchメトリクス
```
CloudWatch > メトリクス > AWS/ApplicationELB または AWS/NetworkELB
```

#### アクセスログ
```
S3 > {AccessLogsBucket} > {ProjectName}-{Environment}-{LoadBalancerType}-lb/
```

#### WAFログ
```
CloudWatch Logs > aws-waf-logs-{WebACLName}
```

## セキュリティベストプラクティス

### ネットワークセキュリティ
- 最小権限の原則に基づくセキュリティグループ設定
- 不要なポートの閉鎖
- 内部ロードバランサーの適切な使用

### SSL/TLS設定
- 最新のTLSバージョンの使用
- 強力な暗号化スイートの選択
- 証明書の定期的な更新

### WAF設定
- 適切な管理ルールセットの選択
- カスタムルールによる追加保護
- 定期的なルール見直し

## 更新履歴

- v1.0: 初期リリース
  - ALB/NLB両対応
  - SSL/TLS終端機能
  - WAF統合
  - 包括的な監視機能
  - Well-Architected Framework準拠