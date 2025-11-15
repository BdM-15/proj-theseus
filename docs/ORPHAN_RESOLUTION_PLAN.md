# Holistic Orphan Resolution Plan
## Pattern-Based Relationship Inference Enhancement

**Date**: November 15, 2025  
**Branch**: To be created  
**Objective**: Fix orphaned entities by discovering and implementing missing relationship patterns, not just individual items

---

## Root Cause Analysis

### Pattern 1: High Co-Occurrence, Zero Relationships
**Finding**: 13 orphaned concepts (DODAAC codes) share chunks with 13+ connected clauses/documents  
**Why LLM Missed It**: Table-embedded field values aren't semantically linked to clause text  
**Impact**: Administrative workflow entities isolated from contract clauses

### Pattern 2: Missing Relationship Type Coverage
**Current State**:
- `DIRECTED`: 3,617 relationships (73.8%)
- `INFERRED_RELATIONSHIP`: 1,285 relationships (26.2%)

**Under-Represented Patterns**:
```
equipment → requirement:   31 existing vs 4 orphaned equipment (11.4% orphan rate)
deliverable → requirement: 135 existing vs 3 orphaned deliverables (2.2% orphan rate)  
person → deliverable:      25 existing vs 6 orphaned persons (19.4% orphan rate)
technology → requirement:  2 existing vs 2 orphaned tech (50% orphan rate!)
```

