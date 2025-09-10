#!/usr/bin/env python3
"""
テンプレートマッピングのテストスクリプト
"""

import json
from pathlib import Path

def test_mapping():
    """マッピングロジックをテストする"""
    
    # テスト用の設定ファイルリスト
    test_configs = [
        "cf-templates/compute/ec2/ec2-config-basic.json",
        "cf-templates/compute/lambda/lambda-config-basic.json",
        "cf-templates/networking/vpc/vpc-config-basic.json",
        "cf-templates/networking/elb/elb-config-basic.json",
        "cf-templates/foundation/iam/iam-config-basic.json",
        "cf-templates/foundation/kms/kms-config-basic.json",
        "cf-templates/patterns/web-application/web-app-config-basic.json",
        "cf-templates/patterns/microservices/microservices-config-basic.json",
        "cf-templates/integration/api-gateway/api-gateway-config-basic.json"
    ]
    
    templates_to_test = []
    
    for config_file in test_configs:
        if not config_file:
            continue
            
        config_path = Path(config_file)
        
        if config_path.parts[0] == 'cf-templates':
            template_dir = config_path.parent
            
            # サービス名の決定（ディレクトリ名から）
            if len(config_path.parts) > 2:
                service_name = config_path.parts[-2]
                # web-applicationのような複合名の場合の特別処理
                if service_name == 'web-application':
                    service_name = 'web-app'
            else:
                service_name = config_path.stem.split('-')[0]
            
            # サービス固有のマッピングパターンを定義
            service_specific_patterns = {
                'ec2': ['ec2-autoscaling', 'ec2-scaling-policies'],
                'lambda': ['lambda-function', 'lambda-layer'],
                'config': ['config-setup'],
                'iam': ['iam-roles-policies'],
                'kms': ['kms-keys'],
                'organization': ['organization-setup'],
                'microservices': ['microservices-pattern'],
                'web-app': ['web-app-pattern'],
                'data-processing': ['data-processing-pattern']
            }
            
            # テンプレートパターンの決定
            if service_name in service_specific_patterns:
                template_patterns = service_specific_patterns[service_name]
            else:
                # 標準的なパターン
                template_patterns = [f"{service_name}-template"]
            
            # 汎用パターンも追加
            template_patterns.extend([f"{service_name}-template", service_name])
            
            possible_templates = []
            for pattern in template_patterns:
                possible_templates.extend([
                    template_dir / f"{pattern}.yaml",
                    template_dir / f"{pattern}.yml"
                ])
            
            # 汎用的なテンプレート名も追加
            possible_templates.extend([
                template_dir / "template.yaml",
                template_dir / "template.yml"
            ])
            
            # 実際に存在するテンプレートを探す
            found_template = None
            for template_path in possible_templates:
                if template_path.exists():
                    found_template = str(template_path)
                    break
            
            if found_template:
                templates_to_test.append({
                    'config': config_file,
                    'template': found_template,
                    'service': service_name
                })
                print(f"✅ {config_file} -> {found_template}")
            else:
                print(f"❌ {config_file} -> No template found")
                print(f"   Searched for: {[str(p) for p in possible_templates[:5]]}")
    
    print(f"\n📊 マッピング結果:")
    print(f"成功: {len(templates_to_test)} 件")
    print(f"失敗: {len(test_configs) - len(templates_to_test)} 件")
    
    return templates_to_test

if __name__ == "__main__":
    test_mapping()