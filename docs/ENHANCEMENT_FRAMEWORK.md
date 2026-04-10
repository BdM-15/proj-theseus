# Enhancement Framework: Upstream Feature Adoption Roadmap

**Date**: 2026-04-10
**Branch**: `069-simplify-dependency-management`
**Purpose**: Map newly available upstream features against our current custom code to identify simplification, deduplication, and enhancement opportunities.

---

## How to Use This Document

For each upstream library upgrade, this document lists:

1. **New Feature** — What the upstream library now provides
2. **Our Current Approach** — What custom code we wrote to solve the same problem
3. **Action** — Whether to **Replace** (remove our code), **Enhance** (layer on top), **Monitor** (wait for maturity), or **Keep** (our code still needed)
4. **Effort** — Low / Medium / High
5. **Risk** — Low / Medium / High

Work through opportunities in priority order. Each can be its own issue/branch.

---

## 1. LightRAG (1.4.9.7 → 1.4.13)

### 1.1 Entity Merge & Deduplication (v1.4.12)

| Aspect               | Detail                                                                                                                                                                        |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | `merge_entities()` API — merges duplicate entities in the knowledge graph with configurable similarity thresholds                                                             |
| **Our Current Code** | Algorithm 8 (Orphan Resolution) in `src/inference/algorithms/algo_8_orphan_resolution.py` partially handles this by connecting orphaned entities                              |
| **Action**           | **Enhance** — Use LightRAG's native merge as a pre-step before our orphan resolution. Our algo 8 handles govcon-specific semantic connections that generic merge won't catch. |
| **Effort**           | Medium                                                                                                                                                                        |
| **Risk**             | Low                                                                                                                                                                           |
| **File**             | `src/inference/algorithms/algo_8_orphan_resolution.py`                                                                                                                        |

### 1.2 Enhanced Document Status Tracking (v1.4.11)

| Aspect               | Detail                                                                                               |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | `kv_store_doc_status.json` with richer per-document metadata, status querying, and batch status APIs |
| **Our Current Code** | `DocumentQueueTracker` in `src/server/routes.py` manually tracks batch completion with timers        |
| **Action**           | **Evaluate** — Check if LightRAG's doc status can replace or simplify our `DocumentQueueTracker`     |
| **Effort**           | Medium                                                                                               |
| **Risk**             | Low                                                                                                  |
| **File**             | `src/server/routes.py`                                                                               |

### 1.3 Improved Query Routing (v1.4.10)

| Aspect               | Detail                                                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Better hybrid/naive/local/global query mode routing with configurable thresholds                                    |
| **Our Current Code** | We pass through query mode from API clients; no custom routing logic                                                |
| **Action**           | **Monitor** — No custom code to replace. Review if new routing defaults improve query quality for govcon use cases. |
| **Effort**           | Low                                                                                                                 |
| **Risk**             | Low                                                                                                                 |

### 1.4 Streaming Insert Support (v1.4.13)

| Aspect               | Detail                                                                                       |
| -------------------- | -------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Streaming document insertion with progress callbacks                                         |
| **Our Current Code** | Batch upload with `register_request_start()`/`register_request_complete()` tracking          |
| **Action**           | **Enhance** — Could provide real-time progress feedback to clients during long RFP ingestion |
| **Effort**           | Medium                                                                                       |
| **Risk**             | Low                                                                                          |

### 1.5 Graph Community Detection Improvements (v1.4.11)

| Aspect               | Detail                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Better community/cluster detection in the knowledge graph                                                                                                                             |
| **Our Current Code** | Algorithm 6 (Concept Linking) in `algo_6_concept_linking.py` uses LLM to find semantic connections between entities                                                                   |
| **Action**           | **Evaluate** — If LightRAG's community detection captures the same concept clusters our algo 6 finds, we may be able to reduce LLM calls or use communities as seed input for algo 6. |
| **Effort**           | Medium                                                                                                                                                                                |
| **Risk**             | Medium — Need to compare quality                                                                                                                                                      |
| **File**             | `src/inference/algorithms/algo_6_concept_linking.py`                                                                                                                                  |

