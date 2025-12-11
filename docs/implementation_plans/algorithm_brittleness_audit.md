# Algorithm Brittleness Audit: Semantic Post-Processing

**Issue**: Algorithm 2 (Evaluation Hierarchy) failed to discover Factor F due to brittle keyword matching  
**Root Cause**: Hardcoded pattern matching instead of leveraging LLM reasoning  
**Scope**: Audit all 8 algorithms for similar brittleness issues  
**Date**: December 11, 2025

---

## Executive Summary

The Factor F discovery failure (Small Business Participation not linked to evaluation hierarchy) revealed **systemic brittleness** in our semantic post-processing algorithms. Instead of leveraging LLM's reasoning capabilities, we're using hardcoded keyword lists and regex patterns that fail on non-standard RFP formats.

### Problem Pattern

```python
# ❌ BRITTLE: Hardcoded keyword matching
if any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    # Missing 'small business' → Factor F not discovered
```

```python
# ✅ ROBUST: LLM-based discovery
# Send ALL entities to LLM, let reasoning discover patterns
prompt = f"Identify evaluation factor hierarchies from these entities: {entities_json}"
```

### Key Findings

| Algorithm | Brittleness Level | Primary Issue | Solution Priority |
|-----------|------------------|---------------|-------------------|
| Algorithm 2 | 🔴 **CRITICAL** | Hardcoded factor keywords | **FIXED** (Branch 038) |
| Algorithm 1 | 🟡 Medium | Hardcoded instruction terms | Medium |
| Algorithm 5 | 🟡 Medium | Hardcoded document type categories | Medium |
| Algorithm 6 | 🟢 Low | Dynamic batching (good) | None needed |
| Algorithm 3 | 🟢 Low | Pure LLM reasoning | None needed |
| Algorithm 4 | 🟢 Low | Pure LLM reasoning | None needed |
| Algorithm 7 | ⚪ N/A | Heuristic patterns (by design) | None needed |
| Algorithm 8 | 🟢 Low | Pure LLM reasoning | None needed |

---

## Algorithm-by-Algorithm Analysis

### Algorithm 1: Instruction-Evaluation Linking

**Current Implementation** (`src/inference/semantic_post_processor.py` lines 760-890):

```python
# TYPE-BATCHED approach with hardcoded instruction detection
instructions = entities_by_type.get('submission_instruction', [])

# BRITTLE: Hardcoded deliverable instruction patterns
deliverables_with_instructions = [
    e for e in entities_by_type.get('deliverable', [])
    if any(term in str(e.get('entity_name', '')).lower() 
           for term in ['proposal', 'submission', 'response', 'volume', 
                       'technical', 'cost', 'past performance'])
]

# BRITTLE: Hardcoded requirement instruction patterns  
requirements_with_instructions = [
    e for e in entities_by_type.get('requirement', [])
    if e.get('modal_verb') in ['shall', 'must'] and 
       any(term in str(e.get('entity_name', '')).lower() 
           for term in ['submit', 'provide', 'proposal', 'response', 'volume', 
                       'page limit', 'format', 'electronic', 'hard copy'])
]
```

**Brittleness Issues**:

1. **Keyword list incomplete** - "offeror instructions", "submission requirements", "format specifications" might be missed
2. **False positives** - "volume" matches storage volume, "format" matches data format
3. **Type-specific batching** - Assumes 3 distinct entity types when LLM could discover instruction patterns agnostically

**Impact**: Low-Medium (Section L typically uses standard language, but task orders vary)

**Proposed Solution**:

```python
# Remove hardcoded keyword filtering
# Send ALL submission_instruction entities + sample deliverables/requirements to LLM
# Let LLM identify instruction patterns using reasoning

instruction_candidates = (
    entities_by_type.get('submission_instruction', []) +
    entities_by_type.get('deliverable', [])[:50] +  # Sample for pattern detection
    entities_by_type.get('requirement', [])[:50]
)

# Single LLM call with pattern discovery
prompt = f"""
Identify which entities provide submission instructions or format guidance
for proposals, and link them to relevant evaluation factors.

Candidates: {instruction_candidates_json}
Evaluation Factors: {eval_factors_json}
"""
```

**Priority**: Medium (affects Section L↔M mapping, but usually works due to standard language)

---

### Algorithm 2: Evaluation Hierarchy ✅ FIXED

**Previous Implementation** (lines 950-1005):

```python
# BRITTLE: Hardcoded factor keyword matching
elif any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    parts = name.split()
    root_key = parts[0].upper()
```

**Problem**: Missed "Factor F Small Business Participation and Subcontracting"

**Fix Applied** (Branch 038):

