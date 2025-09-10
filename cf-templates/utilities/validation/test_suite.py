#!/usr/bin/env python3
"""
Automated Test Suite for CloudFormation Templates
CloudFormationテンプレートの自動テストスイート
"""

import unittest
import json
import yaml
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# テスト対象モジュールをインポート
sys.path.append(str(Path(__file__).parent))
from cloudformation_validator import CloudFormationValidator, ValidationIssue
from parameter_validator import ParameterValidator, ParameterValidationResult
from well_architected_validator import WellArchitectedValidator
from validation_orchestrator import ValidationOrchestrator


class TestCloudFormationValidator(unittest.TestCase):
    """CloudFormation検証機能のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.validator = CloudFormationValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_template(self, template_content: Dict[str, Any], filename: str = "test-template.json") -> str:
        """一時テンプレートファイルを作成"""
        template_path = os.path.join(self.temp_dir, filename)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_content, f, indent=2)
        return template_path
    
    def test_valid_template_structure(self):
        """有効なテンプレート構造のテスト"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Test template",
            "Resources": {
                "TestBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": "test-bucket"
                    }
                }
            }
        }
        
        template_path = self.create_temp_template(template)
        is_valid, issues = self.validator.validate_template(template_path)
        
        # 構文エラーがないことを確認
        syntax_errors = [i for i in issues if i.severity == 'error' and i.category == 'syntax']
        self.assertEqual(len(syntax_errors), 0, f"構文エラーが発生: {syntax_errors}")
    
    def test_invalid_template_structure(self):
        """無効なテンプレート構造のテスト"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Test template",
            # Resourcesセクションが欠落
        }
        
        template_path = self.create_temp_template(template)
        is_valid, issues = self.validator.validate_template(template_path)
        
        # エラーが検出されることを確認
        self.assertFalse(is_valid)
        error_messages = [i.message for i in issues if i.severity == 'error']
        self.assertTrue(any("Resources" in msg for msg in error_messages))
    
    def test_parameter_validation(self):
        """パラメータ検証のテスト"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Parameters": {
                "InstanceType": {
                    "Type": "String",
                    "Default": "t3.micro",
                    "AllowedValues": ["t3.micro", "t3.small", "t3.medium"],
                    "Description": "EC2 instance type"
                }
            },
            "Resources": {
                "TestInstance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": {"Ref": "InstanceType"}
                    }
                }
            }
        }
        
        template_path = self.create_temp_template(template)
        
        # 有効なパラメータ値でテスト
        valid_params = {"InstanceType": "t3.small"}
        is_valid, issues = self.validator.validate_template(template_path, valid_params)
        param_errors = [i for i in issues if i.severity == 'error' and 'parameter' in i.message.lower()]
        self.assertEqual(len(param_errors), 0)
        
        # 無効なパラメータ値でテスト
        invalid_params = {"InstanceType": "t3.large"}  # 許可されていない値
        is_valid, issues = self.validator.validate_template(template_path, invalid_params)
        param_errors = [i for i in issues if i.severity == 'error']
        self.assertTrue(len(param_errors) > 0)
    
    def test_security_validation(self):
        """セキュリティ検証のテスト"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "InsecureSecurityGroup": {
                    "Type": "AWS::EC2::SecurityGroup",
                    "Properties": {
                        "GroupDescription": "Insecure security group",
                        "SecurityGroupIngress": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 22,
                                "ToPort": 22,
                                "CidrIp": "0.0.0.0/0"  # セキュリティ問題
                            }
                        ]
                    }
                }
            }
        }
        
        template_path = self.create_temp_template(template)
        is_valid, issues = self.validator.validate_template(template_path)
        
        # セキュリティ警告が検出されることを確認
        security_issues = [i for i in issues if i.category == 'security']
        self.assertTrue(len(security_issues) > 0)
        ssh_warnings = [i for i in security_issues if 'SSH' in i.message or '22' in i.message]
        self.assertTrue(len(ssh_warnings) > 0)


class TestParameterValidator(unittest.TestCase):
    """パラメータ検証機能のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.validator = ParameterValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_file(self, content: Dict[str, Any], filename: str) -> str:
        """一時ファイルを作成"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        return file_path
    
    def test_parameter_type_validation(self):
        """パラメータ型検証のテスト"""
        template = {
            "Parameters": {
                "StringParam": {"Type": "String"},
                "NumberParam": {"Type": "Number"},
                "ListParam": {"Type": "CommaDelimitedList"}
            },
            "Resources": {}
        }
        
        template_path = self.create_temp_file(template, "template.json")
        
        # 正しい型のパラメータ
        valid_params = {
            "StringParam": "test-string",
            "NumberParam": "123",
            "ListParam": ["item1", "item2"]
        }
        
        params_path = self.create_temp_file(valid_params, "params.json")
        is_valid = self.validator.validate_template_parameters(template_path, params_path)
        self.assertTrue(is_valid)
        
        # 間違った型のパラメータ
        invalid_params = {
            "StringParam": 123,  # 数値だが文字列が期待される
            "NumberParam": "not-a-number",  # 文字列だが数値が期待される
            "ListParam": "not-a-list"  # 文字列だがリストが期待される
        }
        
        invalid_params_path = self.create_temp_file(invalid_params, "invalid_params.json")
        is_valid = self.validator.validate_template_parameters(template_path, invalid_params_path)
        self.assertFalse(is_valid)
    
    def test_parameter_constraints(self):
        """パラメータ制約のテスト"""
        template = {
            "Parameters": {
                "RestrictedParam": {
                    "Type": "String",
                    "AllowedValues": ["value1", "value2", "value3"]
                },
                "PatternParam": {
                    "Type": "String",
                    "AllowedPattern": "^[a-zA-Z][a-zA-Z0-9-]*$"
                },
                "LengthParam": {
                    "Type": "String",
                    "MinLength": 5,
                    "MaxLength": 20
                }
            },
            "Resources": {}
        }
        
        template_path = self.create_temp_file(template, "template.json")
        
        # 制約を満たすパラメータ
        valid_params = {
            "RestrictedParam": "value2",
            "PatternParam": "valid-name",
            "LengthParam": "valid-length"
        }
        
        params_path = self.create_temp_file(valid_params, "params.json")
        is_valid = self.validator.validate_template_parameters(template_path, params_path)
        self.assertTrue(is_valid)
        
        # 制約を満たさないパラメータ
        invalid_params = {
            "RestrictedParam": "invalid-value",  # 許可されていない値
            "PatternParam": "123-invalid",  # パターンに一致しない
            "LengthParam": "short"  # 最小長を満たさない
        }
        
        invalid_params_path = self.create_temp_file(invalid_params, "invalid_params.json")
        is_valid = self.validator.validate_template_parameters(template_path, invalid_params_path)
        self.assertFalse(is_valid)
    
    def test_aws_resource_id_validation(self):
        """AWS リソース ID 検証のテスト"""
        template = {
            "Parameters": {
                "VpcId": {"Type": "AWS::EC2::VPC::Id"},
                "SubnetId": {"Type": "AWS::EC2::Subnet::Id"},
                "SecurityGroupId": {"Type": "AWS::EC2::SecurityGroup::Id"}
            },
            "Resources": {}
        }
        
        template_path = self.create_temp_file(template, "template.json")
        
        # 有効なリソース ID
        valid_params = {
            "VpcId": "vpc-12345678",
            "SubnetId": "subnet-12345678",
            "SecurityGroupId": "sg-12345678"
        }
        
        params_path = self.create_temp_file(valid_params, "params.json")
        is_valid = self.validator.validate_template_parameters(template_path, params_path)
        self.assertTrue(is_valid)
        
        # 無効なリソース ID
        invalid_params = {
            "VpcId": "invalid-vpc-id",
            "SubnetId": "subnet-invalid",
            "SecurityGroupId": "sg-"
        }
        
        invalid_params_path = self.create_temp_file(invalid_params, "invalid_params.json")
        is_valid = self.validator.validate_template_parameters(template_path, invalid_params_path)
        self.assertFalse(is_valid)


class TestWellArchitectedValidator(unittest.TestCase):
    """Well-Architected検証機能のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.validator = WellArchitectedValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_template(self, template_content: Dict[str, Any], filename: str = "test-template.json") -> str:
        """一時テンプレートファイルを作成"""
        template_path = os.path.join(self.temp_dir, filename)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_content, f, indent=2)
        return template_path
    
    def test_well_architected_metadata_validation(self):
        """Well-Architectedメタデータ検証のテスト"""
        template_with_metadata = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Metadata": {
                "wellArchitectedCompliance": {
                    "operationalExcellence": ["OPS04-BP01", "OPS04-BP02"],
                    "security": ["SEC01-BP01", "SEC02-BP02"],
                    "reliability": ["REL01-BP04", "REL02-BP01"]
                }
            },
            "Resources": {
                "TestBucket": {
                    "Type": "AWS::S3::Bucket"
                }
            }
        }
        
        template_path = self.create_temp_template(template_with_metadata)
        is_valid, messages = self.validator.validate_cloudformation_template(template_path)
        
        # 準拠項目が検出されることを確認
        compliance_messages = [m for m in messages if m.startswith("✓")]
        self.assertTrue(len(compliance_messages) > 0)
    
    def test_missing_metadata(self):
        """メタデータ欠落のテスト"""
        template_without_metadata = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "TestBucket": {
                    "Type": "AWS::S3::Bucket"
                }
            }
        }
        
        template_path = self.create_temp_template(template_without_metadata)
        is_valid, messages = self.validator.validate_cloudformation_template(template_path)
        
        # 警告が出ることを確認
        warning_messages = [m for m in messages if m.startswith("Warning")]
        self.assertTrue(len(warning_messages) > 0)
        metadata_warnings = [m for m in warning_messages if "compliance" in m.lower()]
        self.assertTrue(len(metadata_warnings) > 0)


