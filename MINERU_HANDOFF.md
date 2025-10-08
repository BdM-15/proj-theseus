# MinerU Multimodal Setup - Session Handoff

**Date**: October 8, 2025  
**Branch**: `004-mineru-multimodal` (sub-branch of 004-code-optimization)  
**Status**: 🚧 **READY FOR TESTING** - Documentation complete, manual testing required

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

## What Needs To Happen Next

### Phase 1: Manual MinerU Testing (IMMEDIATE)

**Goal**: Verify MinerU CLI works and download models

```powershell
# 1. Activate venv
.venv\Scripts\Activate.ps1

# 2. Verify MinerU installed
mineru --version
# Expected: mineru, version 2.5.4

# 3. Create test output directory
New-Item -ItemType Directory -Force -Path ./test_mineru_output

# 4. Test MinerU on Marine Corps RFP
mineru -p "inputs/__enqueued__/M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf" `
       -o ./test_mineru_output `
       -m auto

# This will:
# - Download models (~2-5GB) to %USERPROFILE%\.cache\huggingface\
# - Parse the 245-page PDF
# - Extract tables, images, equations
# - Output JSON + extracted content to ./test_mineru_output/
```

**Expected Behavior**:

- **First run**: 10-30 minutes (model download)
- **Subsequent runs**: 2-5 minutes per 100 pages

**Success Indicators**:

- ✅ Models downloaded to `%USERPROFILE%\.cache\huggingface\hub`
- ✅ Output directory contains JSON files and extracted images
- ✅ No errors in terminal output

**Troubleshooting** (if download fails):

- Check internet connection (large files)
- May need HuggingFace token: https://huggingface.co/settings/tokens
- Add to .env: `HF_TOKEN=hf_your_token_here`

### Phase 2: RAG-Anything Integration Testing

**Goal**: Verify MinerU works within server processing

```powershell
# 1. Ensure models cached from Phase 1
Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub" | Select-Object Name
# Should show: models--opendatalab--PDF-Extract-Kit

# 2. Start server
python app.py

# 3. Upload Marine Corps RFP via WebUI
# Navigate to: http://localhost:9621/
# Click Upload → Select M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf

# 4. Monitor logs for MinerU execution
# Look for: [MinerU] log entries
# Avoid: "Error processing PDF: No module named 'PyPDF2'" (means fallback)
```

**Success Logs**:

```
INFO: [MinerU] Starting PDF parsing...
INFO: [MinerU] Loading models from cache...
INFO: [MinerU] Processing page 1/245...
INFO: [MinerU] Extracted 12 tables, 5 images
INFO: [MinerU] Parsing complete
INFO: File processed successfully: M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf
```

**Failure Logs** (still using PyPDF2):

```
ERROR: [File Extraction]Error processing PDF: No module named 'PyPDF2'
pipmaster attempting: pip install --upgrade pypdf2
```

### Phase 3: Quality Comparison

**Goal**: Compare MinerU vs PyPDF2 extraction quality

**Test Queries** (after upload completes):

```
1. "Show me all tables extracted from the RFP"
2. "What evaluation factors are in Section M?"
3. "List all deliverables with their formats"
4. "What are the technical requirements?"
```

**What to Look For**:

- **With MinerU**: Structured table data, image references, equations
- **With PyPDF2**: Plain text only, tables as unstructured lines

**Document Findings**:

- Screenshot comparison of knowledge graph (MinerU vs PyPDF2)
- Entity count comparison
- Relationship quality (especially table→requirement linkages)
- Processing time metrics

### Phase 4: Documentation & Merge

**After successful validation**:

```powershell
# 1. Update MINERU_SETUP_GUIDE.md with actual results
# 2. Add performance metrics to README.md
# 3. Commit findings

git add .
git commit -m "test: MinerU multimodal extraction validated

VALIDATION RESULTS:
- Model download time: XX minutes
- Processing time (245 pages): XX seconds
- Tables extracted: XX
- Images extracted: XX
- Entity count: XXX (vs YYY with PyPDF2)
- Quality improvement: [describe findings]

NEXT STEPS:
- Merge to 004-code-optimization
- Test on multiple RFP types
- Document best practices"

# 4. Merge back to 004-code-optimization
git checkout 004-code-optimization
git merge 004-mineru-multimodal

# 5. Eventually merge 004 → main (when fully validated)
```

