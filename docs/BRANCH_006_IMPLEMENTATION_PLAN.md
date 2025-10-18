# Branch 006: Post-Processing Fix & UCF Removal

**Branch**: `006-post-processing-fix`  
**Date**: October 18, 2025  
**Status**: Planning  
**Charter**: Remove UCF detection, generalize prompts, ensure post-processing reliability

---

## Executive Summary

**Problem Identified:**

1. UCF detection creates section metadata that RAG-Anything never reads
2. Inference prompts assume UCF structure (Section L/M terminology)
3. Post-processing may have timing issues with GraphML readiness
4. Unnecessary complexity: 600+ lines of UCF code providing no value

**Solution:**

1. Remove UCF detection entirely (detector.py, processor.py)
2. Generalize relationship inference prompts (Section L/M → generic terms)
3. Simplify processing flow to single path
4. Remove ENABLE_POST_PROCESSING toggle (always run)
5. Add robust GraphML readiness checks

**Benefits:**

- ✅ Works with ALL RFP formats (UCF, task orders, FOPRs, quotes)
- ✅ 600+ fewer lines of code
- ✅ Simpler architecture (one path for all documents)
- ✅ More reliable (fewer failure modes)
- ✅ Post-processing always runs (no configuration needed)

---

## Root Cause Analysis

### Why GraphML Creation Might Be Slow

```python
# Timeline for document processing:
await rag_instance.process_document_complete(...)
# ⬆️ This includes:
# t=0-30s: MinerU multimodal parsing (PDF → structured JSON)
# t=30-90s: LLM entity extraction (8K chunks, 5-6 passes with Grok)
# t=90-100s: LightRAG graph assembly (entities → GraphML)
# t=100s: File system write + buffer flush (Windows may delay)

# Current code waits 1 second after process_document_complete() returns
await asyncio.sleep(1)  # Not enough if filesystem buffers
```

**The Real Issue:**

- `process_document_complete()` is SUPPOSED to be synchronous
- If GraphML isn't ready when it returns, that's a bug we should handle
- Current 1-second wait is a Band-Aid, not a fix

**Proper Solution:**

- Poll for GraphML existence with exponential backoff (1s, 2s, 4s, 8s)
- Validate GraphML has actual content (size > 100 bytes)
- Log if we need more than 1 retry (indicates upstream issue)

---

## Implementation Plan

### Phase 1: Remove UCF Detection (2 hours)

#### **Step 1.1: Delete UCF Files**

```bash
# Files to DELETE:
src/ingestion/detector.py         # 300 lines - UCF pattern detection
src/ingestion/processor.py        # 300 lines - Section boundary extraction
```

#### **Step 1.2: Update Module Imports**

**File: `src/ingestion/__init__.py`**

Remove:

```python
from src.ingestion.detector import detect_ucf_format, UCFDetectionResult
from src.ingestion.processor import prepare_ucf_sections_for_llm
```

Update exports:

```python
__all__ = [
    # Remove: "detect_ucf_format", "UCFDetectionResult", "prepare_ucf_sections_for_llm"
]
```

#### **Step 1.3: Simplify Routes**

**File: `src/server/routes.py`**

**BEFORE** (lines 19-150):

```python
async def process_document_with_ucf_detection(file_path, file_name, rag_instance, llm_func):
    # Lines 54-95: UCF detection + section metadata
    ucf_result = detect_ucf_format(document_text, file_name)
    if ucf_result.is_ucf and ucf_result.confidence >= 0.70:
        sections = prepare_ucf_sections_for_llm(...)
        # Save metadata that's never read

    # Lines 112-145: Always use same RAG-Anything method anyway
    await rag_instance.process_document_complete(...)
```

**AFTER** (simplified):

