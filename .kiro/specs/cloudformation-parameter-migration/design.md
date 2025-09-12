# 設計ドキュメント

## 概要

この設計ドキュメントは、現在のパラメータ不整合問題を解決するためのCloudFormationテンプレートパラメータ移行の技術的アプローチを説明します。移行は3段階のアプローチに従い、統一されたパラメータ構造に向かいながら後方互換性を確保します。

## アーキテクチャ

### 現状分析

**設定ファイル構造:**
- Basic: 直接値を持つシンプルなパラメータ
- Advanced: 追加の監視とスケーリングパラメータ  
- Enterprise: セキュリティとコンプライアンスパラメータを含む完全な機能セット

**テンプレート構造:**
- パターンベース設定にMappingsを使用
- 設定ファイルが期待するいくつかのパラメータが不足
- 一貫性のないパラメータ命名規則

**主要な問題:**
1. パラメータ名の不一致 (`InstancePattern` vs `ConfigurationPattern`)
2. 不足しているパラメータ (`AMIId`, `InstanceType`, `EnableAutoScaling`など)
3. 異なる設計思想 (直接パラメータ vs パターンベース)

### ターゲットアーキテクチャ

**ハイブリッドパラメータアプローチ:**
- Mappingsからのパターンベースデフォルト
- 指定時の個別パラメータオーバーライド
- 両方のアプローチを処理する条件ロジック
- 移行期間中の後方互換性

## コンポーネントとインターフェース

### フェーズ1: 後方互換性レイヤー

#### パラメータマッピング戦略
```yaml
Parameters:
  # レガシーパラメータサポート (フェーズ1)
  InstancePattern:          # ConfigurationPatternにマップ
    Type: String
    Default: ''
  AMIId:                   # InstanceAMIにマップ  
    Type: String
    Default: ''
  InstanceType:            # Mappingベース選択のオーバーライド
    Type: String
    Default: ''
  MinSize:                 # Mappingベース値のオーバーライド
    Type: Number
    Default: 0
  MaxSize:                 # Mappingベース値のオーバーライド
    Type: Number  
    Default: 0
  DesiredCapacity:         # Mappingベース値のオーバーライド
    Type: Number
    Default: 0
  EnableAutoScaling:       # ASG作成制御
    Type: String
    Default: 'true'
    AllowedValues: ['true', 'false']
```

#### 条件ロジック
```yaml
Conditions:
  # レガシーパラメータ検出
  HasLegacyInstancePattern: !Not [!Equals [!Ref InstancePattern, '']]
  HasCustomAMI: !Not [!Equals [!Ref AMIId, '']]
  HasCustomInstanceType: !Not [!Equals [!Ref InstanceType, '']]
  HasCustomMinSize: !Not [!Equals [!Ref MinSize, 0]]
  HasCustomMaxSize: !Not [!Equals [!Ref MaxSize, 0]]
  HasCustomDesiredCapacity: !Not [!Equals [!Ref DesiredCapacity, 0]]
  
  # 機能制御
  CreateAutoScalingGroup: !Equals [!Ref EnableAutoScaling, 'true']
  
  # パターン解決
  UseConfigurationPattern: !If [
    HasLegacyInstancePattern,
    !Ref InstancePattern,
    !Ref ConfigurationPattern
  ]
```

### フェーズ2: 統一されたパラメータ構造

#### 新しいパラメータカテゴリ
```yaml
# コアインフラストラクチャ (必須)
ProjectName: String
Environment: String  
ConfigurationPattern: String
VpcId: AWS::EC2::VPC::Id
SubnetIds: List<AWS::EC2::Subnet::Id>

# インスタンス設定 (オプションオーバーライド)
InstanceAMI: String                    # AMIIdを置換
CustomInstanceType: String            # InstanceTypeを置換
CustomMinSize: Number                 # MinSizeを置換
CustomMaxSize: Number                 # MaxSizeを置換  
CustomDesiredCapacity: Number         # DesiredCapacityを置換

# 機能制御
EnableAutoScaling: String
EnableDetailedMonitoring: String
EnableSpotInstances: String

# 高度な機能 (Advanced/Enterprise)
RootVolumeSize: Number
RootVolumeType: String
EnableEncryption: String
KMSKeyId: String
TargetGroupArns: CommaDelimitedList

# エンタープライズ機能
EnableMixedInstancesPolicy: String
InstanceTypes: CommaDelimitedList
EnableNitroEnclave: String
```

### フェーズ3: クリーンな実装

#### 最終パラメータ構造
- すべてのレガシーパラメータサポートを削除
- 新しい命名規則を強制
- 簡素化された条件ロジック
- 明確なパラメータドキュメント

## データモデル

### 設定ファイルの進化

#### フェーズ1: 後方互換
```json
{
  "Parameters": {
    "InstancePattern": "Basic",        // レガシーサポート
    "ConfigurationPattern": "Basic",   // 新しい推奨
    "AMIId": "ami-12345",             // レガシーサポート
    "InstanceAMI": "ami-12345",       // 新しい推奨
    // ... その他のパラメータ
  }
}
```

#### フェーズ2: 混合サポート
```json
{
  "Parameters": {
    "ConfigurationPattern": "Advanced",
    "InstanceAMI": "ami-12345",
    "CustomInstanceType": "t3.medium",
    "EnableAutoScaling": "true",
    // ... 新しいパラメータ構造
  }
}
```

