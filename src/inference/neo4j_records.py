"""Pure helpers for Neo4j graph record and payload shapes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def entity_record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a Neo4j entity row into the post-processing entity contract."""
    return {
        "id": record["id"],
        "entity_name": record["entity_name"],
        "entity_type": record["entity_type"],
        "description": record["description"],
        "source_id": record["source_id"],
    }


def relationship_record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a Neo4j relationship row into the post-processing edge contract."""
    return {
        "source": record["source"],
        "target": record["target"],
        "type": record["rel_type"],
        "weight": record["weight"],
        "description": record["description"],
        "keywords": record["keywords"],
    }


def type_counts_from_records(records: Any) -> dict[str, int]:
    """Convert rows with type/count fields into a count mapping."""
    return {record["type"]: record["count"] for record in records}


def entity_names_from_records(records: Any) -> list[str]:
    """Extract entity_name values from Neo4j rows."""
    return [record["entity_name"] for record in records]


def count_from_record(record: Any | None, key: str) -> int:
    """Read an integer count from a single Neo4j row."""
    if not record:
        return 0
    return int(record[key] or 0)


def partition_entities_by_name(
    entities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split entity payloads into named and rejected groups."""
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for entity in entities:
        if entity.get("entity_name"):
            valid.append(entity)
        else:
            rejected.append(entity)
    return valid, rejected


def group_entities_by_type(
    entities: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group entities by lowercase entity type for efficient batching."""
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        entity_type = str(entity.get("entity_type") or "").lower()
        grouped[entity_type].append(entity)
    return dict(grouped)
