# API Gateway テンプレート

## 概要

このテンプレートは、AWS Well-Architected Framework に準拠した API Gateway の設定を提供します。REST API と HTTP API の両方をサポートし、認証・認可、レート制限、キャッシング機能を含みます。

## 機能

### サポートされる API タイプ
- **REST API**: 従来の REST API Gateway
- **HTTP API**: 低レイテンシ・低コストの HTTP API Gateway
- **BOTH**: 両方の API タイプを同時にデプロイ

### 認証・認可オプション
- **NONE**: 認証なし
- **AWS_IAM**: IAM ベースの認証
- **COGNITO_USER_POOLS**: Cognito User Pool による認証
- **LAMBDA_AUTHORIZER**: Lambda 関数による認証

### パフォーマンス機能
- **キャッシング**: レスポンスキャッシングによる性能向上
- **レート制限**: API の過負荷を防ぐスロットリング
- **X-Ray トレーシング**: リクエストの詳細な追跡

### 監視・ログ機能
- **CloudWatch ログ**: 詳細なアクセスログ
- **メトリクス**: API の使用状況とパフォーマンス監視
- **アラーム**: 異常検知とアラート

## 設定パターン

### Basic
- 基本的な API Gateway 設定
- CloudWatch ログ記録
- 基本的なメトリクス

### Advanced
- キャッシング機能
- 詳細なメトリクス
- レート制限

### Enterprise
- Lambda Authorizer サポート
- X-Ray トレーシング
- WAF 統合準備
- 高度なセキュリティ設定

## パラメータ

| パラメータ名 | 説明 | デフォルト値 | 必須 |
|-------------|------|-------------|------|
| ProjectName | プロジェクト名 | my-project | Yes |
| Environment | 環境名 (dev/staging/prod) | dev | Yes |
| ApiType | API タイプ (REST/HTTP/BOTH) | REST | Yes |
| ConfigurationPattern | 設定パターン | Basic | Yes |
| AuthenticationType | 認証タイプ | NONE | No |
| CognitoUserPoolId | Cognito User Pool ID | "" | No |
| LambdaAuthorizerFunctionArn | Lambda Authorizer ARN | "" | No |
| EnableCaching | キャッシング有効化 | false | No |
| CachingTtlInSeconds | キャッシュ TTL (秒) | 300 | No |
| ThrottleBurstLimit | バーストリミット | 2000 | No |
| ThrottleRateLimit | レートリミット | 1000 | No |
| EnableXRayTracing | X-Ray トレーシング | false | No |
| LogLevel | ログレベル | INFO | No |

## 使用例

### 基本的な REST API

```json
{
  "Parameters": {
    "ProjectName": "my-api",
    "Environment": "dev",
    "ApiType": "REST",
    "ConfigurationPattern": "Basic"
  }
}
```

### Cognito 認証付き API

```json
{
  "Parameters": {
    "ProjectName": "secure-api",
    "Environment": "prod",
    "ApiType": "REST",
    "ConfigurationPattern": "Advanced",
    "AuthenticationType": "COGNITO_USER_POOLS",
    "CognitoUserPoolId": "us-east-1_XXXXXXXXX",
    "EnableCaching": "true",
    "EnableXRayTracing": "true"
  }
}
```

### Lambda Authorizer 付きエンタープライズ設定

```json
{
  "Parameters": {
    "ProjectName": "enterprise-api",
    "Environment": "prod",
    "ApiType": "BOTH",
    "ConfigurationPattern": "Enterprise",
    "AuthenticationType": "LAMBDA_AUTHORIZER",
    "LambdaAuthorizerFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:my-authorizer",
    "EnableCaching": "true",
    "CachingTtlInSeconds": 600,
    "ThrottleBurstLimit": 5000,
    "ThrottleRateLimit": 2000,
    "EnableXRayTracing": "true",
    "LogLevel": "INFO"
  }
}
```

## デプロイ方法

```bash
# テンプレートの検証
aws cloudformation validate-template \
  --template-body file://api-gateway-template.yaml

# スタックのデプロイ
aws cloudformation deploy \
  --template-file api-gateway-template.yaml \
  --stack-name my-api-gateway \
  --parameter-overrides file://api-gateway-config-example.json \
  --capabilities CAPABILITY_NAMED_IAM
```

## 出力値

| 出力名 | 説明 |
|--------|------|
| RestApiId | REST API の ID |
| RestApiUrl | REST API の URL |
| HttpApiId | HTTP API の ID |
| HttpApiUrl | HTTP API の URL |
| ApiGatewayLogGroupName | CloudWatch ロググループ名 |
| ApiGatewayCloudWatchRoleArn | CloudWatch ロール ARN |

## Well-Architected Framework 準拠

### オペレーショナルエクセレンス
- **OPS04-BP01**: 運用手順の文書化
- **OPS04-BP02**: 運用手順の定期的な見直し
- **OPS07-BP01**: 運用メトリクスの理解

### セキュリティ
- **SEC01-BP01**: アカウントの分離と管理
- **SEC02-BP02**: 最小権限の原則
- **SEC03-BP01**: プログラムによるアクセス
- **SEC03-BP07**: 認証情報の定期的な監査

### 信頼性
- **REL01-BP04**: 制限の監視と管理
- **REL02-BP01**: 障害の分離
- **REL08-BP01**: 自動復旧の実装

### パフォーマンス効率
- **PERF02-BP01**: 進化するテクノロジーの評価
- **PERF03-BP01**: データ駆動型のアーキテクチャ選択
- **PERF04-BP01**: キャッシングの活用

### コスト最適化
- **COST02-BP05**: 使用量の監視
- **COST05-BP01**: コスト効率の高いリソース
- **COST07-BP01**: データ転送の最適化

### 持続可能性
- **SUS02-BP01**: 使用パターンの最適化
- **SUS04-BP02**: ソフトウェアパターンの最適化

## トラブルシューティング

### よくある問題

1. **認証エラー**
   - Cognito User Pool ID が正しいか確認
   - Lambda Authorizer の権限設定を確認

2. **キャッシングが動作しない**
   - キャッシュキーの設定を確認
   - TTL 設定を確認

3. **レート制限エラー**
   - スロットリング設定を確認
   - 使用量プランの設定を確認

### ログの確認

```bash
# API Gateway のログを確認
aws logs describe-log-groups --log-group-name-prefix "/aws/apigateway"

# 特定のログストリームを確認
aws logs get-log-events --log-group-name "/aws/apigateway/my-project-dev" --log-stream-name "log-stream-name"
```

## 関連リソース

- [AWS API Gateway ドキュメント](https://docs.aws.amazon.com/apigateway/)
- [Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [CloudFormation API Gateway リファレンス](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_ApiGateway.html)