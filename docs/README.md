# CloudFormation CI/CD ドキュメント

## 📚 ドキュメント一覧

### 🚀 はじめに

1. **[ワークフロー選択ガイド](workflow-selection-guide.md)** ⭐ **最初に読んでください**
   - マルチアカウント vs 単一アカウント方式の選択
   - プロジェクトの要件に応じた適切なワークフローの選択方法

### ⚙️ セットアップ

2. **[GitHub Actions セットアップガイド](github-actions-setup.md)**
   - GitHub Secrets の設定
   - AWS IAM の設定
   - GitHub Environments の設定

3. **[マルチアカウント認証戦略](multi-account-authentication-strategies.md)**
   - AssumeRole vs 直接Credentials の比較
   - セキュリティベストプラクティス

### 📋 運用ガイド

4. **[ブランチ戦略](branching-strategy.md)**
   - Git Flow ベースのブランチ戦略
   - 命名規則とワークフロー

5. **[デプロイメント設定ガイド](deployment-configuration-guide.md)**
   - 環境ベースのデプロイメント設定
   - JSON パラメータファイルの作成方法

### 🔧 技術詳細

6. **[CI/CDパイプライン概要](ci-cd-pipeline-overview.md)**
   - パイプラインの処理フロー
   - 各ステージの詳細説明

## 🎯 クイックスタート

### Step 1: ワークフローの選択

プロジェクトの要件に応じて適切なワークフローを選択してください：

| 要件 | 推奨ワークフロー | ファイル |
|------|----------------|---------|
| 大規模組織、厳格なセキュリティ | マルチアカウント | `.github/workflows/ci-cd-pipeline.yml` |
| 中小規模、シンプルな運用 | 単一アカウント | `.github/workflows/ci-cd-pipeline-single-account.yml` |

詳細は [ワークフロー選択ガイド](workflow-selection-guide.md) を参照してください。

### Step 2: 環境の設定

選択したワークフローに応じて、以下のガイドに従って設定を行ってください：

1. **AWS IAM の設定**
   - [GitHub Actions セットアップガイド](github-actions-setup.md#aws-iam設定) を参照

2. **GitHub Secrets の設定**
   - [GitHub Actions セットアップガイド](github-actions-setup.md#必要なsecrets設定) を参照

3. **GitHub Environments の設定**
   - [GitHub Actions セットアップガイド](github-actions-setup.md#github-environment設定) を参照

### Step 3: 設定ファイルの作成

環境に応じた JSON パラメータファイルを作成してください：

```json
{
  "Parameters": {
    "Environment": "staging",
    "ProjectName": "MyWebApp",
    "InstanceType": "t3.medium"
  },
  "Tags": {
    "Owner": "DevOps Team",
    "Environment": "Staging"
  }
}
```

詳細は [デプロイメント設定ガイド](deployment-configuration-guide.md) を参照してください。

### Step 4: デプロイメントの実行

1. 設定ファイルを作成・更新
2. Git にコミット・プッシュ
3. GitHub Actions でテストが自動実行
4. 承認プロセスを経てデプロイメント実行

## 🏗️ アーキテクチャ概要

### マルチアカウント方式

```
GitHub Actions
    ↓
Central AWS Account
    ↓ AssumeRole
┌─────────────┬─────────────┬─────────────┐
│ Production  │ Staging     │ Development │
│ Account     │ Account     │ Account     │
└─────────────┴─────────────┴─────────────┘
```

### 単一アカウント方式

```
GitHub Actions
    ↓
Single AWS Account
    ├── prod-*-stack
    ├── staging-*-stack
    └── dev-*-stack
```

## 🔒 セキュリティ

### マルチアカウント方式

- **物理的分離**: アカウント境界による完全な分離
- **AssumeRole**: 一時的な認証情報の使用
- **最小権限**: 環境ごとの細かい権限制御

### 単一アカウント方式

- **論理的分離**: IAM とタグによる分離
- **シンプルな権限管理**: 単一の認証情報セット
- **コスト効率**: 管理オーバーヘッドの削減

## 🛠️ トラブルシューティング

### よくある問題

1. **ワークフローが実行されない**
   - 複数のワークフローファイルが有効になっていないか確認
   - 使用しないワークフローを `.disabled` 拡張子で無効化

2. **認証エラー**
   - GitHub Secrets の設定を確認
   - AWS IAM の権限を確認
   - AssumeRole の信頼関係を確認

3. **環境の混在**
   - 現在のリソース状況を調査
   - 統一する方式を決定して段階的に移行

詳細は各ガイドのトラブルシューティングセクションを参照してください。

## 📞 サポート

- **一般的な質問**: GitHub Discussions
- **バグレポート**: GitHub Issues
- **緊急事態**: DevOps チームに直接連絡

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

---

**注意**: 本番環境での使用前に、必ず設定を確認し、十分なテストを実施してください。