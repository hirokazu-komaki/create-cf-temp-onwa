#!/usr/bin/env python3
"""
Well-Architected Framework Compliance Validator
Validates CloudFormation templates against Well-Architected best practices
"""

import json
import yaml
import sys
from typing import Dict, List, Any, Tuple
from pathlib import Path


class WellArchitectedValidator:
    """Validates templates against Well-Architected Framework best practices"""
    
    def __init__(self, compliance_file: str = None):
        """Initialize the validator
        
        Args:
            compliance_file: Path to Well-Architected compliance definitions
        """
        if compliance_file is None:
            current_dir = Path(__file__).parent
            compliance_file = current_dir.parent.parent / "configurations" / "schemas" / "well-architected-compliance.json"
        
        self.compliance_file = Path(compliance_file)
        self.compliance_data = self._load_compliance_data()
    
    def _load_compliance_data(self) -> Dict[str, Any]:
        """Load Well-Architected compliance data"""
        try:
            with open(self.compliance_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load compliance data: {e}")
            return {}
    
    def validate_template_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate template metadata for Well-Architected compliance
        
        Args:
            metadata: Template metadata dictionary
            
        Returns:
            Tuple of (is_valid, messages)
        """
        messages = []
        is_valid = True
        
        if 'wellArchitectedCompliance' not in metadata:
            messages.append("Warning: No Well-Architected compliance information found")
            return False, messages
        
        compliance = metadata['wellArchitectedCompliance']
        framework = self.compliance_data.get('wellArchitectedFramework', {})
        pillars = framework.get('pillars', {})
        
        # Validate each pillar
        for pillar_name, practices in compliance.items():
            if pillar_name not in pillars:
                messages.append(f"Warning: Unknown pillar '{pillar_name}'")
                continue
            
            pillar_data = pillars[pillar_name]
            valid_practices = pillar_data.get('bestPractices', {})
            
            for practice in practices:
                if practice not in valid_practices:
                    messages.append(f"Warning: Unknown best practice '{practice}' in pillar '{pillar_name}'")
                    is_valid = False
                else:
                    messages.append(f"✓ {practice}: {valid_practices[practice]}")
        
        return is_valid, messages
    
    def validate_cloudformation_template(self, template_path: str) -> Tuple[bool, List[str]]:
        """Validate CloudFormation template for Well-Architected compliance
        
        Args:
            template_path: Path to CloudFormation template
            
        Returns:
            Tuple of (is_valid, messages)
        """
        messages = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                if template_path.endswith('.json'):
                    template = json.load(f)
                else:
                    template = yaml.safe_load(f)
            
            # Check for metadata section
            if 'Metadata' not in template:
                messages.append("Warning: Template does not contain Metadata section")
                return False, messages
            
            metadata = template['Metadata']
            return self.validate_template_metadata(metadata)
            
        except Exception as e:
            messages.append(f"Error reading template: {e}")
            return False, messages
    
    def generate_compliance_report(self, template_path: str, output_path: str = None) -> bool:
        """Generate a compliance report for a template
        
        Args:
            template_path: Path to CloudFormation template
            output_path: Path to output report file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            is_valid, messages = self.validate_cloudformation_template(template_path)
            
            report = {
                "templatePath": template_path,
                "validationTimestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
                "isCompliant": is_valid,
                "messages": messages,
                "summary": {
                    "totalChecks": len(messages),
                    "passed": len([m for m in messages if m.startswith("✓")]),
                    "warnings": len([m for m in messages if m.startswith("Warning")]),
                    "errors": len([m for m in messages if m.startswith("Error")])
                }
            }
            
            if output_path is None:
                template_file = Path(template_path)
                output_path = template_file.parent / f"{template_file.stem}-compliance-report.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error generating compliance report: {e}")
            return False


def main():
    """Command line interface for Well-Architected validator"""
    if len(sys.argv) < 2:
        print("Usage: python well-architected-validator.py <template-file> [report-file]")
        sys.exit(1)
    
    template_file = sys.argv[1]
    report_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    validator = WellArchitectedValidator()
    
    # Validate template
    is_valid, messages = validator.validate_cloudformation_template(template_file)
    
    # Print results
    for message in messages:
        print(message)
    
    # Generate report
    if validator.generate_compliance_report(template_file, report_file):
        print(f"Compliance report generated: {report_file or 'auto-generated'}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()