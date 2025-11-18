# Workload Extraction Regression Analysis

**Date**: November 18, 2025  
**Branch**: 020-user-prompt-integration (investigating issue from main)  
**Status**: CRITICAL REGRESSION IDENTIFIED

## Problem Statement

User reports that workload extraction queries are returning **QASP performance objectives** instead of actual **PWS workload drivers** - a significant regression from pre-branch-013b behavior.

**Example Issue:**

- **Query**: "Review the PWS and provide me a total list of workload drivers for the services described in Appendix F"
- **Expected Output**: "8 facilities", "1,600 daily visitors", "24/7 operations", "7-10 deliveries/week", etc.
- **Actual Output**: "Performance Objective PO-C1", "PO-F1", "PO-F2"... (QASP surveillance metrics)

## Root Cause Hypothesis

### Branch 013b Changed Workload Processing

From `docs/BRANCH_013B_WORKLOAD_SEMANTIC_FIXES.md`:

```
## Objectives

Fix the core issues identified in validation to achieve **85%+ production readiness**:

1. **Workload Enrichment** (0% → 100% target)
   - Add 7 BOE category metadata to REQUIREMENT entities
   - Enable capture manager queries for labor/materials/compliance analysis
```

**Key Change**: Branch 013b added Step 4 to `semantic_post_processor.py`:

```python
# Step 4: Workload Enrichment (BOE metadata for requirements)
logger.info("\n🏗️ Step 4: Enriching requirements with workload metadata...")
from src.inference.workload_enrichment import enrich_workload_metadata

workload_stats = await enrich_workload_metadata(
    neo4j_io=neo4j_io,
    llm_func=_call_llm_async,
    batch_size=50,
    model=llm_model_name,
    temperature=temperature
)
```

### The Problem

1. **Before Branch 013b**: Workload data extracted cleanly during initial RAG ingestion
2. **After Branch 013b**: Post-processing adds workload "enrichment" that appears to:
   - Tag REQUIREMENT entities with BOE categories
   - **Possibly conflate WORKLOAD_DRIVER entities with QASP_OBJECTIVE entities**
   - Interfere with knowledge graph retrieval priorities

### Evidence

**User's Working Query (Pre-013b)**:

```
Review the PWS and provide me a total list of workload drivers for the services described in PWS Appendix F. Workload could be frequencies, quantities, hours, coverage, equipment lists...etc., that can be used to help develop a Bases of Estimate for Labor Totals/Full Time Equivalents. Focus on totality and not samples. We need all the workload available.
```

**Result**: Clean extraction of actual PWS workload data

**Same Query (Post-013b)**:

- Returns QASP performance objectives instead
- Knowledge graph appears to prioritize QASP_OBJECTIVE entities over WORKLOAD_DRIVER entities

## Entity Type Confusion

From ontology (46 government contracting entity types):

- **WORKLOAD_DRIVER**: Actual operational requirements (facilities, volumes, frequencies, deadlines)
- **QASP_OBJECTIVE**: Performance surveillance metrics (PO-XX references, thresholds for surveillance)
- **PERFORMANCE_STANDARD**: Quality/service level expectations
- **SERVICE_LEVEL**: SLA/response time requirements

**Hypothesis**: The workload enrichment process may be:

1. Creating relationships between REQUIREMENT → QASP_OBJECTIVE that shouldn't exist
2. Altering retrieval weights so QASP entities rank higher than WORKLOAD entities
3. Misclassifying workload data as QASP data during enrichment

## Investigation Required

### 1. Check Workload Enrichment Logic

**File**: `src/inference/workload_enrichment.py`

- What entities does it enrich?
- Does it touch QASP_OBJECTIVE entities?
- Does it create relationships that confuse workload vs. QASP?

### 2. Check Relationship Inference

**File**: `src/inference/semantic_post_processor.py`

- Are EVALUATES, FULFILLS, or other relationships being created between PWS_SECTION → QASP_OBJECTIVE?
- Should these relationships only connect PWS_SECTION → WORKLOAD_DRIVER?

### 3. Test Without Workload Enrichment

**Experiment**:

```python
# In semantic_post_processor.py, comment out Step 4:
# logger.info("\n🏗️ Step 4: Enriching requirements with workload metadata...")
# from src.inference.workload_enrichment import enrich_workload_metadata
# workload_stats = await enrich_workload_metadata(...)

# Reprocess RFP, test query
```

**Expected**: If workload enrichment is the culprit, disabling it should restore pre-013b behavior

### 4. Check Neo4j Query Logic

**Question**: When user asks for "workload drivers for Appendix F", what Cypher query is LightRAG generating?

**Files to check**:

- LightRAG's query generation logic (in `lightrag` pip package)
- Does it filter by entity_type?
- Does it use semantic similarity that might rank QASP higher than WORKLOAD?

### 5. Validate Entity Extraction

**Check**: Are QASP objectives being incorrectly labeled as WORKLOAD_DRIVER during initial extraction?

