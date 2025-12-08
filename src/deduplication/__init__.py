"""
Custom deduplication modules for knowledge graph entities and relationships.

LightRAG's native upsert mechanism doesn't properly deduplicate with Neo4j storage,
so we implement our own merge logic before insertion.
"""

from .entity_deduplicator import deduplicate_entities

__all__ = ["deduplicate_entities"]
