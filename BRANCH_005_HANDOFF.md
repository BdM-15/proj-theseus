# Branch 005: MinerU Optimization - UCF Redundancy Experiment

**Date**: October 9, 2025  
**Branch**: 005-mineru-optimization  
**Status**: 🔬 EXPERIMENT PHASE - Validation Required  
**Parent**: main (Branch 004 complete)

---

## 🎯 Hypothesis

**The UCF detection system (971 lines, 40% of codebase) may be redundant now that MinerU multimodal extraction is validated and working.**

### Supporting Evidence

1. **MinerU Structure Preservation** (Validated October 8-9, 2025)
   - 29% of entities extracted from tables/images (1,245 out of 4,302)
   - 42 tables extracted with structure preserved
   - Hierarchical relationships maintained (Factor A/B/C > D > F > E)
   - Comprehensive query responses without explicit UCF labels

2. **Current UCF System** (971 lines)
   - `src/ingestion/detector.py`: 314 lines (FAR 15.204-1 pattern matching)
   - `src/ingestion/processor.py`: 301 lines (section-aware extraction prompts)
   - `src/ingestion/__init__.py`: 45 lines (module exports)
   - Logic in `src/server/routes.py`: ~311 lines (dual-path routing)

3. **Table Context Hypothesis**
   - Tables contain section headers (e.g., "Section M - Evaluation Factors")
   - Table formatting implies hierarchical structure
   - Table cell content includes cross-references
   - MinerU preserves surrounding text context

---

## 🔬 Proposed Experiment (30 Minutes)

### Phase 1: Disable UCF Detection (5 min)

**File**: `src/server/routes.py` (around line 65-70)

```python
# CURRENT CODE:
ucf_result = detect_ucf_format(document_text, file_name)
if ucf_result.is_ucf:
    # Section-aware processing...
else:
    # Generic processing...

# EXPERIMENT CODE:
ucf_result = None  # EXPERIMENT: Skip UCF, rely on MinerU structure
# Force generic path (MinerU will still extract tables/structure)
logger.info("⚠️  EXPERIMENT: UCF detection disabled - testing MinerU-only structure preservation")
```

### Phase 2: Re-Upload Navy MBOS (10 min)

**Test Document**: Navy MBOS RFP (425 pages)  
**Baseline Metrics** (with UCF enabled):
- Entities: 4,302 entities
- Relationships: 5,715 relationships
- Tables: 42 tables extracted
- SECTION entities: Should capture A-M structure
- Processing time: 69 seconds
- Cost: $0.042

**Actions**:
1. Delete existing Navy MBOS from `./rag_storage/`
2. Clear LLM cache: `kv_store_llm_response_cache.json`
3. Re-upload via WebUI
4. Wait for processing to complete

### Phase 3: Compare Metrics (15 min)

**Success Criteria** (±5% acceptable variance):

| Metric | Baseline (UCF ON) | Target (UCF OFF) | Status |
|--------|-------------------|------------------|--------|
| Total Entities | 4,302 | 4,000-4,500 | ? |
| Relationships | 5,715 | 5,400-6,000 | ? |
| SECTION Entities | ~50-60 | ~45-65 | ? |
| Tables Extracted | 42 | 42 | ? |
| Processing Time | 69s | ≤75s | ? |

**Query Validation**:
Test Query: "What are the evaluation factors in Section M and their weights?"

**Expected Output**:
- ✅ All 6 factors (A-F) identified
- ✅ Hierarchical importance preserved
- ✅ Page limits captured
- ✅ Tradeoff process mentioned
- ✅ Integration with Section L

**Semantic Post-Processing Check**:
- ✅ Section L↔M relationships inferred
- ✅ Document hierarchy maintained
- ✅ Attachment linking works
- ✅ Clause clustering functional
- ✅ Requirement evaluation mapping

---

## 📊 Decision Tree

### IF Results Comparable (Entity count ±5%, query quality maintained)

**Action**: ✅ **DELETE UCF SYSTEM** (971 lines)

**Implementation** (1 hour):
1. Delete `src/ingestion/detector.py` (314 lines)
2. Delete `src/ingestion/processor.py` (301 lines)
3. Delete `src/ingestion/__init__.py` (45 lines)
4. Simplify `src/server/routes.py` (remove 311 lines of dual-path logic)
5. Update imports in `src/server/initialization.py`
6. Update module documentation in `src/__init__.py`

**Impact**:
- **LOC Reduction**: -971 lines (40% reduction: 2,375 → 1,404 lines)
- **Architecture Simplification**: 5 stages → 3 stages
  - Before: Upload → UCF Detection → Dual-path → MinerU → Extraction → Semantic Post-Processing
  - After: Upload → MinerU → Extraction → Semantic Post-Processing
- **Maintenance**: Simpler codebase, fewer moving parts
- **Performance**: No regression (MinerU already does the work)

