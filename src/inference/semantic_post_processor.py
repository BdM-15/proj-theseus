"""
Semantic Post-Processing for Government Contracting RFPs
========================================================

Neo4j-native LLM-powered enhancements to the extracted knowledge graph:

1. **Relationship Inference**: Infer missing semantic relationships using 8 algorithms
2. **Workload Enrichment**: Add BOE metadata to requirements

Architecture (Issue #54 - Back to Basics):
- Entity extraction uses native LightRAG with govcon ontology (18 types)
- Pydantic validation is used for POST-PROCESSING only (InferredRelationship)
- No Pydantic validation during extraction - LightRAG handles it natively

Usage:
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    
    stats = await enhance_knowledge_graph(
        rag_storage_path="path/to/rag_storage",
        llm_func=my_llm_function
    )
"""

import logging
import time
import os
import re
import asyncio
import json
from typing import Dict, Callable, Awaitable, List
from pydantic import ValidationError

from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type
from src.inference.schema_prompts import (
    get_instruction_evaluation_guidance,
    get_evaluation_hierarchy_guidance,
    get_document_hierarchy_guidance
)
from src.inference.algorithms import run_all_algorithms_parallel
from src.ontology.schema import VALID_ENTITY_TYPES, InferredRelationship, InferredRelationshipBatch
from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import extract_json_from_response, parse_with_pydantic

logger = logging.getLogger(__name__)

# Convert set to list for prompt generation
ALLOWED_TYPES = list(VALID_ENTITY_TYPES)

# Configuration for semantic post-processing optimization (Issue #30)
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_ASYNC", "8"))
BATCH_SIZE_ALGO3 = int(os.getenv("BATCH_SIZE_ALGORITHM_3", 100))
BATCH_OVERLAP_ALGO3 = int(os.getenv("BATCH_OVERLAP_ALGORITHM_3", 20))
BATCH_SIZE_ALGO4 = int(os.getenv("BATCH_SIZE_ALGORITHM_4", 50))


def _heuristic_table_type_mapping(entity: Dict) -> str:
    """
    Intelligently map "table" entities (from RAG-Anything) to govcon types based on content.
    
    RAG-Anything's TableModalProcessor hardcodes entity_type="table" for all tables.
    This function examines the entity name and description to determine the correct govcon type.
    
    Args:
        entity: Entity dict with entity_name, description, etc.
    
    Returns:
        Mapped govcon type or None if LLM inference needed
    """
    name = (entity.get('entity_name') or '').lower()
    desc = (entity.get('description') or '').lower()
    content = f"{name} {desc}"
    
    # CDRL/Deliverable tables → deliverable
    if any(kw in content for kw in ['cdrl', 'contract data', 'deliverable', 'dd form 1423', 'data item']):
        return 'deliverable'
    
    # Evaluation/Rating tables → evaluation_factor  
    if any(kw in content for kw in ['evaluation', 'rating', 'scoring', 'assessment', 'criteria', 'factor']):
        return 'evaluation_factor'
    
    # Performance/Metrics tables → performance_metric
    if any(kw in content for kw in ['performance', 'metric', 'sla', 'kpi', 'threshold', 'standard']):
        return 'performance_metric'
    
    # Requirements/SOW tables → requirement
    if any(kw in content for kw in ['requirement', 'shall', 'must', 'sow', 'pws', 'task', 'work']):
        return 'requirement'
    
    # Submission/Proposal tables → submission_instruction
    if any(kw in content for kw in ['submission', 'proposal', 'volume', 'page limit', 'format']):
        return 'submission_instruction'
    
    # Clause/Regulation tables → clause
    if any(kw in content for kw in ['far ', 'dfars', 'clause', 'provision', '52.2']):
        return 'clause'
    
    # Section/Document reference tables → section or document
    if any(kw in content for kw in ['section', 'attachment', 'annex', 'exhibit', 'appendix']):
        return 'section'
    
    # Organization/Personnel tables → organization or person
    if any(kw in content for kw in ['organization', 'contractor', 'government', 'agency']):
        return 'organization'
    if any(kw in content for kw in ['personnel', 'staff', 'position', 'role', 'labor category']):
        return 'person'
    
    # Equipment/Material tables → equipment
    if any(kw in content for kw in ['equipment', 'material', 'supply', 'asset', 'gfe', 'gfp']):
        return 'equipment'
    
    # Schedule/Timeline tables → concept (general information)
    if any(kw in content for kw in ['schedule', 'timeline', 'milestone', 'calendar', 'date']):
        return 'concept'
    
    # Pricing/Cost tables → concept (we don't have a pricing type)
    if any(kw in content for kw in ['price', 'cost', 'clin', 'labor rate', 'fee']):
        return 'concept'
    
    # Can't determine heuristically - default to 'concept' (no LLM fallback)
    # With Pydantic validation in extraction, we don't need LLM post-processing
    return 'concept'


