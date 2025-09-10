#!/usr/bin/env python3
"""
Configuration Validator
クロススタック設定ファイルの構造と整合性を検証（AWS接続不要）
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

class ConfigValidator:
    """設定ファイル検証クラス"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.errors.append(f"設定ファイルが見つかりません: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.errors.append(f"JSONパースエラー: {e}")
            return {}
    
    def validate_structure(self, config: Dict[str, Any]) -> bool:
        """設定ファイルの基本構造を検証"""
        required_sections = ['stack_outputs', 'dependencies']
        
        for section in required_sections:
            if section not in config:
                self.errors.append(f"必須セクション '{section}' が見つかりません")
                return False
        
        return True
    
    def validate_stack_outputs(self, stack_outputs: Dict[str, Any]) -> bool:
        """スタックアウトプット設定を検証"""
        valid = True
        
        for stack_name, outputs in stack_outputs.items():
            if not isinstance(outputs, list):
                self.errors.append(f"スタック '{stack_name}' のアウトプットはリスト形式である必要があります")
                valid = False
                continue
            
            for i, output in enumerate(outputs):
                if not isinstance(output, dict):
                    self.errors.append(f"スタック '{stack_name}' のアウトプット {i} は辞書形式である必要があります")
                    valid = False
                    continue
                
                required_fields = ['name', 'description', 'value', 'export_name']
                for field in required_fields:
                    if field not in output:
                        self.errors.append(f"スタック '{stack_name}' のアウトプット {i} に必須フィールド '{field}' がありません")
                        valid = False
                
                # エクスポート名の命名規則チェック
                export_name = output.get('export_name', '')
                if export_name and not ('{ProjectName}' in export_name and '{Environment}' in export_name):
                    self.warnings.append(f"スタック '{stack_name}' のアウトプット '{output.get('name', 'unknown')}' のエクスポート名が命名規則に従っていません: {export_name}")
        
        return valid
    
    def validate_dependencies(self, dependencies: Dict[str, Any]) -> bool:
        """依存関係設定を検証"""
        valid = True
        
        for stack_name, deps in dependencies.items():
            if not isinstance(deps, list):
                self.errors.append(f"スタック '{stack_name}' の依存関係はリスト形式である必要があります")
                valid = False
                continue
            
            for i, dep in enumerate(deps):
                if not isinstance(dep, dict):
                    self.errors.append(f"スタック '{stack_name}' の依存関係 {i} は辞書形式である必要があります")
                    valid = False
                    continue
                
                required_fields = ['stack_name', 'required_outputs']
                for field in required_fields:
                    if field not in dep:
                        self.errors.append(f"スタック '{stack_name}' の依存関係 {i} に必須フィールド '{field}' がありません")
                        valid = False
                
                # required_outputsがリストかチェック
                if 'required_outputs' in dep and not isinstance(dep['required_outputs'], list):
                    self.errors.append(f"スタック '{stack_name}' の依存関係 {i} の 'required_outputs' はリスト形式である必要があります")
                    valid = False
                
                # optional_outputsがリストかチェック（存在する場合）
                if 'optional_outputs' in dep and dep['optional_outputs'] is not None and not isinstance(dep['optional_outputs'], list):
                    self.errors.append(f"スタック '{stack_name}' の依存関係 {i} の 'optional_outputs' はリスト形式である必要があります")
                    valid = False
        
        return valid
    
    def detect_circular_dependencies(self, dependencies: Dict[str, Any]) -> List[List[str]]:
        """循環依存関係を検出"""
        circular_deps = []
        
        def has_path(start: str, end: str, visited: Set[str], path: List[str]) -> bool:
            """startからendへのパスが存在するかチェック"""
            if start == end and len(path) > 1:
                circular_deps.append(path + [end])
                return True
            
            if start in visited:
                return False
            
            visited.add(start)
            
            if start in dependencies:
                for dep in dependencies[start]:
                    dep_stack = dep.get('stack_name')
                    if dep_stack and has_path(dep_stack, end, visited.copy(), path + [start]):
                        return True
            
            return False
        
        # 各スタックから循環依存をチェック
        all_stacks = set(dependencies.keys())
        for deps in dependencies.values():
            for dep in deps:
                dep_stack = dep.get('stack_name')
                if dep_stack:
                    all_stacks.add(dep_stack)
        
        for stack in all_stacks:
            if stack in dependencies:
                has_path(stack, stack, set(), [])
        
        return circular_deps
    
    def validate_output_dependency_consistency(self, config: Dict[str, Any]) -> bool:
        """アウトプットと依存関係の整合性を検証"""
        valid = True
        stack_outputs = config.get('stack_outputs', {})
        dependencies = config.get('dependencies', {})
        
        # 各依存関係で要求されるアウトプットが実際に定義されているかチェック
        for stack_name, deps in dependencies.items():
            for dep in deps:
                dep_stack_name = dep.get('stack_name')
                required_outputs = dep.get('required_outputs', [])
                optional_outputs = dep.get('optional_outputs', [])
                
                if dep_stack_name not in stack_outputs:
                    self.warnings.append(f"依存スタック '{dep_stack_name}' のアウトプット定義が見つかりません")
                    continue
                
                # 定義されているアウトプット名を取得
                defined_outputs = {output['name'] for output in stack_outputs[dep_stack_name]}
                
                # 必須アウトプットのチェック
                for required_output in required_outputs:
                    if required_output not in defined_outputs:
                        self.errors.append(f"スタック '{stack_name}' が要求する必須アウトプット '{required_output}' が依存スタック '{dep_stack_name}' に定義されていません")
                        valid = False
                
                # オプションアウトプットのチェック
                for optional_output in optional_outputs:
                    if optional_output not in defined_outputs:
                        self.warnings.append(f"スタック '{stack_name}' が要求するオプションアウトプット '{optional_output}' が依存スタック '{dep_stack_name}' に定義されていません")
        
        return valid
    
    def validate_export_name_uniqueness(self, stack_outputs: Dict[str, Any]) -> bool:
        """エクスポート名の一意性を検証"""
        valid = True
        export_names = {}
        
        for stack_name, outputs in stack_outputs.items():
            for output in outputs:
                export_name = output.get('export_name')
                if export_name:
                    if export_name in export_names:
                        self.errors.append(f"エクスポート名 '{export_name}' が重複しています: スタック '{stack_name}' と '{export_names[export_name]}'")
                        valid = False
                    else:
                        export_names[export_name] = stack_name
        
        return valid
    
    def generate_report(self) -> str:
        """検証レポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("Cross-Stack Configuration Validation Report")
        report.append("=" * 80)
        report.append("")
        
        # サマリー
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        
        if total_errors == 0 and total_warnings == 0:
            report.append("✓ 設定ファイルは正常です")
        else:
            report.append(f"エラー: {total_errors}")
            report.append(f"警告: {total_warnings}")
        
        report.append("")
        
        # エラー詳細
        if self.errors:
            report.append("エラー:")
            for error in self.errors:
                report.append(f"  ✗ {error}")
            report.append("")
        
        # 警告詳細
        if self.warnings:
            report.append("警告:")
            for warning in self.warnings:
                report.append(f"  ⚠ {warning}")
            report.append("")
        
        return "\n".join(report)
    
    def validate_all(self, config: Dict[str, Any]) -> bool:
        """全ての検証を実行"""
        if not self.validate_structure(config):
            return False
        
        valid = True
        
        # 各セクションの検証
        if not self.validate_stack_outputs(config.get('stack_outputs', {})):
            valid = False
        
        if not self.validate_dependencies(config.get('dependencies', {})):
            valid = False
        
        # 整合性チェック
        if not self.validate_output_dependency_consistency(config):
            valid = False
        
        if not self.validate_export_name_uniqueness(config.get('stack_outputs', {})):
            valid = False
        
        # 循環依存関係チェック
        circular_deps = self.detect_circular_dependencies(config.get('dependencies', {}))
        if circular_deps:
            for cycle in circular_deps:
                self.errors.append(f"循環依存関係が検出されました: {' -> '.join(cycle)}")
            valid = False
        
        return valid

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        config_path = "cross-stack-config.json"
    else:
        config_path = sys.argv[1]
    
    # 設定ファイルのパス解決
    if not Path(config_path).is_absolute():
        config_path = Path(__file__).parent / config_path
    
    validator = ConfigValidator()
    config = validator.load_config(str(config_path))
    
    if not config:
        print("設定ファイルの読み込みに失敗しました")
        sys.exit(1)
    
    # 検証実行
    is_valid = validator.validate_all(config)
    
    # レポート生成
    report = validator.generate_report()
    print(report)
    
    # レポートをファイルに保存
    output_path = "config-validation-report.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n検証レポートを保存しました: {output_path}")
    
    # 終了コード設定
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()