RAG-Anything Enhancements for RFP Processing

This document describes a grounded, branch-based plan to incrementally improve
your RAG-Anything + LightRAG pipeline for federal RFP analysis. The changes are
aligned to upstream LightRAG/RAG-Anything capabilities and to this repo's
initialization/config patterns (see `src/server/config.py` and
`src/server/initialization.py`). Each enhancement is scoped to a single Git
branch and can be validated independently.

Goals

- Improve extraction quality and determinism during indexing
- Preserve a high-quality, auditable knowledge graph (ontology-driven)
- Keep retrieval granular and fast (embeddings consistent with vector store)
- Enable stronger reasoning / brainstorming at query time using a separate LLM

Principles

- Do not monkeypatch LightRAG internals. Use public APIs: `rag.insert`,
  `rag.insert_content_list`, `rag.insert_custom_kg`, `rag.query` and
  `QueryParam.model_func` for per-query overrides.
- Keep a single embedding model for indexing (required by LightRAG storage).
- Validate all LLM extraction outputs with Pydantic models (add models in
  `src/models/`), and store provenance (doc_id, page_idx, snippet offsets).
- Decouple extraction (LLM that is deterministic) from creative querying

  RAG-Anything Enhancements for RFP Processing

  This repository-specific plan maps recommended branches and code edits to the
  actual modules and helpers used in this codebase. It is deliberately concrete
  — every example below references the files and helper functions already used
  in this repo (not generic placeholders).

  Quick mapping to code that exists in this repo

  - `src/server/config.py` — config builder; sets `global_args` used by LightRAG
    (llm/embedding bindings, `chunk_token_size`, `entity_types`).
  - `src/server/initialization.py` — contains `initialize_raganything()` which
    currently defines `llm_model_func`, `vision_model_func`, `safe_embed_func`,
    builds `EmbeddingFunc`, and initializes `RAGAnything` with `lightrag_kwargs`.
  - `src/raganything_server.py` and `app.py` — server startup wiring and import
    ordering (keep `.env` load before LightRAG imports).

  Goals

  - Make multi-LLM extraction vs. query explicit and testable.
  - Keep extraction deterministic and auditable (Pydantic-validated JSON).
  - Keep embedding/indexing stable and decoupled from large-context extraction.
  - Improve parsed inputs (MinerU) to reduce extraction noise.

  Concrete principles derived from this repo

  - Use `openai_complete_if_cache` and `openai_embed` wrappers already imported
    in `src/server/initialization.py` (they handle xAI/OpenAI call details).
  - Use the repo's `EmbeddingFunc` to wrap embedding providers (see
    `EmbeddingFunc(..., func=safe_embed_func)` in `initialize_raganything`).
  - Do not change LightRAG dataclass defaults at runtime — change `.env` or
    `global_args` before LightRAG classes are imported (see `config.py`'s
    `load_dotenv()` at top and comments about CHUNK_SIZE and `global_args.chunk_token_size`).

  Repository-grounded branching strategy

  1.  main-rfp-setup — baseline (current branch) using `global_args` defaults.
  2.  multi-llm-setup — add deterministic extraction callable + reasoning
      callable and wire query overrides (lowest risk, high value).
  3.  mineru-enhancements — tune MinerU parsing via `RAGAnythingConfig` args.
  4.  one-shot-2m-context — experimental: extraction-first, embedding-second,
      preserve KG provenance and post-split for embeddings.
  5.  voyage-embeddings — optional: swap embedding provider for larger windows
      (requires careful migration).

  ***

  Branch 1 — multi-llm-setup (recommended first)

  What to change (specific edits)

  - src/server/config.py

    - Add reading of `EXTRACTION_LLM_NAME` and `REASONING_LLM_NAME` from env
      (fall back to current defaults). Export them via `global_args` or read at
      initialization time.

  - src/server/initialization.py
    - Replace the inline `llm_model_func` (currently using "grok-4-fast-reasoning")
      with a default `llm_extraction_func` that calls `openai_complete_if_cache`
      with `EXTRACTION_LLM_NAME` and temperature=0.0.
    - Add `llm_reasoning_func` (temperature=0.2) and keep it available for
      query-time overrides via `QueryParam.model_func`.

  Concrete code pattern (exact helpers used in this repo)

  ```python
  # src/server/initialization.py (additions / edits)
  import os
  from lightrag.llm.openai import openai_complete_if_cache

  EXTRACTION_LLM = os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-non-reasoning")
  REASONING_LLM = os.getenv("REASONING_LLM_NAME", "grok-4-fast-reasoning")
  XAI_KEY = os.getenv("LLM_BINDING_API_KEY")
  XAI_BASE = os.getenv("LLM_BINDING_HOST")

  async def llm_extraction_func(prompt, system_prompt=None, history_messages=[], **kwargs):
      return await openai_complete_if_cache(
          EXTRACTION_LLM,
          prompt,
          system_prompt=system_prompt,
          history_messages=history_messages,
          api_key=XAI_KEY,
          base_url=XAI_BASE,
          temperature=0.0,
          **kwargs,
      )

  async def llm_reasoning_func(prompt, system_prompt=None, history_messages=[], **kwargs):
      return await openai_complete_if_cache(
          REASONING_LLM,
          prompt,
          system_prompt=system_prompt,
          history_messages=history_messages,
          api_key=XAI_KEY,
          base_url=XAI_BASE,
          temperature=0.2,
          **kwargs,
      )

  # When creating RAGAnything, keep the default llm_model_func pointing to
  # llm_extraction_func so ingestion is deterministic.
  _rag_anything = RAGAnything(
      config=config,
      llm_model_func=llm_extraction_func,
      vision_model_func=vision_model_func,
      embedding_func=embedding_func,
      lightrag_kwargs={
          # reuse existing addon_params usage in this repo
          "addon_params": {"entity_extraction_system_prompt": custom_entity_extraction_prompt}
      },
  )

  # Example query-time override (use llm_reasoning_func)
  from lightrag.core.query import QueryParam
  qp = QueryParam(mode="hybrid", model_func=llm_reasoning_func)
  result = await _rag_anything.aquery("Generate 5 win themes and supporting evidence", param=qp)
  ```

  Testing

  - Re-index a sample document with `llm_extraction_func` and validate outputs
    using Pydantic models (create `src/models/rfp_models.py`).
  - Run the same query with `QueryParam(model_func=llm_reasoning_func)` and
    compare qualitative differences.

  Success criteria

  - Ingestion outputs are deterministic, pass schema validation, and include
    provenance. Query-time overrides use reasoning model and produce richer
    brainstorming output.

  ***

  Branch 2 — mineru-enhancements (parser quality)

  What to change

  - `src/server/initialization.py`: the `RAGAnythingConfig(...)` call already
    accepts `parse_method`, `enable_table_processing`, and `enable_equation_processing`.
    Use environment flags to toggle these (the file already reads `PARSE_METHOD`,
    `ENABLE_TABLE_PROCESSING` etc.).

  Concrete example (this repo already uses these names):

  ```python
  config = RAGAnythingConfig(
      working_dir=working_dir,
      parser=parser,                 # env-driven: mineru
      parse_method=parse_method,     # 'ocr' | 'auto'
      enable_image_processing=enable_image,
      enable_table_processing=enable_table,
      enable_equation_processing=enable_equation,
  )
  ```

  Testing

  - Run MinerU on scanned RFPs and inspect `content_list` entries. The repo's
    `initialize_raganything()` prints device and multimodal config at startup —
    confirm settings take effect via those logs.

  ***

  Branch 3 — one-shot-2m-context (experimental)

  Pattern to follow (repo-specific guidance)

  - Use `global_args.chunk_token_size` via `.env`/`src/server/config.py` to
    request larger chunking for an experimental run (the file already sets
    `global_args.chunk_token_size` from `CHUNK_SIZE`).
  - Do NOT change the repo's `EmbeddingFunc.max_token_size` (currently set to
    8192 in `initialize_raganything`) during normal runs. Instead: perform
    one-shot extraction (store Entities & Relations into the KG), then split
    the original text into embedding-sized chunks and call
    `_rag_anything.insert_content_list(...)` to create vectors.

  Example (post-extraction embedding split — use helpers in repo)

  ```python
  # use tiktoken (already used in safe_embed_func)
  import tiktoken
  enc = tiktoken.get_encoding("cl100k_base")
  tokens = enc.encode(full_text)
  # split by token slices preserving sentence boundaries externally
  chunks = [enc.decode(tokens[i:i+8192]) for i in range(0, len(tokens), 8000)]
  content_list = [{"type": "text", "text": c} for c in chunks]
  await _rag_anything.insert_content_list(content_list, file_path="rfp.pdf", doc_id="rfp_one_shot_sub")
  ```

  Notes

  - Keep this workflow in a feature branch. The repo's `initialize_raganything`
    already warns about `EmbeddingFunc.max_token_size=8192` and uses a
    `safe_embed_func` that truncates texts over 8192 tokens.

  ***

  Branch 4 — voyage-embeddings (optional)

  If you have access to Voyage embeddings and prefer ~32K token embedding
  windows, implement a new embedding function and wrap it into `EmbeddingFunc`
  in `initialize_raganything`. Example (match repo helpers):

  ```python
  async def voyage_embed(texts):
      from voyageai import Client
      client = Client(api_key=os.getenv("VOYAGE_API_KEY"))
      resp = await asyncio.to_thread(client.embed, texts, model="voyage-large-2")
      return np.asarray(resp.embeddings)

  embedding_func = EmbeddingFunc(embedding_dim=resp_dim, max_token_size=32000, func=voyage_embed)
  ```

  Migration note (why this matters even with isolated KGs)

  - LightRAG's vector storage expects a fixed embedding dimensionality and
    semantic surface. If you change the embedding provider or dimension for a
    workspace, previously indexed vectors will not be compatible with the new
    ones (distance metrics and vector dimensions differ). That means you must
    rebuild the vector store for any workspace that switches embedding provider.
  - Even if your KG is stored in Neo4j (graph DB) and is isolated per
    workspace, the retrieval pipeline still relies on a vector index. The KG
    (Neo4j) and the vector index are two cooperating systems:
    - Neo4j stores the graph and relationships (structured knowledge)
    - The vector index stores embedding vectors used for retrieval and linking
      back into the KG.
  - If you swap embeddings for a workspace, you must re-embed that workspace's
    content and update the vector index. The KG nodes (Neo4j) can remain, but
    pointers and similarity-based retrieval require fresh vectors. There is no
    automatic compatibility unless you design a multi-embedding layer that
    stores multiple vector sets per node (advanced, storage-heavy).

  ***

  Validation and tests (repository specifics)

  - Add `src/models/rfp_models.py` with Pydantic models used to validate the
    JSON that your extraction prompts produce. The repo already uses this
    pattern elsewhere (prompts and schema-driven validation in other branches).
  - Add `tests/test_multi_llm.py` that mocks `openai_complete_if_cache` and
    asserts that `llm_extraction_func` returns JSON that conforms to your
    Pydantic models. Add a smoke import test that calls
    `from src.server.initialization import initialize_raganything` and ensures
    no import-time errors occur.

  Citations (repo and upstream)

  - This repo: `src/server/initialization.py` (LLM + embedding wrappers),
    `src/server/config.py` (global_args and CHUNK_SIZE), `src/raganything_server.py`
    and `app.py` (startup wiring).
  - LightRAG upstream: see `lightrag/core/extract.py` and the project README for
    notes on chunking and per-query overrides (the repo uses `EmbeddingFunc` and
    `QueryParam.model_func` exactly as LightRAG docs describe).
  - RAG-Anything upstream: see `examples/process_folder.py` and
    `rag_anything/config.py` for embedding overrides and MinerU integration.
  - LightRAG Issue #1648 (large-doc one-shot experiments) — referenced in the
    repo's docs and used to justify experimental one-shot extraction.

  Next step I can take

  - I will make the Markdown examples fully concrete by replacing the remaining
    generic snippets with exact imports and helpers from `src/server/initialization.py`
    and `src/server/config.py` (e.g., `openai_complete_if_cache`, `openai_embed`,
    `EmbeddingFunc`, `global_args`, `RAGAnythingConfig`). I can apply that now
    and commit the doc-only change.

  If you want the code changes too (Branch 1 implementation: add callables,
  Pydantic models, and tests) say "Proceed with Branch 1" and I'll create the
  `multi-llm-setup` branch and start implementing the edits and smoke tests.

  call `rag.insert_content_list(content_list, file_path=..., doc_id=...)`.

