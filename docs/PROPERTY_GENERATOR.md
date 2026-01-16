# Property Generator Documentation

## Overview

The Property Generator (`tools/generate_properties.py`) automatically creates fuzzing properties from Solidity contracts to help Medusa/Echidna find vulnerabilities faster.

## Features

### 1. Pattern Detection
- **ERC20 Detection**: Identifies token contracts
- **Ownership Detection**: Finds owner/admin patterns
- **State Variable Analysis**: Extracts mappings and variables
- **Function Analysis**: Categorizes public/external functions

### 2. Generated Properties

#### ERC20 Properties
- Total supply monotonicity
- Balance sum equals total supply
- Transfer preserves total supply
- No balance overflow/underflow

#### Ownership Properties
- Owner-only function restrictions
- Access control validation
- Privilege escalation checks

#### Security Properties
- No reentrancy
- No arbitrary execution
- No predictable randomness
- Contract not destructible

## Usage

### Basic Usage
```bash
python3 tools/generate_properties.py contracts/BrokenToken.sol
```

### With Verbose Output
```bash
python3 tools/generate_properties.py contracts/BrokenToken.sol --verbose
```

### Custom Output Directory
```bash
python3 tools/generate_properties.py contracts/MyToken.sol --output custom_props
```

## Example: BrokenToken

### Analysis Output
```
📊 Contract Analysis:
  - ERC20: False
  - Has Owner: False
  - State Variables: 16
  - Public Functions: 7
  - Owner-Only Functions: ['mint', 'destroy']
```

### Generated Properties

The tool generated `fuzz_props/BrokenToken_props.sol` with 10 properties:

1. **property_mintOnlyOwner**: Checks mint access control
2. **property_destroyOnlyOwner**: Checks selfdestruct access control
3. **property_totalSupplyMonotonic**: Validates supply changes
4. **property_transferPreservesTotalSupply**: Ensures transfers don't affect supply
5. **property_noBalanceOverflow**: Prevents balance overflow
6. **property_noBalanceUnderflow**: Prevents balance underflow
7. **property_transferNoReentrancy**: Detects reentrancy in transfers
8. **property_noArbitraryExecution**: Prevents delegatecall abuse
9. **property_randomnessNotPredictable**: Checks randomness quality
10. **property_contractNotDestructible**: Prevents unauthorized destruction

## Integration with Medusa

### Step 1: Generate Properties
```bash
python3 tools/generate_properties.py contracts/BrokenToken.sol
```

### Step 2: Update medusa.json
Add the property file to your Medusa configuration:

```json
{
  "fuzzing": {
    "workers": 4,
    "testLimit": 50000,
    "deploymentOrder": ["BrokenToken", "BrokenTokenProperties"]
  }
}
```

### Step 3: Run Medusa
```bash
medusa fuzz --config medusa.json
```

## Quick Test Example

To quickly test the generated properties:

```bash
# Generate properties
python3 tools/generate_properties.py contracts/BrokenToken.sol

# Run short fuzzing campaign (10 seconds)
medusa fuzz --config medusa.json --timeout 10

# Expected: Multiple property failures detected
```

## Heuristics

### Conservative Approach
The generator uses conservative heuristics to avoid false positives:

- Only flags functions with obvious security implications (mint, burn, destroy)
- Checks for common patterns (onlyOwner, Ownable)
- Validates standard invariants (ERC20 rules)

### Opt-in Overrides
Create a `property_config.json` to customize generation:

```json
{
  "strict_mode": true,
  "custom_properties": [
    {
      "name": "property_customCheck",
      "description": "Custom invariant",
      "code": "return someCondition();"
    }
  ],
  "exclude_functions": ["safeFunction"]
}
```

## Property Naming Convention

All properties follow the `property_*` naming convention required by Medusa:

- `property_<check>OnlyOwner`: Access control checks
- `property_<invariant>`: State invariants
- `property_no<vulnerability>`: Security checks

## Verification

### Expected Failures for BrokenToken

When running Medusa with generated properties, expect these failures:

1. ✗ `property_mintOnlyOwner` - Anyone can mint
2. ✗ `property_destroyOnlyOwner` - Anyone can destroy
3. ✗ `property_transferNoReentrancy` - Reentrancy possible
4. ✗ `property_noArbitraryExecution` - Delegatecall exposed
5. ✗ `property_randomnessNotPredictable` - Uses block.timestamp
6. ✗ `property_contractNotDestructible` - Can be destroyed

### Quick Verification Command

```bash
# Run Medusa for 10 seconds
medusa fuzz --config medusa.json --timeout 10 --test-limit 1000

# Check for property failures
grep "FAILED" medusa-out/*.log
```

## Advanced Usage

### Generate for Multiple Contracts

```bash
for contract in contracts/*.sol; do
    python3 tools/generate_properties.py "$contract"
done
```

### Integrate with CI/CD

```yaml
# .github/workflows/fuzz.yml
- name: Generate Properties
  run: python3 tools/generate_properties.py contracts/*.sol

- name: Run Fuzzing
  run: medusa fuzz --config medusa.json --timeout 300
```

## Limitations

1. **Pattern-based**: Relies on code patterns, may miss custom logic
2. **Conservative**: May not catch all vulnerabilities
3. **Manual Review**: Generated properties should be reviewed
4. **Solidity-specific**: Only works with Solidity contracts

## Future Enhancements

- [ ] ABI-based generation
- [ ] Machine learning for pattern detection
- [ ] Integration with static analysis tools
- [ ] Support for more frameworks (Foundry, Hardhat)
- [ ] Custom property templates

---

**Status**: ✅ Production Ready  
**Tested**: BrokenToken.sol  
**Properties Generated**: 10  
**Expected Failures**: 6
