# Branch 013a: ID-Based Relationship Inference

**Branch**: `013a-id-based-relationships`  
**Parent**: `013-neo4j-implementation-main`  
**Date**: November 10, 2025  
**Status**: ACTIVE

## Problem Solved

**Entity Name Mismatch Causing 36% Relationship Loss**

In branch 013, relationship inference achieved 5.4x improvement (75 relationships found vs 14-21 baseline), but **36% were rejected** (75 found → 48 created) due to entity name mismatches:

```
LLM returns:  "Subfactor 1.1: Task Order Management Plan (TOMP) (evaluation_factor)"
Neo4j has:    "Task Order Management Plan (TOMP)"
Result:       NO MATCH → Relationship rejected
```

**Root Cause:**
- LLM was given entity names in prompt
- LLM returned names with prefixes/suffixes/type annotations
- Name lookup failed: `name_to_id.get("Subfactor 1.1: TOMP...")` → None
- 27/75 relationships lost

## Solution: ID-Based Entity References

**Pass entity IDs to LLM instead of names** → Eliminates all ambiguity.

### Before (Name-Based):
```python
# Prompt shows entity names
entity_summary = "\n".join([
    f"- {e['entity_name']} ({e['entity_type']}): {e.get('description', '')[:100]}"
    for e in batch_entities
])

# LLM returns names (with embellishments)
{"source": "Subfactor 1.1: Task Order...", "target": "TOMP", ...}

# Lookup fails
source_id = name_to_id.get(rel.get('source'))  # Returns None
```

### After (ID-Based):
```python
# Prompt shows entity reference table with IDs
entity_table = "ID | Type | Name | Description\n" + ("-" * 80) + "\n"
entity_table += "\n".join([
    f"{e['id']} | {e['entity_type']} | {e['entity_name']} | {e.get('description', '')[:80]}"
    for e in batch_entities
])

# LLM returns IDs (exact match)
{"source_id": "4:abc123...", "target_id": "4:def456...", ...}

# Lookup always succeeds (if ID valid)
if source_id in id_to_entity and target_id in id_to_entity:
    all_relationships.append({...})
```

## Key Changes

### 1. Prompt Engineering (semantic_post_processor.py)

**ENTITY REFERENCE TABLE FORMAT:**
```
ID                          | Type              | Name                | Description
--------------------------------------------------------------------------------
4:abc123-def456-789...     | requirement       | TOMP Submission     | Contractor shall...
4:ghi789-jkl012-345...     | evaluation_factor | Technical Approach  | Factor 1...
4:mno456-pqr678-901...     | deliverable       | Monthly Report      | Submit by 5th...
```

**Prompt Instructions:**
```
**CRITICAL**: Use entity IDs from the table above, NOT entity names. IDs eliminate ambiguity.

Format your response as JSON array:
[
  {"source_id": "4:abc123...", "target_id": "4:def456...", "type": "EVALUATES", ...}
]
```

### 2. Validation Logic

**Before:**
```python
name_to_id = {e['entity_name']: e['id'] for e in entities}  # Ambiguous lookup
source_id = name_to_id.get(rel.get('source'))  # Fails on mismatch
```

**After:**
```python
id_to_entity = {e['id']: e for e in entities}  # Direct ID lookup
source_id = rel.get('source_id')
if source_id in id_to_entity:  # Always succeeds if ID valid
    all_relationships.append({...})
```

## Expected Results

### Relationship Inference Quality
- **Before (013)**: 75 found → 48 created (36% loss)
- **After (013a)**: 75 found → ~70-75 created (0-7% loss)
  - Only losses: LLM hallucinating invalid IDs (rare with table lookup)
  - 100% match rate for valid relationships

### Validation Score Impact
- **Before (013)**: 36.7% overall (17.6% Section L↔M coverage)
- **After (013a)**: **~75-85% overall** (70-85% Section L↔M coverage)
  - Still missing workload enrichment (0% → adds ~25 points in 013b)
  - But relationship traceability jumps to 70-85%

## Implementation Traps

### Trap 1: LLM Returns Names Despite Instructions
**Symptom**: LLM ignores ID instructions, returns `{"source": "TOMP", ...}` instead of `{"source_id": "4:abc123...", ...}`

**Mitigation**:
- Bold/capitalized instructions in prompt: **CRITICAL: Use entity IDs**
- Validate JSON keys: Accept both `source_id` and `source` (fallback to name lookup)
- Log warnings when LLM disobeys format

### Trap 2: ID Format Varies (Neo4j elementId)
**Symptom**: IDs like `"4:abc123-def456-789..."` are verbose, LLM might truncate

**Mitigation**:
- Use full elementId from Neo4j (no custom short IDs to avoid mapping errors)
- Trust Grok-4's 2M context can handle full IDs (only ~50 chars each)
- If issues: Consider adding short reference IDs (e.g., `[R1]`, `[EF2]`) in future

### Trap 3: Cross-Batch Relationships Still Limited
**Symptom**: Batch 1 entities can't link to Batch 3 entities (not in context)

