# Architecture & Operational Flow - Contract Auditing Tool

## Architecture Summary

The Contract Auditing Tool is a hybrid fuzzing + AI analysis system that combines Medusa property-based testing with Google Gemini AI to detect and explain smart contract vulnerabilities. The architecture follows a pipeline: fuzzing generates crash sequences, a parser extracts canonical findings, an AI analyzer provides human-readable explanations, an evidence validator prevents hallucinations by grounding AI output in actual call traces, a reproducer generator creates Foundry tests, and exporters produce SARIF/JSON reports for CI/CD integration. The system gracefully degrades to simulation mode when API keys are unavailable, ensuring zero-downtime operation.

## End-to-End Dataflow

```
┌──────┐    ┌────────────┐    ┌────────┐    ┌────────┐    ┌───────────┐
│ User │───▶│ auditor_ai │───▶│ Medusa │───▶│ Parser │───▶│ AI        │
└──────┘    │  .py       │    │ Fuzzer │    │        │    │ Analyzer  │
            └────────────┘    └────────┘    └────────┘    └─────┬─────┘
                                                                 │
            ┌────────────────────────────────────────────────────┘
            │
            ▼
      ┌──────────┐    ┌────────────┐    ┌──────────┐    ┌────────┐
      │Evidence  │───▶│ Reproducer │───▶│ Exporter │───▶│ UI/    │
      │Validator │    │ Generator  │    │          │    │ Report │
      └──────────┘    └────────────┘    └──────────┘    └────────┘
            │                                  │
            ▼                                  ▼
      artifacts/                         artifacts/
      validated_findings.json            report.sarif.json
                                         report.json
```

## Component Details

### 1. Main Auditor (`auditor_ai.py`)

**Purpose**: Orchestrates the entire audit pipeline with Rich terminal UI.

**Inputs**: 
- `contracts/*.sol` - Solidity source files
- `medusa.json` - Fuzzer configuration
- `GEMINI_API_KEY` env var (optional)

**Outputs**:
- `audit_report.md` - Markdown report
- `audit_report.json` - JSON findings

**Key Design**: Uses Rich library for live progress bars. Falls back to simulation mode if API unavailable. Runs Medusa via subprocess with 5-60s timeout.

**Limitations**: Hardcoded to BrokenToken.sol in demo mode. Medusa path must be in $PATH.

---

### 2. Medusa Parser (`tools/parse_medusa.py`)

**Purpose**: Extracts vulnerabilities from Medusa JSON output (structured or newline-delimited).

**Inputs**: `medusa-reports/*.json` or `medusa-out/corpus/*.json`

**Output Schema** (`artifacts/findings.json`):
```json
[
  {
    "type": "Unauthorized Minting",
    "function": "mint(address,uint256)",
    "description": "Property violated: anyone can mint",
    "line": 45,
    "sequence": [{"function": "mint", "sender": "0x123"}],
    "raw_trace": "...",
    "timestamp": "2026-01-16T10:30:45Z"
  }
]
```

**Key Design**: Defensive parsing handles malformed JSON. Deduplicates findings by (type, function, line).

**Command**:
```bash
python3 tools/parse_medusa.py --input medusa-reports --output artifacts/findings.json
```

---

### 3. AI Analyzer (`ai_analyzer.py`)

**Purpose**: Generates human-readable explanations using Gemini 2.5 Flash with retry logic and evidence validation.

**Inputs**: 
- `artifacts/findings.json`
- Contract source code
- `GEMINI_API_KEY`

**Outputs**: Enriched findings with `ai_analysis` field containing:
```json
{
  "explanation": "The mint() function lacks access control...",
  "impact": "Attacker can mint unlimited tokens...",
  "exploit_scenario": "1. Attacker calls mint()...",
  "recommended_fix": "function mint() public onlyOwner {...}",
  "prevention": "Use OpenZeppelin Ownable",
  "support": "partial",
  "requires_manual_review": true,
  "validation_details": {...}
}
```

**Key Design**: 
- **Retry Logic**: 2 retries with exponential backoff (1s, 2s)
- **Timeout**: 10s per API call
- **Fallback**: Simulation mode with heuristic-based analysis

**Validation Logic**:
- **supported**: ≥2/3 checks pass (function in trace, fix in source, scenario matches sequence)
- **partial**: 1/3 checks pass
- **unsupported**: 0/3 checks pass
- **simulated**: No API key, using fallback data

---

### 4. Evidence Validator (`ai_analyzer.py:EvidenceValidator`)

**Purpose**: Prevents LLM hallucinations by verifying AI output against actual fuzzing evidence.

**Validation Checks**:
1. **Function Match**: AI-mentioned function appears in call sequence
2. **Code Fix Presence**: Recommended fix references actual source code constructs
3. **Scenario Alignment**: Exploit steps match observed call trace

**Adding New Checks**:
```python
# In EvidenceValidator class
def _validate_bytecode_match(self, analysis, vuln):
    """Check if AI mentions actual opcodes from trace"""
    if 'DELEGATECALL' in vuln.get('raw_trace', ''):
        return 'delegatecall' in analysis.get('explanation', '').lower()
    return False
```

---

### 5. Reproducer Generator (`tools/generate_reproducer.py`)

**Purpose**: Creates Foundry test files from findings for deterministic reproduction.