# NOTE: _infer_entity_type and _infer_entity_types_parallel REMOVED
# With Pydantic validation in extraction, LLM-based entity type correction is no longer needed.
# Invalid types are caught and coerced during extraction, not post-hoc.
# This saves LLM API costs and processing time.


async def _parse_and_validate_relationship_batch(
    response: str,
    id_to_entity: Dict,
    context: str
) -> List[Dict]:
    """
    Parse LLM response and validate relationships with Pydantic (Branch 040 pattern).
    
    Shared helper for all relationship inference algorithms.
    Validates relationships ONE-BY-ONE to gracefully filter self-loops and bad data.
    
    Args:
        response: Raw LLM response text
        id_to_entity: Dict mapping entity IDs to entity objects
        context: Context string for logging (e.g., "Algorithm 1 Batch 2")
        
    Returns:
        List of valid relationship dicts ready for Neo4j insertion
    """
    try:
        # Step 1: Extract JSON from response (handles markdown code blocks, etc.)
        response_json = extract_json_from_response(response, allow_array=True)
        
        # Step 2: Normalize to list of relationship dicts
        if isinstance(response_json, dict):
            # Handle {"relationships": [...]} or {"results": [...]} format
            relationships_data = response_json.get('relationships') or response_json.get('results') or []
        elif isinstance(response_json, list):
            relationships_data = response_json
        else:
            logger.warning(f"    ⚠️ {context}: Unexpected JSON type {type(response_json)}")
            return []
        
        # Step 3: Validate relationships ONE-BY-ONE (graceful partial validation)
        valid_rels = []
        filtered_count = 0
        self_loop_count = 0
        hallucination_count = 0
        
        for idx, rel_data in enumerate(relationships_data):
            try:
                # Validate with Pydantic (catches self-loops, normalizes fields)
                rel = InferredRelationship.model_validate(rel_data)
                
                # Verify entity IDs exist in graph
                if rel.source_id not in id_to_entity:
                    logger.debug(f"    {context}: Unknown source_id '{rel.source_id}'")
                    hallucination_count += 1
                    continue
                if rel.target_id not in id_to_entity:
                    logger.debug(f"    {context}: Unknown target_id '{rel.target_id}'")
                    hallucination_count += 1
                    continue
                
                # Convert to dict for Neo4j insertion
                valid_rels.append(rel.to_dict())
                
            except ValidationError as ve:
                # Pydantic caught a validation error (self-loop, missing field, etc.)
                filtered_count += 1
                if 'Self-loop' in str(ve):
                    self_loop_count += 1
                logger.debug(f"    {context}: Validation error for relationship {idx}: {ve}")
                continue
            except Exception as e:
                filtered_count += 1
                logger.debug(f"    {context}: Unexpected error for relationship {idx}: {e}")
                continue
        
        # Log summary
        total = len(relationships_data)
        if filtered_count > 0 or hallucination_count > 0:
            logger.info(f"    {context}: {len(valid_rels)}/{total} valid "
                       f"(filtered: {filtered_count}, hallucinated: {hallucination_count}, self-loops: {self_loop_count})")
        
        return valid_rels
        
    except Exception as e:
        logger.error(f"    ❌ {context}: Failed to parse response: {e}")
        return []


