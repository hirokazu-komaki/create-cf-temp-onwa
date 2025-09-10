#!/usr/bin/env python3
"""
CloudFormation Template Syntax Validator
CloudFormationテンプレートの構文検証とベストプラクティスチェック
"""

import json
import yaml
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError


@dataclass
class ValidationIssue:
    """検証問題"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'best-practice', 'security', 'performance'
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


class CloudFormationValidator:
    """CloudFormationテンプレート検証クラス"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.issues: List[ValidationIssue] = []
        
        # AWS CloudFormation クライアント（構文検証用）
        try:
            self.cf_client = boto3.client('cloudformation', region_name=region)
        except Exception:
            self.cf_client = None
    
    def load_template(self, template_path: str) -> Tuple[Optional[Dict[str, Any]], List[ValidationIssue]]:
        """テンプレートファイルを読み込み"""
        issues = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # ファイル拡張子に基づいてパース
            if template_path.endswith('.json'):
                template = json.loads(content)
            elif template_path.endswith(('.yaml', '.yml')):
                template = yaml.safe_load(content)
            else:
                # 内容から推測
                try:
                    template = json.loads(content)
                except json.JSONDecodeError:
                    try:
                        template = yaml.safe_load(content)
                    except yaml.YAMLError as e:
                        issues.append(ValidationIssue(
                            severity='error',
                            category='syntax',
                            message=f"テンプレートの解析に失敗: {str(e)}"
                        ))
                        return None, issues
            
            return template, issues
            
        except FileNotFoundError:
            issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"テンプレートファイルが見つかりません: {template_path}"
            ))
            return None, issues
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"テンプレートの構文エラー: {str(e)}"
            ))
            return None, issues
    
    def validate_template_structure(self, template: Dict[str, Any]) -> List[ValidationIssue]:
        """テンプレート基本構造の検証"""
        issues = []
        
        # 必須フィールドの確認
        if 'AWSTemplateFormatVersion' not in template:
            issues.append(ValidationIssue(
                severity='warning',
                category='best-practice',
                message="AWSTemplateFormatVersionが指定されていません",
                suggestion="'2010-09-09'を指定することを推奨します"
            ))
        
        if 'Description' not in template:
            issues.append(ValidationIssue(
                severity='warning',
                category='best-practice',
                message="Descriptionが指定されていません",
                suggestion="テンプレートの目的を説明するDescriptionを追加してください"
            ))
        
        # リソースセクションの確認
        if 'Resources' not in template:
            issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message="Resourcesセクションが必須です"
            ))
        elif not template['Resources']:
            issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message="Resourcesセクションが空です"
            ))
        
        # 有効なセクション名の確認
        valid_sections = {
            'AWSTemplateFormatVersion', 'Description', 'Metadata', 'Parameters',
            'Mappings', 'Conditions', 'Transform', 'Resources', 'Outputs'
        }
        
        for section in template.keys():
            if section not in valid_sections:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"無効なセクション名: {section}",
                    suggestion=f"有効なセクション名: {', '.join(valid_sections)}"
                ))
        
        return issues
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[ValidationIssue]:
        """パラメータセクションの検証"""
        issues = []
        
        for param_name, param_config in parameters.items():
            # パラメータ名の検証
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', param_name):
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"パラメータ名が無効: {param_name}",
                    location=f"Parameters.{param_name}",
                    suggestion="パラメータ名は英字で始まり、英数字のみを含む必要があります"
                ))
            
            # 必須フィールドの確認
            if 'Type' not in param_config:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"パラメータ {param_name} にTypeが指定されていません",
                    location=f"Parameters.{param_name}"
                ))
            
            # Descriptionの推奨
            if 'Description' not in param_config:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='best-practice',
                    message=f"パラメータ {param_name} にDescriptionがありません",
                    location=f"Parameters.{param_name}",
                    suggestion="パラメータの目的を説明するDescriptionを追加してください"
                ))
            
            # デフォルト値の推奨
            param_type = param_config.get('Type', '')
            if param_type in ['String', 'Number'] and 'Default' not in param_config:
                issues.append(ValidationIssue(
                    severity='info',
                    category='best-practice',
                    message=f"パラメータ {param_name} にデフォルト値がありません",
                    location=f"Parameters.{param_name}",
                    suggestion="適切なデフォルト値の設定を検討してください"
                ))
        
        return issues
    
    def validate_resources(self, resources: Dict[str, Any]) -> List[ValidationIssue]:
        """リソースセクションの検証"""
        issues = []
        
        for resource_name, resource_config in resources.items():
            # リソース名の検証
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', resource_name):
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"リソース名が無効: {resource_name}",
                    location=f"Resources.{resource_name}",
                    suggestion="リソース名は英字で始まり、英数字のみを含む必要があります"
                ))
            
            # 必須フィールドの確認
            if 'Type' not in resource_config:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"リソース {resource_name} にTypeが指定されていません",
                    location=f"Resources.{resource_name}"
                ))
            
            # リソースタイプの形式確認
            resource_type = resource_config.get('Type', '')
            if resource_type and not re.match(r'^[A-Z][a-zA-Z0-9]*::[A-Z][a-zA-Z0-9]*::[A-Z][a-zA-Z0-9]*$', resource_type):
                issues.append(ValidationIssue(
                    severity='warning',
                    category='syntax',
                    message=f"リソースタイプの形式が疑わしい: {resource_type}",
                    location=f"Resources.{resource_name}.Type",
                    suggestion="リソースタイプは 'AWS::Service::ResourceType' の形式である必要があります"
                ))
            
            # セキュリティ関連のチェック
            issues.extend(self._validate_resource_security(resource_name, resource_config))
            
            # パフォーマンス関連のチェック
            issues.extend(self._validate_resource_performance(resource_name, resource_config))
        
        return issues
    
    def _validate_resource_security(self, resource_name: str, resource_config: Dict[str, Any]) -> List[ValidationIssue]:
        """リソースのセキュリティ設定検証"""
        issues = []
        resource_type = resource_config.get('Type', '')
        properties = resource_config.get('Properties', {})
        
        # S3バケットのセキュリティチェック
        if resource_type == 'AWS::S3::Bucket':
            if 'PublicReadPolicy' in properties and properties['PublicReadPolicy'] == 'Allow':
                issues.append(ValidationIssue(
                    severity='warning',
                    category='security',
                    message=f"S3バケット {resource_name} でパブリック読み取りが許可されています",
                    location=f"Resources.{resource_name}.Properties.PublicReadPolicy",
                    suggestion="セキュリティ要件を確認し、必要に応じて制限してください"
                ))
            
            if 'VersioningConfiguration' not in properties:
                issues.append(ValidationIssue(
                    severity='info',
                    category='best-practice',
                    message=f"S3バケット {resource_name} でバージョニングが設定されていません",
                    location=f"Resources.{resource_name}.Properties",
                    suggestion="データ保護のためバージョニングの有効化を検討してください"
                ))
        
        # IAMロールのセキュリティチェック
        elif resource_type == 'AWS::IAM::Role':
            assume_role_policy = properties.get('AssumeRolePolicyDocument', {})
            if assume_role_policy:
                statements = assume_role_policy.get('Statement', [])
                for i, statement in enumerate(statements):
                    principal = statement.get('Principal', {})
                    if principal == '*' or (isinstance(principal, dict) and principal.get('AWS') == '*'):
                        issues.append(ValidationIssue(
                            severity='error',
                            category='security',
                            message=f"IAMロール {resource_name} で全てのプリンシパルが許可されています",
                            location=f"Resources.{resource_name}.Properties.AssumeRolePolicyDocument.Statement[{i}].Principal",
                            suggestion="最小権限の原則に従い、特定のプリンシパルのみを許可してください"
                        ))
        
        # セキュリティグループのチェック
        elif resource_type == 'AWS::EC2::SecurityGroup':
            ingress_rules = properties.get('SecurityGroupIngress', [])
            for i, rule in enumerate(ingress_rules):
                cidr_ip = rule.get('CidrIp', '')
                if cidr_ip == '0.0.0.0/0':
                    from_port = rule.get('FromPort', 0)
                    to_port = rule.get('ToPort', 0)
                    if from_port == 22 or to_port == 22:
                        issues.append(ValidationIssue(
                            severity='error',
                            category='security',
                            message=f"セキュリティグループ {resource_name} でSSH(22)が全てのIPに開放されています",
                            location=f"Resources.{resource_name}.Properties.SecurityGroupIngress[{i}]",
                            suggestion="SSH接続は特定のIPアドレスからのみ許可してください"
                        ))
                    elif from_port == 3389 or to_port == 3389:
                        issues.append(ValidationIssue(
                            severity='error',
                            category='security',
                            message=f"セキュリティグループ {resource_name} でRDP(3389)が全てのIPに開放されています",
                            location=f"Resources.{resource_name}.Properties.SecurityGroupIngress[{i}]",
                            suggestion="RDP接続は特定のIPアドレスからのみ許可してください"
                        ))
        
        return issues
    
    def _validate_resource_performance(self, resource_name: str, resource_config: Dict[str, Any]) -> List[ValidationIssue]:
        """リソースのパフォーマンス設定検証"""
        issues = []
        resource_type = resource_config.get('Type', '')
        properties = resource_config.get('Properties', {})
        
        # EC2インスタンスのパフォーマンスチェック
        if resource_type == 'AWS::EC2::Instance':
            instance_type = properties.get('InstanceType', '')
            if instance_type.startswith('t2.') or instance_type.startswith('t3.'):
                issues.append(ValidationIssue(
                    severity='info',
                    category='performance',
                    message=f"EC2インスタンス {resource_name} でバーストパフォーマンスインスタンスが使用されています",
                    location=f"Resources.{resource_name}.Properties.InstanceType",
                    suggestion="継続的な高パフォーマンスが必要な場合は、他のインスタンスタイプを検討してください"
                ))
        
        # RDSインスタンスのパフォーマンスチェック
        elif resource_type == 'AWS::RDS::DBInstance':
            if 'MultiAZ' not in properties or not properties['MultiAZ']:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='performance',
                    message=f"RDSインスタンス {resource_name} でMulti-AZが無効です",
                    location=f"Resources.{resource_name}.Properties",
                    suggestion="高可用性のためMulti-AZの有効化を検討してください"
                ))
        
        return issues
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> List[ValidationIssue]:
        """アウトプットセクションの検証"""
        issues = []
        
        for output_name, output_config in outputs.items():
            # アウトプット名の検証
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', output_name):
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"アウトプット名が無効: {output_name}",
                    location=f"Outputs.{output_name}",
                    suggestion="アウトプット名は英字で始まり、英数字のみを含む必要があります"
                ))
            
            # 必須フィールドの確認
            if 'Value' not in output_config:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"アウトプット {output_name} にValueが指定されていません",
                    location=f"Outputs.{output_name}"
                ))
            
            # Descriptionの推奨
            if 'Description' not in output_config:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='best-practice',
                    message=f"アウトプット {output_name} にDescriptionがありません",
                    location=f"Outputs.{output_name}",
                    suggestion="アウトプットの目的を説明するDescriptionを追加してください"
                ))
            
            # Export名の推奨
            if 'Export' not in output_config:
                issues.append(ValidationIssue(
                    severity='info',
                    category='best-practice',
                    message=f"アウトプット {output_name} にExportが設定されていません",
                    location=f"Outputs.{output_name}",
                    suggestion="クロススタック参照が必要な場合はExportを設定してください"
                ))
        
        return issues
    
    def validate_with_aws_api(self, template: Dict[str, Any]) -> List[ValidationIssue]:
        """AWS APIを使用したテンプレート検証"""
        issues = []
        
        if not self.cf_client:
            issues.append(ValidationIssue(
                severity='warning',
                category='syntax',
                message="AWS APIクライアントが利用できません。構文検証をスキップします"
            ))
            return issues
        
        try:
            # テンプレートをJSON文字列に変換
            template_body = json.dumps(template, ensure_ascii=False)
            
            # AWS CloudFormation APIで検証
            response = self.cf_client.validate_template(TemplateBody=template_body)
            
            # 成功した場合の情報
            issues.append(ValidationIssue(
                severity='info',
                category='syntax',
                message="AWS CloudFormation APIによる構文検証が成功しました"
            ))
            
            # パラメータ情報の確認
            parameters = response.get('Parameters', [])
            if parameters:
                param_names = [p['ParameterKey'] for p in parameters]
                issues.append(ValidationIssue(
                    severity='info',
                    category='syntax',
                    message=f"検出されたパラメータ: {', '.join(param_names)}"
                ))
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ValidationError':
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"AWS CloudFormation構文エラー: {error_message}"
                ))
            else:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='syntax',
                    message=f"AWS API検証エラー ({error_code}): {error_message}"
                ))
        
        return issues
    
    def validate_parameter_values(self, template: Dict[str, Any], parameter_values: Dict[str, Any]) -> List[ValidationIssue]:
        """パラメータ値の妥当性検証"""
        issues = []
        
        template_params = template.get('Parameters', {})
        
        for param_name, param_value in parameter_values.items():
            if param_name not in template_params:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"未定義のパラメータ: {param_name}"
                ))
                continue
            
            param_config = template_params[param_name]
            param_type = param_config.get('Type', 'String')
            
            # 型チェック
            if param_type == 'Number':
                try:
                    float(param_value)
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        severity='error',
                        category='syntax',
                        message=f"パラメータ {param_name} の値が数値ではありません: {param_value}"
                    ))
            
            # 許可値チェック
            allowed_values = param_config.get('AllowedValues', [])
            if allowed_values and param_value not in allowed_values:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"パラメータ {param_name} の値が許可されていません: {param_value}",
                    suggestion=f"許可値: {', '.join(map(str, allowed_values))}"
                ))
            
            # パターンチェック
            allowed_pattern = param_config.get('AllowedPattern')
            if allowed_pattern and isinstance(param_value, str):
                if not re.match(allowed_pattern, param_value):
                    issues.append(ValidationIssue(
                        severity='error',
                        category='syntax',
                        message=f"パラメータ {param_name} の値がパターンに一致しません: {param_value}",
                        suggestion=f"パターン: {allowed_pattern}"
                    ))
            
            # 長さチェック
            min_length = param_config.get('MinLength')
            max_length = param_config.get('MaxLength')
            if isinstance(param_value, str):
                if min_length and len(param_value) < min_length:
                    issues.append(ValidationIssue(
                        severity='error',
                        category='syntax',
                        message=f"パラメータ {param_name} の値が短すぎます: {len(param_value)} < {min_length}"
                    ))
                if max_length and len(param_value) > max_length:
                    issues.append(ValidationIssue(
                        severity='error',
                        category='syntax',
                        message=f"パラメータ {param_name} の値が長すぎます: {len(param_value)} > {max_length}"
                    ))
        
        # 必須パラメータのチェック
        for param_name, param_config in template_params.items():
            if 'Default' not in param_config and param_name not in parameter_values:
                issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message=f"必須パラメータが指定されていません: {param_name}"
                ))
        
        return issues
    
    def validate_template(self, template_path: str, parameter_values: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[ValidationIssue]]:
        """テンプレートの包括的検証"""
        all_issues = []
        
        # テンプレート読み込み
        template, load_issues = self.load_template(template_path)
        all_issues.extend(load_issues)
        
        if template is None:
            return False, all_issues
        
        # 構造検証
        all_issues.extend(self.validate_template_structure(template))
        
        # セクション別検証
        if 'Parameters' in template:
            all_issues.extend(self.validate_parameters(template['Parameters']))
        
        if 'Resources' in template:
            all_issues.extend(self.validate_resources(template['Resources']))
        
        if 'Outputs' in template:
            all_issues.extend(self.validate_outputs(template['Outputs']))
        
        # AWS API検証
        all_issues.extend(self.validate_with_aws_api(template))
        
        # パラメータ値検証
        if parameter_values:
            all_issues.extend(self.validate_parameter_values(template, parameter_values))
        
        # エラーがあるかチェック
        has_errors = any(issue.severity == 'error' for issue in all_issues)
        
        return not has_errors, all_issues
    
    def generate_validation_report(self, issues: List[ValidationIssue], template_path: str) -> str:
        """検証レポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("CloudFormation Template Validation Report")
        report.append("=" * 80)
        report.append(f"Template: {template_path}")
        report.append("")
        
        # サマリー
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        infos = [i for i in issues if i.severity == 'info']
        
        report.append(f"Errors: {len(errors)}")
        report.append(f"Warnings: {len(warnings)}")
        report.append(f"Info: {len(infos)}")
        report.append("")
        
        # 問題の詳細
        for severity, icon in [('error', '✗'), ('warning', '⚠'), ('info', 'ℹ')]:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                report.append(f"{severity.upper()}S:")
                for issue in severity_issues:
                    report.append(f"  {icon} [{issue.category}] {issue.message}")
                    if issue.location:
                        report.append(f"      Location: {issue.location}")
                    if issue.suggestion:
                        report.append(f"      Suggestion: {issue.suggestion}")
                    report.append("")
        
        return "\n".join(report)


def main():
    """コマンドラインインターフェース"""
    if len(sys.argv) < 2:
        print("Usage: python cloudformation-validator.py <template-file> [parameters-file]")
        sys.exit(1)
    
    template_file = sys.argv[1]
    parameters_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # パラメータ値の読み込み
    parameter_values = None
    if parameters_file:
        try:
            with open(parameters_file, 'r', encoding='utf-8') as f:
                if parameters_file.endswith('.json'):
                    parameter_values = json.load(f)
                else:
                    parameter_values = yaml.safe_load(f)
        except Exception as e:
            print(f"パラメータファイルの読み込みエラー: {e}")
            sys.exit(1)
    
    # 検証実行
    validator = CloudFormationValidator()
    is_valid, issues = validator.validate_template(template_file, parameter_values)
    
    # レポート生成
    report = validator.generate_validation_report(issues, template_file)
    print(report)
    
    # レポートをファイルに保存
    output_path = Path(template_file).stem + "-validation-report.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n検証レポートを保存しました: {output_path}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()