```python
async def process_document_with_semantic_inference(
    file_path: str,
    file_name: str,
    rag_instance,
    llm_func
) -> dict:
    """
    Integrated document processing with semantic relationship inference.

    Works with ALL RFP formats (UCF, task orders, quotes, FOPRs).
    No format detection needed - LLM handles structure semantically.

    Pipeline:
    1. RAG-Anything multimodal processing (MinerU parser)
    2. LLM entity extraction (17 types with metadata)
    3. LLM relationship inference (5 algorithms)
    4. Save complete knowledge graph

    Args:
        file_path: Path to document file
        file_name: Original filename
        rag_instance: Initialized RAGAnything instance
        llm_func: LLM function for relationship inference

    Returns:
        dict: Processing result with relationships_inferred count
    """
    logger.info(f"📄 Processing {file_name}")
    logger.info(f"🔧 Using RAG-Anything + LLM semantic inference (format-agnostic)")

    # Step 1: Multimodal extraction + entity extraction
    await rag_instance.process_document_complete(
        file_path=file_path,
        output_dir=global_args.working_dir,
        parse_method="auto"
    )

    # Step 2: CRITICAL - Wait for GraphML with robust retry logic
    graphml_path = Path(global_args.working_dir) / "graph_chunk_entity_relation.graphml"

    max_retries = 5
    wait_times = [1, 2, 3, 4, 5]  # Exponential-ish backoff

    for attempt, wait_time in enumerate(wait_times):
        await asyncio.sleep(wait_time)

        if graphml_path.exists() and graphml_path.stat().st_size > 100:
            logger.info(f"✅ GraphML ready after {sum(wait_times[:attempt+1])}s total wait")
            break

        logger.warning(
            f"⏳ GraphML not ready (attempt {attempt+1}/{max_retries}), "
            f"waiting {wait_time}s... (total wait: {sum(wait_times[:attempt+1])}s)"
        )
    else:
        # All retries exhausted
        logger.error(
            f"❌ GraphML never populated after {sum(wait_times)}s total wait. "
            f"This indicates RAG-Anything processing failed."
        )
        return {
            "relationships_inferred": 0,
            "error": "GraphML file not created"
        }

    # Step 3: Capture BEFORE state for validation
    nodes_before, edges_before = parse_graphml(graphml_path)
    logger.info(f"📊 PRE-INFERENCE: {len(nodes_before)} entities, {len(edges_before)} relationships")

    # Step 4: Run LLM-powered relationship inference
    logger.info(f"🤖 Running LLM-powered relationship inference (5 algorithms)...")
    inference_result = await post_process_knowledge_graph(global_args.working_dir, llm_func)

    # Step 5: Validate AFTER state
    nodes_after, edges_after = parse_graphml(graphml_path)
    actual_new_rels = len(edges_after) - len(edges_before)

    logger.info(f"📊 POST-INFERENCE: {len(nodes_after)} entities, {len(edges_after)} relationships")
    logger.info(f"✅ VALIDATED: {actual_new_rels} new relationships persisted to GraphML")

    if actual_new_rels != inference_result.get("relationships_added", 0):
        logger.warning(
            f"⚠️ Mismatch: Inference reported {inference_result.get('relationships_added')} "
            f"but GraphML delta is {actual_new_rels}"
        )

    return {
        "relationships_inferred": actual_new_rels,
        "inference_result": inference_result
    }
```

**Update endpoint calls** (lines 301, 355):

```python
# Change function name:
process_document_with_ucf_detection → process_document_with_semantic_inference
```

#### **Step 1.4: Remove Background Monitor**

**Rationale**: With synchronous post-processing integrated, no need for background monitor.

**File: `src/server/routes.py`**

DELETE: `async def semantic_post_processor_monitor()` (lines 384-430)

**File: `src/raganything_server.py`**

Remove reference to background monitor (line 109):

```python
# DELETE this line:
print(f"   Background monitor: Removed (synchronous post-processing)\n")
```

#### **Step 1.5: Remove ENABLE_POST_PROCESSING Toggle**

**File: `.env`**

DELETE:

```bash
# Semantic Post-Processing Configuration
ENABLE_POST_PROCESSING=true
```

**File: `src/server/routes.py`**

Remove conditional check (lines 124-143):

```python
# DELETE:
enable_post_processing = os.getenv("ENABLE_POST_PROCESSING", "true").lower() == "true"

if llm_func and enable_post_processing:
    # ... post-processing ...
elif not enable_post_processing:
    logger.info(f"ℹ️ Post-processing disabled (ENABLE_POST_PROCESSING=false)")
else:
    logger.info(f"ℹ️ No LLM function provided, skipping relationship inference")
```

**Replace with:**

