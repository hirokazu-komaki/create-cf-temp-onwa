#!/usr/bin/env python3
"""
Master Integration Test Script
CloudFormation Parameter Migration - Task 7.2 Implementation

このスクリプトはタスク7.2「統合テストとCI/CD検証」の完全な実装です。
GitHub Actionsワークフローでの完全テスト、デプロイメントプロセスの検証、
監視とログ設定の確認を包括的に実行します。
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import time
from datetime import datetime
import concurrent.futures
import threading

class MasterIntegrationTester:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.results_dir = self.project_root / "integration-test-results"
        self.results_dir.mkdir(exist_ok=True)
        
        # AWS プロファイル設定
        os.environ['AWS_PROFILE'] = 'mame-local-wani'
        os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
        
        # テスト実行時刻
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 実行するテストスクリプト
        self.test_scripts = {
            'ci_cd_integration': {
                'script': 'ci-cd-integration-test.py',
                'description': 'CI/CD統合テスト',
                'timeout': 300
            },
            'github_actions_workflow': {
                'script': 'github-actions-workflow-validator.py',
                'description': 'GitHub Actionsワークフロー検証',
                'timeout': 180
            },
            'deployment_process': {
                'script': 'deployment-process-validator.py',
                'description': 'デプロイメントプロセス検証',
                'timeout': 600
            },
            'monitoring_logging': {
                'script': 'monitoring-logging-validator.py',
                'description': '監視・ログ設定検証',
                'timeout': 240
            },
            'phase3_final_validation': {
                'script': 'phase3-final-validation.py',
                'description': 'Phase 3最終検証',
                'timeout': 300
            }
        }
        
        self.test_results = {}
        self.overall_success = True
        
    def log_info(self, message: str):
        """情報メッセージを記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ℹ️  {message}")
        
    def log_success(self, message: str):
        """成功メッセージを記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {message}")
        
    def log_warning(self, message: str):
        """警告メッセージを記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚠️  {message}")
        
    def log_error(self, message: str):
        """エラーメッセージを記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {message}")

    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """前提条件の確認"""
        self.log_info("前提条件を確認中...")
        
        issues = []
        
        # Pythonバージョンの確認
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            issues.append(f"Python 3.8以上が必要です（現在: {python_version.major}.{python_version.minor}）")
        
        # 必要なPythonパッケージの確認
        required_packages = ['boto3', 'yaml', 'jsonschema']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"必要なパッケージが見つかりません: {package}")
        
        # テストスクリプトの存在確認
        for test_name, test_config in self.test_scripts.items():
            script_path = self.scripts_dir / test_config['script']
            if not script_path.exists():
                issues.append(f"テストスクリプトが見つかりません: {script_path}")
        
        # 設定ファイルの存在確認
        config_files = [
            "test-parameters-basic.json",
            "test-parameters-advanced.json",
            "test-parameters-enterprise.json"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if not config_path.exists():
                issues.append(f"設定ファイルが見つかりません: {config_path}")
        
        # CloudFormationテンプレートの存在確認
        template_path = self.project_root / "cf-templates" / "compute" / "ec2" / "ec2-autoscaling.yaml"
        if not template_path.exists():
            issues.append(f"CloudFormationテンプレートが見つかりません: {template_path}")
        
        # GitHub Actionsワークフローの存在確認
        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            issues.append(f"GitHub Actionsワークフローディレクトリが見つかりません: {workflows_dir}")
        else:
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            active_workflows = [f for f in workflow_files if not f.name.endswith('.disabled')]
            if not active_workflows:
                issues.append("有効なGitHub Actionsワークフローファイルが見つかりません")
        
        if issues:
            self.log_error("前提条件チェックで問題が見つかりました")
            for issue in issues:
                self.log_error(f"  - {issue}")
            return False, issues
        else:
            self.log_success("すべての前提条件が満たされています")
            return True, []

    def run_single_test(self, test_name: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """単一テストの実行"""
        script_path = self.scripts_dir / test_config['script']
        description = test_config['description']
        timeout = test_config['timeout']
        
        self.log_info(f"実行中: {description}")
        
        start_time = time.time()
        
        try:
            # テストスクリプトを実行
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 結果の解析
            success = result.returncode == 0
            
            test_result = {
                'test_name': test_name,
                'description': description,
                'success': success,
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                self.log_success(f"完了: {description} ({execution_time:.1f}秒)")
            else:
                self.log_error(f"失敗: {description} ({execution_time:.1f}秒)")
                self.log_error(f"エラー出力: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.log_error(f"タイムアウト: {description} ({timeout}秒)")
            
            return {
                'test_name': test_name,
                'description': description,
                'success': False,
                'execution_time': execution_time,
                'return_code': -1,
                'stdout': '',
                'stderr': f'テストがタイムアウトしました（{timeout}秒）',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.log_error(f"実行エラー: {description} - {str(e)}")
            
            return {
                'test_name': test_name,
                'description': description,
                'success': False,
                'execution_time': execution_time,
                'return_code': -2,
                'stdout': '',
                'stderr': f'テスト実行エラー: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def run_tests_sequentially(self) -> Dict[str, Any]:
        """テストを順次実行"""
        self.log_info("テストを順次実行中...")
        
        for test_name, test_config in self.test_scripts.items():
            result = self.run_single_test(test_name, test_config)
            self.test_results[test_name] = result
            
            if not result['success']:
                self.overall_success = False
        
        return self.test_results

    def run_tests_parallel(self) -> Dict[str, Any]:
        """テストを並列実行（独立性のあるテストのみ）"""
        self.log_info("テストを並列実行中...")
        
        # 並列実行可能なテスト（AWS APIを使用しないもの）
        parallel_tests = ['github_actions_workflow']
        
        # 順次実行が必要なテスト（AWS APIを使用するもの）
        sequential_tests = ['deployment_process', 'monitoring_logging', 'phase3_final_validation', 'ci_cd_integration']
        
        # 並列実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            parallel_futures = {}
            
            for test_name in parallel_tests:
                if test_name in self.test_scripts:
                    future = executor.submit(self.run_single_test, test_name, self.test_scripts[test_name])
                    parallel_futures[future] = test_name
            
            # 並列テストの結果を収集
            for future in concurrent.futures.as_completed(parallel_futures):
                test_name = parallel_futures[future]
                result = future.result()
                self.test_results[test_name] = result
                
                if not result['success']:
                    self.overall_success = False
        
        # 順次実行
        for test_name in sequential_tests:
            if test_name in self.test_scripts:
                result = self.run_single_test(test_name, self.test_scripts[test_name])
                self.test_results[test_name] = result
                
                if not result['success']:
                    self.overall_success = False
        
        return self.test_results

    def generate_summary_report(self) -> Dict[str, Any]:
        """サマリーレポートの生成"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_execution_time = sum(result['execution_time'] for result in self.test_results.values())
        
        summary = {
            'test_session': {
                'timestamp': self.test_timestamp,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_execution_time,
                'overall_success': self.overall_success
            },
            'test_results': self.test_results,
            'environment_info': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform,
                'working_directory': str(self.project_root)
            }
        }
        
        return summary

    def print_summary_report(self, summary: Dict[str, Any]):
        """サマリーレポートの表示"""
        session = summary['test_session']
        
        print("\n" + "=" * 100)
        print("📊 統合テスト実行結果サマリー - Task 7.2: 統合テストとCI/CD検証")
        print("=" * 100)
        
        print(f"実行時刻: {session['timestamp']}")
        print(f"総テスト数: {session['total_tests']}")
        print(f"成功: {session['passed_tests']}")
        print(f"失敗: {session['failed_tests']}")
        print(f"成功率: {session['success_rate']:.1f}%")
        print(f"総実行時間: {session['total_execution_time']:.1f}秒")
        
        print("\n📋 個別テスト結果:")
        print("-" * 80)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{result['description']}: {status} ({result['execution_time']:.1f}秒)")
            
            if not result['success']:
                # エラーの要約を表示
                stderr_lines = result['stderr'].split('\n')
                error_summary = stderr_lines[0] if stderr_lines else "不明なエラー"
                print(f"  エラー: {error_summary}")
        
        print("\n" + "=" * 100)
        if self.overall_success:
            print("🎉 すべての統合テストが成功しました！")
            print("✅ GitHub Actionsワークフローは正常に動作します")
            print("✅ デプロイメントプロセスは適切に設定されています")
            print("✅ 監視とログ設定は正常です")
            print("✅ Phase 3の新パラメータ構造は完全に機能しています")
            print("\n🚀 本番環境へのデプロイメント準備が完了しました！")
        else:
            print("❌ 一部の統合テストが失敗しました")
            print("詳細なエラー情報は個別のテスト結果ファイルを確認してください")
            print("問題を解決してから再実行してください")
        print("=" * 100)

    def save_detailed_results(self, summary: Dict[str, Any]):
        """詳細結果の保存"""
        # メインサマリーファイル
        summary_file = self.results_dir / f"integration-test-summary-{self.test_timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 個別テスト結果ファイル
        for test_name, result in self.test_results.items():
            result_file = self.results_dir / f"{test_name}-result-{self.test_timestamp}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 最新結果へのシンボリックリンク（Windows対応）
        latest_summary = self.results_dir / "latest-integration-test-summary.json"
        try:
            if latest_summary.exists():
                latest_summary.unlink()
            # Windowsではコピーを作成
            import shutil
            shutil.copy2(summary_file, latest_summary)
        except Exception:
            pass  # シンボリックリンク作成に失敗しても続行
        
        self.log_success(f"詳細結果を保存しました: {summary_file}")
        
        # 結果ファイルのリスト表示
        print(f"\n📄 保存された結果ファイル:")
        print(f"  - メインサマリー: {summary_file}")
        for test_name in self.test_results.keys():
            result_file = self.results_dir / f"{test_name}-result-{self.test_timestamp}.json"
            print(f"  - {test_name}: {result_file}")

    def cleanup_old_results(self, keep_days: int = 7):
        """古い結果ファイルのクリーンアップ"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (keep_days * 24 * 60 * 60)
            
            cleaned_files = 0
            for result_file in self.results_dir.glob("*-result-*.json"):
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    cleaned_files += 1
            
            for summary_file in self.results_dir.glob("integration-test-summary-*.json"):
                if summary_file.stat().st_mtime < cutoff_time:
                    summary_file.unlink()
                    cleaned_files += 1
            
            if cleaned_files > 0:
                self.log_info(f"古い結果ファイル {cleaned_files} 個をクリーンアップしました")
                
        except Exception as e:
            self.log_warning(f"結果ファイルクリーンアップエラー: {str(e)}")

    def run_comprehensive_integration_test(self, parallel: bool = False) -> bool:
        """包括的な統合テストの実行"""
        print("🚀 Task 7.2: 統合テストとCI/CD検証 - 実行開始")
        print("=" * 100)
        print("GitHub Actionsワークフローでの完全テスト")
        print("デプロイメントプロセスの検証")
        print("監視とログ設定の確認")
        print("=" * 100)
        
        start_time = time.time()
        
        try:
            # 前提条件の確認
            prerequisites_ok, issues = self.check_prerequisites()
            if not prerequisites_ok:
                self.log_error("前提条件が満たされていません。テストを中止します。")
                return False
            
            # 古い結果ファイルのクリーンアップ
            self.cleanup_old_results()
            
            # テストの実行
            if parallel:
                self.run_tests_parallel()
            else:
                self.run_tests_sequentially()
            
            # 結果の生成と保存
            summary = self.generate_summary_report()
            self.save_detailed_results(summary)
            self.print_summary_report(summary)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n⏱️  総実行時間: {total_time:.1f}秒")
            
            return self.overall_success
            
        except KeyboardInterrupt:
            self.log_error("テスト実行が中断されました")
            return False
        except Exception as e:
            self.log_error(f"統合テスト実行エラー: {str(e)}")
            return False

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Task 7.2: 統合テストとCI/CD検証')
    parser.add_argument('--parallel', action='store_true', 
                       help='可能なテストを並列実行する')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細な出力を表示する')
    
    args = parser.parse_args()
    
    tester = MasterIntegrationTester()
    
    try:
        success = tester.run_comprehensive_integration_test(parallel=args.parallel)
        
        if success:
            print("\n🎯 Task 7.2 完了: すべての統合テストが成功しました")
            sys.exit(0)
        else:
            print("\n❌ Task 7.2 失敗: 一部のテストが失敗しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Task 7.2 実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()