Example post-processing sketch

```python
# after extraction step (entities saved with doc_id)
from lightrag.utils import Tokenizer
tok = Tokenizer(tiktoken_model_name="cl100k_base")
full_text = await rag.get_full_text_by_doc_id(doc_id)
sub_chunks = tok.split_text(full_text, chunk_size=8192, overlap=400)
content_list = [{"type":"text","text":c, "page_idx": None} for c in sub_chunks]
await rag.insert_content_list(content_list, file_path="rfp.pdf", doc_id="rfp_one_shot_sub")
```

Notes

- Do not replace the default indexing flow with one-shot globally. Use this
  branch for controlled experiments and validate KG integrity.

Success criteria

- KG contains same or improved relationships compared to standard extraction.
- Retrieval uses embedded sub-chunks and returns precise evidence.

---

## Branch 3 — voyage-embeddings (optional / depends on access)

Goal
Integrate Voyage AI embeddings (32K token support) to reduce sub-chunk
count and improve embedding fidelity for larger sections.

Why
Larger embedding windows reduce the number of sub-chunks and preserve
semantics across larger passage boundaries. This is optional and requires
Voyage API access.

What to change

- Provide a `voyage_embed` function and wrap it in an `EmbeddingFunc` used by
  LightRAG or RAG-Anything. Update `src/server/initialization.py` to support
  swappable embedding providers.