```python
# Post-processing ALWAYS runs (no toggle needed)
if llm_func:
    # ... post-processing ...
else:
    logger.error(f"❌ No LLM function provided - cannot run relationship inference")
    # This is a critical error - server should not start without LLM
```

---

### Phase 2: Generalize Inference Prompts (2 hours)

#### **Problem**: Prompts assume UCF structure

Current prompts use UCF-specific terminology:

- "Section L" and "Section M"
- "Instructions to Offerors"
- "Evaluation Factors for Award"

But other agencies use:

- **GSA**: "Proposal Instructions" → "Selection Criteria"
- **DHS**: "Quote Instructions" → "Award Methodology"
- **NASA**: "Offer Requirements" → "Evaluation Approach"
- **State/Local**: "Submission Guidelines" → "Scoring Rubric"

#### **Solution**: Entity Types Are Already Generic!

We extract:

- ✅ `SUBMISSION_INSTRUCTION` (not "Section L content")
- ✅ `EVALUATION_FACTOR` (not "Section M content")

We just need to make **prompts terminology-agnostic**.

#### **Files to Update**:

1. `prompts/relationship_inference/section_l_m_mapping.md`
2. `prompts/relationship_inference/section_l_m_linking.md`

#### **Changes Needed**:

**Pattern to Replace:**

Find: References to "Section L", "Section M", "Instructions to Offerors", "Evaluation Factors for Award"

Replace with: Generic terminology + examples from multiple agencies

**Example Transformation:**

**BEFORE**:

```markdown
## Context

Section L (Instructions to Offerors) provides submission guidelines that
directly relate to how proposals are evaluated in Section M (Evaluation Factors).
```

**AFTER**:

```markdown
## Context

Submission instructions (regardless of section label) provide guidelines that
directly relate to how proposals are evaluated. These may appear as:

- **Federal UCF Format**: Section L (Instructions) → Section M (Evaluation Factors)
- **GSA Task Orders**: "Proposal Instructions" → "Selection Criteria"
- **DHS Solicitations**: "Quote Instructions" → "Award Methodology"
- **NASA Procurements**: "Offer Requirements" → "Evaluation Approach"
- **State/Local**: "Submission Guidelines" → "Scoring Rubric"
- **Embedded Format**: Evaluation factors contain format requirements within description

Entity types extracted:

- `SUBMISSION_INSTRUCTION`: Page limits, format requirements, volume structure
- `EVALUATION_FACTOR`: Scoring criteria, relative importance, subfactors

Understanding these relationships is critical for proposal compliance,
regardless of RFP structure or agency terminology.
```

**BEFORE (Examples)**:

```markdown
### Explicit Volume References

- **Section L**: "Technical Approach Volume limited to 25 pages"
- **Section M**: "Factor 1: Technical Approach (40% weight)"
```

**AFTER (Examples)**:

```markdown
### Explicit Volume/Factor References

**UCF Format Example**:

- **Instruction**: "Technical Approach Volume limited to 25 pages" (Section L)
- **Factor**: "Factor 1: Technical Approach (40% weight)" (Section M)
- **Relationship**: Volume name matches factor name

**Task Order Format Example**:

- **Instruction**: "Technical proposal shall not exceed 15 pages"
- **Criterion**: "Technical Approach (Most Important)"
- **Relationship**: Topic alignment + page limit constraint

**Embedded Format Example**:

- **Factor Description**: "The Government will evaluate technical approach...
  Technical volume limited to 20 pages."
- **Relationship**: Instruction embedded within factor description
```

#### **Detection Rule Updates**:

**BEFORE**:

```markdown
1. **Direct Name Matching**: Factor/volume names appear in both sections
   - Case-insensitive comparison
   - Partial matches acceptable (e.g., "Technical" matches "Technical Approach")
```

**AFTER**:

```markdown
1. **Direct Name Matching**: Instruction topic matches evaluation factor topic
   - Case-insensitive comparison
   - Partial matches acceptable (e.g., "Technical" matches "Technical Approach")
   - Works across terminology: "Volume", "Proposal", "Submission", "Response"
   - Examples:
     - "Technical Volume" → "Technical Approach Factor"
     - "Management Proposal" → "Management Criterion"
     - "Past Performance Response" → "Past Performance Evaluation"
```

