"""
Performance Test for Algorithm 7 CDRL Pattern Matching
=======================================================

Validates that Algorithm 7 maintains < 1s runtime as specified in acceptance criteria.
Tests with varying entity counts to ensure scalability.

Usage:
    python tests/test_algorithm_7_performance.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.semantic_post_processor import _algorithm_7_heuristic

print("\n" + "="*80)
print("ALGORITHM 7 PERFORMANCE TEST")
print("="*80)

# ==================================================================================
# TEST 1: Small Dataset (100 entities)
# ==================================================================================

print("\n[TEST 1] Small dataset (100 entities, 10 deliverables)...")

entities_small = []
for i in range(100):
    entities_small.append({
        'id': f'entity_{i}',
        'entity_name': f'Requirement {i}',
        'description': f'Submit per CDRL A{i:03d} or DID {i:04d} specifications',
        'entity_type': 'requirement'
    })

deliverables_small = []
for i in range(10):
    deliverables_small.append({
        'id': f'deliv_{i}',
        'entity_name': f'CDRL A{i:03d}',
        'description': f'Deliverable {i}',
        'entity_type': 'deliverable'
    })

entities_by_type_small = {'deliverable': deliverables_small}

start = time.time()
results_small = _algorithm_7_heuristic(entities_small, entities_by_type_small)
elapsed_small = time.time() - start

print(f"   Entities: {len(entities_small)}")
print(f"   Deliverables: {len(deliverables_small)}")
print(f"   Relationships found: {len(results_small)}")
print(f"   Runtime: {elapsed_small:.4f}s")

if elapsed_small < 0.1:
    print(f"   ✅ Performance: Excellent (< 0.1s)")
elif elapsed_small < 1.0:
    print(f"   ✅ Performance: Good (< 1s)")
else:
    print(f"   ❌ Performance: Slow (> 1s)")
    sys.exit(1)

# ==================================================================================
# TEST 2: Medium Dataset (1,000 entities)
# ==================================================================================

print("\n[TEST 2] Medium dataset (1,000 entities, 50 deliverables)...")

entities_medium = []
for i in range(1000):
    entities_medium.append({
        'id': f'entity_{i}',
        'entity_name': f'Requirement {i}',
        'description': f'Submit per CDRL {i:04d} and DID {i:05d}',
        'entity_type': 'requirement'
    })

deliverables_medium = []
for i in range(50):
    deliverables_medium.append({
        'id': f'deliv_{i}',
        'entity_name': f'CDRL {i:04d}',
        'description': f'Data item {i}',
        'entity_type': 'deliverable'
    })

entities_by_type_medium = {'deliverable': deliverables_medium}

start = time.time()
results_medium = _algorithm_7_heuristic(entities_medium, entities_by_type_medium)
elapsed_medium = time.time() - start

print(f"   Entities: {len(entities_medium)}")
print(f"   Deliverables: {len(deliverables_medium)}")
print(f"   Relationships found: {len(results_medium)}")
print(f"   Runtime: {elapsed_medium:.4f}s")

if elapsed_medium < 0.1:
    print(f"   ✅ Performance: Excellent (< 0.1s)")
elif elapsed_medium < 1.0:
    print(f"   ✅ Performance: Good (< 1s)")
else:
    print(f"   ❌ Performance: Slow (> 1s)")
    sys.exit(1)

# ==================================================================================
# TEST 3: Large Dataset (3,868 entities - MCPP II RFP size)
# ==================================================================================

print("\n[TEST 3] Large dataset (3,868 entities, 150 deliverables - MCPP II RFP)...")

entities_large = []
for i in range(3868):
    # Vary the patterns to simulate realistic data
    if i % 3 == 0:
        desc = f'Submit per CDRL A{i%1000:03d}'
    elif i % 3 == 1:
        desc = f'Reference DID {i:05d} for specifications'
    else:
        desc = f'See Exhibit {chr(65 + (i % 26))}{i % 10} for details'
    
    entities_large.append({
        'id': f'entity_{i}',
        'entity_name': f'Requirement {i}',
        'description': desc,
        'entity_type': 'requirement'
    })

deliverables_large = []
for i in range(150):
    deliverables_large.append({
        'id': f'deliv_{i}',
        'entity_name': f'CDRL A{i:03d}' if i < 100 else f'CDRL {i:04d}',
        'description': f'Deliverable specification {i}',
        'entity_type': 'deliverable'
    })

entities_by_type_large = {'deliverable': deliverables_large}

start = time.time()
results_large = _algorithm_7_heuristic(entities_large, entities_by_type_large)
elapsed_large = time.time() - start

print(f"   Entities: {len(entities_large)}")
print(f"   Deliverables: {len(deliverables_large)}")
print(f"   Relationships found: {len(results_large)}")
print(f"   Runtime: {elapsed_large:.4f}s")

if elapsed_large < 0.1:
    print(f"   ✅ Performance: Excellent (< 0.1s)")
elif elapsed_large < 1.0:
    print(f"   ✅ Performance: Good (< 1s)")
else:
    print(f"   ❌ Performance: Slow (> 1s - FAILED REQUIREMENT)")
    sys.exit(1)

# ==================================================================================
# SUMMARY
# ==================================================================================

print("\n" + "="*80)
print("PERFORMANCE TEST RESULTS")
print("="*80)
print(f"✅ Small dataset (100 entities):     {elapsed_small:.4f}s")
print(f"✅ Medium dataset (1,000 entities):  {elapsed_medium:.4f}s")
print(f"✅ Large dataset (3,868 entities):   {elapsed_large:.4f}s")
print(f"\n🎉 Algorithm 7 meets performance requirement (< 1s for all datasets)")
print(f"   Average throughput: {len(entities_large) / elapsed_large:.0f} entities/second")
print("="*80)
