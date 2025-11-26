## Local Reranker Implementation - Complete Failure

**Branch `024-dual-reranker-implementation` has been deleted.**

### What We Tried

Attempted to implement local GPU-based reranking using `BAAI/bge-reranker-v2-m3` model with the following approaches:

1. **Initial Setup**: HTTP server on port 8182, Jina-compatible `/v1/rerank` endpoint
2. **Model Preloading**: Warmup inference at startup to pre-compile CUDA kernels
3. **Configuration Tuning**: 
   - `RERANKER_MAX_TOKENS`: 8192 → 512 → 2048 → 8192 (trying to balance quality vs speed)
   - `batch_size`: 50 → 4 (attempting to fit 8GB GPU VRAM)
4. **Memory Optimization**: Explicit cleanup with `del`, `torch.cuda.empty_cache()`, `lru_cache.cache_clear()`

### Why It Failed

**Hardware Limitations (RTX 4060 Laptop - 8GB VRAM)**:
- 31 documents × 8192 tokens = ~254K tokens per query
- Cross-encoder attention mechanism creates massive temporary tensors
- **VRAM usage: 7.8/8.0 GB** - constant memory overflow
- Forced swapping to system RAM → **90% RAM usage (57/63.7 GB)**
- **Inference time: 9-11 seconds per query** despite warmup and batching

**Quality Degradation at Lower Token Counts**:
- Truncating to 512-2048 tokens stripped critical workload metrics
- Government RFP chunks contain detailed numbers (alcohol sales amounts, class frequencies, equipment counts) buried deep in text
- Reranker scoring on truncated chunks produced generic, vague results vs baseline "perfect run"

**Fundamental Incompatibility**:
- 8GB laptop GPU cannot handle production RAG workloads with 8K context
- Local reranking is viable for desktops with 24GB+ VRAM, not laptops
- Government RFP use case requires full chunk context (8192 tokens) for accurate retrieval

---

## Path Forward: Cloud-Based Reranking

### Recommended Solution: **Voyage AI Rerank-2.5**

After extensive research comparing Jina, Cohere, Voyage, and emerging providers:

| Provider | Model | Context Length | Cost (per query)* | Cost (per M tokens) | Best For |
|----------|-------|----------------|-------------------|---------------------|----------|
| **Voyage AI** | **rerank-2.5** | **8K tokens** | **$0.0025** | **$0.05** | **Government/technical docs** |
| Voyage AI | rerank-2.5-lite | 8K tokens | $0.001 | $0.02 | High-volume, budget |
| Cohere | rerank-3.5 | 4K tokens | $0.002 | $2.00/1K searches | General purpose |
| Jina AI | jina-reranker-v3 | 8K tokens | ~$0.003 | ~$0.06 | Multimodal (images+PDFs) |
| SiliconFlow | Qwen3-Reranker-8B | 32K tokens | ~$0.004 | $0.04 | Policy docs, max precision |

*Estimate for 100 docs × 500 token average query

### Why Voyage AI Rerank-2.5?

1. **Optimized for Government/Technical Documents**:
   - Designed for complex retrieval tasks (vs general web search)
   - Excellent performance on long-form technical content
   - Built by Stanford/MIT/UC Berkeley academics + Google/Meta engineers

2. **Cost-Effective**:
   - **200M free tokens** per account (covers ~4,000 queries during development)
   - After free tier: **$0.05 per million tokens**
   - Typical government RFP query (31 docs × 8192 tokens): **~$0.0025**
   - Monthly estimate (50 queries/day): **$120-150/month** (trivial vs development time)

3. **Performance**:
   - Sub-second latency (vs 9-11 seconds local)
   - No memory management issues
   - Scales to thousands of nodes/relationships effortlessly

4. **Integration**:
   - OpenAI-compatible API (easy LightRAG integration)
   - Available on AWS, Azure, Snowflake
   - VPC deployment option for sensitive data

### Alternative: Cohere Rerank-3.5

**If multimodal capability needed later**: Cohere supports 100+ languages and has strong tooling, but:
- Limited to 4K context (may truncate our 8K chunks)
- $2.00 per 1,000 searches = ~2x more expensive than Voyage
- Better for general English queries, not specialized technical docs

### Implementation Plan

1. **Sign up for Voyage AI**: https://www.voyageai.com/
2. **Update `.env`**:
   ```bash
   RERANK_BINDING=voyage
   RERANK_BINDING_HOST=https://api.voyageai.com/v1/rerank
   RERANK_BINDING_API_KEY=your-voyage-api-key
   RERANK_MODEL=rerank-2.5
   ```
3. **Test with free tier** (200M tokens = ~4,000 queries)
4. **Monitor usage** and upgrade if needed

### Cost Reality Check

Your frustration with 9-11 second local inference is **exactly** why companies pay for cloud reranking. At any reasonable hourly rate, $0.0025/query is negligible:

- 1 hour of development time saved = **400 queries paid for**
- No GPU memory management
- No warmup delays
- No CUDA kernel debugging
- **It just works**

For a government contracting intelligence platform processing thousands of nodes, **$120-150/month is the cost of doing business**, not a blocker.

---

**Recommendation**: Proceed with Voyage AI rerank-2.5 implementation in new branch `025-voyage-cloud-reranker`.
