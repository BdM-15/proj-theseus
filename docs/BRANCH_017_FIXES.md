# Branch 017: Dependency Upgrade Fixes

**Date**: November 15, 2025  
**Branch**: `017-dependency-upgrades`  
**Issue**: Entity over-extraction and contamination after upgrading to MinerU 2.6.4 + LightRAG 1.4.9.8

---

## Problem Statement

After upgrading dependencies, ISS RFP processing showed:

- **2,858 total entities** (baseline: 1,445) = **2x increase**
- **349 requirements** (baseline: 142) = **2.5x over-extraction**
- **48 contaminated entities** with non-RFP terms:
  - Meta-extraction: "Knowledge Graph", "Knowledge Retrieval", "Extraction Errors"
  - Process analysis: "OCR Extraction Errors", "Automated Extraction Workflows"
  - Fictional characters: References to "Alex", "Taylor", "Jordan" from LightRAG examples

---

## Root Causes Identified

### Root Cause #1: Gleaning Multiplication Effect

**What happened**: `ENTITY_EXTRACT_MAX_GLEANING=2` caused 3 extraction passes (1 initial + 2 gleaning)

**Why it became a problem**:

- MinerU 2.6.4 produces exceptionally clean OCR (30%+ accuracy improvement)
- Clean output → aggressive first-pass extraction (~200+ requirements)
- Each gleaning pass finds "variations" as "new" entities
- Result: 142 baseline requirements → 349 (2.5x multiplication)

**Evidence**:

```python
# LightRAG operate.py line 2854-2902
if entity_extract_max_gleaning > 0:
    glean_result, timestamp = await use_llm_func_with_cache(
        entity_continue_extraction_user_prompt,  # "What did you miss?"
        ...
    )
```

### Root Cause #2: LightRAG Example Contamination

**What happened**: LightRAG's hardcoded fictional examples injected into extraction prompts

**The smoking gun**:

**The smoking gun**:

```python
# LightRAG prompt.py lines 103-209
PROMPTS["entity_extraction_examples"] = [
    """<Input Text>
    while Alex clenched his jaw, the buzz of frustration dull against
    the backdrop of Taylor's authoritarian certainty...

    <Output>
    entity{tuple_delimiter}Alex{tuple_delimiter}person{tuple_delimiter}...
    entity{tuple_delimiter}Taylor{tuple_delimiter}person{tuple_delimiter}...
    entity{tuple_delimiter}Cruz{tuple_delimiter}person{tuple_delimiter}...
    """,
    # + 2 more examples with fake companies, athletes, etc.
]
```

**How it contaminates**:

```python
# LightRAG operate.py line 2766
examples = "\n".join(PROMPTS["entity_extraction_examples"])  # Always uses hardcoded examples
context_base = dict(
    entity_types=",".join(entity_types),  # YOUR ontology
    examples=examples,  # THEIR fictional examples - CONFLICT!
    language=language,
)
```

**Why this is problematic**:

1. LightRAG examples use conflicting entity types: "person", "equipment", "event"
2. Our ontology uses: "organization", "requirement", "evaluation_factor", etc.
3. LLM sees BOTH ontologies in prompt → confusion
4. LLM extracts meta-analysis about extraction process itself
5. Result: "Knowledge Graph", "Extraction Errors" contaminating real RFP data

### Root Cause #3: MinerU Discarded Content Processing

**What happened**: MinerU 2.6.4 correctly identifies discarded content (page numbers, headers, OCR artifacts), but RAG-Anything processes ALL non-text content types through GenericModalProcessor, creating contaminated entities.

**The discovery**: Amend 1 FOPR (8 pages, 6 tables) generated 270 entities instead of expected ~38:

```python
# analyze_discarded_problem.py results:
Total chunks: 19
├─ Text chunks: 1 (4,761 tokens) ✅ Expected
├─ Table chunks: 6 (avg 580 tokens) ✅ Expected
└─ Discarded chunks: 12 (4,612 tokens) ❌ NOISE

Discarded content examples:
- "1 " (page number)
- "T " (OCR glitch)
- Headers, footers, page artifacts

GenericModalProcessor LLM analysis:
"This discarded content represents a minimal textual fragment..."
→ Extracts meta-entities: "OCR Error", "PDF-to-Text Conversion",
  "Forensic Document Reconstruction", "Bounding Box"

Result: 27/270 entities (10%) are contaminated
```

**Why this is problematic**:

1. **MinerU working correctly**: 30%+ better OCR detects MORE artifacts (good!)
2. **RAG-Anything gap**: `separate_content()` sends ALL non-text types to multimodal processing
3. **No filtering mechanism**: GenericModalProcessor receives `type="discarded"` content
4. **LLM analysis**: Creates philosophical analysis of trivial artifacts
5. **Entity contamination**: 10% of extracted entities are document processing meta-concepts