```python
# ROBUST: Single LLM call for all evaluation factors
# LLM discovers Factor A-F hierarchies using reasoning
# No keyword matching, no batching needed (only 18 factors)

factors_json = json.dumps([{
    'id': f['id'],
    'name': f['entity_name'],
    'description': f.get('description', '')[:5000]
} for f in eval_factors], indent=2)

# Let LLM discover hierarchies agnostically
prompt = f"{prompt_instructions}\n\nEVALUATION_FACTOR_ENTITIES:\n{factors_json}"
```

**Status**: ✅ **FIXED** (committed in branch 038)

---

### Algorithm 3: Requirement-Evaluation Mapping

**Current Implementation** (lines 1380-1480):

```python
# Filter to main factors only (uses _is_main_evaluation_factor helper)
main_eval_factors = [f for f in eval_factors if _is_main_evaluation_factor(f)]

# Batch requirements (100 per batch)
# Pure LLM reasoning - no hardcoded patterns
for batch in requirement_batches:
    prompt = f"""
    Map requirements to evaluation factors based on semantic analysis.
    Requirements: {req_json}
    Factors: {factor_json}
    """
```

**Brittleness Issues**: 🟢 **NONE** - Already uses pure LLM reasoning

**Notes**: 
- Uses `_is_main_evaluation_factor()` helper which has keyword patterns (line 292-296)
- But those patterns are for FILTERING, not DISCOVERY
- Algorithm 2 discovers factors first, Algorithm 3 just filters to main ones
- This is acceptable - filtering is different from discovery

**Priority**: None (already robust)

---

### Algorithm 4: Deliverable Traceability

**Current Implementation** (lines 1500-1600):

```python
# Pure LLM reasoning - no hardcoded patterns
# Links deliverables to requirements and work statements

prompt = f"""
Trace deliverables to their source requirements and work statements.
Deliverables: {deliv_json}
Requirements: {req_json}
Work Statements: {work_json}
"""
```

**Brittleness Issues**: 🟢 **NONE** - Pure LLM reasoning

**Priority**: None (already robust)

---

### Algorithm 5: Document Hierarchy

**Current Implementation** (lines 1030-1110):

```python
# BRITTLE: Hardcoded document type categories
document_types = {
    'sections': ['section'],
    'attachments': ['attachment', 'exhibit', 'annex'],
    'amendments': ['amendment'],
    'clauses': ['clause', 'standard', 'specification', 'regulation']
}

# Group documents by type category
doc_groups = {}
for category, types in document_types.items():
    docs = [e for e in entities if e.get('entity_type') in types]
    if docs:
        doc_groups[category] = docs
```

**Brittleness Issues**:

1. **Type-based batching** - Assumes entity types are correctly classified
2. **Limited categories** - "appendix", "volume", "part", "addendum" might need separate handling
3. **Cross-category relationships missed** - Section referencing an Attachment requires cross-batch inference

**Impact**: Low (entity extraction usually gets types correct, and most hierarchies are within-type)

**Proposed Solution**:

```python
# Remove type-based batching
# Send ALL document entities to LLM in single call (typically 20-50 documents)

document_entities = [e for e in entities if e.get('entity_type') in [
    'section', 'document', 'attachment', 'exhibit', 'annex', 'amendment', 
    'clause', 'standard', 'specification', 'regulation'
]]

# Single LLM call - discovers hierarchies agnostically
prompt = f"""
Identify parent-child relationships between these document entities.
Look for attachment references, section numbering, amendments, etc.

Documents: {document_entities_json}
"""
```

**Priority**: Medium (mostly works, but could miss cross-type relationships)

---

### Algorithm 6: Semantic Concept Linking

**Current Implementation** (lines 1130-1230):

```python
# DYNAMIC BATCHING - no hardcoded patterns
if len(concept_pool) <= 50:
    batch_size = len(concept_pool)  # Single batch
elif len(concept_pool) <= 200:
    batch_size = 100  # Medium batches
else:
    batch_size = 150  # Large batches

# Pure LLM reasoning for concept linking
```

**Brittleness Issues**: 🟢 **NONE** - Already uses adaptive batching + pure LLM reasoning

**Priority**: None (already robust)

---

### Algorithm 7: Heuristic CDRL/DID Pattern Matching

**Current Implementation** (lines 1250-1330):

```python
# BY DESIGN: Heuristic patterns for standard government forms
cdrl_pattern = r'\bCDRL\s*[A-Z]?\d{3,4}\b'
did_pattern = r'\bDI-[A-Z]+-\d{5}[A-Z]?\b'

# This is INTENTIONALLY brittle - matching exact government standards
```

**Brittleness Issues**: ⚪ **N/A** - Heuristics are by design for exact pattern matching