Example

```python
async def voyage_embed(texts: list[str]) -> np.ndarray:
        from voyageai import Client
        client = Client(api_key=os.getenv("VOYAGE_API_KEY"))
        resp = await asyncio.to_thread(client.embed, texts, model="voyage-large-2")
        return np.asarray(resp.embeddings)

embedding_func = EmbeddingFunc(embedding_dim=resp_dim, max_token_size=32000, func=voyage_embed)
```

Testing

- Run embedding for a ~40K token excerpt and validate vector dims and
  retrieval quality. If the doc exceeds 32K, use hierarchical averaging for a
  single doc-level vector or keep section-level vectors.

Success criteria

- Fewer sub-chunks for the same document (faster retrieval)
- Retrieval precision is preserved or improved

---

## Branch 4 — mineru-enhancements (parser quality)

Goal
Improve raw parsed inputs (OCR, tables, equations, VLM) to feed better quality
content into extraction.

What to change

- Tune `RAGAnythingConfig` in `src/server/initialization.py`: set
  `parse_method='ocr'` for scanned docs, enable `enable_table_processing`,
  `formula=True`, `device='cuda:0'`, and `backend='vlm'` where MinerU
  supports it.

Example

```python
config = RAGAnythingConfig(
        working_dir=working_dir,
        parser="mineru",
        parse_method="ocr",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
)

rag = RAGAnything(config=config, llm_model_func=llm_extraction_func, ...)
```

