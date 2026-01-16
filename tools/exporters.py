#!/usr/bin/env python3
"""
Report Exporters for Smart Contract Auditing Tool
Generates SARIF v2.1 and standardized JSON reports
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib


class SeverityMapper:
    """Deterministic severity mapping based on vulnerability characteristics"""
    
    # CWE mappings for common smart contract vulnerabilities
    CWE_MAPPINGS = {
        "Unauthorized Minting": "CWE-284",  # Improper Access Control
        "Reentrancy Vulnerability": "CWE-841",  # Improper Enforcement of Behavioral Workflow
        "Unrestricted Delegatecall": "CWE-829",  # Inclusion of Functionality from Untrusted Control Sphere
        "Weak Randomness": "CWE-338",  # Use of Cryptographically Weak PRNG
        "Unprotected Selfdestruct": "CWE-284",  # Improper Access Control
        "Integer Overflow": "CWE-190",  # Integer Overflow
        "Integer Underflow": "CWE-191",  # Integer Underflow
        "Access Control Violation": "CWE-284",  # Improper Access Control
        "Unchecked Return Value": "CWE-252",  # Unchecked Return Value
        "Denial of Service": "CWE-400",  # Uncontrolled Resource Consumption
    }
    
    # Severity rules based on vulnerability type and evidence
    SEVERITY_RULES = {
        "Unauthorized Minting": "critical",
        "Unrestricted Delegatecall": "critical",
        "Unprotected Selfdestruct": "critical",
        "Reentrancy Vulnerability": "high",
        "Access Control Violation": "high",
        "Integer Overflow": "high",
        "Integer Underflow": "high",
        "Weak Randomness": "medium",
        "Unchecked Return Value": "medium",
        "Denial of Service": "medium",
    }
    
    @classmethod
    def map_severity(cls, vulnerability: Dict) -> str:
        """
        Deterministically map vulnerability to severity level
        
        Priority:
        1. Explicit severity field
        2. Vulnerability type mapping
        3. AI analysis impact
        4. Default to medium
        """
        # Check explicit severity
        if 'severity' in vulnerability:
            return vulnerability['severity'].lower()
        
        # Check type-based mapping
        vuln_type = vulnerability.get('type', '')
        if vuln_type in cls.SEVERITY_RULES:
            return cls.SEVERITY_RULES[vuln_type]
        
        # Check AI analysis impact
        ai_analysis = vulnerability.get('ai_analysis', {})
        impact = ai_analysis.get('impact', '').lower()
        
        if any(word in impact for word in ['critical', 'catastrophic', 'total loss']):
            return 'critical'
        elif any(word in impact for word in ['severe', 'significant', 'major']):
            return 'high'
        elif any(word in impact for word in ['moderate', 'medium']):
            return 'medium'
        
        # Default
        return 'medium'
    
    @classmethod
    def get_cwe(cls, vulnerability: Dict) -> Optional[str]:
        """Get CWE identifier for vulnerability"""
        vuln_type = vulnerability.get('type', '')
        return cls.CWE_MAPPINGS.get(vuln_type)


class ReportExporter:
    """Export findings to various formats"""
    
    def __init__(self, findings: List[Dict], contract_name: str = "Contract"):
        self.findings = findings
        self.contract_name = contract_name
        self.severity_mapper = SeverityMapper()
    
    def export_json(self, output_path: Path) -> Path:
        """
        Export to standardized JSON format
        
        Format:
        {
          "id": "unique-hash",
          "title": "Vulnerability Title",
          "description": "Detailed description",
          "severity": "critical|high|medium|low",
          "evidence_files": ["path/to/evidence"],
          "confidence": "supported|partial|unsupported",
          "cwe": "CWE-XXX",
          "suggested_fix": "Code fix",
          "reproducer_command": "forge test ..."
        }
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        standardized_findings = []
        
        for idx, finding in enumerate(self.findings, 1):
            # Generate unique ID
            finding_id = self._generate_id(finding)
            
            # Map severity
            severity = self.severity_mapper.map_severity(finding)
            
            # Get CWE
            cwe = self.severity_mapper.get_cwe(finding)
            
            # Extract AI analysis
            ai_analysis = finding.get('ai_analysis', {})
            
            # Build standardized finding
            standardized = {
                "id": finding_id,
                "title": f"{finding.get('type', 'Unknown Vulnerability')} in {finding.get('function', 'unknown')}",
                "description": finding.get('description', 'No description available'),
                "severity": severity,
                "contract": finding.get('contract', self.contract_name),
                "function": finding.get('function', 'unknown'),
                "line": finding.get('line', 0),
                "evidence_files": finding.get('evidence_files', []),
                "confidence": ai_analysis.get('support', 'unknown'),
                "requires_manual_review": ai_analysis.get('requires_manual_review', True),
                "cwe": cwe,
                "suggested_fix": ai_analysis.get('recommended_fix', ''),
                "explanation": ai_analysis.get('explanation', ''),
                "impact": ai_analysis.get('impact', ''),
                "exploit_scenario": ai_analysis.get('exploit_scenario', ''),
                "prevention": ai_analysis.get('prevention', ''),
                "reproducer_command": self._generate_reproducer_command(finding, idx),
                "timestamp": finding.get('timestamp', datetime.now().isoformat())
            }
            
            standardized_findings.append(standardized)
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(standardized_findings, f, indent=2)
        
        print(f"✓ Exported {len(standardized_findings)} findings to {output_path}")
        return output_path
    
    def export_sarif(self, output_path: Path) -> Path:
        """
        Export to SARIF v2.1 format
        
        SARIF is the Static Analysis Results Interchange Format
        Used by GitHub, VS Code, and other tools
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build SARIF structure
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Antigravity Smart Contract Auditor",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/yourusername/antigravity-auditor",
                            "rules": self._generate_sarif_rules()
                        }
                    },
                    "results": self._generate_sarif_results(),
                    "properties": {
                        "contract": self.contract_name,
                        "generatedAt": datetime.now().isoformat()
                    }
                }
            ]
        }
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(sarif, f, indent=2)
        
        print(f"✓ Exported SARIF report to {output_path}")
        return output_path
    
    def _generate_sarif_rules(self) -> List[Dict]:
        """Generate SARIF rule definitions"""
        rules = []
        seen_types = set()
        
        for finding in self.findings:
            vuln_type = finding.get('type', 'Unknown')
            if vuln_type in seen_types:
                continue
            seen_types.add(vuln_type)
            
            rule_id = self._generate_rule_id(vuln_type)
            severity = self.severity_mapper.map_severity(finding)
            cwe = self.severity_mapper.get_cwe(finding)
            
            rule = {
                "id": rule_id,
                "name": vuln_type,
                "shortDescription": {
                    "text": vuln_type
                },
                "fullDescription": {
                    "text": finding.get('description', vuln_type)
                },
                "defaultConfiguration": {
                    "level": self._sarif_level(severity)
                },
                "properties": {
                    "tags": ["security", "smart-contract"],
                    "precision": "high"
                }
            }
            
            if cwe:
                rule["properties"]["cwe"] = cwe
            
            rules.append(rule)
        
        return rules
    
    def _generate_sarif_results(self) -> List[Dict]:
        """Generate SARIF results"""
        results = []
        
        for idx, finding in enumerate(self.findings, 1):
            vuln_type = finding.get('type', 'Unknown')
            rule_id = self._generate_rule_id(vuln_type)
            severity = self.severity_mapper.map_severity(finding)
            
            ai_analysis = finding.get('ai_analysis', {})
            
            result = {
                "ruleId": rule_id,
                "ruleIndex": 0,  # Simplified
                "level": self._sarif_level(severity),
                "message": {
                    "text": finding.get('description', vuln_type)
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": f"contracts/{finding.get('contract', self.contract_name)}.sol"
                            },
                            "region": {
                                "startLine": finding.get('line', 1),
                                "snippet": {
                                    "text": finding.get('function', '')
                                }
                            }
                        }
                    }
                ],
                "properties": {
                    "confidence": ai_analysis.get('support', 'unknown'),
                    "requires_manual_review": ai_analysis.get('requires_manual_review', True),
                    "reproducer_command": self._generate_reproducer_command(finding, idx)
                }
            }
            
            # Add fix if available
            if ai_analysis.get('recommended_fix'):
                result["fixes"] = [
                    {
                        "description": {
                            "text": "Apply recommended fix"
                        },
                        "artifactChanges": [
                            {
                                "artifactLocation": {
                                    "uri": f"contracts/{finding.get('contract', self.contract_name)}.sol"
                                },
                                "replacements": [
                                    {
                                        "deletedRegion": {
                                            "startLine": finding.get('line', 1)
                                        },
                                        "insertedContent": {
                                            "text": ai_analysis.get('recommended_fix', '')
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            
            results.append(result)
        
        return results
    
    def _generate_id(self, finding: Dict) -> str:
        """Generate unique ID for finding"""
        content = f"{finding.get('contract')}{finding.get('function')}{finding.get('type')}{finding.get('line')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_rule_id(self, vuln_type: str) -> str:
        """Generate SARIF rule ID"""
        return vuln_type.replace(' ', '-').replace('/', '-').lower()
    
    def _sarif_level(self, severity: str) -> str:
        """Map severity to SARIF level"""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note'
        }
        return mapping.get(severity.lower(), 'warning')
    
    def _generate_reproducer_command(self, finding: Dict, idx: int) -> str:
        """Generate reproducer command"""
        finding_hash = self._generate_id(finding)[:8]
        return f"forge test --match-path 'artifacts/reproducers/finding_{idx}_{finding_hash}/ReproTest.sol' -vvv"


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Export audit findings to various formats'
    )
    parser.add_argument(
        'findings',
        help='Path to findings JSON file'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'sarif', 'both'],
        default='both',
        help='Export format'
    )
    parser.add_argument(
        '--output-dir',
        default='artifacts',
        help='Output directory'
    )
    parser.add_argument(
        '--contract',
        default='Contract',
        help='Contract name'
    )
    
    args = parser.parse_args()
    
    # Load findings
    with open(args.findings) as f:
        findings = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(findings, dict) and 'vulnerabilities' in findings:
        findings = findings['vulnerabilities']
    
    exporter = ReportExporter(findings, args.contract)
    
    output_dir = Path(args.output_dir)
    
    # Export based on format
    if args.format in ['json', 'both']:
        exporter.export_json(output_dir / 'report.json')
    
    if args.format in ['sarif', 'both']:
        exporter.export_sarif(output_dir / 'report.sarif.json')
    
    print(f"\n✅ Export complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
