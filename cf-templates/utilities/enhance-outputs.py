#!/usr/bin/env python3
"""
Enhanced Outputs Generator
CloudFormationテンプレートのOutputsセクションを手動で強化
"""

import json
from pathlib import Path

def generate_enhanced_outputs():
    """強化されたOutputsセクションを生成"""
    
    # VPCテンプレート用の追加Outputs
    vpc_additional_outputs = """
  # Cross-Stack Integration Outputs
  VPCDefaultSecurityGroupId:
    Description: VPC Default Security Group ID
    Value: !GetAtt VPC.DefaultSecurityGroup
    Export:
      Name: !Sub '${ProjectName}-${Environment}-VPC-DefaultSG-ID'

  VPCDefaultNetworkAclId:
    Description: VPC Default Network ACL ID
    Value: !GetAtt VPC.DefaultNetworkAcl
    Export:
      Name: !Sub '${ProjectName}-${Environment}-VPC-DefaultACL-ID'

  AvailabilityZones:
    Description: List of Availability Zones used
    Value: !If
      - IsBasicPattern
      - !Join [',', [!Select [0, !GetAZs ''], !Select [1, !GetAZs '']]]
      - !Join [',', [!Select [0, !GetAZs ''], !Select [1, !GetAZs ''], !Select [2, !GetAZs '']]]
    Export:
      Name: !Sub '${ProjectName}-${Environment}-AvailabilityZones'

  PublicRouteTableId:
    Description: Public Route Table ID
    Value: !Ref PublicRouteTable
    Export:
      Name: !Sub '${ProjectName}-${Environment}-PublicRouteTable-ID'

  PrivateRouteTable1Id:
    Description: Private Route Table 1 ID
    Value: !Ref PrivateRouteTable1
    Export:
      Name: !Sub '${ProjectName}-${Environment}-PrivateRouteTable1-ID'

  PrivateRouteTable2Id:
    Description: Private Route Table 2 ID
    Value: !Ref PrivateRouteTable2
    Export:
      Name: !Sub '${ProjectName}-${Environment}-PrivateRouteTable2-ID'

  PrivateRouteTable3Id:
    Condition: !Or [!Condition IsAdvancedPattern, !Condition IsEnterprisePattern]
    Description: Private Route Table 3 ID
    Value: !Ref PrivateRouteTable3
    Export:
      Name: !Sub '${ProjectName}-${Environment}-PrivateRouteTable3-ID'
"""

    # IAMテンプレート用の追加Outputs
    iam_additional_outputs = """
  # Cross-Stack Integration Outputs
  ExecutionRoleArn:
    Description: 現在のパターンに対応する実行ロールARN
    Value: !If
      - IsBasicPattern
      - !GetAtt BasicExecutionRole.Arn
      - !If
        - IsAdvancedPattern
        - !GetAtt AdvancedExecutionRole.Arn
        - !GetAtt EnterpriseExecutionRole.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-execution-role-arn'

  InstanceProfileArn:
    Description: 現在のパターンに対応するインスタンスプロファイルARN
    Value: !If
      - IsBasicPattern
      - !GetAtt BasicInstanceProfile.Arn
      - !If
        - IsAdvancedPattern
        - !GetAtt AdvancedInstanceProfile.Arn
        - !GetAtt EnterpriseInstanceProfile.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-instance-profile-arn'

  CrossAccountAccessRoleArn:
    Condition: IsCrossAccountEnabled
    Description: クロスアカウントアクセスロールのARN
    Value: !GetAtt CrossAccountAccessRole.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-cross-account-access-role-arn'
"""

    # KMSテンプレート用の追加Outputs
    kms_additional_outputs = """
  # Cross-Stack Integration Outputs
  ApplicationKMSKeyId:
    Description: アプリケーション用KMSキーID（汎用キー）
    Value: !Ref GeneralPurposeKey
    Export:
      Name: !Sub '${ProjectName}-${Environment}-application-kms-key-id'

  ApplicationKMSKeyArn:
    Description: アプリケーション用KMSキーARN（汎用キー）
    Value: !GetAtt GeneralPurposeKey.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-application-kms-key-arn'

  DatabaseKMSKeyId:
    Condition: IsAdvancedPattern
    Description: データベース用KMSキーID
    Value: !Ref RDSEncryptionKey
    Export:
      Name: !Sub '${ProjectName}-${Environment}-database-kms-key-id'

  DatabaseKMSKeyArn:
    Condition: IsAdvancedPattern
    Description: データベース用KMSキーARN
    Value: !GetAtt RDSEncryptionKey.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-database-kms-key-arn'

  StorageKMSKeyId:
    Condition: IsAdvancedPattern
    Description: ストレージ用KMSキーID（S3/EBS）
    Value: !If
      - IsAdvancedPattern
      - !Ref S3EncryptionKey
      - !Ref GeneralPurposeKey
    Export:
      Name: !Sub '${ProjectName}-${Environment}-storage-kms-key-id'

  StorageKMSKeyArn:
    Condition: IsAdvancedPattern
    Description: ストレージ用KMSキーARN（S3/EBS）
    Value: !If
      - IsAdvancedPattern
      - !GetAtt S3EncryptionKey.Arn
      - !GetAtt GeneralPurposeKey.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-storage-kms-key-arn'
"""

    # EC2テンプレート用の追加Outputs
    ec2_additional_outputs = """
  # Cross-Stack Integration Outputs
  LaunchTemplateId:
    Description: Launch Template ID
    Value: !Ref EC2LaunchTemplate
    Export:
      Name: !Sub '${ProjectName}-${Environment}-LaunchTemplate-Id'

  LaunchTemplateVersion:
    Description: Launch Template Latest Version
    Value: !GetAtt EC2LaunchTemplate.LatestVersionNumber
    Export:
      Name: !Sub '${ProjectName}-${Environment}-LaunchTemplate-Version'

  IAMRoleArn:
    Description: EC2 IAM Role ARN
    Value: !GetAtt EC2Role.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-IAM-Role-Arn'

  InstanceProfileArn:
    Description: EC2 Instance Profile ARN
    Value: !GetAtt EC2InstanceProfile.Arn
    Export:
      Name: !Sub '${ProjectName}-${Environment}-InstanceProfile-Arn'

  EC2LogGroupName:
    Description: EC2 Log Group Name
    Value: !Ref EC2LogGroup
    Export:
      Name: !Sub '${ProjectName}-${Environment}-EC2-LogGroup-Name'
"""

    # CloudWatchテンプレート用の追加Outputs
    cloudwatch_additional_outputs = """
  # Cross-Stack Integration Outputs
  SlackNotificationFunctionArn:
    Description: Slack Notification Lambda Function ARN
    Value: !If [HasSlackWebhook, !GetAtt SlackNotificationFunction.Arn, "N/A"]
    Export:
      Name: !Sub '${ProjectName}-${Environment}-slack-notification-function-arn'

  MonitoringDashboardUrl:
    Description: CloudWatch Dashboard URL
    Value: !If
      - CreateAdvancedResources
      - !Sub 'https://${AWS::Region}.console.aws.amazon.com/cloudwatch/home?region=${AWS::Region}#dashboards:name=${ProjectName}-${Environment}-monitoring'
      - "N/A"
    Export:
      Name: !Sub '${ProjectName}-${Environment}-dashboard-url'

  EnterpriseDashboardUrl:
    Description: Enterprise CloudWatch Dashboard URL
    Value: !If
      - CreateEnterpriseResources
      - !Sub 'https://${AWS::Region}.console.aws.amazon.com/cloudwatch/home?region=${AWS::Region}#dashboards:name=${ProjectName}-${Environment}-enterprise'
      - "N/A"
    Export:
      Name: !Sub '${ProjectName}-${Environment}-enterprise-dashboard-url'

  ErrorMetricFilterName:
    Description: Error Metric Filter Name
    Value: !Ref ErrorMetricFilter
    Export:
      Name: !Sub '${ProjectName}-${Environment}-error-metric-filter'

  WarningMetricFilterName:
    Description: Warning Metric Filter Name
    Value: !Ref WarningMetricFilter
    Export:
      Name: !Sub '${ProjectName}-${Environment}-warning-metric-filter'
"""

    return {
        'vpc': vpc_additional_outputs,
        'iam': iam_additional_outputs,
        'kms': kms_additional_outputs,
        'ec2': ec2_additional_outputs,
        'cloudwatch': cloudwatch_additional_outputs
    }

