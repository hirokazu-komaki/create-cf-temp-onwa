# KMS Encryption Keys Template

## 概要

このテンプレートは、AWS Well-Architected Frameworkのセキュリティ柱に準拠したKMS暗号化キー管理システムを作成します。自動キーローテーション、詳細なアクセス制御、複数の用途別キーパターンを提供し、包括的な暗号化戦略を実装します。

## Well-Architected準拠項目

- **SEC08-BP01**: 保存時の暗号化を実装する
- **SEC08-BP02**: 転送時の暗号化を実装する
- **SEC08-BP03**: 暗号化キーを自動化して管理する
- **SEC08-BP04**: 暗号化キーの使用を強制する
- **SEC02-BP01**: 最小権限の原則を使用する
- **OPS04-BP01**: 設定管理システムを実装する
- **OPS05-BP01**: 自動化を使用してデプロイメントリスクを軽減する
- **REL03-BP01**: 自動復旧機能を実装する

## キー管理パターン

### Basic
- **用途**: 開発環境、シンプルな暗号化要件
- **キー数**: 1個（汎用キー）
- **機能**: 基本的な暗号化・復号化
- **ローテーション**: 有効

### Advanced
- **用途**: 本番環境、複雑な暗号化要件
- **キー数**: 4個（汎用、S3、RDS、EBS専用）
- **機能**: サービス別専用キー、詳細アクセス制御
- **ローテーション**: 有効

### Enterprise
- **用途**: 大規模組織、厳格なコンプライアンス
- **キー数**: 6個（Advanced + Secrets Manager、CloudTrail専用）
- **機能**: 包括的キー管理、監査機能
- **ローテーション**: 有効 + 監視

## パラメータ

| パラメータ名 | 型 | デフォルト | 説明 |
|-------------|-----|-----------|------|
| KMSPattern | String | Basic | KMS設定パターン |
| ProjectName | String | MyProject | プロジェクト名 |
| Environment | String | dev | 環境名 |
| EnableKeyRotation | String | true | 自動キーローテーション |
| KeyUsage | String | ENCRYPT_DECRYPT | キー使用目的 |
| KeySpec | String | SYMMETRIC_DEFAULT | キー仕様 |
| DeletionWindowInDays | Number | 30 | キー削除待機期間 |
| CrossAccountAccessRoleArns | CommaDelimitedList | - | クロスアカウントアクセスロール |
| EnableCloudTrailIntegration | String | true | CloudTrail統合 |

## 作成されるキー

### 汎用暗号化キー（全パターン）
- **用途**: 一般的な暗号化・復号化
- **アクセス**: プロジェクト内のすべてのロール
- **エイリアス**: `alias/{ProjectName}-{Environment}-general-purpose`

### S3専用暗号化キー（Advanced以上）
- **用途**: S3バケットとオブジェクトの暗号化
- **アクセス**: S3サービス + プロジェクトロール
- **エイリアス**: `alias/{ProjectName}-{Environment}-s3-encryption`

### RDS専用暗号化キー（Advanced以上）
- **用途**: RDSインスタンスとスナップショットの暗号化
- **アクセス**: RDSサービス + プロジェクトロール
- **エイリアス**: `alias/{ProjectName}-{Environment}-rds-encryption`

### EBS専用暗号化キー（Advanced以上）
- **用途**: EBSボリュームの暗号化
- **アクセス**: EC2サービス + プロジェクトロール
- **エイリアス**: `alias/{ProjectName}-{Environment}-ebs-encryption`

### Secrets Manager専用暗号化キー（Enterprise）
- **用途**: Secrets Managerシークレットの暗号化
- **アクセス**: Secrets Managerサービス + プロジェクトロール
- **エイリアス**: `alias/{ProjectName}-{Environment}-secrets-manager-encryption`

### CloudTrail専用暗号化キー（Enterprise）
- **用途**: CloudTrailログの暗号化
- **アクセス**: CloudTrailサービス
- **エイリアス**: `alias/{ProjectName}-{Environment}-cloudtrail-encryption`

## セキュリティ機能

### アクセス制御
- **最小権限**: 各キーは特定の用途とサービスに限定
- **サービス制限**: ViaService条件による制限
- **クロスアカウント**: 指定されたロールのみアクセス可能

### 監視と監査
- **CloudWatch Alarms**: キー使用状況の監視
- **CloudWatch Events**: キーローテーションイベントの追跡
- **CloudTrail**: すべてのキー操作の記録

### 自動化
- **キーローテーション**: 年次自動ローテーション
- **ライフサイクル管理**: 削除保護期間の設定
- **タグ管理**: 自動的なタグ付け

## 使用例

### 基本的な使用方法

```bash
aws cloudformation create-stack \
  --stack-name my-project-kms \
  --template-body file://kms-keys.yaml \
  --parameters file://sample-config.json \
  --capabilities CAPABILITY_IAM
```

### S3バケット暗号化での使用

```yaml
S3Bucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: aws:kms
            KMSMasterKeyID: !ImportValue MyProject-prod-s3-encryption-key-arn
```

### RDS暗号化での使用

```yaml
RDSInstance:
  Type: AWS::RDS::DBInstance
  Properties:
    StorageEncrypted: true
    KmsKeyId: !ImportValue MyProject-prod-rds-encryption-key-arn
```

## 運用考慮事項

### コスト管理
- **キー数**: 必要最小限のキー数に制限
- **リクエスト数**: キー使用量の監視
- **ストレージ**: 暗号化データのストレージコスト

### パフォーマンス
- **キャッシング**: データキーのキャッシング活用
- **リージョン**: 同一リージョン内でのキー使用
- **バッチ処理**: 大量データ処理時の考慮

### 災害復旧
- **キーバックアップ**: 自動的なキーマテリアルバックアップ
- **クロスリージョン**: 必要に応じたマルチリージョン展開
- **復旧手順**: キー復旧プロセスの文書化

## セキュリティベストプラクティス

1. **キー分離**: 用途別のキー分離
2. **アクセス制限**: 最小権限の原則
3. **監査**: 定期的なアクセスレビュー
4. **ローテーション**: 定期的なキーローテーション
5. **監視**: 異常なキー使用の検出

## 出力値

- **各キーのID**: キー識別子
- **各キーのARN**: キーのAmazon Resource Name
- **キーエイリアス**: 人間が読みやすいキー名
- **KMSPattern**: 使用されたパターン

## トラブルシューティング

### よくある問題

1. **アクセス拒否エラー**
   ```bash
   aws kms describe-key --key-id alias/my-key
   ```

2. **キーローテーション失敗**
   ```bash
   aws kms get-key-rotation-status --key-id key-id
   ```

3. **クロスアカウントアクセス問題**
   ```bash
   aws kms get-key-policy --key-id key-id --policy-name default
   ```

### 確認コマンド

```bash
# キー一覧確認
aws kms list-keys

# キー詳細確認
aws kms describe-key --key-id key-id

# キー使用状況確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/KMS \
  --metric-name NumberOfRequestsSucceeded \
  --dimensions Name=KeyId,Value=key-id \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 注意事項

⚠️ **重要**: KMSキーの削除は不可逆的です。削除前に必ず影響範囲を確認してください。

⚠️ **警告**: キーポリシーの変更は既存のアクセス権限に影響する可能性があります。

⚠️ **推奨**: 本番環境では必ずキーローテーションを有効にし、定期的な監査を実施してください。

⚠️ **コスト**: KMSキーは作成するだけで月額料金が発生します。不要なキーは削除してください。