---

## Key Files Reference

### Documentation

- `docs/MINERU_SETUP_GUIDE.md` - Complete troubleshooting guide
- `README.md` - Updated with architecture stack
- `.github/copilot-instructions.md` - Added MinerU to critical refs
- `MINERU_HANDOFF.md` - **THIS FILE**

### Configuration

- `.env.example` - Check if HF_TOKEN added
- `src/raganything_server.py` - Verify parser="mineru"
- `pyproject.toml` - PyPDF2 added as fallback

### Test Data

- `inputs/__enqueued__/M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf` - Marine Corps RFP (245 pages)

---

## Critical Reminders

### User Constraints

1. **Never run server** - User handles all `python app.py` operations
2. **Minimal dependencies** - "Work with what the libraries have"
3. **No code in main branch** - Only production-ready releases
4. **Always use workspace tools** - Never PowerShell for file operations

### Technical Facts

- MinerU models: One-time 2-5GB download from HuggingFace
- xAI/OpenAI models: NOT used by MinerU (separate systems)
- PyPDF2: Temporary fallback until MinerU configured
- Current results: Good with text-only, better with multimodal

### Branch Strategy

```
004-mineru-multimodal (test MinerU)
    ↓ (merge after validation)
004-code-optimization (complete feature set)
    ↓ (merge when stable)
main (production only)
```

---

## Outstanding Questions

1. **HuggingFace Authentication**: Do MinerU models require auth token?

   - Test: Try manual download without token
   - If fails: Get token from https://huggingface.co/settings/tokens

2. **Model Storage Location**: Confirm cache directory writable

   - Path: `%USERPROFILE%\.cache\huggingface\hub`
   - Test: Manual file write to directory

3. **Subprocess Environment**: Does RAG-Anything pass env vars to MinerU?

   - Check: HF_TOKEN inheritance
   - Verify: PATH includes mineru executable

4. **Performance Impact**: How much slower is MinerU vs PyPDF2?
   - Baseline: PyPDF2 processing time (unknown)
   - Target: <5 minutes per 100 pages (MinerU)

---

## Success Criteria

Before merging `004-mineru-multimodal` → `004-code-optimization`:

- [ ] MinerU CLI test succeeds (manual command)
- [ ] Models downloaded to HuggingFace cache
- [ ] Server upload shows `[MinerU]` logs (not PyPDF2 fallback)
- [ ] Tables extracted and visible in knowledge graph
- [ ] Images referenced in processed content
- [ ] Processing completes without errors
- [ ] Quality improvement over PyPDF2 documented
- [ ] Performance metrics acceptable (<10 min for 245 pages)

---

## Contact Information

**Project**: GovCon Capture Vibe  
**Repository**: https://github.com/BdM-15/govcon-capture-vibe  
**MinerU**: https://github.com/opendatalab/MinerU  
**RAG-Anything**: https://github.com/HKUDS/RAG-Anything

**Critical References**:

- MinerU GitHub issues: https://github.com/opendatalab/MinerU/issues
- HuggingFace token: https://huggingface.co/settings/tokens
- PDF-Extract-Kit models: https://huggingface.co/opendatalab/PDF-Extract-Kit

---

## Next Session Starter Prompt

```
I'm continuing work on the MinerU multimodal setup (branch 004-mineru-multimodal).

Current status:
- Branch created and documentation committed
- PyPDF2 fallback installed and working
- MinerU models NOT yet downloaded
- Ready to test manual MinerU CLI

Please review MINERU_HANDOFF.md for context, then help me:
1. Test MinerU CLI on Marine Corps RFP
2. Verify model download completes
3. Test RAG-Anything integration
4. Document quality comparison

The goal is to enable full multimodal extraction (tables, images, equations)
instead of basic text-only processing.
```

---

**End of Handoff Document**

_Generated: October 8, 2025_  
_Session Duration: ~4 hours_  
_Key Achievement: Discovered MinerU never configured, established testing path_