def append_outputs_to_template(template_path: str, additional_outputs: str):
    """テンプレートファイルにOutputsを追加"""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Outputsセクションの最後を見つけて追加
    if 'Outputs:' in content:
        # 既存のOutputsセクションの最後に追加
        content += additional_outputs
    else:
        # Outputsセクションが存在しない場合は新規作成
        content += f"\nOutputs:{additional_outputs}"
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Enhanced outputs added to {template_path}")

def main():
    """メイン処理"""
    
    # 強化されたOutputsを生成
    enhanced_outputs = generate_enhanced_outputs()
    
    # テンプレートファイルのマッピング
    template_mappings = {
        'cf-templates/networking/vpc/vpc-template.yaml': 'vpc',
        'cf-templates/foundation/iam/iam-roles-policies.yaml': 'iam',
        'cf-templates/foundation/kms/kms-keys.yaml': 'kms',
        'cf-templates/compute/ec2/ec2-autoscaling.yaml': 'ec2',
        'cf-templates/integration/cloudwatch/cloudwatch-template.yaml': 'cloudwatch'
    }
    
    # 各テンプレートにOutputsを追加
    for template_path, output_type in template_mappings.items():
        template_file = Path(template_path)
        
        if template_file.exists() and output_type in enhanced_outputs:
            print(f"\nProcessing {template_path}")
            append_outputs_to_template(str(template_file), enhanced_outputs[output_type])
        else:
            print(f"Warning: Template not found or no outputs defined: {template_path}")
    
    print("\nAll templates have been enhanced with cross-stack outputs!")

if __name__ == "__main__":
    main()