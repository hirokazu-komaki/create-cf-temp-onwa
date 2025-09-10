#!/usr/bin/env python3
"""
Configuration Processing Utility
Main entry point for processing JSON configurations and generating CloudFormation parameters
"""

import sys
import os
from pathlib import Path

# Add parameter processor to path
sys.path.insert(0, str(Path(__file__).parent / "parameter-processor"))

from parameter_processor import ParameterProcessor


def main():
    """Main function for configuration processing"""
    if len(sys.argv) < 2:
        print("Configuration Processing Utility")
        print("Usage: python process-config.py <config-file> [output-file]")
        print("")
        print("Examples:")
        print("  python process-config.py configurations/examples/sample-project-config.json")
        print("  python process-config.py my-config.json my-cf-params.json")
        sys.exit(1)
    
    config_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("Well-Architected CloudFormation Configuration Processor")
    print("=" * 55)
    print(f"Processing configuration: {config_file}")
    
    # Initialize processor
    processor = ParameterProcessor()
    
    # Process configuration
    success, messages = processor.process_config_file(config_file, output_file)
    
    # Display results
    print("")
    for message in messages:
        print(f"  {message}")
    
    print("")
    if success:
        print("✓ Configuration processed successfully!")
    else:
        print("✗ Configuration processing failed!")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()