class TestValidationOrchestrator(unittest.TestCase):
    """検証オーケストレータのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.orchestrator = ValidationOrchestrator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_template(self, template_content: Dict[str, Any], filename: str = "test-template.json") -> str:
        """一時テンプレートファイルを作成"""
        template_path = os.path.join(self.temp_dir, filename)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_content, f, indent=2)
        return template_path
    
    def test_comprehensive_validation(self):
        """包括的検証のテスト"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Test template for comprehensive validation",
            "Metadata": {
                "wellArchitectedCompliance": {
                    "security": ["SEC01-BP01"]
                }
            },
            "Parameters": {
                "BucketName": {
                    "Type": "String",
                    "Description": "S3 bucket name"
                }
            },
            "Resources": {
                "TestBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": {"Ref": "BucketName"}
                    }
                }
            },
            "Outputs": {
                "BucketName": {
                    "Description": "Name of the created bucket",
                    "Value": {"Ref": "TestBucket"}
                }
            }
        }
        
        parameters = {
            "BucketName": "test-bucket-name"
        }
        
        template_path = self.create_temp_template(template)
        params_path = self.create_temp_template(parameters, "params.json")
        
        summary = self.orchestrator.run_comprehensive_validation(template_path, params_path)
        
        # 検証が実行されることを確認
        self.assertIsNotNone(summary)
        self.assertEqual(summary.template_path, template_path)
        self.assertEqual(summary.parameters_path, params_path)
        
        # 各検証の結果が含まれることを確認
        self.assertIn('status', summary.syntax_validation)
        self.assertIn('status', summary.parameter_validation)
        self.assertIn('status', summary.well_architected_validation)