async def _infer_relationships_batch(entities: List[Dict], existing_rels: List[Dict], model: str, temperature: float) -> List[Dict]:
    """
    Infer missing relationships between entities using chunked batching with ID-based lookups.
    
    With 2M context window, processes 500 entities per batch with 100-entity overlap.
    This reduces LLM calls by 90%+ while maintaining cross-batch relationship detection.
    
    **ID-Based Approach (Branch 013a):**
    - LLM receives entity IDs (e.g., "entity_123") instead of names
    - Eliminates ambiguity from name mismatches (e.g., "Subfactor 1.1: TOMP" vs "TOMP")
    - 100% match rate for valid relationships
    
    Args:
        entities: All entities to analyze
        existing_rels: Existing relationships (for context)
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of inferred relationships
    """
    import json
    
    all_relationships = []
    batch_size = 500  # Increased from 50 to leverage 2M context window
    overlap = 100     # Increased from 25 to maintain relationship coverage
    total_entities = len(entities)
    
    # Build ID-to-entity mapping and entity reference list for LLM
    id_to_entity = {e['id']: e for e in entities}
    
    # Process in overlapping batches
    batch_num = 0
    start_idx = 0
    
    while start_idx < total_entities:
        end_idx = min(start_idx + batch_size, total_entities)
        batch_entities = entities[start_idx:end_idx]
        batch_num += 1
        
        logger.info(f"  Processing batch {batch_num}: entities {start_idx+1}-{end_idx} of {total_entities}")
        
        # Build entity reference table with IDs (eliminates name ambiguity)
        # Format: entity_123 | requirement | Task Order Management Plan (TOMP) | Contractor shall develop...
        entity_table = "ID | Type | Name | Description\n" + ("-" * 80) + "\n"
        entity_table += "\n".join([
            f"{e['id']} | {e['entity_type']} | {e['entity_name']} | {e.get('description', '')[:5000]}"
            for e in batch_entities
        ])
        
        prompt = f"""You are analyzing a government contracting knowledge graph. Identify missing relationships between these entities.

ENTITY REFERENCE TABLE:
{entity_table}

Relationship types to use:

REQUIREMENT-CENTRIC:
- REQUIRES: Requirement → Equipment/Resource needed (including quantified items)
- ENABLED_BY: Requirement → Government-provided Technology/Equipment
- FULFILLS: Deliverable → Requirement it satisfies
- RESPONSIBLE_FOR: Person → Deliverable they submit/create

STRUCTURAL:
- PART_OF: Sub-component → Parent component
- FIELD_IN: Table field → Table/Document containing it
- REFERENCES: Document/Section → Another document/section

REGULATORY:
- EVALUATES: Section M evaluation criteria → Section L requirements
- APPLIES_TO: Clause/Regulation → Program/Contract

SPECIAL PATTERNS TO CATCH:
1. Quantified equipment: "X receptacles must be emptied Y times" → REQUIRES(requirement → equipment)
2. Government-provided: "furnished by Government" → ENABLED_BY(requirement → technology)
3. Conditional equipment: "may substitute" → REQUIRES(requirement → equipment)
4. Table fields: "field in X table" → FIELD_IN(concept → document)
5. Person submissions: "shall submit" → RESPONSIBLE_FOR(person → deliverable)

Find logical relationships that are missing. For each relationship, provide:
1. Source entity ID (from ID column above - e.g., "4:abc123...")
2. Target entity ID (from ID column above - e.g., "4:def456...")
3. Relationship type (one of the above)
4. Confidence (0.0-1.0)
5. Brief reasoning

**CRITICAL**: Use entity IDs from the table above, NOT entity names. IDs eliminate ambiguity.

Format your response as JSON array:
[
  {{"source_id": "4:abc123...", "target_id": "4:def456...", "type": "EVALUATES", "confidence": 0.85, "reasoning": "..."}}
]

Return ONLY the JSON array. If no relationships found, return []."""
        
        try:
            response = await call_llm_async(prompt, model=model, temperature=temperature)
            
            # Parse JSON response
            relationships = json.loads(response)
            
            # Validate entity IDs and build relationships
            for rel in relationships:
                # Handle both 'type' and 'relationship_type' keys
                rel_type = rel.get('type') or rel.get('relationship_type')
                if not rel_type:
                    logger.warning(f"  Skipping relationship without type: {rel}")
                    continue
                
                source_id = rel.get('source_id')
                target_id = rel.get('target_id')
                
                # Validate IDs exist in our entity map
                if source_id in id_to_entity and target_id in id_to_entity:
                    all_relationships.append({
                        'source_id': source_id,
                        'target_id': target_id,
                        'relationship_type': rel_type,
                        'confidence': rel.get('confidence', 0.7),
                        'reasoning': rel.get('reasoning', '')
                    })
                else:
                    if source_id not in id_to_entity:
                        logger.warning(f"  Invalid source entity ID: {source_id}")
                    if target_id not in id_to_entity:
                        logger.warning(f"  Invalid target entity ID: {target_id}")
            
            logger.info(f"    → Found {len(relationships)} relationships in batch {batch_num}")
            
        except json.JSONDecodeError as e:
            logger.error(f"  JSON parse error in batch {batch_num}: {e}")
        except Exception as e:
            logger.error(f"  Error inferring relationships in batch {batch_num}: {e}", exc_info=True)
        
        # Move to next batch with overlap
        start_idx += (batch_size - overlap)
    
    logger.info(f"\n  Total relationships inferred across {batch_num} batches: {len(all_relationships)}")
    return all_relationships


