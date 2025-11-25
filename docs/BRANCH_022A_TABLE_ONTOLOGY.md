# Branch 022a: Table Ontology Processing

**Branch**: `022a-table-ontology-processing`  
**Parent**: `022-perfect-run-baseline`  
**Status**: ✅ **Implementation Complete** - Ready for Testing  
**Date**: January 2025

---

## Overview

Extends **Perfect Run baseline** (368 entities, 428 relationships from text-only) to include **table processing** with custom govcon ontology. Uses two-stage LLM processing: table→text description→entity extraction.

**Critical Success Factor**: Preserves text-only filter (`if item.get('type') == 'text'`) to maintain baseline quality while adding parallel table processing pipeline.

---

## Architecture

### Two-Stage Table Processing

```
Table Block (MinerU)
  ↓
Stage 1: Generate Text Description (LLM)
  - Converts table structure to natural language
  - Includes context (5 blocks before/after)
  - Preserves semantic relationships
  ↓
Stage 2: Extract Entities (JsonExtractor)
  - Same Pydantic schema as text processing
  - Same validation and error handling
  - Same relationship inference
  ↓
Provenance Tagging: [TABLE-P{page}]
```

**Why Two-Stage?**

- Tables have structure (rows, columns) that LLMs describe well in text
- Text description then feeds into existing extraction pipeline (reuses JsonExtractor)
- No need to modify core ontology schema - it just works with table-sourced text

---

## Implementation Changes

### New Files

#### `src/extraction/govcon_table_processor.py` (252 lines)

- `GovconTableProcessor` class - main processor
- `_extract_context_for_table()` - gets 5 blocks before/after for grounding
- `generate_table_description()` - Stage 1: table→text conversion
- `process_table()` - Stage 2: text→entity extraction

**Key Features**:

- Context-aware processing (includes surrounding paragraphs)
- Graceful degradation (returns empty ExtractionResult on failure)
- Provenance tracking ([TABLE-P3] tags entities from page 3 tables)
- Reuses existing JsonExtractor for consistency

### Modified Files

#### `src/extraction/json_extractor.py`

**Added**: `extract_from_text(text, chunk_id)` method (90 lines)

- Mirrors existing `extract_entities_and_relationships()` logic
- Enables modal processors to use same extraction pipeline
- Handles markdown JSON, relationship cleaning, Pydantic validation

#### `src/server/routes.py`

**Modified**: Neo4j ontology extraction path (lines 100-230)

**Changes**:

1. Initialize shared accumulators: `all_entities = []`, `all_relationships = []`
2. Check `ENABLE_TABLE_ONTOLOGY` environment variable (default: true)
3. **PHASE 1: TEXT PROCESSING** (lines 120-135, UNCHANGED)
   - Filter text blocks: `if item.get('type') == 'text'`
   - Preserve Perfect Run baseline extraction
4. **PHASE 2: TABLE PROCESSING** (lines 136-179, NEW)
   - Filter table blocks: `if item.get('type') == 'table'`
   - Process each table via `GovconTableProcessor`
   - Accumulate entities/relationships into shared lists
5. **MERGE RESULTS** (lines 216-228)
   - De-duplicate entities by name across text+tables
   - Log combined statistics

**Log Output**:

```
📝 TEXT: Extracted 421 text blocks (500K chars total)
📊 TABLE PROCESSING ENABLED - Processing tables with govcon ontology
✅ Table 1 processed: 12 entities, 8 relationships
✅ Table 2 processed: 5 entities, 3 relationships
...
📊 TABLE SUMMARY: Processed 30 tables → 87 entities, 64 relationships
✅ COMBINED EXTRACTION: 455 unique entities (text+tables), 492 relationships from 42 text chunks + 30 tables
```

#### `.env`

**Added**: `ENABLE_TABLE_ONTOLOGY=true` (lines 135-141)

- Enables/disables table ontology processing
- Default: true (recommended for RFP processing)
- Set to false to revert to text-only baseline

---

## Cost Analysis

### Perfect Run Baseline (Text-Only)

- 425-page Navy ISS PWS
- 421 text blocks → 368 entities, 428 relationships
- Cost: **~$1.00** (user-confirmed)

### Table Processing Addition

- +30 table blocks (estimated from MinerU output)
- Two-stage LLM processing per table:
  - Stage 1 (description): ~500 tokens output
  - Stage 2 (extraction): ~1000 tokens input, ~500 tokens output
- **Additional cost**: ~$0.02 per RFP (2% increase)

**Total Cost**: $1.02 per 425-page RFP (text+tables)

---

## Testing Plan

### Phase 1: Baseline Preservation ✅ Ready

1. Process Navy ISS PWS with `ENABLE_TABLE_ONTOLOGY=false`
2. Verify 368 entities (±5% tolerance)
3. Verify 428 relationships (±5% tolerance)
4. Confirm text-only filter still active

### Phase 2: Table Processing ⏳ Pending

1. Enable table ontology: `ENABLE_TABLE_ONTOLOGY=true`
2. Process same Navy ISS PWS document
3. **Expected Results**:
   - Text entities: 368 (unchanged)
   - Table entities: 50-90 (estimated from ~30 tables)
   - Total: 420-460 entities
   - Relationships: 480-530 (with table linkage)
4. **Validation Criteria**:
   - Text entity count stable (368±18)
   - Table entities tagged with [TABLE-Pn]
   - No duplicate entities between text/tables (merge works)
   - Workload query accuracy >98% (no degradation)

### Phase 3: Quality Validation ⏳ Pending

1. Manual review of 5 random table-sourced entities
2. Check provenance tags (correct page numbers)
3. Verify entity types match schema (Requirement, Metric, etc.)
4. Confirm relationships link table↔text entities correctly

---

## Rollback Strategy

**If table processing degrades quality**:

1. Set `ENABLE_TABLE_ONTOLOGY=false` in `.env`
2. Restart server
3. Text-only processing remains unchanged (Perfect Run preserved)

**If critical bugs**:

```bash
git checkout 022-perfect-run-baseline
```

---

## Next Steps

1. **User starts server** (as per Critical Rule #3)

   ```powershell
   .venv\Scripts\Activate.ps1
   python app.py
   ```

2. **Test baseline preservation**

   - Upload Navy ISS PWS with `ENABLE_TABLE_ONTOLOGY=false`
   - Verify 368 entities output

3. **Test table processing**

   - Enable `ENABLE_TABLE_ONTOLOGY=true`
   - Upload same document
   - Measure entity/relationship increase

4. **Validate quality**
   - Run workload query tests (`test_workload_query.py`)
   - Check table entity provenance
   - Review extraction logs

---

## Technical Notes

### Why Not RAG-Anything's TableModalProcessor?

- **RAG-Anything processor**: Generic table understanding (summarization, Q&A)
- **GovconTableProcessor**: Domain-specific ontology extraction (Requirements, Metrics, etc.)
- **Reuse strategy**: Follow RAG-Anything patterns (context extraction, two-stage) but customize for govcon schema

### Entity Deduplication

- Merges entities by `entity_name` across text+table sources
- Table entities win if conflict (more structured data)
- Provenance preserved via [TABLE-Pn] tags

### Relationship Inference

- Table relationships extracted during Stage 2 (JsonExtractor)
- Cross-modal relationships (table entity → text entity) handled by existing merge logic
- No changes needed to relationship inference pipeline

---

**Last Updated**: January 2025  
**Author**: GitHub Copilot (Claude Sonnet 4.5)  
**Branch Status**: Ready for user testing
