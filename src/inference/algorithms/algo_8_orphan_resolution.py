"""
Algorithm 8: Orphan Pattern Resolution

Identifies orphan entities and suggests relationships.
Processes ALL orphans in batches to ensure complete graph connectivity.
"""
import asyncio
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)

# Configuration
ORPHAN_BATCH_SIZE = 30  # Process orphans in batches
TARGET_BATCH_SIZE = 100  # Number of target entities per batch
MAX_CONCURRENT_BATCHES = 4  # Parallel LLM calls


async def algo_8_orphan_resolution(
    entities: List[Dict],
    id_to_entity: Dict,
    neo4j_io,
    model: str,
    temperature: float,
    system_prompt: str = None
) -> List[Dict]:
    """
    Algorithm 8: Orphan Pattern Resolution
    
    Identifies entities with no relationships and suggests
    connections based on content similarity.
    
    Now processes ALL orphans in batches instead of just first 50.
    """
    logger.info(f"  [Algo 8] Orphan Resolution")
    
    orphans = []
    try:
        if neo4j_io:
            # Get ALL orphan entity names from Neo4j
            orphan_names = neo4j_io.get_orphaned_entity_ids()
            
            # Build name→entity lookup for matching
            name_to_entity = {e.get('entity_name', ''): e for e in entities}
            
            # Build COMPLETE orphan list (no limit)
            for orphan_name in orphan_names:
                if orphan_name in name_to_entity:
                    orphans.append(name_to_entity[orphan_name])
                    
            if orphan_names and not orphans:
                logger.warning(f"    Found {len(orphan_names)} orphans in Neo4j but none matched in-memory entities")
    except Exception as e:
        logger.warning(f"    Could not query orphans: {e}")
    
    if not orphans:
        logger.info(f"    No orphans detected (graph is well-connected)")
        return []
    
    logger.info(f"    Found {len(orphans)} orphan entities to resolve")
    
    # Build target entity pool (non-orphans, prioritized by type)
    orphan_ids = {o['id'] for o in orphans}
    non_orphan_entities = [e for e in entities if e['id'] not in orphan_ids]
    
    # Prioritize high-value target types
    priority_order = ['requirement', 'document_section', 'deliverable', 'document', 'clause',
                      'work_scope_item', 'evaluation_factor', 'proposal_instruction']
    
    def get_priority(entity):
        etype = entity.get('entity_type', 'zzz')
        try:
            return priority_order.index(etype)
        except ValueError:
            return len(priority_order)
    
    non_orphan_entities.sort(key=get_priority)
    target_pool = non_orphan_entities[:TARGET_BATCH_SIZE * 2]  # Larger pool for variety
    
    if not target_pool:
        logger.warning(f"    No target entities available for linking")
        return []
    
    if not system_prompt:
        system_prompt = await load_prompt_template("system_prompt.md")
    
    # Process orphans in batches
    all_relationships = []
    batches = [orphans[i:i + ORPHAN_BATCH_SIZE] for i in range(0, len(orphans), ORPHAN_BATCH_SIZE)]
    
    logger.info(f"    Processing {len(orphans)} orphans in {len(batches)} batches")
    
    async def process_batch(batch_idx: int, batch: List[Dict]) -> List[Dict]:
        """Process a single batch of orphans."""
        # Select relevant targets for this batch based on orphan types
        batch_types = {o.get('entity_type', '') for o in batch}
        
        # Include targets that complement the batch types
        targets = target_pool[:TARGET_BATCH_SIZE]
        
        orphans_json = json.dumps([{
            'id': o['id'],
            'name': o.get('entity_name', ''),
            'type': o.get('entity_type', ''),
            'description': (o.get('description') or '')[:2000]
        } for o in batch], indent=2)
        
        targets_json = json.dumps([{
            'id': e['id'],
            'name': e['entity_name'],
            'type': e.get('entity_type', ''),
            'description': (e.get('description') or '')[:2000]
        } for e in targets], indent=2)
        
        prompt = f"""Analyze orphan entities that have no relationships.
Suggest connections to other entities based on semantic similarity and government contracting domain knowledge.

ORPHAN ENTITIES (need relationships):
{orphans_json}

TARGET ENTITIES (potential relationship targets):
{targets_json}

RELATIONSHIP PATTERNS TO CONSIDER:
- Requirements → Sections they belong to (PART_OF)
- Requirements → Deliverables they mandate (REQUIRES_DELIVERABLE)
- Documents → Sections that reference them (REFERENCED_BY)
- Concepts → Requirements that implement them (IMPLEMENTED_BY)
- Organizations → Requirements that govern them (SUBJECT_TO)
- Locations → Requirements specific to that location (APPLIES_TO)

Return ONLY valid JSON array with relationships for AS MANY orphans as possible:
[{{"source_id": "orphan_id", "target_id": "target_id", "relationship_type": "TYPE", "confidence": 0.6-0.9, "reasoning": "brief explanation"}}]
"""
        
        try:
            response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = parse_llm_json_response(response, f"Algorithm 8 Batch {batch_idx}")
            if not rels:
                return []
            valid_rels = validate_relationships(rels, id_to_entity, f"Algorithm 8 Batch {batch_idx}")
            return valid_rels
        except Exception as e:
            logger.error(f"    Algorithm 8 Batch {batch_idx} failed: {e}")
            return []
    
    # Process batches with limited concurrency
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    
    async def process_with_semaphore(batch_idx: int, batch: List[Dict]) -> List[Dict]:
        async with semaphore:
            return await process_batch(batch_idx, batch)
    
    tasks = [process_with_semaphore(i, batch) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"    Batch {i} failed with exception: {result}")
        elif result:
            all_relationships.extend(result)
    
    logger.info(f"    -> Algo 8: {len(all_relationships)} relationships (from {len(orphans)} orphans)")
    return all_relationships
