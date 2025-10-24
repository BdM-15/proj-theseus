"""
Manual test script for user query prompts

Usage:
    python manual_test_prompts.py

Requirements:
    - Server running: python app.py
    - RFP already ingested in default collection
"""

import requests
from pathlib import Path
from src.core.prompt_loader import load_prompt

# Server endpoint
BASE_URL = "http://localhost:9621"

# Test queries for each prompt
TEST_CASES = [
    {
        "name": "Proposal Outline Generation",
        "prompt": "user_queries/proposal_outline_generation",
        "query": "Generate a proposal outline based on this RFP",
        "expected_keywords": ["volume", "page", "section", "evaluation factor"]
    },
    {
        "name": "Compliance Assessment",
        "prompt": "user_queries/compliance_assessment",
        "query": "Assess our compliance with all RFP requirements",
        "expected_keywords": ["score", "compliant", "requirement", "gap"]
    },
    {
        "name": "Questions for Government",
        "prompt": "user_queries/generate_qfg",
        "query": "What questions should we ask during the Q&A period?",
        "expected_keywords": ["question", "?", "section", "ambiguity"]
    },
    {
        "name": "Win Theme Identification",
        "prompt": "user_queries/win_theme_identification",
        "query": "What are our win themes for this opportunity?",
        "expected_keywords": ["theme", "evaluation factor", "advantage", "discriminator"]
    }
]


def test_server_health():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not reachable: {e}")
        print("\nStart server with: python app.py")
        return False


def test_prompt(test_case):
    """Test a single prompt"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_case['name']}")
    print(f"{'='*60}")
    
    # Load prompt
    try:
        prompt_text = load_prompt(test_case["prompt"])
        print(f"✅ Prompt loaded ({len(prompt_text)} chars)")
    except Exception as e:
        print(f"❌ Failed to load prompt: {e}")
        return False
    
    # Execute query
    print(f"\nQuery: {test_case['query']}")
    print("Executing query...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "query": test_case["query"],
                "mode": "hybrid",
                "user_prompt": prompt_text
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        response_text = result.get("response", "")
        
        print(f"\n✅ Query successful ({len(response_text)} chars)")
        
        # Validate response contains expected keywords
        found_keywords = []
        missing_keywords = []
        
        for keyword in test_case["expected_keywords"]:
            if keyword.lower() in response_text.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        print(f"\nKeyword validation:")
        print(f"  ✅ Found: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"  ⚠️  Missing: {', '.join(missing_keywords)}")
        
        # Show preview of response
        print(f"\nResponse preview (first 500 chars):")
        print("-" * 60)
        print(response_text[:500])
        if len(response_text) > 500:
            print("...")
        print("-" * 60)
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Query timed out (>30 seconds)")
        return False
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("User Query Prompts - Manual Test Suite")
    print("Branch 010 Phase 1 Implementation")
    print("="*60)
    
    # Check server
    if not test_server_health():
        return
    
    # Run tests
    results = []
    for test_case in TEST_CASES:
        success = test_prompt(test_case)
        results.append((test_case["name"], success))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 1 implementation validated.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")


if __name__ == "__main__":
    main()
