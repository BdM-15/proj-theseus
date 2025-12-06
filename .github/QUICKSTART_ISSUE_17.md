# Quick Start: Implementing Issue #17

**Issue**: [#17 - Parallel Chunk Processing](https://github.com/BdM-15/govcon-capture-vibe/issues/17)  
**Next Branch Number**: 028  
**Estimated Effort**: 8-12 hours

---

## Step 1: Create Feature Branch (Manual)

```powershell
# Ensure you're on main and up-to-date
git checkout main
git pull origin main

# Create feature branch (agent will suggest this name)
git checkout -b 028-parallel-chunk-extraction
```

**Why this name?**

- `028` = Next sequential branch number (last was 027)
- `parallel-chunk-extraction` = Descriptive kebab-case from issue title
- Easy to track when this feature was developed in project lifecycle

---

## Step 2: Use Plan Agent

**In VS Code GitHub Copilot Chat:**

```
@workspace Use the plan agent to create implementation plan for Issue #17
```

**Or reference the prompt directly:**

```
@workspace /plan-feature 17
```

**The agent will:**

1. Fetch Issue #17 details automatically
2. Research `src/server/routes.py` (sequential loop on lines 200-320)
3. Research `src/extraction/json_extractor.py` (async extraction already implemented)
4. Create structured plan with:
   - Architecture analysis (why NOT use LightRAG native parallelism)
   - File changes needed (~15 lines in routes.py)
   - Test cases to add
   - Configuration updates (.env.example)
   - Acceptance criteria validation
   - Estimated effort breakdown

**Expected Output:**

```markdown
# Implementation Plan: Issue #17 - Parallel Chunk Processing

## Architecture Analysis

[Agent analyzes why keeping JsonExtractor + adding asyncio.gather]

## File Changes

1. src/server/routes.py (lines 200-320)

   - Replace sequential for loop with asyncio.gather
   - Add semaphore with MAX_ASYNC env var
   - Preserve error handling logic

2. .env.example
   - Document MAX_ASYNC usage for extraction

## Test Cases

[Agent defines tests]

## Estimated Effort: 8-12 hours

[Agent breaks down by task]
```

---

## Step 3: Review and Approve Plan

**Review the plan for:**

- ✅ Correct file locations
- ✅ Preserves existing error handling
- ✅ Uses existing MAX_ASYNC env var (no new config)
- ✅ Test coverage adequate

**If plan looks good, proceed to implementation.**

---

## Step 4: Use Implementation Agent

**In VS Code GitHub Copilot Chat:**

```
@workspace Use the implement agent to execute this plan:

[paste plan from Step 2]
```

**Or reference the prompt:**

```
@workspace /implement-feature
```

**The agent will:**

1. Write tests FIRST (TDD approach):
   - `tests/test_parallel_extraction.py` - Test semaphore concurrency
   - Mock asyncio.gather to verify parallel execution
2. Implement changes in `src/server/routes.py`:

   ```python
   # Replace sequential loop (lines 200-320)
   async def extract_with_semaphore(chunk_text, chunk_idx, semaphore):
       async with semaphore:
           return await json_extractor.extract(chunk_text, f"chunk-{chunk_idx}")

   max_parallel = int(os.getenv("MAX_ASYNC", "8"))
   semaphore = asyncio.Semaphore(max_parallel)

   tasks = [extract_with_semaphore(chunk, i, semaphore)
            for i, chunk in enumerate(chunked_texts)]
   results = await asyncio.gather(*tasks, return_exceptions=True)

   # Handle results with error checking
   for i, result in enumerate(results):
       if isinstance(result, Exception):
           logger.error(f"Chunk {i} failed: {result}")
       else:
           all_entities.extend(result.entities)
           all_relationships.extend(result.relationships)
   ```

3. Update `.env.example`:

   ```bash
   # Parallel extraction concurrency (default: 8)
   MAX_ASYNC=8
   ```

4. Run validation

---

## Step 5: Use Validation Agent

**In VS Code GitHub Copilot Chat:**

```
@workspace Use the validate agent to verify implementation
```

**Or reference the prompt:**

```
@workspace /validate-changes
```

**The agent will:**

1. Activate `.venv` (MANDATORY)
2. Run tests:
   ```powershell
   pytest tests/test_parallel_extraction.py -v
   pytest tests/test_json_extraction.py -v  # Regression test
   ```
3. Check for errors: `get_errors` tool
4. Manual validation (process real RFP):

   ```powershell
   # Start server
   python app.py

   # Upload test RFP (in another terminal)
   curl -X POST http://localhost:9621/documents/upload `
     -F "file=@inputs/uploaded/test_rfp.pdf" `
     -F "mode=auto"
   ```

5. Verify Neo4j results:
   - Open http://localhost:7474
   - Count entities: `MATCH (n) RETURN count(n)`
   - Verify quality unchanged vs sequential processing

**Expected improvements:**

- 75-87% time reduction for extraction phase
- Zero entity quality degradation
- No API rate limiting errors

---

## Step 6: Commit and Push

**Agent suggests commit message:**

```powershell
git add src/server/routes.py .env.example tests/test_parallel_extraction.py
git commit -m "feat(extraction): implement parallel chunk processing with asyncio.gather

- Add semaphore-based concurrency (8x default)
- Use existing MAX_ASYNC env var (no new config needed)
- Preserve JsonExtractor error handling and retry logic
- Expected 87% time reduction for extraction phase (24min → 3min)

Implementation:
- Replace sequential for loop in routes.py with asyncio.gather
- Add extract_with_semaphore helper function
- Handle exceptions gracefully with return_exceptions=True
- Document MAX_ASYNC in .env.example

Testing:
- Added tests/test_parallel_extraction.py for concurrency validation
- Regression tested with test_json_extraction.py
- Manual validation: 425-page MCPP RFP processed successfully

Closes #17"

git push -u origin 028-parallel-chunk-extraction
```

---

## Step 7: Create Pull Request

**Using GitHub UI or gh CLI:**

```powershell
gh pr create --title "Implement Parallel Chunk Processing (Issue #17)" `
  --body "Fixes #17

## Summary
Implements parallel chunk extraction using asyncio.gather + semaphore, reducing extraction time by ~87% (24min → 3min for 32-chunk RFP).

## Changes
- src/server/routes.py: Parallel extraction with semaphore
- .env.example: Document MAX_ASYNC usage
- tests/test_parallel_extraction.py: Concurrency validation

## Testing
- ✅ Unit tests pass
- ✅ Regression tests pass
- ✅ Manual validation: 425-page MCPP RFP (no quality degradation)
- ✅ No API rate limiting at 8x concurrency

## Performance
- Extraction time: 24min → 3min (87% reduction)
- End-to-end: 60min → 39min (35% reduction)
- API safety: ~10 RPM (well under 100 RPM limit)"
```

---

## Agent Branching Intelligence

**Yes, the agent WILL understand the branch numbering system** because:

1. **Branch strategy documented in copilot-instructions.md** (just updated):

   - Format: `{number}-{descriptive-kebab-case-name}`
   - Agent must check `git branch -a` for highest number
   - Agent creates descriptive name from issue title

2. **Plan agent includes branch creation** in every plan:

   ```markdown
   ## Branch Setup

   Next branch number: 028 (current highest: 027)
   Suggested name: 028-parallel-chunk-extraction
   Command: git checkout -b 028-parallel-chunk-extraction
   ```

3. **Context from instructions** guides agent automatically:
   - Agent sees: "Agent MUST identify next branch number"
   - Agent runs: `git branch -a | grep -E '^\s*\d+'` (or PowerShell equivalent)
   - Agent extracts: Highest number, adds 1
   - Agent suggests: `{next_number}-{kebab-case-issue-title}`

**You don't need to instruct it** - the copilot-instructions.md file now serves as the "system prompt" for all agents.

---

## Timeline Estimate

| Phase                   | Duration       | Notes                              |
| ----------------------- | -------------- | ---------------------------------- |
| Planning (Step 2)       | 15-30 min      | Agent research + plan creation     |
| Implementation (Step 4) | 4-6 hours      | TDD: tests → code → documentation  |
| Validation (Step 5)     | 2-3 hours      | Unit tests + manual RFP processing |
| PR Review               | 1-2 hours      | Code review, merge conflicts       |
| **Total**               | **8-12 hours** | Matches issue estimate             |

---

## Next Steps After This Issue

Once Issue #17 is merged:

1. **Issue #14**: Prompt compression (reduces per-chunk LLM time)
2. **Issue #18**: Chunk size increase (fewer chunks to process)
3. **Issue #25**: Shipley knowledge graph (agent-powered feature)

All following the same agent workflow!

---

**Created**: December 6, 2025  
**Status**: Ready to start
