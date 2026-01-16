#!/usr/bin/env python3
"""
Quick test script to verify Gemini AI integration
"""

import os
import sys

# Set your API key
os.environ["GEMINI_API_KEY"] = "AIzaSyDkSYwAHhwCzG0vNUmgQ9joJ4pQ6unz5tI"

from ai_analyzer import AIAnalyzer

def main():
    print("🔮 Testing Gemini AI Integration...")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = AIAnalyzer()
    
    # Test vulnerability
    test_vuln = {
        "type": "Unauthorized Minting",
        "severity": "CRITICAL",
        "function": "mint(address,uint256)",
        "description": "Anyone can mint unlimited tokens due to missing access control",
        "line": 45
    }
    
    # Simple contract code
    contract_code = """
    pragma solidity ^0.8.0;
    
    contract BrokenToken {
        mapping(address => uint256) public balanceOf;
        uint256 public totalSupply;
        
        function mint(address _to, uint256 _amount) public {
            // VULNERABLE: No access control!
            balanceOf[_to] += _amount;
            totalSupply += _amount;
        }
    }
    """
    
    print("\n📊 Analyzing vulnerability...")
    results = analyzer.batch_analyze([test_vuln], contract_code)
    
    if results:
        vuln = results[0]
        ai = vuln.get("ai_analysis", {})
        
        print("\n✅ Analysis Complete!")
        print("=" * 60)
        print(f"\n📋 Explanation:\n{ai.get('explanation', 'N/A')}")
        print(f"\n💥 Impact:\n{ai.get('impact', 'N/A')}")
        print(f"\n🎯 Exploit Scenario:\n{ai.get('exploit_scenario', 'N/A')}")
        print(f"\n🔧 Recommended Fix:\n{ai.get('recommended_fix', 'N/A')}")
        print(f"\n🛡️  Prevention:\n{ai.get('prevention', 'N/A')}")
        print("\n" + "=" * 60)
        
        if analyzer.simulation_mode:
            print("\n⚠️  Running in SIMULATION mode (no API key or library)")
        else:
            print("\n✔️  Running with LIVE Gemini AI")
    else:
        print("\n❌ No results returned")

if __name__ == "__main__":
    main()
