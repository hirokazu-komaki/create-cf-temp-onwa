#!/usr/bin/env python3
"""
Validation Orchestrator
全ての検証機能を統合し、包括的な検証レポートを生成
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import datetime

# 他の検証モジュールをインポート
from cloudformation_validator import CloudFormationValidator, ValidationIssue
from parameter_validator import ParameterValidator, ParameterValidationResult
from well_architected_validator import WellArchitectedValidator


@dataclass
class ValidationSummary:
    """検証サマリー"""
    template_path: str
    parameters_path: Optional[str]
    timestamp: str
    overall_status: str  # 'PASS', 'FAIL', 'WARNING'
    
    # 各検証の結果
    syntax_validation: Dict[str, Any]
    parameter_validation: Dict[str, Any]
    well_architected_validation: Dict[str, Any]
    
    # 統計
    total_issues: int
    errors: int
    warnings: int
    infos: int


class ValidationOrchestrator:
    """検証オーケストレータ"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cf_validator = CloudFormationValidator(region)
        self.param_validator = ParameterValidator()
        self.wa_validator = WellArchitectedValidator()
    
    def run_comprehensive_validation(self, 
                                   template_path: str, 
                                   parameters_path: Optional[str] = None,
                                   config_path: Optional[str] = None) -> ValidationSummary:
        """包括的検証の実行"""
        
        timestamp = datetime.datetime.now().isoformat()
        
        # 1. CloudFormation構文検証
        print("🔍 CloudFormation構文検証を実行中...")
        syntax_results = self._run_syntax_validation(template_path, parameters_path)
        
        # 2. パラメータ検証
        print("🔍 パラメータ検証を実行中...")
        parameter_results = self._run_parameter_validation(template_path, parameters_path, config_path)
        
        # 3. Well-Architected準拠チェック
        print("🔍 Well-Architected準拠チェックを実行中...")
        wa_results = self._run_well_architected_validation(template_path)
        
        # 4. 結果の統合
        summary = self._create_validation_summary(
            template_path, parameters_path, timestamp,
            syntax_results, parameter_results, wa_results
        )
        
        return summary
    
    def _run_syntax_validation(self, template_path: str, parameters_path: Optional[str]) -> Dict[str, Any]:
        """構文検証の実行"""
        try:
            # パラメータ値の読み込み
            parameter_values = None
            if parameters_path:
                parameter_values = self.param_validator.load_parameters(parameters_path)
                if parameter_values and 'serviceConfigs' in parameter_values:
                    parameter_values = parameter_values['serviceConfigs']
            
            # 検証実行
            is_valid, issues = self.cf_validator.validate_template(template_path, parameter_values)
            
            return {
                'status': 'PASS' if is_valid else 'FAIL',
                'is_valid': is_valid,
                'issues': issues,
                'error_count': len([i for i in issues if i.severity == 'error']),
                'warning_count': len([i for i in issues if i.severity == 'warning']),
                'info_count': len([i for i in issues if i.severity == 'info'])
            }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'is_valid': False,
                'issues': [ValidationIssue(
                    severity='error',
                    category='system',
                    message=f"構文検証中にエラーが発生: {str(e)}"
                )],
                'error_count': 1,
                'warning_count': 0,
                'info_count': 0
            }
    
    def _run_parameter_validation(self, template_path: str, parameters_path: Optional[str], config_path: Optional[str]) -> Dict[str, Any]:
        """パラメータ検証の実行"""
        if not parameters_path:
            return {
                'status': 'SKIPPED',
                'is_valid': True,
                'results': [],
                'config_errors': [],
                'error_count': 0,
                'warning_count': 0
            }
        
        try:
            # テンプレート読み込み
            template = self.param_validator.load_template(template_path)
            if not template:
                return {
                    'status': 'ERROR',
                    'is_valid': False,
                    'results': [],
                    'config_errors': ['テンプレートの読み込みに失敗'],
                    'error_count': 1,
                    'warning_count': 0
                }
            
            # パラメータ読み込み
            parameters = self.param_validator.load_parameters(parameters_path)
            if not parameters:
                return {
                    'status': 'ERROR',
                    'is_valid': False,
                    'results': [],
                    'config_errors': ['パラメータファイルの読み込みに失敗'],
                    'error_count': 1,
                    'warning_count': 0
                }
            
            # 設定検証
            config_errors = []
            if config_path:
                config_errors = self.param_validator.validate_json_config_schema(parameters, config_path)
            
            consistency_errors = self.param_validator.validate_config_consistency(parameters)
            config_errors.extend(consistency_errors)
            
            # パラメータ検証
            param_values = parameters.get('serviceConfigs', parameters)
            results = self.param_validator.validate_parameters(template, param_values)
            
            has_errors = any(not r.is_valid for r in results) or bool(config_errors)
            
            return {
                'status': 'FAIL' if has_errors else 'PASS',
                'is_valid': not has_errors,
                'results': results,
                'config_errors': config_errors,
                'error_count': len([r for r in results if not r.is_valid]) + len(config_errors),
                'warning_count': sum(len(r.warnings) for r in results)
            }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'is_valid': False,
                'results': [],
                'config_errors': [f"パラメータ検証中にエラーが発生: {str(e)}"],
                'error_count': 1,
                'warning_count': 0
            }
    
    def _run_well_architected_validation(self, template_path: str) -> Dict[str, Any]:
        """Well-Architected検証の実行"""
        try:
            is_valid, messages = self.wa_validator.validate_cloudformation_template(template_path)
            
            error_count = len([m for m in messages if m.startswith("Error")])
            warning_count = len([m for m in messages if m.startswith("Warning")])
            info_count = len([m for m in messages if m.startswith("✓")])
            
            return {
                'status': 'FAIL' if not is_valid else 'PASS',
                'is_valid': is_valid,
                'messages': messages,
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count
            }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'is_valid': False,
                'messages': [f"Well-Architected検証中にエラーが発生: {str(e)}"],
                'error_count': 1,
                'warning_count': 0,
                'info_count': 0
            }
    
    def _create_validation_summary(self, 
                                 template_path: str,
                                 parameters_path: Optional[str],
                                 timestamp: str,
                                 syntax_results: Dict[str, Any],
                                 parameter_results: Dict[str, Any],
                                 wa_results: Dict[str, Any]) -> ValidationSummary:
        """検証サマリーの作成"""
        
        # 全体のステータス決定
        all_valid = (
            syntax_results['is_valid'] and 
            parameter_results['is_valid'] and 
            wa_results['is_valid']
        )
        
        has_warnings = (
            syntax_results.get('warning_count', 0) > 0 or
            parameter_results.get('warning_count', 0) > 0 or
            wa_results.get('warning_count', 0) > 0
        )
        
        if all_valid:
            overall_status = 'WARNING' if has_warnings else 'PASS'
        else:
            overall_status = 'FAIL'
        
        # 統計計算
        total_errors = (
            syntax_results.get('error_count', 0) +
            parameter_results.get('error_count', 0) +
            wa_results.get('error_count', 0)
        )
        
        total_warnings = (
            syntax_results.get('warning_count', 0) +
            parameter_results.get('warning_count', 0) +
            wa_results.get('warning_count', 0)
        )
        
        total_infos = (
            syntax_results.get('info_count', 0) +
            wa_results.get('info_count', 0)
        )
        
        return ValidationSummary(
            template_path=template_path,
            parameters_path=parameters_path,
            timestamp=timestamp,
            overall_status=overall_status,
            syntax_validation=syntax_results,
            parameter_validation=parameter_results,
            well_architected_validation=wa_results,
            total_issues=total_errors + total_warnings + total_infos,
            errors=total_errors,
            warnings=total_warnings,
            infos=total_infos
        )
    
    def generate_comprehensive_report(self, summary: ValidationSummary) -> str:
        """包括的検証レポートの生成"""
        report = []
        
        # ヘッダー
        report.append("=" * 100)
        report.append("COMPREHENSIVE CLOUDFORMATION VALIDATION REPORT")
        report.append("=" * 100)
        report.append(f"Template: {summary.template_path}")
        if summary.parameters_path:
            report.append(f"Parameters: {summary.parameters_path}")
        report.append(f"Timestamp: {summary.timestamp}")
        report.append("")
        
        # 全体サマリー
        status_icon = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌'
        }.get(summary.overall_status, '❓')
        
        report.append(f"OVERALL STATUS: {status_icon} {summary.overall_status}")
        report.append("")
        report.append("SUMMARY:")
        report.append(f"  Total Issues: {summary.total_issues}")
        report.append(f"  Errors: {summary.errors}")
        report.append(f"  Warnings: {summary.warnings}")
        report.append(f"  Info: {summary.infos}")
        report.append("")
        
        # 各検証の詳細
        report.append("VALIDATION DETAILS:")
        report.append("")
        
        # 1. 構文検証
        report.append("1. CLOUDFORMATION SYNTAX VALIDATION")
        report.append("-" * 50)
        syntax = summary.syntax_validation
        status_icon = '✅' if syntax['is_valid'] else '❌'
        report.append(f"Status: {status_icon} {syntax['status']}")
        report.append(f"Errors: {syntax.get('error_count', 0)}")
        report.append(f"Warnings: {syntax.get('warning_count', 0)}")
        report.append(f"Info: {syntax.get('info_count', 0)}")
        
        if syntax.get('issues'):
            report.append("\nIssues:")
            for issue in syntax['issues']:
                icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(issue.severity, '❓')
                report.append(f"  {icon} [{issue.category}] {issue.message}")
                if issue.location:
                    report.append(f"      Location: {issue.location}")
                if issue.suggestion:
                    report.append(f"      Suggestion: {issue.suggestion}")
        
        report.append("")
        
        # 2. パラメータ検証
        report.append("2. PARAMETER VALIDATION")
        report.append("-" * 50)
        params = summary.parameter_validation
        
        if params['status'] == 'SKIPPED':
            report.append("Status: ⏭️ SKIPPED (No parameters file provided)")
        else:
            status_icon = '✅' if params['is_valid'] else '❌'
            report.append(f"Status: {status_icon} {params['status']}")
            report.append(f"Errors: {params.get('error_count', 0)}")
            report.append(f"Warnings: {params.get('warning_count', 0)}")
            
            if params.get('config_errors'):
                report.append("\nConfiguration Errors:")
                for error in params['config_errors']:
                    report.append(f"  ❌ {error}")
            
            if params.get('results'):
                report.append("\nParameter Details:")
                for result in params['results']:
                    status_icon = '✅' if result.is_valid else '❌'
                    report.append(f"  {status_icon} {result.parameter_name} ({result.expected_type})")
                    
                    for error in result.errors:
                        report.append(f"      ❌ {error}")
                    
                    for warning in result.warnings:
                        report.append(f"      ⚠️ {warning}")
        
        report.append("")
        
        # 3. Well-Architected検証
        report.append("3. WELL-ARCHITECTED COMPLIANCE VALIDATION")
        report.append("-" * 50)
        wa = summary.well_architected_validation
        status_icon = '✅' if wa['is_valid'] else '❌'
        report.append(f"Status: {status_icon} {wa['status']}")
        report.append(f"Errors: {wa.get('error_count', 0)}")
        report.append(f"Warnings: {wa.get('warning_count', 0)}")
        report.append(f"Compliance Items: {wa.get('info_count', 0)}")
        
        if wa.get('messages'):
            report.append("\nCompliance Details:")
            for message in wa['messages']:
                if message.startswith("✓"):
                    report.append(f"  ✅ {message[2:]}")
                elif message.startswith("Warning"):
                    report.append(f"  ⚠️ {message}")
                elif message.startswith("Error"):
                    report.append(f"  ❌ {message}")
                else:
                    report.append(f"  ℹ️ {message}")
        
        report.append("")
        
        # 推奨事項
        report.append("RECOMMENDATIONS:")
        report.append("-" * 50)
        
        if summary.overall_status == 'FAIL':
            report.append("❌ 検証に失敗しました。上記のエラーを修正してください。")
        elif summary.overall_status == 'WARNING':
            report.append("⚠️ 検証は成功しましたが、警告があります。確認することを推奨します。")
        else:
            report.append("✅ 全ての検証に成功しました。")
        
        if summary.errors > 0:
            report.append("• エラーを修正してから再度検証を実行してください")
        
        if summary.warnings > 0:
            report.append("• 警告項目を確認し、必要に応じて修正してください")
        
        report.append("• 定期的な検証の実行を推奨します")
        
        report.append("")
        report.append("=" * 100)
        
        return "\n".join(report)
    
    def save_validation_report(self, summary: ValidationSummary, output_path: Optional[str] = None) -> str:
        """検証レポートをファイルに保存"""
        if output_path is None:
            template_name = Path(summary.template_path).stem
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{template_name}_comprehensive_validation_{timestamp}.txt"
        
        report = self.generate_comprehensive_report(summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return output_path
    
    def save_validation_json(self, summary: ValidationSummary, output_path: Optional[str] = None) -> str:
        """検証結果をJSONファイルに保存"""
        if output_path is None:
            template_name = Path(summary.template_path).stem
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{template_name}_validation_results_{timestamp}.json"
        
        # ValidationSummaryをJSONシリアライズ可能な形式に変換
        json_data = {
            'template_path': summary.template_path,
            'parameters_path': summary.parameters_path,
            'timestamp': summary.timestamp,
            'overall_status': summary.overall_status,
            'statistics': {
                'total_issues': summary.total_issues,
                'errors': summary.errors,
                'warnings': summary.warnings,
                'infos': summary.infos
            },
            'syntax_validation': {
                'status': summary.syntax_validation['status'],
                'is_valid': summary.syntax_validation['is_valid'],
                'error_count': summary.syntax_validation.get('error_count', 0),
                'warning_count': summary.syntax_validation.get('warning_count', 0),
                'info_count': summary.syntax_validation.get('info_count', 0),
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'message': issue.message,
                        'location': issue.location,
                        'suggestion': issue.suggestion
                    }
                    for issue in summary.syntax_validation.get('issues', [])
                ]
            },
            'parameter_validation': {
                'status': summary.parameter_validation['status'],
                'is_valid': summary.parameter_validation['is_valid'],
                'error_count': summary.parameter_validation.get('error_count', 0),
                'warning_count': summary.parameter_validation.get('warning_count', 0),
                'config_errors': summary.parameter_validation.get('config_errors', []),
                'results': [
                    {
                        'parameter_name': result.parameter_name,
                        'is_valid': result.is_valid,
                        'errors': result.errors,
                        'warnings': result.warnings,
                        'expected_type': result.expected_type,
                        'value': result.value
                    }
                    for result in summary.parameter_validation.get('results', [])
                ]
            },
            'well_architected_validation': {
                'status': summary.well_architected_validation['status'],
                'is_valid': summary.well_architected_validation['is_valid'],
                'error_count': summary.well_architected_validation.get('error_count', 0),
                'warning_count': summary.well_architected_validation.get('warning_count', 0),
                'info_count': summary.well_architected_validation.get('info_count', 0),
                'messages': summary.well_architected_validation.get('messages', [])
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return output_path


def main():
    """コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description='Comprehensive CloudFormation Template Validation')
    parser.add_argument('template', help='CloudFormation template file path')
    parser.add_argument('--parameters', '-p', help='Parameters file path')
    parser.add_argument('--config', '-c', help='Configuration schema file path')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    parser.add_argument('--output', '-o', help='Output report file path')
    parser.add_argument('--json', '-j', help='Output JSON results file path')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # 検証実行
    orchestrator = ValidationOrchestrator(region=args.region)
    
    if not args.quiet:
        print("🚀 包括的CloudFormation検証を開始します...")
        print(f"📄 テンプレート: {args.template}")
        if args.parameters:
            print(f"⚙️ パラメータ: {args.parameters}")
        print("")
    
    summary = orchestrator.run_comprehensive_validation(
        template_path=args.template,
        parameters_path=args.parameters,
        config_path=args.config
    )
    
    # レポート生成
    if not args.quiet:
        report = orchestrator.generate_comprehensive_report(summary)
        print(report)
    
    # ファイル保存
    if args.output or not args.quiet:
        report_path = orchestrator.save_validation_report(summary, args.output)
        if not args.quiet:
            print(f"\n📊 検証レポートを保存しました: {report_path}")
    
    if args.json:
        json_path = orchestrator.save_validation_json(summary, args.json)
        if not args.quiet:
            print(f"📋 JSON結果を保存しました: {json_path}")
    
    # 終了コード
    exit_code = 0 if summary.overall_status in ['PASS', 'WARNING'] else 1
    
    if not args.quiet:
        status_message = {
            'PASS': '✅ 検証完了: 全てのチェックに合格しました',
            'WARNING': '⚠️ 検証完了: 警告がありますが、基本的な検証は合格しました',
            'FAIL': '❌ 検証失敗: エラーを修正してください'
        }.get(summary.overall_status, '❓ 検証完了: 不明なステータス')
        
        print(f"\n{status_message}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()