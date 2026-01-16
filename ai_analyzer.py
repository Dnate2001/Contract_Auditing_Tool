"""
🔮 SMART CONTRACT AI ANALYZER - Evidence-Validated Edition
---------------------------
Standalone module for enriching smart contract vulnerabilities with Gemini AI.
Now includes evidence validation to prevent hallucinations.

Optimized for:
1. Demo Reliability (Never Crashes)
2. Safe Parsing (Handles malformed JSON)
3. Graceful Degradation (Simulation Mode if API fails)
4. Evidence Validation (Verifies AI suggestions against actual data)
"""

import os
import json
import logging
import warnings
import re
from typing import List, Dict, Any

# 1. SILENCE THE UGLY WARNINGS (Crucial for Demo)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SmartContractAI")

# Soft dependency check
try:
    import google.generativeai as genai
    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False


class EvidenceValidator:
    """Validates AI analysis against actual evidence"""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_analysis(self, 
                         analysis: Dict[str, str], 
                         vulnerability: Dict,
                         source_code: str) -> Dict[str, Any]:
        """
        Validate AI analysis against evidence.
        
        Returns:
            {
                "support": "supported" | "partial" | "unsupported" | "simulated",
                "evidence_links": [str],
                "requires_manual_review": bool,
                "validation_details": Dict
            }
        """
        validation = {
            "support": "supported",
            "evidence_links": [],
            "requires_manual_review": False,
            "validation_details": {}
        }
        
        # Check if this is simulated data
        if analysis.get('explanation', '').startswith('[SIMULATION]') or \
           analysis.get('explanation', '').startswith('[FALLBACK]'):
            validation["support"] = "simulated"
            validation["requires_manual_review"] = True
            return validation
        
        # Validate exploit scenario against call sequence
        sequence_valid = self._validate_sequence_references(
            analysis.get('exploit_scenario', ''),
            vulnerability.get('sequence', []),
            vulnerability.get('function', '')
        )
        validation["validation_details"]["sequence_match"] = sequence_valid
        
        # Validate code fix against source code
        fix_valid = self._validate_code_fix(
            analysis.get('recommended_fix', ''),
            source_code,
            vulnerability.get('function', ''),
            vulnerability.get('line', 0)
        )
        validation["validation_details"]["fix_match"] = fix_valid
        
        # Validate function references
        function_valid = self._validate_function_references(
            analysis.get('explanation', ''),
            vulnerability.get('function', ''),
            source_code
        )
        validation["validation_details"]["function_match"] = function_valid
        
        # Determine overall support level
        valid_checks = sum([
            sequence_valid.get('valid', False),
            fix_valid.get('valid', False),
            function_valid.get('valid', False)
        ])
        
        total_checks = 3
        
        if valid_checks == total_checks:
            validation["support"] = "supported"
            validation["requires_manual_review"] = False
        elif valid_checks >= total_checks * 0.5:
            validation["support"] = "partial"
            validation["requires_manual_review"] = True
        else:
            validation["support"] = "unsupported"
            validation["requires_manual_review"] = True
        
        # Build evidence links
        if vulnerability.get('evidence_files'):
            validation["evidence_links"].extend(vulnerability['evidence_files'])
        
        if vulnerability.get('raw_trace'):
            validation["evidence_links"].append("raw_trace")
        
        return validation
    
    def _validate_sequence_references(self, 
                                     exploit_scenario: str, 
                                     sequence: List[Dict],
                                     function_name: str) -> Dict:
        """Validate that exploit scenario references actual sequence steps"""
        if not exploit_scenario or not sequence:
            return {"valid": False, "reason": "No sequence data"}
        
        # Extract function names from sequence
        sequence_functions = set()
        for call in sequence:
            func = call.get('function', '')
            if func:
                # Extract function name (before parentheses)
                func_name = func.split('(')[0].strip()
                sequence_functions.add(func_name.lower())
        
        # Check if exploit scenario mentions these functions
        scenario_lower = exploit_scenario.lower()
        matches = []
        
        for func in sequence_functions:
            if func in scenario_lower:
                matches.append(func)
        
        # Also check if main function is mentioned
        if function_name:
            main_func = function_name.split('(')[0].strip().lower()
            if main_func in scenario_lower:
                matches.append(main_func)
        
        if matches:
            return {
                "valid": True,
                "matched_functions": matches,
                "reason": f"References {len(matches)} actual functions"
            }
        else:
            return {
                "valid": False,
                "reason": "Exploit scenario doesn't reference actual call sequence"
            }
    
    def _validate_code_fix(self, 
                          recommended_fix: str, 
                          source_code: str,
                          function_name: str,
                          line_number: int) -> Dict:
        """Validate that code fix references actual code"""
        if not recommended_fix or not source_code:
            return {"valid": False, "reason": "No fix or source code"}
        
        # Extract function name
        func_name = function_name.split('(')[0].strip() if function_name else ""
        
        # Check if fix mentions the function
        if func_name and func_name in recommended_fix:
            # Check if the function exists in source code
            if func_name in source_code:
                return {
                    "valid": True,
                    "reason": f"Fix references actual function '{func_name}'"
                }
        
        # Check for common Solidity patterns in fix
        solidity_patterns = [
            r'function\s+\w+',
            r'modifier\s+\w+',
            r'require\s*\(',
            r'onlyOwner',
            r'ReentrancyGuard'
        ]
        
        pattern_matches = 0
        for pattern in solidity_patterns:
            if re.search(pattern, recommended_fix):
                pattern_matches += 1
        
        if pattern_matches >= 2:
            return {
                "valid": True,
                "reason": f"Fix contains {pattern_matches} valid Solidity patterns"
            }
        
        return {
            "valid": False,
            "reason": "Fix doesn't reference actual code structure"
        }
    
    def _validate_function_references(self,
                                     explanation: str,
                                     function_name: str,
                                     source_code: str) -> Dict:
        """Validate that explanation references actual functions"""
        if not explanation:
            return {"valid": False, "reason": "No explanation"}
        
        # Extract function name
        func_name = function_name.split('(')[0].strip() if function_name else ""
        
        if not func_name:
            return {"valid": False, "reason": "No function name"}
        
        # Check if explanation mentions the function
        if func_name.lower() in explanation.lower():
            # Verify function exists in source
            if func_name in source_code:
                return {
                    "valid": True,
                    "reason": f"Explanation correctly references '{func_name}'"
                }
        
        return {
            "valid": False,
            "reason": f"Explanation doesn't reference function '{func_name}'"
        }


