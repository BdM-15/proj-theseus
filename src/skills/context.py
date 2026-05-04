"""Workspace context builders for skill invocation.

This module owns the skill briefing-book interface: given a workspace storage
folder and optional retrieval helper, produce the deterministic evidence payload
that legacy skills receive and tools-mode skills can fetch through kg_* tools.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

QueryDataFunc = Callable[
    [str, str, list[dict], dict],
    Awaitable[dict],
]


def build_skill_briefing_book(
    workspace_dir: Path,
    entity_types: Optional[list[str]],
    max_per_type: int,
    max_chunks_per_entity: int = 2,
    max_relationships_per_entity: int = 5,
    relevant_entity_names: Optional[set[str]] = None,
) -> dict[str, Any]:
    """Build the source-grounded briefing book for a skill invocation.

    Returns a dict with three top-level keys:

    * ``entities``: ``{entity_type: [{name, description, source_chunks}]}``
    * ``source_chunks``: verbatim chunk text for cited entities
    * ``relationships``: typed KG edges connected to sliced entities

    ``relevant_entity_names`` is a lowercased whitelist from retrieval. When it
    is present, only matching entities survive; otherwise framework-noise
    buckets are dropped so bulk slices stay focused on solicitation content.
    """
    workspace_dir = Path(workspace_dir)
    entities_path = workspace_dir / "vdb_entities.json"
    if not entities_path.exists():
        return {"entities": {}, "source_chunks": [], "relationships": []}

    try:
        raw = json.loads(entities_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read entity store for skill context: %s", exc)
        return {"entities": {}, "source_chunks": [], "relationships": []}

    records: list[dict[str, Any]] = []
    if isinstance(raw, dict) and isinstance(raw.get("data"), list):
        records = [record for record in raw["data"] if isinstance(record, dict)]
    elif isinstance(raw, list):
        records = [record for record in raw if isinstance(record, dict)]

    noise_buckets = {"concept", "unknown"}
    wanted = {entity_type.lower() for entity_type in entity_types} if entity_types else None
    bucketed: dict[str, list[dict[str, Any]]] = {}
    entity_chunk_map: dict[str, list[str]] = {}
    entity_name_set: set[str] = set()

    for entity in records:
        entity_type = str(entity.get("entity_type", "")).lower()
        name = entity.get("entity_name") or entity.get("name") or ""
        name_lc = str(name).strip().lower()
        if relevant_entity_names is not None:
            if not name_lc or name_lc not in relevant_entity_names:
                continue
        else:
            if wanted is None and entity_type in noise_buckets:
                continue
        if wanted and entity_type not in wanted:
            continue
        bucket = bucketed.setdefault(entity_type or "unknown", [])
        if len(bucket) >= max_per_type:
            continue
        raw_src = str(entity.get("source_id") or "")
        chunk_ids = [chunk.strip() for chunk in raw_src.split("<SEP>") if chunk.strip()]
        bucket.append(
            {
                "name": name,
                "description": (entity.get("description") or "")[:400],
                "source_chunks": (
                    chunk_ids[:max_chunks_per_entity]
                    if max_chunks_per_entity > 0
                    else []
                ),
            }
        )
        if name:
            entity_chunk_map[name] = chunk_ids
            entity_name_set.add(name_lc)

    source_chunks = _load_source_chunks(
        workspace_dir,
        entity_chunk_map,
        max_chunks_per_entity,
    )
    relationships = _load_relationships(
        workspace_dir,
        entity_name_set,
        max_relationships_per_entity,
    )

    return {
        "entities": bucketed,
        "source_chunks": source_chunks,
        "relationships": relationships,
    }


def _load_source_chunks(
    workspace_dir: Path,
    entity_chunk_map: dict[str, list[str]],
    max_chunks_per_entity: int,
) -> list[dict[str, Any]]:
    wanted_chunk_ids: set[str] = set()
    if max_chunks_per_entity > 0:
        for chunk_ids in entity_chunk_map.values():
            for chunk_id in chunk_ids[:max_chunks_per_entity]:
                wanted_chunk_ids.add(chunk_id)

    if not wanted_chunk_ids:
        return []

    chunks_path = workspace_dir / "vdb_chunks.json"
    if not chunks_path.exists():
        return []

    source_chunks: list[dict[str, Any]] = []
    try:
        chunks_raw = json.loads(chunks_path.read_text(encoding="utf-8"))
        chunk_records: list[dict[str, Any]] = []
        if isinstance(chunks_raw, dict) and isinstance(chunks_raw.get("data"), list):
            chunk_records = [record for record in chunks_raw["data"] if isinstance(record, dict)]
        for record in chunk_records:
            chunk_id = record.get("__id__")
            if chunk_id not in wanted_chunk_ids:
                continue
            source_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_path": record.get("file_path"),
                    "content": (record.get("content") or "")[:1500],
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read chunk store for skill context: %s", exc)
    return source_chunks


def _load_relationships(
    workspace_dir: Path,
    entity_name_set: set[str],
    max_relationships_per_entity: int,
) -> list[dict[str, Any]]:
    if max_relationships_per_entity <= 0 or not entity_name_set:
        return []

    rels_path = workspace_dir / "vdb_relationships.json"
    if not rels_path.exists():
        return []

    relationships: list[dict[str, Any]] = []
    try:
        rels_raw = json.loads(rels_path.read_text(encoding="utf-8"))
        rel_records: list[dict[str, Any]] = []
        if isinstance(rels_raw, dict) and isinstance(rels_raw.get("data"), list):
            rel_records = [record for record in rels_raw["data"] if isinstance(record, dict)]
        edge_count: dict[str, int] = {name: 0 for name in entity_name_set}
        for record in rel_records:
            source = str(record.get("src_id") or "")
            target = str(record.get("tgt_id") or "")
            source_lc = source.lower()
            target_lc = target.lower()
            source_in = source_lc in entity_name_set
            target_in = target_lc in entity_name_set
            if not (source_in or target_in):
                continue
            if (
                (not source_in or edge_count.get(source_lc, 0) >= max_relationships_per_entity)
                and (not target_in or edge_count.get(target_lc, 0) >= max_relationships_per_entity)
            ):
                continue
            relationships.append(
                {
                    "src": source,
                    "type": str(record.get("keywords") or "").strip(),
                    "tgt": target,
                    "description": (record.get("description") or "")[:300],
                    "source_chunk": record.get("source_id"),
                }
            )
            if source_in:
                edge_count[source_lc] = edge_count.get(source_lc, 0) + 1
            if target_in:
                edge_count[target_lc] = edge_count.get(target_lc, 0) + 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read relationship store for skill context: %s", exc)
    return relationships


async def retrieve_relevant_entities_for_skill(
    data_func: Optional[QueryDataFunc],
    prompt: str,
    skill_description: str,
    mode: str,
    top_k: int,
) -> dict[str, Any]:
    """Run structured retrieval and return entity and chunk identifiers.

    The return shape is ``{names, chunk_ids, metadata}``, where ``names`` is a
    lowercased entity-name whitelist and ``chunk_ids`` are retrieval-ranked
    chunks available to future callers that want to augment the briefing book.
    """
    meta: dict[str, Any] = {
        "mode": mode,
        "top_k": top_k,
        "matched_entities": 0,
        "matched_chunks": 0,
        "used": False,
        "reason": "",
    }
    if mode == "off":
        meta["reason"] = "retrieval disabled (mode=off)"
        return {"names": set(), "chunk_ids": set(), "metadata": meta}
    if data_func is None:
        meta["reason"] = "server has no data_func; falling back to bulk slice"
        return {"names": set(), "chunk_ids": set(), "metadata": meta}

    user_prompt = (prompt or "").strip()
    hint = (skill_description or "").strip()
    if not user_prompt and not hint:
        meta["reason"] = "empty prompt + skill description; bulk slice"
        return {"names": set(), "chunk_ids": set(), "metadata": meta}

    retrieval_query = f"{user_prompt}\n\n[Skill context: {hint}]" if hint else user_prompt
    overrides = {
        "top_k": top_k,
        "chunk_top_k": min(top_k, 30),
        "only_need_context": True,
    }
    try:
        data = await data_func(retrieval_query, mode, [], overrides)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Skill retrieval failed (mode=%s): %s", mode, exc)
        meta["reason"] = f"retrieval error: {exc}"
        return {"names": set(), "chunk_ids": set(), "metadata": meta}

    payload = data.get("data") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        meta["reason"] = "retrieval returned no data block"
        return {"names": set(), "chunk_ids": set(), "metadata": meta}

    names: set[str] = set()
    for entity in payload.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        name = entity.get("entity_name") or entity.get("entity_id") or entity.get("name")
        if name:
            names.add(str(name).strip().lower())
    if len(names) > top_k:
        names = set(list(names)[:top_k])

    chunk_ids: set[str] = set()
    for chunk in payload.get("chunks") or []:
        if not isinstance(chunk, dict):
            continue
        chunk_id = chunk.get("chunk_id") or chunk.get("__id__")
        if chunk_id:
            chunk_ids.add(str(chunk_id))

    meta["matched_entities"] = len(names)
    meta["matched_chunks"] = len(chunk_ids)
    meta["used"] = bool(names)
    if not names:
        meta["reason"] = "retrieval returned 0 entities; falling back to bulk slice"
    return {"names": names, "chunk_ids": chunk_ids, "metadata": meta}
