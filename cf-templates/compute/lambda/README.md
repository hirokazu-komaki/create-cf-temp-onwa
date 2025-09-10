# Lambda Function テンプレート

## 概要

このディレクトリには、AWS Well-Architected Framework準拠のLambda Functionテンプレートが含まれています。サーバーレスアーキテクチャ、監視、セキュリティ、コスト最適化を重視した設計となっています。

## テンプレート構成

### 1. lambda-function.yaml
メインのLambda Functionテンプレート

**主な機能:**
- 複数の設定パターン（Basic/Advanced/Enterprise）
- IAM実行ロールとセキュリティ設定
- CloudWatch監視とX-Rayトレーシング
- VPC設定オプション
- Provisioned Concurrency対応
- デッドレターキュー統合

### 2. lambda-layer.yaml
Lambda Layerテンプレート

**主な機能:**
- 共有ライブラリとユーティリティ
- 複数ランタイム対応
- 共通関数とヘルパークラス

### 3. lambda-config-example.json
設定例ファイル

## 設定パターン

### Basic（基本）
- **用途**: 軽量処理、API Gateway統合
- **メモリ**: 128MB
- **タイムアウト**: 30秒
- **同時実行数**: 10
- **特徴**: コスト重視、シンプルな処理向け

### Advanced（高度）
- **用途**: データ変換、外部API呼び出し
- **メモリ**: 512MB
- **タイムアウト**: 5分
- **同時実行数**: 50
- **特徴**: バランス重視、中程度の処理向け

### Enterprise（エンタープライズ）
- **用途**: バッチ処理、機械学習推論
- **メモリ**: 1024MB
- **タイムアウト**: 15分
- **同時実行数**: 100
- **特徴**: パフォーマンス重視、高負荷処理向け

## デプロイ方法

### 1. Lambda Function デプロイ
```bash
aws cloudformation create-stack \
  --stack-name my-project-dev-lambda \
  --template-body file://lambda-function.yaml \
  --parameters file://lambda-config-example.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### 2. Lambda Layer デプロイ
```bash
aws cloudformation create-stack \
  --stack-name my-project-dev-lambda-layer \
  --template-body file://lambda-layer.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=my-project
```

### 3. 関数コードのアップロード
```bash
# S3にコードをアップロード
aws s3 cp function.zip s3://my-bucket/lambda-code/function.zip

# 関数コードを更新
aws lambda update-function-code \
  --function-name my-project-dev-api-handler \
  --s3-bucket my-bucket \
  --s3-key lambda-code/function.zip
```

## パラメータ説明

### 必須パラメータ
- **ProjectName**: プロジェクト名
- **Environment**: 環境名 (dev/staging/prod)
- **FunctionName**: Lambda関数名

### オプションパラメータ
- **ConfigurationPattern**: 設定パターン (Basic/Advanced/Enterprise)
- **Runtime**: ランタイム (python3.9, nodejs18.x等)
- **Handler**: ハンドラー関数
- **EnableVPC**: VPC内実行の有効化
- **EnableXRayTracing**: X-Rayトレーシングの有効化
- **LogRetentionDays**: ログ保持日数

## VPC設定

### VPC使用時の考慮事項
- **コールドスタート**: ENI作成による初期化遅延
- **NAT Gateway**: 外部API呼び出し時に必要
- **セキュリティグループ**: 適切なアウトバウンドルール設定
- **サブネット**: 複数AZのプライベートサブネット推奨

### VPC設定例
```json
{
  "enableVPC": "true",
  "vpcId": "vpc-12345678",
  "subnetIds": ["subnet-12345678", "subnet-87654321"]
}
```

## 監視とアラート

### CloudWatchメトリクス
- **Invocations**: 実行回数
- **Duration**: 実行時間
- **Errors**: エラー数
- **Throttles**: スロットリング数
- **ConcurrentExecutions**: 同時実行数

### アラーム設定
- **エラー率アラーム**: 5回以上のエラー
- **実行時間アラーム**: タイムアウト値の80%超過
- **スロットリングアラーム**: スロットリング発生

### X-Rayトレーシング
- 分散トレーシングによるパフォーマンス分析
- 外部サービス呼び出しの可視化
- ボトルネック特定とレイテンシ分析

## コスト最適化

### メモリサイズ最適化
- CPU性能はメモリサイズに比例
- 実行時間とメモリのバランス最適化
- AWS Lambda Power Tuningツール活用

### 同時実行制御
- **Reserved Concurrency**: コスト制御
- **Provisioned Concurrency**: コールドスタート削減
- 予測可能な負荷パターンでの活用

### ログ管理
- 環境別のログ保持期間設定
- 不要なログレベルの削減
- 構造化ログによる効率化

## セキュリティ

### IAM権限
- 最小権限の原則
- リソースベースのポリシー
- クロスアカウントアクセス制御

### VPCセキュリティ
- プライベートサブネット配置
- セキュリティグループによる通信制御
- NACLによる追加防御

### 暗号化
- 環境変数の暗号化
- KMSキーによる暗号化
- 転送時暗号化（HTTPS）

## Well-Architected Framework準拠項目

### オペレーショナルエクセレンス
- **OPS04-BP01**: Infrastructure as Codeによる自動化
- **OPS04-BP02**: 運用手順の文書化
- **OPS05-BP01**: CloudWatch監視
- **OPS06-BP01**: カスタムメトリクス収集

### セキュリティ
- **SEC01-BP01**: IAMロールによる最小権限アクセス
- **SEC02-BP02**: VPCによる多層防御
- **SEC05-BP01**: CloudWatchログ記録
- **SEC09-BP01**: X-Rayトレーシング

### 信頼性
- **REL02-BP01**: 自動復旧とリトライ機能
- **REL03-BP01**: ヘルスチェックとアラーム
- **REL04-BP01**: デッドレターキュー
- **REL11-BP01**: 同時実行制御

### パフォーマンス効率
- **PERF01-BP01**: 適切なメモリサイズ選択
- **PERF03-BP01**: 監視とアラート
- **PERF04-BP01**: Provisioned Concurrency

### コスト最適化
- **COST01-BP01**: 使用量ベースの課金モデル
- **COST02-BP01**: 適切なリソースサイジング
- **COST07-BP01**: リソース使用量監視

### 持続可能性
- **SUS01-BP01**: サーバーレスアーキテクチャ
- **SUS02-BP01**: 効率的なリソース使用
- **SUS06-BP01**: 最適化されたコード

## サンプルコード

### Python関数例
```python
import json
import logging
import os
from datetime import datetime

