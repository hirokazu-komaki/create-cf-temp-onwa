#!/usr/bin/env python3
"""
Cross-Stack Reference Manager
Well-Architected準拠CloudFormationテンプレート用のクロススタック参照管理ユーティリティ
"""

import json
import yaml
import boto3
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class StackOutput:
    """スタックアウトプット情報"""
    name: str
    description: str
    value: str
    export_name: str
    conditions: Optional[List[str]] = None

@dataclass
class StackDependency:
    """スタック依存関係情報"""
    stack_name: str
    required_outputs: List[str]
    optional_outputs: List[str] = None

class CrossStackManager:
    """クロススタック参照管理クラス"""
    
    def __init__(self, region: str = 'us-east-1', profile: str = 'mame-local-wani'):
        self.region = region
        session = boto3.Session(profile_name=profile)
        self.cf_client = session.client('cloudformation', region_name=region)
        self.stack_outputs = {}
        self.dependencies = {}
    
    def register_stack_outputs(self, stack_name: str, outputs: List[StackOutput]):
        """スタックのアウトプットを登録"""
        self.stack_outputs[stack_name] = outputs
    
    def register_dependency(self, stack_name: str, dependency: StackDependency):
        """スタック依存関係を登録"""
        if stack_name not in self.dependencies:
            self.dependencies[stack_name] = []
        self.dependencies[stack_name].append(dependency)
    
    def validate_dependencies(self, stack_name: str) -> Dict[str, Any]:
        """依存関係の検証"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_outputs': []
        }
        
        if stack_name not in self.dependencies:
            return validation_result
        
        for dependency in self.dependencies[stack_name]:
            # 依存スタックの存在確認
            try:
                response = self.cf_client.describe_stacks(StackName=dependency.stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
                
                if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                    validation_result['errors'].append(
                        f"依存スタック '{dependency.stack_name}' のステータスが不正: {stack_status}"
                    )
                    validation_result['valid'] = False
                
                # アウトプットの存在確認
                stack_outputs = response['Stacks'][0].get('Outputs', [])
                available_outputs = {output['OutputKey'] for output in stack_outputs}
                
                for required_output in dependency.required_outputs:
                    if required_output not in available_outputs:
                        validation_result['missing_outputs'].append(
                            f"必須アウトプット '{required_output}' が依存スタック '{dependency.stack_name}' に存在しません"
                        )
                        validation_result['valid'] = False
                
                if dependency.optional_outputs:
                    for optional_output in dependency.optional_outputs:
                        if optional_output not in available_outputs:
                            validation_result['warnings'].append(
                                f"オプションアウトプット '{optional_output}' が依存スタック '{dependency.stack_name}' に存在しません"
                            )
            
            except self.cf_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ValidationError':
                    validation_result['errors'].append(
                        f"依存スタック '{dependency.stack_name}' が存在しません"
                    )
                    validation_result['valid'] = False
                else:
                    raise
        
        return validation_result
    
    def generate_import_parameters(self, stack_name: str, project_name: str, environment: str) -> Dict[str, Any]:
        """インポートパラメータの生成"""
        import_params = {}
        
        if stack_name not in self.dependencies:
            return import_params
        
        for dependency in self.dependencies[stack_name]:
            for output_name in dependency.required_outputs:
                export_name = f"{project_name}-{environment}-{output_name}"
                import_params[f"Import{output_name}"] = {
                    "Type": "String",
                    "Description": f"Import {output_name} from {dependency.stack_name}",
                    "Default": {"Fn::ImportValue": export_name}
                }
        
        return import_params
    
    def generate_outputs_section(self, stack_outputs: List[StackOutput], project_name: str, environment: str) -> Dict[str, Any]:
        """Outputsセクションの生成"""
        outputs = {}
        
        for output in stack_outputs:
            output_config = {
                "Description": output.description,
                "Value": output.value
            }
            
            # Export設定
            if output.export_name:
                export_name = output.export_name.format(
                    ProjectName=project_name,
                    Environment=environment
                )
                output_config["Export"] = {"Name": export_name}
            
            # Condition設定
            if output.conditions:
                # 複数条件の場合はAndで結合
                if len(output.conditions) > 1:
                    output_config["Condition"] = {"Fn::And": [
                        {"Condition": condition} for condition in output.conditions
                    ]}
                else:
                    output_config["Condition"] = output.conditions[0]
            
            outputs[output.name] = output_config
        
        return outputs
    
    def update_template_with_cross_stack_support(self, template_path: str, stack_name: str, 
                                                project_name: str = "${ProjectName}", 
                                                environment: str = "${Environment}"):
        """テンプレートにクロススタック対応を追加"""
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
        
        # パラメータセクションにインポートパラメータを追加
        if stack_name in self.dependencies:
            import_params = self.generate_import_parameters(stack_name, project_name, environment)
            if 'Parameters' not in template:
                template['Parameters'] = {}
            template['Parameters'].update(import_params)
        
        # Outputsセクションを更新
        if stack_name in self.stack_outputs:
            outputs = self.generate_outputs_section(
                self.stack_outputs[stack_name], 
                project_name, 
                environment
            )
            template['Outputs'] = outputs
        
        # テンプレートを保存
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def generate_dependency_graph(self) -> Dict[str, Any]:
        """依存関係グラフの生成"""
        graph = {
            'nodes': [],
            'edges': []
        }
        
        # ノードの追加
        all_stacks = set(self.dependencies.keys())
        for deps in self.dependencies.values():
            for dep in deps:
                all_stacks.add(dep.stack_name)
        
        for stack in all_stacks:
            graph['nodes'].append({
                'id': stack,
                'label': stack,
                'type': 'stack'
            })
        
        # エッジの追加
        for stack_name, deps in self.dependencies.items():
            for dep in deps:
                graph['edges'].append({
                    'from': dep.stack_name,
                    'to': stack_name,
                    'label': f"exports: {', '.join(dep.required_outputs)}"
                })
        
        return graph
    
    def export_configuration(self, output_path: str):
        """設定をJSONファイルにエクスポート"""
        config = {
            'stack_outputs': {
                stack: [
                    {
                        'name': output.name,
                        'description': output.description,
                        'value': output.value,
                        'export_name': output.export_name,
                        'conditions': output.conditions
                    }
                    for output in outputs
                ]
                for stack, outputs in self.stack_outputs.items()
            },
            'dependencies': {
                stack: [
                    {
                        'stack_name': dep.stack_name,
                        'required_outputs': dep.required_outputs,
                        'optional_outputs': dep.optional_outputs or []
                    }
                    for dep in deps
                ]
                for stack, deps in self.dependencies.items()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def import_configuration(self, config_path: str):
        """JSONファイルから設定をインポート"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # スタックアウトプットの復元
        for stack_name, outputs_data in config.get('stack_outputs', {}).items():
            outputs = []
            for output_data in outputs_data:
                outputs.append(StackOutput(
                    name=output_data['name'],
                    description=output_data['description'],
                    value=output_data['value'],
                    export_name=output_data['export_name'],
                    conditions=output_data.get('conditions')
                ))
            self.register_stack_outputs(stack_name, outputs)
        
        # 依存関係の復元
        for stack_name, deps_data in config.get('dependencies', {}).items():
            for dep_data in deps_data:
                dependency = StackDependency(
                    stack_name=dep_data['stack_name'],
                    required_outputs=dep_data['required_outputs'],
                    optional_outputs=dep_data.get('optional_outputs')
                )
                self.register_dependency(stack_name, dependency)

