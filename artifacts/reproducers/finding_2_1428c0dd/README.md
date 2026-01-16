# Reproducer for Finding #2

## Vulnerability Details

- **Type**: Reentrancy Vulnerability
- **Severity**: HIGH
- **Contract**: BrokenToken
- **Function**: transfer
- **Line**: 35

## Description

Reentrancy detected in transfer

## Property Failed

property_transferNoReentrancy

## How to Run

### Using Foundry

```bash
# Run this specific test
forge test --match-path artifacts/reproducers/finding_2_*/ReproTest.sol -vvv

# Or run with more verbosity to see traces
forge test --match-path artifacts/reproducers/finding_2_*/ReproTest.sol -vvvv
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
1. 0xattacker... -> transfer(address,uint256) (value: 0)
2. 0xmaliciou... -> transfer(address,uint256) (value: 0)
```

## Evidence Files

/home/user/.gemini/antigravity/playground/electric-hawking/medusa-reports/fixture1.json

## Timestamp

2026-01-16T10:31:22Z
