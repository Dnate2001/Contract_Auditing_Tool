# Example PR Comment Output

## Scenario 1: Vulnerabilities Found

```markdown
## 🛡️ Security Audit Results

**Total Findings**: 5
- 🔴 Critical: 2
- 🟠 High: 2
- 🟡 Medium: 1

### Top Findings

1. **[CRITICAL]** Unauthorized Minting in mint
2. **[CRITICAL]** Unprotected Selfdestruct in destroy
3. **[HIGH]** Reentrancy Vulnerability in transfer

*...and 2 more findings*

📊 View detailed report in workflow artifacts.
```

## Scenario 2: No Vulnerabilities

```markdown
## 🛡️ Security Audit Results

**Total Findings**: 0
- 🔴 Critical: 0
- 🟠 High: 0
- 🟡 Medium: 0

✅ No vulnerabilities detected!

📊 View detailed report in workflow artifacts.
```

## Scenario 3: Audit Error

```markdown
## ⚠️ Security Audit Warning

The security audit encountered an issue: Timeout after 60 seconds

Please review the workflow logs for details.
```

## Scenario 4: Missing Tools

```markdown
## ⚠️ Security Audit Warning

The security audit encountered an issue: Medusa not installed

Please review the workflow logs for details.
```

---

## Workflow Features

### ✅ Implemented

1. **Triggers on PR** to `main` or `develop` branches
2. **Installs all dependencies**:
   - Python 3.12 with caching
   - Go 1.21 for Medusa
   - Foundry toolchain
   - Solidity compiler v0.8.20
3. **Runs audit** with 60s timeout
4. **Uploads artifacts**:
   - `report.json` (standardized format)
   - `report.sarif.json` (for GitHub Security)
   - `reproducers/` (test files)
5. **Posts PR comment** with summary
6. **Uploads SARIF** to GitHub Code Scanning
7. **Fails on critical issues** (blocks merge)

### 🛡️ Error Handling

- `continue-on-error: true` on dependency installation
- Graceful degradation if tools missing
- Warning comments instead of hard failures
- Timeout protection (60s for audit, 15min for job)

### 🔒 Security

- Uses `secrets.GEMINI_API_KEY` for AI analysis
- Read-only checkout
- Write permissions only for PR comments
- SARIF upload to Security tab

### 📊 Artifacts

All artifacts retained for 30 days:
- Full JSON report
- SARIF report (GitHub Security integration)
- Reproducer test files

### 🚦 Status Checks

- ✅ Green: No critical issues
- ❌ Red: Critical vulnerabilities found
- ⚠️ Yellow: Audit warnings (still passes)

---

## Usage

### Setup

1. Add workflow file to `.github/workflows/audit.yml`
2. Add `GEMINI_API_KEY` to repository secrets
3. Create PR with contract changes

### Viewing Results

**In PR:**
- Comment appears automatically with summary
- Click "Details" on status check for full logs

**In Security Tab:**
- Navigate to Security → Code scanning
- View SARIF results with line-level annotations

**In Artifacts:**
- Go to workflow run
- Download `security-audit-report.zip`
- Contains JSON, SARIF, and reproducers

### Local Testing

```bash
# Simulate CI environment
export GEMINI_API_KEY="your-key"

# Run audit (60s timeout like CI)
timeout 60 python3 auditor_ai.py 5

# Generate reports
python3 tools/exporters.py artifacts/findings.json

# View results
cat artifacts/report.json | jq
```

---

## Customization

### Adjust Timeout

```yaml
# In audit.yml, line ~70
timeout 60 python3 auditor_ai.py 5
# Change to:
timeout 120 python3 auditor_ai.py 10  # 2 minutes, 10 iterations
```

### Change Severity Threshold

```yaml
# In audit.yml, last step
critical = [f for f in findings if f.get('severity', '').lower() == 'critical']
# Change to:
high_or_critical = [f for f in findings if f.get('severity', '').lower() in ['critical', 'high']]
```

### Add Slack Notifications

```yaml
- name: Notify Slack
  if: steps.audit.outputs.audit_success == 'true'
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Security audit found ${{ steps.summary.outputs.total }} issues"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Troubleshooting

### Workflow Fails to Install Medusa

**Solution**: Medusa installation has `continue-on-error: true`, so workflow continues with warning

### Timeout Issues

**Solution**: Increase timeout or reduce fuzzing iterations:
```yaml
timeout 120 python3 auditor_ai.py 3  # Fewer iterations
```

### API Key Not Working

**Solution**: Verify secret is set:
1. Go to Settings → Secrets → Actions
2. Add `GEMINI_API_KEY`
3. Re-run workflow

### No PR Comment Posted

**Solution**: Check permissions:
```yaml
permissions:
  pull-requests: write  # Required for comments
```

---

## Integration with Branch Protection

### Require Audit to Pass

1. Go to Settings → Branches
2. Add rule for `main`
3. Enable "Require status checks to pass"
4. Select "security-audit"
5. Enable "Require branches to be up to date"

### Block Critical Issues

The workflow automatically fails if critical vulnerabilities are found, preventing merge.

---

## Performance

- **Average runtime**: 2-3 minutes
- **Timeout**: 60 seconds for audit, 15 minutes total
- **Caching**: Python dependencies cached
- **Parallel**: Runs in parallel with other checks

---

## Future Enhancements

- [ ] Cache Medusa installation
- [ ] Parallel contract analysis
- [ ] Incremental analysis (only changed contracts)
- [ ] Historical trend tracking
- [ ] Integration with Jira/Linear for issue creation
- [ ] Custom severity thresholds per repo
