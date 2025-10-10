# Branch 004 Baseline Metrics

**Date**: October 8, 2025  
**Branch**: 004-code-optimization  
**Purpose**: Establish baseline before optimization work

---

## Static Metrics (Code Footprint)

### Lines of Code (LOC)

**Total**: 3,577 lines (src/ + app.py)

**Breakdown by file**:

```powershell
# Measurement command:
(Get-ChildItem -Recurse -File -Include *.py src/,app.py |
 ForEach-Object { (Get-Content $_.FullName).Count } |
 Measure-Object -Sum).Sum
```

**File inventory** (9 Python files):

1. `app.py` - Entry point (~60 lines)
2. `src/__init__.py` - Package marker (~5 lines)
3. `src/raganything_server.py` - Main server (~790 lines)
4. `src/llm_relationship_inference.py` - Phase 6 LLM inference (~882 lines)
5. `src/phase6_prompts.py` - Prompt templates (~519 lines)
6. `src/phase6_validation.py` - Phase 6 validation (~200 lines estimated)
7. `src/ucf_detector.py` - UCF format detection (~200 lines estimated)
8. `src/ucf_extractor.py` - UCF entity extraction (~150 lines estimated)
9. `src/ucf_section_processor.py` - Section-aware processing (~150 lines estimated)

### File Structure

```
app.py                           # ~60 lines
src/
├── __init__.py                  # ~5 lines
├── raganything_server.py        # ~790 lines
├── llm_relationship_inference.py # ~882 lines
├── phase6_prompts.py            # ~519 lines
├── phase6_validation.py         # ~200 lines
├── ucf_detector.py              # ~200 lines
├── ucf_extractor.py             # ~150 lines
└── ucf_section_processor.py     # ~150 lines
```

### Dependencies

**Core** (from pyproject.toml):

- `raganything[all]>=1.2.8` (includes lightrag-hku, MinerU, pydantic, etc.)
- `openai>=1.0.0`
- `fastapi>=0.118.0`
- `uvicorn>=0.37.0`
- `python-dotenv>=1.0.0`

**Note**: Plain Pydantic already available via raganything[all]

---

## Runtime Metrics (Performance)

### Startup Time

**Measurement**: Time from `python app.py` to "ready" log

**Command**:

```powershell
Measure-Command {
    $process = Start-Process python -ArgumentList "app.py" -PassThru -NoNewWindow
    Start-Sleep -Seconds 5  # Wait for ready log
    Stop-Process -Id $process.Id -Force
}
```

**Baseline**: TBD (needs server startup test)

### P95 Latency (Critical Endpoints)

#### /health endpoint

**Command**:

```powershell
$times = 1..10 | ForEach-Object {
    (Measure-Command { Invoke-RestMethod http://localhost:9621/health }).TotalMilliseconds
}
$p95 = ($times | Sort-Object)[-2]
Write-Host "p95 latency: $p95 ms"
```

**Baseline**: TBD (needs running server)

#### /query endpoint (representative query)

**Test query**: "List all REQUIREMENT entities with MANDATORY criticality"

**Command**:

```powershell
$times = 1..10 | ForEach-Object {
    (Measure-Command {
        Invoke-RestMethod -Method POST http://localhost:9621/query `
            -ContentType "application/json" `
            -Body '{"query":"List all REQUIREMENT entities with MANDATORY criticality","mode":"hybrid"}'
    }).TotalMilliseconds
}
$p95 = ($times | Sort-Object)[-2]
Write-Host "p95 query latency: $p95 ms"
```

**Baseline**: TBD (needs running server with processed RFP)

### Memory Usage (Steady-State RSS)

**Command**:

```powershell
# After server startup and idle for 30 seconds
Get-Process python | Select-Object WorkingSet64 | ForEach-Object {
    [math]::Round($_.WorkingSet64 / 1MB, 2)
}
```

**Baseline**: TBD (needs running server)

---

## Optimization Targets

### Code Footprint Goals

- **LOC**: 3,577 → 3,200-3,400 (target: -177 to -377 lines, 5-10% reduction)
- **File count**: 9 → 8-9 (inline if beneficial)
- **Average file size**: ~397 lines/file → maintain or reduce

### Runtime Non-Regression Constraints

- **Startup time**: ≤ baseline (no increase allowed)
- **p95 /health**: ≤ baseline (no increase allowed)
- **p95 /query**: ≤ baseline (no increase allowed)
- **Memory RSS**: ≤ baseline (no increase allowed)

### Expected Optimizations

#### 1. Dead Code Removal (-50 to -100 LOC)

- Unused imports
- Dead functions (defined but never called)
- Commented-out code blocks
- Duplicate logic

#### 2. Pydantic Validation Addition (Net: -20 to -50 LOC)

- Add BaseModel schemas for Phase 6 outputs (+50 LOC)
- Remove manual JSON parsing/validation (-70 to -100 LOC)
- **Net reduction** via consolidation

#### 3. Prompt Consolidation (-100 to -150 LOC)

- Merge duplicated prompt patterns in phase6_prompts.py
- Extract common templates
- DRY principle for similar prompts

#### 4. UCF Pipeline Simplification (-50 to -100 LOC)

- Inline small helper functions
- Merge redundant detection logic
- Reduce over-abstraction

---

## Measurement Schedule

### Before Each Change

1. Note current LOC count
2. Identify target files for change
3. Estimate expected LOC delta

### After Each Change

1. Re-count LOC
2. Verify startup time (if server-related changes)
3. Verify p95 latency (if request-handling changes)
4. Verify memory usage (if data structure changes)
5. Commit if all metrics pass, revert if regression

### Per-Iteration Metrics

Each iteration should log:

```
Iteration N: [Change Description]
- LOC delta: -XX lines
- Files changed: [file1, file2]
- Startup: unchanged / +X ms (revert if increase)
- p95 /health: unchanged / +X ms (revert if increase)
- p95 /query: unchanged / +X ms (revert if increase)
- Memory: unchanged / +X MB (revert if increase)
```

---

## Notes

### PydanticAI Decision

- **Branch 004**: Use plain Pydantic (already in dependencies) - NOT PydanticAI
- **Future branch**: PydanticAI for document generation agents (checklists, PowerPoints, reports)
- **Rationale**: See `docs/FUTURE_AGENT_ARCHITECTURE.md` for agent design

### Measurement Tooling

- Keep measurement scripts minimal and temporary
- Delete after Branch 004 completion per charter guidelines
- Favor built-in PowerShell cmdlets over new dependencies

---

**Status**: Baseline established (static metrics only)  
**Next**: Run server to capture runtime baselines  
**Then**: Begin optimization iterations
