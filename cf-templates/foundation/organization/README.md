# AWS Organizations Setup Template

## 概要

このテンプレートは、AWS Well-Architected Frameworkに準拠したAWS Organizations設定を作成します。組織単位（OU）の構造、Service Control Policy（SCP）、セキュリティサービスの統合を含む包括的なガバナンス設定を提供します。

## Well-Architected準拠項目

- **SEC01-BP01**: 強力なアイデンティティ基盤を確立する
- **SEC01-BP02**: 一元化されたアイデンティティプロバイダーを使用する
- **SEC02-BP01**: 最小権限の原則を使用する
- **SEC03-BP01**: プログラムによるアクセスを制御する
- **SEC04-BP01**: セキュリティイベントをキャプチャし分析する
- **OPS01-BP01**: 組織の優先順位を評価する
- **OPS01-BP02**: 組織構造を評価する
- **COST01-BP01**: コスト最適化機能を実装する

## 組織パターン

### Basic
- **用途**: 小規模組織、シンプルなガバナンス
- **OU構造**: Security、Production
- **SCP**: 基本的な制限
- **サービス**: CloudTrail、Config

### Advanced
- **用途**: 中規模組織、部門別管理
- **OU構造**: Security、Production、Development、Staging
- **SCP**: 詳細な権限制御
- **サービス**: CloudTrail、Config、GuardDuty

### Enterprise
- **用途**: 大規模組織、厳格なコンプライアンス
- **OU構造**: 全OU + Sandbox、SharedServices
- **SCP**: 包括的なリスク軽減
- **サービス**: 全セキュリティサービス統合

## パラメータ

| パラメータ名 | 型 | デフォルト | 説明 |
|-------------|-----|-----------|------|
| OrganizationPattern | String | Basic | 組織設定パターン |
| OrganizationName | String | MyOrganization | 組織名 |
| EnableAllFeatures | String | true | すべての機能を有効化 |
| EnableCloudTrail | String | true | CloudTrail有効化 |
| EnableConfig | String | true | Config有効化 |
| EnableGuardDuty | String | true | GuardDuty有効化 |
| EnableSecurityHub | String | true | Security Hub有効化 |
| DenyRootUserActions | String | true | ルートユーザー制限 |
| RestrictRegions | String | true | リージョン制限 |
| AllowedRegions | CommaDelimitedList | us-east-1,us-west-2,ap-northeast-1 | 許可リージョン |

## 作成されるリソース

### 組織構造
- **Organization**: AWS Organizations
- **OU**: 環境別組織単位
- **SCP**: Service Control Policy

### セキュリティサービス
- **CloudTrail**: 組織全体の監査ログ
- **Config**: 設定変更の追跡
- **GuardDuty**: 脅威検出
- **Security Hub**: セキュリティ統合

### ガバナンス
- **SCP**: 権限制限ポリシー
- **リージョン制限**: 使用可能リージョンの制御
- **ルートユーザー制限**: 危険なアクションの防止

## Service Control Policies (SCP)

### DenyRootUserActions
ルートユーザーによる危険なアクションを防止：
- IAMユーザー/ロールの作成・削除
- 組織からの離脱
- アカウントの閉鎖

### RegionRestriction
指定されたリージョン以外での操作を制限：
- グローバルサービスは除外
- 必要なサービスプリンシパルは許可

### DenyHighRiskActions（Enterprise）
高リスクなアクションを制限：
- インスタンス終了
- データベース削除
- バケット削除

## 使用例

### 基本的な使用方法

```bash
aws cloudformation create-stack \
  --stack-name my-organization \
  --template-body file://organization-setup.yaml \
  --parameters file://sample-config.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### エンタープライズ設定

```json
{
  "Parameters": {
    "OrganizationPattern": "Enterprise",
    "EnableAllFeatures": "true",
    "DenyRootUserActions": "true",
    "RestrictRegions": "true",
    "AllowedRegions": ["us-east-1", "us-west-2", "eu-west-1"]
  }
}
```

## セキュリティ考慮事項

1. **SCP適用**: 本番環境では必ずSCPを適用してください
2. **ルートユーザー**: ルートユーザーのアクセスを厳格に制限
3. **リージョン制限**: 必要最小限のリージョンのみ許可
4. **監査ログ**: CloudTrailログの保護と監視

## 運用考慮事項

1. **アカウント移動**: OUの変更は慎重に実施
2. **SCP変更**: 影響範囲を事前に確認
3. **コスト監視**: 組織全体のコスト追跡
4. **コンプライアンス**: 定期的な準拠性チェック

## 出力値

- **OrganizationId**: 組織ID
- **OrganizationRootId**: ルートID
- **各OUId**: 組織単位ID
- **サービスARN**: 各セキュリティサービスのARN

## トラブルシューティング

### よくある問題

1. **SCP適用エラー**: 既存の権限との競合を確認
2. **サービス有効化失敗**: 必要な権限があるか確認
3. **リージョン制限**: グローバルサービスが除外されているか確認

### 確認コマンド

```bash
# 組織情報確認
aws organizations describe-organization

# OU一覧確認
aws organizations list-organizational-units-for-parent --parent-id r-xxxx

# SCP確認
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
```

## 注意事項

⚠️ **重要**: このテンプレートは組織のマスターアカウントでのみ実行してください。

⚠️ **警告**: SCPの適用は既存のアクセス権限に影響する可能性があります。事前にテスト環境で検証してください。