**Evidence from RAG-Anything source**:

```python
# raganything/utils.py::separate_content()
def separate_content(content_list):
    for item in content_list:
        content_type = item.get("type", "text")
        if content_type == "text":
            text_parts.append(item)
        else:
            multimodal_items.append(item)  # ALL non-text (including "discarded")

    # No filtering - discarded content flows to GenericModalProcessor
```

**MinerU discarded types** (from `mineru/utils/enum_class.py`):

- `DISCARDED` - Generic artifacts
- `HEADER` - Page headers
- `FOOTER` - Page footers
- `PAGE_NUMBER` - Page numbers
- `ASIDE_TEXT` - Marginal notes
- `PAGE_FOOTNOTE` - Footer notes (not document footnotes)

---

## Fixes Applied

### Fix #1: Disable Gleaning

**File**: `.env`  
**Change**: `ENTITY_EXTRACT_MAX_GLEANING=2` → `0`

**Rationale**:

- MinerU 2.6.4's clean OCR makes gleaning unnecessary
- Single-pass extraction sufficient with 30%+ better accuracy
- Prevents multiplication of entity variations

**Expected impact**:

- 349 requirements → ~140-160 (back to baseline)
- 2,858 entities → ~1,400-1,600 (back to baseline)

### Fix #2: Disable LightRAG Examples

**File**: `src/server/initialization.py`  
**Change**: Override `PROMPTS["entity_extraction_examples"]` after LightRAG initialization

```python
# CRITICAL: Disable LightRAG's hardcoded fictional examples to prevent ontology contamination
# LightRAG always uses PROMPTS["entity_extraction_examples"] (does NOT check addon_params)
# These examples contain Alex/Taylor/Jordan with conflicting entity types (person, equipment)
# that contaminate our government contracting ontology (requirement, organization, etc.)
from lightrag.prompt import PROMPTS
PROMPTS["entity_extraction_examples"] = []  # Empty list = no examples injected
logger.info("✅ Disabled LightRAG's fictional example entities (prevents ontology contamination)")
```

**Why this is necessary**:

