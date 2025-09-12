#!/usr/bin/env python3
"""
CI/CD Integration Test Script
CloudFormation Parameter Migration - GitHub Actions Workflow Testing

このスクリプトはGitHub Actionsワークフローでの統合テストを実行し、
デプロイメントプロセスと監視・ログ設定を検証します。
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import time
import tempfile
import shutil

# CloudFormation対応のYAMLパーサーを使用
try:
    from awscli.customizations.cloudformation.yamlhelper import yaml_parse
except ImportError:
    # フォールバック: 標準のyamlを使用
    import yaml
    def yaml_parse(content):
        return yaml.safe_load(content)

class CICDIntegrationTester:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.template_path = self.project_root / "cf-templates" / "compute" / "ec2" / "ec2-autoscaling.yaml"
        self.config_files = {
            "basic": self.project_root / "test-parameters-basic.json",
            "advanced": self.project_root / "test-parameters-advanced.json", 
            "enterprise": self.project_root / "test-parameters-enterprise.json"
        }
        self.test_results = {}
        
    def log_info(self, message: str):
        """情報メッセージを記録"""
        print(f"ℹ️  {message}")
        
    def log_success(self, message: str):
        """成功メッセージを記録"""
        print(f"✅ {message}")
        
    def log_warning(self, message: str):
        """警告メッセージを記録"""
        print(f"⚠️  {message}")
        
    def log_error(self, message: str):
        """エラーメッセージを記録"""
        print(f"❌ {message}")

    def validate_github_actions_workflow(self) -> Tuple[bool, List[str]]:
        """GitHub Actionsワークフローファイルの検証"""
        self.log_info("GitHub Actionsワークフローファイルを検証中...")
        
        issues = []
        
        # ワークフローファイルの存在確認
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        if not workflow_files:
            issues.append("GitHub Actionsワークフローファイルが見つかりません")
            return False, issues
        
        active_workflows = [f for f in workflow_files if not f.name.endswith('.disabled')]
        
        if not active_workflows:
            issues.append("有効なGitHub Actionsワークフローファイルが見つかりません")
            return False, issues
        
        self.log_info(f"検証対象ワークフロー: {[f.name for f in active_workflows]}")
        
        # 各ワークフローファイルの検証
        for workflow_file in active_workflows:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    workflow = yaml_parse(content)
                
                # 必須セクションの確認
                required_sections = ['name', 'jobs']
                missing_sections = [section for section in required_sections if section not in workflow]
                
                # onフィールドの確認（YAMLパーサーがTrueとして解釈する場合もある）
                if 'on' not in workflow and True not in workflow:
                    missing_sections.append('on')
                
                if missing_sections:
                    issues.append(f"{workflow_file.name}: 必須セクションが不足: {missing_sections}")
                    continue
                
                # トリガー設定の確認
                triggers = workflow.get('on', {})
                if not any(trigger in triggers for trigger in ['push', 'pull_request', 'workflow_dispatch']):
                    issues.append(f"{workflow_file.name}: 適切なトリガーが設定されていません")
                
                # ジョブの確認
                jobs = workflow.get('jobs', {})
                if not jobs:
                    issues.append(f"{workflow_file.name}: ジョブが定義されていません")
                    continue
                
                # 必要なジョブの確認
                expected_jobs = ['validate-and-map', 'test-templates']
                for job_name in expected_jobs:
                    if job_name not in jobs:
                        issues.append(f"{workflow_file.name}: 必要なジョブ '{job_name}' が見つかりません")
                
                # 環境変数の確認
                env_vars = workflow.get('env', {})
                required_env_vars = ['AWS_DEFAULT_REGION', 'PYTHON_VERSION']
                for env_var in required_env_vars:
                    if env_var not in env_vars:
                        issues.append(f"{workflow_file.name}: 必要な環境変数 '{env_var}' が設定されていません")
                
                self.log_success(f"ワークフロー {workflow_file.name} の基本構造は正常です")
                
            except yaml.YAMLError as e:
                issues.append(f"{workflow_file.name}: YAML構文エラー: {e}")
            except Exception as e:
                issues.append(f"{workflow_file.name}: 検証エラー: {e}")
        
        return len(issues) == 0, issues

    def test_workflow_job_dependencies(self) -> Tuple[bool, List[str]]:
        """ワークフロージョブの依存関係テスト"""
        self.log_info("ワークフロージョブの依存関係を検証中...")
        
        issues = []
        
        try:
            workflow_file = self.workflows_dir / "ci-cd-pipeline-single-account.yml"
            if not workflow_file.exists():
                workflow_file = next(self.workflows_dir.glob("*.yml"), None)
            
            if not workflow_file:
                issues.append("検証対象のワークフローファイルが見つかりません")
                return False, issues
            
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
                workflow = yaml_parse(content)
            
            jobs = workflow.get('jobs', {})
            
            # 依存関係の検証
            dependency_chain = [
                ('validate-and-map', []),
                ('test-templates', ['validate-and-map']),
                ('request-deployment-approval', ['validate-and-map', 'test-templates']),
                ('deploy-to-aws', ['validate-and-map', 'test-templates', 'request-deployment-approval'])
            ]
            
            for job_name, expected_deps in dependency_chain:
                if job_name not in jobs:
                    continue
                
                job_config = jobs[job_name]
                actual_needs = job_config.get('needs', [])
                
                if isinstance(actual_needs, str):
                    actual_needs = [actual_needs]
                
                # 期待される依存関係がすべて含まれているかチェック
                missing_deps = [dep for dep in expected_deps if dep not in actual_needs]
                if missing_deps:
                    issues.append(f"ジョブ '{job_name}' に必要な依存関係が不足: {missing_deps}")
                
                self.log_success(f"ジョブ '{job_name}' の依存関係は正常です")
            
        except Exception as e:
            issues.append(f"依存関係検証エラー: {e}")
        
        return len(issues) == 0, issues

    def validate_deployment_process(self) -> Tuple[bool, List[str]]:
        """デプロイメントプロセスの検証"""
        self.log_info("デプロイメントプロセスを検証中...")
        
        issues = []
        
        # 設定ファイルとテンプレートの整合性確認
        for config_name, config_path in self.config_files.items():
            if not config_path.exists():
                issues.append(f"設定ファイルが見つかりません: {config_path}")
                continue
            
            try:
                # 設定ファイルの読み込み
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # パラメータの存在確認
                parameters = config.get('Parameters', {})
                if not parameters:
                    issues.append(f"{config_name}: パラメータが定義されていません")
                    continue
                
                # 必須パラメータの確認
                required_params = ['ProjectName', 'Environment', 'ConfigurationPattern', 'VpcId', 'SubnetIds']
                missing_params = [param for param in required_params if param not in parameters]
                
                if missing_params:
                    issues.append(f"{config_name}: 必須パラメータが不足: {missing_params}")
                
                # レガシーパラメータの確認（Phase 3では存在してはいけない）
                legacy_params = ['InstancePattern', 'AMIId', 'InstanceType', 'MinSize', 'MaxSize', 'DesiredCapacity']
                found_legacy = [param for param in legacy_params if param in parameters]
                
                if found_legacy:
                    issues.append(f"{config_name}: レガシーパラメータが残存（Phase 3では削除されるべき）: {found_legacy}")
                
                # パターン固有の検証
                pattern = parameters.get('ConfigurationPattern', '')
                if pattern == 'Enterprise':
                    enterprise_params = ['EnableEncryption', 'EnableDetailedMonitoring']
                    missing_enterprise = [param for param in enterprise_params if parameters.get(param) != 'true']
                    if missing_enterprise:
                        issues.append(f"{config_name}: Enterpriseパターンで必要な設定が無効: {missing_enterprise}")
                
                self.log_success(f"設定ファイル {config_name} の検証が完了")
                
            except json.JSONDecodeError as e:
                issues.append(f"{config_name}: JSON構文エラー: {e}")
            except Exception as e:
                issues.append(f"{config_name}: 検証エラー: {e}")
        
        return len(issues) == 0, issues

    def test_cloudformation_validation(self) -> Tuple[bool, List[str]]:
        """CloudFormationテンプレートの検証"""
        self.log_info("CloudFormationテンプレートを検証中...")
        
        issues = []
        
        if not self.template_path.exists():
            issues.append(f"CloudFormationテンプレートが見つかりません: {self.template_path}")
            return False, issues
        
        try:
            # テンプレート構文検証
            result = subprocess.run(
                ['aws', 'cloudformation', 'validate-template', '--template-body', f'file://{self.template_path}', '--profile', 'mame-local-wani'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_success("AWS CloudFormationテンプレート検証が成功")
            else:
                issues.append(f"CloudFormationテンプレート検証失敗: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            issues.append("CloudFormationテンプレート検証がタイムアウト")
        except FileNotFoundError:
            self.log_warning("AWS CLIが見つかりません。ローカル検証のみ実行")
            
            # ローカルYAML検証
            try:
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    template = yaml_parse(content)
                
                required_sections = ['AWSTemplateFormatVersion', 'Parameters', 'Resources']
                missing_sections = [section for section in required_sections if section not in template]
                
                if missing_sections:
                    issues.append(f"テンプレートに必須セクションが不足: {missing_sections}")
                else:
                    self.log_success("ローカルYAML検証が成功")
                    
            except yaml.YAMLError as e:
                issues.append(f"テンプレートYAML構文エラー: {e}")
        except Exception as e:
            issues.append(f"テンプレート検証エラー: {e}")
        
        # cfn-lint検証
        try:
            result = subprocess.run(
                ['cfn-lint', str(self.template_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log_success("cfn-lint検証が成功")
            else:
                # 重要なエラーのみを問題として扱う
                if "E" in result.stdout:
                    issues.append(f"cfn-lint重要エラー: {result.stdout}")
                else:
                    self.log_warning(f"cfn-lint警告: {result.stdout}")
                    
        except subprocess.TimeoutExpired:
            issues.append("cfn-lint検証がタイムアウト")
        except FileNotFoundError:
            self.log_warning("cfn-lintが見つかりません。スキップします")
        except Exception as e:
            issues.append(f"cfn-lint検証エラー: {e}")
        
        return len(issues) == 0, issues

    def test_changeset_creation(self) -> Tuple[bool, List[str]]:
        """CloudFormation Change Set作成テスト"""
        self.log_info("CloudFormation Change Set作成をテスト中...")
        
        issues = []
        
        for config_name, config_path in self.config_files.items():
            if not config_path.exists():
                continue
            
            try:
                # 設定ファイルの読み込み
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # CloudFormationパラメータ形式に変換
                cf_parameters = []
                for key, value in config.get('Parameters', {}).items():
                    cf_parameters.append({
                        'ParameterKey': key,
                        'ParameterValue': str(value)
                    })
                
                # 一時パラメータファイル作成
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(cf_parameters, f, indent=2)
                    param_file = f.name
                
                try:
                    stack_name = f"test-{config_name}-{os.getpid()}"
                    changeset_name = f"test-changeset-{config_name}"
                    
                    # Change Set作成
                    result = subprocess.run([
                        'aws', 'cloudformation', 'create-change-set',
                        '--stack-name', stack_name,
                        '--template-body', f'file://{self.template_path}',
                        '--parameters', f'file://{param_file}',
                        '--change-set-name', changeset_name,
                        '--capabilities', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM',
                        '--change-set-type', 'CREATE',
                        '--profile', 'mame-local-wani'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        self.log_success(f"{config_name}: Change Set作成が成功")
                        
                        # Change Set削除（クリーンアップ）
                        subprocess.run([
                            'aws', 'cloudformation', 'delete-change-set',
                            '--stack-name', stack_name,
                            '--change-set-name', changeset_name,
                            '--profile', 'mame-local-wani'
                        ], capture_output=True, timeout=30)
                        
                    else:
                        issues.append(f"{config_name}: Change Set作成失敗: {result.stderr}")
                
                finally:
                    os.unlink(param_file)
                    
            except subprocess.TimeoutExpired:
                issues.append(f"{config_name}: Change Set作成がタイムアウト")
            except FileNotFoundError:
                self.log_warning("AWS CLIが見つかりません。Change Setテストをスキップ")
                break
            except Exception as e:
                issues.append(f"{config_name}: Change Set作成エラー: {e}")
        
        return len(issues) == 0, issues

    def validate_monitoring_and_logging_configuration(self) -> Tuple[bool, List[str]]:
        """監視とログ設定の検証"""
        self.log_info("監視とログ設定を検証中...")
        
        issues = []
        
        try:
            # テンプレートから監視関連リソースを確認
            with open(self.template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                template = yaml_parse(content)
            
            resources = template.get('Resources', {})
            
            # CloudWatch関連リソースの確認
            cloudwatch_resources = [name for name, resource in resources.items() 
                                  if resource.get('Type', '').startswith('AWS::CloudWatch')]
            
            if not cloudwatch_resources:
                issues.append("CloudWatch監視リソースが定義されていません")
            else:
                self.log_success(f"CloudWatch監視リソースが定義されています: {cloudwatch_resources}")
            
            # Auto Scaling通知の確認
            notification_resources = [name for name, resource in resources.items() 
                                    if resource.get('Type') == 'AWS::AutoScaling::NotificationConfiguration']
            
            if not notification_resources:
                self.log_warning("Auto Scaling通知設定が見つかりません")
            else:
                self.log_success(f"Auto Scaling通知が設定されています: {notification_resources}")
            
            # IAMロールの確認
            iam_roles = [name for name, resource in resources.items() 
                        if resource.get('Type') == 'AWS::IAM::Role']
            
            if not iam_roles:
                issues.append("IAMロールが定義されていません")
            else:
                self.log_success(f"IAMロールが定義されています: {iam_roles}")
                
                # CloudWatchログ権限の確認
                for role_name in iam_roles:
                    role_resource = resources[role_name]
                    policies = role_resource.get('Properties', {}).get('Policies', [])
                    
                    has_cloudwatch_logs = False
                    for policy in policies:
                        policy_doc = policy.get('PolicyDocument', {})
                        statements = policy_doc.get('Statement', [])
                        
                        for statement in statements:
                            actions = statement.get('Action', [])
                            if isinstance(actions, str):
                                actions = [actions]
                            
                            if any('logs:' in action for action in actions):
                                has_cloudwatch_logs = True
                                break
                    
                    if has_cloudwatch_logs:
                        self.log_success(f"IAMロール {role_name} にCloudWatchログ権限が設定されています")
                    else:
                        self.log_warning(f"IAMロール {role_name} にCloudWatchログ権限が見つかりません")
            
            # セキュリティグループのログ設定確認
            security_groups = [name for name, resource in resources.items() 
                             if resource.get('Type') == 'AWS::EC2::SecurityGroup']
            
            if security_groups:
                self.log_success(f"セキュリティグループが定義されています: {security_groups}")
            else:
                issues.append("セキュリティグループが定義されていません")
            
        except Exception as e:
            issues.append(f"監視・ログ設定検証エラー: {e}")
        
        return len(issues) == 0, issues

    def test_environment_specific_deployment(self) -> Tuple[bool, List[str]]:
        """環境固有のデプロイメント設定テスト"""
        self.log_info("環境固有のデプロイメント設定をテスト中...")
        
        issues = []
        
        # 各設定ファイルの環境固有設定を確認
        for config_name, config_path in self.config_files.items():
            if not config_path.exists():
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                parameters = config.get('Parameters', {})
                environment = parameters.get('Environment', '')
                pattern = parameters.get('ConfigurationPattern', '')
                
                # 環境とパターンの整合性確認
                expected_patterns = {
                    'basic': ['Basic'],
                    'advanced': ['Advanced'],
                    'enterprise': ['Enterprise']
                }
                
                if pattern not in expected_patterns.get(config_name, []):
                    issues.append(f"{config_name}: 設定パターン '{pattern}' が設定名と一致しません")
                
                # 環境固有の設定確認
                if config_name == 'enterprise':
                    # Enterpriseは本番環境向けの設定が必要
                    if parameters.get('EnableEncryption') != 'true':
                        issues.append(f"{config_name}: Enterprise設定で暗号化が有効になっていません")
                    
                    if parameters.get('EnableDetailedMonitoring') != 'true':
                        issues.append(f"{config_name}: Enterprise設定で詳細監視が有効になっていません")
                
                elif config_name == 'basic':
                    # Basicは開発環境向けの軽量設定
                    if parameters.get('EnableSpotInstances') == 'true':
                        self.log_success(f"{config_name}: コスト最適化のためスポットインスタンスが有効")
                
                # タグ設定の確認
                tags = config.get('Tags', {})
                if not tags:
                    self.log_warning(f"{config_name}: タグが設定されていません")
                else:
                    required_tags = ['Environment', 'Project']
                    missing_tags = [tag for tag in required_tags if tag not in tags]
                    if missing_tags:
                        self.log_warning(f"{config_name}: 推奨タグが不足: {missing_tags}")
                
                self.log_success(f"{config_name}: 環境固有設定の検証が完了")
                
            except Exception as e:
                issues.append(f"{config_name}: 環境固有設定検証エラー: {e}")
        
        return len(issues) == 0, issues

    def run_comprehensive_ci_cd_test(self) -> Dict[str, Any]:
        """包括的なCI/CD統合テストを実行"""
        print("🚀 CI/CD統合テスト開始")
        print("=" * 80)
        
        test_results = {
            'overall_success': True,
            'tests': {}
        }
        
        # テスト1: GitHub Actionsワークフロー検証
        success, issues = self.validate_github_actions_workflow()
        test_results['tests']['github_actions_workflow'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト2: ワークフロージョブ依存関係テスト
        success, issues = self.test_workflow_job_dependencies()
        test_results['tests']['workflow_job_dependencies'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト3: デプロイメントプロセス検証
        success, issues = self.validate_deployment_process()
        test_results['tests']['deployment_process'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト4: CloudFormation検証
        success, issues = self.test_cloudformation_validation()
        test_results['tests']['cloudformation_validation'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト5: Change Set作成テスト
        success, issues = self.test_changeset_creation()
        test_results['tests']['changeset_creation'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト6: 監視・ログ設定検証
        success, issues = self.validate_monitoring_and_logging_configuration()
        test_results['tests']['monitoring_logging'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        # テスト7: 環境固有デプロイメントテスト
        success, issues = self.test_environment_specific_deployment()
        test_results['tests']['environment_specific_deployment'] = {
            'success': success,
            'issues': issues
        }
        if not success:
            test_results['overall_success'] = False
        
        return test_results

    def print_test_results(self, results: Dict[str, Any]):
        """テスト結果の表示"""
        print("\n" + "=" * 80)
        print("📊 CI/CD統合テスト結果")
        print("=" * 80)
        
        for test_name, test_result in results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            print(f"\n{test_name}: {status}")
            
            if not test_result['success'] and test_result['issues']:
                for issue in test_result['issues']:
                    print(f"  - {issue}")
        
        print("\n" + "=" * 80)
        if results['overall_success']:
            print("🎉 すべてのCI/CD統合テストが成功しました！")
            print("✅ GitHub Actionsワークフローは正常に動作します")
            print("✅ デプロイメントプロセスは適切に設定されています")
            print("✅ 監視とログ設定は正常です")
        else:
            print("❌ 一部のCI/CD統合テストが失敗しました")
            print("上記の問題を解決してから再実行してください")
        print("=" * 80)

def main():
    """メイン実行関数"""
    tester = CICDIntegrationTester()
    
    try:
        results = tester.run_comprehensive_ci_cd_test()
        tester.print_test_results(results)
        
        # 結果をファイルに保存
        results_file = tester.project_root / "ci-cd-integration-test-results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細結果を保存しました: {results_file}")
        
        # 終了コード設定
        sys.exit(0 if results['overall_success'] else 1)
        
    except Exception as e:
        print(f"❌ CI/CD統合テストが失敗しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()