---

## 2. RAG-Anything (1.2.8 → 1.2.10)

### 2.1 MinerU 2.0 Field Name Normalization (v1.2.10)

| Aspect               | Detail                                                                                                                              |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | `_FIELD_ALIASES` mapping in `parser.py` automatically normalizes `img_caption` → `image_caption`, `img_footnote` → `image_footnote` |
| **Our Current Code** | Any fallback field handling in `GovconMultimodalProcessor` for caption/footnote field names                                         |
| **Action**           | **Replace** — Remove any duplicate field-name normalization in our processor code. RAG-Anything now handles this.                   |
| **Effort**           | Low                                                                                                                                 |
| **Risk**             | Low                                                                                                                                 |
| **File**             | `src/processors/govcon_multimodal_processor.py`                                                                                     |

### 2.2 Custom Parser Plugin Support (v1.2.9)

| Aspect               | Detail                                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Register custom parsers via plugin API — no need to subclass or monkey-patch                                                                |
| **Our Current Code** | We use the default MinerU parser with configuration passed via `RAGAnythingConfig`                                                          |
| **Action**           | **Monitor** — Could be useful if we need custom parsing logic for specific RFP formats (scanned documents, appendices with unusual layouts) |
| **Effort**           | Low (no action now)                                                                                                                         |
| **Risk**             | Low                                                                                                                                         |

### 2.3 Circuit Breaker for API Failures (v1.2.10)

| Aspect               | Detail                                                                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Upstream Feature** | Automatic circuit breaker that stops retrying after repeated API failures                                                                                          |
| **Our Current Code** | We rely on Instructor's retry mechanism + our own error handling in `call_llm_async()`                                                                             |
| **Action**           | **Evaluate** — RAG-Anything's circuit breaker may prevent cascading failures during large batch ingestion. Check if it works alongside our Instructor retry logic. |
| **Effort**           | Low                                                                                                                                                                |
| **Risk**             | Low                                                                                                                                                                |
| **File**             | `src/utils/llm_client.py`                                                                                                                                          |

### 2.4 Batch Dry-Run (v1.2.10)

| Aspect               | Detail                                                                                                                            |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Dry-run mode that estimates cost/token usage before processing a document batch                                                   |
| **Our Current Code** | No equivalent — we process and hope for the best                                                                                  |
| **Action**           | **Enhance** — Add dry-run option to our `/documents/upload` endpoint to preview token/cost estimates before processing large RFPs |
| **Effort**           | Low                                                                                                                               |
| **Risk**             | Low                                                                                                                               |
| **File**             | `src/server/routes.py`                                                                                                            |

### 2.5 Context-Aware Processing Improvements (v1.2.9+)

| Aspect               | Detail                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Better `context_extractor` with surrounding page context for tables/images                                    |
| **Our Current Code** | `GovconMultimodalProcessor` uses context extraction for section awareness                                     |
| **Action**           | **Evaluate** — Check if upstream improvements to context extraction eliminate any of our custom context logic |
| **Effort**           | Medium                                                                                                        |
| **Risk**             | Low                                                                                                           |
| **File**             | `src/processors/govcon_multimodal_processor.py`                                                               |

---

## 3. Instructor (1.3.2 → 1.15.1)

### 3.1 xAI/Grok Streaming Support (v1.8.0+)

| Aspect               | Detail                                                                                                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | First-class xAI Grok streaming with partial response validation                                                                                                                    |
| **Our Current Code** | `call_llm_async()` in `src/utils/llm_client.py` uses non-streaming Instructor calls                                                                                                |
| **Action**           | **Enhance** — Enable streaming for long inference calls (especially algo 3/4 which process large batches). Streaming reduces perceived latency and allows early failure detection. |
| **Effort**           | Medium                                                                                                                                                                             |
| **Risk**             | Low                                                                                                                                                                                |
| **File**             | `src/utils/llm_client.py`                                                                                                                                                          |