async def _load_prompt_template(prompt_filename: str) -> str:
    """Load a prompt template from prompts/relationship_inference/"""
    from pathlib import Path
    prompt_path = Path("prompts/relationship_inference") / prompt_filename
    try:
        return prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {prompt_path}")
        return ""


def _validate_relationships(rels: List[Dict], id_to_entity: Dict, algorithm_name: str) -> List[Dict]:
    """
    Validate relationships using Pydantic models (Branch 040 pattern).
    
    Graceful degradation: Validates ONE-BY-ONE, drops bad ones, keeps batch.
    
    Args:
        rels: List of relationship dicts from LLM
        id_to_entity: Mapping of entity IDs to entities
        algorithm_name: Name of algorithm for logging
        
    Returns:
        List of valid relationships with required fields only
    """
    valid_rels = []
    filtered_count = 0
    self_loop_count = 0
    hallucination_count = 0
    
    for rel in rels:
        try:
            # Validate with Pydantic (catches self-loops, normalizes fields)
            validated = InferredRelationship.model_validate(rel)
            
            # Verify entity IDs exist in graph
            if validated.source_id not in id_to_entity:
                hallucination_count += 1
                continue
            if validated.target_id not in id_to_entity:
                hallucination_count += 1
                continue
            
            # Convert to dict for Neo4j insertion
            valid_rels.append(validated.to_dict())
            
        except ValidationError as ve:
            # Pydantic caught a validation error (self-loop, missing field, etc.)
            filtered_count += 1
            if 'Self-loop' in str(ve):
                self_loop_count += 1
            logger.debug(f"    {algorithm_name}: Pydantic validation failed - {ve}")
            continue
        except Exception as e:
            filtered_count += 1
            logger.debug(f"    {algorithm_name}: Unexpected error - {e}")
            continue
    
    # Log summary if any were filtered
    total = len(rels)
    if filtered_count > 0 or hallucination_count > 0:
        logger.info(f"    {algorithm_name}: {len(valid_rels)}/{total} valid "
                   f"(filtered: {filtered_count}, hallucinated: {hallucination_count}, self-loops: {self_loop_count})")
    
    return valid_rels


