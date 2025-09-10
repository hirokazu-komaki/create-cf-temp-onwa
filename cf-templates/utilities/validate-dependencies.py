#!/usr/bin/env python3
"""
Cross-Stack Dependencies Validator
クロススタック依存関係の検証とエラーハンドリング
"""

import json
import yaml
import boto3
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse

@dataclass
class ValidationResult:
    """検証結果"""
    stack_name: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_exports: List[str]
    circular_dependencies: List[str]

class DependencyValidator:
    """依存関係検証クラス"""
    
    def __init__(self, region: str = 'us-east-1', profile: str = 'mame-local-wani'):
        self.region = region
        session = boto3.Session(profile_name=profile)
        self.cf_client = session.client('cloudformation', region_name=region)
        self.validation_results = {}
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_stack_exports(self, stack_name: str) -> Dict[str, str]:
        """スタックのエクスポート値を取得"""
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            if stack['StackStatus'] not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                return {}
            
            exports = {}
            for output in stack.get('Outputs', []):
                if 'ExportName' in output:
                    exports[output['OutputKey']] = output['ExportName']
            
            return exports
            
        except self.cf_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                return {}  # スタックが存在しない
            raise
    
    def validate_stack_dependencies(self, stack_name: str, config: Dict[str, Any]) -> ValidationResult:
        """単一スタックの依存関係を検証"""
        result = ValidationResult(
            stack_name=stack_name,
            is_valid=True,
            errors=[],
            warnings=[],
            missing_exports=[],
            circular_dependencies=[]
        )
        
        if stack_name not in config['dependencies']:
            return result
        
        dependencies = config['dependencies'][stack_name]
        
        for dep in dependencies:
            dep_stack_name = dep['stack_name']
            required_outputs = dep['required_outputs']
            optional_outputs = dep.get('optional_outputs', [])
            
            # 依存スタックの存在確認
            try:
                response = self.cf_client.describe_stacks(StackName=dep_stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
                
                if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                    result.errors.append(
                        f"依存スタック '{dep_stack_name}' のステータスが不正: {stack_status}"
                    )
                    result.is_valid = False
                    continue
                
                # エクスポート値の確認
                stack_outputs = response['Stacks'][0].get('Outputs', [])
                available_exports = {}
                for output in stack_outputs:
                    if 'ExportName' in output:
                        available_exports[output['OutputKey']] = output['ExportName']
                
                # 必須エクスポートの確認
                for required_output in required_outputs:
                    if required_output not in available_exports:
                        result.missing_exports.append(
                            f"必須エクスポート '{required_output}' が依存スタック '{dep_stack_name}' に存在しません"
                        )
                        result.is_valid = False
                
                # オプションエクスポートの確認
                for optional_output in optional_outputs:
                    if optional_output not in available_exports:
                        result.warnings.append(
                            f"オプションエクスポート '{optional_output}' が依存スタック '{dep_stack_name}' に存在しません"
                        )
            
            except self.cf_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ValidationError':
                    result.errors.append(f"依存スタック '{dep_stack_name}' が存在しません")
                    result.is_valid = False
                else:
                    result.errors.append(f"依存スタック '{dep_stack_name}' の確認中にエラー: {str(e)}")
                    result.is_valid = False
        
        return result
    
    def detect_circular_dependencies(self, config: Dict[str, Any]) -> List[List[str]]:
        """循環依存関係を検出"""
        dependencies = config.get('dependencies', {})
        circular_deps = []
        
        def has_path(start: str, end: str, visited: set) -> bool:
            """startからendへのパスが存在するかチェック"""
            if start == end:
                return True
            
            if start in visited:
                return False
            
            visited.add(start)
            
            if start in dependencies:
                for dep in dependencies[start]:
                    if has_path(dep['stack_name'], end, visited.copy()):
                        return True
            
            return False
        
        # 各スタックペアで循環依存をチェック
        all_stacks = set(dependencies.keys())
        for deps in dependencies.values():
            for dep in deps:
                all_stacks.add(dep['stack_name'])
        
        for stack_a in all_stacks:
            for stack_b in all_stacks:
                if stack_a != stack_b:
                    if (has_path(stack_a, stack_b, set()) and 
                        has_path(stack_b, stack_a, set())):
                        cycle = [stack_a, stack_b]
                        if cycle not in circular_deps and cycle[::-1] not in circular_deps:
                            circular_deps.append(cycle)
        
        return circular_deps
    
    def validate_export_naming_consistency(self, config: Dict[str, Any]) -> List[str]:
        """エクスポート名の命名規則一貫性をチェック"""
        issues = []
        stack_outputs = config.get('stack_outputs', {})
        
        for stack_name, outputs in stack_outputs.items():
            for output in outputs:
                export_name = output.get('export_name', '')
                if not export_name:
                    continue
                
                # 命名規則チェック: {ProjectName}-{Environment}-{ResourceName}
                if not ('{ProjectName}' in export_name and '{Environment}' in export_name):
                    issues.append(
                        f"スタック '{stack_name}' のエクスポート '{output['name']}' の命名規則が不正: {export_name}"
                    )
        
        return issues
    
    def validate_all_stacks(self, config: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """全スタックの依存関係を検証"""
        results = {}
        
        # 循環依存関係の検出
        circular_deps = self.detect_circular_dependencies(config)
        
        # エクスポート命名規則の検証
        naming_issues = self.validate_export_naming_consistency(config)
        
        # 各スタックの検証
        all_stacks = set(config.get('dependencies', {}).keys())
        for deps in config.get('dependencies', {}).values():
            for dep in deps:
                all_stacks.add(dep['stack_name'])
        
        for stack_name in all_stacks:
            result = self.validate_stack_dependencies(stack_name, config)
            
            # 循環依存関係の情報を追加
            for cycle in circular_deps:
                if stack_name in cycle:
                    result.circular_dependencies.extend(cycle)
                    result.errors.append(f"循環依存関係が検出されました: {' -> '.join(cycle)}")
                    result.is_valid = False
            
            results[stack_name] = result
        
        # 命名規則の問題を全体の警告として追加
        if naming_issues:
            for stack_name in results:
                results[stack_name].warnings.extend(naming_issues)
        
        return results
    
    def generate_validation_report(self, results: Dict[str, ValidationResult]) -> str:
        """検証レポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("Cross-Stack Dependencies Validation Report")
        report.append("=" * 80)
        report.append("")
        
        # サマリー
        total_stacks = len(results)
        valid_stacks = sum(1 for r in results.values() if r.is_valid)
        invalid_stacks = total_stacks - valid_stacks
        
        report.append(f"Total Stacks: {total_stacks}")
        report.append(f"Valid Stacks: {valid_stacks}")
        report.append(f"Invalid Stacks: {invalid_stacks}")
        report.append("")
        
        # 各スタックの詳細
        for stack_name, result in results.items():
            report.append(f"Stack: {stack_name}")
            report.append(f"Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
            
            if result.errors:
                report.append("  Errors:")
                for error in result.errors:
                    report.append(f"    - {error}")
            
            if result.warnings:
                report.append("  Warnings:")
                for warning in result.warnings:
                    report.append(f"    - {warning}")
            
            if result.missing_exports:
                report.append("  Missing Exports:")
                for missing in result.missing_exports:
                    report.append(f"    - {missing}")
            
            report.append("")
        
        return "\n".join(report)
    
    def save_validation_report(self, results: Dict[str, ValidationResult], output_path: str):
        """検証レポートをファイルに保存"""
        report = self.generate_validation_report(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Validation report saved to: {output_path}")

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='Cross-Stack Dependencies Validator')
    parser.add_argument('--config', '-c', 
                       default='cross-stack-config.json',
                       help='Configuration file path')
    parser.add_argument('--region', '-r', 
                       default='us-east-1',
                       help='AWS region')
    parser.add_argument('--profile', '-p',
                       default='mame-local-wani',
                       help='AWS profile name')
    parser.add_argument('--output', '-o',
                       default='validation-report.txt',
                       help='Output report file path')
    parser.add_argument('--stack', '-s',
                       help='Validate specific stack only')
    
    args = parser.parse_args()
    
    # 設定ファイルのパス解決
    config_path = Path(args.config)
    if not config_path.is_absolute():
        if str(config_path).startswith('cf-templates/'):
            config_path = Path(args.config)
        else:
            config_path = Path(__file__).parent / config_path
    
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    # バリデーターを初期化
    validator = DependencyValidator(region=args.region, profile=args.profile)
    
    # 設定を読み込み
    config = validator.load_config(str(config_path))
    
    # 検証実行
    if args.stack:
        # 特定スタックのみ検証
        result = validator.validate_stack_dependencies(args.stack, config)
        results = {args.stack: result}
    else:
        # 全スタック検証
        results = validator.validate_all_stacks(config)
    
    # レポート生成
    report = validator.generate_validation_report(results)
    print(report)
    
    # レポート保存
    validator.save_validation_report(results, args.output)
    
    # 終了コード設定
    has_errors = any(not r.is_valid for r in results.values())
    sys.exit(1 if has_errors else 0)

if __name__ == "__main__":
    main()