#### フェーズ3: クリーンな構造
```json
{
  "Parameters": {
    "ConfigurationPattern": "Enterprise",
    "ProjectName": "MyApp",
    "Environment": "prod",
    // ... 新しいパラメータのみ
  }
}
```

### Mapping構造の強化

```yaml
Mappings:
  InstanceTypePatterns:
    Basic:
      PrimaryType: t3.micro
      SecondaryType: t3.small
      MinSize: 1
      MaxSize: 2
      DesiredCapacity: 1
      MonitoringEnabled: false
      SpotEnabled: false
    Advanced:
      PrimaryType: t3.medium
      SecondaryType: m5.large
      MinSize: 2
      MaxSize: 4
      DesiredCapacity: 2
      MonitoringEnabled: true
      SpotEnabled: true
    Enterprise:
      PrimaryType: m5.large
      SecondaryType: m5.xlarge
      MinSize: 3
      MaxSize: 10
      DesiredCapacity: 3
      MonitoringEnabled: true
      SpotEnabled: false
```

## エラーハンドリング

### フェーズ1: 検証戦略
- 古いパラメータ名と新しいパラメータ名の両方を受け入れ
- パラメータの組み合わせを検証
- 競合に対する明確なエラーメッセージを提供
- 非推奨パラメータに対する警告をログ出力

### フェーズ2: 移行検証
- 新しいパラメータ構造を検証
- パターンに基づく必須パラメータをチェック
- Advanced/Enterprise機能が適切に設定されていることを確認
- パラメータ値の制約を検証

### フェーズ3: 厳密な検証
- レガシーパラメータ名を拒否
- 新しいパラメータ構造を強制
- エラーメッセージで移行ガイダンスを提供
- 完全なパラメータ一貫性を検証

## テスト戦略

### フェーズ1テスト
1. **後方互換性テスト**
   - すべての既存設定ファイルをテスト
   - CloudFormationテンプレート構文を検証
   - cfn-lint検証を実行
   - GitHub Actionsワークフローを実行
   - ドライラン デプロイメントを実行

2. **パラメータマッピングテスト**
   - レガシーパラメータマッピングを検証
   - 条件ロジックをテスト
   - 異なるパラメータ組み合わせでのリソース作成を検証

### フェーズ2テスト
1. **新しいパラメータ構造テスト**
   - 新しい設定ファイルをテスト
   - パラメータオーバーライドロジックを検証
   - パターンベースデフォルトをテスト
   - Advanced/Enterprise機能の有効化を検証

2. **混合設定テスト**
   - 古いパラメータと新しいパラメータの組み合わせをテスト
   - 優先順位ルールを検証
   - 移行シナリオをテスト

### フェーズ3テスト
1. **クリーンな実装テスト**
   - 最終パラメータ構造をテスト
   - レガシーパラメータのエラーハンドリングを検証
   - すべての設定パターンをテスト
   - 包括的な統合テストを実行

### 各フェーズの検証チェックリスト

#### テンプレート検証
- [ ] CloudFormationテンプレート構文検証が通る
- [ ] cfn-lint検証が重要な問題なしで通る
- [ ] パラメータ制約が適切に定義されている
- [ ] 条件ロジックが正しい

#### デプロイメント検証  
- [ ] GitHub Actionsワークフローが正常に実行される
- [ ] すべての設定ファイルでチェンジセット作成が成功する
- [ ] ドライランデプロイメントがエラーなしで完了する
- [ ] スタック作成/更新操作が成功する

#### 機能検証
- [ ] リソースが正しい設定で作成される
- [ ] Auto Scaling Groupが正しいサイジングを持つ
- [ ] インスタンスタイプが期待値と一致する
- [ ] セキュリティグループとIAMロールが適切に設定される
- [ ] 監視とログが期待通りに設定される

#### 回帰テスト
- [ ] 既存機能がそのまま維持される
- [ ] サポートされるユースケースに破壊的変更がない
- [ ] パフォーマンス特性が維持される
- [ ] セキュリティ設定が保持される

## 実装タイムライン

### フェーズ1: 1-2日
- テンプレートに不足しているパラメータを追加
- 後方互換性ロジックを実装
- 条件ベースのリソース作成を追加
- 包括的なテストと検証

### フェーズ2: 2-3日  
- 新しいパラメータ構造を実装
- 設定ファイルを更新
- 高度な機能サポートを追加
- 移行テストと検証

### フェーズ3: 1-2日
- レガシーパラメータサポートを削除
- 条件ロジックをクリーンアップ
- ドキュメントを更新
- 最終テストと検証

## リスク軽減

### デプロイメントリスク
- **リスク**: 既存デプロイメントの破壊
- **軽減策**: フェーズ1での包括的な後方互換性

### パラメータ競合
- **リスク**: パラメータ値の競合
- **軽減策**: 明確な優先順位ルールと検証

### 機能回帰
- **リスク**: 移行中の機能喪失
- **軽減策**: 各フェーズでの広範囲なテスト

### 移行の複雑さ
- **リスク**: 複雑な移行プロセス
- **軽減策**: 検証チェックポイントを持つ段階的アプローチ