#### **Special Cases to Add**:

```markdown
### Non-UCF Format Patterns

#### Pattern 1: Embedded Instructions (No Separate Instruction Section)

**Example**:
```

EVALUATION CRITERION 2: Management Approach (Significantly More Important)

The Government will evaluate the offeror's management plan including:

- Staffing approach and key personnel qualifications
- Training program and quality assurance procedures

Management proposal shall not exceed 15 pages, 12-point font, 1-inch margins.

```

**Detection**:
1. Extract EVALUATION_FACTOR "Criterion 2: Management Approach"
2. Extract SUBMISSION_INSTRUCTION "Management proposal format requirements"
3. Create GUIDES relationship (confidence: 0.85 - embedded within factor)

#### Pattern 2: Generic Terminology (No "Section L" or "Section M")

**Example**:
```

Proposal Requirements:

- Technical approach (20 pages maximum)
- Management plan (10 pages maximum)

Selection Criteria:

- Technical merit (40 points)
- Management capability (30 points)

```

**Detection**:
1. Map "Technical approach" instruction → "Technical merit" criterion
2. Map "Management plan" instruction → "Management capability" criterion
3. Use semantic similarity (topic alignment) since naming differs
```

---

### Phase 3: Testing & Validation (1 hour)

#### **Test Case 1: UCF Format RFP (Navy MBOS)**

**Expected Results**:

- ✅ Entity extraction works (no UCF detection needed)
- ✅ Post-processing runs automatically
- ✅ L↔M relationships inferred (using generic prompt)
- ✅ GraphML validation shows new relationships

**Validation Commands**:

```powershell
# Check for post-processing log messages:
# "🤖 Running LLM-powered relationship inference"
# "📊 PRE-INFERENCE: X entities, Y relationships"
# "📊 POST-INFERENCE: X entities, Y+Z relationships"
# "✅ VALIDATED: Z new relationships persisted"
```

#### **Test Case 2: Non-UCF Format (Task Order / FOPR)**

**Test File**: Any GSA task order, DHS quote, or state/local RFP

**Expected Results**:

- ✅ Processes without errors (no UCF section detection)
- ✅ Extracts SUBMISSION_INSTRUCTION entities (regardless of label)
- ✅ Extracts EVALUATION_FACTOR entities (regardless of terminology)
- ✅ Infers relationships using generic patterns

**Validation**:

- Query: "What are the submission instructions?"
- Query: "What are the evaluation factors?"
- Query: "Which instructions relate to which factors?"

#### **Test Case 3: Embedded Format (Instructions Within Factors)**

**Characteristics**: No separate instruction section, format requirements embedded in factor descriptions

**Expected Results**:

- ✅ Detects embedded instructions
- ✅ Creates GUIDES relationships with confidence ~0.8
- ✅ No errors about missing sections

---

## Success Criteria

### Code Quality

- [ ] **-600 lines of code** (detector.py + processor.py removed)
- [ ] **Single processing path** (no UCF/non-UCF branching)
- [ ] **No ENABLE_POST_PROCESSING toggle** (always runs)
- [ ] **Robust GraphML wait logic** (retry with backoff)

### Functional Requirements

- [ ] **Works with UCF RFPs** (Navy MBOS baseline)
- [ ] **Works with non-UCF formats** (task orders, quotes, FOPRs)
- [ ] **Post-processing always runs** (no configuration needed)
- [ ] **Relationships validated** (before/after counts logged)

### Prompt Generalization

- [ ] **No "Section L" or "Section M" assumptions** (generic terminology)
- [ ] **Multiple agency examples** (GSA, DHS, NASA, state/local)
- [ ] **Embedded instruction patterns** (handles all formats)

### Testing

- [ ] **Navy MBOS re-processed** (baseline validation)
- [ ] **Non-UCF RFP tested** (new format validation)
- [ ] **WebUI graph inspection** (relationships visible)
- [ ] **Query validation** (relationships queryable)

---

## Implementation Checklist

### Phase 1: Remove UCF Detection