**Mitigation**:
- Current: 100-entity overlap catches most cross-batch relationships
- Future: Global index pass (after batches) to find cross-workspace relationships
- Acceptable: Most relationships are local (same appendix, same section)

## Testing Plan

### Test 1: Reprocess ISS RFP (afcapv_adab_iss_2025)
```powershell
# Clear Neo4j workspace
python tools/clear_neo4j.py afcapv_adab_iss_2025

# Restart app (uses new ID-based inference)
python app.py

# Upload: inputs/uploaded/ADAB_ISS_RFP_Amendment_1.pdf (mode=auto)
# Wait for processing...

# Validate results
python tools/validate_rfp_processing.py afcapv_adab_iss_2025
```

**Expected Metrics:**
- Total entities: ~1,400-1,600 (consistent with Runs 2-5)
- Requirements: ~120-173 (Grok-4 consistency)
- Relationships inferred: **70-75** (vs 48 in Run 5)
- **Section L↔M coverage: 70-85%** (vs 17.6% in Run 5)
- Overall validation score: **75-85%** (vs 36.7% in Run 5)

### Test 2: Log Analysis
```powershell
# Check relationship inference logs
grep "Found.*relationships in batch" logs/server.log

# Expected: Same 75 found (good inference)
# Check created relationships
grep "Relationships inferred:" logs/server.log

# Expected: ~70-75 created (minimal loss vs 48 before)
```

### Test 3: Neo4j Verification
```cypher
// Check Section L↔M relationships
MATCH (r:afcapv_adab_iss_2025 {entity_type: 'requirement'})-[rel]-(e:afcapv_adab_iss_2025 {entity_type: 'evaluation_factor'})
RETURN count(DISTINCT r) AS requirements_linked, count(DISTINCT e) AS eval_factors_linked

// Expected: 120+ requirements linked (vs 15 in Run 5)
//           40+ eval factors linked (vs 13 in Run 5)
```

## Success Criteria

### Minimum (PASS):
- ✅ Relationship match rate ≥ 90% (70/75 or better)
- ✅ Section L↔M coverage ≥ 70%
- ✅ Overall validation score ≥ 70%

### Target (PRODUCTION READY with 013b):
- 🎯 Relationship match rate ≥ 95% (71/75 or better)
- 🎯 Section L↔M coverage ≥ 80%
- 🎯 Overall validation score ≥ 75% (013a alone, 85%+ with 013b workload enrichment)

### Stretch (OPTIMAL):
- ⭐ Relationship match rate = 100% (75/75)
- ⭐ Section L↔M coverage ≥ 85%
- ⭐ Overall validation score ≥ 80% (013a alone)

## Next Steps: Branch 013b

**Branch 013b: Workload Enrichment + Additional Semantic Fixes**

After proving ID-based relationships work, branch 013b will add:

1. **Workload Metadata Enrichment** (from removed code)
   - 7 BOE categories: Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance
   - Add properties to REQUIREMENT entities: `has_workload_metric`, `workload_categories`, `labor_drivers`, etc.
   - Target: 100% requirement enrichment (adds ~25 points to validation score)

2. **Additional Relationship Types** (if needed)
   - `SUPPORTS`: Technology → Capability
   - `CONSTRAINS`: Regulation → Deliverable
   - `INHERITS`: Sub-requirement → Parent requirement

3. **Confidence Threshold Tuning**
   - Current: Accept all relationships (confidence ≥ 0.0)
   - 013b: Only accept high-confidence (≥ 0.7) to reduce noise

**Combined Target (013a + 013b):**
- Overall validation score: **≥ 85% (PRODUCTION READY)**
- Section L↔M: 80-85%
- Workload enrichment: 100%
- Deliverable traceability: 80-90%
- Query quality: 100% (already achieved)

## Files Changed

### Modified:
- `src/inference/semantic_post_processor.py`:
  - `_infer_relationships_batch()`: ID-based entity references
  - Prompt engineering: Entity reference table format
  - Validation: `id_to_entity` lookup instead of `name_to_id`

### Created:
- `docs/BRANCH_013A_ID_BASED_RELATIONSHIPS.md`: This document

### Testing Scripts (Optional):
- `tests/test_id_based_inference.py`: Unit test for ID validation logic
- `tools/compare_013_vs_013a.py`: A/B comparison of relationship match rates

## References

**Parent Branch:**
- `013-neo4j-implementation-main`: Relationship batching fix (50 → 500 entities)
- Commit: `31ae860` - "Fix relationship inference batching + validation framework"

**Problem Analysis:**
- `docs/BASELINE_ISS_RFP_20251109.md`: Multi-run analysis, Run 5 name mismatch discovery
- Logs: `logs/server.log` (2025-11-10 14:48:33 - 14:49:08) - 75 found, 48 created

**Related Issues:**
- Issue: Entity name format inconsistency (LLM adds prefixes)
- Solution: Bypass names entirely, use IDs as ground truth
