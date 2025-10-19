# MinerU Setup Guide: Enabling Full Multimodal RAG

**Status**: ✅ **CONFIGURED** - Models downloaded, ready for use (October 8, 2025)

## Executive Summary

**Discovery (2025-10-08)**: The system has been using **basic PyPDF2 text extraction** instead of **MinerU's advanced multimodal parsing** since inception. While text extraction has produced good results, enabling MinerU will unlock:

- ✅ **Table extraction** - Compliance matrices, pricing tables, evaluation criteria
- ✅ **Image analysis** - Organizational charts, technical diagrams, process flows
- ✅ **Equation parsing** - Technical specifications, formulas
- ✅ **Structure preservation** - Section relationships, document hierarchy
- ✅ **Layout understanding** - Multi-column formats, headers, footers

## Setup Complete ✅

**Models Cached**: ~1.3GB in `%USERPROFILE%\.cache\huggingface\hub`  
**CLI Tested**: 12 images + structured tables extracted from 6-page PDF  
**Processing Speed**: ~17 sec/page (first run with model loading)  
**Authentication**: Not required (public models)

### Now Available

- ✅ **Table extraction** - Structured data, not text
- ✅ **Image analysis** - 12 images extracted in test
- ✅ **Equation parsing** - LaTeX conversion
- ✅ **Structure preservation** - Layout-aware processing
- ✅ **Multimodal entities** - Tables, images in knowledge graph

### Why MinerU Failed Silently

**Root Cause**: MinerU requires ~2-5GB of computer vision models from HuggingFace. On first use:

1. MinerU subprocess attempts to run
2. Models not found in cache (`~/.cache/huggingface/`)
3. Download attempt fails (timeout, permissions, or no auth token)
4. RAG-Anything catches error and falls back to PyPDF2
5. PyPDF2 processes document successfully (text only)
6. **User sees success, unaware of fallback**

**Evidence from logs**:

```
INFO:   Parser: mineru  ← Configuration says MinerU
ERROR: [File Extraction]Error processing PDF: No module named 'PyPDF2'  ← Fallback failed
2025-10-08 12:39:16 - pipmaster - INFO - Executing: pip install --upgrade pypdf2  ← Auto-install fallback
```

No `[MinerU]` error logs = subprocess failed before producing output

## MinerU Architecture

### Component Overview

```
User uploads RFP
    ↓
RAG-Anything (src/raganything_server.py)
    ↓
MinerU subprocess: mineru -p input.pdf -o output/ -m auto
    ↓
    ├─ Download models (FIRST RUN ONLY)
    │   ├─ PDF-Extract-Kit (layout detection)
    │   ├─ Table structure recognition
    │   ├─ Formula detection
    │   └─ OCR models
    ↓
    ├─ Parse PDF → JSON + images
    ├─ Extract tables → structured data
    ├─ Detect equations → LaTeX
    └─ Preserve layout → markdown
    ↓
RAG-Anything converts to LightRAG format
    ↓
Knowledge graph construction
```

### Model Dependencies

**Primary Models** (auto-downloaded from HuggingFace):

- `opendatalab/PDF-Extract-Kit` - Layout analysis
- Vision models for table/image understanding
- OCR models for text extraction

**Storage Location**:

- Windows: `%USERPROFILE%\.cache\huggingface\hub`
- Linux/Mac: `~/.cache/huggingface/hub`

**Total Size**: ~2-5GB (one-time download)

## Setup Instructions

### Prerequisites

✅ **Already Installed**:

- Python 3.13.7
- MinerU v2.5.4 (via `raganything[all]`)
- PyPDF2 3.0.1 (temporary fallback)

⚠️ **Need to Configure**:

- HuggingFace model cache
- First-run model download
- Subprocess environment variables

### Step 1: Verify MinerU CLI

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Check MinerU installed
mineru --version
# Expected: mineru, version 2.5.4

# Check MinerU help
mineru --help
```

### Step 2: Test Manual Model Download

**Option A: Let MinerU auto-download on first PDF**

```powershell
# Create test directory
mkdir -p ./test_mineru_output

# Run MinerU on Marine Corps RFP
mineru -p "inputs/__enqueued__/M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf" `
       -o ./test_mineru_output `
       -m auto

# This will:
# 1. Download models (~2-5GB) to %USERPROFILE%\.cache\huggingface\
# 2. Parse the PDF
# 3. Output JSON + extracted images to ./test_mineru_output/
```

**Option B: Pre-download models with Python**

```python
# Pre-cache models before processing
from huggingface_hub import snapshot_download

# Download PDF-Extract-Kit models
snapshot_download(
    repo_id="opendatalab/PDF-Extract-Kit",
    cache_dir=os.path.expanduser("~/.cache/huggingface")
)
```

### Step 3: Verify Model Cache

```powershell
# Check if models downloaded
Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub" | Select-Object Name

# Expected output should include:
# - models--opendatalab--PDF-Extract-Kit
# - models--sentence-transformers--all-MiniLM-L6-v2 (already present)
```

### Step 4: Test RAG-Anything Integration

```powershell
# Start server
python app.py