- ❌ LightRAG code: `examples = "\n".join(PROMPTS["entity_extraction_examples"])` - ALWAYS uses PROMPTS dict
- ❌ NO code path exists to override via `addon_params["entity_extraction_examples"]`
- ✅ Setting to `[]` makes `"\n".join([])` return empty string (valid, doesn't break extraction)
- ✅ This is the ONLY way to disable examples within LightRAG's current architecture

**Why this placement**:

- ✅ After LightRAG initialization (ensures PROMPTS dict exists)
- ✅ Before document processing (prevents contamination)
- ✅ Within intended workflow (not module-load monkey-patching)
- ✅ Preserves custom ontology and prompts (addon_params still used)

**Expected impact**:

- Zero contaminated entities (no "Knowledge Graph", "Extraction Errors", etc.)
- Cleaner extraction focused on actual RFP content
- No conflicting ontology signals to confuse LLM

### Fix #3: Filter Discarded Content Before RAG-Anything Processing

**File**: `src/server/routes.py`  
**Change**: Pre-filter MinerU output using RAG-Anything's official `insert_content_list()` API

```python
# Step 1: Parse document with MinerU
content_list, doc_id = await rag_instance.parse_document(
    file_path=file_path,
    output_dir=global_args.working_dir,
    parse_method="auto"
)

# Step 2: Filter out discarded content types
DISCARDED_TYPES = {
    "discarded", "header", "footer",
    "page_number", "aside_text", "page_footnote"
}

filtered_content = [
    item for item in content_list
    if item.get("type") not in DISCARDED_TYPES
]

# Step 3: Insert filtered content using official API
await rag_instance.insert_content_list(
    content_list=filtered_content,
    file_path=file_path,
    doc_id=doc_id
)
```

**Why this is the correct approach**:

- ✅ Uses RAG-Anything's **official** `insert_content_list()` API (documented method)
- ✅ Pre-filtering at data entry point (no contamination pathway)
- ✅ Zero code modifications to RAG-Anything or LightRAG (pure data filtering)
- ✅ Respects custom ontology and prompts (no configuration changes)
- ✅ Transparent to LightRAG extraction (same entity types, same prompts)

**Why pre-filtering works**:

1. **MinerU → content_list**: Includes discarded blocks (transparency)
2. **Filter → filtered_content**: Removes noise BEFORE processing
3. **insert_content_list()**: Official API that RAG-Anything provides for pre-parsed content
4. **separate_content()**: Only sees filtered list (no discarded items to process)
5. **GenericModalProcessor**: Only receives legitimate content (tables, images, equations)
6. **LightRAG extraction**: 100% signal, 0% noise

**Expected impact**:

- Amend 1 FOPR: 270 entities → ~38 entities (expected baseline)
- Zero "OCR Error", "Forensic Document Reconstruction" contamination
- 10% noise entities eliminated
- Cleaner knowledge graph with only RFP content

---

## Verification Plan

### Step 1: Clear Workspace

```bash
# Clear Neo4j workspace
python tools/clear_neo4j.py afcapv_adab_iss_2025
```

### Step 2: Reprocess ISS RFP

Upload 4 ISS documents via WebUI with fixes applied

### Step 3: Validate Metrics

**Target metrics** (based on November 9-10 baseline):

- Total entities: **1,400-1,600** (currently 2,858)
- Requirements: **140-160** (currently 349)
- Deliverables: **120-140** (currently 178)
- Relationships: **3,000-4,000** (currently 9,336 may be inflated)
- **Zero contamination**: No "Knowledge Graph", "Extraction Errors", fictional characters

**Quality checks**:

```bash
# Run contamination analysis
python analyze_extraction.py
```

Expected output:

- ✅ 0 contaminated entities (currently 48)
- ✅ 0 parsing artifacts
- ✅ Only government contracting terminology
- ✅ No Alex/Taylor/Jordan references

### Step 4: Baseline Comparison

Compare against `docs/BASELINE_ISS_RFP_20251109.md`:

- Run 4 metrics: 142 requirements, 1,445 entities, 2.57 avg relationships/entity
- Current contaminated: 349 requirements, 2,858 entities
- Expected post-fix: ~145 requirements, ~1,450 entities

---

## Technical Details

### Your Architecture (Confirmed Working)

1. ✅ **Custom ontology**: 17 government contracting entity types passed via `addon_params["entity_types"]`
2. ✅ **Custom prompts**: 2,605-line extraction prompt passed via `addon_params["entity_extraction_system_prompt"]`
3. ✅ **RAG-Anything integration**: Multimodal processing with MinerU parser
4. ✅ **Neo4j storage**: Workspace isolation with dual labeling
5. ⚠️ **LightRAG examples**: ALWAYS injected from `PROMPTS` dict (addon_params does NOT override)

**Critical architectural finding**: LightRAG's `extract_entities()` function pulls examples directly from `PROMPTS["entity_extraction_examples"]` - there is NO code path to override this via `addon_params`. Both your custom ontology AND LightRAG's fictional examples are injected into the same prompt, causing ontology conflict.

### What Changed in Upgrades

- **LightRAG 1.4.9.7 → 1.4.9.8**: No extraction behavior changes (metadata limits, security fixes only)
- **MinerU 2.6.3 → 2.6.4**: 30%+ OCR accuracy, better table parsing, cross-page merging
- **huggingface-hub 1.1.4 → 0.36.0**: Downgraded to fix MinerU compatibility

### Why We Didn't Notice Before

Possible theory: LightRAG examples were ALWAYS injected, but:

- Lower-quality OCR (pre-2.6.4) → less aggressive extraction
- Gleaning found fewer "new" variations in noisy text
- Contamination was present but at lower volume
- With MinerU 2.6.4 clean output + gleaning → contamination amplified

---

## Files Modified (Uncommitted)

1. `.env` - Gleaning disabled (Fix #1)
2. `src/server/initialization.py` - Examples override added (Fix #2)
3. `src/server/routes.py` - Discarded content filtering (Fix #3)
4. `src/server/config.py` - Chunk size defaults removed (earlier fix)
5. `analyze_extraction.py` - Diagnostic tool created
6. `analyze_discarded_problem.py` - Discarded content diagnostic tool

**Ready to commit after validation**

---

## Success Criteria

### Quantitative

- [ ] Entity count: 1,400-1,600 (±10% of baseline)
- [ ] Requirements: 140-160 (±10% of baseline)
- [ ] Zero contaminated entities
- [ ] Relationship density: 2.5-3.0 per entity

### Qualitative

- [ ] No meta-extraction terms
- [ ] No fictional character references
- [ ] Only government contracting terminology
- [ ] Clean Neo4j entity browser display

### Performance

- [ ] Processing time comparable to baseline (~5-10 minutes for 4 docs)
- [ ] No errors or warnings in logs
- [ ] MinerU GPU acceleration working (30-60 seconds per document)

---

## Next Steps

1. **Restart server** with fixes applied
2. **Reprocess ISS RFP** (clear workspace first)
3. **Run diagnostics** (`analyze_extraction.py`)
4. **Compare to baseline** (`BASELINE_ISS_RFP_20251109.md`)
5. **Commit fixes** if validation successful
6. **Merge to main** after final testing

---

## Open Questions

1. Were LightRAG examples ALWAYS contaminating extraction, but at lower volume?
2. Does disabling examples affect extraction quality (rely more on ontology)?
3. Should we add custom examples aligned with government contracting ontology?
4. Is there a better way to override PROMPTS within RAG-Anything architecture?

---

**Status**: Fixes applied, ready for validation reprocessing
