# Issue #63: Workload Table Retrieval Gap

## Problem Statement

When querying "What's the scope of work at ADAB and what drives the workload?", the LLM returns H.1.x requirements (lavatory servicing, forecast updates, tool control) but claims **"no workload details in the context"** - despite MinerU successfully parsing 40 workload tables with full aircraft counts and monthly breakdowns.

## Verified: Data IS Properly Stored

### Graph Storage (Neo4j)

- **866 entities**, **2,150 relationships** in `swa_tas` workspace
- `table_p53`: 5,180 chars with full ADAB workload data (760 aircraft, monthly breakdowns by type)
- `Table H.2.0 Al Dhafra Aircraft Visit Schedule`: 377 chars with summary
- Graph paths exist: `Appendix H Al Dhafra Air Base (ADAB), UAE` → `table_p53` (1 hop)

### VDB Storage

- **48 chunks** (40 Table Analysis from multimodal, 8 text)
- All 40 table chunks have context-aware indicators (Document Location, Section refs, PWS references)
- Chunk `chunk-4ca139678fa5fe9bb273119a59a228b1`: 31,502 chars with full workload table HTML

### Context-Aware Processing Working

- `CONTEXT_WINDOW=2`, `CONTEXT_MODE=page`, `INCLUDE_HEADERS=true`
- 40/40 Table Analysis chunks contain: Document Location, surrounding context, Page refs, Appendix refs, PWS refs

## Root Cause: Entity Token Budget Truncation

### Query Retrieval Flow (from logs)

```
Query nodes: ADAB, site-specific requirements, Appendix H... (top_k:40)
Local query: 40 entities, 420 relations
Raw search results: 83 entities, 441 relations, 20 chunks
After truncation: 15 entities, 191 relations  ← PROBLEM HERE
Final context: 15 entities, 191 relations, 20 chunks
```

### LightRAG Default Token Budgets

```python
DEFAULT_MAX_ENTITY_TOKENS = 6000   # ~15-20 typical entities
DEFAULT_MAX_RELATION_TOKENS = 8000
DEFAULT_MAX_TOTAL_TOKENS = 30000
```

### Why `table_p53` Gets Dropped

1. `table_p53` is **5,180 chars** (~1,300 tokens) - the **largest entity**
2. With 6,000 token budget, `table_p53` alone consumes ~20% of entity budget
3. `truncate_list_by_token_size` iterates through entities and stops when budget exceeded
4. **Truncation prefers quantity over quality** - keeps 15 small H.1.x entities instead of 1 large workload table

### Secondary Issue: Semantic Keyword Gaps

Even if retrieved, entity rankings may be suboptimal:

| Entity                    | "scope of work" | "workload driver" | "aircraft counts" |
| ------------------------- | --------------- | ----------------- | ----------------- |
| `table_p53`               | ❌ MISSING      | ✅ Found          | ✅ Found          |
| `H.2.0 Estimated Monthly` | ❌ MISSING      | ❌ MISSING        | ❌ MISSING        |
| `Appendix H Al Dhafra`    | ❌ MISSING      | ❌ MISSING        | ❌ MISSING        |

Query "scope of work" has low semantic overlap with entity content.

## Attempted Fixes (Not Working)

1. **Increased `max_total_tokens` to 128,000** in WebUI → Same result (doesn't affect entity budget)
2. **Cleared LLM cache** → Same result (confirmed not cache contamination)

## Solution Options

### Option A: Increase Entity Token Budget (WebUI Parameter)

- Set `max_entity_tokens` to 20,000-24,000 in WebUI query parameters
- Set `max_relation_tokens` to 16,000
- **Risk**: Higher token cost per query
- **Benefit**: Allows large entities like `table_p53` to survive truncation

### Option B: Add Semantic Aliases to Key Entities (Post-Processing)

Enrich workload entities with query-friendly synonyms:

```python
aliases = ["scope of work", "workload summary", "monthly totals",
           "aircraft volume", "transient aircraft services"]
```

- **Risk**: Requires re-processing or entity update
- **Benefit**: Improves initial retrieval ranking

### Option C: Create Compact Workload Summary Entity

During post-processing, create "ADAB Workload Summary" (~500 chars):

- Key metrics: "760 total aircraft, C-17 (224), C-130 (271)"
- Links to detailed `table_p53`
- Query-friendly terms included
- **Risk**: Additional complexity in post-processing
- **Benefit**: Summary survives truncation, detailed data graph-reachable

## Recommended Next Step

**Test Option A first** - increase `max_entity_tokens` to 20,000 in WebUI. This is the lowest-risk immediate fix. If insufficient, implement Option B (semantic enrichment) as Algorithm 9 in post-processing.

## Key Files

- `rag_storage/swa_tas/vdb_entities.json` - Entity embeddings
- `rag_storage/swa_tas/vdb_chunks.json` - Chunk embeddings
- `.venv-clean/Lib/site-packages/lightrag/constants.py` - Default token limits
- `.venv-clean/Lib/site-packages/lightrag/operate.py` - `truncate_list_by_token_size` logic (line 3694)
- `logs/processing.log` - Query retrieval logs (lines 719-749)

## Diagnostic Tools Created

- `tools/check_graph_connectivity.py` - Neo4j path analysis
- `tools/check_vdb_content.py` - VDB entity content inspection
