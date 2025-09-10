#!/usr/bin/env python3
"""
マルチアカウントAWS認証情報セットアップスクリプト

このスクリプトは、複数のAWSアカウント用の認証情報を管理し、
GitHub Secretsの設定に必要な情報を生成します。
"""

import json
import boto3
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import yaml


class MultiAccountCredentialManager:
    """複数AWSアカウントの認証情報管理クラス"""
    
    def __init__(self):
        self.accounts = {}
        self.config_file = Path('.aws-accounts-config.json')
        
    def load_config(self):
        """設定ファイルから既存の設定を読み込み"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.accounts = json.load(f)
                print(f"✅ Loaded existing config from {self.config_file}")
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
        else:
            print("ℹ️  No existing config found, starting fresh")
    
    def save_config(self):
        """設定をファイルに保存"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.accounts, f, indent=2)
            print(f"✅ Config saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def add_account(self, account_id: str, account_name: str, access_key: str, 
                   secret_key: str, role_arn: str = None, region: str = 'us-east-1'):
        """新しいAWSアカウントを追加"""
        
        # アカウントIDの検証
        if not account_id.isdigit() or len(account_id) != 12:
            raise ValueError("Account ID must be a 12-digit number")
        
        # 認証情報の検証
        try:
            client = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # 認証情報の有効性を確認
            response = client.get_caller_identity()
            actual_account_id = response['Account']
            
            if actual_account_id != account_id:
                print(f"⚠️  Warning: Provided account ID ({account_id}) doesn't match actual account ID ({actual_account_id})")
                account_id = actual_account_id
            
            print(f"✅ Credentials validated for account {account_id}")
            
        except Exception as e:
            print(f"❌ Error validating credentials: {e}")
            raise
        
        # アカウント情報を保存
        self.accounts[account_id] = {
            'name': account_name,
            'access_key': access_key,
            'secret_key': secret_key,
            'role_arn': role_arn,
            'region': region,
            'validated': True
        }
        
        print(f"✅ Added account {account_id} ({account_name})")
    
    def remove_account(self, account_id: str):
        """アカウントを削除"""
        if account_id in self.accounts:
            account_name = self.accounts[account_id]['name']
            del self.accounts[account_id]
            print(f"✅ Removed account {account_id} ({account_name})")
        else:
            print(f"❌ Account {account_id} not found")
    
    def list_accounts(self):
        """設定されているアカウントを一覧表示"""
        if not self.accounts:
            print("No accounts configured")
            return
        
        print("\n📋 Configured AWS Accounts:")
        print("=" * 60)
        for account_id, config in self.accounts.items():
            status = "✅ Validated" if config.get('validated') else "⚠️  Not validated"
            print(f"Account ID: {account_id}")
            print(f"Name: {config['name']}")
            print(f"Region: {config['region']}")
            print(f"Role ARN: {config.get('role_arn', 'Not specified')}")
            print(f"Status: {status}")
            print("-" * 60)
    
    def generate_github_secrets_config(self) -> Dict[str, str]:
        """GitHub Secrets用の設定を生成"""
        secrets = {}
        
        for account_id, config in self.accounts.items():
            prefix = f"AWS_ACCESS_KEY_ID_{account_id}"
            secrets[f"AWS_ACCESS_KEY_ID_{account_id}"] = config['access_key']
            secrets[f"AWS_SECRET_ACCESS_KEY_{account_id}"] = config['secret_key']
            
            if config.get('role_arn'):
                secrets[f"AWS_DEPLOYMENT_ROLE_ARN_{account_id}"] = config['role_arn']
        
        return secrets
    
    def export_github_secrets_script(self, output_file: str = 'setup-github-secrets.sh'):
        """GitHub Secrets設定用のシェルスクリプトを生成"""
        secrets = self.generate_github_secrets_config()
        
        script_content = """#!/bin/bash
# GitHub Secrets設定スクリプト
# 使用方法: ./setup-github-secrets.sh <OWNER> <REPO>
# 例: ./setup-github-secrets.sh myorg myrepo

if [ $# -ne 2 ]; then
    echo "Usage: $0 <OWNER> <REPO>"
    echo "Example: $0 myorg myrepo"
    exit 1
fi

OWNER=$1
REPO=$2

echo "Setting up GitHub Secrets for $OWNER/$REPO"
echo "Note: You need to have 'gh' CLI installed and authenticated"

"""
        
        for secret_name, secret_value in secrets.items():
            # セキュリティのため、実際の値は表示せず、プレースホルダーを使用
            masked_value = secret_value[:4] + "*" * (len(secret_value) - 8) + secret_value[-4:]
            script_content += f"""
# Setting {secret_name}
echo "Setting {secret_name} (value: {masked_value})"
gh secret set {secret_name} --body "{secret_value}" --repo $OWNER/$REPO
"""
        
        script_content += """
echo "✅ All secrets have been set!"
echo "Please verify the secrets in your GitHub repository settings."
"""
        
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # 実行権限を付与
        os.chmod(output_file, 0o755)
        
        print(f"✅ GitHub Secrets setup script generated: {output_file}")
        print(f"Run: ./{output_file} <OWNER> <REPO>")
    
    def export_terraform_config(self, output_file: str = 'aws-accounts.tf'):
        """Terraform設定ファイルを生成"""
        tf_content = """# AWS Accounts Configuration for Terraform
# This file defines multiple AWS providers for different accounts

"""
        
        for account_id, config in self.accounts.items():
            account_name = config['name'].lower().replace(' ', '_')
            tf_content += f"""
# Provider for {config['name']} ({account_id})
provider "aws" {{
  alias  = "{account_name}"
  region = "{config['region']}"
  
  assume_role {{
    role_arn = "{config.get('role_arn', f'arn:aws:iam::{account_id}:role/TerraformRole')}"
  }}
  
  default_tags {{
    tags = {{
      ManagedBy = "Terraform"
      Account   = "{config['name']}"
      AccountId = "{account_id}"
    }}
  }}
}}
"""
        
        with open(output_file, 'w') as f:
            f.write(tf_content)
        
        print(f"✅ Terraform configuration generated: {output_file}")
    
    def validate_all_accounts(self):
        """すべてのアカウントの認証情報を検証"""
        print("🔍 Validating all account credentials...")
        
        for account_id, config in self.accounts.items():
            try:
                client = boto3.client(
                    'sts',
                    aws_access_key_id=config['access_key'],
                    aws_secret_access_key=config['secret_key'],
                    region_name=config['region']
                )
                
                response = client.get_caller_identity()
                actual_account_id = response['Account']
                
                if actual_account_id == account_id:
                    print(f"✅ {config['name']} ({account_id}): Valid")
                    self.accounts[account_id]['validated'] = True
                else:
                    print(f"❌ {config['name']} ({account_id}): Account ID mismatch")
                    self.accounts[account_id]['validated'] = False
                
            except Exception as e:
                print(f"❌ {config['name']} ({account_id}): {e}")
                self.accounts[account_id]['validated'] = False
    
    def scan_config_files_for_accounts(self, directory: str = 'cf-templates') -> List[str]:
        """設定ファイルからAWSアカウントIDを抽出"""
        found_accounts = set()
        config_dir = Path(directory)
        
        if not config_dir.exists():
            print(f"❌ Directory {directory} not found")
            return []
        
        # JSON設定ファイルを検索
        config_files = list(config_dir.rglob('*-config-*.json'))
        
        print(f"🔍 Scanning {len(config_files)} config files for AWS account references...")
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # AWSアカウントIDを検索
                account_keys = ['AWSAccount', 'TargetAccount', 'AccountId']
                
                for key in account_keys:
                    if key in config.get('Parameters', {}):
                        account_id = str(config['Parameters'][key])
                        if account_id.isdigit() and len(account_id) == 12:
                            found_accounts.add(account_id)
                            print(f"  Found account {account_id} in {config_file}")
                    elif key in config:
                        account_id = str(config[key])
                        if account_id.isdigit() and len(account_id) == 12:
                            found_accounts.add(account_id)
                            print(f"  Found account {account_id} in {config_file}")
                
            except Exception as e:
                print(f"⚠️  Error reading {config_file}: {e}")
        
        return sorted(list(found_accounts))
    
    def interactive_setup(self):
        """対話的なセットアップ"""
        print("🚀 Interactive AWS Multi-Account Setup")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Add new account")
            print("2. Remove account")
            print("3. List accounts")
            print("4. Validate all accounts")
            print("5. Scan config files for accounts")
            print("6. Generate GitHub Secrets script")
            print("7. Generate Terraform config")
            print("8. Save and exit")
            print("9. Exit without saving")
            
            choice = input("\nSelect option (1-9): ").strip()
            
            if choice == '1':
                self._interactive_add_account()
            elif choice == '2':
                self._interactive_remove_account()
            elif choice == '3':
                self.list_accounts()
            elif choice == '4':
                self.validate_all_accounts()
            elif choice == '5':
                accounts = self.scan_config_files_for_accounts()
                if accounts:
                    print(f"Found accounts: {', '.join(accounts)}")
                    if input("Add missing accounts? (y/n): ").lower() == 'y':
                        for account_id in accounts:
                            if account_id not in self.accounts:
                                print(f"\nSetting up account {account_id}:")
                                self._interactive_add_account(account_id)
                else:
                    print("No accounts found in config files")
            elif choice == '6':
                filename = input("Output filename (default: setup-github-secrets.sh): ").strip()
                if not filename:
                    filename = 'setup-github-secrets.sh'
                self.export_github_secrets_script(filename)
            elif choice == '7':
                filename = input("Output filename (default: aws-accounts.tf): ").strip()
                if not filename:
                    filename = 'aws-accounts.tf'
                self.export_terraform_config(filename)
            elif choice == '8':
                self.save_config()
                print("👋 Configuration saved. Goodbye!")
                break
            elif choice == '9':
                print("👋 Exiting without saving. Goodbye!")
                break
            else:
                print("❌ Invalid option. Please try again.")
    
    def _interactive_add_account(self, account_id: str = None):
        """対話的なアカウント追加"""
        try:
            if not account_id:
                account_id = input("AWS Account ID (12 digits): ").strip()
            
            if account_id in self.accounts:
                print(f"⚠️  Account {account_id} already exists")
                if input("Update existing account? (y/n): ").lower() != 'y':
                    return
            
            account_name = input("Account name (e.g., 'Production', 'Staging'): ").strip()
            access_key = input("AWS Access Key ID: ").strip()
            secret_key = input("AWS Secret Access Key: ").strip()
            role_arn = input("Deployment Role ARN (optional): ").strip()
            region = input("Default region (default: us-east-1): ").strip()
            
            if not region:
                region = 'us-east-1'
            
            self.add_account(account_id, account_name, access_key, secret_key, 
                           role_arn if role_arn else None, region)
            
        except Exception as e:
            print(f"❌ Error adding account: {e}")
    
    def _interactive_remove_account(self):
        """対話的なアカウント削除"""
        if not self.accounts:
            print("No accounts to remove")
            return
        
        print("\nConfigured accounts:")
        for account_id, config in self.accounts.items():
            print(f"  {account_id}: {config['name']}")
        
        account_id = input("\nEnter Account ID to remove: ").strip()
        self.remove_account(account_id)


