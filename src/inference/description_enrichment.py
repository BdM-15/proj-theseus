"""
Entity Description Enrichment (Post-Processing)

Goal: improve query-time KG retrieval by backfilling concise, source-only entity
descriptions *after* ingestion succeeds.

Why post-processing:
- Dense chunks can contain hundreds of entities. Generating per-entity narrative
  text during extraction creates huge JSON outputs and increases timeouts.
- Post-processing can be batched, rate-limited, retried, and does not risk losing
  the entire chunk extraction.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import parse_with_pydantic

logger = logging.getLogger(__name__)


DESCRIPTION_MAX_CHARS = 400
# For batched description generation, keep evidence short and limited.
EVIDENCE_CHUNKS_PER_ENTITY = 1
EVIDENCE_CHUNK_MAX_CHARS = 450

# Batch size for the *LLM* description pass. We only use LLM for a subset of types.
# Default higher to avoid hundreds of calls on 4k entities; can be tuned via env.
DESCRIPTION_BATCH_SIZE = int(os.getenv("DESCRIPTION_BATCH_SIZE", "120"))

# Entity types that genuinely benefit from narrative descriptions for KG traversal.
# Everything else uses deterministic templates / structured fields / name-only.
LLM_DESCRIPTION_TYPES = {
    "requirement",
    "statement_of_work",
    "deliverable",
    "performance_metric",
    "strategic_theme",
    "document",
    "section",
}

# IMPORTANT (query regression note):
# LightRAG typically uses `description` heavily for entity retrieval/similarity.
# Storing raw context snippets inside `description` makes many entities look like
# near-duplicate compliance text, harming retrieval diversity and query quality.
#
# New approach:
# - Store raw snippet as `evidence_snippet` (grounding / inspection)
# - Keep `description` as a compact semantic summary for query-critical types (LLM-batched)
# - For non-critical types: use templates/name-only for stable, short descriptions
DEFAULT_SEMANTIC_LLM_TYPES = [
    "requirement",
    "deliverable",
    "evaluation_factor",
    "submission_instruction",
    "performance_metric",
    "statement_of_work",
    "strategic_theme",
]
SEMANTIC_LLM_TYPES = {
    t.strip().lower()
    for t in os.getenv("DESCRIPTION_SEMANTIC_LLM_TYPES", ",".join(DEFAULT_SEMANTIC_LLM_TYPES)).split(",")
    if t.strip()
}

# Description enrichment uses cloud Grok only (no Ollama).
DESCRIPTION_LLM_PROVIDER = (os.getenv("DESCRIPTION_LLM_PROVIDER", "") or "").strip().lower()


@dataclass(frozen=True)
class KVStores:
    entity_chunks: Dict[str, Dict[str, Any]]
    text_chunks: Dict[str, Dict[str, Any]]


class DescriptionItem(BaseModel):
    entity_name: str = Field(..., description="The entity_id / entity_name identifier")
    description: str = Field(..., description="Concise, source-only description (<=400 chars)")


class DescriptionBatch(BaseModel):
    items: List[DescriptionItem] = Field(default_factory=list)


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _clamp(text: str, max_chars: int = DESCRIPTION_MAX_CHARS) -> str:
    text = _collapse_ws(text)
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _pick_workspace_dir(rag_storage_root: str) -> Optional[Path]:
    """
    Pick the rag_storage/<workspace>/ directory containing kv_store_* files.

    Primary: env WORKSPACE
    Fallback: most recently modified directory that contains kv_store_entity_chunks.json
    """
    root = Path(rag_storage_root)
    if not root.exists():
        return None

    # Prefer explicit workspace identifiers to avoid cross-workspace contamination.
    ws = (os.getenv("WORKSPACE", "") or "").strip()
    neo_ws = (os.getenv("NEO4J_WORKSPACE", "") or "").strip()
    preferred = ws or neo_ws
    if preferred:
        cand = root / preferred
        if (cand / "kv_store_entity_chunks.json").exists() and (cand / "kv_store_text_chunks.json").exists():
            return cand
        # If a workspace was explicitly provided but kv stores are missing, do NOT fall back.
        return None

    # Fallback: scan
    candidates: List[Path] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if (child / "kv_store_entity_chunks.json").exists() and (child / "kv_store_text_chunks.json").exists():
            candidates.append(child)

    if not candidates:
        return None

    candidates.sort(key=lambda p: (p / "kv_store_entity_chunks.json").stat().st_mtime, reverse=True)
    return candidates[0]


def _load_kv_stores(rag_storage_root: str) -> Optional[KVStores]:
    ws_dir = _pick_workspace_dir(rag_storage_root)
    if ws_dir is None:
        logger.warning("Description enrichment skipped: no kv_store_* files found under rag_storage")
        return None

    ent_path = ws_dir / "kv_store_entity_chunks.json"
    txt_path = ws_dir / "kv_store_text_chunks.json"
    try:
        entity_chunks = json.loads(ent_path.read_text(encoding="utf-8"))
        text_chunks = json.loads(txt_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Description enrichment skipped: failed reading kv stores: {e}")
        return None

    if not isinstance(entity_chunks, dict) or not isinstance(text_chunks, dict):
        logger.warning("Description enrichment skipped: kv store files not dict-shaped")
        return None

    logger.info(
        f"📚 Loaded kv stores for description enrichment: entities={len(entity_chunks)}, chunks={len(text_chunks)}"
    )
    return KVStores(entity_chunks=entity_chunks, text_chunks=text_chunks)


def _score_chunk_for_entity(entity_name: str, chunk_content: str) -> int:
    """
    Score a chunk by how many times the entity name (or variants) appears.
    Higher score = better evidence chunk.
    """
    if not entity_name or not chunk_content:
        return 0
    
    name_lower = entity_name.lower()
    content_lower = chunk_content.lower()
    
    # Count exact matches
    exact_count = content_lower.count(name_lower)
    
    # Also count partial matches for multi-word entity names
    words = name_lower.split()
    partial_count = 0
    if len(words) > 1:
        # Count occurrences of significant words (>3 chars)
        for word in words:
            if len(word) > 3:
                partial_count += content_lower.count(word)
    
    # Weight exact matches higher than partial
    return exact_count * 3 + partial_count


def _extract_context_snippet(entity_name: str, chunk_content: str, snippet_chars: int = 100) -> str:
    """
    Extract a context snippet centered around the entity name mention.
    Returns ~snippet_chars of text around the first occurrence.
    """
    if not entity_name or not chunk_content:
        return ""
    
    name_lower = entity_name.lower()
    content_lower = chunk_content.lower()
    
    # Find first occurrence
    pos = content_lower.find(name_lower)
    if pos == -1:
        # Try finding significant words
        words = name_lower.split()
        for word in words:
            if len(word) > 3:
                pos = content_lower.find(word)
                if pos != -1:
                    break
    
    if pos == -1:
        # No match found, return start of chunk
        return _clamp(chunk_content, snippet_chars)
    
    # Center the snippet around the match
    half = snippet_chars // 2
    start = max(0, pos - half)
    end = min(len(chunk_content), pos + len(entity_name) + half)
    
    # Expand to word boundaries
    if start > 0:
        # Find previous space
        space_pos = chunk_content.rfind(' ', 0, start)
        if space_pos > start - 20:  # Don't go back too far
            start = space_pos + 1
    
    if end < len(chunk_content):
        # Find next space
        space_pos = chunk_content.find(' ', end)
        if space_pos != -1 and space_pos < end + 20:  # Don't go forward too far
            end = space_pos
    
    snippet = chunk_content[start:end].strip()
    
    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(chunk_content):
        snippet = snippet + "..."
    
    return snippet


def _get_entity_evidence(entity_name: str, kv: KVStores) -> Tuple[List[str], List[str]]:
    """
    Returns (chunk_ids, chunk_texts) for an entity.
    
    IMPROVED (Issue #46): Prefers best_chunk_id from enriched kv_store when available,
    rather than blindly picking the first chunk.
    """
    entry = kv.entity_chunks.get(entity_name) or {}
    chunk_ids = entry.get("chunk_ids") or []
    if not isinstance(chunk_ids, list):
        chunk_ids = []
    
    # Issue #46: Prefer enriched best_chunk_id if available
    best_chunk_id = entry.get("best_chunk_id")
    if best_chunk_id and best_chunk_id in kv.text_chunks:
        # Reorder to put best_chunk first
        if best_chunk_id in chunk_ids:
            chunk_ids = [best_chunk_id] + [cid for cid in chunk_ids if cid != best_chunk_id]
        else:
            chunk_ids = [best_chunk_id] + chunk_ids

    picked_ids: List[str] = []
    texts: List[str] = []
    for cid in chunk_ids[:EVIDENCE_CHUNKS_PER_ENTITY]:
        if cid not in kv.text_chunks:
            continue
        c = kv.text_chunks[cid]
        content = _collapse_ws(c.get("content", ""))
        if not content:
            continue
        if len(content) > EVIDENCE_CHUNK_MAX_CHARS:
            content = content[:EVIDENCE_CHUNK_MAX_CHARS].rstrip()
        picked_ids.append(cid)
        texts.append(content)

    return picked_ids, texts


def _templated_description(entity: Dict[str, Any]) -> Optional[str]:
    """
    For types where structured fields are often sufficient, generate a compact template.
    Returns None if template can't add signal beyond name.
    """
    t = (entity.get("entity_type") or "").lower().strip()
    name = _collapse_ws(entity.get("entity_name", ""))

    if not name or not t:
        return None

    if t == "clause":
        clause_number = _collapse_ws(entity.get("clause_number", "")) or name
        regulation = _collapse_ws(entity.get("regulation", ""))
        base = clause_number
        if regulation and regulation.lower() not in clause_number.lower():
            base = f"{regulation} {clause_number}"
        return _clamp(base)

    if t == "submission_instruction":
        parts = [name]
        if entity.get("volume"):
            parts.append(f"[Volume: {_collapse_ws(entity['volume'])}]")
        if entity.get("page_limit"):
            parts.append(f"[Page Limit: {_collapse_ws(entity['page_limit'])}]")
        if entity.get("format_reqs"):
            parts.append(f"[Format: {_collapse_ws(entity['format_reqs'])}]")
        out = " ".join([p for p in parts if p])
        return _clamp(out) if out and out != name else _clamp(name)

    if t == "evaluation_factor":
        parts = [name]
        if entity.get("weight"):
            parts.append(f"[Weight: {_collapse_ws(entity['weight'])}]")
        if entity.get("importance"):
            parts.append(f"[Importance: {_collapse_ws(entity['importance'])}]")
        out = " ".join([p for p in parts if p])
        return _clamp(out) if out and out != name else _clamp(name)

    if t == "performance_metric":
        parts = [name]
        if entity.get("threshold"):
            parts.append(f"[Threshold: {_collapse_ws(entity['threshold'])}]")
        if entity.get("measurement_method"):
            parts.append(f"[Method: {_collapse_ws(entity['measurement_method'])}]")
        out = " ".join([p for p in parts if p])
        return _clamp(out) if out else _clamp(name)

    if t == "requirement":
        parts = [name]
        if entity.get("criticality"):
            parts.append(f"[Criticality: {_collapse_ws(entity['criticality'])}]")
        if entity.get("modal_verb"):
            parts.append(f"[Modal: {_collapse_ws(entity['modal_verb'])}]")
        if entity.get("req_type"):
            parts.append(f"[Type: {_collapse_ws(entity['req_type'])}]")
        out = " ".join([p for p in parts if p])
        # NOTE: requirements often benefit from narrative; template is a fallback,
        # but the main path uses LLM for richer signal.
        return _clamp(out) if out else _clamp(name)

    if t in {"organization", "person", "location", "technology", "program", "equipment", "concept", "event"}:
        # Name-only is usually sufficient; narrative is rarely worth the cost.
        return _clamp(name)

    return None


async def _llm_description(entity: Dict[str, Any], evidence: List[str], model: str, temperature: float) -> str:
    """
    LLM-based description for entity types that benefit from narrative context.
    Output: 1–3 sentences, source-only, <=400 chars.
    """
    name = _collapse_ws(entity.get("entity_name", ""))
    t = _collapse_ws(entity.get("entity_type", ""))

    # Include a few typed fields if present (helps anchor the description)
    typed_bits = []
    for k in (
        "criticality",
        "modal_verb",
        "req_type",
        "weight",
        "importance",
        "page_limit",
        "volume",
        "clause_number",
        "threshold",
        "measurement_method",
        "theme_type",
    ):
        v = entity.get(k)
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            if not v:
                continue
            v = ", ".join([_collapse_ws(x) for x in v[:5] if _collapse_ws(x)])
        else:
            v = _collapse_ws(v)
        if v:
            typed_bits.append(f"{k}={v}")

    typed_block = "; ".join(typed_bits) if typed_bits else ""
    evidence_block = "\n\n---\n\n".join(evidence) if evidence else ""

    prompt = (
        "You are enriching a knowledge graph node extracted from an RFP.\n"
        "Write a concise, source-only description to improve retrieval.\n\n"
        f"Entity:\n- entity_name: {name}\n- entity_type: {t}\n"
        + (f"- known_fields: {typed_block}\n" if typed_block else "")
        + "\n"
        "Evidence (verbatim text chunks):\n"
        f"{evidence_block}\n\n"
        "Constraints:\n"
        "- 1–3 sentences\n"
        "- Source-only (no outside knowledge)\n"
        "- No bullet lists\n"
        f"- Hard limit: <= {DESCRIPTION_MAX_CHARS} characters\n"
        "- If evidence is empty or unclear, output the entity_name only.\n\n"
        "Output ONLY the description text."
    )

    if not evidence_block:
        return _clamp(name)

    try:
        resp = await call_llm_async(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=220,
        )
        return _clamp(resp)
    except Exception as e:
        logger.warning(f"Description LLM failed for {name} ({t}): {e}")
        return _clamp(name)


async def _llm_descriptions_batched(
    *,
    entities: List[Dict[str, Any]],
    kv: KVStores,
    model: str,
    temperature: float,
) -> Dict[str, str]:
    """
    Batch-generate descriptions to avoid one-LLM-call-per-entity (too slow/costly on large RFPs).
    Returns mapping entity_name -> description.
    
    Issue #46 Enhancement: Includes context_snippet from enriched kv_store for better grounding.
    """
    payload: List[Dict[str, Any]] = []
    for ent in entities:
        name = _collapse_ws(ent.get("entity_name", ""))
        if not name:
            continue
        _, evidence = _get_entity_evidence(name, kv)
        
        # Issue #46: Get context_snippet from enriched kv_store
        entry = kv.entity_chunks.get(name) or {}
        context_snippet = entry.get("context_snippet", "")

        typed_bits = []
        for k in (
            "criticality",
            "modal_verb",
            "req_type",
            "weight",
            "importance",
            "page_limit",
            "volume",
            "clause_number",
            "threshold",
            "measurement_method",
            "theme_type",
        ):
            v = ent.get(k)
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                if not v:
                    continue
                v = ", ".join([_collapse_ws(x) for x in v[:5] if _collapse_ws(x)])
            else:
                v = _collapse_ws(v)
            if v:
                typed_bits.append(f"{k}={v}")

        item = {
            "entity_name": name,
            "entity_type": _collapse_ws(ent.get("entity_type", "")),
            "known_fields": "; ".join(typed_bits),
            "evidence": evidence,
        }
        
        # Issue #46: Include context snippet if available (provides immediate grounding)
        if context_snippet:
            item["context_snippet"] = context_snippet
        
        payload.append(item)

    if not payload:
        return {}

    prompt = (
        "You are enriching a knowledge graph extracted from an RFP.\n"
        "For EACH item, write a concise, source-only description to improve retrieval.\n\n"
        "Constraints:\n"
        "- 1–3 sentences\n"
        "- Source-only (no outside knowledge)\n"
        "- No bullet lists\n"
        f"- Hard limit: <= {DESCRIPTION_MAX_CHARS} characters per description\n"
        "- Use context_snippet (if provided) as the primary source - it contains the most relevant text\n"
        "- If evidence and context_snippet are empty or unclear, use the entity_name only.\n\n"
        "Return ONLY valid JSON in this exact shape:\n"
        '{"items":[{"entity_name":"...","description":"..."}]}\n\n'
        "Items:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    # Cloud Grok: enforce JSON mode for reliability.
    # Issue #46: Increased max_tokens from 4000 to 100000
    # Previous limit caused 84% failure rate (only ~30 descriptions fit in 4000 tokens)
    # Grok-4 supports large outputs, so use 100000 for safety
    resp = await call_llm_async(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=100000,
        json_mode=True,
    )

    parsed = parse_with_pydantic(resp, DescriptionBatch, context="Description enrichment batch", allow_partial=True)
    if not parsed:
        return {}

    out: Dict[str, str] = {}
    for item in parsed.items:
        out[_collapse_ws(item.entity_name)] = _clamp(item.description)
    return out


def enrich_entity_chunk_context(rag_storage_root: str) -> Dict[str, Any]:
    """
    Enrich kv_store_entity_chunks.json with best_chunk_id and context_snippet.
    
    Issue #46: Post-extraction KV store enrichment (pure Python, no LLM).
    
    For each entity:
    1. Score all its chunks by entity mention frequency
    2. Pick the best chunk (highest score)
    3. Extract a ~100-char context snippet around the entity name
    4. Write enriched kv_store back to disk
    
    This improves description generation by:
    - Using the most relevant chunk instead of the first chunk
    - Providing immediate context grounding for LLM descriptions
    
    Args:
        rag_storage_root: Path to rag_storage directory
        
    Returns:
        Dict with enrichment statistics
    """
    ws_dir = _pick_workspace_dir(rag_storage_root)
    if ws_dir is None:
        logger.warning("KV store enrichment skipped: no workspace directory found")
        return {"status": "skipped", "reason": "no_workspace", "entities_enriched": 0}
    
    ent_path = ws_dir / "kv_store_entity_chunks.json"
    txt_path = ws_dir / "kv_store_text_chunks.json"
    
    try:
        entity_chunks = json.loads(ent_path.read_text(encoding="utf-8"))
        text_chunks = json.loads(txt_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"KV store enrichment skipped: failed reading files: {e}")
        return {"status": "skipped", "reason": "read_error", "entities_enriched": 0}
    
    if not isinstance(entity_chunks, dict) or not isinstance(text_chunks, dict):
        logger.warning("KV store enrichment skipped: invalid file format")
        return {"status": "skipped", "reason": "invalid_format", "entities_enriched": 0}
    
    logger.info(f"🔍 KV Store Context Enrichment: {len(entity_chunks)} entities, {len(text_chunks)} chunks")
    
    enriched_count = 0
    skipped_count = 0
    
    for entity_name, entry in entity_chunks.items():
        chunk_ids = entry.get("chunk_ids") or []
        if not chunk_ids:
            skipped_count += 1
            continue
        
        # Score each chunk
        best_chunk_id = None
        best_score = -1
        best_content = ""
        
        for cid in chunk_ids:
            chunk_data = text_chunks.get(cid)
            if not chunk_data:
                continue
            content = chunk_data.get("content", "")
            if not content:
                continue
            
            score = _score_chunk_for_entity(entity_name, content)
            if score > best_score:
                best_score = score
                best_chunk_id = cid
                best_content = content
        
        if best_chunk_id and best_content:
            # Extract context snippet
            context_snippet = _extract_context_snippet(entity_name, best_content, snippet_chars=150)
            
            # Update entry with enriched fields
            entry["best_chunk_id"] = best_chunk_id
            entry["context_snippet"] = context_snippet
            entry["chunk_score"] = best_score
            enriched_count += 1
        else:
            skipped_count += 1
    
    # Write enriched kv_store back to disk
    try:
        ent_path.write_text(json.dumps(entity_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"  ✅ Enriched {enriched_count} entities with context snippets (skipped {skipped_count})")
    except Exception as e:
        logger.error(f"  ❌ Failed to write enriched kv_store: {e}")
        return {"status": "error", "reason": str(e), "entities_enriched": enriched_count}
    
    return {
        "status": "success",
        "entities_enriched": enriched_count,
        "entities_skipped": skipped_count,
        "workspace": str(ws_dir)
    }


async def enrich_entity_descriptions(
    *,
    neo4j_io,
    rag_storage_path: str,
    model: str,
    temperature: float = 0.1,
    max_concurrency: int = 8,
) -> Dict[str, Any]:
    """
    Backfill Neo4j node `description` for all entities.

    Strategy:
    - Template for metadata-sufficient types (clause, submission_instruction, evaluation_factor)
    - LLM for others using evidence chunks from kv_store_entity_chunks/text_chunks
    """
    kv = _load_kv_stores(rag_storage_path)
    if kv is None:
        return {"status": "skipped", "reason": "missing_kv_stores", "entities_updated": 0}

    entities = neo4j_io.get_all_entities()
    if not entities:
        return {"status": "skipped", "reason": "no_entities", "entities_updated": 0}

    updated = 0
    to_update: List[Dict[str, Any]] = []

    logger.info(f"🧠 Description enrichment: model={model} batch_size={DESCRIPTION_BATCH_SIZE} max_tokens=100000")
    logger.info(f"📝 Processing {len(entities)} entities (concurrency={max_concurrency})")
    
    # Count entity types for detailed logging
    type_counts = {}
    for ent in entities:
        et = _collapse_ws(ent.get("entity_type", "unknown")).lower()
        type_counts[et] = type_counts.get(et, 0) + 1
    
    llm_type_count = sum(type_counts.get(t, 0) for t in LLM_DESCRIPTION_TYPES)
    template_type_count = len(entities) - llm_type_count
    
    logger.info(f"  📊 Entity type breakdown:")
    logger.info(f"      LLM-eligible types: {llm_type_count} ({', '.join(LLM_DESCRIPTION_TYPES)})")
    logger.info(f"      Template types:     {template_type_count}")

    # FIXED LOGIC: Check context snippets for ALL entity types FIRST
    # Only fall back to templates/LLM if no good snippet available
    # Issue #46 Fix: Previously only checked snippets for LLM_DESCRIPTION_TYPES
    #
    # NOTE (query quality): we store snippets as `evidence_snippet` (grounding) and keep
    # `description` semantic/compact for retrieval. See SEMANTIC_LLM_TYPES.
    
    llm_needed: List[Dict[str, Any]] = []
    snippet_used_count = 0
    snippet_skipped_reasons = {"no_snippet": 0, "low_score": 0, "too_short": 0}
    sample_snippets = []  # For logging examples
    
    for ent in entities:
        name = _collapse_ws(ent.get("entity_name", ""))
        if not name:
            continue
        et = _collapse_ws(ent.get("entity_type", "")).lower()

        # STEP 1: Try context snippet for ALL entity types (Python-first, zero LLM cost)
        entry = kv.entity_chunks.get(name) or {}
        context_snippet = entry.get("context_snippet", "")
        chunk_score = entry.get("chunk_score", 0)
        
        # Check if we have a good context snippet
        has_good_snippet = (
            context_snippet 
            and chunk_score >= 5 
            and len(context_snippet) >= 50
        )
        
        if has_good_snippet:
            # Good snippet - store as evidence for grounding/inspection.
            # Do NOT put the snippet into `description` (hurts retrieval diversity).
            snippet_evidence = _clamp(context_snippet.strip(), max_chars=DESCRIPTION_MAX_CHARS)

            # Collect samples for logging
            if len(sample_snippets) < 5:
                sample_snippets.append({"type": et, "name": name, "desc": snippet_evidence[:150]})

            snippet_used_count += 1
            to_update.append(
                {
                    "id": ent["id"],
                    "properties": {
                        "evidence_snippet": snippet_evidence,
                        "evidence_method": "context_snippet_v1",
                        "chunk_score": chunk_score,
                    },
                    "enriched_by": "description_enrichment_v1",
                }
            )
            # Fall through to choose a DESCRIPTION strategy (LLM/template/name).
        
        # STEP 2: No good snippet - track reason
        if not context_snippet:
            snippet_skipped_reasons["no_snippet"] += 1
        elif chunk_score < 5:
            snippet_skipped_reasons["low_score"] += 1
        elif len(context_snippet) < 50:
            snippet_skipped_reasons["too_short"] += 1
        
        # STEP 3: For semantic/query-critical types, generate a compact LLM description
        # (batched) to keep retrieval meaningful without giant source_text blobs.
        if et in SEMANTIC_LLM_TYPES:
            llm_needed.append(ent)
            continue
        
        # STEP 4: For non-LLM types, use template or name-only
        templ = _templated_description(ent)
        if templ is not None:
            to_update.append(
                {
                    "id": ent["id"],
                    "properties": {
                        "description": templ,
                        "description_method": "template_v1",
                    },
                    "enriched_by": "description_enrichment_v1",
                }
            )
        else:
            # Default fallback: name-only, no LLM
            to_update.append(
                {
                    "id": ent["id"],
                    "properties": {
                        "description": _clamp(name),
                        "description_method": "name_only_v1",
                    },
                    "enriched_by": "description_enrichment_v1",
                }
            )

    # Apply deterministic updates first (evidence snippets + templates/name-only).
    evidence_snippet_count = sum(1 for u in to_update if u["properties"].get("evidence_method") == "context_snippet_v1")
    template_count = sum(1 for u in to_update if u["properties"].get("description_method") == "template_v1")
    name_only_count = sum(1 for u in to_update if u["properties"].get("description_method") == "name_only_v1")
    
    logger.info(f"\n  ═══════════════════════════════════════════════════════════════")
    logger.info(f"  📊 DESCRIPTION ENRICHMENT (Evidence + Semantic Summary)")
    logger.info(f"  ═══════════════════════════════════════════════════════════════")
    logger.info(f"  ✅ evidence_snippet_v1: {evidence_snippet_count:>5} (stored evidence_snippet)")
    logger.info(f"  ✅ template_v1:         {template_count:>5} (metadata-based template)")
    logger.info(f"  ⚠️  name_only_v1:        {name_only_count:>5} (no template available)")
    logger.info(f"  ───────────────────────────────────────────────────────────────")
    logger.info(f"  📈 Total deterministic: {evidence_snippet_count + template_count + name_only_count:>5}")
    logger.info(f"  ───────────────────────────────────────────────────────────────")
    
    total_skipped = snippet_skipped_reasons["no_snippet"] + snippet_skipped_reasons["low_score"] + snippet_skipped_reasons["too_short"]
    if total_skipped > 0:
        logger.info(f"  📋 Snippet skip reasons (fell through to template/LLM):")
        logger.info(f"      no_snippet: {snippet_skipped_reasons['no_snippet']} | low_score (<5): {snippet_skipped_reasons['low_score']} | too_short (<50): {snippet_skipped_reasons['too_short']}")
    
    if sample_snippets:
        logger.info(f"\n  📝 Sample context_snippet descriptions:")
        for s in sample_snippets:
            logger.info(f"      [{s['type']}] {s['desc'][:100]}...")
    
    if to_update:
        neo4j_io.update_entity_properties(to_update)
        updated += len(to_update)
        logger.info(f"\n  💾 Saved {updated} Python-generated descriptions to Neo4j")
        to_update = []
    
    logger.info(f"\n  📊 Remaining for LLM: {len(llm_needed)} entities")

    # LLM batches (bounded concurrency)
    semaphore = asyncio.Semaphore(max_concurrency)
    llm_success_count = 0
    llm_fallback_count = 0
    llm_sample_descriptions = []

    async def process_llm_batch(batch: List[Dict[str, Any]], batch_num: int) -> List[Dict[str, Any]]:
        nonlocal llm_success_count, llm_fallback_count, llm_sample_descriptions
        async with semaphore:
            mapping = await _llm_descriptions_batched(entities=batch, kv=kv, model=model, temperature=temperature)
            updates: List[Dict[str, Any]] = []
            batch_success = 0
            batch_fallback = 0
            
            for ent in batch:
                name = _collapse_ws(ent.get("entity_name", ""))
                if not name:
                    continue
                desc = mapping.get(name)
                desc_method = "llm_v1"
                if not desc:
                    desc = _clamp(name)
                    desc_method = "llm_v1_fallback_name"
                    batch_fallback += 1
                else:
                    batch_success += 1
                    # Collect sample LLM descriptions
                    if len(llm_sample_descriptions) < 3:
                        llm_sample_descriptions.append({
                            "type": ent.get("entity_type", "unknown"),
                            "name": name,
                            "desc": desc[:150]
                        })
                
                updates.append(
                    {
                        "id": ent["id"],
                        "properties": {
                            "description": desc,
                            "description_method": desc_method,
                        },
                        "enriched_by": "description_enrichment_v1",
                    }
                )
            
            llm_success_count += batch_success
            llm_fallback_count += batch_fallback
            
            return updates

    if llm_needed:
        logger.info(f"\n  ═══════════════════════════════════════════════════════════════")
        logger.info(f"  🤖 LLM DESCRIPTION ENRICHMENT")
        logger.info(f"  ═══════════════════════════════════════════════════════════════")
        
        # Create LLM batches
        llm_batches: List[List[Dict[str, Any]]] = [
            llm_needed[i : i + DESCRIPTION_BATCH_SIZE]
            for i in range(0, len(llm_needed), DESCRIPTION_BATCH_SIZE)
        ]
        
        logger.info(f"  📦 {len(llm_needed)} entities in {len(llm_batches)} batches (batch_size={DESCRIPTION_BATCH_SIZE})")

        # Run batches in waves to control memory
        wave_size = max_concurrency * 2
        batch_num = 0
        for start in range(0, len(llm_batches), wave_size):
            wave = llm_batches[start : start + wave_size]
            wave_results = await asyncio.gather(
                *(process_llm_batch(b, batch_num + i) for i, b in enumerate(wave)), 
                return_exceptions=True
            )
            batch_num += len(wave)
            
            for res in wave_results:
                if isinstance(res, Exception):
                    logger.warning(f"  ⚠️  LLM batch failed: {res}")
                    continue
                to_update.extend(res)

            if to_update:
                neo4j_io.update_entity_properties(to_update)
                updated += len(to_update)
                to_update = []
            
            # Progress log
            logger.info(f"  📊 Batch {batch_num}/{len(llm_batches)}: success={llm_success_count} fallback={llm_fallback_count}")
        
        # LLM summary
        logger.info(f"\n  ───────────────────────────────────────────────────────────────")
        logger.info(f"  ✅ llm_v1:              {llm_success_count:>5} (LLM generated)")
        logger.info(f"  ⚠️  llm_v1_fallback:     {llm_fallback_count:>5} (LLM failed, used name)")
        
        if llm_sample_descriptions:
            logger.info(f"\n  📝 Sample LLM descriptions:")
            for s in llm_sample_descriptions:
                logger.info(f"      [{s['type']}] {s['desc'][:100]}...")
    
    # Final summary
    logger.info(f"\n  ═══════════════════════════════════════════════════════════════")
    logger.info(f"  📊 DESCRIPTION ENRICHMENT COMPLETE")
    logger.info(f"  ═══════════════════════════════════════════════════════════════")
    logger.info(f"  Total entities:         {len(entities)}")
    logger.info(f"  Total updated:          {updated}")
    logger.info(f"  ───────────────────────────────────────────────────────────────")
    logger.info(f"  Python methods:         {context_snippet_count + template_count + name_only_count}")
    logger.info(f"    - context_snippet_v1: {context_snippet_count}")
    logger.info(f"    - template_v1:        {template_count}")
    logger.info(f"    - name_only_v1:       {name_only_count}")
    logger.info(f"  LLM methods:            {llm_success_count + llm_fallback_count}")
    logger.info(f"    - llm_v1:             {llm_success_count}")
    logger.info(f"    - llm_v1_fallback:    {llm_fallback_count}")
    logger.info(f"  ═══════════════════════════════════════════════════════════════\n")

    return {"status": "success", "entities_updated": updated}