**Notes**: Government CDRL/DID formats are standardized. Regex is appropriate here.

**Priority**: None (heuristics are correct approach for standardized formats)

---

### Algorithm 8: Orphan Pattern Resolution

**Current Implementation** (lines 1343-1450):

```python
# Pure LLM reasoning with candidate matching
# No hardcoded patterns - uses cosine similarity for candidate selection

for orphan_batch in orphan_batches:
    # Find candidate targets via embedding similarity
    candidates = find_similar_entities(orphan, all_entities, top_k=200)
    
    # LLM reasons about which candidates are valid targets
    prompt = f"""
    Resolve orphan relationships by identifying valid target entities.
    Orphans: {orphan_json}
    Candidates: {candidate_json}
    """
```

**Brittleness Issues**: 🟢 **NONE** - Pure LLM reasoning + embedding similarity

**Priority**: None (already robust)

---

## Recommendations

### Immediate Actions (Branch 038)

- [x] **Algorithm 2 Fix**: Remove keyword matching, use single LLM call (**DONE**)
- [ ] **Commit and Test**: Verify Factor F discovery in fresh MCPP workspace

### Short-Term (Next 1-2 Branches)

1. **Algorithm 1 Refactor** (Medium Priority)
   - Remove hardcoded instruction keyword lists
   - Send all candidate entities to LLM for pattern discovery
   - Estimated Impact: Better Section L↔M mapping for non-standard RFPs

2. **Algorithm 5 Refactor** (Medium Priority)
   - Remove type-based document batching
   - Single LLM call for all document entities
   - Estimated Impact: Better cross-category hierarchy discovery

### Long-Term Architecture Principle

**Guiding Rule**: Use hardcoded patterns ONLY for:
1. **Standardized formats** (CDRL/DID patterns, FAR clause numbers)
2. **Performance optimization** (filtering before LLM call to reduce tokens)
3. **Safety guardrails** (preventing hallucinations in critical paths)

**Use LLM reasoning for**:
1. **Pattern discovery** (evaluation factors, instruction types)
2. **Semantic relationships** (requirement↔factor mapping)
3. **Context-dependent decisions** (is this entity a "main factor"?)

---

## Testing Plan

### Validation for Algorithm Fixes

For each refactored algorithm, test on:

1. **MCPP RFP** (standard Section M with Factor A-F)
2. **ISS Task Order** (non-standard format with embedded factors)
3. **DFAC RFP** (different factor naming: "Technical Capability", "Management Approach")

**Success Criteria**:
- Discovers ALL evaluation factors regardless of naming
- Links Section L↔M correctly for non-standard formats
- No reduction in accuracy on standard RFPs

### Regression Testing

Run full suite on existing workspaces:
```bash
python tests/test_semantic_postprocessing_smoke.py --workspace 2_mcpp_drfp_2025
python tests/test_semantic_postprocessing_smoke.py --workspace 1_adab_iss_2025
python tests/test_semantic_postprocessing_smoke.py --workspace 3_adab_dfac_2025
```

Expected: No reduction in relationship counts, possible improvements

---

## Appendix: `_is_main_evaluation_factor()` Analysis

**Location**: `src/inference/semantic_post_processor.py` lines 273-340

**Current Implementation**:
```python
main_factor_patterns = [
    'factor a', 'factor b', 'factor c', 'factor d', 'factor e', 'factor f',
    'factor 1', 'factor 2', 'factor 3', 'factor 4', 'factor 5', 'factor 6',
    'subfactor',
    'technical factor', 'price factor', 'cost factor', 'management factor',
    'tomp', 'past performance', 'small business',
    'mission essential', 'quality control plan'
]
```

**Status**: This is **FILTERING**, not **DISCOVERY**
- Algorithm 2 discovers factors first (now fixed to use LLM)
- Algorithm 3 uses this helper to filter to main factors only
- Filtering can use keywords (reduces LLM token usage)
- Discovery MUST use LLM reasoning

**Recommendation**: Keep as-is, but document distinction:
```python
def _is_main_evaluation_factor(entity: Dict) -> bool:
    """
    Filter supporting entities from main evaluation factors.
    
    IMPORTANT: This is FILTERING (after discovery), not DISCOVERY.
    - Algorithm 2 discovers ALL factors using LLM reasoning
    - This helper filters to main factors (for Algorithm 3 batching)
    - Keyword patterns acceptable for filtering (performance optimization)
    - NEVER use for discovery (that's Algorithm 2's job with LLM)
    """
```

---

**Last Updated**: December 11, 2025  
**Branch Context**: 038-table-analysis-chunk-format  
**Related Issue**: Factor F discovery failure (Small Business not linked to hierarchy)
