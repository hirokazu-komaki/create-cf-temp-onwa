#!/usr/bin/env python3
"""
Template Outputs Updater
既存のCloudFormationテンプレートにクロススタック対応のOutputsを追加
"""

import yaml
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def update_template_outputs(template_path: str, stack_name: str, config_path: str):
    """テンプレートのOutputsセクションを更新"""
    
    # 設定ファイルを読み込み
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # テンプレートを読み込み
    with open(template_path, 'r', encoding='utf-8') as f:
        template = yaml.safe_load(f)
    
    # 該当スタックのアウトプット設定を取得
    if stack_name not in config['stack_outputs']:
        print(f"Warning: {stack_name} の設定が見つかりません")
        return
    
    outputs_config = config['stack_outputs'][stack_name]
    
    # Outputsセクションを構築
    outputs = {}
    for output_config in outputs_config:
        output_def = {
            'Description': output_config['description'],
            'Value': output_config['value']
        }
        
        # Export設定
        if output_config['export_name']:
            export_name = output_config['export_name'].replace('{ProjectName}', '${ProjectName}').replace('{Environment}', '${Environment}')
            output_def['Export'] = {'Name': export_name}
        
        # Condition設定
        if output_config['conditions']:
            if len(output_config['conditions']) == 1:
                output_def['Condition'] = output_config['conditions'][0]
            else:
                # 複数条件の場合はOrで結合（設定によってはAndも可能）
                output_def['Condition'] = {'Fn::Or': [
                    {'Condition': condition} for condition in output_config['conditions']
                ]}
        
        outputs[output_config['name']] = output_def
    
    # テンプレートのOutputsセクションを更新
    template['Outputs'] = outputs
    
    # テンプレートを保存
    with open(template_path, 'w', encoding='utf-8') as f:
        yaml.dump(template, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Updated outputs for {template_path}")

def add_import_parameters(template_path: str, stack_name: str, config_path: str):
    """テンプレートにインポートパラメータを追加"""
    
    # 設定ファイルを読み込み
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # テンプレートを読み込み
    with open(template_path, 'r', encoding='utf-8') as f:
        template = yaml.safe_load(f)
    
    # 該当スタックの依存関係設定を取得
    if stack_name not in config['dependencies']:
        print(f"Info: {stack_name} には依存関係がありません")
        return
    
    dependencies = config['dependencies'][stack_name]
    
    # Parametersセクションが存在しない場合は作成
    if 'Parameters' not in template:
        template['Parameters'] = {}
    
    # 各依存関係からインポートパラメータを生成
    for dep in dependencies:
        dep_stack_name = dep['stack_name']
        
        # 必須アウトプット用のパラメータ
        for output_name in dep['required_outputs']:
            param_name = f"Import{output_name.replace('-', '')}"
            export_name = f"${{ProjectName}}-${{Environment}}-{output_name.lower().replace('_', '-')}"
            
            template['Parameters'][param_name] = {
                'Type': 'String',
                'Description': f"Import {output_name} from {dep_stack_name} stack",
                'Default': {'Fn::ImportValue': export_name}
            }
        
        # オプションアウトプット用のパラメータ
        for output_name in dep.get('optional_outputs', []):
            param_name = f"Import{output_name.replace('-', '')}Optional"
            export_name = f"${{ProjectName}}-${{Environment}}-{output_name.lower().replace('_', '-')}"
            
            template['Parameters'][param_name] = {
                'Type': 'String',
                'Description': f"Optional import {output_name} from {dep_stack_name} stack",
                'Default': ''
            }
    
    # テンプレートを保存
    with open(template_path, 'w', encoding='utf-8') as f:
        yaml.dump(template, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Added import parameters for {template_path}")

def main():
    """メイン処理"""
    config_path = Path(__file__).parent / 'cross-stack-config.json'
    templates_base = Path(__file__).parent.parent
    
    # テンプレートとスタック名のマッピング
    template_mappings = {
        'foundation/iam/iam-roles-policies.yaml': 'foundation-iam',
        'foundation/kms/kms-template.yaml': 'foundation-kms',
        'networking/vpc/vpc-template.yaml': 'networking-vpc',
        'compute/ec2/ec2-autoscaling.yaml': 'compute-ec2',
        'compute/lambda/lambda-function.yaml': 'compute-lambda',
        'networking/elb/elb-template.yaml': 'networking-elb',
        'integration/api-gateway/api-gateway-template.yaml': 'integration-api-gateway',
        'integration/cloudwatch/cloudwatch-template.yaml': 'integration-cloudwatch'
    }
    
    # 各テンプレートを更新
    for template_rel_path, stack_name in template_mappings.items():
        template_path = templates_base / template_rel_path
        
        if template_path.exists():
            print(f"\nProcessing {template_path}")
            
            # Outputsセクションを更新
            update_template_outputs(str(template_path), stack_name, str(config_path))
            
            # インポートパラメータを追加
            add_import_parameters(str(template_path), stack_name, str(config_path))
        else:
            print(f"Warning: Template not found: {template_path}")
    
    print("\nAll templates have been updated with cross-stack support!")

if __name__ == "__main__":
    main()