# Lambda Layerからユーティリティをインポート
from lambda_layer import setup_logging, create_response, MetricsHelper

logger = setup_logging()
metrics = MetricsHelper(os.environ.get('POWERTOOLS_METRICS_NAMESPACE'))

def lambda_handler(event, context):
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
        # ビジネスロジック
        result = process_request(event)
        
        # カスタムメトリクス送信
        metrics.put_metric('ProcessedRequests', 1, 'Count')
        
        return create_response(200, {
            'message': 'Success',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        metrics.put_metric('ProcessingErrors', 1, 'Count')
        
        return create_response(500, {
            'error': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        })

def process_request(event):
    # ビジネスロジックの実装
    return {"processed": True}
```

### Node.js関数例
```javascript
const AWS = require('aws-sdk');

exports.handler = async (event, context) => {
    console.log('Event:', JSON.stringify(event, null, 2));
    
    try {
        const result = await processRequest(event);
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                message: 'Success',
                result: result,
                timestamp: new Date().toISOString()
            })
        };
        
    } catch (error) {
        console.error('Error:', error);
        
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                error: 'Internal server error',
                timestamp: new Date().toISOString()
            })
        };
    }
};

async function processRequest(event) {
    // ビジネスロジックの実装
    return { processed: true };
}
```

## トラブルシューティング

### よくある問題

1. **コールドスタートが遅い**
   - Provisioned Concurrencyの使用検討
   - 不要な依存関係の削除
   - Lambda Layerの活用

2. **メモリ不足エラー**
   - メモリサイズの増加
   - メモリ使用量の最適化
   - ストリーミング処理の検討

3. **タイムアウトエラー**
   - タイムアウト値の調整
   - 処理の分割・並列化
   - 非同期処理の活用

4. **VPC内での外部API呼び出し失敗**
   - NAT Gatewayの設定確認
   - セキュリティグループの確認
   - ルートテーブルの確認

### ログ確認
```bash
# CloudWatchログの確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/my-project"

# 最新のログストリーム確認
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/my-project-dev-api-handler" \
  --order-by LastEventTime --descending
```

### メトリクス確認
```bash
# Lambda関数のメトリクス取得
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=my-project-dev-api-handler \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

## 関連テンプレート

- **API Gateway**: `cf-templates/integration/api-gateway/`
- **VPC**: `cf-templates/networking/vpc/`
- **IAM**: `cf-templates/foundation/iam/`
- **CloudWatch**: `cf-templates/integration/cloudwatch/`

## 更新履歴

- v1.0: 初期リリース
  - 基本的なLambda Function機能
  - Well-Architected Framework準拠
  - 監視とアラート機能
  - Lambda Layer対応