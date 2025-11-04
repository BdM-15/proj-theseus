# Neo4j Post-Processing Test Scripts

Quick validation scripts to test Neo4j semantic post-processing **without waiting 45 minutes** for full document upload.

---

## Quick Start

**Fastest test** (2 minutes):

```powershell
.venv\Scripts\Activate.ps1
python test_event_loop.py
```

**Full validation** (5 minutes):

```powershell
.venv\Scripts\Activate.ps1
python test_neo4j_quick.py
```

---

## Test Scripts

### 1. `test_event_loop.py` ⚡ FASTEST

**Purpose**: Verify the async/event loop fix works correctly

**What it tests**:

- ✅ Async LLM calls work from within event loop
- ✅ Entity type inference works without blocking
- ✅ Concurrent calls handle properly
- ✅ No more "asyncio.run() cannot be called" errors

**Runtime**: ~30 seconds

**Use when**: You want to quickly verify the event loop fix

**Example output**:

```
🔄 EVENT LOOP TEST - Simulating FastAPI Context
✅ Already in async event loop (like FastAPI)
1️⃣  Testing _call_llm_async()...
   ✅ Success: Hello
2️⃣  Testing _infer_entity_type()...
   ✅ Success: Inferred type = deliverable
3️⃣  Testing concurrent calls (stress test)...
   ✅ Success: 5 concurrent calls completed
✅ EVENT LOOP TEST PASSED!
```

---

### 2. `test_neo4j_quick.py` 🚀 RECOMMENDED

**Purpose**: Full validation of Neo4j post-processing

**What it tests**:

- ✅ Async LLM calls
- ✅ Entity type inference
- ✅ Neo4j connection and data access
- ✅ Full post-processing pipeline (if data exists)

**Runtime**: ~2-5 minutes (depending on Neo4j data size)

**Use when**: You want comprehensive validation before document upload

**Example output**:

```
🧪 QUICK NEO4J POST-PROCESSING TEST
1️⃣  Testing async LLM call...
   ✅ LLM responded: 4
2️⃣  Testing entity type inference...
   ✅ Inferred type: organization
3️⃣  Testing Neo4j connection...
   ✅ Connected to Neo4j
   ✅ Found 3754 entities, 892 relationships
4️⃣  Testing full post-processing pipeline...
   ✅ Status: success
   ✅ Entities corrected: 125
   ✅ Relationships inferred: 43
✅ ALL TESTS PASSED!
```

---

### 3. `tests/test_neo4j_postprocessing.py` 🧪 COMPREHENSIVE

**Purpose**: Full test suite with detailed reporting

**What it tests**:

- ✅ Environment variables configured
- ✅ All async functions individually
- ✅ Neo4j I/O operations
- ✅ Full pipeline integration
- ✅ Error handling and edge cases

**Runtime**: ~5-10 minutes

**Use when**: You need detailed test reports or are debugging issues

**Usage**:

```powershell
# With pytest (if installed)
pytest tests/test_neo4j_postprocessing.py -v

# Or directly
python tests/test_neo4j_postprocessing.py
```

**Example output**:

```
🧪 NEO4J SEMANTIC POST-PROCESSING TEST SUITE
📋 Environment Check:
  ✅ GRAPH_STORAGE: Neo4JStorage
  ✅ NEO4J_URI: neo4j://localhost:7687
  ✅ LLM_MODEL: grok-beta
TEST 1: Async LLM Call
  ✅ LLM Response: 4
TEST 2: Entity Type Inference
  ✅ Inferred type: organization
...
📊 TEST SUMMARY
  ✅ PASS: llm_call
  ✅ PASS: entity_inference
  ✅ PASS: neo4j_connection
  Passed: 5/5
✅ ALL TESTS PASSED
```

---

## Prerequisites

### Environment Variables

Required in `.env`:

```bash
# Neo4j
GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_WORKSPACE=mcpp_drfp_2025

# LLM
LLM_MODEL=grok-beta
LLM_BINDING_API_KEY=xai-your-key
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL_TEMPERATURE=0.1
```

### Neo4j Running

Make sure Neo4j is running:

```powershell
# Check Neo4j status
curl http://localhost:7474

# Or check in browser
# http://localhost:7474
```

### Virtual Environment

Always activate `.venv` first:

```powershell
.venv\Scripts\Activate.ps1
```

