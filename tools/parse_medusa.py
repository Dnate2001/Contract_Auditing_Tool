#!/usr/bin/env python3
"""
Medusa Output Parser for Contract_Auditing_Tool
Parses Medusa fuzzer crash/revert/coverage artifacts into canonical vulnerability format.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import argparse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MedusaParser:
    """Robust parser for Medusa fuzzer outputs"""
    
    def __init__(self, input_dir: Path):
        self.input_dir = Path(input_dir)
        self.findings = []
        
    def parse_medusa_outputs(self) -> List[Dict]:
        """
        Main entry point: finds and parses all Medusa artifacts.
        Returns list of canonical vulnerability dicts.
        """
        if not self.input_dir.exists():
            logger.warning(f"Input directory does not exist: {self.input_dir}")
            return []
        
        # Search for JSON files in medusa output directories
        json_files = list(self.input_dir.rglob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {self.input_dir}")
            return []
        
        logger.info(f"Found {len(json_files)} JSON files to parse")
        
        for json_file in json_files:
            try:
                self._parse_file(json_file)
            except Exception as e:
                logger.warning(f"Failed to parse {json_file}: {e}")
                continue
        
        logger.info(f"Extracted {len(self.findings)} findings")
        return self.findings
    
    def _parse_file(self, filepath: Path):
        """Parse a single JSON file (handles both single JSON and newline-delimited JSON)"""
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                
            # Try parsing as single JSON object
            try:
                data = json.loads(content)
                self._extract_findings(data, filepath)
            except json.JSONDecodeError:
                # Try parsing as newline-delimited JSON
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._extract_findings(data, filepath, line_num)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at {filepath}:{line_num}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
    
    def _extract_findings(self, data: Dict, filepath: Path, line_num: Optional[int] = None):
        """Extract vulnerability findings from parsed JSON data"""
        
        # Handle different Medusa output formats
        if isinstance(data, dict):
            # Check for crash/revert entries
            if 'test_results' in data:
                self._parse_test_results(data['test_results'], filepath)
            elif 'crashes' in data:
                self._parse_crashes(data['crashes'], filepath)
            elif 'reverts' in data:
                self._parse_reverts(data['reverts'], filepath)
            elif 'call_sequence' in data or 'sequence' in data:
                # Single crash/revert entry
                self._parse_single_entry(data, filepath, line_num)
            elif 'coverage' in data:
                # Coverage data - log but don't extract as finding
                logger.debug(f"Found coverage data in {filepath}")
            else:
                # Unknown format - try to extract what we can
                logger.debug(f"Unknown format in {filepath}, attempting best-effort extraction")
                self._parse_single_entry(data, filepath, line_num)
    
    def _parse_test_results(self, test_results: Any, filepath: Path):
        """Parse test_results array from Medusa output"""
        if not isinstance(test_results, list):
            test_results = [test_results]
        
        for result in test_results:
            if isinstance(result, dict):
                if result.get('status') in ['failed', 'reverted', 'crashed']:
                    self._parse_single_entry(result, filepath)
    
    def _parse_crashes(self, crashes: Any, filepath: Path):
        """Parse crashes array"""
        if not isinstance(crashes, list):
            crashes = [crashes]
        
        for crash in crashes:
            if isinstance(crash, dict):
                self._parse_single_entry(crash, filepath)
    
    def _parse_reverts(self, reverts: Any, filepath: Path):
        """Parse reverts array"""
        if not isinstance(reverts, list):
            reverts = [reverts]
        
        for revert in reverts:
            if isinstance(revert, dict):
                self._parse_single_entry(revert, filepath)
    
    def _parse_single_entry(self, entry: Dict, filepath: Path, line_num: Optional[int] = None):
        """Parse a single crash/revert entry into canonical format"""
        try:
            # Extract call sequence
            sequence = self._extract_sequence(entry)
            
            # Extract basic fields with defensive fallbacks
            contract = entry.get('contract', entry.get('target_contract', 'Unknown'))
            function = entry.get('function', entry.get('failing_function', 
                                entry.get('test_name', 'unknown_function')))
            
            # Extract revert reason
            revert_reason = entry.get('revert_reason', 
                                     entry.get('error', 
                                     entry.get('message', 'Unknown revert')))
            
            # Determine vulnerability type from function name or revert reason
            vuln_type = self._infer_vulnerability_type(function, revert_reason, entry)
            
            # Build canonical finding
            finding = {
                'type': vuln_type,
                'contract': contract,
                'function': function,
                'line': entry.get('line', 0),
                'description': revert_reason,
                'severity': self._infer_severity(vuln_type),
                'sequence': sequence,
                'evidence_files': [str(filepath)],
                'raw_trace': entry.get('trace', entry.get('stack_trace', '')),
                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                'property_failed': entry.get('property', entry.get('assertion', ''))
            }
            
            self.findings.append(finding)
            logger.debug(f"Extracted finding: {vuln_type} in {function}")
            
        except Exception as e:
            logger.warning(f"Failed to parse entry from {filepath}: {e}")
    
    def _extract_sequence(self, entry: Dict) -> List[Dict]:
        """Extract and normalize call sequence"""
        sequence = []
        
        # Try different sequence field names
        raw_sequence = (entry.get('call_sequence') or 
                       entry.get('sequence') or 
                       entry.get('calls') or 
                       entry.get('transactions') or [])
        
        if not isinstance(raw_sequence, list):
            raw_sequence = [raw_sequence]
        
        for call in raw_sequence:
            if isinstance(call, dict):
                normalized_call = {
                    'sender': call.get('sender', call.get('from', call.get('caller', '0x0'))),
                    'target': call.get('target', call.get('to', call.get('contract', ''))),
                    'function': call.get('function', call.get('method', call.get('signature', ''))),
                    'calldata': call.get('calldata', call.get('data', call.get('input', ''))),
                    'value': call.get('value', call.get('amount', 0)),
                    'gas': call.get('gas', call.get('gas_limit', 0))
                }
                sequence.append(normalized_call)
            elif isinstance(call, str):
                # Simple string representation
                sequence.append({'function': call, 'sender': '0x0', 'target': '', 'calldata': '', 'value': 0, 'gas': 0})
        
        return sequence
    
    def _infer_vulnerability_type(self, function: str, revert_reason: str, entry: Dict) -> str:
        """Infer vulnerability type from function name and revert reason"""
        function_lower = function.lower()
        revert_lower = revert_reason.lower()
        
        # Check property name first
        property_name = entry.get('property', entry.get('assertion', '')).lower()
        
        if 'mint' in function_lower or 'mint' in property_name:
            return 'Unauthorized Minting'
        elif 'reentrancy' in revert_lower or 'reentrancy' in property_name:
            return 'Reentrancy Vulnerability'
        elif 'delegatecall' in function_lower or 'delegatecall' in revert_lower:
            return 'Unrestricted Delegatecall'
        elif 'random' in function_lower or 'random' in property_name:
            return 'Weak Randomness'
        elif 'selfdestruct' in function_lower or 'destroy' in function_lower:
            return 'Unprotected Selfdestruct'
        elif 'overflow' in revert_lower or 'underflow' in revert_lower:
            return 'Integer Overflow/Underflow'
        elif 'access' in revert_lower or 'unauthorized' in revert_lower:
            return 'Access Control Violation'
        else:
            return 'Property Violation'
    
    def _infer_severity(self, vuln_type: str) -> str:
        """Infer severity level from vulnerability type"""
        critical_types = ['Unauthorized Minting', 'Unrestricted Delegatecall', 
                         'Unprotected Selfdestruct', 'Integer Overflow/Underflow']
        high_types = ['Reentrancy Vulnerability', 'Access Control Violation']
        
        if vuln_type in critical_types:
            return 'CRITICAL'
        elif vuln_type in high_types:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def save_findings(self, output_path: Path):
        """Save findings to canonical JSON format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.findings, f, indent=2)
        
        logger.info(f"Saved {len(self.findings)} findings to {output_path}")


