#!/usr/bin/env python3
"""
Parameter Validation Utility
CloudFormationテンプレートのパラメータ値検証とJSON設定ファイル検証
"""

import json
import yaml
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import jsonschema
from jsonschema import validate, ValidationError


@dataclass
class ParameterValidationResult:
    """パラメータ検証結果"""
    parameter_name: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    value: Any
    expected_type: str


class ParameterValidator:
    """パラメータ検証クラス"""
    
    def __init__(self):
        self.validation_results: List[ParameterValidationResult] = []
    
    def load_template(self, template_path: str) -> Optional[Dict[str, Any]]:
        """テンプレートファイルを読み込み"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                if template_path.endswith('.json'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"テンプレート読み込みエラー: {e}")
            return None
    
    def load_parameters(self, parameters_path: str) -> Optional[Dict[str, Any]]:
        """パラメータファイルを読み込み"""
        try:
            with open(parameters_path, 'r', encoding='utf-8') as f:
                if parameters_path.endswith('.json'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"パラメータファイル読み込みエラー: {e}")
            return None
    
    def validate_parameter_type(self, param_name: str, param_value: Any, param_config: Dict[str, Any]) -> ParameterValidationResult:
        """パラメータの型検証"""
        param_type = param_config.get('Type', 'String')
        errors = []
        warnings = []
        is_valid = True
        
        # 型チェック
        if param_type == 'String':
            if not isinstance(param_value, str):
                errors.append(f"文字列型が期待されますが、{type(param_value).__name__}型です")
                is_valid = False
        
        elif param_type == 'Number':
            try:
                float(param_value)
            except (ValueError, TypeError):
                errors.append(f"数値型が期待されますが、変換できません: {param_value}")
                is_valid = False
        
        elif param_type == 'CommaDelimitedList':
            if isinstance(param_value, str):
                # カンマ区切り文字列の場合
                if not param_value.strip():
                    warnings.append("空のカンマ区切りリストです")
            elif isinstance(param_value, list):
                # リスト形式の場合（JSON設定で一般的）
                if not param_value:
                    warnings.append("空のリストです")
            else:
                errors.append(f"カンマ区切りリストまたは配列が期待されますが、{type(param_value).__name__}型です")
                is_valid = False
        
        elif param_type.startswith('AWS::'):
            # AWS固有の型（例：AWS::EC2::Instance::Id）
            if not isinstance(param_value, str):
                errors.append(f"AWS リソース ID（文字列）が期待されますが、{type(param_value).__name__}型です")
                is_valid = False
            elif not param_value.strip():
                errors.append("AWS リソース ID が空です")
                is_valid = False
        
        elif param_type.startswith('List<'):
            # リスト型（例：List<AWS::EC2::Subnet::Id>）
            if not isinstance(param_value, list):
                errors.append(f"リスト型が期待されますが、{type(param_value).__name__}型です")
                is_valid = False
            elif not param_value:
                warnings.append("空のリストです")
        
        return ParameterValidationResult(
            parameter_name=param_name,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            value=param_value,
            expected_type=param_type
        )
    
    def validate_parameter_constraints(self, param_name: str, param_value: Any, param_config: Dict[str, Any]) -> List[str]:
        """パラメータ制約の検証"""
        errors = []
        
        # 許可値チェック
        allowed_values = param_config.get('AllowedValues', [])
        if allowed_values and param_value not in allowed_values:
            errors.append(f"許可されていない値です: {param_value}. 許可値: {', '.join(map(str, allowed_values))}")
        
        # パターンチェック
        allowed_pattern = param_config.get('AllowedPattern')
        if allowed_pattern and isinstance(param_value, str):
            try:
                if not re.match(allowed_pattern, param_value):
                    errors.append(f"パターンに一致しません: {param_value}. パターン: {allowed_pattern}")
            except re.error as e:
                errors.append(f"正規表現パターンが無効です: {allowed_pattern}. エラー: {e}")
        
        # 長さチェック
        if isinstance(param_value, str):
            min_length = param_config.get('MinLength')
            max_length = param_config.get('MaxLength')
            
            if min_length is not None and len(param_value) < min_length:
                errors.append(f"最小長制約違反: {len(param_value)} < {min_length}")
            
            if max_length is not None and len(param_value) > max_length:
                errors.append(f"最大長制約違反: {len(param_value)} > {max_length}")
        
        # 数値範囲チェック
        param_type = param_config.get('Type', 'String')
        if param_type == 'Number':
            try:
                numeric_value = float(param_value)
                min_value = param_config.get('MinValue')
                max_value = param_config.get('MaxValue')
                
                if min_value is not None and numeric_value < min_value:
                    errors.append(f"最小値制約違反: {numeric_value} < {min_value}")
                
                if max_value is not None and numeric_value > max_value:
                    errors.append(f"最大値制約違反: {numeric_value} > {max_value}")
            
            except (ValueError, TypeError):
                # 型チェックで既にエラーが報告されているはず
                pass
        
        return errors
    
    def validate_aws_resource_ids(self, param_name: str, param_value: Any, param_type: str) -> List[str]:
        """AWS リソース ID の形式検証"""
        errors = []
        
        if not isinstance(param_value, str):
            return errors  # 型チェックで既にエラーが報告されているはず
        
        # VPC ID
        if param_type == 'AWS::EC2::VPC::Id':
            if not re.match(r'^vpc-[0-9a-f]{8,17}$', param_value):
                errors.append(f"VPC ID の形式が無効です: {param_value}")
        
        # Subnet ID
        elif param_type == 'AWS::EC2::Subnet::Id':
            if not re.match(r'^subnet-[0-9a-f]{8,17}$', param_value):
                errors.append(f"Subnet ID の形式が無効です: {param_value}")
        
        # Security Group ID
        elif param_type == 'AWS::EC2::SecurityGroup::Id':
            if not re.match(r'^sg-[0-9a-f]{8,17}$', param_value):
                errors.append(f"Security Group ID の形式が無効です: {param_value}")
        
        # Instance ID
        elif param_type == 'AWS::EC2::Instance::Id':
            if not re.match(r'^i-[0-9a-f]{8,17}$', param_value):
                errors.append(f"Instance ID の形式が無効です: {param_value}")
        
        # Key Pair Name
        elif param_type == 'AWS::EC2::KeyPair::KeyName':
            if not re.match(r'^[a-zA-Z0-9\-_]{1,255}$', param_value):
                errors.append(f"Key Pair 名の形式が無効です: {param_value}")
        
        # AMI ID
        elif param_type == 'AWS::EC2::Image::Id':
            if not re.match(r'^ami-[0-9a-f]{8,17}$', param_value):
                errors.append(f"AMI ID の形式が無効です: {param_value}")
        
        return errors
    
    def validate_parameters(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> List[ParameterValidationResult]:
        """全パラメータの検証"""
        results = []
        template_params = template.get('Parameters', {})
        
        # 提供されたパラメータの検証
        for param_name, param_value in parameters.items():
            if param_name not in template_params:
                result = ParameterValidationResult(
                    parameter_name=param_name,
                    is_valid=False,
                    errors=[f"テンプレートに定義されていないパラメータです"],
                    warnings=[],
                    value=param_value,
                    expected_type="Unknown"
                )
                results.append(result)
                continue
            
            param_config = template_params[param_name]
            
            # 型検証
            result = self.validate_parameter_type(param_name, param_value, param_config)
            
            # 制約検証
            constraint_errors = self.validate_parameter_constraints(param_name, param_value, param_config)
            result.errors.extend(constraint_errors)
            
            # AWS リソース ID 検証
            param_type = param_config.get('Type', 'String')
            if param_type.startswith('AWS::'):
                aws_errors = self.validate_aws_resource_ids(param_name, param_value, param_type)
                result.errors.extend(aws_errors)
            
            # エラーがある場合は無効とマーク
            if result.errors:
                result.is_valid = False
            
            results.append(result)
        
        # 必須パラメータのチェック
        for param_name, param_config in template_params.items():
            if 'Default' not in param_config and param_name not in parameters:
                result = ParameterValidationResult(
                    parameter_name=param_name,
                    is_valid=False,
                    errors=[f"必須パラメータが指定されていません"],
                    warnings=[],
                    value=None,
                    expected_type=param_config.get('Type', 'String')
                )
                results.append(result)
        
        return results
    
    def validate_json_config_schema(self, config: Dict[str, Any], schema_path: Optional[str] = None) -> List[str]:
        """JSON設定ファイルのスキーマ検証"""
        errors = []
        
        if schema_path is None:
            # デフォルトスキーマパスを設定
            current_dir = Path(__file__).parent
            schema_path = current_dir.parent.parent / "configurations" / "schemas" / "config-schema.json"
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            validate(instance=config, schema=schema)
            
        except FileNotFoundError:
            errors.append(f"スキーマファイルが見つかりません: {schema_path}")
        except ValidationError as e:
            errors.append(f"スキーマ検証エラー: {e.message}")
        except Exception as e:
            errors.append(f"スキーマ検証中にエラー: {str(e)}")
        
        return errors
    
    def validate_config_consistency(self, config: Dict[str, Any]) -> List[str]:
        """設定の一貫性チェック"""
        errors = []
        
        # プロジェクト設定の確認
        project_config = config.get('projectConfig', {})
        if not project_config.get('projectName'):
            errors.append("プロジェクト名が指定されていません")
        
        if not project_config.get('environment'):
            errors.append("環境が指定されていません")
        
        # サービス設定の確認
        service_configs = config.get('serviceConfigs', {})
        
        # VPC設定の確認
        vpc_config = service_configs.get('vpc', {})
        if vpc_config:
            cidr_block = vpc_config.get('cidrBlock')
            if cidr_block:
                # CIDR形式の確認
                if not re.match(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$', cidr_block):
                    errors.append(f"VPC CIDR ブロックの形式が無効です: {cidr_block}")
        
        # EC2設定の確認
        ec2_config = service_configs.get('ec2', {})
        if ec2_config:
            instance_type = ec2_config.get('instanceType')
            if instance_type:
                # インスタンスタイプの形式確認
                if not re.match(r'^[a-z0-9]+\.[a-z0-9]+$', instance_type):
                    errors.append(f"EC2 インスタンスタイプの形式が無効です: {instance_type}")
        
        return errors
    
    def generate_validation_report(self, results: List[ParameterValidationResult], config_errors: List[str] = None) -> str:
        """検証レポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("Parameter Validation Report")
        report.append("=" * 80)
        report.append("")
        
        # サマリー
        total_params = len(results)
        valid_params = sum(1 for r in results if r.is_valid)
        invalid_params = total_params - valid_params
        
        report.append(f"Total Parameters: {total_params}")
        report.append(f"Valid Parameters: {valid_params}")
        report.append(f"Invalid Parameters: {invalid_params}")
        
        if config_errors:
            report.append(f"Configuration Errors: {len(config_errors)}")
        
        report.append("")
        
        # 設定エラー
        if config_errors:
            report.append("CONFIGURATION ERRORS:")
            for error in config_errors:
                report.append(f"  ✗ {error}")
            report.append("")
        
        # パラメータ詳細
        if results:
            report.append("PARAMETER VALIDATION DETAILS:")
            for result in results:
                status = "✓ VALID" if result.is_valid else "✗ INVALID"
                report.append(f"  {result.parameter_name} ({result.expected_type}): {status}")
                
                if result.errors:
                    for error in result.errors:
                        report.append(f"    Error: {error}")
                
                if result.warnings:
                    for warning in result.warnings:
                        report.append(f"    Warning: {warning}")
                
                if result.value is not None:
                    report.append(f"    Value: {result.value}")
                
                report.append("")
        
        return "\n".join(report)
    
    def validate_template_parameters(self, template_path: str, parameters_path: str, schema_path: Optional[str] = None) -> bool:
        """テンプレートとパラメータの包括的検証"""
        # テンプレート読み込み
        template = self.load_template(template_path)
        if not template:
            return False
        
        # パラメータ読み込み
        parameters = self.load_parameters(parameters_path)
        if not parameters:
            return False
        
        # スキーマ検証
        config_errors = []
        if schema_path or Path(parameters_path).suffix == '.json':
            config_errors = self.validate_json_config_schema(parameters, schema_path)
        
        # 一貫性チェック
        consistency_errors = self.validate_config_consistency(parameters)
        config_errors.extend(consistency_errors)
        
        # パラメータ検証
        param_values = parameters.get('serviceConfigs', parameters)  # JSON設定の場合はserviceConfigsを使用
        results = self.validate_parameters(template, param_values)
        
        # レポート生成
        report = self.generate_validation_report(results, config_errors)
        print(report)
        
        # レポート保存
        output_path = Path(parameters_path).stem + "-parameter-validation-report.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nパラメータ検証レポートを保存しました: {output_path}")
        
        # 検証結果
        has_errors = any(not r.is_valid for r in results) or bool(config_errors)
        return not has_errors


def main():
    """コマンドラインインターフェース"""
    if len(sys.argv) < 3:
        print("Usage: python parameter-validator.py <template-file> <parameters-file> [schema-file]")
        sys.exit(1)
    
    template_file = sys.argv[1]
    parameters_file = sys.argv[2]
    schema_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    validator = ParameterValidator()
    is_valid = validator.validate_template_parameters(template_file, parameters_file, schema_file)
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()