### 3.2 Retry Tracking & Metrics (v1.10.0+)

| Aspect               | Detail                                                                               |
| -------------------- | ------------------------------------------------------------------------------------ |
| **Upstream Feature** | Built-in retry attempt tracking with `_raw_response` metadata                        |
| **Our Current Code** | We log retry attempts manually in `call_llm_async()`                                 |
| **Action**           | **Replace** — Use Instructor's built-in retry tracking instead of our manual logging |
| **Effort**           | Low                                                                                  |
| **Risk**             | Low                                                                                  |
| **File**             | `src/utils/llm_client.py`                                                            |

### 3.3 JSON Reask Fix (v1.12.0+)

| Aspect               | Detail                                                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Fixed JSON mode reask — automatically re-prompts when LLM returns invalid JSON, with smarter error messages                                                                                                          |
| **Our Current Code** | `extract_json_from_response()` in `src/utils/llm_parsing.py` does custom JSON extraction with regex fallbacks                                                                                                        |
| **Action**           | **Evaluate** — If Instructor's JSON reask handles our edge cases (markdown-wrapped JSON, partial JSON), we can simplify our custom parsing. But our `extract_json_from_response()` handles non-Instructor paths too. |
| **Effort**           | Medium                                                                                                                                                                                                               |
| **Risk**             | Medium — Need to verify it handles Grok's output quirks                                                                                                                                                              |
| **File**             | `src/utils/llm_parsing.py`                                                                                                                                                                                           |

### 3.4 Improved Pydantic Validation Error Messages (v1.14.0+)

| Aspect               | Detail                                                                                                                                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Upstream Feature** | Cleaner validation error messages sent back to LLM for reask, resulting in better self-correction                                                |
| **Our Current Code** | Our Pydantic schemas in `src/ontology/schema.py` have custom validators; error handling in `parse_with_pydantic()` in `src/utils/llm_parsing.py` |
| **Action**           | **Monitor** — This should automatically improve quality of our existing Instructor calls. No code changes needed.                                |
| **Effort**           | None                                                                                                                                             |
| **Risk**             | Low                                                                                                                                              |

### 3.5 Python 3.13 Compatibility Fix (v1.11.0+)

| Aspect               | Detail                                                         |
| -------------------- | -------------------------------------------------------------- |
| **Upstream Feature** | Full Python 3.13 compatibility with no deprecation warnings    |
| **Our Current Code** | Already on Python 3.13.7                                       |
| **Action**           | **Done** — We already benefit from this via the 1.15.1 upgrade |
| **Effort**           | None                                                           |
| **Risk**             | None                                                           |

---

## 4. OpenAI SDK (1.x → 2.31.0)

### 4.1 Structured Outputs (v2.0+)

| Aspect               | Detail                                                                                                                                                                                                                                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Upstream Feature** | Native `response_format={"type": "json_schema", ...}` support with guaranteed schema compliance                                                                                                                                                  |
| **Our Current Code** | We use Instructor on top of the OpenAI SDK for structured output extraction                                                                                                                                                                      |
| **Action**           | **Evaluate** — For code paths that don't need Instructor's retry/reask logic, native structured outputs could be simpler and faster. However, we route through xAI (Grok), not OpenAI directly — need to verify xAI supports structured outputs. |
| **Effort**           | Medium                                                                                                                                                                                                                                           |
| **Risk**             | Medium — xAI API compatibility unknown                                                                                                                                                                                                           |
| **File**             | `src/utils/llm_client.py`                                                                                                                                                                                                                        |

### 4.2 Enhanced Async Client (v2.0+)

| Aspect               | Detail                                                                                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Improved `AsyncOpenAI` client with better connection pooling, timeout handling, and HTTP/2 support                                                 |
| **Our Current Code** | We create `AsyncOpenAI` clients in `call_llm_async()`                                                                                              |
| **Action**           | **Done** — Already benefiting from this via the SDK upgrade. Consider adding connection pool tuning for better throughput during batch processing. |
| **Effort**           | Low                                                                                                                                                |
| **Risk**             | Low                                                                                                                                                |

