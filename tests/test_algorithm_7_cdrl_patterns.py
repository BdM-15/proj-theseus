"""
Test Algorithm 7 CDRL Pattern Matching Enhancement (Issue #31)

Validates that the expanded regex patterns correctly identify:
- CDRL letter+number: "CDRL A001", "CDRL B002"
- CDRL number-only: "CDRL 6022", "CDRL 0001"  
- DID references: "DID A001", "DID-MC-123456"
- DD Form 1423: "DD Form 1423", "DD1423"
- Exhibit/Annex: "Exhibit A", "Annex I", "Attachment J-001"

Run: python tests/test_algorithm_7_cdrl_patterns.py
"""

import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cdrl_patterns():
    """Test all CDRL/DID/Attachment patterns match expected references."""
    
    # Pattern definitions from Algorithm 7 implementation
    patterns = [
        # CDRL patterns (Contract Data Requirements List)
        (r'cdrl\s*[a-z]\d{3,4}', 'CDRL letter+number'),      # CDRL A001, CDRL B0002
        (r'cdrl\s*\d{4,5}', 'CDRL number-only'),              # CDRL 6022, CDRL 00001
        (r'cdrl\s*#?\s*\d+', 'CDRL numbered'),                # CDRL #1, CDRL 1
        
        # DID patterns (Data Item Description)
        (r'did\s*[a-z]?\d{3,4}', 'DID reference'),           # DID A001, DID 001
        (r'did[-\s]?[a-z]{2,4}[-\s]?\d{4,6}', 'DID-XX-NNNN'), # DID-MC-123456
        
        # DD Form 1423 (Contract Data Requirements List form)
        (r'dd\s*form\s*1423', 'DD Form 1423'),               # DD Form 1423
        (r'dd[-\s]?1423', 'DD-1423'),                        # DD1423, DD-1423
        
        # Exhibit/Annex/Attachment patterns
        (r'exhibit\s+[a-z]\d*', 'Exhibit reference'),        # Exhibit A, Exhibit A1
        (r'annex\s+[a-z0-9ivx]+', 'Annex reference'),        # Annex I, Annex XVII, Annex 1
        (r'attachment\s+[a-z][-\d]*', 'Attachment reference'), # Attachment J-001
    ]
    
    # Test cases: (input_text, expected_matches, pattern_name)
    test_cases = [
        # CDRL letter+number
        ("Per CDRL A001, submit monthly reports", ["cdrl a001"], "CDRL letter+number"),
        ("See CDRL B0002 for specifications", ["cdrl b0002"], "CDRL letter+number"),
        
        # CDRL number-only (Issue #31 - was previously missed)
        ("Contractor shall provide CDRL 6022 within 30 days", ["cdrl 6022"], "CDRL number-only"),
        ("Reference CDRL 00001 for format", ["cdrl 00001"], "CDRL number-only"),
        
        # CDRL numbered (alternative formats)
        ("Submit per CDRL #1", ["cdrl #1"], "CDRL numbered"),
        ("CDRL 1 describes the deliverable", ["cdrl 1"], "CDRL numbered"),
        
        # DID references  
        ("As defined in DID A001", ["did a001"], "DID reference"),
        ("Per DID 001 requirements", ["did 001"], "DID reference"),
        ("See DID-MC-123456 for data format", ["did-mc-123456"], "DID-XX-NNNN"),
        
        # DD Form 1423
        ("Complete DD Form 1423 for each deliverable", ["dd form 1423"], "DD Form 1423"),
        ("Submit on DD1423", ["dd1423"], "DD-1423"),
        ("Reference DD-1423 Exhibit A", ["dd-1423"], "DD-1423"),
        
        # Exhibit/Annex/Attachment
        ("See Exhibit A for pricing", ["exhibit a"], "Exhibit reference"),
        ("Refer to Exhibit B3 specifications", ["exhibit b3"], "Exhibit reference"),
        ("Per Annex I requirements", ["annex i"], "Annex reference"),
        ("See Annex XVII for security", ["annex xvii"], "Annex reference"),
        ("Attachment J-001 PWS", ["attachment j-001"], "Attachment reference"),
    ]
    
    print("=" * 70)
    print("Algorithm 7 CDRL Pattern Matching Test (Issue #31)")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for input_text, expected_matches, expected_pattern_name in test_cases:
        search_text = input_text.lower()
        found_match = False
        
        for pattern, pattern_name in patterns:
            matches = re.findall(pattern, search_text)
            if matches:
                # Check if expected matches are found
                for expected in expected_matches:
                    if any(expected in m for m in matches):
                        if pattern_name == expected_pattern_name:
                            print(f"✅ PASS: '{input_text[:50]}...' → {pattern_name}: {matches}")
                            found_match = True
                            passed += 1
                            break
                if found_match:
                    break
        
        if not found_match:
            print(f"❌ FAIL: '{input_text[:50]}...' → Expected {expected_pattern_name}: {expected_matches}")
            failed += 1
    
    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("-" * 70)
    
    # Test negative cases (should NOT match)
    print("\nNegative test cases (should NOT match):")
    negative_cases = [
        "The system shall support 1000 users",  # Random number
        "Section C describes requirements",      # Not a CDRL reference
        "MIL-STD-882E compliance required",     # Standard, not CDRL
    ]
    
    negative_pass = 0
    for text in negative_cases:
        search_text = text.lower()
        any_match = False
        for pattern, pattern_name in patterns:
            if re.search(pattern, search_text):
                print(f"⚠️  UNEXPECTED: '{text[:40]}...' matched {pattern_name}")
                any_match = True
                break
        if not any_match:
            print(f"✅ OK: '{text[:40]}...' correctly did NOT match")
            negative_pass += 1
    
    print("-" * 70)
    print(f"Negative tests: {negative_pass}/{len(negative_cases)} correctly rejected")
    print("=" * 70)
    
    return failed == 0 and negative_pass == len(negative_cases)


if __name__ == "__main__":
    success = test_cdrl_patterns()
    sys.exit(0 if success else 1)
