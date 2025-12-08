"""
Unit Tests for Algorithm 7 CDRL Pattern Matching (Issue #30 Phase 1)
=====================================================================

Validates the expanded regex patterns for CDRL/DID/DD Form/Exhibit/Annex references.

Tests:
1. CDRL letter+number format (CDRL A001, CDRL B123)
2. CDRL number-only format (CDRL 6022, CDRL 1234)
3. DID references (DID 6022, DID A001)
4. DD Form 1423 references
5. Exhibit/Annex references (Exhibit A1, Annex B)
6. Case insensitivity
7. Multiple patterns in single entity
8. No false positives (non-matching patterns)

Usage:
    python tests/test_algorithm_7_cdrl_patterns.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.semantic_post_processor import _algorithm_7_heuristic

print("\n" + "="*80)
print("ALGORITHM 7 CDRL PATTERN MATCHING TESTS")
print("="*80)

# ==================================================================================
# TEST 1: CDRL Letter+Number Format
# ==================================================================================

print("\n[TEST 1] CDRL letter+number format...")

entities_test1 = [
    {
        'id': 'entity_1',
        'entity_name': 'Test Req 1',
        'description': 'Submit monthly report per CDRL A001',
        'entity_type': 'requirement'
    },
    {
        'id': 'entity_2',
        'entity_name': 'Test Req 2',
        'description': 'See CDRL B123 for deliverable specs',
        'entity_type': 'requirement'
    }
]

deliverables_test1 = [
    {
        'id': 'deliv_1',
        'entity_name': 'CDRL A001 - Monthly Status Report',
        'description': 'Monthly status report',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_2',
        'entity_name': 'CDRL B123',
        'description': 'Deliverable specification B123',
        'entity_type': 'deliverable'
    }
]

entities_by_type_1 = {'deliverable': deliverables_test1}
results_1 = _algorithm_7_heuristic(entities_test1, entities_by_type_1)

if len(results_1) == 2:
    print(f"✅ Found {len(results_1)} CDRL letter+number relationships")
else:
    print(f"❌ Expected 2 relationships, got {len(results_1)}")
    sys.exit(1)

# ==================================================================================
# TEST 2: CDRL Number-Only Format
# ==================================================================================

print("\n[TEST 2] CDRL number-only format...")

entities_test2 = [
    {
        'id': 'entity_3',
        'entity_name': 'Reporting requirement',
        'description': 'Submit data per CDRL 6022 quarterly',
        'entity_type': 'requirement'
    },
    {
        'id': 'entity_4',
        'entity_name': 'Documentation req',
        'description': 'Reference CDRL 1234 for format',
        'entity_type': 'requirement'
    }
]

deliverables_test2 = [
    {
        'id': 'deliv_3',
        'entity_name': 'CDRL 6022 - Quarterly Data Report',
        'description': 'Data item 6022',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_4',
        'entity_name': 'CDRL1234',  # No space
        'description': 'Documentation format',
        'entity_type': 'deliverable'
    }
]

entities_by_type_2 = {'deliverable': deliverables_test2}
results_2 = _algorithm_7_heuristic(entities_test2, entities_by_type_2)

if len(results_2) == 2:
    print(f"✅ Found {len(results_2)} CDRL number-only relationships")
else:
    print(f"❌ Expected 2 relationships, got {len(results_2)}")
    sys.exit(1)

# ==================================================================================
# TEST 3: DID References
# ==================================================================================

print("\n[TEST 3] DID references...")

entities_test3 = [
    {
        'id': 'entity_5',
        'entity_name': 'Technical data req',
        'description': 'Submit per DID 6022 specifications',
        'entity_type': 'requirement'
    },
    {
        'id': 'entity_6',
        'entity_name': 'Data item req',
        'description': 'Follow DID A001 format',
        'entity_type': 'requirement'
    }
]

deliverables_test3 = [
    {
        'id': 'deliv_5',
        'entity_name': 'DID 6022 - Technical Data Package',
        'description': 'DID reference 6022',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_6',
        'entity_name': 'DID A001',
        'description': 'Data item description A001',
        'entity_type': 'deliverable'
    }
]

entities_by_type_3 = {'deliverable': deliverables_test3}
results_3 = _algorithm_7_heuristic(entities_test3, entities_by_type_3)

if len(results_3) == 2:
    print(f"✅ Found {len(results_3)} DID reference relationships")
else:
    print(f"❌ Expected 2 relationships, got {len(results_3)}")
    sys.exit(1)

# ==================================================================================
# TEST 4: DD Form 1423 References
# ==================================================================================

print("\n[TEST 4] DD Form 1423 references...")

entities_test4 = [
    {
        'id': 'entity_7',
        'entity_name': 'Form requirement',
        'description': 'Use DD Form 1423 for all CDRLs',
        'entity_type': 'requirement'
    }
]

deliverables_test4 = [
    {
        'id': 'deliv_7',
        'entity_name': 'DD Form 1423 - CDRL Template',
        'description': 'Standard form for contract deliverables',
        'entity_type': 'deliverable'
    }
]

entities_by_type_4 = {'deliverable': deliverables_test4}
results_4 = _algorithm_7_heuristic(entities_test4, entities_by_type_4)

if len(results_4) == 1:
    print(f"✅ Found {len(results_4)} DD Form 1423 relationship")
else:
    print(f"❌ Expected 1 relationship, got {len(results_4)}")
    sys.exit(1)

# ==================================================================================
# TEST 5: Exhibit/Annex References
# ==================================================================================

print("\n[TEST 5] Exhibit/Annex references...")

entities_test5 = [
    {
        'id': 'entity_8',
        'entity_name': 'Attachment reference',
        'description': 'See Exhibit A1 for technical details',
        'entity_type': 'requirement'
    },
    {
        'id': 'entity_9',
        'entity_name': 'Annex reference',
        'description': 'Refer to Annex B for specifications',
        'entity_type': 'requirement'
    }
]

deliverables_test5 = [
    {
        'id': 'deliv_8',
        'entity_name': 'Exhibit A1 - Technical Specifications',
        'description': 'Technical details attachment',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_9',
        'entity_name': 'Annex B',
        'description': 'Specifications annex',
        'entity_type': 'deliverable'
    }
]

entities_by_type_5 = {'deliverable': deliverables_test5}
results_5 = _algorithm_7_heuristic(entities_test5, entities_by_type_5)

if len(results_5) == 2:
    print(f"✅ Found {len(results_5)} Exhibit/Annex relationships")
else:
    print(f"❌ Expected 2 relationships, got {len(results_5)}")
    sys.exit(1)

# ==================================================================================
# TEST 6: Case Insensitivity
# ==================================================================================

print("\n[TEST 6] Case insensitivity...")

entities_test6 = [
    {
        'id': 'entity_10',
        'entity_name': 'Mixed case test',
        'description': 'Submit per CdRl A001 format',
        'entity_type': 'requirement'
    }
]

deliverables_test6 = [
    {
        'id': 'deliv_10',
        'entity_name': 'cdrl a001',  # Lowercase
        'description': 'lowercase deliverable',
        'entity_type': 'deliverable'
    }
]

entities_by_type_6 = {'deliverable': deliverables_test6}
results_6 = _algorithm_7_heuristic(entities_test6, entities_by_type_6)

if len(results_6) == 1:
    print(f"✅ Case insensitive matching works")
else:
    print(f"❌ Case insensitive matching failed: expected 1, got {len(results_6)}")
    sys.exit(1)

# ==================================================================================
# TEST 7: Multiple Patterns in Single Entity
# ==================================================================================

print("\n[TEST 7] Multiple patterns in single entity...")

entities_test7 = [
    {
        'id': 'entity_11',
        'entity_name': 'Multi-reference requirement',
        'description': 'Submit CDRL A001, CDRL 6022, and DID 1234 per Exhibit A',
        'entity_type': 'requirement'
    }
]

deliverables_test7 = [
    {
        'id': 'deliv_11',
        'entity_name': 'CDRL A001',
        'description': 'First deliverable',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_12',
        'entity_name': 'CDRL 6022',
        'description': 'Second deliverable',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_13',
        'entity_name': 'DID 1234',
        'description': 'Third deliverable',
        'entity_type': 'deliverable'
    },
    {
        'id': 'deliv_14',
        'entity_name': 'Exhibit A',
        'description': 'Fourth deliverable',
        'entity_type': 'deliverable'
    }
]

entities_by_type_7 = {'deliverable': deliverables_test7}
results_7 = _algorithm_7_heuristic(entities_test7, entities_by_type_7)

if len(results_7) >= 3:  # Should match at least 3 different patterns
    print(f"✅ Multiple pattern matching works: {len(results_7)} relationships")
else:
    print(f"❌ Multiple pattern matching failed: expected >= 3, got {len(results_7)}")
    sys.exit(1)

# ==================================================================================
# TEST 8: No False Positives
# ==================================================================================

print("\n[TEST 8] No false positives...")

entities_test8 = [
    {
        'id': 'entity_12',
        'entity_name': 'Non-matching requirement',
        'description': 'This has no CDRL or DID references at all',
        'entity_type': 'requirement'
    }
]

deliverables_test8 = [
    {
        'id': 'deliv_15',
        'entity_name': 'Random Deliverable',
        'description': 'No matching pattern',
        'entity_type': 'deliverable'
    }
]

entities_by_type_8 = {'deliverable': deliverables_test8}
results_8 = _algorithm_7_heuristic(entities_test8, entities_by_type_8)

if len(results_8) == 0:
    print(f"✅ No false positives detected")
else:
    print(f"❌ False positives detected: expected 0, got {len(results_8)}")
    print(f"   Results: {results_8}")
    sys.exit(1)

# ==================================================================================
# SUMMARY
# ==================================================================================

total_tests = 8
print("\n" + "="*80)
print("ALGORITHM 7 TEST RESULTS")
print("="*80)
print(f"✅ All {total_tests} pattern matching tests PASSED")
print(f"   - CDRL letter+number: ✅")
print(f"   - CDRL number-only: ✅")
print(f"   - DID references: ✅")
print(f"   - DD Form 1423: ✅")
print(f"   - Exhibit/Annex: ✅")
print(f"   - Case insensitivity: ✅")
print(f"   - Multiple patterns: ✅")
print(f"   - No false positives: ✅")
print("\n🎉 Algorithm 7 CDRL pattern matching is working correctly!")
print("="*80)