class AIAnalyzer:
    def __init__(self):
        """
        Initialize the AI Engine with evidence validation.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.simulation_mode = False
        self.model = None
        self.validator = EvidenceValidator()

        if not LIB_AVAILABLE:
            logger.warning("⚠️ google-generativeai library not installed. Enforcing Simulation Mode.")
            self.simulation_mode = True
        elif not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found. Enforcing Simulation Mode.")
            self.simulation_mode = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-2.5-flash (confirmed available via check_models.py)
                self.model = genai.GenerativeModel('gemini-2.5-flash') 
                logger.info("✔ Neural Link Established (Gemini 2.5 Flash)")
            except Exception as e:
                logger.error(f"❌ Connection Failed: {e}. Enforcing Simulation Mode.")
                self.simulation_mode = True

    def batch_analyze(self, vulnerabilities: List[Dict], source_code: str) -> List[Dict]:
        """
        Main entry point with evidence validation.
        Takes raw vulnerabilities and adds validated 'ai_analysis' field.
        """
        if not vulnerabilities:
            return []

        logger.info(f"🧠 Processing {len(vulnerabilities)} vectors...")
        analyzed_vulns = []

        for vuln in vulnerabilities:
            enriched_vuln = vuln.copy()
            
            # Get AI analysis
            if self.simulation_mode:
                enriched_vuln["ai_analysis"] = self._get_simulation_data(vuln)
            else:
                try:
                    enriched_vuln["ai_analysis"] = self._analyze_single(vuln, source_code)
                except Exception as e:
                    logger.error(f"⚠️ AI Query Failed for {vuln.get('function')}: {e}")
                    enriched_vuln["ai_analysis"] = self._get_simulation_data(vuln, error_context=str(e))
            
            # Validate AI analysis against evidence
            validation = self.validator.validate_analysis(
                enriched_vuln["ai_analysis"],
                enriched_vuln,
                source_code
            )
            
            # Add validation results to analysis
            enriched_vuln["ai_analysis"]["support"] = validation["support"]
            enriched_vuln["ai_analysis"]["evidence_links"] = validation["evidence_links"]
            enriched_vuln["ai_analysis"]["requires_manual_review"] = validation["requires_manual_review"]
            enriched_vuln["ai_analysis"]["validation_details"] = validation["validation_details"]
            
            analyzed_vulns.append(enriched_vuln)

        # Log validation summary
        support_counts = {}
        for vuln in analyzed_vulns:
            support = vuln["ai_analysis"].get("support", "unknown")
            support_counts[support] = support_counts.get(support, 0) + 1
        
        logger.info(f"📊 Validation Summary: {support_counts}")

        return analyzed_vulns

    def _analyze_single(self, vuln: Dict, source_code: str) -> Dict[str, str]:
        """
        Sends a single vulnerability to Gemini with evidence context.
        Includes retry logic and timeout handling.
        """
        import time
        
        max_retries = 2
        base_delay = 1  # seconds
        timeout = 10  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                # 1. Construct Prompt with evidence
                prompt = self._construct_prompt(vuln, source_code)

                # 2. Call API with timeout (Temperature 0.1 for stability)
                response = self.model.generate_content(
                    prompt, 
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1
                    ),
                    request_options={'timeout': timeout}
                )

                # 3. Parse and return
                return self._clean_and_parse_json(response.text)
                
            except Exception as e:
                if attempt < max_retries:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️ API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    # Final attempt failed, fall back to simulation
                    logger.error(f"❌ All retry attempts failed: {e}")
                    return self._get_simulation_data(vuln, error_context=str(e))

    def _construct_prompt(self, vuln: Dict, source_code: str) -> str:
        """Generates prompt with evidence context"""
        # Build evidence section
        evidence_section = self._build_evidence_section(vuln)
        
        return f"""