**Critical**: `technology → requirement` has 50% orphan rate - this is ODC-critical (Gov't-provided equipment)

### Pattern 3: Semantic Description Patterns
**Table-Embedded** (7 orphans): "field in WAWF routing data table"  
**Government-Role** (4 orphans): "provided by the Government", "furnished"  
**Conditional** (2 orphans): "may substitute", "as necessary"  
**Quantified** (4 orphans): Has specific quantities (10 receptacles, 6 trash cans)

### Pattern 4: Rich Context, Still Missed
**All orphan chunks have 40+ entities with 7-9 type diversity**  
→ This proves chunks ARE processed, but LLM fails on specific semantic patterns

---

## Solution Architecture

### Phase 1: Targeted Relationship Inference Algorithms
**Goal**: Add specialized algorithms for discovered patterns

#### Algorithm 1: Equipment-Requirement Quantified Matcher
```python
Pattern: "X [equipment] must be Y [action] Z [frequency/metric]"
Example: "Trash Receptacles must be emptied no less than twice a day"

Logic:
1. Find requirements with quantified actions (frequency/metric)
2. Extract equipment nouns from requirement description
3. Match to orphaned equipment entities by name similarity
4. Create REQUIRES relationship (requirement → equipment)
```

#### Algorithm 2: Government-Provided Equipment Linker
```python
Pattern: "Government provides/furnishes [equipment] for [requirement]"
Example: "Ancillary Hardware provided by Government for PWS requirements"

Logic:
1. Find orphaned equipment/technology with "government" + "provided/furnished"
2. Extract requirement context from description
3. Match to requirements mentioning same equipment category
4. Create ENABLED_BY relationship (requirement → technology)
```

#### Algorithm 3: Deliverable-Submitter Linker
```python
Pattern: "[Person role] shall submit [deliverable]"
Example: "Program Manager photo required in Key Contact Listing"

Logic:
1. Find orphaned deliverables with submission requirements
2. Extract person roles mentioned in description
3. Match to person entities with same role
4. Create RESPONSIBLE_FOR relationship (person → deliverable)
```

#### Algorithm 4: Table-Embedded Field Context Linker
```python
Pattern: "[Field], a field in [Table] for [Purpose]"
Example: "Admin DODAAC, a field in WAWF routing table for administration"

Logic:
1. Find orphaned concepts with "field in" + table reference
2. Find clauses/documents mentioning the same table
3. Create FIELD_IN relationship (concept → document/clause)
```

---

### Phase 2: Enhanced LLM Prompts
**Goal**: Improve general-purpose relationship inference for discovered patterns

#### Current Prompt Issues
```python
# Current semantic_post_processor.py prompt (line ~120)
"""
Relationship types to use:
- EVALUATES: Section M evaluation criteria → Section L requirements
- FULFILLS: Deliverable → Requirement it satisfies
- REQUIRES: Requirement → Equipment/Resource needed
- REFERENCES: Document/Section → Another document/section
- APPLIES_TO: Clause/Regulation → Program/Contract
- PART_OF: Sub-component → Parent component
"""
```

**Problems**:
1. Missing `ENABLED_BY` (for Gov't-provided equipment → requirements)
2. Missing `RESPONSIBLE_FOR` (person → deliverable)
3. No guidance for quantified/conditional entities
4. No table-embedded entity handling

#### Enhanced Prompt
```python
"""
Relationship types to use:

REQUIREMENT-CENTRIC:
- REQUIRES: Requirement → Equipment/Resource needed (including quantities)
- ENABLED_BY: Requirement → Government-provided Technology/Equipment
- FULFILLED_BY: Requirement → Deliverable that satisfies it
- RESPONSIBLE_FOR: Person → Deliverable they submit/create

STRUCTURAL:
- PART_OF: Sub-component → Parent component
- FIELD_IN: Table field → Table/Document containing it
- REFERENCES: Document/Section → Another document/section

REGULATORY:
- EVALUATES: Section M evaluation criteria → Section L requirements  
- APPLIES_TO: Clause/Regulation → Program/Contract

SPECIAL PATTERNS TO CATCH:
1. Quantified equipment: "X receptacles must be Y" → REQUIRES(requirement → equipment)
2. Government-provided: "furnished by Government" → ENABLED_BY(requirement → technology)
3. Conditional equipment: "may substitute" → REQUIRES(requirement → equipment)
4. Table fields: "field in X table" → FIELD_IN(concept → document)
5. Person submissions: "shall submit" → RESPONSIBLE_FOR(person → deliverable)
"""
```

---

### Phase 3: Orphan Detection & Correction Pipeline
**Goal**: Automated workflow to detect and fix orphans in future RFPs

#### Component 1: Post-Phase-6 Orphan Detector
```python
# src/inference/orphan_detection.py

async def detect_orphan_patterns(neo4j_io: Neo4jGraphIO) -> Dict:
    """
    Run after Phase 6/7 completion to identify orphan patterns.
    
    Returns:
        {
            'orphans_by_type': {...},
            'critical_orphans': [...],  # ODC/BOE-relevant
            'fixable_patterns': [...],   # Match algorithms 1-4
            'peripheral_orphans': [...]  # Admin/minor, accept as-is
        }
    """
```

#### Component 2: Pattern-Based Fixer
```python
# src/inference/orphan_fixer.py

async def fix_orphans_by_pattern(
    neo4j_io: Neo4jGraphIO,
    patterns: List[str]  # ['equipment_quantified', 'govt_provided', ...]
) -> Dict:
    """
    Apply algorithms 1-4 to create missing relationships.
    
    Returns:
        {
            'relationships_created': 123,
            'orphans_fixed': 45,
            'remaining_orphans': 12
        }
    """
```

#### Component 3: Integration into routes.py
```python
# After Phase 7 completes
inference_result = await enhance_knowledge_graph(...)

# NEW: Orphan detection and fixing
from src.inference.orphan_detection import detect_orphan_patterns
from src.inference.orphan_fixer import fix_orphans_by_pattern

orphan_analysis = await detect_orphan_patterns(neo4j_io)

if orphan_analysis['critical_orphans']:
    logger.info(f"⚠️  {len(orphan_analysis['critical_orphans'])} critical orphans detected")
    logger.info("🔧 Running pattern-based orphan fixer...")
    
    fix_result = await fix_orphans_by_pattern(
        neo4j_io,
        patterns=['equipment_quantified', 'govt_provided', 'person_deliverable', 'table_field']
    )
    
    logger.info(f"✅ Fixed {fix_result['orphans_fixed']} orphans")
    logger.info(f"📊 {fix_result['remaining_orphans']} orphans remain (peripheral/acceptable)")
```

---

## Implementation Plan

### Branch: `019-pattern-based-orphan-resolution`

### Step 1: Create Targeted Algorithms (2-3 hours)
**Files**:
- `src/inference/orphan_patterns.py` - Pattern matchers (Algorithms 1-4)
- `tests/test_orphan_patterns.py` - Unit tests for each algorithm

**Deliverable**: 4 working algorithms that can create relationships for discovered patterns

### Step 2: Enhance LLM Prompts (1 hour)
**Files**:
- `src/inference/semantic_post_processor.py` - Update relationship inference prompt
- `prompts/relationship_inference/enhanced_patterns.txt` - Detailed examples

**Deliverable**: Improved general-purpose relationship inference

### Step 3: Build Detection & Correction Pipeline (2 hours)
**Files**:
- `src/inference/orphan_detection.py` - Post-Phase-6 orphan analyzer
- `src/inference/orphan_fixer.py` - Pattern-based relationship creator
- `src/server/routes.py` - Integration into processing pipeline

**Deliverable**: Automated orphan fixing after Phase 6/7

### Step 4: Validation (1 hour)
**Test Cases**:
1. Re-process Amend 1 FOPR (clear Neo4j first)
2. Verify orphan count reduction (target: <10 orphans, <1%)
3. Verify critical patterns fixed:
   - Sanitizing Wipes → Sanitizing Wipes Requirement
   - Trash Receptacles → Trash Emptying Requirement
   - Ancillary Hardware → Requirements using it
4. Validate no relationship quality regression

**Acceptance Criteria**:
- Orphan rate < 1% (currently 2.4%)
- All ODC-critical items linked (equipment, gov't-provided, deliverables)
- All BOE-critical items linked (person roles, deliverables, requirements)
- No false-positive relationships created

---

## Success Metrics

**Before (Current State)**:
- Total orphans: 34/1,410 = 2.4%
- Critical orphans: 12 (equipment, deliverables, gov't-provided)
- Technology → requirement orphan rate: 50%

**After (Target)**:
- Total orphans: <14/1,410 = <1%
- Critical orphans: 0
- Technology → requirement orphan rate: <10%
- Pattern coverage: 100% of discovered patterns have algorithms

---

## Risks & Mitigations

**Risk 1**: False-positive relationships (incorrect links)  
**Mitigation**: Confidence thresholds + human review for first RFP, then auto-apply

**Risk 2**: Pattern overfitting (works for ISS FOPR, fails on other RFPs)  
**Mitigation**: Test on multiple RFP types (FOPR, full RFP, task order)

**Risk 3**: LLM prompt changes affect existing quality  
**Mitigation**: A/B test enhanced prompts vs current prompts, compare metrics

---

## Next Actions

1. **User Decision**: Approve plan and create branch 019?
2. **Implementation**: Start with Algorithm 1 (equipment-requirement quantified matcher)
3. **Validation**: Test on current graph before clearing and reprocessing
4. **Iteration**: Refine algorithms based on results, then move to Step 2

**Estimated Total Time**: 6-8 hours for complete implementation and validation