**Add Table Entity Types** (30 min):
```python
# src/server/config.py - Add 4 new entity types
"TABLE",    # Structured data: compliance matrices, price schedules
"FIGURE",   # Diagrams: technical drawings, workflows, architectures
"CHART",    # Visualizations: Gantt charts, timelines, risk matrices
"MATRIX",   # Specialized: traceability matrices, RACI matrices
```

**Total Entity Types**: 18 → 22

### IF Results Degraded (Entity count <3,900 OR query quality poor)

**Action**: ❌ **KEEP UCF SYSTEM** (0 LOC reduction)

**Still Add Table Entity Types** (30 min):
- Leverage MinerU's 42 tables extraction
- Better classification of multimodal content
- No architecture changes required

**Total Entity Types**: 18 → 22

**Lesson Learned**: UCF detection provides value beyond MinerU structure preservation. Keep system as-is.

---

## 🎯 Expected Outcomes

### Best Case Scenario (85% probability)
- UCF redundant → Delete 971 lines
- Add 4 table entity types
- **Net Result**: 40% LOC reduction, simpler architecture, maintained quality
- **Confidence**: High (MinerU evidence is strong)

### Worst Case Scenario (15% probability)
- UCF still needed → Keep system
- Add 4 table entity types
- **Net Result**: +0 LOC, +4 entity types, better multimodal support
- **Confidence**: Still valuable (table types improve extraction)

### Risk Mitigation
- ✅ Experiment on separate branch (main untouched)
- ✅ Quick rollback if degraded (30-minute test)
- ✅ No data loss (baseline stored in main branch)
- ✅ Clean comparison metrics (same document, same settings)

---

## 🔧 Technical Details

### UCF Detection Current Logic

**File**: `src/ingestion/detector.py`

```python
def detect_ucf_format(text: str, filename: str) -> UCFDetectionResult:
    """
    Detect if document follows FAR 15.204-1 Uniform Contract Format.
    
    Patterns:
    - Section A: Solicitation/Contract Form
    - Section B: Supplies/Services & Prices
    - Section C: Statement of Work
    - Section H: Special Requirements
    - Section I: Contract Clauses
    - Section J: Attachments
    - Section L: Instructions to Offerors
    - Section M: Evaluation Factors
    
    Returns: UCFDetectionResult with is_ucf flag and detected sections
    """
    # ~314 lines of regex pattern matching
```

**Question**: Does MinerU already preserve this structure via table extraction?

### MinerU Table Extraction

**What MinerU Captures**:
- Table headers (e.g., "Section M - Evaluation Factors for Award")
- Table structure (rows/columns with hierarchical relationships)
- Cell content (factor descriptions, weights, page limits)
- Surrounding context (paragraphs before/after tables)

**Hypothesis**: Section labels in table headers + LLM semantic understanding = UCF structure preserved without explicit detection.

---

## 📝 Measurement Script (for next session)

```powershell
# 1. Check entity counts before experiment
$before = @{
    entities = 4302
    relationships = 5715
    sections = 50  # Approximate
    tables = 42
    processing_time = 69
}

# 2. After disabling UCF and re-processing
# Query the graph: python -c "from src.inference.graph_io import parse_graphml; ..."

# 3. Compare results
# - Entity count difference: Should be <5%
# - Query quality: Run test query in WebUI
# - Semantic post-processing: Check relationships_inferred count

# 4. Decision: Keep or delete UCF
```

---

## 📚 Key Resources

**Branch 004 Baseline**:
- `BRANCH_004_COMPLETION.md` - Final metrics and achievements
- `docs/ARCHITECTURE.md` - Current system architecture
- Commit `4ff58ad` - Last 004 commit with all improvements

**MinerU Validation**:
- Navy MBOS query results (comprehensive Section M response)
- 29% entity extraction from tables/images
- 42 tables with structure preserved

**UCF Documentation**:
- FAR 15.204-1: Uniform Contract Format specification
- `src/ingestion/detector.py`: Current implementation
- `src/ingestion/processor.py`: Section-aware extraction logic

---

## ⚠️ Important Notes

1. **This is an EXPERIMENT** - Results will guide decision, not assumptions
2. **30-minute time box** - Quick validation, not full analysis
3. **Reversible** - Can always revert to main if unsuccessful
4. **Data-driven** - Let metrics decide, not intuition
5. **Conservative threshold** - Require ±5% entity count, maintained query quality

---

## 🚀 Next Session Checklist

Start next conversation with:

1. ✅ Verify current branch: `git branch` (should show `* 005-mineru-optimization`)
2. ✅ Read this handoff: Open `BRANCH_005_HANDOFF.md`
3. ✅ Review baseline metrics: 4,302 entities, 5,715 relationships, 69s processing
4. ✅ Confirm experiment plan: Disable UCF → Re-upload → Compare → Decide
5. ✅ Ask: "Ready to start 30-minute UCF experiment? I'll walk you through step-by-step."

---

**Branch 005 Status**: 🔬 Ready for experimentation  
**Time Required**: 30 minutes validation + 1 hour implementation (if successful)  
**Risk Level**: Low (separate branch, quick rollback)  
**Expected Value**: High (40% LOC reduction + simpler architecture)