class TestIntegrationTests(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = Path(__file__).parent.parent.parent
    
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_template_validation(self):
        """実際のテンプレートファイルの検証テスト"""
        # 実際のテンプレートファイルを探す
        template_files = []
        for pattern in ['**/*.json', '**/*.yaml', '**/*.yml']:
            template_files.extend(self.templates_dir.glob(pattern))
        
        # CloudFormationテンプレートらしきファイルをフィルタ
        cf_templates = []
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'AWSTemplateFormatVersion' in content or 'Resources' in content:
                        cf_templates.append(template_file)
            except Exception:
                continue
        
        if not cf_templates:
            self.skipTest("実際のCloudFormationテンプレートが見つかりません")
        
        # 最初のテンプレートで検証テスト
        template_path = str(cf_templates[0])
        validator = CloudFormationValidator()
        
        try:
            is_valid, issues = validator.validate_template(template_path)
            # 検証が実行されることを確認（結果は問わない）
            self.assertIsInstance(is_valid, bool)
            self.assertIsInstance(issues, list)
        except Exception as e:
            self.fail(f"実際のテンプレート検証中にエラー: {e}")


class TestRunner:
    """テスト実行クラス"""
    
    def __init__(self):
        self.test_results = {}
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """単体テストの実行"""
        print("🧪 単体テストを実行中...")
        
        # テストスイートを作成
        test_classes = [
            TestCloudFormationValidator,
            TestParameterValidator,
            TestWellArchitectedValidator,
            TestValidationOrchestrator
        ]
        
        suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # テスト実行
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'failure_details': result.failures,
            'error_details': result.errors
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """統合テストの実行"""
        print("🔗 統合テストを実行中...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegrationTests)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'failure_details': result.failures,
            'error_details': result.errors
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストの実行"""
        print("🚀 自動テストスイートを開始します...")
        print("=" * 80)
        
        # 単体テスト実行
        unit_results = self.run_unit_tests()
        print(f"\n単体テスト結果: {unit_results['tests_run']}件実行, "
              f"{unit_results['failures']}件失敗, {unit_results['errors']}件エラー")
        
        # 統合テスト実行
        integration_results = self.run_integration_tests()
        print(f"\n統合テスト結果: {integration_results['tests_run']}件実行, "
              f"{integration_results['failures']}件失敗, {integration_results['errors']}件エラー")
        
        # 全体結果
        total_tests = unit_results['tests_run'] + integration_results['tests_run']
        total_failures = unit_results['failures'] + integration_results['failures']
        total_errors = unit_results['errors'] + integration_results['errors']
        overall_success = unit_results['success'] and integration_results['success']
        
        print("\n" + "=" * 80)
        print(f"📊 テスト結果サマリー:")
        print(f"   総テスト数: {total_tests}")
        print(f"   失敗: {total_failures}")
        print(f"   エラー: {total_errors}")
        print(f"   成功率: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%" if total_tests > 0 else "N/A")
        
        status = "✅ 成功" if overall_success else "❌ 失敗"
        print(f"   全体結果: {status}")
        
        return {
            'unit_tests': unit_results,
            'integration_tests': integration_results,
            'summary': {
                'total_tests': total_tests,
                'total_failures': total_failures,
                'total_errors': total_errors,
                'overall_success': overall_success
            }
        }
    
    def generate_test_report(self, results: Dict[str, Any], output_path: str = "test-report.txt"):
        """テストレポートの生成"""
        report = []
        report.append("=" * 80)
        report.append("CLOUDFORMATION VALIDATION TEST REPORT")
        report.append("=" * 80)
        report.append(f"実行日時: {__import__('datetime').datetime.now().isoformat()}")
        report.append("")
        
        # サマリー
        summary = results['summary']
        report.append("テスト結果サマリー:")
        report.append(f"  総テスト数: {summary['total_tests']}")
        report.append(f"  失敗: {summary['total_failures']}")
        report.append(f"  エラー: {summary['total_errors']}")
        report.append(f"  成功率: {((summary['total_tests'] - summary['total_failures'] - summary['total_errors']) / summary['total_tests'] * 100):.1f}%" if summary['total_tests'] > 0 else "N/A")
        report.append(f"  全体結果: {'成功' if summary['overall_success'] else '失敗'}")
        report.append("")
        
        # 詳細結果
        for test_type in ['unit_tests', 'integration_tests']:
            test_name = '単体テスト' if test_type == 'unit_tests' else '統合テスト'
            test_results = results[test_type]
            
            report.append(f"{test_name}:")
            report.append(f"  実行数: {test_results['tests_run']}")
            report.append(f"  失敗: {test_results['failures']}")
            report.append(f"  エラー: {test_results['errors']}")
            report.append(f"  結果: {'成功' if test_results['success'] else '失敗'}")
            
            # 失敗詳細
            if test_results['failure_details']:
                report.append("  失敗詳細:")
                for failure in test_results['failure_details']:
                    report.append(f"    - {failure[0]}: {failure[1]}")
            
            # エラー詳細
            if test_results['error_details']:
                report.append("  エラー詳細:")
                for error in test_results['error_details']:
                    report.append(f"    - {error[0]}: {error[1]}")
            
            report.append("")
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"📄 テストレポートを保存しました: {output_path}")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CloudFormation Validation Test Suite')
    parser.add_argument('--unit', action='store_true', help='単体テストのみ実行')
    parser.add_argument('--integration', action='store_true', help='統合テストのみ実行')
    parser.add_argument('--report', '-r', help='テストレポート出力パス')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細出力')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.unit:
        results = {'unit_tests': runner.run_unit_tests(), 'integration_tests': {'tests_run': 0, 'failures': 0, 'errors': 0, 'success': True}}
        results['summary'] = {
            'total_tests': results['unit_tests']['tests_run'],
            'total_failures': results['unit_tests']['failures'],
            'total_errors': results['unit_tests']['errors'],
            'overall_success': results['unit_tests']['success']
        }
    elif args.integration:
        results = {'unit_tests': {'tests_run': 0, 'failures': 0, 'errors': 0, 'success': True}, 'integration_tests': runner.run_integration_tests()}
        results['summary'] = {
            'total_tests': results['integration_tests']['tests_run'],
            'total_failures': results['integration_tests']['failures'],
            'total_errors': results['integration_tests']['errors'],
            'overall_success': results['integration_tests']['success']
        }
    else:
        results = runner.run_all_tests()
    
    # レポート生成
    if args.report:
        runner.generate_test_report(results, args.report)
    
    # 終了コード
    sys.exit(0 if results['summary']['overall_success'] else 1)


if __name__ == "__main__":
    main()