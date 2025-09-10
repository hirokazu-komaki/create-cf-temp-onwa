# IAM Roles and Policies Template

## 概要

このテンプレートは、AWS Well-Architected Frameworkのセキュリティ柱に準拠したIAMロールとポリシーを作成します。最小権限の原則に基づき、3つの権限パターン（Basic、Advanced、Enterprise）を提供し、クロスアカウントアクセスとMFA要件をサポートします。

## Well-Architected準拠項目

- **SEC02-BP01**: 最小権限の原則を使用する
- **SEC02-BP02**: 一時的な認証情報を使用する
- **SEC02-BP03**: 強力なアイデンティティ基盤を確立する
- **SEC03-BP01**: プログラムによるアクセスを制御する
- **SEC03-BP02**: ルートユーザーとプロパティを管理する
- **OPS04-BP01**: 設定管理システムを実装する
- **OPS04-BP02**: 設定ドリフトを管理する

## 権限パターン

### Basic
- **用途**: 開発環境、小規模プロジェクト
- **権限**: EC2、S3、CloudWatch の基本操作
- **セッション時間**: 1時間
- **MFA**: オプション

### Advanced
- **用途**: 本番環境、中規模プロジェクト
- **権限**: EC2、S3、RDS、Lambda、IAM、CloudWatch の包括的操作
- **セッション時間**: 2時間
- **MFA**: 推奨

### Enterprise
- **用途**: 大規模組織、コンプライアンス要件
- **権限**: 全サービスアクセス（危険な操作は除外）
- **セッション時間**: 4時間
- **MFA**: 必須

## パラメータ

| パラメータ名 | 型 | デフォルト | 説明 |
|-------------|-----|-----------|------|
| PermissionPattern | String | Basic | 権限パターンの選択 |
| ProjectName | String | MyProject | プロジェクト名 |
| Environment | String | dev | 環境名 |
| EnableCrossAccountAccess | String | false | クロスアカウントアクセスの有効化 |
| TrustedAccountIds | CommaDelimitedList | - | 信頼するアカウントIDリスト |
| EnableMFARequirement | String | true | MFA要件の有効化 |
| SessionDurationHours | Number | 1 | セッション継続時間 |

## 作成されるリソース

### ロール
- **実行ロール**: 選択されたパターンに応じた権限を持つメインロール
- **インスタンスプロファイル**: EC2インスタンス用のプロファイル
- **クロスアカウントアクセスロール**: 他アカウントからのアクセス用
- **監査ロール**: 読み取り専用の監査用ロール

### ポリシー
- **実行ポリシー**: パターンに応じたカスタムポリシー
- **管理ポリシー**: AWS管理ポリシーのアタッチ

## 使用例

### 基本的な使用方法

```bash
aws cloudformation create-stack \
  --stack-name my-project-iam \
  --template-body file://iam-roles-policies.yaml \
  --parameters file://sample-config.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### クロスアカウントアクセス有効化

```json
{
  "Parameters": {
    "PermissionPattern": "Advanced",
    "EnableCrossAccountAccess": "true",
    "TrustedAccountIds": ["123456789012", "987654321098"],
    "EnableMFARequirement": "true"
  }
}
```

## セキュリティ考慮事項

1. **MFA要件**: 本番環境では必ずMFAを有効にしてください
2. **セッション時間**: 必要最小限の時間に設定してください
3. **信頼アカウント**: クロスアカウントアクセスでは信頼するアカウントを慎重に選択してください
4. **権限パターン**: 必要最小限の権限パターンを選択してください

## 出力値

- **ExecutionRoleArn**: 実行ロールのARN
- **InstanceProfileArn**: インスタンスプロファイルのARN
- **CrossAccountAccessRoleArn**: クロスアカウントアクセスロールのARN
- **AuditRoleArn**: 監査ロールのARN
- **PermissionPattern**: 使用された権限パターン

## トラブルシューティング

### よくある問題

1. **権限不足エラー**: より高い権限パターンを選択するか、カスタムポリシーを追加
2. **MFA要件エラー**: MFAが有効になっているか確認
3. **クロスアカウントアクセス失敗**: 信頼アカウントIDが正しいか確認

### ログ確認

CloudTrailでIAMアクションのログを確認できます：

```bash
aws logs filter-log-events \
  --log-group-name CloudTrail/IAMEvents \
  --filter-pattern "{ $.eventName = AssumeRole }"
```