def main():
    """メイン関数 - 使用例"""
    manager = CrossStackManager()
    
    # VPCスタックのアウトプット定義
    vpc_outputs = [
        StackOutput(
            name="VPCId",
            description="VPC ID",
            value="!Ref VPC",
            export_name="{ProjectName}-{Environment}-VPC-ID"
        ),
        StackOutput(
            name="PublicSubnets",
            description="List of Public Subnet IDs",
            value="!Join [',', [!Ref PublicSubnet1, !Ref PublicSubnet2]]",
            export_name="{ProjectName}-{Environment}-PublicSubnets"
        ),
        StackOutput(
            name="PrivateSubnets",
            description="List of Private Subnet IDs",
            value="!Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]",
            export_name="{ProjectName}-{Environment}-PrivateSubnets"
        )
    ]
    
    manager.register_stack_outputs("vpc-stack", vpc_outputs)
    
    # EC2スタックの依存関係定義
    ec2_dependency = StackDependency(
        stack_name="vpc-stack",
        required_outputs=["VPCId", "PrivateSubnets"],
        optional_outputs=["PublicSubnets"]
    )
    
    manager.register_dependency("ec2-stack", ec2_dependency)
    
    # 設定をエクスポート
    manager.export_configuration("cross-stack-config.json")
    
    print("クロススタック設定が生成されました")

if __name__ == "__main__":
    main()