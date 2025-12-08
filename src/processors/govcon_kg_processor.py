"""
Government Contracting Knowledge Graph Processor

Implements LightRAG's three-phase extraction pipeline for custom ontology:
- Phase 1: Accumulation & Grouping (receive pre-extracted entities/rels from chunks)
- Phase 2: Entity & Relationship Merging (deduplication)
- Phase 3: Graph Finalization (format for LightRAG insertion)

This mirrors LightRAG's native pipeline but with 18 govcon entity types
and Pydantic validation instead of generic extraction.
"""

import logging
from typing import Dict, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class GovconKGProcessor:
    """
    Three-phase knowledge graph processing pipeline for government contracting ontology.
    
    Mirrors LightRAG's extraction → merge → finalize pattern with custom ontology.
    """
    
    def __init__(self):
        """Initialize the processor."""
        self.phase1_entities = defaultdict(list)  # entity_name -> [entity_dicts]
        self.phase1_relationships = defaultdict(list)  # (src, tgt) -> [rel_dicts]
        
    def reset(self):
        """Reset internal state for new document processing."""
        self.phase1_entities.clear()
        self.phase1_relationships.clear()
    
    # ============================================================================
    # PHASE 1: ACCUMULATION (receive pre-extracted data)
    # ============================================================================
    
    def add_chunk_extractions(
        self,
        chunk_id: str,
        entities: List[Dict],
        relationships: List[Dict],
        chunk_index: int,
        total_chunks: int
    ) -> None:
        """
        Add extraction results from a single chunk (Phase 1).
        
        Args:
            chunk_id: Unique chunk identifier
            entities: List of entity dicts with 'entity_name' keys
            relationships: List of relationship dicts with 'source_id', 'target_id' keys
            chunk_index: Current chunk number (1-indexed)
            total_chunks: Total number of chunks
            
        Logs:
            LightRAG-style: "Chunk X of Y extracted N Ent + M Rel {chunk_id}"
        """
        # Group entities by name for merge phase
        for entity in entities:
            entity_name = entity.get("entity_name")
            if entity_name:
                # Add source tracking
                entity["source_chunk_id"] = chunk_id
                self.phase1_entities[entity_name].append(entity)
        
        # Group relationships by (source, target) pair
        for rel in relationships:
            src_id = rel.get("src_id")
            tgt_id = rel.get("tgt_id")
            if src_id and tgt_id:
                # Normalize relationship key (undirected - sorted order)
                rel_key = tuple(sorted([src_id, tgt_id]))
                rel["source_chunk_id"] = chunk_id
                self.phase1_relationships[rel_key].append(rel)
        
        # Log in LightRAG format
        logger.info(
            f"Chunk {chunk_index} of {total_chunks} received "
            f"{len(entities)} Ent + {len(relationships)} Rel {chunk_id}"
        )
    
    # ============================================================================
    # PHASE 2: MERGE (deduplicate entities & relationships)
    # ============================================================================
    
    def merge_entities(self) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Merge duplicate entities by entity_name (Phase 2).
        
        Returns:
            Tuple of (merged_entities, duplicate_stats)
            - merged_entities: List of deduplicated entity dicts
            - duplicate_stats: Dict mapping entity_name to occurrence count (duplicates only)
            
        Merge Strategy:
            - Keep first occurrence
            - Concatenate descriptions from duplicates
            - Track all source_chunk_ids
            
        Logs:
            LightRAG-style: "Merged: '{entity_name}' | X+1" for each duplicate
        """
        merged_entities = []
        duplicate_stats = {}
        
        entities_merged_count = 0
        
        for entity_name, entity_list in self.phase1_entities.items():
            if len(entity_list) > 1:
                # Track duplicates for logging
                duplicate_stats[entity_name] = len(entity_list)
                entities_merged_count += len(entity_list) - 1
            
            # Merge logic: keep first, concatenate descriptions
            merged_entity = entity_list[0].copy()
            
            if len(entity_list) > 1:
                # Collect all descriptions
                all_descriptions = []
                all_source_chunks = set()
                
                for entity in entity_list:
                    desc = entity.get("description", "").strip()
                    if desc and desc not in all_descriptions:
                        all_descriptions.append(desc)
                    
                    chunk_id = entity.get("source_chunk_id")
                    if chunk_id:
                        all_source_chunks.add(chunk_id)
                
                # Update merged entity
                merged_entity["description"] = " ".join(all_descriptions)
                merged_entity["source_chunk_ids"] = list(all_source_chunks)
                
                # Log merge in LightRAG format
                logger.info(f"Merged: `{entity_name}` | {len(entity_list)-1}+1")
            
            merged_entities.append(merged_entity)
        
        # Summary log
        if entities_merged_count > 0:
            logger.info(
                f"Phase 2 Entity Merge: {len(self.phase1_entities)} unique names, "
                f"{entities_merged_count} duplicates merged"
            )
        else:
            logger.info(f"Phase 2 Entity Merge: {len(merged_entities)} entities (no duplicates)")
        
        return merged_entities, duplicate_stats
    
    def merge_relationships(self) -> Tuple[List[Dict], int]:
        """
        Merge duplicate relationships by (source_id, target_id) pair (Phase 2).
        
        Returns:
            Tuple of (merged_relationships, duplicates_merged_count)
            
        Merge Strategy:
            - Deduplicate by normalized (source, target) key
            - Concatenate keywords from duplicates
            - Track all source_chunk_ids
            
        Logs:
            Summary count of relationship duplicates merged
        """
        merged_relationships = []
        relationships_merged_count = 0
        
        for rel_key, rel_list in self.phase1_relationships.items():
            if len(rel_list) > 1:
                relationships_merged_count += len(rel_list) - 1
            
            # Merge logic: keep first, merge keywords
            merged_rel = rel_list[0].copy()
            
            if len(rel_list) > 1:
                # Collect all keywords
                all_keywords = set()
                all_source_chunks = set()
                
                for rel in rel_list:
                    keywords = rel.get("keywords", "")
                    if keywords:
                        all_keywords.update(k.strip() for k in keywords.split(","))
                    
                    chunk_id = rel.get("source_chunk_id")
                    if chunk_id:
                        all_source_chunks.add(chunk_id)
                
                # Update merged relationship
                if all_keywords:
                    merged_rel["keywords"] = ", ".join(sorted(all_keywords))
                merged_rel["source_chunk_ids"] = list(all_source_chunks)
            
            merged_relationships.append(merged_rel)
        
        # Summary log
        if relationships_merged_count > 0:
            logger.info(
                f"Phase 2 Relationship Merge: {len(self.phase1_relationships)} unique pairs, "
                f"{relationships_merged_count} duplicates merged"
            )
        else:
            logger.info(
                f"Phase 2 Relationship Merge: {len(merged_relationships)} relationships (no duplicates)"
            )
        
        return merged_relationships, relationships_merged_count
    
    # ============================================================================
    # PHASE 3: FINALIZE (format for LightRAG insertion)
    # ============================================================================
    
    def finalize_custom_kg(
        self,
        merged_entities: List[Dict],
        merged_relationships: List[Dict]
    ) -> Dict:
        """
        Format merged entities/relationships for LightRAG's ainsert_custom_kg() (Phase 3).
        
        Args:
            merged_entities: Deduplicated entities from Phase 2
            merged_relationships: Deduplicated relationships from Phase 2
            
        Returns:
            Dict with 'entities' and 'relationships' keys in LightRAG format
            
        Logs:
            Final counts ready for insertion
        """
        custom_kg = {
            "entities": merged_entities,
            "relationships": merged_relationships
        }
        
        logger.info(
            f"Phase 3 Finalize: Ready to insert {len(merged_entities)} entities, "
            f"{len(merged_relationships)} relationships"
        )
        
        return custom_kg
    
    # ============================================================================
    # FULL PIPELINE (orchestrates all 3 phases)
    # ============================================================================
    
    def process_document(
        self,
        text_chunks: List[Tuple[str, List[Dict], List[Dict]]],
        multimodal_items: List[Tuple[str, List[Dict], List[Dict]]] = None
    ) -> Dict:
        """
        Execute complete three-phase pipeline for a document.
        
        Args:
            text_chunks: List of (chunk_id, entities, relationships) tuples
            multimodal_items: Optional list of (item_id, entities, relationships) tuples
            
        Returns:
            Custom KG dict ready for LightRAG insertion
            
        Pipeline:
            1. Phase 1: Accumulate & group pre-extracted entities/rels from all chunks
            2. Phase 2: Merge duplicates by entity name and relationship pairs
            3. Phase 3: Format merged data for LightRAG insertion
        """
        # Reset state
        self.reset()
        
        logger.info("=" * 80)
        logger.info("GOVCON KNOWLEDGE GRAPH PROCESSOR - 3-Phase Pipeline")
        logger.info("=" * 80)
        
        # PHASE 1: ACCUMULATION
        logger.info("")
        logger.info("Phase 1: Accumulation & Grouping")
        logger.info("-" * 80)
        
        total_chunks = len(text_chunks)
        for i, (chunk_id, entities, relationships) in enumerate(text_chunks, 1):
            self.add_chunk_extractions(chunk_id, entities, relationships, i, total_chunks)
        
        if multimodal_items:
            logger.info("")
            logger.info("Phase 1b: Multimodal Accumulation")
            logger.info("-" * 80)
            total_items = len(multimodal_items)
            for i, (item_id, entities, relationships) in enumerate(multimodal_items, 1):
                self.add_chunk_extractions(item_id, entities, relationships, i, total_items)
        
        # PHASE 2: MERGE
        logger.info("")
        logger.info("Phase 2: Entity & Relationship Merging (Deduplication)")
        logger.info("-" * 80)
        
        merged_entities, entity_dupe_stats = self.merge_entities()
        merged_relationships, rel_dupes_merged = self.merge_relationships()
        
        # PHASE 3: FINALIZE
        logger.info("")
        logger.info("Phase 3: Graph Finalization")
        logger.info("-" * 80)
        
        custom_kg = self.finalize_custom_kg(merged_entities, merged_relationships)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"PIPELINE COMPLETE: {len(merged_entities)} entities, {len(merged_relationships)} relationships")
        logger.info("=" * 80)
        
        return custom_kg
