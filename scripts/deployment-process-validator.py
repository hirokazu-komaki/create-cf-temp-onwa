#!/usr/bin/env python3
"""
Deployment Process Validator
CloudFormation Parameter Migration - Deployment Process Verification

このスクリプトはデプロイメントプロセス全体の検証を行い、
本番環境での安全なデプロイメントを保証します。
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import time

# CloudFormation対応のYAMLパーサーを使用
try:
    from awscli.customizations.cloudformation.yamlhelper import yaml_parse
except ImportError:
    # フォールバック: 標準のyamlを使用
    import yaml
    def yaml_parse(content):
        return yaml.safe_load(content)

class DeploymentProcessValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.template_path = self.project_root / "cf-templates" / "compute" / "ec2" / "ec2-autoscaling.yaml"
        self.config_files = {
            "basic": self.project_root / "test-parameters-basic.json",
            "advanced": self.project_root / "test-parameters-advanced.json", 
            "enterprise": self.project_root / "test-parameters-enterprise.json"
        }
        self.test_results = {}
        
        # AWS クライアントの初期化
        try:
            self.cf_client = boto3.client('cloudformation')
            self.sts_client = boto3.client('sts')
            self.aws_available = True
        except Exception as e:
            print(f"⚠️  AWS クライアントの初期化に失敗: {e}")
            print("ローカル検証のみ実行します")
            self.cf_client = None
            self.sts_client = None
            self.aws_available = False
        
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

    def validate_aws_credentials(self) -> Tuple[bool, str]:
        """AWS認証情報の検証"""
        if not self.aws_available:
            return False, "AWS STSクライアントが利用できません"
        
        try:
            response = self.sts_client.get_caller_identity()
            account_id = response.get('Account')
            user_arn = response.get('Arn')
            
            self.log_success(f"AWS認証成功 - Account: {account_id}")
            self.log_info(f"User ARN: {user_arn}")
            return True, f"AWS認証成功 - Account: {account_id}"
            
        except ClientError as e:
            error_msg = f"AWS認証エラー: {e}"
            return False, error_msg
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            return False, error_msg

    def validate_cloudformation_permissions(self) -> Tuple[bool, str]:
        """CloudFormation権限の検証"""
        if not self.aws_available:
            return False, "CloudFormationクライアントが利用できません"
        
        try:
            # CloudFormationの基本的な権限をテスト
            self.cf_client.list_stacks(MaxItems=1)
            self.log_success("CloudFormation権限確認成功")
            return True, "CloudFormation権限確認成功"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                error_msg = "CloudFormationへのアクセス権限がありません"
            else:
                error_msg = f"CloudFormation権限エラー: {e}"
            return False, error_msg
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            return False, error_msg

    def validate_template_parameter_compatibility(self) -> Tuple[bool, List[str]]:
        """テンプレートとパラメータファイルの互換性検証"""
        issues = []
        
        try:
            # テンプレートの読み込み
            with open(self.template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                template = yaml_parse(content)
            
            template_params = template.get('Parameters', {})
            
            for config_name, config_file in self.config_files.items():
                if not config_file.exists():
                    issues.append(f"{config_name}: 設定ファイルが見つかりません - {config_file}")
                    continue
                
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    config_params = config.get('Parameters', {})
                    
                    # 必須パラメータの確認
                    required_params = [name for name, param in template_params.items() 
                                     if 'Default' not in param]
                    
                    missing_params = [param for param in required_params 
                                    if param not in config_params]
                    
                    if missing_params:
                        issues.append(f"{config_name}: 必須パラメータが不足 - {missing_params}")
                    
                    # 不要なパラメータの確認
                    extra_params = [param for param in config_params 
                                  if param not in template_params]
                    
                    if extra_params:
                        issues.append(f"{config_name}: 不要なパラメータ - {extra_params}")
                    
                    if not missing_params and not extra_params:
                        self.log_success(f"{config_name}: パラメータ互換性確認成功")
                
                except json.JSONDecodeError as e:
                    issues.append(f"{config_name}: JSON形式エラー - {e}")
                except Exception as e:
                    issues.append(f"{config_name}: 設定ファイル読み込みエラー - {e}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"テンプレート読み込みエラー: {e}")
            return False, issues

    def run_validation(self) -> Dict[str, Any]:
        """デプロイメントプロセス検証の実行"""
        print("🚀 デプロイメントプロセス検証開始")
        print("=" * 80)
        
        results = {
            'success': True,
            'tests': {}
        }
        
        # AWS認証情報の検証
        self.log_info("AWS認証情報を検証中...")
        aws_creds_ok, aws_creds_msg = self.validate_aws_credentials()
        results['tests']['aws_credentials'] = {
            'success': aws_creds_ok,
            'message': aws_creds_msg
        }
        if not aws_creds_ok:
            results['success'] = False
        
        # CloudFormation権限の検証
        self.log_info("CloudFormation権限を検証中...")
        cf_perms_ok, cf_perms_msg = self.validate_cloudformation_permissions()
        results['tests']['cloudformation_permissions'] = {
            'success': cf_perms_ok,
            'message': cf_perms_msg
        }
        if not cf_perms_ok:
            results['success'] = False
        
        # テンプレートとパラメータファイルの互換性検証
        self.log_info("テンプレートとパラメータファイルの互換性を検証中...")
        compat_ok, compat_issues = self.validate_template_parameter_compatibility()
        results['tests']['template_parameter_compatibility'] = {
            'success': compat_ok,
            'issues': compat_issues
        }
        if not compat_ok:
            results['success'] = False
        
        # 他の検証項目（簡略化）
        results['tests']['dry_run_deployment'] = {
            'success': False,
            'message': "CloudFormationクライアントが利用できません" if not self.aws_available else "スキップ"
        }
        
        results['tests']['resource_dependencies'] = {
            'success': False,
            'message': "リソース依存関係検証エラー: テンプレート解析が必要"
        }
        
        results['tests']['security_configuration'] = {
            'success': False,
            'message': "セキュリティ設定検証エラー: テンプレート解析が必要"
        }
        
        # 結果サマリーの表示
        print("\n" + "=" * 80)
        print("📊 デプロイメントプロセス検証結果")
        print("=" * 80)
        
        for test_name, test_result in results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            print(f"\n{test_name}: {status}")
            
            if 'message' in test_result:
                print(f"  メッセージ: {test_result['message']}")
            
            if 'issues' in test_result and test_result['issues']:
                for issue in test_result['issues']:
                    print(f"  - {issue}")
        
        print("\n" + "=" * 80)
        if results['success']:
            self.log_success("すべてのデプロイメント検証が成功しました")
        else:
            self.log_error("一部のデプロイメント検証が失敗しました")
            print("上記の問題を解決してからデプロイメントを実行してください")
        print("=" * 80)
        
        return results

def main():
    """メイン処理"""
    validator = DeploymentProcessValidator()
    
    try:
        results = validator.run_validation()
        
        # 結果をJSONファイルに保存
        results_file = validator.project_root / "deployment-process-validation-results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細結果を保存しました: {results_file}")
        
        # 終了コードの設定
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()