### 4.3 Minimal Breaking Change (v2.0.0)

| Aspect               | Detail                                                                         |
| -------------------- | ------------------------------------------------------------------------------ |
| **Upstream Feature** | `ResponseFunctionToolCallOutputItem.output` type change (only breaking change) |
| **Our Current Code** | We don't use function tool call outputs directly                               |
| **Action**           | **Done** — Not applicable to our codebase                                      |
| **Effort**           | None                                                                           |
| **Risk**             | None                                                                           |

---

## 5. MinerU Upgrade Path (When 3.0 Becomes Available)

These are **future opportunities** contingent on MinerU 3.0 becoming deployable on our stack (see [MINERU_3X_INTEGRATION_ASSESSMENT.md](MINERU_3X_INTEGRATION_ASSESSMENT.md)).

### 5.1 Native Heading Detection via `text_level`

| Aspect               | Detail                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | MinerU 3.0 `content_list.json` includes `text_level` field (1=H1, 2=H2, etc.) for all text blocks                                                                                     |
| **Our Current Code** | Algorithm 5 (Document Hierarchy) in `algo_5_doc_hierarchy.py` uses LLM to infer PARENT_SECTION / CHILD_OF relationships; Algorithm 7 (Heuristic) does pattern-based section detection |
| **Action**           | **Replace (partial)** — `text_level` could replace or seed heuristic heading detection in algo 7 and reduce LLM calls in algo 5                                                       |
| **Effort**           | Medium                                                                                                                                                                                |
| **Risk**             | Low                                                                                                                                                                                   |
| **Files**            | `algo_5_doc_hierarchy.py`, `algo_7_heuristic.py`                                                                                                                                      |

### 5.2 DOCX Native Parsing

| Aspect               | Detail                                                                                       |
| -------------------- | -------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Direct DOCX parsing (no PDF conversion needed) — 10x+ speed improvement                      |
| **Our Current Code** | We only support PDF input currently                                                          |
| **Action**           | **Enhance** — Accept DOCX uploads directly. Many draft RFPs are available as Word documents. |
| **Effort**           | Low (mostly endpoint change)                                                                 |
| **Risk**             | Low                                                                                          |

### 5.3 New Content Types: code, list, chart, seal

| Aspect               | Detail                                                                                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | MinerU 3.0 recognizes code blocks, lists, charts, and seals as distinct content types                                                                   |
| **Our Current Code** | All non-image, non-table content is treated as generic "text"                                                                                           |
| **Action**           | **Enhance** — Map new content types to govcon entity types (e.g., `chart` → WORKLOAD_DATA, `list` → REQUIREMENT_LIST, `code` → TECHNICAL_SPECIFICATION) |
| **Effort**           | Medium                                                                                                                                                  |
| **Risk**             | Low                                                                                                                                                     |

### 5.4 Improved Table Parsing (In-Table Formulas/Images)

| Aspect               | Detail                                                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Tables can now contain parsed formulas and images (not just text/HTML)                                     |
| **Our Current Code** | Tables are processed as HTML via `table_body` field                                                        |
| **Action**           | **Monitor** — Most RFP tables are text-only. Revisit when we encounter RFPs with complex technical tables. |
| **Effort**           | Low                                                                                                        |
| **Risk**             | Low                                                                                                        |

### 5.5 Sliding Window for Long Documents

| Aspect               | Detail                                                                                        |
| -------------------- | --------------------------------------------------------------------------------------------- |
| **Upstream Feature** | Memory-optimized parsing with sliding window — handles 1000+ page documents without splitting |
| **Our Current Code** | No special handling for very long documents                                                   |
| **Action**           | **Enhance** — Remove any document size limits or warnings once 3.0 is available               |
| **Effort**           | Low                                                                                           |
| **Risk**             | Low                                                                                           |

---

## 6. Cross-Cutting Opportunities

### 6.1 Simplify Custom JSON Parsing Pipeline

