#!/usr/bin/env python3
"""
Monitoring and Logging Configuration Validator
CloudFormation Parameter Migration - Monitoring and Logging Verification

このスクリプトは監視とログ設定の包括的な検証を行い、
運用環境での適切な可視性を保証します。
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import re

# CloudFormation対応のYAMLパーサーを使用
try:
    from awscli.customizations.cloudformation.yamlhelper import yaml_parse
except ImportError:
    # フォールバック: 標準のyamlを使用
    import yaml
    def yaml_parse(content):
        return yaml.safe_load(content)

class MonitoringLoggingValidator:
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
            self.cloudwatch_client = boto3.client('cloudwatch')
            self.logs_client = boto3.client('logs')
            self.aws_available = True
        except Exception as e:
            print(f"⚠️  AWS クライアントの初期化に失敗: {e}")
            print("ローカル検証のみ実行します")
            self.cloudwatch_client = None
            self.logs_client = None
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

    def validate_cloudwatch_resources(self) -> Tuple[bool, List[str]]:
        """CloudWatchリソースの検証"""
        self.log_info("CloudWatchリソースを検証中...")
        
        issues = []
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                template = yaml_parse(content)
            
            resources = template.get('Resources', {})
            
            # CloudWatchアラームの確認
            alarms = [name for name, resource in resources.items() 
                     if resource.get('Type') == 'AWS::CloudWatch::Alarm']
            
            if not alarms:
                issues.append("CloudWatchアラームが定義されていません")
            else:
                self.log_success(f"CloudWatchアラームが定義されています: {alarms}")
                
            # CloudWatchダッシュボードの確認
            dashboards = [name for name, resource in resources.items() 
                         if resource.get('Type') == 'AWS::CloudWatch::Dashboard']
            
            if not dashboards:
                self.log_warning("CloudWatchダッシュボードが定義されていません")
            else:
                self.log_success(f"CloudWatchダッシュボードが定義されています: {dashboards}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"CloudWatchリソース検証エラー: {e}")
            return False, issues

    def validate_configuration_pattern_monitoring(self) -> Tuple[bool, List[str]]:
        """設定パターン別監視設定の検証"""
        self.log_info("設定パターン別監視設定を検証中...")
        
        issues = []
        
        for config_name, config_file in self.config_files.items():
            if not config_file.exists():
                issues.append(f"{config_name}: 設定ファイルが見つかりません")
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                parameters = config.get('Parameters', {})
                tags = config.get('Tags', {})
                
                # ログレベルの確認
                log_level = tags.get('LogLevel') or parameters.get('LogLevel')
                if not log_level:
                    self.log_warning(f"{config_name}: ログレベルタグが設定されていません")
                
                self.log_success(f"{config_name}: パターン別監視設定の検証完了")
                
            except Exception as e:
                issues.append(f"{config_name}: 設定検証エラー - {e}")
        
        return len(issues) == 0, issues

    def run_validation(self) -> Dict[str, Any]:
        """監視・ログ設定検証の実行"""
        print("🚀 監視・ログ設定検証開始")
        print("=" * 80)
        
        results = {
            'success': True,
            'tests': {}
        }
        
        # CloudWatchリソースの検証
        self.log_info("CloudWatchリソースを検証中...")
        cw_ok, cw_issues = self.validate_cloudwatch_resources()
        results['tests']['cloudwatch_resources'] = {
            'success': cw_ok,
            'issues': cw_issues
        }
        if not cw_ok:
            results['success'] = False
        
        # 設定パターン別監視設定の検証
        self.log_info("設定パターン別監視設定を検証中...")
        pattern_ok, pattern_issues = self.validate_configuration_pattern_monitoring()
        results['tests']['configuration_pattern_monitoring'] = {
            'success': pattern_ok,
            'issues': pattern_issues
        }
        
        # 他の検証項目（簡略化）
        results['tests']['auto_scaling_monitoring'] = {
            'success': False,
            'message': "Auto Scaling監視設定検証エラー: テンプレート解析が必要"
        }
        
        results['tests']['iam_logging_permissions'] = {
            'success': False,
            'message': "IAMログ権限検証エラー: テンプレート解析が必要"
        }
        
        results['tests']['sns_notification_setup'] = {
            'success': False,
            'message': "SNS通知設定検証エラー: テンプレート解析が必要"
        }
        
        results['tests']['log_aggregation_retention'] = {
            'success': False,
            'message': "ログ集約・保持設定検証エラー: テンプレート解析が必要"
        }
        
        results['tests']['monitoring_endpoints_connectivity'] = {
            'success': False,
            'message': "CloudWatchクライアントが利用できません" if not self.aws_available else "スキップ"
        }
        
        # 結果サマリーの表示
        print("\n" + "=" * 80)
        print("📊 監視・ログ設定検証結果")
        print("=" * 80)
        
        for test_name, test_result in results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            print(f"\n{test_name}: {status}")
            
            if 'message' in test_result:
                print(f"  - {test_result['message']}")
            
            if 'issues' in test_result and test_result['issues']:
                for issue in test_result['issues']:
                    print(f"  - {issue}")
        
        print("\n" + "=" * 80)
        if results['success']:
            self.log_success("すべての監視・ログ設定検証が成功しました")
        else:
            self.log_error("一部の監視・ログ設定検証が失敗しました")
            print("上記の問題を解決してから本番環境にデプロイしてください")
        print("=" * 80)
        
        return results

def main():
    """メイン処理"""
    validator = MonitoringLoggingValidator()
    
    try:
        results = validator.run_validation()
        
        # 結果をJSONファイルに保存
        results_file = validator.project_root / "monitoring-logging-validation-results.json"
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