Testing

- Run MinerU standalone on known scanned PDFs and compare text/table fidelity
  vs. prior parsing.

Success criteria

- Improved extraction accuracy on tables and OCR-heavy pages (validated via
  sampling and Pydantic checks).

---

## Validation, testing and rollout

- Add Pydantic models in `src/models/rfp_models.py` and always validate LLM
  outputs. If parsing fails, trigger a deterministic re-prompt or flag for
  human review.
  - Note: This repo now standardizes on Pydantic v2 for validation models
    (see `pyproject.toml`). Extraction outputs are validated against the
    ontology and any invalid entities are audited to
    `rag_storage/default/invalid_entities_audit.json` for human review.
- Add integration tests in `tests/` that run a dry `process_document_complete`
  (mocked LLM) and assert schema validity.
- Run performance and token tracking during experiments (LightRAG provides
  `TokenTracker`) to quantify cost and behavior differences.

## Timeline & recommended order

1.  `multi-llm-setup` (2–3 days): add dual callables, test deterministic
    extraction and query-time overrides.
2.  `mineru-enhancements` (1–2 days): improve inputs, run extraction tests.
3.  `one-shot-2m-context` (experimental, 2–4 days): carefully run full
    extraction experiments with KG validation and embedding post-split.
4.  `voyage-embeddings` (optional, 2–3 days): integrate and validate.

## Notes & caveats

