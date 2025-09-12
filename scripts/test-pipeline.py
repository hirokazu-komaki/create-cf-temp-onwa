#!/usr/bin/env python3
"""
CloudFormation CI/CD パイプライン テストスクリプト

このスクリプトは、GitHub Actions CI/CDパイプラインの動作をローカルでテストするためのものです。
実際のパイプラインと同じ検証ロジックを使用して、設定ファイルとテンプレートの妥当性を確認します。
"""

import json

# CloudFormation対応のYAMLパーサーを使用
try:
    from awscli.customizations.cloudformation.yamlhelper import yaml_parse
except ImportError:
    # フォールバック: 標準のyamlを使用
    import yaml
    def yaml_parse(content):
        return yaml.safe_load(content)
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import boto3
from jsonschema import validate, ValidationError


class PipelineTester:
    """CI/CDパイプラインのテスト機能を提供するクラス"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.cf_templates_dir = self.workspace_root / "cf-templates"
        self.errors = []
        self.warnings = []
        
    def log_error(self, message: str):
        """エラーメッセージを記録"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
        
    def log_warning(self, message: str):
        """警告メッセージを記録"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
        
    def log_info(self, message: str):
        """情報メッセージを記録"""
        print(f"ℹ️  INFO: {message}")
        
    def log_success(self, message: str):
        """成功メッセージを記録"""
        print(f"✅ SUCCESS: {message}")

    def find_config_files(self, pattern: str = "*-config-*.json") -> List[Path]:
        """設定ファイルを検索"""
        config_files = list(self.workspace_root.rglob(pattern))
        self.log_info(f"Found {len(config_files)} config files")
        return config_files

    def validate_json_config(self, config_file: Path) -> bool:
        """JSON設定ファイルの妥当性を検証"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 基本スキーマ検証
            schema = {
                "type": "object",
                "required": ["Parameters"],
                "properties": {
                    "Parameters": {
                        "type": "object",
                        "minProperties": 1
                    },
                    "Tags": {"type": "object"},
                    "Description": {"type": "string"}
                }
            }
            
            validate(instance=config, schema=schema)
            self.log_success(f"JSON validation passed: {config_file.name}")
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in {config_file}: {e}")
            return False
        except ValidationError as e:
            self.log_error(f"Schema validation failed for {config_file}: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error validating {config_file}: {e}")
            return False

    def extract_deployment_info(self, config_file: Path) -> Tuple[str, str, str]:
        """設定ファイルからデプロイメント情報を抽出"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 環境の検出（主要な判定基準）
            environment = None
            if 'Environment' in config.get('Parameters', {}):
                environment = config['Parameters']['Environment'].lower()
            elif 'Environment' in config.get('Tags', {}):
                environment = config['Tags']['Environment'].lower()
            
            # リージョンの検出（ARNから推定も含む）
            region = None
            if 'Region' in config.get('Parameters', {}):
                region = config['Parameters']['Region']
            elif 'AWSRegion' in config.get('Parameters', {}):
                region = config['Parameters']['AWSRegion']
            else:
                # ARNからリージョンを推定
                for key, value in config.get('Parameters', {}).items():
                    if isinstance(value, str) and value.startswith('arn:aws:'):
                        parts = value.split(':')
                        if len(parts) >= 4 and parts[3]:
                            region = parts[3]
                            break
            
            # オプション: AWSアカウントの明示的指定
            aws_account = None
            if 'AWSAccount' in config.get('Parameters', {}):
                aws_account = config['Parameters']['AWSAccount']
            elif 'TargetAccount' in config.get('Parameters', {}):
                aws_account = config['Parameters']['TargetAccount']
            
            # 環境の正規化
            environment_mapping = {
                'production': 'prod',
                'prod': 'prod', 
                'staging': 'staging',
                'stage': 'staging',
                'development': 'dev',
                'dev': 'dev',
                'test': 'dev'
            }
            
            normalized_env = environment_mapping.get(environment, 'dev')
            
            return normalized_env, region or 'us-east-1', aws_account or ''
            
        except Exception as e:
            self.log_error(f"Error extracting deployment info from {config_file}: {e}")
            return 'dev', 'us-east-1', ''

    def map_config_to_template(self, config_file: Path) -> Path:
        """設定ファイルに対応するテンプレートファイルを検索"""
        config_dir = config_file.parent
        
        # サービス名を推定
        if config_dir.parts[-2:] == ('cf-templates',):
            service_name = config_file.stem.split('-config-')[0]
        else:
            service_name = config_dir.name
        
        # 可能なテンプレートファイル名を試行
        possible_templates = [
            config_dir / f"{service_name}-template.yaml",
            config_dir / f"{service_name}-template.yml", 
            config_dir / f"{service_name}.yaml",
            config_dir / f"{service_name}.yml",
            config_dir / "template.yaml",
            config_dir / "template.yml"
        ]
        
        for template_path in possible_templates:
            if template_path.exists():
                return template_path
        
        self.log_warning(f"No template found for config {config_file}")
        return None

    def lint_cloudformation_template(self, template_file: Path) -> bool:
        """CloudFormationテンプレートのLintチェック"""
        try:
            result = subprocess.run(
                ['cfn-lint', str(template_file)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.log_success(f"CFN Lint passed: {template_file.name}")
                return True
            else:
                self.log_error(f"CFN Lint failed for {template_file}:\n{result.stdout}")
                return False
                
        except FileNotFoundError:
            self.log_warning("cfn-lint not found. Install with: pip install cfn-lint")
            return True  # スキップ
        except Exception as e:
            self.log_error(f"Error running cfn-lint on {template_file}: {e}")
            return False

    def validate_cloudformation_template(self, template_file: Path, use_aws: bool = False) -> bool:
        """CloudFormationテンプレートの構文検証"""
        try:
            # YAMLファイルの読み込みテスト
            with open(template_file, \'r\', encoding=\'utf-8\') as f:

                content = f.read()

                template = yaml_parse(content)
            
            # 基本構造の確認
            if not isinstance(template, dict):
                self.log_error(f"Template {template_file} is not a valid YAML object")
                return False
            
            required_keys = ['AWSTemplateFormatVersion', 'Resources']
            missing_keys = [key for key in required_keys if key not in template]
            
            if missing_keys:
                self.log_error(f"Template {template_file} missing required keys: {missing_keys}")
                return False
            
            # AWS CLIを使用した検証（オプション）
            if use_aws:
                try:
                    result = subprocess.run([
                        'aws', 'cloudformation', 'validate-template',
                        '--template-body', f'file://{template_file}'
                    ], capture_output=True, text=True, check=True)
                    
                    self.log_success(f"AWS validation passed: {template_file.name}")
                    
                except subprocess.CalledProcessError as e:
                    self.log_error(f"AWS validation failed for {template_file}: {e.stderr}")
                    return False
                except FileNotFoundError:
                    self.log_warning("AWS CLI not found. Skipping AWS validation.")
            
            self.log_success(f"Template validation passed: {template_file.name}")
            return True
            
        except yaml.YAMLError as e:
            self.log_error(f"YAML parsing error in {template_file}: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error validating template {template_file}: {e}")
            return False

    def check_well_architected_compliance(self, template_file: Path) -> Dict[str, List[str]]:
        """Well-Architected Framework準拠チェック"""
        try:
            with open(template_file, \'r\', encoding=\'utf-8\') as f:

                content = f.read()

                template = yaml_parse(content)
            
            metadata = template.get('Metadata', {})
            wa_compliance = metadata.get('WellArchitectedCompliance', {})
            
            pillars = {
                'OperationalExcellence': wa_compliance.get('OperationalExcellence', []),
                'Security': wa_compliance.get('Security', []),
                'Reliability': wa_compliance.get('Reliability', []),
                'PerformanceEfficiency': wa_compliance.get('PerformanceEfficiency', []),
                'CostOptimization': wa_compliance.get('CostOptimization', []),
                'Sustainability': wa_compliance.get('Sustainability', [])
            }
            
            self.log_info(f"Well-Architected compliance for {template_file.name}:")
            for pillar, practices in pillars.items():
                if practices:
                    self.log_info(f"  ✓ {pillar}: {', '.join(practices)}")
                else:
                    self.log_warning(f"  - {pillar}: No practices defined")
            
            return pillars
            
        except Exception as e:
            self.log_error(f"Error checking Well-Architected compliance for {template_file}: {e}")
            return {}

    def convert_config_to_cf_parameters(self, config_file: Path) -> List[Dict[str, str]]:
        """JSON設定をCloudFormationパラメータ形式に変換"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            parameters = []
            for key, value in config.get('Parameters', {}).items():
                parameters.append({
                    'ParameterKey': key,
                    'ParameterValue': str(value)
                })
            
            self.log_success(f"Converted {len(parameters)} parameters from {config_file.name}")
            return parameters
            
        except Exception as e:
            self.log_error(f"Error converting config {config_file}: {e}")
            return []

    def test_template_deployment_dry_run(self, template_file: Path, parameters: List[Dict[str, str]], use_aws: bool = False) -> bool:
        """テンプレートデプロイメントのドライランテスト"""
        if not use_aws:
            self.log_info(f"Skipping AWS dry-run test for {template_file.name} (AWS not enabled)")
            return True
        
        try:
            import tempfile
            
            # パラメータファイルを一時作成
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(parameters, f, indent=2)
                param_file = f.name
            
            try:
                stack_name = f"test-{template_file.stem}-{os.getpid()}"
                
                # Change Setを作成してテスト
                result = subprocess.run([
                    'aws', 'cloudformation', 'create-change-set',
                    '--stack-name', stack_name,
                    '--template-body', f'file://{template_file}',
                    '--parameters', f'file://{param_file}',
                    '--change-set-name', 'test-changeset',
                    '--capabilities', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'
                ], capture_output=True, text=True, check=False)
                
                if result.returncode == 0:
                    self.log_success(f"Dry-run test passed: {template_file.name}")
                    
                    # Change Setを削除
                    subprocess.run([
                        'aws', 'cloudformation', 'delete-change-set',
                        '--stack-name', stack_name,
                        '--change-set-name', 'test-changeset'
                    ], capture_output=True, check=False)
                    
                    return True
                else:
                    self.log_error(f"Dry-run test failed for {template_file}: {result.stderr}")
                    return False
                    
            finally:
                os.unlink(param_file)
                
        except Exception as e:
            self.log_error(f"Error in dry-run test for {template_file}: {e}")
            return False

    def run_full_pipeline_test(self, config_files: List[Path] = None, use_aws: bool = False) -> bool:
        """完全なパイプラインテストを実行"""
        print("🚀 Starting CI/CD Pipeline Test")
        print("=" * 50)
        
        if config_files is None:
            config_files = self.find_config_files()
        
        if not config_files:
            self.log_warning("No config files found to test")
            return True
        
        all_passed = True
        
        for config_file in config_files:
            print(f"\n📋 Testing: {config_file}")
            print("-" * 30)
            
            # ステップ1: JSON設定ファイルの検証
            if not self.validate_json_config(config_file):
                all_passed = False
                continue
            
            # ステップ2: デプロイメント情報の抽出
            environment, region, aws_account = self.extract_deployment_info(config_file)
            self.log_info(f"Target Environment: {environment}")
            self.log_info(f"Target Region: {region}")
            if aws_account:
                self.log_info(f"Explicit AWS Account: {aws_account}")
            else:
                self.log_info("AWS Account: Environment-based default")
            
            # ステップ3: テンプレートファイルのマッピング
            template_file = self.map_config_to_template(config_file)
            if not template_file:
                all_passed = False
                continue
            
            # ステップ4: CloudFormationテンプレートのLint
            if not self.lint_cloudformation_template(template_file):
                all_passed = False
                continue
            
            # ステップ5: テンプレートの構文検証
            if not self.validate_cloudformation_template(template_file, use_aws):
                all_passed = False
                continue
            
            # ステップ6: Well-Architected準拠チェック
            self.check_well_architected_compliance(template_file)
            
            # ステップ7: パラメータ変換
            parameters = self.convert_config_to_cf_parameters(config_file)
            
            # ステップ8: ドライランテスト
            if not self.test_template_deployment_dry_run(template_file, parameters, use_aws):
                all_passed = False
                continue
            
            self.log_success(f"All tests passed for {config_file.name}")
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        if all_passed and not self.errors:
            print("🎉 All tests passed successfully!")
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} warnings found:")
                for warning in self.warnings:
                    print(f"   - {warning}")
        else:
            print(f"❌ {len(self.errors)} errors found:")
            for error in self.errors:
                print(f"   - {error}")
            
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} warnings found:")
                for warning in self.warnings:
                    print(f"   - {warning}")
        
        return all_passed and not self.errors


def main():
    parser = argparse.ArgumentParser(description='CloudFormation CI/CD Pipeline Tester')
    parser.add_argument('--config', '-c', type=str, nargs='*', 
                       help='Specific config files to test')
    parser.add_argument('--aws', action='store_true',
                       help='Enable AWS CLI validation and dry-run tests')
    parser.add_argument('--workspace', '-w', type=str, default='.',
                       help='Workspace root directory')
    
    args = parser.parse_args()
    
    tester = PipelineTester(args.workspace)
    
    config_files = None
    if args.config:
        config_files = [Path(f) for f in args.config]
        # 存在確認
        for f in config_files:
            if not f.exists():
                print(f"❌ Config file not found: {f}")
                sys.exit(1)
    
    success = tester.run_full_pipeline_test(config_files, args.aws)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()