def parse_medusa_outputs(input_path: str) -> List[Dict]:
    """
    Public API: Parse Medusa outputs from given path.
    
    Args:
        input_path: Path to medusa output directory
        
    Returns:
        List of canonical vulnerability dictionaries
    """
    parser = MedusaParser(Path(input_path))
    return parser.parse_medusa_outputs()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Parse Medusa fuzzer outputs')
    parser.add_argument('--input', default='medusa-reports', 
                       help='Input directory containing Medusa outputs')
    parser.add_argument('--output', default='artifacts/findings.json',
                       help='Output path for canonical findings JSON')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Search both common Medusa output directories
    search_dirs = [args.input, 'medusa-out', 'medusa-reports']
    
    all_findings = []
    for search_dir in search_dirs:
        if Path(search_dir).exists():
            logger.info(f"Searching {search_dir}...")
            medusa_parser = MedusaParser(Path(search_dir))
            findings = medusa_parser.parse_medusa_outputs()
            all_findings.extend(findings)
    
    if all_findings:
        # Deduplicate findings by (type, function, contract)
        unique_findings = []
        seen = set()
        for finding in all_findings:
            key = (finding['type'], finding['function'], finding['contract'])
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        
        # Save to output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(unique_findings, f, indent=2)
        
        logger.info(f"✓ Saved {len(unique_findings)} unique findings to {args.output}")
        return 0
    else:
        logger.warning("No findings extracted from Medusa outputs")
        return 1


if __name__ == '__main__':
    sys.exit(main())