---

## What Each Test Validates

### Event Loop Fix ✅

**Before fix**:

```
ERROR: asyncio.run() cannot be called from a running event loop
```

**After fix**:

```
✅ All async calls work properly
✅ No blocking or deadlocks
✅ Concurrent calls handled correctly
```

### Entity Type Correction ✅

**Tests**:

- UNKNOWN → proper type (e.g., organization, deliverable)
- Forbidden types (event, concept) → better types
- LLM response validation
- Fallback to 'concept' on error

**Example**:

```
Input:  "US Navy" (entity_type: UNKNOWN)
Output: "organization" (validated against 17 allowed types)
```

### Relationship Inference ✅

**Tests**:

- LLM generates relationships from entity context
- JSON parsing and validation
- Entity name → Neo4j ID mapping
- Confidence scores and reasoning

**Example**:

```
Inferred: Section L --[REQUIRES]--> Technical Proposal
Confidence: 0.85
Reasoning: Section L mandates submission of Technical Proposal
```

### Neo4j Integration ✅

**Tests**:

- Connection to database
- Read entities with workspace labels
- Read relationships with metadata
- Write entity type updates
- Create inferred relationships
- Statistics aggregation

---

## Interpreting Results

### ✅ All Tests Pass

```
✅ ALL TESTS PASSED!
```

**Action**: You're ready to process documents! Restart app and upload RFP.

### ❌ LLM Call Failed

```
❌ LLM call failed: HTTPError 401
```

**Fix**: Check `LLM_BINDING_API_KEY` in `.env`

### ❌ Neo4j Connection Failed

```
❌ Neo4j connection failed: ServiceUnavailable
```

**Fix**:

1. Start Neo4j: Check http://localhost:7474
2. Verify `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `.env`
3. Check Neo4j is running: `neo4j status`

### ❌ Import Failed

```
❌ Import failed: ModuleNotFoundError
```

**Fix**:

1. Activate virtual environment: `.venv\Scripts\Activate.ps1`
2. Install dependencies: `uv sync`

---

## Typical Workflow

### Development Cycle

```powershell
# 1. Make code changes to src/inference/semantic_post_processor.py

# 2. Quick test (30 seconds)
python test_event_loop.py

# 3. If event loop test passes, full validation (2 minutes)
python test_neo4j_quick.py

# 4. If all tests pass, restart app and test with real document
python app.py
# Upload RFP via http://localhost:9621/webui
```

### Before Committing

```powershell
# Run full test suite
python tests/test_neo4j_postprocessing.py

# If all pass, commit
git add .
git commit -m "Fix: Neo4j post-processing async handling"
```

---

## Troubleshooting

### Test Hangs Forever

**Cause**: LLM API timeout or deadlock

**Fix**:

- Press Ctrl+C to stop
- Check LLM API status
- Reduce test entity count in script

### "No entities in Neo4j"

**Cause**: Database is empty or wrong workspace

**Fix**:

- Upload a document first via WebUI
- Check `NEO4J_WORKSPACE` matches in `.env`
- Query in Neo4j Browser: `MATCH (n) RETURN count(n)`

### Import Errors

**Cause**: Virtual environment not activated

**Fix**:

```powershell
.venv\Scripts\Activate.ps1
python test_neo4j_quick.py
```

---

## Next Steps After Tests Pass

1. ✅ **Restart Application**

   ```powershell
   python app.py
   ```

2. ✅ **Upload Test Document**

   - Open http://localhost:9621/webui
   - Upload small RFP (10-20 pages)
   - Watch logs for post-processing

3. ✅ **Verify in Neo4j Browser**

   ```cypher
   // Check entity types
   MATCH (n:`mcpp_drfp_2025`)
   RETURN n.entity_type, count(n)
   ORDER BY count(n) DESC

   // Check inferred relationships
   MATCH ()-[r:INFERRED_RELATIONSHIP]->()
   RETURN type(r), count(r)
   ```

4. ✅ **Full RFP Processing**
   - Upload full MCPP RFP
   - Should complete without errors
   - Post-processing runs automatically

---

## Success Criteria

✅ **test_event_loop.py** passes → Async fix working  
✅ **test_neo4j_quick.py** passes → Full pipeline working  
✅ **Document upload** completes → Production ready

**Estimated time saved**: ~45 minutes per development cycle!