def main():
    parser = argparse.ArgumentParser(description='Multi-Account AWS Credentials Manager')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List configured accounts')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate all account credentials')
    parser.add_argument('--scan', '-s', type=str, metavar='DIR',
                       help='Scan directory for AWS account references')
    parser.add_argument('--github-secrets', '-g', type=str, metavar='FILE',
                       help='Generate GitHub Secrets setup script')
    parser.add_argument('--terraform', '-t', type=str, metavar='FILE',
                       help='Generate Terraform configuration')
    
    args = parser.parse_args()
    
    manager = MultiAccountCredentialManager()
    manager.load_config()
    
    if args.interactive:
        manager.interactive_setup()
    elif args.list:
        manager.list_accounts()
    elif args.validate:
        manager.validate_all_accounts()
        manager.save_config()
    elif args.scan:
        accounts = manager.scan_config_files_for_accounts(args.scan)
        if accounts:
            print(f"Found AWS accounts: {', '.join(accounts)}")
        else:
            print("No AWS accounts found")
    elif args.github_secrets:
        manager.export_github_secrets_script(args.github_secrets)
    elif args.terraform:
        manager.export_terraform_config(args.terraform)
    else:
        print("No action specified. Use --help for options or --interactive for interactive mode.")


if __name__ == '__main__':
    main()