# Report Exporters Documentation

## Overview

The Report Exporters (`tools/exporters.py`) generate standardized reports in multiple formats from audit findings, including SARIF v2.1 for IDE/CI integration and JSON for programmatic access.

## Features

### 1. Standardized JSON Export
Clean, structured JSON format with all vulnerability details.

### 2. SARIF v2.1 Export
Industry-standard format compatible with:
- GitHub Code Scanning
- VS Code
- Azure DevOps
- GitLab
- Other SARIF-compatible tools

### 3. Deterministic Severity Mapping
Rule-based severity classification for consistency.

### 4. CWE Classification
Automatic Common Weakness Enumeration mapping.

## Severity Mapping Rules

### Critical
- Unauthorized Minting
- Unrestricted Delegatecall
- Unprotected Selfdestruct

### High
- Reentrancy Vulnerability
- Access Control Violation
- Integer Overflow/Underflow

### Medium
- Weak Randomness
- Unchecked Return Value
- Denial of Service

### Low
- Code quality issues
- Gas optimizations

## CWE Mappings

| Vulnerability Type | CWE |
|-------------------|-----|
| Unauthorized Minting | CWE-284 (Improper Access Control) |
| Reentrancy | CWE-841 (Behavioral Workflow) |
| Unrestricted Delegatecall | CWE-829 (Untrusted Control) |
| Weak Randomness | CWE-338 (Weak PRNG) |
| Unprotected Selfdestruct | CWE-284 (Access Control) |
| Integer Overflow | CWE-190 |
| Integer Underflow | CWE-191 |

## Usage

### Export Both Formats
```bash
python3 tools/exporters.py artifacts/findings.json --contract BrokenToken
```

**Output:**
```
✓ Exported 2 findings to artifacts/report.json
✓ Exported SARIF report to artifacts/report.sarif.json
```

### Export JSON Only
```bash
python3 tools/exporters.py artifacts/findings.json --format json
```

### Export SARIF Only
```bash
python3 tools/exporters.py artifacts/findings.json --format sarif
```

### Custom Output Directory
```bash
python3 tools/exporters.py artifacts/findings.json --output-dir reports
```

## JSON Report Format

```json
[
  {
    "id": "54753d2e447c4e2c",
    "title": "Unauthorized Minting in mint",
    "description": "Property violated: anyone can mint tokens",
    "severity": "critical",
    "contract": "BrokenToken",
    "function": "mint",
    "line": 45,
    "evidence_files": ["medusa-reports/fixture1.json"],
    "confidence": "supported",
    "requires_manual_review": false,
    "cwe": "CWE-284",
    "suggested_fix": "function mint() public onlyOwner { ... }",
    "explanation": "The mint() function lacks access control...",
    "impact": "An attacker can mint unlimited tokens...",
    "exploit_scenario": "1. Attacker calls mint()...",
    "prevention": "Use OpenZeppelin's Ownable...",
    "reproducer_command": "forge test --match-path 'artifacts/reproducers/finding_1_54753d2e/ReproTest.sol' -vvv",
    "timestamp": "2026-01-16T10:30:45Z"
  }
]
```

## SARIF Report Format

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Antigravity Smart Contract Auditor",
          "version": "1.0.0",
          "rules": [
            {
              "id": "unauthorized-minting",
              "name": "Unauthorized Minting",
              "defaultConfiguration": {"level": "error"},
              "properties": {
                "cwe": "CWE-284",
                "tags": ["security", "smart-contract"]
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "unauthorized-minting",
          "level": "error",
          "message": {"text": "Property violated: anyone can mint tokens"},
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {"uri": "contracts/BrokenToken.sol"},
                "region": {"startLine": 45}
              }
            }
          ],
          "properties": {
            "confidence": "supported",
            "reproducer_command": "forge test ..."
          }
        }
      ]
    }
  ]
}
```

## Validation

### Validate SARIF Output
```bash
python3 tools/validate_sarif.py artifacts/report.sarif.json
```

**Output:**
```
✅ SARIF file is valid!
   Tool: Antigravity Smart Contract Auditor
   Results: 2
   Rules: 2
