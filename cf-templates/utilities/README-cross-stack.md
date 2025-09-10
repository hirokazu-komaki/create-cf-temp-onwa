# Cross-Stack Integration Management

このディレクトリには、Well-Architected準拠CloudFormationテンプレート間のクロススタック統合を管理するためのユーティリティが含まれています。

## 概要

クロススタック統合機能により、以下が可能になります：

- **依存関係管理**: スタック間の依存関係を明確に定義
- **Outputs/Imports**: CloudFormationのExport/ImportValue機能を活用した値の共有
- **検証機能**: 依存関係の整合性チェックとエラーハンドリング
- **自動化**: テンプレートの自動更新とパラメータ生成

## ファイル構成

```
utilities/
├── cross-stack-manager.py      # メインの管理クラス
├── cross-stack-config.json     # スタック間依存関係の設定
├── update-outputs.py           # テンプレートのOutputs更新スクリプト
├── validate-dependencies.py    # 依存関係検証スクリプト
└── README-cross-stack.md       # このファイル
```

## 使用方法

### 1. 設定ファイルの理解

`cross-stack-config.json`には以下の情報が定義されています：

```json
{
  "stack_outputs": {
    "スタック名": [
      {
        "name": "出力名",
        "description": "説明",
        "value": "CloudFormation値",
        "export_name": "エクスポート名テンプレート",
        "conditions": ["条件名"]
      }
    ]
  },
  "dependencies": {
    "スタック名": [
      {
        "stack_name": "依存先スタック名",
        "required_outputs": ["必須出力リスト"],
        "optional_outputs": ["オプション出力リスト"]
      }
    ]
  }
}
```

### 2. テンプレートの更新

既存のテンプレートにクロススタック対応を追加：

```bash
python update-outputs.py
```

このスクリプトは以下を実行します：
- 各テンプレートのOutputsセクションを設定に基づいて更新
- 依存関係に基づいてインポートパラメータを追加

### 3. 依存関係の検証

デプロイ前に依存関係を検証：

```bash
# 全スタックの検証
python validate-dependencies.py --region us-east-1

# 特定スタックのみ検証
python validate-dependencies.py --stack networking-vpc --region us-east-1

# AWSプロファイルを指定
python validate-dependencies.py --profile my-profile --region us-east-1
```

### 4. プログラムによる管理

Pythonスクリプトから直接管理：

```python
from cross_stack_manager import CrossStackManager, StackOutput, StackDependency

# マネージャーを初期化
manager = CrossStackManager(region='us-east-1')

# 設定を読み込み
manager.import_configuration('cross-stack-config.json')

# 依存関係を検証
result = manager.validate_dependencies('compute-ec2')
if result['valid']:
    print("依存関係は正常です")
else:
    print("エラー:", result['errors'])
```

## スタック依存関係

### 基盤レイヤー
- `foundation-iam`: IAMロールとポリシー
- `foundation-kms`: 暗号化キー
- `foundation-config`: AWS Config設定
- `foundation-organization`: AWS Organizations設定

### ネットワークレイヤー
- `networking-vpc`: VPCとサブネット（基盤レイヤーに依存）
- `networking-route53`: DNS管理
- `networking-elb`: ロードバランサー（VPCに依存）

### コンピューティングレイヤー
- `compute-ec2`: EC2インスタンス（VPC、IAMに依存）
- `compute-lambda`: Lambda関数（VPC、IAM、KMSに依存）

### 統合レイヤー
- `integration-api-gateway`: API Gateway（Lambdaに依存）
- `integration-cloudwatch`: 監視とログ

### パターンレイヤー
- `patterns-web-application`: Webアプリケーションパターン
- `patterns-microservices`: マイクロサービスパターン
- `patterns-data-processing`: データ処理パターン

## エクスポート命名規則

すべてのエクスポート名は以下の形式に従います：

```
{ProjectName}-{Environment}-{ResourceType}-{Identifier}
```

例：
- `MyProject-prod-VPC-ID`
- `MyProject-dev-ALB-DNSName`
- `MyProject-staging-Lambda-Function-Arn`

## 依存関係の解決順序

スタックは以下の順序でデプロイする必要があります：

1. **基盤レイヤー** (並行可能)
   - foundation-iam
   - foundation-kms
   - foundation-config
   - foundation-organization

2. **ネットワークレイヤー**
   - networking-vpc
   - networking-route53 (並行可能)

3. **コンピューティングレイヤー** (並行可能)
   - compute-ec2
   - compute-lambda

4. **統合レイヤー**
   - networking-elb
   - integration-api-gateway
   - integration-cloudwatch (並行可能)

5. **パターンレイヤー** (並行可能)
   - patterns-web-application
   - patterns-microservices
   - patterns-data-processing

## エラーハンドリング

### 一般的なエラーと対処法

1. **依存スタックが存在しない**
   ```
   Error: 依存スタック 'networking-vpc' が存在しません
   ```
   対処法: 依存スタックを先にデプロイしてください

2. **必須エクスポートが見つからない**
   ```
   Error: 必須エクスポート 'VPCId' が依存スタック 'networking-vpc' に存在しません
   ```
   対処法: 依存スタックのOutputsセクションを確認してください

3. **循環依存関係**
   ```
   Error: 循環依存関係が検出されました: stack-a -> stack-b -> stack-a
   ```
   対処法: 依存関係を見直し、循環を解消してください

4. **スタックステータスが不正**
   ```
   Error: 依存スタック 'networking-vpc' のステータスが不正: UPDATE_ROLLBACK_COMPLETE
   ```
   対処法: 依存スタックを正常な状態に修復してください

## ベストプラクティス

### 1. 段階的デプロイメント
- 依存関係の順序に従ってスタックをデプロイ
- 各レイヤーの完了を確認してから次に進む

### 2. 検証の実行
- デプロイ前に必ず依存関係を検証
- CI/CDパイプラインに検証ステップを組み込み

### 3. エクスポート名の管理
- 一貫した命名規則の使用
- プロジェクト名と環境名の適切な設定

### 4. 条件付きリソース
- 条件付きOutputsの適切な使用
- パターンに応じた柔軟な設定

### 5. ドキュメント化
- 依存関係の明確な文書化
- 変更時の影響範囲の把握

## トラブルシューティング

### デバッグ情報の取得

```bash
# 詳細な検証レポートを生成
python validate-dependencies.py --output detailed-report.txt

# 特定スタックの詳細確認
aws cloudformation describe-stacks --stack-name my-stack --region us-east-1

# エクスポート値の確認
aws cloudformation list-exports --region us-east-1
```

### よくある問題

1. **テンプレート更新後のエラー**
   - 構文エラーの確認
   - YAML形式の検証

2. **パラメータの不一致**
   - インポートパラメータ名の確認
   - エクスポート名の一致確認

3. **権限エラー**
   - CloudFormation実行権限の確認
   - クロスアカウントアクセスの設定確認

## 拡張方法

### 新しいスタックの追加

1. `cross-stack-config.json`に設定を追加
2. `update-outputs.py`のマッピングを更新
3. テンプレートを更新実行
4. 依存関係を検証

### カスタム検証ルールの追加

`validate-dependencies.py`を拡張して、プロジェクト固有の検証ルールを追加できます。

## サポート

問題が発生した場合は、以下を確認してください：

1. AWS CLIの設定と権限
2. CloudFormationスタックの状態
3. エクスポート値の存在
4. 依存関係の順序

詳細なログとエラーメッセージを含めて報告してください。