| Component                                                   | Current State                                            | Opportunity                                                                                                                       |
| ----------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `src/utils/llm_parsing.py` — `extract_json_from_response()` | Regex-based JSON extraction with markdown fence handling | Instructor 1.15.1's improved JSON reask may eliminate most edge cases. Evaluate if we can simplify to just Instructor + fallback. |
| `src/utils/llm_client.py` — `call_llm_async()`              | Manual retry logging, error classification               | Instructor 1.15.1's retry tracking + OpenAI SDK 2.x's better error types may simplify this significantly.                         |

### 6.2 Reduce LLM Calls in Post-Processing

| Algorithm                         | Purpose                                                      | Upstream Feature That Could Reduce/Replace                                           |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Algo 1 (Instruction-Eval Linking) | Links Section L instructions to Section M evaluation factors | **None** — govcon-specific, no upstream equivalent                                   |
| Algo 2 (Eval Hierarchy)           | Builds evaluation factor hierarchy                           | **None** — govcon-specific                                                           |
| Algo 3 (Requirement-Eval)         | Maps requirements to evaluation criteria                     | **None** — govcon-specific, but LightRAG community detection could identify clusters |
| Algo 4 (Deliverable Traceability) | Links SOW deliverables to requirements                       | **None** — govcon-specific                                                           |
| Algo 5 (Document Hierarchy)       | Infers section parent-child structure                        | **MinerU 3.0 `text_level`** could provide heading hierarchy directly                 |
| Algo 6 (Concept Linking)          | Finds semantic connections between entities                  | **LightRAG community detection** could seed or replace                               |
| Algo 7 (Heuristic)                | Pattern-based section detection, attachment linking          | **MinerU 3.0 `text_level`** for headings; still needed for attachment heuristics     |
| Algo 8 (Orphan Resolution)        | Connects isolated entities                                   | **LightRAG `merge_entities()`** for duplicates; still needed for semantic orphans    |

### 6.3 Remove Redundant Error Handling

With Instructor 1.15.1 + OpenAI SDK 2.x, many of our manual error handling patterns are now handled upstream:

- JSON parsing retries → Instructor JSON reask
- Validation error formatting → Instructor Pydantic error passthrough
- Connection retry → OpenAI SDK built-in retry with backoff

---

## 7. Priority Matrix

| Priority    | Item                                                       | Effort | Impact | Risk    |
| ----------- | ---------------------------------------------------------- | ------ | ------ | ------- |
| **P0**      | MinerU 2.7.6 upgrade (safe)                                | Low    | Low    | Low     |
| **P1**      | Simplify `call_llm_async()` with Instructor retry tracking | Low    | Medium | Low     |
| **P1**      | Evaluate doc status tracking simplification                | Medium | Medium | Low     |
| **P2**      | Add batch dry-run via RAG-Anything                         | Low    | Medium | Low     |
| **P2**      | Evaluate JSON parsing simplification                       | Medium | Medium | Medium  |
| **P2**      | Evaluate community detection vs algo 6                     | Medium | Medium | Medium  |
| **P3**      | Enable xAI streaming for inference algos                   | Medium | Medium | Low     |
| **P3**      | Evaluate LightRAG merge_entities vs algo 8                 | Medium | Medium | Medium  |
| **BLOCKED** | MinerU 3.0 features (text_level, DOCX, etc.)               | —      | High   | Blocked |

---

## 8. What NOT to Remove

Some custom code serves govcon-specific purposes that no upstream library will ever provide:

1. **18 Govcon Entity Types** (`src/ontology/schema.py`) — Domain-specific ontology
2. **Algorithms 1-4** — Section L↔M mapping, requirement traceability — pure govcon logic
3. **Shipley Methodology Integration** — Capture intelligence domain knowledge
4. **GovconMultimodalProcessor** — Govcon-specific table mapping, section awareness
5. **Extraction Prompts** (`prompts/extraction/govcon_lightrag_native.txt`) — Domain-tuned extraction

These represent the core value proposition and should be maintained/enhanced, not replaced.