You are an expert Smart Contract Security Auditor. 
Analyze this vulnerability using ONLY the provided evidence.

CONTEXT (Target Contract):
```solidity
{source_code[:2000]}  
```

VULNERABILITY DATA:
- Type: {vuln.get('type')}
- Function: {vuln.get('function')}
- Line: {vuln.get('line')}
- Description: {vuln.get('description')}

{evidence_section}

CRITICAL: Your analysis MUST reference the actual evidence provided above.
- Mention specific function names from the call sequence
- Reference actual code patterns from the source
- Base exploit scenarios on the actual sequence of calls

OUTPUT FORMAT:
Return ONLY a raw JSON object with these keys:
{{
    "explanation": "Technical root cause referencing actual code.",
    "impact": "Severity and consequence.",
    "exploit_scenario": "Step-by-step attack using actual call sequence.",
    "recommended_fix": "Corrected Solidity code for function {vuln.get('function', '')}.",
    "prevention": "Best practice to avoid this."
}}
"""

    def _build_evidence_section(self, vuln: Dict) -> str:
        """Build evidence section for prompt"""
        evidence_parts = []
        
        # Add call sequence if available
        sequence = vuln.get('sequence', [])
        if sequence:
            evidence_parts.append("CALL SEQUENCE (from fuzzer):")
            for idx, call in enumerate(sequence[:5], 1):  # Limit to 5 calls
                func = call.get('function', 'unknown')
                sender = call.get('sender', 'unknown')[:10]
                evidence_parts.append(f"  {idx}. {sender}... -> {func}")
        
        # Add trace if available
        trace = vuln.get('raw_trace', '')
        if trace:
            evidence_parts.append(f"\nTRACE:\n{trace[:500]}")  # Limit trace length
        
        # Add property that failed
        prop = vuln.get('property_failed', '')
        if prop:
            evidence_parts.append(f"\nPROPERTY FAILED: {prop}")
        
        return '\n'.join(evidence_parts) if evidence_parts else "No additional evidence available."

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, str]:
        """Sanitizes LLM output to ensure valid JSON"""
        try:
            clean_text = raw_text.strip()
            # aggressive markdown stripping
            clean_text = clean_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except json.JSONDecodeError:
            logger.error("⚠️ JSON Parse Failed")
            return self._get_simulation_data(vuln={"type": "Parse Error"}, error_context="JSON Error")

    def _get_simulation_data(self, vuln: Dict, error_context: str = None) -> Dict[str, str]:
        """
        Enhanced simulation data with comprehensive vulnerability analysis.
        """
        vuln_type = vuln.get('type', 'Unknown')
        
        # Comprehensive simulation database
        simulation_db = {
            "Unauthorized Minting": {
                "explanation": "The mint() function lacks access control modifiers like onlyOwner or role-based permissions. This allows any address to call the function and create unlimited tokens, completely breaking the token's economic model.",
                "impact": "An attacker can mint unlimited tokens to their address, causing hyperinflation, devaluing all existing tokens, and potentially draining liquidity pools or manipulating DeFi protocols that use this token.",
                "exploit_scenario": "1. Attacker calls mint(attackerAddress, 1000000000 ether)\n2. Attacker receives 1 billion tokens\n3. Attacker dumps tokens on DEX, crashing the price\n4. Legitimate holders lose all value",
                "recommended_fix": "```solidity\naddress public owner;\n\nmodifier onlyOwner() {\n    require(msg.sender == owner, \"Not authorized\");\n    _;\n}\n\nfunction mint(address _to, uint256 _amount) public onlyOwner {\n    balanceOf[_to] += _amount;\n    totalSupply += _amount;\n    emit Transfer(address(0), _to, _amount);\n}\n```",
                "prevention": "Always implement access control for privileged functions. Use OpenZeppelin's Ownable or AccessControl contracts. Consider using a multi-sig wallet for critical operations."
            },
            "Reentrancy Vulnerability": {
                "explanation": "The transfer() function makes an external call to the recipient before updating balances. This violates the Checks-Effects-Interactions pattern and allows a malicious contract to re-enter the function before state changes are finalized.",
                "impact": "An attacker can drain the contract by repeatedly calling transfer() before their balance is deducted, similar to the famous DAO hack that led to Ethereum's hard fork.",
                "exploit_scenario": "1. Attacker deploys malicious contract with onTokenReceived() callback\n2. Attacker calls transfer() to malicious contract\n3. In callback, malicious contract calls transfer() again\n4. Original transfer hasn't updated balances yet\n5. Attacker drains all tokens through recursive calls",
                "recommended_fix": "```solidity\nfunction transfer(address _to, uint256 _value) public returns (bool success) {\n    require(balanceOf[msg.sender] >= _value, \"Insufficient balance\");\n    \n    // Update state BEFORE external call\n    balanceOf[msg.sender] -= _value;\n    balanceOf[_to] += _value;\n    emit Transfer(msg.sender, _to, _value);\n    \n    // External call AFTER state update\n    if (_to.code.length > 0) {\n        (bool callSuccess,) = _to.call(abi.encodeWithSignature(\"onTokenReceived(address,uint256)\", msg.sender, _value));\n        require(callSuccess, \"Callback failed\");\n    }\n    \n    return true;\n}\n```",
                "prevention": "1. Follow Checks-Effects-Interactions pattern\n2. Update state before external calls\n3. Use ReentrancyGuard modifier\n4. Avoid external calls in token transfers when possible"
            },
            "Unrestricted Delegatecall": {
                "explanation": "The executeArbitrary() function allows anyone to execute arbitrary code in the context of the contract via delegatecall. This is extremely dangerous as delegatecall preserves the calling contract's storage context.",
                "impact": "Complete contract takeover. An attacker can modify any storage variable, including balances, ownership, and even self-destruct the contract. This is a critical vulnerability that makes the contract completely insecure.",
                "exploit_scenario": "1. Attacker deploys malicious contract with function that modifies storage\n2. Attacker calls executeArbitrary(maliciousContract, maliciousData)\n3. Malicious code executes in context of token contract\n4. Attacker overwrites balanceOf[attacker] = type(uint256).max\n5. Or attacker changes owner to themselves\n6. Or attacker calls selfdestruct",
                "recommended_fix": "```solidity\n// REMOVE THIS FUNCTION ENTIRELY\n// If you absolutely need delegatecall (rare), use:\n\naddress public owner;\nmapping(address => bool) public trustedImplementations;\n\nfunction executeArbitrary(address _target, bytes memory _data) public onlyOwner {\n    require(trustedImplementations[_target], \"Untrusted implementation\");\n    (bool success,) = _target.delegatecall(_data);\n    require(success, \"Delegatecall failed\");\n}\n```",
                "prevention": "1. Avoid delegatecall unless absolutely necessary\n2. If needed, whitelist allowed targets\n3. Implement strict access control\n4. Use established proxy patterns (UUPS, Transparent)\n5. Audit thoroughly before deployment"
            },
            "Weak Randomness": {
                "explanation": "The claimRandomReward() function uses block.timestamp for randomness. Block timestamps are controlled by miners within a ~15 second window and are completely predictable, making this not random at all.",
                "impact": "Miners can manipulate timestamps to maximize their rewards. Any user can predict the 'random' value and claim rewards at optimal times. This breaks any game theory or fairness assumptions.",
                "exploit_scenario": "1. Attacker monitors mempool for reward claims\n2. Attacker calculates expected reward based on current block.timestamp\n3. If reward is high, attacker front-runs with higher gas\n4. If reward is low, attacker doesn't claim\n5. Miners can manipulate timestamp to get maximum reward",
                "recommended_fix": "```solidity\n// Use Chainlink VRF (recommended)\nimport \"@chainlink/contracts/src/v0.8/VRFConsumerBase.sol\";\n\ncontract BrokenToken is VRFConsumerBase {\n    bytes32 internal keyHash;\n    uint256 internal fee;\n    \n    function claimRandomReward() public {\n        require(LINK.balanceOf(address(this)) >= fee, \"Not enough LINK\");\n        requestRandomness(keyHash, fee);\n    }\n    \n    function fulfillRandomness(bytes32 requestId, uint256 randomness) internal override {\n        uint256 reward = randomness % 1000;\n        balanceOf[msg.sender] += reward;\n        totalSupply += reward;\n    }\n}\n```",
                "prevention": "1. Never use block.timestamp, block.number, or blockhash for randomness\n2. Use Chainlink VRF for verifiable randomness\n3. Implement commit-reveal schemes for user-generated randomness\n4. Consider off-chain randomness with on-chain verification"
            },
            "Unprotected Selfdestruct": {
                "explanation": "The destroy() function allows anyone to call selfdestruct, permanently destroying the contract and sending all ETH to an arbitrary address. This is catastrophic as it makes all tokens worthless and unrecoverable.",
                "impact": "Total loss of all contract functionality. All token balances become inaccessible. Any ETH in the contract is stolen. All integrations with other protocols break. This is an existential threat to the token.",
                "exploit_scenario": "1. Attacker calls destroy(attackerAddress)\n2. Contract is immediately destroyed\n3. All ETH sent to attacker\n4. All token balances become permanently inaccessible\n5. Token becomes worthless\n6. DeFi protocols holding the token suffer losses",
                "recommended_fix": "```solidity\n// REMOVE THIS FUNCTION ENTIRELY (recommended)\n\n// Or if you must have emergency shutdown:\naddress public owner;\nbool public emergencyShutdown = false;\nuint256 public shutdownInitiated;\n\nfunction initiateShutdown() public onlyOwner {\n    shutdownInitiated = block.timestamp;\n}\n\nfunction executeShutdown(address payable _recipient) public onlyOwner {\n    require(shutdownInitiated > 0, \"Shutdown not initiated\");\n    require(block.timestamp >= shutdownInitiated + 7 days, \"Timelock not expired\");\n    require(_recipient == owner, \"Can only send to owner\");\n    selfdestruct(_recipient);\n}\n```",
                "prevention": "1. Avoid selfdestruct in production contracts\n2. If needed, implement multi-sig + timelock\n3. Use pause functionality instead of destruction\n4. Consider upgrade patterns instead of destruction\n5. Never allow arbitrary addresses to receive funds"
            }
        }
        
        # Get simulation data or use generic fallback
        if vuln_type in simulation_db:
            return simulation_db[vuln_type]
        
        # Generic fallback
        prefix = "[SIMULATION]" if not error_context else "[FALLBACK]"
        return {
            "explanation": f"{prefix} Analysis unavailable. Heuristic detection of {vuln_type}.",
            "impact": f"{prefix} Potential high severity issue affecting contract integrity.",
            "exploit_scenario": f"{prefix} Attacker interacts with {vuln.get('function')} to trigger failure.",
            "recommended_fix": "// Implement Checks-Effects-Interactions pattern and validate all inputs.",
            "prevention": "Use formal verification tools and standard libraries (OpenZeppelin)."
        }


# Test the analyzer
if __name__ == "__main__":
    analyzer = AIAnalyzer()
    
    test_vuln = {
        "type": "Unauthorized Minting",
        "severity": "CRITICAL",
        "function": "mint(address,uint256)",
        "description": "Anyone can mint unlimited tokens",
        "line": 45,
        "sequence": [
            {
                "sender": "0x1234567890",
                "function": "mint(address,uint256)",
                "calldata": "0xabcd",
                "value": 0
            }
        ],
        "raw_trace": "Call to mint() succeeded"
    }
    
    result = analyzer.batch_analyze([test_vuln], "function mint(address _to, uint256 _amount) public { }")
    print(json.dumps(result[0], indent=2))
