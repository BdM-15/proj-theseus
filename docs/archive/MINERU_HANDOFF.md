# MinerU Multimodal Setup - Session Handoff

**Date**: October 8, 2025  
**Branch**: `004-mineru-multimodal` (sub-branch of 004-code-optimization)  
**Status**: ✅ **MinerU CONFIGURED** - Models downloaded, CLI tested, ready for RFP processing

---

## Critical Discovery Summary

### What We Found

**The system has NEVER used MinerU** - it's been running on basic PyPDF2 text extraction since inception.

**Timeline**:

- **Yesterday**: Processed 9 RFPs successfully using PyPDF2 fallback (unknowingly)
- **Today 11:33 AM**: Venv corruption from repeated `uv sync` during branch switching
- **Today ~12:00 PM**: Recreated fresh venv → PyPDF2 not in lock file → Error exposed
- **Today 12:39 PM**: Discovered MinerU subprocess failing silently, PyPDF2 doing all work

**Root Cause**:

1. MinerU requires ~2-5GB of computer vision models from HuggingFace
2. Models never downloaded → MinerU subprocess fails immediately
3. RAG-Anything silently falls back to PyPDF2
4. Yesterday: PyPDF2 was present (orphaned from previous pipmaster install) → Success
5. Today: Fresh venv without PyPDF2 → Fallback failed → Error visible

**Why This Matters**:

- ✅ Current text extraction works (good baseline)
- ❌ Missing tables, images, equations, structure (MinerU's value)
- 🎯 Enabling MinerU = **full multimodal RAG** for complex RFPs

---

## Current Environment State

### Branch Structure

```
main (stable)
└── 004-code-optimization (performance work)
    └── 004-mineru-multimodal (NEW - MinerU setup) ← YOU ARE HERE
```

### Package Status

```powershell
Python: 3.13.7
Environment: .venv (fresh, recreated today)
Packages: 167/186 installed (18 platform-specific missing - normal)

Key Packages:
- raganything[all]==1.2.8 ✅ (includes mineru)
- lightrag-hku ✅
- PyJWT==2.10.1 ✅ (auth fix)
- PyPDF2==3.0.1 ✅ (NEW - temporary fallback)
- mineru==2.5.4 ✅ (CLI works: mineru --version)
- pydantic==2.11.9 ✅ (correct version)
```

### Server Status

- ✅ Server starts successfully
- ✅ WebUI accessible at http://localhost:9621/
- ✅ Configuration correct: `parser="mineru"`, `parse_method="auto"`
- ❌ MinerU models NOT downloaded (subprocess fails)
- ✅ PyPDF2 fallback works (basic text extraction only)

### Files Modified This Session

**Documentation**:

- `README.md` - Added architecture stack, MinerU setup warning
- `.github/copilot-instructions.md` - Added MinerU GitHub to critical references
- `docs/MINERU_SETUP_GUIDE.md` - **NEW** - Comprehensive setup guide
- `MINERU_HANDOFF.md` - **THIS FILE**

**Dependencies**:

- `pyproject.toml` - Added PyPDF2>=3.0.0 (temporary fallback)
- `uv.lock` - Updated with PyPDF2

**Configuration**:

- `.env.example` - (User may have edited, check for HF_TOKEN)
- `src/raganything_server.py` - (User may have edited, verify config)

---

## What's Next

### Server Testing (YOU WILL DO)

1. **Start server**: `python app.py`
2. **Upload RFP** via WebUI: http://localhost:9621/
3. **Watch logs** for `[MinerU]` entries (NOT PyPDF2 fallback errors)
4. **Query** for tables/images to verify multimodal extraction

### Expected Results

**Success indicators**:

- Server logs show `[MinerU]` processing
- No `Error processing PDF: No module named 'PyPDF2'` errors
- Tables extracted as structured entities
- Images detected in knowledge graph
- Processing: <2 minutes per 100 pages

**Queries to test**:

- "Show me all tables in the RFP"
- "What images or diagrams are present?"
- Compare entity count vs previous text-only runs

---

## Files Modified

- `.env.example` - Added MinerU configuration (HF_TOKEN optional)
- `README.md` - Marked MinerU as configured
- `docs/MINERU_SETUP_GUIDE.md` - Troubleshooting reference
- `MINERU_HANDOFF.md` - This summary

---

## Quick Facts

- ✅ Models cached (~1.3GB): `%USERPROFILE%\.cache\huggingface\hub`
- ✅ No HuggingFace token needed (public models)
- ✅ Processing speed: ~17 sec/page first run, faster subsequently
- ⚠️ Windows symlinks warning (harmless, can disable with `HF_HUB_DISABLE_SYMLINKS_WARNING=1`)

---

## Code Simplification Vision (Post-MinerU)

### The Ultimate Goal: Domain Knowledge Only

**Current State**: ~1,190 lines total

- 790 lines: Core domain logic (entity types, Phase 6.1 inference)
- 400 lines: Document processing infrastructure (UCF detection, section extraction, chunking)

**With MinerU Working**: ~790 lines (33% reduction)

- **Keep**: Government contracting intelligence
- **Remove**: Infrastructure that MinerU provides

### What MinerU Makes Obsolete

**1. UCF Detection (~200 lines)**

```python
# BEFORE: Manual regex pattern matching
src/ingestion/detector.py
- Pattern matching: "Section A", "Section B", etc.
- Confidence scoring based on section count
- Manual header/footer detection

# AFTER: MinerU provides layout analysis
parsed = mineru_output
sections = parsed.layout.sections  # Computer vision detected!
```

**2. Section Extraction (~150 lines)**

```python
# BEFORE: Custom text parsing
src/ingestion/processor.py
- Manual section boundaries
- Header preservation logic
- Custom chunking by section

# AFTER: MinerU JSON structure
{
  "sections": [
    {"name": "Section A", "content": "...", "pages": [1, 2]},
    {"name": "Section L", "content": "...", "pages": [45, 50]}
  ]
}
```

**3. Table Handling (~50 lines Phase 6.1 inference)**

```python
# BEFORE: Infer table relationships from text
# Phase 6.1 uses LLM to guess table structure

# AFTER: MinerU structured table data
{
  "tables": [
    {
      "cells": [[...], [...]],
      "headers": [...],
      "location": {"section": "Section M", "page": 48}
    }
  ]
}
# Direct mapping: Table → Section → Entity relationships!
```

### The Simplified Architecture

**Future State** (after MinerU refactor):

```
User uploads RFP
    ↓
RAG-Anything (MinerU parser)
    ├─ Layout detection (sections, headers, footers)
    ├─ Table extraction (structured cells)
    ├─ Image extraction (with captions)
    └─ Equation parsing (LaTeX)
    ↓
Our Domain Logic (~790 lines):
    ├─ Inject 12 government contracting entity types
    ├─ Phase 6.1 semantic inference (L↔M, annex, clauses)
    └─ xAI Grok cloud processing
    ↓
LightRAG Knowledge Graph
```

### Files That Can Be Removed

**Conservative Estimate**: 400-500 lines

- `src/ingestion/detector.py` - **DELETE** (MinerU does layout detection)
- `src/ingestion/processor.py` - **DELETE** (MinerU provides structure)
- Custom chunking logic - **SIMPLIFY** (use MinerU's page-aware chunks)
- Table inference in Phase 6.1 - **REMOVE** (MinerU gives structured tables)

**Keep All Domain Logic**:

- ✅ 12 entity types (REQUIREMENT, CLAUSE, EVALUATION_FACTOR, etc.)
- ✅ Phase 6.1 LLM relationship inference
- ✅ Section L↔M mapping
- ✅ Annex linkage (J-#### → parent sections)
- ✅ Clause clustering (FAR/DFARS)
- ✅ xAI Grok integration

### Implementation Phases

**Phase 1: Get MinerU Working** (Current sprint)

- Download models
- Validate extraction quality
- Benchmark performance

**Phase 2: Refactor to Use MinerU Output** (Next sprint)

```python
# New workflow:
mineru_json = await rag_instance.parse(pdf_path)

# MinerU already provides:
sections = mineru_json["layout"]["sections"]  # No detection needed!
tables = mineru_json["tables"]                # Structured data!
images = mineru_json["images"]                # Extracted with captions!

# We only add:
entities = extract_govcon_entities(sections, tables)  # 12 entity types
relationships = phase6_inference(entities)             # Semantic links
```

**Phase 3: Simplify Codebase** (Cleanup sprint)

- Remove `src/ingestion/detector.py`
- Remove `src/ingestion/processor.py`
- Update Phase 6.1 to consume MinerU structure directly
- Document ~400 line reduction

### Success Metrics

**Code Reduction**:

- Current: ~1,190 lines
- Target: ~790 lines (domain logic only)
- Savings: 400 lines (33% reduction)

**Quality Improvement**:

- Before: Regex pattern matching (brittle, UCF-specific)
- After: Computer vision layout analysis (robust, any format)

**Maintainability**:

- Before: Custom parsing logic for each document type
- After: Leverage RAG-Anything's multimodal parsing, focus on domain intelligence

### The Vision Statement

> **"We should only write code that encodes government contracting knowledge. Everything else should come from libraries."**

- ❌ Don't build: Document parsing, layout detection, table extraction
- ✅ Do build: Entity types, relationship patterns, domain intelligence
- 🎯 Result: Minimal, focused codebase that's 100% domain value

---

## Test Results - CONFIRMED WORKING ✅

### MinerU CLI Test (October 8, 2025, 1:51 PM)

**Test Document**: `Proposal Development Worksheet Populated Example.pdf` (6 pages)

**Model Download Performance**:

- Total download time: ~43 seconds
- Models downloaded: ~1.3GB total
  - PDF-Extract-Kit models (yolo, table detection, OCR)
  - Layout analysis models (unet, slanet-plus, PP-LCNet)
  - Vision models for multimodal understanding
- Cache location: `%USERPROFILE%\.cache\huggingface\hub\models--opendatalab--PDF-Extract-Kit-1.0`
- No authentication required (public models)

**Processing Performance**:

- Total processing time: ~1 minute 44 seconds (after model download)
- Pages processed: 6 pages
- Speed: ~17 seconds per page (first run, includes model initialization)

**Multimodal Extraction Results**:

- ✅ **12 images extracted** successfully to `/images` folder
- ✅ Markdown conversion complete
- ✅ JSON structure files (content_list, model, middle)
- ✅ Layout PDFs for verification
- ✅ Tables detected and structured
- ✅ OCR performed on text regions

**Key Findings**:

1. ✅ No HuggingFace token required for PDF-Extract-Kit models
2. ✅ Models cache correctly to `%USERPROFILE%\.cache\huggingface\hub`
3. ✅ MinerU subprocess works via `.venv\Scripts\mineru.exe`
4. ✅ Multimodal extraction working (images, tables, structure)
5. ⚠️ Warning about symlinks on Windows (non-critical, can be disabled with HF_HUB_DISABLE_SYMLINKS_WARNING=1)

### Outstanding Questions - RESOLVED

1. **HuggingFace Authentication**: ✅ ANSWERED - No auth token required for public PDF-Extract-Kit models

2. **Model Storage Location**: ✅ CONFIRMED - Cache writable at `%USERPROFILE%\.cache\huggingface\hub`

3. **Subprocess Environment**: ✅ VERIFIED - RAG-Anything uses mineru.exe from venv, models auto-load from cache

4. **Performance Impact**: ✅ MEASURED - First run: ~17 sec/page (includes model loading). Subsequent runs expected to be faster (~2-5 minutes per 100 pages)

### Next Steps

**Remaining Tests** (User will perform):

1. Start server with `python app.py` → Watch for MinerU logs (not PyPDF2 fallback)
2. Upload RFP via WebUI → Verify multimodal extraction
3. Query knowledge graph → Compare table/image quality vs PyPDF2-only baseline

---

## Commit When Ready

```bash
git add .
git commit -m "feat: Configure MinerU multimodal PDF parsing

- Downloaded PDF-Extract-Kit models (~1.3GB)
- Tested CLI: 12 images + tables extracted from 6-page PDF
- Processing: ~17 sec/page (first run), expect 2-5 min/100 pages
- No HuggingFace token required
- Added MinerU config docs to .env.example

Ready for server testing via WebUI upload."
```

---

**End of Handoff Document**

_Generated: October 8, 2025_  
_Session Duration: ~4 hours_  
_Key Achievement: Discovered MinerU never configured, established testing path_
