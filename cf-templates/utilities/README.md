# CloudFormation Template Utilities

このディレクトリには、Well-Architected Framework準拠のCloudFormationテンプレートを使用するためのユーティリティが含まれています。

## ユーティリティ概要

### Parameter Processor
JSON設定ファイルをCloudFormationパラメータに変換するユーティリティです。

**機能:**
- JSON設定ファイルの検証
- CloudFormationパラメータ形式への変換
- エラーハンドリングとメッセージ生成

**使用方法:**
```bash
# 基本的な使用方法
python utilities/process-config.py configurations/examples/sample-project-config.json

# 出力ファイルを指定
python utilities/process-config.py my-config.json my-cf-params.json

# 直接パラメータプロセッサを使用
python utilities/parameter-processor/parameter-processor.py config.json output.json
```

### Well-Architected Validator
CloudFormationテンプレートのWell-Architected Framework準拠をチェックするユーティリティです。

**機能:**
- テンプレートメタデータの検証
- Well-Architected準拠チェック
- コンプライアンスレポートの生成

**使用方法:**
```bash
# テンプレートの検証
python utilities/validation/well-architected-validator.py template.yaml

# レポート生成
python utilities/validation/well-architected-validator.py template.yaml report.json
```

## 設定ファイル形式

### プロジェクト設定ファイル
```json
{
  "projectConfig": {
    "projectName": "my-project",
    "environment": "dev|staging|prod",
    "region": "us-east-1",
    "availabilityZones": ["us-east-1a", "us-east-1b"],
    "tags": {
      "Project": "MyProject",
      "Environment": "Development"
    }
  },
  "serviceConfigs": {
    "vpc": {
      "pattern": "basic|advanced|enterprise",
      "cidrBlock": "10.0.0.0/16",
      "enableDnsHostnames": true,
      "enableDnsSupport": true
    },
    "ec2": {
      "pattern": "basic|advanced|enterprise",
      "instanceType": "t3.micro",
      "keyPairName": "my-key-pair"
    }
  },
  "integrationOptions": {
    "crossStackReferences": true,
    "sharedResources": ["vpc", "security-groups"],
    "monitoringIntegration": true
  }
}
```

## 依存関係

Python 3.7以上が必要です。

必要なパッケージをインストール:
```bash
pip install -r utilities/parameter-processor/requirements.txt
```

## エラーハンドリング

ユーティリティは以下のエラーを適切に処理します:

1. **設定エラー**
   - 無効なJSON形式
   - 必須パラメータの不足
   - パラメータ値の範囲外

2. **テンプレートエラー**
   - テンプレートの構文エラー
   - メタデータの不足
   - Well-Architected準拠項目の不正

3. **ファイルエラー**
   - ファイルが見つからない
   - 読み取り権限がない
   - 書き込み権限がない

## 出力形式

### CloudFormationパラメータファイル
```json
[
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "my-project"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "dev"
  }
]
```

### コンプライアンスレポート
```json
{
  "templatePath": "template.yaml",
  "validationTimestamp": "2024-01-01T00:00:00Z",
  "isCompliant": true,
  "messages": [
    "✓ SEC01-BP01: Separate workloads using accounts",
    "✓ REL02-BP01: Use highly available network connectivity"
  ],
  "summary": {
    "totalChecks": 10,
    "passed": 8,
    "warnings": 2,
    "errors": 0
  }
}
```