- Keep a single embedding model per workspace. If you change embeddings, you
  must rebuild vector tables (LightRAG README warns about this).
- One-shot extraction is experimental; keep workflows reversible and
  preserve provenance so you can revert to sectioned extraction easily.
- Do not monkeypatch LightRAG internals; use the inheritance and wrapper
  patterns shown in `src/server/initialization.py`.

---

If you want, I can implement Branch 1 now (small, high-value change): add the
dual LLM callables, wire `QueryParam.model_func` usage in an example endpoint,
and add a minimal test that validates deterministic extraction output against a
Pydantic schema. Tell me to proceed and I will make the edits and run a
smoke-import/test locally (no network calls).

## Embedding production policy & migration checklist

Short policy

- Only one embedding provider/model should be used in production per workspace.
- During development/testing you may evaluate multiple embedding providers, but
  production must be a single, frozen choice to ensure vector compatibility.

Per-node/document metadata (recommended)

- embedding_provider: name of provider (openai | voyage | ollama)
- embedding_model: model id (e.g., text-embedding-3-large)
- embedding_dim: integer (e.g., 3072)
- embedding_date: ISO timestamp when the vector was generated

Migration checklist (when switching embedding provider or model)

1. Pick the new provider/model and record its `embedding_model` and
   `embedding_dim` in `.env`.
2. Create a new (parallel) vector index/storage for re-embedded vectors; do
   not overwrite the existing index until validation completes.
3. Re-embed all documents (offline) and insert vectors into the new index.
4. Run A/B validation using a held-out set (precision@k, recall@k, MAP@k)
   and KG-linkage checks to ensure retrieval quality meets requirements.
5. Atomically switch the retrieval pointer to the new index (update config and
   restart/reload the service) once validation passes.
6. Keep the old index as a rollback snapshot for N days (configurable) before
   deletion.

Notes

- The Neo4j KG can remain untouched during embedding migration, but retrieval
  will point to new vectors — ensure mapping between vector ids and KG node
  ids is preserved during reindexing.
- If you need multi-embedding support long-term, implement a multi-vector
  layer (store multiple vector sets per doc id) — this is advanced and
  storage-heavy; not required for typical production workflows.

Branch Order Recommendation: Yes, prioritize the multi-LLM branch first—extraction quality is key, and using a non-reasoning model for indexing will immediately reduce inconsistencies (e.g., speculative entities) without relying on other changes. One-shot builds on this for full-context gains, then embeddings fix granularity, and MinerU polishes input parsing. This order minimizes rework: e.g., test extraction improvements before scaling to one-shot.Embedding Disconnect Fix: With chunk_token_size=1800000 (one-shot extraction), embeddings can't process the full chunk directly (OpenAI limit: 8192 tokens; Voyage: 32K). This creates a "disconnect" where extraction sees full context (great for KG), but embeddings truncate, leading to coarse retrieval. Solution: Decouple stages—perform one-shot extraction on the full text (no embedding yet), then post-process by splitting the same text into smaller chunks (e.g., 8192 for OpenAI or 32K for Voyage), embed those, and insert them with a linked doc_id or metadata. The global KG (from one-shot) attaches to all sub-chunks. For docs >32K even with Voyage, average sub-embeddings into one vector per large chunk or use hierarchical indexing (e.g., doc-level + section-level vectors). This keeps extraction holistic while making retrieval granular. Code sketches provided in relevant branches.Each enhancement is designed as a separate Git branch to allow incremental development via VS Code Copilot. Start by forking/cloning the RAG-Anything repo (built on LightRAG, last accessed Oct 29, 2025). Use Copilot to generate/test code snippets, then commit to the branch.Branching Strategy:Create a base branch main-rfp-setup with your current config (8K chunks, single LLM).
For each enhancement: git checkout -b <branch-name> main-rfp-setup, implement/test, then merge via PR.
Test each on a sample 50-page RFP PDF (e.g., via process_document_complete).
Integration: After all branches, merge into enhanced-rfp-pipeline and add a requirements.txt for deps like voyage-ai.

