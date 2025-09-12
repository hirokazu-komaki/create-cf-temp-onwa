# EC2 Auto Scaling テンプレート

## 概要

このディレクトリには、AWS Well-Architected Framework準拠のEC2 Auto Scalingテンプレートが含まれています。コスト最適化、セキュリティ、信頼性を重視した設計となっています。

## テンプレート構成

### 1. ec2-autoscaling.yaml
メインのEC2 Auto Scalingテンプレート

**主な機能:**
- 複数のインスタンスタイプパターン（Basic/Advanced/Enterprise）
- IAMロールとセキュリティグループの統合
- CloudWatch監視とログ記録
- スポットインスタンス対応
- マルチAZ配置

### 2. ec2-scaling-policies.yaml
Auto Scalingポリシーとアラーム

**主な機能:**
- Target Tracking Scaling Policy
- Step Scaling Policy
- CloudWatchアラーム
- スケジュールベースのスケーリング（非本番環境）
- SNS通知

### 3. ec2-config-example.json
設定例ファイル

## 設定パターン

### Basic（基本）
- **用途**: 開発環境
- **インスタンスタイプ**: t3.micro, t3.small
- **容量**: Min:1, Max:2, Desired:1
- **特徴**: スポットインスタンス使用、コスト重視

### Advanced（高度）
- **用途**: ステージング環境
- **インスタンスタイプ**: t3.medium, m5.large
- **容量**: Min:2, Max:4, Desired:2
- **特徴**: 詳細監視有効、バランス重視

### Enterprise（エンタープライズ）
- **用途**: 本番環境
- **インスタンスタイプ**: m5.large, m5.xlarge, c5.large
- **容量**: Min:3, Max:10, Desired:3
- **特徴**: 高可用性、パフォーマンス重視

## デプロイ方法

### 1. 基本デプロイ
```bash
aws cloudformation create-stack \
  --stack-name my-project-dev-ec2 \
  --template-body file://ec2-autoscaling.yaml \
  --parameters file://ec2-config-example.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### 2. スケーリングポリシー追加
```bash
aws cloudformation create-stack \
  --stack-name my-project-dev-ec2-scaling \
  --template-body file://ec2-scaling-policies.yaml \
  --parameters ParameterKey=AutoScalingGroupName,ParameterValue=my-project-dev-ASG
