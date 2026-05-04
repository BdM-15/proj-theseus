"""Pure relationship payload helpers for Neo4j graph writes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def partition_relationships_by_type(
    relationships: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split relationship payloads into valid and rejected groups.

    Neo4j cannot create relationships with null or empty relationship types.
    Keeping this pure makes malformed-payload handling easy to test without a
    database connection.
    """
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for relationship in relationships:
        relationship_type = relationship.get("relationship_type")
        if not relationship_type or (
            isinstance(relationship_type, str) and not relationship_type.strip()
        ):
            rejected.append(relationship)
            continue
        valid.append(relationship)
    return valid, rejected


def group_retype_updates(
    updates: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group relationship retype updates by old/new type pair."""
    batches: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for update in updates:
        key = (update["old_type"], update["new_type"])
        batches[key].append(update)
    return dict(batches)