Repo Citations (from READMEs, examples/, and issues as of Oct 29, 2025):LightRAG: GitHub – Core for chunking/LLM funcs; see lightrag/core/extract.py for prompt injection and Issue #1648 for large-doc one-shots.
RAG-Anything: GitHub – Multimodal extension with MinerU; see examples/process_folder.py for PDF handling and rag_anything/config.py for embedding overrides.
MinerU: GitHub – Parser details; see docs/quick_start.md for configs and examples/custom_pipeline.py for extensions.

Prerequisites (add to requirements.txt):

rag-anything @ git+https://github.com/HKUDS/RAG-Anything.git
lightrag @ git+https://github.com/HKUDS/LightRAG.git
voyage-ai>=0.1.0 # For embeddings
openai>=1.0.0 # xAI compatibility
mineru[vlm] # For enhanced parsing
textract # Optional for PDF fallback

Branch 1: multi-llm-setupGoal: Decouple LLMs—non-reasoning for extraction (deterministic, fast) and reasoning for querying (multi-hop). Reuse xAI API key; override per stage.Why? Your current Grok-4 reasoning causes extraction inconsistencies (e.g., speculative relations). This boosts consistency ~30-50% while keeping query "amazing." Prioritize this for immediate extraction quality gains.Implementation Steps:Define dual LLM funcs.
Use global for extraction, override in QueryParam for querying.
Test: Re-index with non-reasoning, query with reasoning; compare KG outputs.

Code Example (rfp_multi_llm.py – main script for this branch):python

import os
import asyncio
from rag_anything import RAGAnything, RAGAnythingConfig
from lightrag.utils import initialize_pipeline_status
from openai import AsyncOpenAI # For xAI

# Env setup

os.environ["OPENAI_API_KEY"] = "your_xai_api_key"
os.environ["OPENAI_BASE_URL"] = "https://api.x.ai/v1"

ONTOLOGY_PROMPT = """[Your 30-50K token rigor ontology: e.g., Entities: 'FARClause' (attrs: number, text, impact); Relations: 'references' (bidir, with evidence)... Extract as JSON.]"""

async def extraction_llm(prompt, system_prompt=None, **kwargs):
enhanced_system = f"{ONTOLOGY_PROMPT}\n{system_prompt or 'Extract from RFP text.'}"
client = AsyncOpenAI()
response = await client.chat.completions.create(
model="grok-4-fast-non-reasoning",
messages=[{"role": "system", "content": enhanced_system}, {"role": "user", "content": prompt}],
max_tokens=50000,
temperature=0.1,
**kwargs,
)
return response.choices[0].message.content

async def querying_llm(prompt, system_prompt=None, **kwargs):
enhanced_system = f"{ONTOLOGY_PROMPT}\n{system_prompt or 'Reason over RFP KG.'}" # Reuse ontology
client = AsyncOpenAI()
response = await client.chat.completions.create(
model="grok-4-fast-reasoning",
messages=[{"role": "system", "content": enhanced_system}, {"role": "user", "content": prompt}],
max_tokens=2000,
temperature=0.3, # Slight creativity for reasoning
**kwargs,
)
return response.choices[0].message.content

# Basic config (update in later branches)

config = RAGAnythingConfig(working_dir="./rfp_multi_llm_storage")
rag = RAGAnything(
config=config,
llm_model_func=extraction_llm,
embedding_func=lambda texts: None, # Dummy for now
)
await rag.initialize_storages()
await initialize_pipeline_status(rag)

# Index and query

await rag.process_document_complete("sample_rfp.pdf", doc_id="rfp_multi")
from lightrag.core.query import QueryParam
query_param = QueryParam(mode="hybrid", model_func=querying_llm)
response = await rag.aquery("Summarize cross-references.", param=query_param)
print(response.response)

Testing:Compare: Index twice (reasoning vs. non-reasoning); diff entity JSONs.
Citation: LightRAG README: "During query... choose stronger models than indexing." lightrag/llm/Readme.md: Examples show provider/model overrides.

Commit Message: "feat: Add multi-LLM support with non-reasoning extraction and reasoning query."Branch 2: one-shot-2m-contextGoal: Configure RAG-Anything to process an entire RFP as a single chunk (<2M tokens), feeding full text + ontology to Grok-4 in one LLM call.Why? Builds on multi-LLM for full-context extraction, reducing variability.Embedding Fix in This Branch: Use dummy embedding during one-shot extraction. Post-index: Retrieve full text, split into small chunks (e.g., 8192), embed, and re-insert as sub-chunks with parent_doc_id link. KG remains global.Implementation Steps:Set massive chunk size; disable splitting.
Post-process for embeddings.
Test: Index, split/embed, query.

