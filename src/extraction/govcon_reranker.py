"""
Local BGE Reranker for govcon RAG queries.

Uses BAAI/bge-reranker-v2-m3 (XLM-RoBERTa cross-encoder, 8192 ctx, ~1.2 GB VRAM @ FP16)
to re-score query-chunk pairs AFTER LightRAG's vector/entity/relation triple-merge.
Improves chunk ordering before LLM context assembly — typically 15-25% NDCG@10 lift
on dense English RAG benchmarks (NVIDIA arXiv 2409.07691).

Wired via LightRAG's `rerank_model_func` extension point. Heavy ML imports are
deferred to first call so disabled mode pays zero import cost.

Module-level singleton: model loaded once on first query, reused for server lifetime.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# Singleton state — loaded lazily by _get_reranker() on first query
_reranker_instance: Any = None
_reranker_model_name: str | None = None


def _get_reranker() -> Any:
    """Lazy-load the FlagReranker singleton.

    Heavy imports (FlagEmbedding, torch) happen here, not at module import.
    Reloads if the configured model name changes between server restarts.
    """
    global _reranker_instance, _reranker_model_name
    settings = get_settings()

    if _reranker_instance is None or _reranker_model_name != settings.rerank_model:
        # Defer heavy imports until first actual use
        from FlagEmbedding import FlagReranker  # type: ignore[import-not-found]

        load_start = time.perf_counter()
        _reranker_instance = FlagReranker(
            settings.rerank_model,
            use_fp16=settings.rerank_use_fp16,
            devices=[settings.rerank_device],
        )
        _reranker_model_name = settings.rerank_model
        load_ms = (time.perf_counter() - load_start) * 1000
        logger.info(
            "✅ Loaded reranker: %s on %s (FP16=%s, cold-start=%.0fms)",
            settings.rerank_model,
            settings.rerank_device,
            settings.rerank_use_fp16,
            load_ms,
        )

    return _reranker_instance


async def govcon_rerank_func(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Rerank documents by query-chunk relevance using local BGE cross-encoder.

    Signature matches LightRAG's `rerank_model_func` contract — see
    `lightrag/rerank.py` for reference (cohere_rerank, jina_rerank).

    Args:
        query: User query string.
        documents: List of dicts; each must contain a 'content' key with the chunk text.
            Other keys are preserved.
        top_n: If set, return only the top N highest-scoring documents.
        **kwargs: Ignored (LightRAG may pass extra context).

    Returns:
        Documents sorted by 'rerank_score' descending. Each dict gets a new
        'rerank_score' field (float in [0.0, 1.0] when normalize=True).
        Documents below `min_rerank_score` are filtered out.
    """
    if not documents:
        return []

    settings = get_settings()
    reranker = _get_reranker()

    rerank_start = time.perf_counter()
    pairs = [(query, doc.get("content", "")) for doc in documents]
    scores = reranker.compute_score(pairs, normalize=True)
    # FlagReranker returns a single float for one pair, list for many — normalize
    if isinstance(scores, float):
        scores = [scores]

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    # Filter by min score, then sort descending
    min_score = settings.min_rerank_score
    filtered = [d for d in documents if d["rerank_score"] >= min_score]
    filtered.sort(key=lambda d: d["rerank_score"], reverse=True)
    n_filtered = len(documents) - len(filtered)

    elapsed_ms = (time.perf_counter() - rerank_start) * 1000
    top_score = filtered[0]["rerank_score"] if filtered else 0.0
    logger.debug(
        "Reranked %d chunks in %.0fms | top_score=%.3f | filtered_below_%.2f=%d",
        len(documents),
        elapsed_ms,
        top_score,
        min_score,
        n_filtered,
    )

    return filtered[:top_n] if top_n else filtered


def make_govcon_rerank_func() -> Any | None:
    """Factory returning the rerank function or None if disabled.

    Called once at server startup from `src/server/initialization.py`.
    Returning None lets LightRAG skip reranking entirely (zero overhead).
    """
    settings = get_settings()
    if not settings.enable_rerank:
        logger.info("⏭️ Local reranking DISABLED (ENABLE_RERANK=false)")
        return None

    logger.info(
        "🎯 Local reranker ENABLED: %s (device=%s, fp16=%s, min_score=%.2f)",
        settings.rerank_model,
        settings.rerank_device,
        settings.rerank_use_fp16,
        settings.min_rerank_score,
    )
    return govcon_rerank_func