**Tool**: Query Neo4j directly

```cypher
// Find all QASP objectives
MATCH (n)
WHERE n.entity_type CONTAINS 'QASP'
RETURN n.entity_name, n.entity_type, n.description
LIMIT 20

// Find all workload drivers
MATCH (n)
WHERE n.entity_type CONTAINS 'WORKLOAD'
RETURN n.entity_name, n.entity_type, n.description
LIMIT 20

// Check relationships from Appendix F section
MATCH (section:Entity {entity_type: 'PWS_SECTION'})-[r]->(target)
WHERE section.entity_name CONTAINS 'Appendix F'
RETURN section.entity_name, type(r), target.entity_type, target.entity_name
LIMIT 50
```

## Recommended Actions

### Immediate (Stop the Bleeding)

1. **Simplify user-facing prompts** ✅ DONE

   - Reverted Query 7.1, 7.2, 7.3 to simple working format
   - Removed overly complex prompt engineering that may interfere with retrieval

2. **Document the issue** ✅ THIS FILE
   - Capture user's observation about pre-013b better performance
   - Create hypothesis and investigation plan

### Short-Term (Diagnose)

3. **Test without workload enrichment**

   - Comment out Step 4 in semantic_post_processor.py
   - Reprocess same RFP
   - Test Query 7.2 on Appendix F
   - Compare results

4. **Query Neo4j directly**

   - Examine QASP vs WORKLOAD entity distribution
   - Check relationships from PWS sections
   - Identify if entity types are confused

5. **Review extraction prompts**
   - Check `prompts/extraction/` for entity classification rules
   - Ensure QASP objectives are correctly classified
   - Ensure workload drivers are correctly classified

### Long-Term (Fix)

6. **If workload enrichment is the problem**:

   - Redesign enrichment to NOT touch QASP entities
   - Add entity type filtering to enrichment logic
   - Only enrich WORKLOAD_DRIVER and REQUIREMENT entities

7. **If relationship inference is the problem**:

   - Fix relationship detection to separate QASP from PWS workload
   - Add explicit filtering: PWS_SECTION → WORKLOAD_DRIVER (not QASP_OBJECTIVE)

8. **If LightRAG retrieval is the problem**:

   - May need to add entity_type filtering to user_prompt
   - Example: "Only retrieve WORKLOAD_DRIVER entities, exclude QASP_OBJECTIVE"

9. **If extraction is the problem**:
   - Fix entity classification during initial extraction
   - Improve prompts to distinguish QASP surveillance from PWS workload

## Success Criteria

**Test Query**:

```
Review the PWS and provide me a total list of workload drivers for the services described in Appendix F. Workload could be frequencies, quantities, hours, coverage, equipment lists...etc. Focus on totality and not samples. We need all the workload available.
```

**Expected Output**:

```
Appendix F Workload Drivers:

F.2.1 Facilities:
- 8 facilities to operate and maintain
- 24/7 operations required
- 1,600 daily visitors average

F.2.2 Resale Operations:
- Daily inventories (submission NLT 0900)
- Weekly full resale inventories
- $2,000-$5,000 nightly sales ($10,000 during special events)

F.2.3 Equipment:
- 12 refrigeration units (3x daily temperature checks)
- 450 fitness equipment pieces (weekly inspection, monthly maintenance)
- 95% operational standard required

F.2.4 Events:
- Minimum 2 special events/month
- 14-16 ongoing activities
- Each activity 2x daily
- 7-10 vendor deliveries/week

F.2.5 Deliverables:
- Hourly customer counts (daily submission)
- Daily inventory reports (NLT 0900)
- Monthly performance reports (by 5th of month)
- After-action reports (within 48 hours of event)
```

**MUST NOT Output**:

```
❌ Performance Objective PO-C1: no more than two (2) customer service desk coverage discrepancies
❌ Performance Objective PO-F1: threshold: no violations allowed
❌ Performance Objective PO-F2: no more than two (2) late recreation services events
❌ Surveillance Method: periodic inspection
```

## User Feedback

> "There is an issue with how the workload data is being inferenced. We had better results when there was not workload inferencing being done in extraction or post processing which was pre branch 013b. We need to look deep and hard into this issue as the current method is a significant regression."

**Translation**: The system worked better when it just extracted entities cleanly without trying to "enrich" or "infer" workload metadata. The added intelligence is causing confusion between QASP surveillance metrics and actual PWS operational workload.

## Next Steps

1. ✅ Simplify user prompts (completed)
2. ⏳ Test query without workload enrichment Step 4
3. ⏳ Query Neo4j to examine entity type distribution
4. ⏳ Review extraction prompts for classification rules
5. ⏳ Compare pre-013b vs post-013b branch behavior
6. ⏳ Fix root cause (TBD based on diagnosis)

**Estimated Investigation Time**: 2-4 hours  
**Estimated Fix Time**: 1-4 hours (depending on root cause)

---

**Last Updated**: November 18, 2025 (Branch 020 - Initial Analysis)