**Output Location**: `artifacts/reproducers/finding_{idx}_{hash}/ReproTest.sol`

**Example Reproducer**:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../../contracts/BrokenToken.sol";

contract ReproTest is Test {
    BrokenToken token;
    
    function setUp() public {
        token = new BrokenToken();
    }
    
    function testUnauthorizedMinting() public {
        address attacker = address(0x123);
        vm.prank(attacker);
        token.mint(attacker, 1000000);
        assertEq(token.balanceOf(attacker), 1000000);
    }
}
```

**Run Command**:
```bash
forge test --match-path 'artifacts/reproducers/finding_1_*/ReproTest.sol' -vvv
```

---

### 6. Exporter (`tools/exporters.py`)

**Purpose**: Generates SARIF v2.1 and standardized JSON for CI/CD integration.

**Outputs**:
- `artifacts/report.json` - Standardized format
- `artifacts/report.sarif.json` - GitHub Security compatible

**Severity Mapping**:
- CRITICAL: Unauthorized minting, delegatecall, selfdestruct
- HIGH: Reentrancy, access control, overflow
- MEDIUM: Weak randomness, unchecked returns

**Command**:
```bash
python3 tools/exporters.py artifacts/findings.json --contract BrokenToken
```

---

## Operator Runbook

### Demo Run (Simulation Mode)

**Prerequisites**: Python 3.10+, solc 0.8.20

```bash
# 1. Install dependencies
pip3 install rich google-generativeai pytest

# 2. Run audit (no API key needed)
unset GEMINI_API_KEY
python3 auditor_ai.py 5

# Expected output:
# ✓ Contracts compiled
# ✓ Fuzzing complete (5 vulnerabilities)
# 📊 Validation Summary: {'partial': 5}
# ✓ Report generated: audit_report.md

# 3. View results
cat audit_report.md
cat audit_report.json | jq '.vulnerabilities[0]'
```

---

### Full Run (Real Medusa + Gemini)

**Prerequisites**: Medusa, Foundry, Gemini API key

```bash
# 1. Install Medusa
go install github.com/crytic/medusa@latest
export PATH=$PATH:$HOME/go/bin

# 2. Set API key
export GEMINI_API_KEY="your-key-here"

# 3. Run full audit
python3 auditor_ai.py 30

# 4. Generate reproducers
python3 tools/generate_reproducer.py artifacts/findings.json

# 5. Run reproducers
forge test --match-path 'artifacts/reproducers/*/ReproTest.sol' -vvv

# 6. Export SARIF
python3 tools/exporters.py artifacts/findings.json --format sarif
```

---

## CI Integration

**Minimal GitHub Actions** (`.github/workflows/audit.yml`):
```yaml
name: Security Audit
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install rich google-generativeai
      
      - name: Run audit (simulation, 60s timeout)
        run: timeout 60 python3 auditor_ai.py 3 || true
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: audit-report
          path: |
            audit_report.json
            artifacts/report.sarif.json
      
      - name: Post comment
        run: |
          CRITICAL=$(jq '[.vulnerabilities[] | select(.ai_analysis.severity=="critical")] | length' audit_report.json)
          echo "🛡️ Found $CRITICAL critical issues" >> $GITHUB_STEP_SUMMARY
```

**Timeboxing**: Use `timeout 60` for PR checks, full fuzzing (300s+) in nightly jobs.

---

## Security & Ops Checklist

- [ ] Rotate API keys every 90 days
- [ ] Enable pre-commit hooks (`pre-commit install`)
- [ ] Scan artifacts for secrets (`git secrets --scan`)
- [ ] Use `.env` for keys (never commit)
- [ ] Set rate limits (10 req/min for Gemini)
- [ ] Test model discovery fallback monthly
- [ ] Review `requires_manual_review` flags before deployment
- [ ] Archive reports with git tags (`git tag audit-v1.0`)

---

## Roadmap (Next 6-12 Weeks)

**High Priority**:
1. Automated property generation from ABI
2. Coverage-guided corpus minimization
3. Multi-contract analysis (dependencies)
4. Bytecode-level validation checks

**Medium Priority**:
5. HTML report generation
6. Integration with Slither/Mythril
7. Custom severity rules via config
8. Historical trend tracking

**Low Priority**:
9. Interactive CLI mode
10. VS Code extension
11. Slack/Discord notifications

---

## What Success Looks Like

Success is when a senior engineer can clone this repo, run `python3 auditor_ai.py 10`, and within 2 minutes receive a trustworthy audit report that clearly distinguishes evidence-backed findings from AI speculation, with reproducible test cases ready to run in Foundry, and SARIF output that integrates seamlessly into their existing CI/CD pipeline—all without needing to read documentation beyond this file.

---

## TL;DR Commands Cheat-Sheet

```bash
# Quick demo
python3 auditor_ai.py 5

# Full audit with AI
export GEMINI_API_KEY="key"
python3 auditor_ai.py 30

# Generate reproducers
python3 tools/generate_reproducer.py artifacts/findings.json

# Run reproducers
forge test --match-path 'artifacts/reproducers/*/ReproTest.sol' -vvv

# Export SARIF
python3 tools/exporters.py artifacts/findings.json --format sarif

# Validate SARIF
python3 tools/validate_sarif.py artifacts/report.sarif.json

# Run benchmarks
bash scripts/benchmark_run.sh

# Run tests
pytest tests/ -v
```