async def _resolve_orphan_patterns(
    entities: List[Dict],
    id_to_entity: Dict[str, Dict],
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Resolve orphaned entities using LLM-powered relationship inference.
    
    Strategy: Single batched LLM call with all orphans + connected entities
    for focused inference. More efficient than per-orphan calls and more
    adaptive than regex patterns.
    
    Patterns addressed:
    - Equipment/Technology → Requirements (quantified, Gov't-provided)
    - Person → Deliverable (submission responsibilities)
    - Concept → Document (table fields, data elements)
    - Any other missing relationships the LLM detects
    
    Args:
        entities: All entities to analyze
        id_to_entity: Entity ID lookup dictionary
        neo4j_io: Neo4jGraphIO instance for querying orphans
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationships for orphan patterns
    """
    import json
    
    # Get truly orphaned entity IDs from Neo4j (nodes with NO relationships)
    orphan_ids = set(neo4j_io.get_orphaned_entity_ids())
    
    if not orphan_ids:
        logger.info("    → No orphaned entities found")
        return []
    
    # Filter entities to only those that are actually orphaned
    orphaned = [e for e in entities if e['id'] in orphan_ids]
    
    if not orphaned:
        logger.info("    → No orphaned entities found")
        return []
    
    logger.info(f"    → Found {len(orphaned)} orphaned entities")
    
    # Build entity type indices for candidate relationships
    entities_by_type = {}
    for e in entities:
        etype = e.get('entity_type', 'concept')
        if etype not in entities_by_type:
            entities_by_type[etype] = []
        entities_by_type[etype].append(e)
    
    # Gather candidate entities for linking (focus on high-value types)
    candidate_types = ['requirement', 'deliverable', 'document', 'clause', 'section', 
                      'work_statement', 'evaluation_factor', 'technology', 'equipment']
    
    candidates = []
    for etype in candidate_types:
        candidates.extend(entities_by_type.get(etype, []))
    
    # Limit candidates to avoid massive prompts (take top 200 most relevant)
    # Prioritize requirements and deliverables (most common link targets)
    priority_candidates = (
        entities_by_type.get('requirement', [])[:100] +
        entities_by_type.get('deliverable', [])[:50] +
        entities_by_type.get('document', [])[:30] +
        entities_by_type.get('clause', [])[:20]
    )
    
    if not priority_candidates:
        logger.info("    → No candidate entities for linking")
        return []
    
    logger.info(f"    → Using {len(orphaned)} orphans × {len(priority_candidates)} candidates for inference")
    
    # Build JSON representations (truncate descriptions to save tokens)
    orphan_json = json.dumps([{
        'id': o['id'],
        'name': o['entity_name'],
        'type': o.get('entity_type'),
        'description': o.get('description', '')[:5000]
    } for o in orphaned], indent=2)
    
    candidate_json = json.dumps([{
        'id': c['id'],
        'name': c['entity_name'],
        'type': c.get('entity_type'),
        'description': c.get('description', '')[:5000]
    } for c in priority_candidates], indent=2)
    
    # LLM prompt optimized for orphan resolution
    prompt = f"""You are analyzing orphaned entities in a government contracting knowledge graph. 
These entities were extracted correctly but lack relationships to other entities.

ORPHANED ENTITIES (need relationships):
{orphan_json}

CANDIDATE ENTITIES (potential relationship targets):
{candidate_json}

Find logical relationships for as many orphans as possible. Common patterns:

REQUIREMENT-CENTRIC:
- REQUIRES: Requirement → Equipment/Resource (e.g., "Trash must be emptied" → trash receptacles)
- ENABLED_BY: Requirement → Gov't-provided Technology/Equipment (e.g., "GFE ancillary hardware")
- SATISFIED_BY: Requirement → Deliverable

PERSON-CENTRIC:
- RESPONSIBLE_FOR: Person → Deliverable they submit/create (e.g., "Program Manager submits QCP")

DOCUMENT-CENTRIC:
- FIELD_IN: Table field/Data element → Document/Clause containing it (e.g., "DODAAC field in WAWF table")
- PART_OF: Sub-component → Parent document
- REFERENCES: Document → Another document

SPECIAL PATTERNS:
- Quantified items: "X equipment must be Y times" → REQUIRES
- Government-provided: "furnished by Government" → ENABLED_BY
- Conditional requirements: "may substitute" → REQUIRES
- Table/data references: "field in X" → FIELD_IN

Use entity IDs from 'id' field. Return ONLY valid relationships.
Return ONLY valid JSON array:
[
  {{"source_id": "entity_id", "target_id": "entity_id", "relationship_type": "TYPE", "reasoning": "brief evidence"}}
]

If no relationships found, return []."""

    try:
        response = await call_llm_async(prompt, model=model, temperature=temperature)
        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 8")
        logger.info(f"    → Found {len(valid_rels)} orphan relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 8 failed: {e}")
        return []


# NOTE: Algorithm functions moved to src/inference/algorithms/ modules
# Orchestrated by run_all_algorithms_parallel() from src.inference.algorithms



async def _semantic_post_processor_neo4j(
    llm_model_name: str = None,
    temperature: float = 0.1,
    rag_storage_path: str = "./rag_storage",
) -> Dict:
    """
    Neo4j-native semantic post-processing using Cypher queries.
    
    This function:
    1. Reads entities/relationships from Neo4j
    2. Corrects entity types using LLM inference
    3. Infers missing relationships using LLM inference
    4. Writes updates back to Neo4j via Cypher
    
    Args:
        llm_model_name: Name of LLM model to use
        temperature: Temperature for LLM inference
        
    Returns:
        Dict with processing statistics
    """
    if llm_model_name is None:
        # Use REASONING model for post-processing (not extraction model)
        llm_model_name = os.getenv("REASONING_LLM_NAME", "grok-4-fast-reasoning")
    
    logger.info("🔧 Starting Neo4j semantic post-processing...")
    start_time = time.time()
    
    # Initialize Neo4j I/O
    logger.info("\n📊 Initializing Neo4j connection...")
    neo4j_io = Neo4jGraphIO()
    
    try:
        # Step 1: Load entities and relationships
        logger.info("\n📥 Step 1: Loading knowledge graph from Neo4j...")
        entities = neo4j_io.get_all_entities()
        relationships = neo4j_io.get_all_relationships()
        
        # Capture initial counts from main processing (before post-processing)
        initial_entity_count = len(entities)
        initial_rel_count = len(relationships)
        logger.info(f"  📊 Main Processing Results: {initial_entity_count} entities, {initial_rel_count} relationships")
        
        if not entities:
            logger.warning("⚠️  No entities found in Neo4j workspace")
            return {
                "status": "skipped",
                "reason": "no_entities",
                "entities_corrected": 0,
                "relationships_inferred": 0,
                "processing_time": 0
            }
        
        # Step 2: Lightweight Entity Type Cleanup (NO LLM INFERENCE)
        # ========================================================================
        # With native LightRAG extraction, most types are valid from our ontology.
        # This step ONLY handles edge cases:
        # 1. "table" from RAG-Anything's multimodal processors (generic type)
        # 2. Hash-prefixed types (#requirement) from LightRAG internal markers
        # 
        # NO LLM calls needed - all corrections are heuristic/deterministic.
        # ========================================================================
        logger.info("\n🔧 Step 2: Lightweight entity type cleanup (native LightRAG handles most types)...")
        entity_updates = []
        grouped = group_entities_by_type(entities)
        
        table_mapped = 0
        hash_cleaned = 0
        unknown_entities = []  # Collect UNKNOWN entities for LLM retyping
        
        for entity_type, entity_group in grouped.items():
            entity_type_clean = entity_type.lower()
            has_hash_prefix = entity_type_clean.startswith('#')
            
            # Strip # prefix if present (LightRAG internal marker)
            if has_hash_prefix:
                entity_type_clean = entity_type_clean[1:]
            
            # CASE 1: "table" entities from RAG-Anything multimodal processors
            # These bypass our Pydantic adapter - map based on content heuristically
            if entity_type_clean == 'table':
                logger.info(f"  📊 Processing {len(entity_group)} table entities (from RAG-Anything)...")
                for entity in entity_group:
                    mapped_type = _heuristic_table_type_mapping(entity)
                    if mapped_type:
                        entity_updates.append({
                            'id': entity['id'],
                            'new_entity_type': mapped_type
                        })
                        table_mapped += 1
                    # If can't map, leave as 'concept' (safe default)
                    # NO LLM fallback - extraction should have handled this
                continue
            
            # CASE 2: Hash-prefixed types (#requirement) - just clean the prefix
            if has_hash_prefix and entity_type_clean in [t.lower() for t in ALLOWED_TYPES]:
                logger.info(f"  🔧 Cleaning {len(entity_group)} '{entity_type}' → '{entity_type_clean}'")
                for entity in entity_group:
                    entity_updates.append({
                        'id': entity['id'],
                        'new_entity_type': entity_type_clean
                    })
                    hash_cleaned += 1
                continue
            
            # CASE 3: "UNKNOWN" entities - created by LightRAG when relationships reference
            # entities that weren't extracted (due to delimiter corruption or missing extraction).
            # These could contain critical workload drivers - retype them with LLM.
            if entity_type_clean == 'unknown':
                unknown_entities.extend(entity_group)
        
        if table_mapped > 0:
            logger.info(f"  ✅ Heuristically mapped {table_mapped} table entities")
        if hash_cleaned > 0:
            logger.info(f"  ✅ Cleaned {hash_cleaned} hash-prefixed entity types")
        
        # CASE 3 Processing: LLM retype UNKNOWN entities (could be critical workload drivers)
        unknown_retyped = 0
        if unknown_entities:
            logger.info(f"  🔍 Retyping {len(unknown_entities)} UNKNOWN entities with LLM...")
            from src.inference.entity_operations import retype_entities_batch
            from src.utils.llm_client import call_llm_async
            
            # LLM function wrapper for retyping
            async def llm_func(prompt: str, system_prompt: str) -> str:
                return await call_llm_async(
                    prompt=prompt,
                    model=llm_model_name,
                    system_prompt=system_prompt,
                    temperature=0.1  # Low temp for consistent typing
                )
            
            # Process in batches of 20 to avoid token limits
            batch_size = 20
            for i in range(0, len(unknown_entities), batch_size):
                batch = unknown_entities[i:i+batch_size]
                try:
                    retyped = await retype_entities_batch(batch, llm_func)
                    for entity in batch:
                        entity_name = entity.get('entity_name')
                        if entity_name in retyped:
                            new_type = retyped[entity_name]
                            if new_type and new_type.lower() != 'unknown':
                                entity_updates.append({
                                    'id': entity['id'],
                                    'new_entity_type': new_type.lower()
                                })
                                unknown_retyped += 1
                                logger.debug(f"    Retyped '{entity_name}': UNKNOWN → {new_type}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to retype batch {i//batch_size + 1}: {e}")
            
            if unknown_retyped > 0:
                logger.info(f"  ✅ LLM retyped {unknown_retyped}/{len(unknown_entities)} UNKNOWN entities")
        
        entities_corrected = 0
        if entity_updates:
            logger.info(f"\n💾 Updating {len(entity_updates)} entity types in Neo4j...")
            entities_corrected = neo4j_io.update_entity_types(entity_updates)
        else:
            logger.info("\n✅ No entity type corrections needed (native LightRAG extraction working)")
        
        # Step 3: Infer missing relationships using PARALLEL modular algorithms
        logger.info("\n🔗 Step 3: Inferring relationships with PARALLEL algorithm execution...")
        
        # Build lookups for algorithm orchestrator
        entities_by_type = grouped  # Already built from step 2
        id_to_entity = {e['id']: e for e in entities}
        
        new_relationships = await run_all_algorithms_parallel(
            entities=entities,
            entities_by_type=entities_by_type,
            id_to_entity=id_to_entity,
            neo4j_io=neo4j_io,
            model=llm_model_name,
            temperature=temperature
        )
        
        relationships_inferred = 0
        if new_relationships:
            logger.info(f"\n💾 Creating {len(new_relationships)} new relationships in Neo4j...")
            relationships_inferred = neo4j_io.create_relationships(new_relationships)
        else:
            logger.info("\n✅ No new relationships inferred")
        
        # Step 4: Workload Enrichment (BOE metadata for requirements)
        logger.info("\n🏗️ Step 4: Enriching requirements with workload metadata...")
        from src.inference.workload_enrichment import enrich_workload_metadata
        
        workload_stats = await enrich_workload_metadata(
            neo4j_io=neo4j_io,
            batch_size=5,  # Small batches, NO truncation - full detail for quality (~94K tokens max)
            model=llm_model_name,
            temperature=temperature
        )
        
        requirements_enriched = workload_stats.get("requirements_enriched", 0)
        enrichment_rate = workload_stats.get("enrichment_rate", 0)
        category_distribution = workload_stats.get("category_distribution", {})
        
        logger.info(f"\n✅ Workload enrichment complete:")
        logger.info(f"  Requirements enriched: {requirements_enriched}")
        logger.info(f"  Enrichment rate:       {enrichment_rate:.1f}%")
        if category_distribution:
            logger.info(f"  BOE categories used:   {', '.join([f'{k}:{v}' for k,v in category_distribution.items() if v > 0])}")
        
        # Summary statistics
        processing_time = time.time() - start_time
        logger.info("\n" + "="*80)
        logger.info("✅ SEMANTIC POST-PROCESSING COMPLETE (Neo4j)")
        logger.info("="*80)
        logger.info(f"  Entities corrected:      {entities_corrected}")
        logger.info(f"  Relationships inferred:  {relationships_inferred}")
        logger.info(f"  Requirements enriched:   {requirements_enriched}")
        logger.info(f"  Processing time:         {processing_time:.2f}s")
        logger.info("="*80)
        
        # Get updated counts
        type_counts = neo4j_io.get_entity_count_by_type()
        rel_counts = neo4j_io.get_relationship_count_by_type()
        
        final_entity_count = sum(type_counts.values())
        final_relationship_count = sum(rel_counts.values())
        
        logger.info("\n📊 Entity Type Distribution (ALL 18 types):")
        # Show all types, sorted by count
        for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {entity_type:30s}: {count:4d}")
        
        # Show summary counts
        logger.info("\n" + "="*60)
        logger.info("📈 FINAL COUNTS:")
        logger.info("="*60)
        logger.info(f"  Main Processing Entities:      {initial_entity_count}")
        logger.info(f"  Main Processing Relationships: {initial_rel_count}")
        logger.info(f"  Post-Processing Added Rels:    {relationships_inferred}")
        logger.info(f"  ─────────────────────────────────────")
        logger.info(f"  Final Entity Count:            {final_entity_count}")
        logger.info(f"  Final Relationship Count:      {final_relationship_count}")
        logger.info("="*60)
        
        return {
            "status": "success",
            "entities_corrected": entities_corrected,
            "relationships_inferred": relationships_inferred,
            "requirements_enriched": requirements_enriched,
            "enrichment_rate": enrichment_rate,
            "category_distribution": category_distribution,
            "processing_time": processing_time,
            "entity_type_counts": type_counts
        }
        
    except Exception as e:
        logger.error(f"❌ Error during Neo4j post-processing: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "entities_corrected": 0,
            "relationships_inferred": 0,
            "requirements_enriched": 0,
            "processing_time": time.time() - start_time
        }
    finally:
        neo4j_io.close()


async def enhance_knowledge_graph(
    rag_storage_path: str,
    llm_func: Callable[[str, str], Awaitable[str]],
    batch_size: int = 50
) -> Dict:
    """
    Run semantic post-processing on extracted knowledge graph (Neo4j).
    
    Steps:
    1. Load entities/relationships from Neo4j
    2. Infer missing relationships (8 algorithms)
    3. Enrich requirements with workload metadata
    4. Write updates back to Neo4j
    
    Note: Entity type enforcement is handled at extraction time via Pydantic
    schema validation - no post-processing correction needed.
    
    Args:
        rag_storage_path: Path to rag_storage directory (unused - kept for API compatibility)
        llm_func: Async LLM function (unused - we use centralized call_llm_async)
        batch_size: Batch size for LLM calls (default: 50)
    
    Returns:
        Stats dict with:
        - relationships_inferred: Number of new relationships
        - requirements_enriched: Number of requirements with BOE metadata
        - processing_time: Total time in seconds
    """
    logger.info("=" * 80)
    logger.info("🧠 SEMANTIC POST-PROCESSING: LLM-Powered Graph Enhancement (Neo4j)")
    logger.info("=" * 80)
    
    # Get LLM model from environment - use REASONING model for post-processing
    llm_model = os.getenv("REASONING_LLM_NAME", "grok-4-fast-reasoning")
    llm_temp = float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
    
    return await _semantic_post_processor_neo4j(
        llm_model_name=llm_model,
        temperature=llm_temp,
        rag_storage_path=rag_storage_path,
    )