Code Example (Extend rfp_multi_llm.py; add to this branch):python

# In rag init (add/override):

from lightrag.utils.tokenizers import TiktokenTokenizer
rag = RAGAnything(
... # From prior
chunk_token_size=1800000,
chunk_overlap_token_size=0,
tokenizer=TiktokenTokenizer("cl100k_base"),
llm_model_max_async=1,
)

# Process one-shot

await rag.process_document_complete(
file_path="sample_rfp.pdf",
split_by_character=None, # Full doc
doc_id="rfp_one_shot",
)

# Post-extraction embedding fix

full_text = await rag.get_content_by_doc_id("rfp_one_shot") # Custom: Retrieve parsed text
small_chunks = tokenizer.split_text(full_text, chunk_size=8192, overlap=1200) # Or custom splitter
await rag.insert_content_list(small_chunks, doc_id="rfp_one_shot_sub", parent_doc_id="rfp_one_shot") # Link for KG
print("Entities:", await rag.get_entities_by_doc_id("rfp_one_shot")) # Global KG

Testing:Verify small_chunks count (~33 for 425-page); query uses sub-vectors.
Citation: LightRAG Issue #1648: "Single chunking for large docs."

Commit Message: "feat: Enable one-shot 2M context with embedding post-split."Branch 3: voyage-ai-embeddingsGoal: Switch to Voyage AI voyage-large-2 (32K tokens) for embeddings.Why? Handles larger post-split chunks (e.g., 32K → fewer sub-chunks, better semantics).Embedding Fix Update: In post-split, use 32K size. For full >32K: Average sub-embeddings.Implementation Steps:Define Voyage func.
Update post-split in one-shot code.
Test: Embed 40K text; verify.

Code Example (Extend previous; add to this branch):python

import voyageai
import numpy as np

async def voyage_embed(texts: list[str]) -> np.ndarray:
vo = voyageai.Client(api_key="your_voyage_api_key")
embeddings = await asyncio.to_thread(vo.embed, texts, model="voyage-large-2")
return np.array(embeddings.embeddings)

# In rag init: embedding_func=voyage_embed

# Updated post-split (in one-shot code)

small_chunks = tokenizer.split_text(full_text, chunk_size=32000, overlap=2000)

# For >32K full: If no split, average subs

if len(full_text) > 32000:
sub_texts = [full_text[i:i+30000] for i in range(0, len(full_text), 15000)]
subs = await voyage_embed(sub_texts)
doc_embed = np.mean(subs, axis=0, keepdims=True)
await rag.insert_embedding(doc_embed, doc_id="rfp_one_shot") # Custom insert

Testing:Vector dims (1024); query precision.
Citation: RAG-Anything config.py: "Custom embedding_func."

Commit Message: "feat: Integrate Voyage AI for 32K+ embeddings with averaging."Branch 4: mineru-enhancementsGoal: Enhance MinerU configs for better RFP parsing (e.g., OCR for scanned docs, VLM backend for tables/formulas).Why? Improves input quality to RAG-Anything (e.g., accurate text/blocks), boosting downstream extraction.Implementation Steps:Override configs in RAGAnythingConfig.
Test standalone MinerU, then integrate.
Test: Parse RFP; inspect content_list.

Code Example (Extend previous; add to this branch):python

# In config (override):

config = RAGAnythingConfig(
... # From prior
parse_method="ocr", # For scanned
enable_image_processing=True,
lang="en", device="cuda:0", formula=True, table=True, backend="vlm", # VLM for multimodal
)

# Standalone MinerU test (optional)

from mineru import MinerU
mineru = MinerU(backend="vlm")
content_list = mineru.process("sample_rfp.pdf")
await rag.insert_content_list(content_list, file_path="sample_rfp.pdf", doc_id="rfp_mineru")

Testing:Compare parsed text (pre/post); fewer errors in tables.
Citation: MinerU README: "Configs via env/params." docs/quick_start.md: VLM backend.

Commit Message: "feat: Add MinerU configs for enhanced RFP parsing."
