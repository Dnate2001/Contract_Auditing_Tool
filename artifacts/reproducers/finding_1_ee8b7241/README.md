# Reproducer for Finding #1

## Vulnerability Details

- **Type**: Unauthorized Minting
- **Severity**: CRITICAL
- **Contract**: BrokenToken
- **Function**: mint
- **Line**: 45

## Description

Property violated: anyone can mint tokens

## Property Failed

property_onlyOwnerCanMint

## How to Run

### Using Foundry

```bash
# Run this specific test
forge test --match-path artifacts/reproducers/finding_1_*/ReproTest.sol -vvv

# Or run with more verbosity to see traces
forge test --match-path artifacts/reproducers/finding_1_*/ReproTest.sol -vvvv
```

### Expected Behavior

This test reproduces the vulnerability by:
1. Deploying the target contract
2. Setting up test accounts
3. Replaying the call sequence that triggered the vulnerability
4. Asserting that the vulnerability condition is met

**Note**: The test passing indicates the vulnerability is reproducible.

## Call Sequence

```
1. 0x12345678... -> mint(address,uint256) (value: 0)
```

## Evidence Files

/home/user/.gemini/antigravity/playground/electric-hawking/medusa-reports/fixture1.json

## Timestamp

2026-01-16T10:30:45Z