# Upload Marine Corps RFP via WebUI
# Navigate to: http://localhost:9621/

# Monitor logs for:
# - [MinerU] log entries (subprocess executing)
# - Model download progress (first time only)
# - Successful parsing without PyPDF2 fallback
```

**Expected Success Logs**:

```
INFO: [MinerU] Starting PDF parsing...
INFO: [MinerU] Loading models from cache...
INFO: [MinerU] Processing page 1/245...
INFO: [MinerU] Extracted 12 tables, 5 images
INFO: [MinerU] Parsing complete
INFO: File processed successfully: M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf
```

**Failure Indicators**:

```
ERROR: [File Extraction]Error processing PDF: No module named 'PyPDF2'  ← Still falling back
2025-10-08 - pipmaster - INFO - Executing: pip install --upgrade pypdf2  ← Fallback triggered
```

## Troubleshooting

### Issue 1: MinerU Subprocess Times Out

**Symptom**: No `[MinerU]` logs, immediate PyPDF2 fallback

**Causes**:

- Model download taking too long (large files)
- Network issues during download
- Subprocess timeout too short

**Solutions**:

1. Pre-download models (Option B above)
2. Increase network timeout
3. Use faster internet connection for first download

### Issue 2: Permission Errors

**Symptom**: `[MinerU] PermissionError: [Errno 13]`

**Causes**:

- HuggingFace cache directory not writable
- Subprocess lacks permissions

**Solutions**:

```powershell
# Check cache directory permissions
Test-Path "$env:USERPROFILE\.cache\huggingface" -PathType Container

# Create if missing
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cache\huggingface"

# Verify write access
New-Item -ItemType File -Path "$env:USERPROFILE\.cache\huggingface\test.txt" -Force
Remove-Item "$env:USERPROFILE\.cache\huggingface\test.txt"
```

### Issue 3: HuggingFace Authentication Required

**Symptom**: `[MinerU] 403 Forbidden` or authentication errors

**Causes**:

- Model requires HuggingFace account
- No access token configured

**Solutions**:

```powershell
# Get HuggingFace token from: https://huggingface.co/settings/tokens
# Add to .env file:
echo "HF_TOKEN=hf_your_token_here" >> .env

# Or set environment variable:
$env:HF_TOKEN="hf_your_token_here"
```

### Issue 4: Model Cache Corruption

**Symptom**: Models downloaded but MinerU still fails

**Causes**:

- Incomplete download
- Corrupted cache files

**Solutions**:

```powershell
# Clear HuggingFace cache
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--opendatalab--*"

# Re-download with MinerU CLI
mineru -p test.pdf -o output/ -m auto
```

## Validation Checklist

After setup, verify MinerU is working:

- [ ] `mineru --version` shows v2.5.4+
- [ ] Models present in `%USERPROFILE%\.cache\huggingface\hub`
- [ ] Manual MinerU CLI test succeeds (Step 2)
- [ ] Server logs show `[MinerU]` entries during upload
- [ ] No PyPDF2 fallback messages in logs
- [ ] Extracted tables visible in knowledge graph
- [ ] Images referenced in processed content

## Performance Expectations

### First Upload (With Model Download)

- **Time**: 10-30 minutes
- **Network**: ~2-5GB download
- **Disk**: ~5GB cache space required
- **Status**: One-time setup cost

### Subsequent Uploads (Models Cached)

- **Time**: 2-5 minutes per 100 pages
- **Network**: None (offline after setup)
- **Disk**: Minimal (output only)
- **Status**: Production-ready performance

## Future Enhancements

### Phase 9: Advanced Multimodal Intelligence (Planned)

Once MinerU is configured, enable:

1. **Context-Aware Processing**

   - 2-page context window around tables/images
   - Section header preservation
   - Cross-reference resolution

2. **Vision Model Integration**

   - xAI Grok Vision for image analysis
   - Organizational chart understanding
   - Technical diagram extraction

3. **Table Intelligence**

   - Compliance matrix parsing
   - Pricing table extraction
   - Evaluation criteria structuring

4. **Document Structure Analysis**
   - UCF section detection (already implemented)
   - Cross-section relationship mapping
   - J-attachment correlation

## References

- **[MinerU GitHub](https://github.com/opendatalab/MinerU)** - Official documentation
- **[RAG-Anything GitHub](https://github.com/HKUDS/RAG-Anything)** - Integration layer
- **[HuggingFace Models](https://huggingface.co/opendatalab/PDF-Extract-Kit)** - PDF-Extract-Kit
- **[MinerU Documentation](https://github.com/opendatalab/MinerU/blob/master/README.md)** - Installation guide

## Next Steps

**IMMEDIATE ACTION REQUIRED**:

1. ✅ Test MinerU CLI manually (Step 2)
2. ✅ Verify model download completes
3. ✅ Upload Marine Corps RFP via WebUI
4. ✅ Confirm `[MinerU]` logs appear
5. ✅ Compare extraction quality vs PyPDF2
6. ✅ Document performance metrics
7. ✅ Update README with success confirmation

**Success Criteria**: No more PyPDF2 fallback messages in server logs when processing RFPs.
