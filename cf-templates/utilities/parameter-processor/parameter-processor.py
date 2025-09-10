#!/usr/bin/env python3
"""
Parameter Processor Utility for CloudFormation Templates
Validates JSON configuration files and converts them to CloudFormation parameters
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from jsonschema import validate, ValidationError
from pathlib import Path


class ParameterProcessor:
    """Processes JSON configuration files for CloudFormation templates"""
    
    def __init__(self, schema_dir: str = None):
        """Initialize the parameter processor
        
        Args:
            schema_dir: Directory containing JSON schemas
        """
        if schema_dir is None:
            current_dir = Path(__file__).parent
            schema_dir = current_dir.parent.parent / "configurations" / "schemas"
        
        self.schema_dir = Path(schema_dir)
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load all JSON schemas from the schema directory"""
        schemas = {}
        
        try:
            # Load project configuration schema
            project_schema_path = self.schema_dir / "project-config-schema.json"
            if project_schema_path.exists():
                with open(project_schema_path, 'r', encoding='utf-8') as f:
                    schemas['project-config'] = json.load(f)
            
            # Load template metadata schema
            template_schema_path = self.schema_dir / "template-metadata-schema.json"
            if template_schema_path.exists():
                with open(template_schema_path, 'r', encoding='utf-8') as f:
                    schemas['template-metadata'] = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load schemas: {e}")
        
        return schemas
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration against schema
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if 'project-config' not in self.schemas:
            errors.append("Project configuration schema not found")
            return False, errors
        
        try:
            validate(instance=config, schema=self.schemas['project-config'])
            return True, []
        except ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            if e.path:
                errors.append(f"Path: {' -> '.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            return False, errors
    
    def convert_to_cf_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON configuration to CloudFormation parameters format
        
        Args:
            config: Validated configuration dictionary
            
        Returns:
            CloudFormation parameters dictionary
        """
        cf_params = {}
        
        # Process project configuration
        if 'projectConfig' in config:
            project_config = config['projectConfig']
            
            # Basic project parameters
            cf_params['ProjectName'] = project_config.get('projectName', '')
            cf_params['Environment'] = project_config.get('environment', 'dev')
            cf_params['Region'] = project_config.get('region', 'us-east-1')
            
            # Availability zones
            if 'availabilityZones' in project_config:
                az_list = project_config['availabilityZones']
                cf_params['AvailabilityZones'] = ','.join(az_list)
                cf_params['AvailabilityZoneCount'] = str(len(az_list))
            
            # Tags
            if 'tags' in project_config:
                tags = project_config['tags']
                # Convert tags to CloudFormation format
                tag_list = []
                for key, value in tags.items():
                    tag_list.append(f"{key}={value}")
                cf_params['ResourceTags'] = ','.join(tag_list)
        
        # Process service configurations
        if 'serviceConfigs' in config:
            service_configs = config['serviceConfigs']
            
            # VPC configuration
            if 'vpc' in service_configs:
                vpc_config = service_configs['vpc']
                cf_params['VpcPattern'] = vpc_config.get('pattern', 'basic')
                cf_params['VpcCidrBlock'] = vpc_config.get('cidrBlock', '10.0.0.0/16')
                cf_params['EnableDnsHostnames'] = str(vpc_config.get('enableDnsHostnames', True)).lower()
                cf_params['EnableDnsSupport'] = str(vpc_config.get('enableDnsSupport', True)).lower()
            
            # EC2 configuration
            if 'ec2' in service_configs:
                ec2_config = service_configs['ec2']
                cf_params['Ec2Pattern'] = ec2_config.get('pattern', 'basic')
                if 'instanceType' in ec2_config:
                    cf_params['InstanceType'] = ec2_config['instanceType']
                if 'amiId' in ec2_config:
                    cf_params['AmiId'] = ec2_config['amiId']
                if 'keyPairName' in ec2_config:
                    cf_params['KeyPairName'] = ec2_config['keyPairName']
        
        # Process integration options
        if 'integrationOptions' in config:
            integration_options = config['integrationOptions']
            cf_params['EnableCrossStackReferences'] = str(integration_options.get('crossStackReferences', True)).lower()
            cf_params['EnableMonitoringIntegration'] = str(integration_options.get('monitoringIntegration', True)).lower()
            
            if 'sharedResources' in integration_options:
                shared_resources = integration_options['sharedResources']
                cf_params['SharedResources'] = ','.join(shared_resources)
        
        return cf_params
    
    def generate_cf_parameters_file(self, config: Dict[str, Any], output_path: str) -> bool:
        """Generate CloudFormation parameters file
        
        Args:
            config: Configuration dictionary
            output_path: Path to output parameters file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cf_params = self.convert_to_cf_parameters(config)
            
            # Create CloudFormation parameters format
            cf_parameters = []
            for key, value in cf_params.items():
                cf_parameters.append({
                    "ParameterKey": key,
                    "ParameterValue": str(value)
                })
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cf_parameters, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error generating CloudFormation parameters file: {e}")
            return False
    
    def process_config_file(self, config_path: str, output_path: str = None) -> Tuple[bool, List[str]]:
        """Process a configuration file
        
        Args:
            config_path: Path to JSON configuration file
            output_path: Path to output CloudFormation parameters file
            
        Returns:
            Tuple of (success, messages)
        """
        messages = []
        
        try:
            # Load configuration file
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate configuration
            is_valid, validation_errors = self.validate_config(config)
            if not is_valid:
                messages.extend(validation_errors)
                return False, messages
            
            messages.append("Configuration validation successful")
            
            # Generate output path if not provided
            if output_path is None:
                config_file = Path(config_path)
                output_path = config_file.parent / f"{config_file.stem}-cf-parameters.json"
            
            # Generate CloudFormation parameters file
            if self.generate_cf_parameters_file(config, output_path):
                messages.append(f"CloudFormation parameters file generated: {output_path}")
                return True, messages
            else:
                messages.append("Failed to generate CloudFormation parameters file")
                return False, messages
                
        except FileNotFoundError:
            messages.append(f"Configuration file not found: {config_path}")
            return False, messages
        except json.JSONDecodeError as e:
            messages.append(f"Invalid JSON in configuration file: {e}")
            return False, messages
        except Exception as e:
            messages.append(f"Unexpected error processing configuration: {e}")
            return False, messages


def main():
    """Command line interface for parameter processor"""
    if len(sys.argv) < 2:
        print("Usage: python parameter-processor.py <config-file> [output-file]")
        sys.exit(1)
    
    config_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    processor = ParameterProcessor()
    success, messages = processor.process_config_file(config_file, output_file)
    
    for message in messages:
        print(message)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()