```

## パラメータ説明

### 必須パラメータ
- **ProjectName**: プロジェクト名（3-50文字、英字で始まり英数字で終わる）
- **ConfigurationPattern**: 設定パターン (Basic/Advanced/Enterprise)
- **Environment**: 環境名 (dev/staging/prod)
- **VpcId**: VPC ID
- **SubnetIds**: サブネットIDリスト

### コアインフラストラクチャパラメータ
- **InstanceAMI**: AMI ID（SSMパラメータ推奨）
- **KeyPairName**: EC2キーペア名（オプション）

### カスタムオーバーライドパラメータ
- **CustomInstanceType**: インスタンスタイプのオーバーライド
- **CustomMinSize**: Auto Scaling Group最小サイズのオーバーライド
- **CustomMaxSize**: Auto Scaling Group最大サイズのオーバーライド
- **CustomDesiredCapacity**: Auto Scaling Group希望サイズのオーバーライド

### 機能制御パラメータ
- **EnableAutoScaling**: Auto Scaling Groupの有効化
- **EnableDetailedMonitoring**: 詳細監視の有効化
- **EnableSpotInstances**: スポットインスタンスの使用
- **SpotMaxPrice**: スポットインスタンスの最大価格

### 高度な機能パラメータ（Advanced/Enterprise）
- **RootVolumeSize**: ルートボリュームサイズ
- **RootVolumeType**: ルートボリュームタイプ
- **EnableEncryption**: EBSボリューム暗号化
- **KMSKeyId**: 暗号化用KMSキーID
- **TargetGroupArns**: ターゲットグループARNリスト

### エンタープライズ機能パラメータ（Enterprise）
- **EnableMixedInstancesPolicy**: 混合インスタンスポリシー
- **InstanceTypes**: 混合インスタンスポリシー用インスタンスタイプリスト
- **EnableNitroEnclave**: Nitro Enclaveの有効化

## Well-Architected Framework準拠項目

### オペレーショナルエクセレンス
- **OPS04-BP01**: CloudWatchによる運用メトリクス収集
- **OPS04-BP02**: UserDataによる自動設定
- **OPS05-BP01**: 包括的な監視とアラート

### セキュリティ
- **SEC01-BP01**: IAMロールによる最小権限アクセス
- **SEC02-BP02**: セキュリティグループによる多層防御
- **SEC03-BP01**: VPC内でのネットワーク分離
- **SEC05-BP01**: CloudWatchログによるログ記録

### 信頼性
- **REL01-BP04**: 複数AZでの配置
- **REL02-BP01**: Auto Scalingによる自動復旧
- **REL03-BP01**: ELBヘルスチェック
- **REL08-BP01**: 需要に応じた自動スケーリング

### パフォーマンス効率
- **PERF02-BP01**: ワークロードに適したインスタンスタイプ
- **PERF03-BP01**: CloudWatch監視
- **PERF04-BP01**: Target Tracking Scaling

### コスト最適化
- **COST02-BP05**: スポットインスタンスの活用
- **COST05-BP01**: 適切なインスタンスサイジング
- **COST06-BP01**: スケジュールベースのスケーリング
- **COST07-BP01**: リソース使用量の監視

### 持続可能性
- **SUS02-BP01**: 効率的なリソース使用
- **SUS04-BP02**: 非本番環境の自動シャットダウン
- **SUS05-BP01**: 最適化されたワークロード配置

## 監視とアラート

### CloudWatchメトリクス
- CPU使用率
- メモリ使用率
- ディスク使用率
- ネットワークI/O

### アラーム
- 高CPU使用率アラーム（85%以上）
- 低CPU使用率アラーム（20%以下）
- 高メモリ使用率アラーム（設定可能）
- 高ディスク使用率アラーム（85%以上）

### 通知
- SNSトピックによるアラート通知
- スケーリングイベントの通知

## コスト最適化機能

### スポットインスタンス
- 開発環境でのコスト削減
- 最大価格設定による予算管理

### スケジュールスケーリング
- 非本番環境での自動シャットダウン
- 営業時間外のリソース削減

### 適切なサイジング
- パターンベースのインスタンス選択
- 使用量に応じた自動調整

## トラブルシューティング

### よくある問題

1. **インスタンスが起動しない**
   - AMI IDの確認
   - セキュリティグループの設定確認
   - サブネットの可用性確認

2. **スケーリングが動作しない**
   - CloudWatchメトリクスの確認
   - スケーリングポリシーの設定確認
   - クールダウン時間の確認

3. **ヘルスチェックが失敗する**
   - セキュリティグループの設定確認
   - アプリケーションの起動状況確認
   - ELBターゲットグループの設定確認

### ログ確認
```bash
# CloudWatchログの確認
aws logs describe-log-groups --log-group-name-prefix "/aws/ec2/my-project"

# インスタンスのシステムログ確認
aws ec2 get-console-output --instance-id i-1234567890abcdef0
```

## 関連テンプレート

- **VPC**: `cf-templates/networking/vpc/`
- **ELB**: `cf-templates/networking/elb/`
- **IAM**: `cf-templates/foundation/iam/`
- **CloudWatch**: `cf-templates/integration/cloudwatch/`

## パラメータ移行について

**重要**: Phase 3の完了により、レガシーパラメータのサポートが終了しました。

### 移行が必要なパラメータ

| 旧パラメータ | 新パラメータ | 備考 |
|---|---|---|
| `InstancePattern` | `ConfigurationPattern` | 必須パラメータ |
| `AMIId` | `InstanceAMI` | - |
| `InstanceType` | `CustomInstanceType` | オーバーライド用 |
| `MinSize` | `CustomMinSize` | オーバーライド用 |
| `MaxSize` | `CustomMaxSize` | オーバーライド用 |
| `DesiredCapacity` | `CustomDesiredCapacity` | オーバーライド用 |
| `TargetGroupArn` | `TargetGroupArns` | 配列形式 |
| `EnableEBSOptimization` | （削除） | パターンベースで自動設定 |

### 移行手順

1. **設定ファイルの更新**: 上記の対応表に従ってパラメータ名を変更
2. **必須パラメータの追加**: `ProjectName`と`ConfigurationPattern`を必須で設定
3. **検証の実行**: `aws cloudformation validate-template`で構文確認
4. **テストデプロイ**: 新しい設定でのドライラン実行

詳細な移行手順については、[MIGRATION-GUIDE.md](./MIGRATION-GUIDE.md) を参照してください。

## 更新履歴

- v3.0: Phase 3完了 - レガシーパラメータサポート終了
  - 統一されたパラメータ構造
  - 強化されたパラメータ検証
  - 包括的な移行ガイド
- v2.0: Phase 2完了 - 新パラメータ構造導入
  - 後方互換性を保持した新パラメータ
  - パターンベースのデフォルト値
  - Advanced/Enterprise機能の追加
- v1.0: Phase 1完了 - 後方互換性確保
  - 基本的なAuto Scaling機能
  - Well-Architected Framework準拠
  - コスト最適化機能