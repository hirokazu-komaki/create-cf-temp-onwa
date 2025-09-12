#!/usr/bin/env python3
"""
GitHub Actions Workflow Validator
CloudFormation Parameter Migration - Workflow Testing and Validation

このスクリプトはGitHub Actionsワークフローの完全性と正確性を検証します。
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import re
import tempfile

# GitHub ActionsワークフローにはPyYAMLを使用
import yaml

class GitHubActionsValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.test_results = {}
        
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

    def validate_workflow_syntax(self, workflow_file: Path) -> Tuple[bool, List[str]]:
        """ワークフローファイルのYAML構文を検証"""
        issues = []
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
            
            if not isinstance(workflow, dict):
                issues.append("ワークフローファイルが有効なYAMLオブジェクトではありません")
                return False, issues
            
            self.log_success(f"YAML構文検証成功: {workflow_file.name}")
            return True, issues
            
        except Exception as e:
            issues.append(f"YAML構文エラー: {e}")
            return False, issues

    def validate_workflow_structure(self, workflow_file: Path) -> Tuple[bool, List[str]]:
        """ワークフロー構造の検証"""
        issues = []
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
            
            # 必須フィールドの確認
            required_fields = ['name', 'jobs']
            for field in required_fields:
                if field not in workflow:
                    issues.append(f"必須フィールドが不足: {field}")
            
            # onフィールドの確認（YAMLパーサーがTrueとして解釈する場合もある）
            if 'on' not in workflow and True not in workflow:
                issues.append("必須フィールドが不足: on")
            
            # nameフィールドの検証
            if 'name' in workflow:
                if not isinstance(workflow['name'], str) or not workflow['name'].strip():
                    issues.append("nameフィールドが空または無効です")
            
            # onフィールドの検証（YAMLパーサーがTrueとして解釈する場合もある）
            triggers = workflow.get('on') or workflow.get(True)
            if triggers is not None:
                if isinstance(triggers, str):
                    triggers = {triggers: {}}
                elif not isinstance(triggers, dict):
                    issues.append("onフィールドの形式が無効です")
                else:
                    # 推奨トリガーの確認
                    recommended_triggers = ['push', 'pull_request']
                    has_recommended = any(trigger in triggers for trigger in recommended_triggers)
                    if not has_recommended:
                        issues.append("推奨トリガー（push、pull_request）が設定されていません")
            
            # jobsフィールドの検証
            if 'jobs' in workflow:
                jobs = workflow['jobs']
                if not isinstance(jobs, dict) or not jobs:
                    issues.append("jobsフィールドが空または無効です")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"ワークフロー構造検証エラー: {e}")
            return False, issues

    def run_validation(self) -> Dict[str, Any]:
        """GitHub Actionsワークフロー検証の実行"""
        print("🚀 GitHub Actionsワークフロー検証開始")
        print("=" * 80)
        
        results = {
            'success': True,
            'workflows': {},
            'summary': {
                'total_workflows': 0,
                'valid_workflows': 0,
                'issues_found': []
            }
        }
        
        # ワークフローファイルの検出
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        if not workflow_files:
            self.log_warning("ワークフローファイルが見つかりません")
            results['success'] = False
            return results
        
        self.log_info(f"発見されたワークフローファイル: {len(workflow_files)}")
        
        for workflow_file in workflow_files:
            self.log_info(f"検証中: {workflow_file.name}")
            print("-" * 60)
            
            workflow_result = {
                'yaml_syntax': True,
                'workflow_structure': True,
                'issues': []
            }
            
            # YAML構文検証
            syntax_ok, syntax_issues = self.validate_workflow_syntax(workflow_file)
            workflow_result['yaml_syntax'] = syntax_ok
            workflow_result['issues'].extend(syntax_issues)
            
            # ワークフロー構造検証
            if syntax_ok:
                structure_ok, structure_issues = self.validate_workflow_structure(workflow_file)
                workflow_result['workflow_structure'] = structure_ok
                workflow_result['issues'].extend(structure_issues)
            
            results['workflows'][workflow_file.name] = workflow_result
            results['summary']['total_workflows'] += 1
            
            if syntax_ok and workflow_result['workflow_structure']:
                results['summary']['valid_workflows'] += 1
            else:
                results['success'] = False
                results['summary']['issues_found'].extend(workflow_result['issues'])
        
        # 結果サマリーの表示
        print("\n" + "=" * 80)
        print("📊 GitHub Actionsワークフロー検証結果")
        print("=" * 80)
        
        for workflow_name, result in results['workflows'].items():
            status = "✅" if result['yaml_syntax'] and result['workflow_structure'] else "❌"
            print(f"\n📄 {workflow_name}: {status}")
            print(f"  yaml_syntax: {'✅' if result['yaml_syntax'] else '❌'}")
            print(f"  workflow_structure: {'✅' if result['workflow_structure'] else '❌'}")
            
            if result['issues']:
                for issue in result['issues']:
                    print(f"    - {issue}")
        
        print("\n" + "=" * 80)
        if results['success']:
            self.log_success("すべてのワークフロー検証が成功しました")
        else:
            self.log_error("一部のワークフロー検証が失敗しました")
            print("上記の問題を解決してから再実行してください")
        print("=" * 80)
        
        return results

def main():
    """メイン処理"""
    validator = GitHubActionsValidator()
    
    try:
        results = validator.run_validation()
        
        # 結果をJSONファイルに保存
        results_file = validator.project_root / "github-actions-validation-results.json"
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