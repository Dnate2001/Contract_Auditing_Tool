#!/usr/bin/env python3
"""
Simple SARIF validator
Validates SARIF files against basic schema requirements
"""

import json
import sys
from pathlib import Path


def validate_sarif(sarif_path: Path) -> bool:
    """Validate SARIF file"""
    try:
        with open(sarif_path) as f:
            sarif = json.load(f)
        
        # Check required top-level fields
        required_fields = ['$schema', 'version', 'runs']
        for field in required_fields:
            if field not in sarif:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check version
        if sarif['version'] != '2.1.0':
            print(f"⚠️ Warning: Version is {sarif['version']}, expected 2.1.0")
        
        # Check runs
        if not isinstance(sarif['runs'], list) or len(sarif['runs']) == 0:
            print("❌ 'runs' must be a non-empty array")
            return False
        
        # Check first run
        run = sarif['runs'][0]
        if 'tool' not in run:
            print("❌ Run missing 'tool' field")
            return False
        
        if 'driver' not in run['tool']:
            print("❌ Tool missing 'driver' field")
            return False
        
        driver = run['tool']['driver']
        if 'name' not in driver:
            print("❌ Driver missing 'name' field")
            return False
        
        # Check results
        if 'results' in run:
            if not isinstance(run['results'], list):
                print("❌ 'results' must be an array")
                return False
            
            for idx, result in enumerate(run['results']):
                if 'ruleId' not in result:
                    print(f"❌ Result {idx} missing 'ruleId'")
                    return False
                if 'message' not in result:
                    print(f"❌ Result {idx} missing 'message'")
                    return False
        
        print("✅ SARIF file is valid!")
        print(f"   Tool: {driver['name']}")
        print(f"   Results: {len(run.get('results', []))}")
        print(f"   Rules: {len(run.get('tool', {}).get('driver', {}).get('rules', []))}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 validate_sarif.py <sarif-file>")
        sys.exit(1)
    
    sarif_file = Path(sys.argv[1])
    if not sarif_file.exists():
        print(f"❌ File not found: {sarif_file}")
        sys.exit(1)
    
    valid = validate_sarif(sarif_file)
    sys.exit(0 if valid else 1)