- [ ] Delete `src/ingestion/detector.py`
- [ ] Delete `src/ingestion/processor.py`
- [ ] Update `src/ingestion/__init__.py` (remove imports)
- [ ] Rename `process_document_with_ucf_detection()` → `process_document_with_semantic_inference()`
- [ ] Simplify function (remove UCF logic)
- [ ] Add robust GraphML wait logic
- [ ] Add before/after validation
- [ ] Remove background monitor function
- [ ] Remove ENABLE_POST_PROCESSING from `.env`
- [ ] Remove ENABLE_POST_PROCESSING check from code
- [ ] Update both endpoint calls (`/insert`, `/documents/upload`)

### Phase 2: Generalize Prompts

- [ ] Update `section_l_m_mapping.md` header and context
- [ ] Update `section_l_m_mapping.md` examples (add non-UCF)
- [ ] Update `section_l_m_mapping.md` detection rules
- [ ] Update `section_l_m_linking.md` header and context
- [ ] Update `section_l_m_linking.md` patterns (add embedded, generic)
- [ ] Update `section_l_m_linking.md` examples
- [ ] Review `document_section_linking.md` for UCF assumptions
- [ ] Review `clause_clustering.md` for UCF assumptions

### Phase 3: Testing

- [ ] Process Navy MBOS (baseline validation)
- [ ] Verify post-processing runs (log messages)
- [ ] Verify relationships added (before/after counts)
- [ ] Process non-UCF RFP (format validation)
- [ ] Query for relationships (WebUI + API)
- [ ] Inspect GraphML (relationship types, confidence)

### Phase 4: Documentation

- [ ] Update `README.md` (remove UCF references)
- [ ] Update `ARCHITECTURE.md` (single processing path)
- [ ] Create `BRANCH_006_COMPLETION.md` (results summary)
- [ ] Archive this implementation plan

---

## Risk Analysis

### Low Risk

- ✅ **Removing unused code** (detector/processor never actually used)
- ✅ **Simplifying flow** (fewer code paths = fewer bugs)
- ✅ **Removing toggle** (post-processing should always run)

### Medium Risk

- ⚠️ **Prompt generalization** (might reduce UCF performance slightly)
  - Mitigation: UCF examples still included, just not exclusive
  - Validation: Re-test Navy MBOS to ensure no regression

### High Risk (Mitigated)

- ⚠️ **GraphML timing issues** (if wait logic insufficient)
  - Mitigation: Exponential backoff with 5 retries (15s total)
  - Fallback: Explicit error message if GraphML never appears
  - Validation: Log actual wait times to identify upstream issues

---

## Rollback Plan

If Phase 2 testing reveals issues:

1. **Keep Phase 1 changes** (UCF removal is pure simplification)
2. **Revert prompt changes** (restore UCF-specific terminology temporarily)
3. **Investigate root cause** (why generic prompts underperform)
4. **Iterate on prompts** (find better generic patterns)

Rollback is low-risk because:

- UCF detection wasn't working anyway (metadata never consumed)
- Entity types remain unchanged (SUBMISSION_INSTRUCTION, EVALUATION_FACTOR)
- Only prompt wording changes, not extraction logic

---

## Timeline

**Total Estimated Time**: 5-6 hours

- **Phase 1 (Remove UCF)**: 2 hours

  - Delete files: 10 minutes
  - Update imports: 10 minutes
  - Simplify routes.py: 60 minutes
  - Remove toggles: 10 minutes
  - Testing: 30 minutes

- **Phase 2 (Generalize Prompts)**: 2 hours

  - Update section_l_m_mapping.md: 45 minutes
  - Update section_l_m_linking.md: 45 minutes
  - Review other prompts: 30 minutes

- **Phase 3 (Testing)**: 1-2 hours
  - Navy MBOS re-processing: 10 minutes
  - Non-UCF RFP testing: 30 minutes
  - Relationship validation: 30 minutes
  - Query testing: 30 minutes

---

## Next Steps

**Ready to proceed?** I recommend:

1. **Start with Phase 1** (remove UCF) - This is pure simplification
2. **Test immediately** with Navy MBOS to ensure post-processing works
3. **Then Phase 2** (generalize prompts) once we confirm baseline works
4. **Then Phase 3** (test non-UCF) to validate generalization

Want me to start implementing Phase 1, or would you like to review this plan first?