```

## Integration Examples

### GitHub Code Scanning

Upload SARIF to GitHub:

```yaml
# .github/workflows/audit.yml
- name: Run Audit
  run: python3 auditor_ai.py 30

- name: Export SARIF
  run: python3 tools/exporters.py artifacts/findings.json --format sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: artifacts/report.sarif.json
```

### VS Code Integration

1. Install SARIF Viewer extension
2. Open `artifacts/report.sarif.json`
3. View findings in Problems panel

### CI/CD Pipeline

```bash
# Run audit
python3 auditor_ai.py 30

# Export reports
python3 tools/exporters.py artifacts/findings.json

# Validate SARIF
python3 tools/validate_sarif.py artifacts/report.sarif.json

# Fail if critical issues found
jq -e '.[] | select(.severity == "critical")' artifacts/report.json && exit 1
```

## Severity Determination Logic

The exporter uses a multi-tier approach:

1. **Explicit Severity**: Use if provided in finding
2. **Type-Based Mapping**: Match vulnerability type to severity rules
3. **AI Analysis Impact**: Parse impact description for severity keywords
4. **Default**: Medium severity if no other indicators

```python
def map_severity(vulnerability):
    # 1. Check explicit severity
    if 'severity' in vulnerability:
        return vulnerability['severity'].lower()
    
    # 2. Check type mapping
    if vulnerability['type'] in SEVERITY_RULES:
        return SEVERITY_RULES[vulnerability['type']]
    
    # 3. Check AI impact
    impact = vulnerability.get('ai_analysis', {}).get('impact', '')
    if 'critical' in impact.lower():
        return 'critical'
    
    # 4. Default
    return 'medium'
```

## Field Descriptions

### Standardized JSON Fields

- **id**: Unique hash identifier (MD5 of contract+function+type+line)
- **title**: Human-readable vulnerability title
- **description**: Brief description from fuzzer
- **severity**: critical|high|medium|low
- **contract**: Contract name
- **function**: Vulnerable function
- **line**: Line number
- **evidence_files**: Paths to evidence (Medusa outputs)
- **confidence**: supported|partial|unsupported|simulated
- **requires_manual_review**: Boolean flag
- **cwe**: CWE identifier (e.g., "CWE-284")
- **suggested_fix**: Code fix from AI
- **explanation**: Technical explanation from AI
- **impact**: Impact analysis from AI
- **exploit_scenario**: Step-by-step attack from AI
- **prevention**: Prevention best practices from AI
- **reproducer_command**: Command to run reproducer test
- **timestamp**: ISO 8601 timestamp

## Best Practices

### 1. Version Control
- Commit `report.json` for tracking
- Use `.gitignore` for large SARIF files
- Tag reports with version/date

### 2. CI/CD Integration
- Fail builds on critical findings
- Upload SARIF to code scanning
- Archive reports as artifacts

### 3. Report Distribution
- Share JSON with developers
- Upload SARIF to security dashboards
- Include in audit documentation

### 4. Severity Consistency
- Use deterministic mapping
- Document custom severity rules
- Review AI-assigned severities

## Troubleshooting

### Invalid SARIF
```
❌ Missing required field: $schema
```
**Solution**: Ensure findings have all required fields

### Missing CWE
```
"cwe": null
```
**Solution**: Add vulnerability type to CWE_MAPPINGS

### Wrong Severity
```
"severity": "medium"  # Expected: "critical"
```
**Solution**: Update SEVERITY_RULES or add explicit severity to finding

## Future Enhancements

- [ ] HTML report generation
- [ ] PDF export
- [ ] Custom severity rules via config
- [ ] SARIF 2.2 support
- [ ] Integration with SonarQube
- [ ] Markdown report generation

---

**Status**: ✅ Production Ready  
**Formats**: JSON, SARIF v2.1  
**Validation**: Included  
**CWE Mappings**: 10 vulnerability types
