# VPC CloudFormation テンプレート

## 概要

このテンプレートは、AWS Well-Architected Frameworkの原則に準拠したVPC（Virtual Private Cloud）を作成します。マルチAZ配置、プライベート/パブリックサブネット、NAT Gateway、Internet Gatewayの設定を含む包括的なネットワーク基盤を提供します。

## Well-Architected 準拠項目

### オペレーショナルエクセレンス
- **OPS04-BP01**: ワークロードの監視 - VPC Flow Logsによるネットワークトラフィック監視
- **OPS04-BP02**: メトリクスとログの分析 - CloudWatch Logsへのフローログ出力

### セキュリティ
- **SEC05-BP01**: ネットワークレイヤーでの防御 - プライベート/パブリックサブネットの分離
- **SEC05-BP02**: すべてのレイヤーでのトラフィック制御 - ルートテーブルによるトラフィック制御
- **SEC05-BP03**: ネットワーク通信の自動化 - VPC Flow Logsによる自動監視

### 信頼性
- **REL10-BP01**: 複数の場所へのワークロードのデプロイ - マルチAZ配置
- **REL10-BP02**: 適切な場所の選択 - 複数のアベイラビリティゾーンの活用
- **REL11-BP01**: 障害の監視 - VPC Flow Logsとヘルスチェック

### パフォーマンス効率
- **PERF02-BP01**: 利用可能なネットワーク機能の評価 - 最適なサブネット配置
- **PERF03-BP01**: データ転送方法の最適化 - NAT Gatewayによる効率的なアウトバウンド通信

### コスト最適化
- **COST02-BP05**: 動的スケーリングの実装 - 必要に応じたNAT Gateway数の調整
- **COST05-BP01**: コスト効率の高いリソースの選択 - Single NAT Gatewayオプション

### 持続可能性
- **SUS02-BP01**: 使用率の高いインスタンスタイプの選択 - 効率的なネットワーク設計
- **SUS04-BP02**: 最適化されたデータアクセスとストレージパターンの実装 - 適切なサブネット分離

## 機能

### サブネットパターン

#### Basic パターン
- 2つのアベイラビリティゾーン
- パブリックサブネット × 2
- プライベートサブネット × 2
- NAT Gateway × 1（オプション）

#### Advanced パターン
- 3つのアベイラビリティゾーン
- パブリックサブネット × 3
- プライベートサブネット × 3
- データベースサブネット × 3
- NAT Gateway × 3（冗長化）

#### Enterprise パターン
- 3つのアベイラビリティゾーン
- パブリックサブネット × 3
- プライベートサブネット × 3
- データベースサブネット × 3
- 管理サブネット × 3
- NAT Gateway × 3（完全冗長化）

### セキュリティ機能

- **VPC Flow Logs**: すべてのネットワークトラフィックの監視
- **プライベートサブネット**: インターネットから直接アクセスできない安全な環境
- **NAT Gateway**: プライベートサブネットからの安全なアウトバウンド通信
- **適切なタグ付け**: リソース管理とコスト追跡

## パラメータ

| パラメータ名 | 説明 | デフォルト値 | 必須 |
|-------------|------|-------------|------|
| ProjectName | プロジェクト名 | MyProject | Yes |
| Environment | 環境名 (dev/staging/prod) | dev | Yes |
| VpcCidr | VPCのCIDRブロック | 10.0.0.0/16 | Yes |
| SubnetPattern | サブネットパターン (Basic/Advanced/Enterprise) | Basic | Yes |
| EnableDnsHostnames | DNS ホスト名の有効化 | true | No |
| EnableDnsSupport | DNS サポートの有効化 | true | No |
| EnableNatGateway | NAT Gatewayの有効化 | true | No |
| SingleNatGateway | 単一NAT Gateway使用 | false | No |

## 使用方法

### 1. 基本的なデプロイメント

```bash
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://vpc-template.yaml \
  --parameters file://vpc-config-basic.json \
  --capabilities CAPABILITY_IAM
```

### 2. 高度な設定でのデプロイメント

```bash
aws cloudformation create-stack \
  --stack-name my-vpc-advanced-stack \
  --template-body file://vpc-template.yaml \
  --parameters file://vpc-config-advanced.json \
  --capabilities CAPABILITY_IAM
```

### 3. エンタープライズ設定でのデプロイメント

```bash
aws cloudformation create-stack \
  --stack-name my-vpc-enterprise-stack \
  --template-body file://vpc-template.yaml \
  --parameters file://vpc-config-enterprise.json \
  --capabilities CAPABILITY_IAM
```

## 出力値

このテンプレートは以下の値をエクスポートします：

- **VPC-ID**: VPCのID
- **VPC-CIDR**: VPCのCIDRブロック
- **PublicSubnet1-ID, PublicSubnet2-ID, PublicSubnet3-ID**: パブリックサブネットのID
- **PrivateSubnet1-ID, PrivateSubnet2-ID, PrivateSubnet3-ID**: プライベートサブネットのID
- **DatabaseSubnet1-ID, DatabaseSubnet2-ID, DatabaseSubnet3-ID**: データベースサブネットのID
- **ManagementSubnet1-ID, ManagementSubnet2-ID, ManagementSubnet3-ID**: 管理サブネットのID
- **PublicSubnets**: パブリックサブネットのリスト
- **PrivateSubnets**: プライベートサブネットのリスト
- **DatabaseSubnets**: データベースサブネットのリスト
- **IGW-ID**: Internet GatewayのID
- **NatGateway1-ID, NatGateway2-ID, NatGateway3-ID**: NAT GatewayのID

## 依存関係

このテンプレートは独立して動作し、他のテンプレートに依存しません。ただし、出力値は他のテンプレートから参照可能です。

## コスト考慮事項

- **NAT Gateway**: 時間単位とデータ処理量に基づく課金
- **Elastic IP**: NAT Gateway用のEIPに対する課金
- **VPC Flow Logs**: CloudWatch Logsの保存とデータ取り込み料金

コスト最適化のため、開発環境では `SingleNatGateway: true` の設定を推奨します。

## トラブルシューティング

### よくある問題

1. **CIDR ブロックの重複**
   - 既存のVPCやサブネットとCIDRが重複していないか確認

2. **アベイラビリティゾーンの不足**
   - 選択したリージョンに十分なAZがあることを確認

3. **IAM権限不足**
   - VPC、サブネット、NAT Gateway、IAMロール作成権限が必要

### ログの確認

VPC Flow Logsは以下の場所で確認できます：
```
CloudWatch Logs > /aws/vpc/flowlogs/{ProjectName}-{Environment}
```

## 更新履歴

- v1.0: 初期リリース
  - Basic, Advanced, Enterprise パターンの実装
  - VPC Flow Logs対応
  - Well-Architected Framework準拠