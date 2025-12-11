# Algorithm Brittleness Audit: Semantic Post-Processing

**Issue**: Algorithm 2 (Evaluation Hierarchy) failed to discover Factor F due to brittle keyword matching  
**Root Cause**: Hardcoded pattern matching instead of leveraging LLM reasoning  
**Scope**: Audit all 8 algorithms for similar brittleness issues  
**Date**: December 11, 2025  
**Updated**: December 11, 2025 - Issue #43 Schema-Driven Refactoring Complete

---

## Executive Summary

The Factor F discovery failure (Small Business Participation not linked to evaluation hierarchy) revealed **systemic brittleness** in our semantic post-processing algorithms. Instead of leveraging LLM's reasoning capabilities, we're using hardcoded keyword lists and regex patterns that fail on non-standard RFP formats.

### Solution: Schema-Driven LLM Prompts (Issue #43)

**IMPLEMENTED**: Algorithms 1, 2, and 5 now use Pydantic schema metadata to guide LLM reasoning:

```python
# ✅ SCHEMA-DRIVEN: Extract field descriptions from Pydantic models
from src.inference.schema_prompts import get_schema_guidance
from src.ontology.schema import EvaluationFactor

guidance = get_schema_guidance(EvaluationFactor)
# Output:
# SCHEMA GUIDANCE: EvaluationFactor
# - weight: Numerical weight (e.g., '40%', '25 points').
# - importance: Relative importance (e.g., 'Most Important').
# - subfactors: List of sub-criteria or subfactors.
#
# IDENTIFICATION HINTS:
# - Main factors typically have weight/importance fields populated
# - Subfactors reference parent factors or appear in subfactors list
# ...
```

### Problem Pattern (OLD)

```python
# ❌ BRITTLE: Hardcoded keyword matching
if any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    # Missing 'small business' → Factor F not discovered
```

### Solution Pattern (NEW)

```python
# ✅ ROBUST: Schema-driven LLM discovery
schema_guidance = get_evaluation_hierarchy_guidance()
prompt = f"""{schema_guidance}

EVALUATION_FACTOR_ENTITIES:
{factors_json}

Include ALL factors regardless of naming convention (e.g., "Small Business Participation" is a valid factor).
"""
```

### Key Findings (Updated)

