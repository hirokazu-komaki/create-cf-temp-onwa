#!/usr/bin/env python3
"""
Import Parameters Generator
依存関係のあるテンプレートにインポートパラメータを追加
"""

from pathlib import Path

def generate_import_parameters():
    """各テンプレート用のインポートパラメータを生成"""
    
    # EC2テンプレート用のインポートパラメータ
    ec2_import_parameters = """
  # Cross-Stack Import Parameters
  ImportVPCId:
    Type: String
    Description: Import VPC ID from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-VPC-ID'

  ImportPrivateSubnets:
    Type: String
    Description: Import Private Subnets from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-PrivateSubnets'

  ImportPublicSubnets:
    Type: String
    Description: Import Public Subnets from networking-vpc stack (optional)
    Default: ''

  ImportExecutionRoleArn:
    Type: String
    Description: Import Execution Role ARN from foundation-iam stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-execution-role-arn'

  ImportInstanceProfileArn:
    Type: String
    Description: Import Instance Profile ARN from foundation-iam stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-instance-profile-arn'

  ImportApplicationKMSKeyArn:
    Type: String
    Description: Import Application KMS Key ARN from foundation-kms stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-application-kms-key-arn'
"""

    # Lambda テンプレート用のインポートパラメータ
    lambda_import_parameters = """
  # Cross-Stack Import Parameters
  ImportVPCId:
    Type: String
    Description: Import VPC ID from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-VPC-ID'

  ImportPrivateSubnets:
    Type: String
    Description: Import Private Subnets from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-PrivateSubnets'

  ImportExecutionRoleArn:
    Type: String
    Description: Import Execution Role ARN from foundation-iam stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-execution-role-arn'

  ImportApplicationKMSKeyArn:
    Type: String
    Description: Import Application KMS Key ARN from foundation-kms stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-application-kms-key-arn'
"""

    # ELB テンプレート用のインポートパラメータ
    elb_import_parameters = """
  # Cross-Stack Import Parameters
  ImportVPCId:
    Type: String
    Description: Import VPC ID from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-VPC-ID'

  ImportPublicSubnets:
    Type: String
    Description: Import Public Subnets from networking-vpc stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-PublicSubnets'

  ImportAutoScalingGroupName:
    Type: String
    Description: Import Auto Scaling Group Name from compute-ec2 stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-ASG-Name'

  ImportEC2SecurityGroupId:
    Type: String
    Description: Import EC2 Security Group ID from compute-ec2 stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-EC2-SG-Id'
"""

    # API Gateway テンプレート用のインポートパラメータ
    api_gateway_import_parameters = """
  # Cross-Stack Import Parameters
  ImportLambdaFunctionArn:
    Type: String
    Description: Import Lambda Function ARN from compute-lambda stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-Lambda-Function-Arn'

  ImportExecutionRoleArn:
    Type: String
    Description: Import Execution Role ARN from foundation-iam stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-execution-role-arn'

  ImportApplicationLogGroupName:
    Type: String
    Description: Import Application Log Group Name from integration-cloudwatch stack
    Default: !ImportValue
      Fn::Sub: '${ProjectName}-${Environment}-application-log-group'
"""

    return {
        'ec2': ec2_import_parameters,
        'lambda': lambda_import_parameters,
        'elb': elb_import_parameters,
        'api-gateway': api_gateway_import_parameters
    }

def add_parameters_to_template(template_path: str, import_parameters: str):
    """テンプレートファイルにパラメータを追加"""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parametersセクションを見つけて追加
    if 'Parameters:' in content:
        # Parametersセクションの後に追加
        lines = content.split('\n')
        new_lines = []
        parameters_found = False
        
        for line in lines:
            new_lines.append(line)
            if line.strip() == 'Parameters:' and not parameters_found:
                # インポートパラメータを追加
                for param_line in import_parameters.split('\n'):
                    new_lines.append(param_line)
                parameters_found = True
        
        content = '\n'.join(new_lines)
    else:
        # Parametersセクションが存在しない場合は新規作成
        # AWSTemplateFormatVersionの後に追加
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if line.startswith('Description:'):
                # Descriptionの後にParametersセクションを追加
                new_lines.append('')
                new_lines.append('Parameters:')
                for param_line in import_parameters.split('\n'):
                    new_lines.append(param_line)
                new_lines.append('')
                break
        
        # 残りの行を追加
        new_lines.extend(lines[i+1:])
        content = '\n'.join(new_lines)
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Import parameters added to {template_path}")

def main():
    """メイン処理"""
    
    # インポートパラメータを生成
    import_parameters = generate_import_parameters()
    
    # テンプレートファイルのマッピング（依存関係があるもののみ）
    template_mappings = {
        'cf-templates/compute/ec2/ec2-autoscaling.yaml': 'ec2',
        'cf-templates/compute/lambda/lambda-function.yaml': 'lambda',
        'cf-templates/networking/elb/elb-template.yaml': 'elb',
        'cf-templates/integration/api-gateway/api-gateway-template.yaml': 'api-gateway'
    }
    
    # 各テンプレートにパラメータを追加
    for template_path, param_type in template_mappings.items():
        template_file = Path(template_path)
        
        if template_file.exists() and param_type in import_parameters:
            print(f"\nProcessing {template_path}")
            add_parameters_to_template(str(template_file), import_parameters[param_type])
        else:
            print(f"Warning: Template not found or no parameters defined: {template_path}")
    
    print("\nAll dependent templates have been enhanced with import parameters!")

if __name__ == "__main__":
    main()