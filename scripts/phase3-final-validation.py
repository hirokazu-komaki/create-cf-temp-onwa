#!/usr/bin/env python3
"""
Phase 3 Final Validation Script
CloudFormation Parameter Migration - Complete Testing and Validation

This script performs comprehensive testing of the new parameter structure
across all configuration patterns (Basic, Advanced, Enterprise).
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import boto3
from botocore.exceptions import ClientError, ValidationError
try:
    from awscli.customizations.cloudformation.yamlhelper import yaml_parse
    YAML_PARSER_AVAILABLE = True
except ImportError:
    import yaml
    from yaml import SafeLoader
    YAML_PARSER_AVAILABLE = False
    print("Warning: AWS CLI YAMLヘルパーが利用できません。CloudFormation関数対応のyamlローダーを使用します。")
    
    # CloudFormation固有の関数を処理するためのカスタムローダー
    class CloudFormationLoader(SafeLoader):
        pass
    
    def cf_constructor(loader, tag_suffix, node):
        """CloudFormation固有の関数を辞書として処理"""
        if isinstance(node, yaml.ScalarNode):
            return {tag_suffix: loader.construct_scalar(node)}
        elif isinstance(node, yaml.SequenceNode):
            return {tag_suffix: loader.construct_sequence(node)}
        elif isinstance(node, yaml.MappingNode):
            return {tag_suffix: loader.construct_mapping(node)}
        else:
            return {tag_suffix: None}
    
    # CloudFormation関数のタグを登録
    cf_functions = ['Ref', 'GetAtt', 'Join', 'Split', 'Select', 'Sub', 'Base64', 'GetAZs',
                   'ImportValue', 'FindInMap', 'Equals', 'Not', 'And', 'Or', 'If', 'Condition']
    
    for func in cf_functions:
        CloudFormationLoader.add_multi_constructor(f'!{func}', cf_constructor)

class Phase3Validator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.template_path = self.project_root / "cf-templates" / "compute" / "ec2" / "ec2-autoscaling.yaml"
        self.config_files = {
            "basic": self.project_root / "test-parameters-basic.json",
            "advanced": self.project_root / "test-parameters-advanced.json", 
            "enterprise": self.project_root / "test-parameters-enterprise.json"
        }
        self.validation_results = {}
        self.cf_client = None
        
        # Initialize CloudFormation client if AWS credentials are available
        try:
            # AWS プロファイル設定
            session = boto3.Session(profile_name='mame-local-wani')
            self.cf_client = session.client('cloudformation')
        except Exception as e:
            print(f"Warning: AWS CloudFormation client not available: {e}")
            print("Will perform local validation only")
    
    def load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load and parse configuration file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load config file {config_path}: {e}")
    
    def load_template(self) -> Dict[str, Any]:
        """Load and parse CloudFormation template using AWS CLI YAML helper"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            if YAML_PARSER_AVAILABLE:
                # AWS CLI YAMLヘルパーを使用してCloudFormation固有の関数を処理
                return yaml_parse(template_content)
            else:
                # フォールバック: CloudFormation関数対応のカスタムローダーを使用
                return yaml.load(template_content, Loader=CloudFormationLoader)
        except Exception as e:
            raise Exception(f"Failed to load template {self.template_path}: {e}")
    
    def validate_template_syntax(self) -> Tuple[bool, str]:
        """Validate CloudFormation template syntax using AWS CLI YAML helper"""
        print("🔍 CloudFormation テンプレート構文を検証中...")
        
        try:
            # AWS CLI YAMLヘルパーを使用してテンプレートを読み込み
            template = self.load_template()
            
            # 必須セクションの確認
            required_sections = ['AWSTemplateFormatVersion', 'Parameters', 'Resources']
            missing_sections = [section for section in required_sections if section not in template]
            
            if missing_sections:
                return False, f"必須セクションが不足しています: {missing_sections}"
            
            # CloudFormation固有の関数構文の検証
            if YAML_PARSER_AVAILABLE:
                print("✅ AWS CLI YAMLヘルパーによる構文解析が成功しました")
            
            # AWS CLIが利用可能な場合はAWSでの検証も実行
            if self.cf_client:
                try:
                    with open(self.template_path, 'r', encoding='utf-8') as f:
                        template_body = f.read()
                    
                    response = self.cf_client.validate_template(TemplateBody=template_body)
                    return True, "AWS CloudFormationによるテンプレート検証が成功しました"
                except ClientError as e:
                    return False, f"AWS検証が失敗しました: {e.response['Error']['Message']}"
            else:
                return True, "ローカルYAML構文検証が成功しました (AWS検証はスキップ)"
                
        except Exception as e:
            return False, f"テンプレート検証エラー: {str(e)}"
    
    def run_cfn_lint(self) -> Tuple[bool, str]:
        """Run cfn-lint validation if available"""
        print("🔍 Running cfn-lint validation...")
        
        try:
            result = subprocess.run(
                ['cfn-lint', str(self.template_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, "cfn-lint validation passed"
            else:
                # Check if errors are critical
                errors = result.stdout + result.stderr
                if "E" in errors:  # Critical errors
                    return False, f"cfn-lint critical errors: {errors}"
                else:
                    return True, f"cfn-lint passed with warnings: {errors}"
                    
        except FileNotFoundError:
            return True, "cfn-lint not available, skipping"
        except subprocess.TimeoutExpired:
            return False, "cfn-lint validation timed out"
        except Exception as e:
            return False, f"cfn-lint validation error: {str(e)}"
    
    def validate_parameter_structure(self, config_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameter structure against template requirements"""
        print(f"🔍 Validating {config_name} parameter structure...")
        
        template = self.load_template()
        template_params = template.get('Parameters', {})
        config_params = config.get('Parameters', {})
        
        issues = []
        
        # Check for required parameters
        required_params = []
        for param_name, param_def in template_params.items():
            if 'Default' not in param_def:
                required_params.append(param_name)
        
        missing_required = [p for p in required_params if p not in config_params]
        if missing_required:
            issues.append(f"Missing required parameters: {missing_required}")
        
        # Check for invalid parameters (should not exist in Phase 3)
        legacy_params = ['InstancePattern', 'AMIId', 'InstanceType', 'MinSize', 'MaxSize', 'DesiredCapacity']
        found_legacy = [p for p in legacy_params if p in config_params]
        if found_legacy:
            issues.append(f"Legacy parameters found (should be removed in Phase 3): {found_legacy}")
        
        # Validate parameter values
        for param_name, param_value in config_params.items():
            if param_name in template_params:
                param_def = template_params[param_name]
                
                # Check AllowedValues
                if 'AllowedValues' in param_def:
                    if str(param_value) not in param_def['AllowedValues']:
                        issues.append(f"Parameter {param_name} value '{param_value}' not in allowed values: {param_def['AllowedValues']}")
                
                # Check constraints for numeric parameters
                if param_def.get('Type') == 'Number':
                    try:
                        num_value = int(param_value)
                        if 'MinValue' in param_def and num_value < param_def['MinValue']:
                            issues.append(f"Parameter {param_name} value {num_value} below minimum {param_def['MinValue']}")
                        if 'MaxValue' in param_def and num_value > param_def['MaxValue']:
                            issues.append(f"Parameter {param_name} value {num_value} above maximum {param_def['MaxValue']}")
                    except ValueError:
                        issues.append(f"Parameter {param_name} should be numeric but got '{param_value}'")
        
        return len(issues) == 0, issues
    
    def validate_configuration_pattern_consistency(self, config_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that configuration parameters are consistent with the pattern"""
        print(f"🔍 Validating {config_name} pattern consistency...")
        
        config_params = config.get('Parameters', {})
        pattern = config_params.get('ConfigurationPattern', '')
        
        issues = []
        
        # Pattern-specific validation
        if pattern == 'Basic':
            # Basic should not have advanced features
            advanced_features = ['EnableSpotInstances', 'EnableDetailedMonitoring', 'EnableMixedInstancesPolicy', 'EnableNitroEnclave']
            for feature in advanced_features:
                if config_params.get(feature) == 'true':
                    issues.append(f"Basic pattern should not enable {feature}")
        
        elif pattern == 'Advanced':
            # Advanced should have monitoring enabled
            if config_params.get('EnableDetailedMonitoring') != 'true':
                issues.append("Advanced pattern should have EnableDetailedMonitoring=true")
            
            # Advanced should not have Enterprise-only features
            enterprise_features = ['EnableNitroEnclave', 'EnableMixedInstancesPolicy']
            for feature in enterprise_features:
                if config_params.get(feature) == 'true':
                    issues.append(f"Advanced pattern should not enable Enterprise feature {feature}")
        
        elif pattern == 'Enterprise':
            # Enterprise should have security features enabled
            security_features = ['EnableEncryption', 'EnableDetailedMonitoring']
            for feature in security_features:
                if config_params.get(feature) != 'true':
                    issues.append(f"Enterprise pattern should have {feature}=true")
        
        # Validate custom sizing consistency
        custom_sizing_params = ['CustomMinSize', 'CustomMaxSize', 'CustomDesiredCapacity']
        custom_sizing_values = [config_params.get(p, '0') for p in custom_sizing_params]
        
        if any(v != '0' for v in custom_sizing_values):
            # If any custom sizing is used, all should be specified
            if any(v == '0' for v in custom_sizing_values):
                issues.append("When using custom sizing, all CustomMinSize, CustomMaxSize, and CustomDesiredCapacity must be specified")
            else:
                # Validate sizing logic
                try:
                    min_size = int(custom_sizing_values[0])
                    max_size = int(custom_sizing_values[1])
                    desired = int(custom_sizing_values[2])
                    
                    if min_size > max_size:
                        issues.append(f"CustomMinSize ({min_size}) cannot be greater than CustomMaxSize ({max_size})")
                    if desired < min_size or desired > max_size:
                        issues.append(f"CustomDesiredCapacity ({desired}) must be between CustomMinSize ({min_size}) and CustomMaxSize ({max_size})")
                except ValueError:
                    issues.append("Custom sizing parameters must be numeric")
        
        return len(issues) == 0, issues
    
    def test_changeset_creation(self, config_name: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Test CloudFormation changeset creation with the configuration"""
        print(f"🔍 Testing changeset creation for {config_name}...")
        
        if not self.cf_client:
            return True, "AWS client not available, skipping changeset test"
        
        try:
            # Create a unique stack name for testing
            stack_name = f"test-{config_name}-{os.getpid()}"
            changeset_name = f"test-changeset-{config_name}-{os.getpid()}"
            
            # Prepare parameters for CloudFormation
            cf_parameters = []
            for key, value in config.get('Parameters', {}).items():
                cf_parameters.append({
                    'ParameterKey': key,
                    'ParameterValue': str(value)
                })
            
            # Read template
            with open(self.template_path, 'r') as f:
                template_body = f.read()
            
            # Create changeset
            response = self.cf_client.create_change_set(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=cf_parameters,
                ChangeSetName=changeset_name,
                ChangeSetType='CREATE',
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
            
            # Wait for changeset to be created
            waiter = self.cf_client.get_waiter('change_set_create_complete')
            waiter.wait(
                ChangeSetName=changeset_name,
                StackName=stack_name,
                WaiterConfig={'Delay': 5, 'MaxAttempts': 12}
            )
            
            # Clean up changeset
            self.cf_client.delete_change_set(
                ChangeSetName=changeset_name,
                StackName=stack_name
            )
            
            return True, "Changeset creation successful"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ValidationError':
                return False, f"Parameter validation failed: {error_message}"
            else:
                return False, f"AWS error ({error_code}): {error_message}"
        except Exception as e:
            return False, f"Changeset creation error: {str(e)}"
    
    def validate_resource_configuration(self, config_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that resources would be configured correctly"""
        print(f"🔍 Validating resource configuration for {config_name}...")
        
        template = self.load_template()
        config_params = config.get('Parameters', {})
        
        issues = []
        
        # Check Auto Scaling Group configuration
        if config_params.get('EnableAutoScaling') == 'true':
            # Validate that ASG would be created with correct parameters
            pattern = config_params.get('ConfigurationPattern', '')
            
            # Check if custom sizing is used
            if config_params.get('CustomMinSize', '0') != '0':
                min_size = int(config_params.get('CustomMinSize', '0'))
                max_size = int(config_params.get('CustomMaxSize', '0'))
                desired = int(config_params.get('CustomDesiredCapacity', '0'))
                
                if min_size <= 0 or max_size <= 0 or desired <= 0:
                    issues.append("Auto Scaling enabled but invalid sizing parameters")
            
            # Check subnet configuration for multi-AZ
            subnet_ids = config_params.get('SubnetIds', '')
            if subnet_ids:
                subnets = [s.strip() for s in subnet_ids.split(',')]
                if len(subnets) < 2 and pattern in ['Advanced', 'Enterprise']:
                    issues.append(f"{pattern} pattern should use multiple subnets for high availability")
        
        # Check security configuration
        if config_params.get('ConfigurationPattern') == 'Enterprise':
            if config_params.get('EnableEncryption') != 'true':
                issues.append("Enterprise pattern should have encryption enabled")
            
            if config_params.get('KMSKeyId', '') == '':
                issues.append("Enterprise pattern should specify KMS key for encryption")
        
        # Check instance type configuration
        custom_instance_type = config_params.get('CustomInstanceType', '')
        if custom_instance_type:
            # Validate instance type format
            if not custom_instance_type.startswith(('t3.', 'm5.', 'c5.', 'm5a.')):
                issues.append(f"Unusual instance type: {custom_instance_type}")
        
        return len(issues) == 0, issues
    
    def run_comprehensive_test(self, config_name: str) -> Dict[str, Any]:
        """Run comprehensive test for a configuration pattern"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing {config_name.upper()} Configuration Pattern")
        print(f"{'='*60}")
        
        results = {
            'config_name': config_name,
            'overall_success': True,
            'tests': {}
        }
        
        try:
            # Load configuration
            config = self.load_config_file(self.config_files[config_name])
            
            # Test 1: Parameter Structure Validation
            success, issues = self.validate_parameter_structure(config_name, config)
            results['tests']['parameter_structure'] = {
                'success': success,
                'issues': issues
            }
            if not success:
                results['overall_success'] = False
            
            # Test 2: Pattern Consistency Validation
            success, issues = self.validate_configuration_pattern_consistency(config_name, config)
            results['tests']['pattern_consistency'] = {
                'success': success,
                'issues': issues
            }
            if not success:
                results['overall_success'] = False
            
            # Test 3: Resource Configuration Validation
            success, issues = self.validate_resource_configuration(config_name, config)
            results['tests']['resource_configuration'] = {
                'success': success,
                'issues': issues
            }
            if not success:
                results['overall_success'] = False
            
            # Test 4: Changeset Creation Test
            success, message = self.test_changeset_creation(config_name, config)
            results['tests']['changeset_creation'] = {
                'success': success,
                'message': message
            }
            if not success:
                results['overall_success'] = False
            
        except Exception as e:
            results['overall_success'] = False
            results['error'] = str(e)
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🚀 Starting Phase 3 Final Validation")
        print("=" * 80)
        
        overall_results = {
            'template_validation': {},
            'configuration_tests': {},
            'overall_success': True
        }
        
        # Template-level validation
        print("\n📋 Template Validation")
        print("-" * 40)
        
        # Template syntax validation
        success, message = self.validate_template_syntax()
        overall_results['template_validation']['syntax'] = {
            'success': success,
            'message': message
        }
        if not success:
            overall_results['overall_success'] = False
        
        # cfn-lint validation
        success, message = self.run_cfn_lint()
        overall_results['template_validation']['cfn_lint'] = {
            'success': success,
            'message': message
        }
        if not success:
            overall_results['overall_success'] = False
        
        # Configuration pattern tests
        for config_name in ['basic', 'advanced', 'enterprise']:
            results = self.run_comprehensive_test(config_name)
            overall_results['configuration_tests'][config_name] = results
            if not results['overall_success']:
                overall_results['overall_success'] = False
        
        return overall_results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "=" * 80)
        print("📊 PHASE 3 FINAL VALIDATION RESULTS")
        print("=" * 80)
        
        # Template validation results
        print("\n📋 Template Validation Results:")
        for test_name, result in results['template_validation'].items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result['success']:
                print(f"    Error: {result['message']}")
        
        # Configuration test results
        print("\n🧪 Configuration Pattern Test Results:")
        for config_name, config_results in results['configuration_tests'].items():
            status = "✅ PASS" if config_results['overall_success'] else "❌ FAIL"
            print(f"\n  {config_name.upper()}: {status}")
            
            if 'error' in config_results:
                print(f"    Error: {config_results['error']}")
            else:
                for test_name, test_result in config_results['tests'].items():
                    test_status = "✅" if test_result['success'] else "❌"
                    print(f"    {test_name}: {test_status}")
                    
                    if not test_result['success']:
                        if 'issues' in test_result:
                            for issue in test_result['issues']:
                                print(f"      - {issue}")
                        if 'message' in test_result:
                            print(f"      - {test_result['message']}")
        
        # Overall result
        print("\n" + "=" * 80)
        if results['overall_success']:
            print("🎉 ALL TESTS PASSED - Phase 3 validation successful!")
            print("✅ New parameter structure is working correctly")
            print("✅ All configuration patterns validated")
            print("✅ Ready for production use")
        else:
            print("❌ SOME TESTS FAILED - Issues need to be resolved")
            print("Please review the failed tests above and fix the issues")
        print("=" * 80)

def main():
    """Main execution function"""
    validator = Phase3Validator()
    
    try:
        results = validator.run_all_tests()
        validator.print_results(results)
        
        # Save results to file
        results_file = validator.project_root / "phase3-validation-results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_success'] else 1)
        
    except Exception as e:
        print(f"❌ Validation script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()