| Algorithm | Brittleness Level | Primary Issue | Status |
|-----------|------------------|---------------|--------|
| Algorithm 1 | ✅ **FIXED** | Hardcoded instruction terms | Schema-driven (Issue #43) |
| Algorithm 2 | ✅ **FIXED** | Hardcoded factor keywords | Schema-driven (Issue #43) |
| Algorithm 5 | ✅ **FIXED** | Hardcoded document type categories | Schema-driven (Issue #43) |
| Algorithm 6 | 🟢 Low | Dynamic batching (good) | None needed |
| Algorithm 3 | 🟢 Low | Pure LLM reasoning | None needed |
| Algorithm 4 | 🟢 Low | Pure LLM reasoning | None needed |
| Algorithm 7 | ⚪ N/A | Heuristic patterns (by design) | None needed |
| Algorithm 8 | 🟢 Low | Pure LLM reasoning | None needed |

---

## Algorithm-by-Algorithm Analysis

### Algorithm 1: Instruction-Evaluation Linking ✅ FIXED (Issue #43)

**Previous Implementation** (brittle keyword matching):

```python
# BRITTLE: Hardcoded deliverable instruction patterns
deliverables_with_instructions = [
    e for e in entities_by_type.get('deliverable', [])
    if any(term in str(e.get('entity_name', '')).lower() 
           for term in ['proposal', 'submission', 'response', 'volume', 
                       'technical', 'cost', 'past performance'])
]
```

**New Implementation** (`src/inference/semantic_post_processor.py`):

```python
# SCHEMA-DRIVEN: Use schema guidance instead of keyword filtering
schema_guidance = get_instruction_evaluation_guidance()

# Include ALL deliverables as candidates - LLM identifies instruction entities
deliverable_candidates = entities_by_type.get('deliverable', [])[:100]

prompt = f"""{schema_guidance}

DELIVERABLE CANDIDATES (identify those with submission instruction semantics):
{deliv_json}

Use the SCHEMA GUIDANCE above to identify deliverables that function as submission instructions.
Look for: page limits, format requirements, volume assignments, proposal preparation guidance.
"""
```

**Schema Guidance Includes**:
- `SubmissionInstruction` field descriptions: `page_limit`, `format_reqs`, `volume`
- Identification hints: "Look for page limits, format requirements, volume assignments"
- Relationship guidance: "GUIDES: Instruction → Factor"

**Status**: ✅ **FIXED** - Issue #43 schema-driven refactoring

---

### Algorithm 2: Evaluation Hierarchy ✅ FIXED (Issue #43)

**Previous Implementation** (brittle keyword matching):

```python
# BRITTLE: Hardcoded factor keyword matching
elif any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    parts = name.split()
    root_key = parts[0].upper()
```

**Problem**: Missed "Factor F Small Business Participation and Subcontracting"

**New Implementation** (`src/inference/semantic_post_processor.py`):

```python
# SCHEMA-DRIVEN: Use EvaluationFactor schema guidance
schema_guidance = get_evaluation_hierarchy_guidance()

# Only use structural patterns (Factor A, Factor 1) for grouping - no keywords
# LLM discovers hierarchies using schema understanding

prompt = f"""{schema_guidance}

EVALUATION_FACTOR_ENTITIES:
{factors_json}

Include ALL factors regardless of naming convention (e.g., "Small Business Participation" is a valid factor).
"""
```

**Schema Guidance Includes**:
- `EvaluationFactor` field descriptions: `weight`, `importance`, `subfactors`
- Identification hints: "Main factors have weight/importance fields populated"
- Explicit instruction: "Include ALL factors regardless of naming"

**Status**: ✅ **FIXED** - Issue #43 schema-driven refactoring (enhanced from Branch 038)

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

### Algorithm 5: Document Hierarchy ✅ FIXED (Issue #43)

**Previous Implementation** (brittle type-based batching):

```python
# BRITTLE: Hardcoded document type categories
document_types = {
    'sections': ['section'],
    'attachments': ['attachment', 'exhibit', 'annex'],
    'amendments': ['amendment'],
    'clauses': ['clause', 'standard', 'specification', 'regulation']
}
```

**New Implementation** (`src/inference/semantic_post_processor.py`):

```python
# SCHEMA-DRIVEN: Use document hierarchy guidance from schema
schema_guidance = get_document_hierarchy_guidance()

# Use VALID_ENTITY_TYPES - no hardcoded categories
document_entity_types = {'document', 'section', 'clause', 'attachment'}
all_docs = [e for e in entities if e.get('entity_type') in document_entity_types]

# Single batch with all documents - discovers cross-type relationships
prompt = f"""{schema_guidance}

DOCUMENT ENTITIES (all types - discover cross-type relationships):
{docs_json}

Discover relationships ACROSS entity types (e.g., section referencing attachment).
"""
```

**Schema Guidance Includes**:
- Document type categories from `VALID_ENTITY_TYPES`
- Hierarchy relationship types: `CHILD_OF`, `ATTACHMENT_OF`, `AMENDS`, `INCORPORATES`
- Identification patterns: Section numbering, attachment naming, amendment references
- Cross-type discovery instructions

**Status**: ✅ **FIXED** - Issue #43 schema-driven refactoring

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

### Completed Actions (Issue #43)

- [x] **Algorithm 2 Fix**: Remove keyword matching, use schema-driven LLM guidance (**DONE**)
- [x] **Algorithm 1 Refactor**: Remove hardcoded instruction keywords (**DONE**)
- [x] **Algorithm 5 Refactor**: Remove type-based batching (**DONE**)
- [x] **Schema Prompts Utility**: Created `src/inference/schema_prompts.py` (**DONE**)
- [x] **Unit Tests**: Created `tests/test_schema_prompts.py` (**DONE**)

### Schema Prompts Utility

New utility module `src/inference/schema_prompts.py` provides:

```python
# Single schema extraction
from src.inference.schema_prompts import get_schema_guidance
from src.ontology.schema import EvaluationFactor

guidance = get_schema_guidance(EvaluationFactor)

# Multiple schemas combined
from src.inference.schema_prompts import get_multi_schema_guidance
guidance = get_multi_schema_guidance(EvaluationFactor, SubmissionInstruction)

# Specialized guidance functions
from src.inference.schema_prompts import (
    get_entity_type_guidance,          # VALID_ENTITY_TYPES categories
    get_document_hierarchy_guidance,   # Algorithm 5
    get_evaluation_hierarchy_guidance, # Algorithm 2
    get_instruction_evaluation_guidance # Algorithm 1
)
```

### Architecture Principle (Implemented)

**Guiding Rule**: Use hardcoded patterns ONLY for:
1. **Standardized formats** (CDRL/DID patterns, FAR clause numbers) - Algorithm 7
2. **Performance optimization** (sampling before LLM call to reduce tokens)
3. **Safety guardrails** (preventing hallucinations in critical paths)

**Use Schema-Driven LLM Guidance for**:
1. **Pattern discovery** (evaluation factors, instruction types) - Algorithms 1, 2
2. **Semantic relationships** (requirement↔factor mapping) - Algorithms 3, 4
3. **Cross-type hierarchy discovery** (documents, sections, attachments) - Algorithm 5

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
**Branch Context**: Issue #43 - Leverage Pydantic Schema Metadata for Algorithm Robustness  
**Related Issues**: 
- Issue #43: Schema-driven LLM prompts implementation
- Issue #38: Factor F discovery failure (Small Business not linked to hierarchy)
- Branch 038: Initial Algorithm 2 fix

**Files Changed**:
- `src/inference/schema_prompts.py` (NEW) - Schema extraction utilities
- `src/inference/semantic_post_processor.py` (MODIFIED) - Algorithms 1, 2, 5 refactored
- `tests/test_schema_prompts.py` (NEW) - Unit tests for schema utilities
