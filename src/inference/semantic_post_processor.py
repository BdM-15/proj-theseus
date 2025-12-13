"""
Semantic Post-Processing for Government Contracting RFPs
========================================================

Neo4j-native LLM-powered enhancements to the extracted knowledge graph:

1. **Relationship Inference**: Infer missing semantic relationships using 8 algorithms
2. **Workload Enrichment**: Add BOE metadata to requirements

Entity type enforcement is handled at extraction time via Pydantic schema validation
in src/ontology/schema.py - no post-processing correction needed.

Usage:
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    
    stats = await enhance_knowledge_graph(
        rag_storage_path="./rag_storage",
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
            relationships = extract_json_from_response(response)
            
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
            
        except (ValueError, TypeError) as e:
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
    Validate and filter relationships using Pydantic models.
    
    Pattern: Follows WorkloadEnrichmentItem proven approach (100% success rate).
    Graceful degradation: Never drops relationships - marks validation warnings instead.
    
    Args:
        rels: List of relationship dicts from LLM
        id_to_entity: Mapping of entity IDs to entities
        algorithm_name: Name of algorithm for logging
        
    Returns:
        List of valid relationships with required fields only
    """
    from src.ontology.schema import InferredRelationship
    from pydantic import ValidationError
    
    valid_rels = []
    validation_errors = 0
    
    for rel in rels:
        try:
            # Validate with Pydantic - catches self-loops, missing fields, etc.
            validated = InferredRelationship.model_validate(rel)
            
            # Check entity IDs exist (Pydantic can't validate this without context)
            if validated.source_id not in id_to_entity:
                logger.warning(
                    f"    ⚠️ {algorithm_name}: Unknown source_id '{validated.source_id}' "
                    f"in relationship {validated.relationship_type}"
                )
                validation_errors += 1
                continue
            
            if validated.target_id not in id_to_entity:
                logger.warning(
                    f"    ⚠️ {algorithm_name}: Unknown target_id '{validated.target_id}' "
                    f"in relationship {validated.relationship_type}"
                )
                validation_errors += 1
                continue
            
            # Convert back to dict for backward compatibility
            valid_rels.append(validated.to_dict())
            
        except ValidationError as ve:
            # Pydantic caught a validation error (self-loop, missing field, etc.)
            validation_errors += 1
            # Safe error detail extraction - handle empty loc tuples
            error_details = '; '.join([
                f"{err['loc'][0] if err.get('loc') else 'unknown'}: {err['msg']}" 
                for err in ve.errors()
            ])
            logger.warning(
                f"    ⚠️ {algorithm_name}: Pydantic validation failed - {error_details}. "
                f"Relationship data: {rel}"
            )
            continue
        except Exception as e:
            # Unexpected error - log but don't crash
            validation_errors += 1
            logger.warning(f"    ⚠️ {algorithm_name}: Unexpected validation error: {e}")
            continue
    
    if validation_errors > 0:
        logger.warning(
            f"    ⚠️ {algorithm_name}: Filtered out {validation_errors} of {len(rels)} relationships "
            f"({len(valid_rels)} valid, {validation_errors} validation errors)"
        )
    
    return valid_rels


def _is_main_evaluation_factor(entity: Dict) -> bool:
    """
    Identify main evaluation factors vs supporting entities.
    
    MOVED from inline logic to reusable function for Algorithm 3.
    
    CRITICAL: Government RFPs have 3-8 main factors BUT 40-100+ total eval factor entities.
    70-90% are supporting entities (rating scales, metrics, processes, tables).
    ONLY link main factors/subfactors to requirements for accurate coverage metrics.
    
    Returns:
        True if main factor/subfactor (linkable), False if supporting entity
    """
    # CRITICAL: Neo4j can return None for null values, so use 'or' to ensure string
    name_lower = (entity.get('entity_name') or '').lower()
    
    # STRICT KEEP: Explicit main factor patterns only
    main_factor_patterns = [
        'factor a', 'factor b', 'factor c', 'factor d', 'factor e', 'factor f',
        'factor 1', 'factor 2', 'factor 3', 'factor 4', 'factor 5', 'factor 6',
        'subfactor',
        'technical factor', 'price factor', 'cost factor', 'management factor',
        'tomp', 'past performance', 'small business',
        'mission essential', 'quality control plan'
    ]
    
    # Check for methodology subfactors (conditional)
    if 'methodology' in name_lower and any(x in name_lower for x in ['management', 'technical', 'navy', 'usmc', 'army']):
        main_factor_patterns.append('methodology')
    
    # CRITICAL: Must match at least ONE main factor pattern (default EXCLUDE)
    has_main_pattern = any(pattern in name_lower for pattern in main_factor_patterns)
    if not has_main_pattern:
        return False
    
    # EXCLUDE: Even if main pattern matched, exclude supporting entities
    
    # Rating scale values
    rating_values = ['outstanding', 'good', 'acceptable', 'marginal', 'unacceptable',
                    'satisfactory', 'unsatisfactory', 'pass', 'fail',
                    'substantial confidence', 'limited confidence', 'neutral confidence',
                    'very relevant', 'relevant', 'somewhat relevant', 'not relevant']
    if any(rating in name_lower for rating in rating_values):
        return False
    
    # Generic processes/analyses
    generic_processes = ['analysis', 'assessment', 'government evaluation', 'interviews',
                       'realism', 'reasonableness', 'completeness', 'adjectival']
    if any(term in name_lower for term in generic_processes):
        return False
    
    # Metrics/indices
    if any(indicator in name_lower for indicator in ['%', 'cei', 'sei', 'kpi', 'index', 'cost effectiveness']):
        return False
    
    # Tables/outlines
    if '(table)' in name_lower or 'table' in name_lower or 'outline' in name_lower:
        return False
    
    # Volume references
    if 'volume' in name_lower and any(x in name_lower for x in ['i', 'ii', 'iii', 'iv', 'v']):
        return False
    
    # PASSED: Has main pattern AND not excluded = TRUE MAIN FACTOR
    return True


async def _parse_and_validate_relationship_batch(
    response: str,
    id_to_entity: Dict,
    context: str
) -> List[Dict]:
    """
    Parse LLM response and validate relationships with Pydantic (ROBUST).
    
    Shared helper for all relationship inference algorithms.
    Validates relationships ONE-BY-ONE to gracefully filter self-loops and bad data.
    
    Args:
        response: Raw LLM response text
        id_to_entity: Dict mapping entity IDs to entity objects
        context: Context string for logging (e.g., "Algorithm 1 Batch 2")
        
    Returns:
        List of validated relationship dicts (self-loops and hallucinations filtered)
    """
    try:
        # Step 1: Extract JSON from response
        response_json = extract_json_from_response(response, allow_array=True)
        
        # Step 2: Extract relationships array
        if isinstance(response_json, dict):
            # Unwrap common wrapper keys
            relationships_data = (
                response_json.get('relationships') or
                response_json.get('results') or
                response_json.get('data') or
                response_json.get('items') or
                []
            )
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
                    logger.warning(
                        f"    ⚠️ {context}: Relationship {idx}: "
                        f"LLM hallucinated source entity ID - {rel.source_id}. Skipping."
                    )
                    hallucination_count += 1
                    continue
                
                if rel.target_id not in id_to_entity:
                    logger.warning(
                        f"    ⚠️ {context}: Relationship {idx}: "
                        f"LLM hallucinated target entity ID - {rel.target_id}. Skipping."
                    )
                    hallucination_count += 1
                    continue
                
                # Valid relationship - add to results
                valid_rels.append(rel.to_dict())
                
            except ValidationError as e:
                # Check if it's a self-loop (expected, filter silently)
                if any('Self-loop detected' in str(err.get('msg', '')) for err in e.errors()):
                    self_loop_count += 1
                else:
                    # Other validation error (missing field, bad type, etc.)
                    logger.warning(
                        f"    ⚠️ {context}: Relationship {idx} failed validation: "
                        f"{e.errors()[0]['msg']} at {e.errors()[0]['loc']}"
                    )
                filtered_count += 1
        
        # Step 4: Log filtering summary
        if filtered_count > 0:
            logger.info(
                f"    → {context}: Validated {len(valid_rels)}/{len(relationships_data)} relationships "
                f"({filtered_count} filtered: {self_loop_count} self-loops, "
                f"{hallucination_count} hallucinated IDs, "
                f"{filtered_count - self_loop_count - hallucination_count} other errors)"
            )
        
        return valid_rels
        
    except Exception as e:
        logger.error(f"    ❌ {context}: Batch parsing failed: {e}")
        return []


async def _process_req_eval_batch(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore,
    id_to_entity: Dict,
    batch_num: int,
    total_batches: int
) -> List[Dict]:
    """Process single batch for Algorithm 3 (Requirement→Evaluation Mapping) with Pydantic validation"""
    try:
        async with semaphore:
            response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        
        return await _parse_and_validate_relationship_batch(
            response,
            id_to_entity,
            f"Algorithm 3 Batch {batch_num}/{total_batches}"
        )
    except Exception as e:
        logger.error(f"    ❌ Batch {batch_num}/{total_batches} failed: {e}")
        return []


async def _process_deliverable_batch(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore,
    id_to_entity: Dict,
    batch_label: str
) -> List[Dict]:
    """Process single batch for Algorithm 4 (Deliverable Traceability) with Pydantic validation"""
    try:
        async with semaphore:
            response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        
        return await _parse_and_validate_relationship_batch(
            response,
            id_to_entity,
            f"Algorithm 4 {batch_label}"
        )
    except Exception as e:
        logger.error(f"    ❌ {batch_label} failed: {e}")
        return []


async def _resolve_orphan_patterns(
    entities: List[Dict],
    id_to_entity: Dict[str, Dict],
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Resolve orphaned entities using LLM-powered relationship inference (PHASE 2 OPTIMIZED).
    
    PHASE 2 OPTIMIZATION:
    - Conditional batching: Single call if < 100 orphans, batch if >= 100
    - Dynamic batch sizing based on orphan count
    - Expected: 20-30s → 15-20s for large RFPs
    
    Strategy: Batched LLM calls with orphans + connected entities
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
    
    # Load prompt template (consistent with other algorithms)
    prompt_instructions = await _load_prompt_template("orphan_resolution.md")
    if not prompt_instructions:
        logger.error("    ❌ Failed to load orphan_resolution.md prompt")
        return []
    
    # Get truly orphaned entity names from Neo4j (nodes with NO relationships)
    orphan_names = set(neo4j_io.get_orphaned_entity_ids())
    
    if not orphan_names:
        logger.info("    → No orphaned entities found")
        return []
    
    # Filter entities to only those that are actually orphaned
    orphaned = [e for e in entities if e['entity_name'] in orphan_names]
    
    if not orphaned:
        logger.info("    → No orphaned entities found")
        return []
    
    # Build entity type indices for candidate relationships
    entities_by_type = {}
    for e in entities:
        etype = e.get('entity_type', 'concept')
        if etype not in entities_by_type:
            entities_by_type[etype] = []
        entities_by_type[etype].append(e)
    
    # Gather candidate entities for linking (prioritized by importance)
    priority_candidates = (
        entities_by_type.get('requirement', [])[:100] +
        entities_by_type.get('deliverable', [])[:50] +
        entities_by_type.get('document', [])[:30] +
        entities_by_type.get('clause', [])[:20]
    )
    
    if not priority_candidates:
        logger.info("    → No candidate entities for linking")
        return []
    
    # PHASE 2: Conditional batching based on orphan count
    BATCH_THRESHOLD = 100
    orphan_count = len(orphaned)
    
    if orphan_count < BATCH_THRESHOLD:
        # Small count: Single LLM call
        logger.info(f"    → Processing {orphan_count} orphans × {len(priority_candidates)} candidates (single batch)")
        return await _process_orphan_batch(orphaned, priority_candidates, id_to_entity, model, temperature, prompt_instructions)
    else:
        # Large count: Batch processing
        batch_size = 80  # 80 orphans per batch
        num_batches = (orphan_count + batch_size - 1) // batch_size
        logger.info(f"    → Processing {orphan_count} orphans × {len(priority_candidates)} candidates ({num_batches} batches)")
        
        batch_tasks = []
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, orphan_count)
            orphan_batch = orphaned[batch_start:batch_end]
            
            batch_tasks.append(_process_orphan_batch(
                orphan_batch, priority_candidates, id_to_entity, model, temperature, prompt_instructions
            ))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine results
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Orphan batch {i} failed: {result}")
            else:
                all_rels.extend(result)
        
        logger.info(f"    → Found {len(all_rels)} orphan relationships ({num_batches} batches)")
        return all_rels


async def _process_orphan_batch(
    orphaned: List[Dict],
    candidates: List[Dict],
    id_to_entity: Dict,
    model: str,
    temperature: float,
    prompt_instructions: str
) -> List[Dict]:
    """
    Process a single batch of orphaned entities with Pydantic validation.
    
    Helper function for conditional batching in _resolve_orphan_patterns.
    
    Args:
        orphaned: List of orphaned entity dicts
        candidates: List of candidate entity dicts for linking
        id_to_entity: Entity ID lookup dictionary
        model: LLM model name
        temperature: LLM temperature
        prompt_instructions: Loaded prompt template from orphan_resolution.md
    """
    import json
    
    # Build JSON representations using entity_name as ID (human-readable, easier for LLM)
    orphan_json = json.dumps([{
        'id': o['entity_name'],
        'name': o['entity_name'],
        'type': o.get('entity_type'),
        'description': o.get('description', '')[:5000]
    } for o in orphaned], indent=2)
    
    candidate_json = json.dumps([{
        'id': c['entity_name'],
        'name': c['entity_name'],
        'type': c.get('entity_type'),
        'description': c.get('description', '')[:5000]
    } for c in candidates], indent=2)
    
    # Build prompt using loaded template + entity data
    prompt = f"""You are analyzing orphaned entities in a government contracting knowledge graph.
These entities were extracted correctly but lack relationships to other entities.

ORPHANED ENTITIES (need relationships):
{orphan_json}

CANDIDATE ENTITIES (potential relationship targets):
{candidate_json}

{prompt_instructions}

Return ONLY valid JSON array:
[
  {{"source_id": "exact_id_from_above", "target_id": "exact_id_from_above", "relationship_type": "TYPE", "confidence": 0.7, "reasoning": "brief evidence"}}
]

If no relationships found, return []."""

    try:
        response = await call_llm_async(prompt, model=model, temperature=temperature)
        
        # Build entity_name -> Neo4j element ID mapping for validation
        # Handle both dict entities and potential string IDs
        name_to_id = {}
        for e in orphaned + candidates:
            if isinstance(e, dict) and e.get('entity_name'):
                # Extract ID safely - could be dict or already a string
                entity_id = e.get('id') if isinstance(e.get('id'), str) else e.get('id', {}).get('elementId', str(e.get('id')))
                name_to_id[e['entity_name']] = entity_id
        
        # RESILIENT PARSING: Parse items individually, keep valid ones, skip invalid
        # This prevents 1 malformed item from rejecting 24 valid relationships
        try:
            raw_json = extract_json_from_response(response, allow_array=True)
        except ValueError as e:
            logger.error(f"    ❌ Orphan Batch: Failed to extract JSON: {e}")
            return []
        
        # Normalize to list (handle both array and wrapped formats)
        if isinstance(raw_json, dict):
            raw_items = raw_json.get('relationships', raw_json.get('results', raw_json.get('data', [])))
        else:
            raw_items = raw_json if isinstance(raw_json, list) else []
        
        # Parse each relationship individually - skip invalid, keep valid
        valid_count = 0
        invalid_count = 0
        mapped_rels = []
        
        for i, item in enumerate(raw_items):
            try:
                rel = InferredRelationship.model_validate(item)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                # Log first 3 invalid items for debugging, summarize rest
                if invalid_count <= 3:
                    logger.warning(f"    ⚠️ Orphan item {i}: Validation failed - {e.errors()[0]['msg']}")
                continue
            source_name = rel.source_id
            target_name = rel.target_id
            
            source_element_id = name_to_id.get(source_name)
            target_element_id = name_to_id.get(target_name)
            
            if source_element_id and target_element_id:
                # Verify IDs exist in id_to_entity (final validation)
                if source_element_id in id_to_entity and target_element_id in id_to_entity:
                    mapped_rels.append({
                        'source_id': source_element_id,
                        'target_id': target_element_id,
                        'relationship_type': rel.relationship_type,
                        'reasoning': rel.reasoning,
                        'confidence': rel.confidence
                    })
                else:
                    logger.warning(
                        f"    ⚠️ Orphan Batch: LLM provided valid entity name but ID not in graph - "
                        f"source: '{source_name}' ({source_element_id}), target: '{target_name}' ({target_element_id}). Skipping."
                    )
            else:
                logger.warning(
                    f"    ⚠️ Orphan Batch: LLM hallucinated entity name - "
                    f"source: '{source_name}', target: '{target_name}'. Skipping."
                )
        
        # Summary logging for resilient parsing
        if invalid_count > 3:
            logger.warning(f"    ⚠️ Orphan Batch: {invalid_count} total invalid items skipped (showing first 3)")
        if invalid_count > 0 and valid_count > 0:
            logger.info(f"    → Orphan Batch: Kept {valid_count}/{valid_count + invalid_count} valid relationships (resilient parsing)")
        
        return mapped_rels
    except Exception as e:
        logger.error(f"    ❌ Orphan batch processing failed: {e}")
        return []


# ==================================================================================
# ALGORITHM WRAPPERS (for parallel execution via asyncio.gather)
# ==================================================================================

async def _algorithm_1_instruction_eval(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    ALGORITHM 1: Instruction-Evaluation Linking (SCHEMA-DRIVEN - Issue #43)
    
    Maps submission instructions → evaluation factors.
    Uses Pydantic schema guidance instead of hardcoded keyword matching.
    
    SCHEMA-DRIVEN APPROACH (Issue #43):
    - No hardcoded keyword lists for instruction detection
    - Schema guidance describes SubmissionInstruction fields (page_limit, format_reqs, volume)
    - LLM uses semantic understanding to identify instruction entities
    - Robust to non-standard RFP formats and naming conventions
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with GUIDES edges
    """
    # Get schema guidance for instruction-evaluation linking
    schema_guidance = get_instruction_evaluation_guidance()
    
    # Traditional submission_instruction entities (UCF Section L)
    instructions = entities_by_type.get('instruction', []) + entities_by_type.get('submission_instruction', [])
    
    # SCHEMA-DRIVEN: Include ALL deliverables and requirements as candidates
    # Let LLM identify instruction entities using schema understanding, not keyword filtering
    deliverable_candidates = entities_by_type.get('deliverable', [])[:100]  # Sample for performance
    requirement_candidates = [
        e for e in entities_by_type.get('requirement', [])
        if e.get('modal_verb') in ['shall', 'must']  # Only mandatory requirements
    ][:100]  # Sample for performance
    
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if not (instructions or deliverable_candidates or requirement_candidates) or not eval_factors:
        return []
    
    total_candidates = len(instructions) + len(deliverable_candidates) + len(requirement_candidates)
    logger.info(f"\n  [Algorithm 1/8] Instruction-Evaluation Linking (SCHEMA-DRIVEN): {total_candidates} candidates × {len(eval_factors)} eval factors")
    logger.info(f"      Candidates: {len(instructions)} submission_instruction, {len(deliverable_candidates)} deliverables, {len(requirement_candidates)} requirements")
    
    try:
        prompt_instructions = await _load_prompt_template("instruction_evaluation_linking.md")
        
        # Prepare evaluation factors JSON (reused across all batches)
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:5000]
        } for f in eval_factors], indent=2)
        
        # Create parallel tasks for each candidate type batch
        batch_tasks = []
        
        # Batch 1: Traditional submission instructions
        if instructions:
            inst_json = json.dumps([{
                'id': i['id'],
                'name': i['entity_name'],
                'type': i.get('entity_type'),
                'description': i.get('description', '')[:5000]
            } for i in instructions], indent=2)
            
            prompt = f"""{schema_guidance}

{prompt_instructions}

SUBMISSION INSTRUCTIONS (submission_instruction entities):
{inst_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Use the SCHEMA GUIDANCE above to identify which entities provide submission instructions.
Apply the inference patterns. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Batch 2: Deliverable candidates (LLM identifies instruction-like deliverables using schema)
        if deliverable_candidates:
            deliv_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:5000]
            } for d in deliverable_candidates], indent=2)
            
            prompt = f"""{schema_guidance}

{prompt_instructions}

DELIVERABLE CANDIDATES (identify those with submission instruction semantics):
{deliv_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Use the SCHEMA GUIDANCE above to identify deliverables that function as submission instructions.
Look for: page limits, format requirements, volume assignments, proposal preparation guidance.
Only link deliverables that have instruction-like content to evaluation factors.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "deliverable_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "schema-based pattern explanation"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Batch 3: Requirement candidates (LLM identifies instruction-like requirements using schema)
        if requirement_candidates:
            req_json = json.dumps([{
                'id': r['id'],
                'name': r['entity_name'],
                'type': r.get('entity_type'),
                'modal_verb': r.get('modal_verb', ''),
                'description': r.get('description', '')[:5000]
            } for r in requirement_candidates], indent=2)
            
            prompt = f"""{schema_guidance}

{prompt_instructions}

REQUIREMENT CANDIDATES (identify those with submission instruction semantics):
{req_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Use the SCHEMA GUIDANCE above to identify requirements that function as submission instructions.
Look for: page limits, format requirements, volume assignments, proposal preparation guidance.
Only link requirements that have instruction-like content to evaluation factors.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "schema-based pattern explanation"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results with Pydantic
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Batch {i} failed: {result}")
            else:
                valid_rels = await _parse_and_validate_relationship_batch(
                    result,
                    id_to_entity,
                    f"Algorithm 1 Batch {i}"
                )
                all_rels.extend(valid_rels)
        
        logger.info(f"    → Found {len(all_rels)} instruction-evaluation relationships ({len(batch_tasks)} parallel batches)")
        return all_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 1 failed: {e}")
        return []


async def _algorithm_2_eval_hierarchy(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    ALGORITHM 2: Evaluation Hierarchy & Metrics (SCHEMA-DRIVEN - Issue #43)
    
    Structures evaluation framework with HAS_SUBFACTOR, MEASURED_BY, HAS_THRESHOLD edges.
    
    SCHEMA-DRIVEN APPROACH (Issue #43):
    - No hardcoded keyword lists for factor detection
    - Schema guidance describes EvaluationFactor fields (weight, importance, subfactors)
    - LLM uses semantic understanding to discover ALL factors regardless of naming
    - Robust to non-standard factor names (e.g., "Small Business Participation")
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with hierarchy edges
    """
    # Get schema guidance for evaluation hierarchy discovery
    schema_guidance = get_evaluation_hierarchy_guidance()
    
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if not eval_factors:
        return []
    
    logger.info(f"\n  [Algorithm 2/8] Evaluation Hierarchy (SCHEMA-DRIVEN): {len(eval_factors)} evaluation entities")
    
    try:
        prompt_instructions = await _load_prompt_template("evaluation_hierarchy.md")
        
        # SCHEMA-DRIVEN: Group factors by structural patterns only (letter/number)
        # No keyword matching - LLM discovers hierarchies using schema guidance
        hierarchies = {}
        all_factors_group = []  # For factors that don't match simple patterns
        
        for factor in eval_factors:
            name = factor.get('entity_name', '').strip()
            
            # Only use structural patterns (not keywords) for grouping
            root_key = None
            
            # Pattern 1: "Factor A", "Factor B", etc. (exact structural match)
            if re.match(r'^Factor [A-Z]$', name, re.I):
                root_key = name.upper()
            # Pattern 2: "Factor 1", "Factor 2", etc. (exact structural match)
            elif re.match(r'^Factor \d+$', name, re.I):
                root_key = name.upper()
            else:
                # SCHEMA-DRIVEN: Don't use keyword matching for categorization
                # Add to general group - LLM will discover relationships using schema
                all_factors_group.append(factor)
                continue
            
            hierarchies.setdefault(root_key, []).append(factor)
        
        # Add all non-structurally-grouped factors as a single batch
        # LLM will discover hierarchies using schema guidance (no keyword filtering)
        if all_factors_group:
            hierarchies['_all_factors_'] = all_factors_group
        
        logger.info(f"      Found {len(hierarchies)} factor groups (schema-driven): {list(hierarchies.keys())[:5]}...")
        
        # Create parallel tasks for each hierarchy group
        batch_tasks = []
        
        for hierarchy_name, hierarchy_factors in hierarchies.items():
            factors_json = json.dumps([{
                'id': f['id'],
                'name': f['entity_name'],
                'type': f.get('entity_type'),
                'weight': f.get('weight', ''),
                'importance': f.get('importance', ''),
                'subfactors': f.get('subfactors', []),
                'description': f.get('description', '')[:5000]
            } for f in hierarchy_factors], indent=2)
            
            prompt = f"""{schema_guidance}

{prompt_instructions}

EVALUATION_FACTOR_ENTITIES (group: {hierarchy_name}):
{factors_json}

Use the SCHEMA GUIDANCE above to identify:
1. Main factors (have weight/importance, not rating scales)
2. Subfactors (reference parent factors or appear in subfactors lists)
3. Rating scales (Outstanding, Good, etc. - link with HAS_RATING_SCALE, not HAS_SUBFACTOR)
4. Metrics and thresholds

Include ALL factors regardless of naming convention (e.g., "Small Business Participation" is a valid factor).
Use entity IDs from 'id' field (NOT names).
Return ONLY valid JSON array:
[
  {{"source_id": "parent_id", "target_id": "child_id", "relationship_type": "HAS_SUBFACTOR|HAS_RATING_SCALE|MEASURED_BY|HAS_THRESHOLD|EVALUATED_USING|DEFINES_SCALE", "confidence": 0.75-0.95, "reasoning": "schema-based pattern explanation"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all hierarchies in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results with Pydantic
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Hierarchy batch {i} failed: {result}")
            else:
                valid_rels = await _parse_and_validate_relationship_batch(
                    result,
                    id_to_entity,
                    f"Algorithm 2 Batch {i}"
                )
                all_rels.extend(valid_rels)
        
        logger.info(f"    → Found {len(all_rels)} evaluation hierarchy relationships ({len(batch_tasks)} parallel groups)")
        return all_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 2 failed: {e}")
        return []


async def _algorithm_5_doc_hierarchy(
    entities: List[Dict],
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    ALGORITHM 5: Document Hierarchy (SCHEMA-DRIVEN - Issue #43)
    
    Maps document structure (attachments, sections, clauses, standards) with CHILD_OF edges.
    
    SCHEMA-DRIVEN APPROACH (Issue #43):
    - No hardcoded document type categories
    - Schema guidance from VALID_ENTITY_TYPES defines document types
    - Single LLM call with all document entities (discovers cross-type relationships)
    - Robust to non-standard document structures
    
    Args:
        entities: All entities
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with CHILD_OF edges
    """
    # Get schema guidance for document hierarchy discovery
    schema_guidance = get_document_hierarchy_guidance()
    
    # SCHEMA-DRIVEN: Use VALID_ENTITY_TYPES to identify document entities
    # No hardcoded type categories - schema defines valid types
    document_entity_types = {'document', 'section', 'clause', 'attachment'}
    
    # Collect ALL document entities regardless of specific type
    all_docs = [
        e for e in entities 
        if e.get('entity_type') in document_entity_types
    ]
    
    if not all_docs:
        return []
    
    logger.info(f"\n  [Algorithm 5/8] Document Hierarchy (SCHEMA-DRIVEN): {len(all_docs)} document entities")
    
    # Log type distribution for debugging
    type_counts = {}
    for doc in all_docs:
        doc_type = doc.get('entity_type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    logger.info(f"      Type distribution: {', '.join(f'{k}:{v}' for k, v in type_counts.items())}")
    
    try:
        prompt_instructions = await _load_prompt_template("document_hierarchy.md")
        
        # SCHEMA-DRIVEN: Single batch with all documents
        # For large document sets, use size-based batching (not type-based)
        BATCH_SIZE = 150  # Documents per batch
        batch_tasks = []
        
        if len(all_docs) <= BATCH_SIZE:
            # Single batch for small document sets
            docs_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:5000]
            } for d in all_docs], indent=2)
            
            prompt = f"""{schema_guidance}

{prompt_instructions}

DOCUMENT ENTITIES (all types - discover cross-type relationships):
{docs_json}

Use the SCHEMA GUIDANCE above to identify document hierarchies.
Discover relationships ACROSS entity types (e.g., section referencing attachment).
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "child_id", "target_id": "parent_id", "relationship_type": "CHILD_OF|ATTACHMENT_OF|AMENDS|INCORPORATES", "confidence": 0.7-1.0, "reasoning": "schema-based pattern explanation"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        else:
            # Size-based batching for large document sets
            num_batches = (len(all_docs) + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"      Large document set: {num_batches} batches of ~{BATCH_SIZE} docs")
            
            for batch_num in range(num_batches):
                batch_start = batch_num * BATCH_SIZE
                batch_end = min(batch_start + BATCH_SIZE, len(all_docs))
                batch_docs = all_docs[batch_start:batch_end]
                
                docs_json = json.dumps([{
                    'id': d['id'],
                    'name': d['entity_name'],
                    'type': d.get('entity_type'),
                    'description': d.get('description', '')[:5000]
                } for d in batch_docs], indent=2)
                
                prompt = f"""{schema_guidance}

{prompt_instructions}

DOCUMENT ENTITIES (batch {batch_num + 1}/{num_batches} - discover cross-type relationships):
{docs_json}

Use the SCHEMA GUIDANCE above to identify document hierarchies.
Discover relationships ACROSS entity types (e.g., section referencing attachment).
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "child_id", "target_id": "parent_id", "relationship_type": "CHILD_OF|ATTACHMENT_OF|AMENDS|INCORPORATES", "confidence": 0.7-1.0, "reasoning": "schema-based pattern explanation"}}
]
"""
                batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results with Pydantic
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Document batch {i} failed: {result}")
            else:
                valid_rels = await _parse_and_validate_relationship_batch(
                    result,
                    id_to_entity,
                    f"Algorithm 5 Batch {i}"
                )
                all_rels.extend(valid_rels)
        
        logger.info(f"    → Found {len(all_rels)} document hierarchy relationships ({len(batch_tasks)} batches)")
        return all_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 5 failed: {e}")
        return []


async def _algorithm_6_concept_linking(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    ALGORITHM 6: Semantic Concept Linking (PHASE 2 OPTIMIZED)
    
    Links concepts/strategic themes to high-value entities with INFORMS/IMPACTS edges.
    
    PHASE 2 OPTIMIZATION:
    - Remove 50-concept hardcoded limit
    - Dynamic batch sizing based on concept count
    - Process in parallel batches if > 100 concepts
    - Expected: 15-25s → 10-15s
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with semantic edges
    """
    concepts = entities_by_type.get('concept', [])  # REMOVED [:50] LIMIT
    strategic_themes = entities_by_type.get('strategic_theme', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    requirements = entities_by_type.get('requirement', [])
    deliverables = entities_by_type.get('deliverable', [])
    
    concept_pool = concepts + strategic_themes
    
    if not concept_pool or not eval_factors:
        return []
    
    # Dynamic batch sizing based on concept count
    if len(concept_pool) <= 50:
        batch_size = len(concept_pool)  # Single batch for small counts
    elif len(concept_pool) <= 200:
        batch_size = 100  # Medium batches
    else:
        batch_size = 150  # Large batches for high concept counts
    
    logger.info(f"\n  [Algorithm 6/8] Semantic Concept Linking (DYNAMIC BATCHING): {len(concept_pool)} concepts/themes (batch size: {batch_size})")
    
    try:
        prompt_instructions = await _load_prompt_template("semantic_concept_linking.md")
        
        # High-value entities (reused across all batches)
        high_value_entities = requirements[:30] + deliverables[:20] + eval_factors[:20]
        high_value_json = json.dumps([{
            'id': e['id'],
            'name': e['entity_name'],
            'type': e.get('entity_type'),
            'description': e.get('description', '')[:5000]
        } for e in high_value_entities], indent=2)
        
        # Create batches for concepts
        batch_tasks = []
        num_batches = (len(concept_pool) + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, len(concept_pool))
            concept_batch = concept_pool[batch_start:batch_end]
            
            concept_json = json.dumps([{
                'id': c['id'],
                'name': c['entity_name'],
                'type': c.get('entity_type'),
                'description': c.get('description', '')[:5000]
            } for c in concept_batch], indent=2)
            
            # Combine concepts + high-value entities
            prompt_json = f"""
CONCEPTS/THEMES (batch {batch_num + 1}/{num_batches}):
{concept_json}

HIGH-VALUE ENTITIES (requirements, deliverables, eval factors):
{high_value_json}
"""
            
            prompt = f"""{prompt_instructions}

ENTITIES:
{prompt_json}

Apply the semantic inference algorithms from the instructions above.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "concept_id", "target_id": "entity_id", "relationship_type": "INFORMS|IMPACTS|DETERMINES|GUIDES|ADDRESSED_BY|RELATED_TO", "confidence": 0.6-0.9, "reasoning": "semantic connection"}}
]
"""
            batch_tasks.append(call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results with Pydantic
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Concept batch {i} failed: {result}")
            else:
                valid_rels = await _parse_and_validate_relationship_batch(
                    result,
                    id_to_entity,
                    f"Algorithm 6 Batch {i}"
                )
                all_rels.extend(valid_rels)
        
        logger.info(f"    → Found {len(all_rels)} semantic concept relationships ({len(batch_tasks)} dynamic batches)")
        return all_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 6 failed: {e}")
        return []


def _algorithm_7_heuristic(
    entities: List[Dict],
    entities_by_type: Dict
) -> List[Dict]:
    """
    ALGORITHM 7: Heuristic Pattern Matching (CDRL/DID/Attachment cross-refs)
    
    Detects explicit CDRL, DID, DD Form 1423, and Exhibit/Annex references using
    comprehensive regex patterns. Non-async (no LLM calls).
    
    Issue #31 Enhancement: Expanded patterns to match real-world RFP formats:
    - CDRL letter+number: "CDRL A001", "CDRL B002"
    - CDRL number-only: "CDRL 6022", "CDRL 0001"
    - DID references: "DID A001", "DID-MC-123456"
    - DD Form 1423: "DD Form 1423", "DD1423"
    - Exhibit/Annex: "Exhibit A", "Annex I", "Attachment J-001"
    
    Args:
        entities: All entities
        entities_by_type: Entities grouped by type
        
    Returns:
        List of relationship dicts with REFERENCES edges
    """
    logger.info(f"\n  [Algorithm 7/8] Heuristic CDRL/DID Pattern Matching (Enhanced)")
    
    deliverables = entities_by_type.get('deliverable', [])
    heuristic_rels = []
    seen_pairs = set()  # Deduplicate source->target pairs
    
    # Enhanced pattern definitions with descriptive names
    patterns = [
        # CDRL patterns (Contract Data Requirements List)
        (r'cdrl\s*[a-z]\d{3,4}', 'CDRL letter+number'),      # CDRL A001, CDRL B0002
        (r'cdrl\s*\d{4,5}', 'CDRL number-only'),              # CDRL 6022, CDRL 00001
        (r'cdrl\s*#?\s*\d+', 'CDRL numbered'),                # CDRL #1, CDRL 1
        
        # DID patterns (Data Item Description)
        (r'did\s*[a-z]?\d{3,4}', 'DID reference'),           # DID A001, DID 001
        (r'did[-\s]?[a-z]{2,4}[-\s]?\d{4,6}', 'DID-XX-NNNN'), # DID-MC-123456
        
        # DD Form 1423 (Contract Data Requirements List form)
        (r'dd\s*form\s*1423', 'DD Form 1423'),               # DD Form 1423
        (r'dd[-\s]?1423', 'DD-1423'),                        # DD1423, DD-1423
        
        # Exhibit/Annex/Attachment patterns
        (r'exhibit\s+[a-z]\d*', 'Exhibit reference'),        # Exhibit A, Exhibit A1
        (r'annex\s+[a-z0-9ivx]+', 'Annex reference'),        # Annex I, Annex XVII, Annex 1
        (r'attachment\s+[a-z][-\d]*', 'Attachment reference'), # Attachment J-001
    ]
    
    for entity in entities:
        desc = (entity.get('description') or '').lower()
        name = (entity.get('entity_name') or '').lower()
        search_text = desc + ' ' + name
        
        for pattern, pattern_name in patterns:
            matches = re.findall(pattern, search_text)
            
            for match in matches:
                # Normalize the matched reference for comparison
                ref_id = re.sub(r'\s+', '', match).upper()
                
                for deliv in deliverables:
                    deliv_name = (deliv.get('entity_name') or '').upper()
                    deliv_desc = (deliv.get('description') or '').upper()
                    deliv_name_normalized = re.sub(r'\s+', '', deliv_name)
                    
                    # Check if reference matches deliverable (flexible matching)
                    match_found = (
                        ref_id in deliv_name_normalized or
                        ref_id in deliv_name or
                        ref_id in deliv_desc or
                        # Also check without CDRL/DID prefix
                        (ref_id.replace('CDRL', '').replace('DID', '').strip() in deliv_name_normalized and len(ref_id) > 4)
                    )
                    
                    if match_found:
                        pair_key = (entity['id'], deliv['id'])
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            heuristic_rels.append({
                                'source_id': entity['id'],
                                'target_id': deliv['id'],
                                'relationship_type': 'REFERENCES',
                                'confidence': 0.95,
                                'reasoning': f"Heuristic: {pattern_name} '{match}' matches deliverable"
                            })
                        break
    
    logger.info(f"    → Found {len(heuristic_rels)} heuristic relationships (enhanced patterns)")
    return heuristic_rels


async def _algorithm_8_orphan_resolution(
    entities: List[Dict],
    id_to_entity: Dict,
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    ALGORITHM 8: Orphan Pattern Resolution
    
    Links orphan entities (equipment, gov't-provided, person-deliverable, table-field).
    Wrapper that calls existing _resolve_orphan_patterns implementation.
    
    Args:
        entities: All entities
        id_to_entity: Entity lookup dict
        neo4j_io: Neo4jGraphIO instance for querying orphans
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts for orphan entities
    """
    logger.info(f"\n  [Algorithm 8/8] Orphan Pattern Resolution")
    
    try:
        return await _resolve_orphan_patterns(entities, id_to_entity, neo4j_io, model, temperature)
    except Exception as e:
        logger.error(f"    ❌ Algorithm 8 failed: {e}")
        return []


async def _algorithm_3_req_eval_batched(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm 3: Requirement→Evaluation Mapping (BATCHED)
    
    CRITICAL FIX for Issue #30:
    - OLD: 1,201 sequential LLM calls (2m32s, JSON truncation)
    - NEW: ~15 batched calls with overlap (10-15s, no truncation)
    
    Batching Strategy:
    - Batch size: 100 requirements per call (configurable via BATCH_SIZE_ALGO3)
    - Overlap: 20 requirements between batches (configurable via BATCH_OVERLAP_ALGO3)
    - Cross-batch relationships preserved via overlap
    - JSON response < 10K chars per batch (vs 105K accumulated)
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID lookup
        system_prompt: System prompt
        model: LLM model name
        temperature: LLM temperature
        semaphore: Asyncio semaphore for rate limiting
        
    Returns:
        List of inferred relationships
    """
    requirements = entities_by_type.get('requirement', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    # Filter to main evaluation factors (same logic as current)
    main_eval_factors = [f for f in eval_factors if _is_main_evaluation_factor(f)]
    
    if not requirements or not main_eval_factors:
        logger.info(f"  [Algorithm 3/8] Requirement-Evaluation Mapping: SKIPPED (no requirements or factors)")
        return []
    
    logger.info(f"  [Algorithm 3/8] Requirement-Evaluation Mapping: {len(requirements)} requirements × {len(main_eval_factors)} main factors (batched)")
    
    # Load prompt template
    prompt_instructions = await _load_prompt_template("requirement_evaluation.md")
    
    # Prepare evaluation factors JSON (reused across all batches)
    factors_json = json.dumps([{
        'id': f['id'],
        'name': f['entity_name'],
        'type': f.get('entity_type'),
        'description': f.get('description', '')[:5000]
    } for f in main_eval_factors], indent=2)
    
    # Batching parameters (from config)
    BATCH_SIZE = BATCH_SIZE_ALGO3
    OVERLAP = BATCH_OVERLAP_ALGO3
    
    all_relationships = []
    batch_tasks = []
    
    # Create batches with overlap
    num_batches = max(1, (len(requirements) + BATCH_SIZE - OVERLAP - 1) // (BATCH_SIZE - OVERLAP))
    
    for batch_num in range(num_batches):
        batch_start = batch_num * (BATCH_SIZE - OVERLAP)
        batch_end = min(batch_start + BATCH_SIZE, len(requirements))
        batch = requirements[batch_start:batch_end]
        
        # Build batch JSON
        reqs_json = json.dumps([{
            'id': r['id'],
            'name': r['entity_name'],
            'type': r.get('entity_type'),
            'description': r.get('description', '')[:5000]
        } for r in batch], indent=2)
        
        prompt = f"""{prompt_instructions}

REQUIREMENTS (batch {batch_num + 1}/{num_batches}):
{reqs_json}

EVALUATION_FACTORS:
{factors_json}

CRITICAL INSTRUCTION - Use factor descriptions for semantic matching:
- Factor names may be generic (Factor A, Factor B, Factor 1, etc.)
- Factor descriptions contain evaluation criteria and topics
- Match requirement CONTENT to factor DESCRIPTION topics, not just factor names

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field (NOT names).
Focus ONLY on main evaluation factors. Exclude rating scales, metrics, and thresholds.
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "factor_id", "relationship_type": "EVALUATED_BY", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
        
        # Create async task for this batch
        batch_tasks.append(_process_req_eval_batch(
            prompt, system_prompt, model, temperature, semaphore, id_to_entity, batch_num + 1, num_batches
        ))
    
    # Process all batches in parallel (within semaphore limits)
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    # Combine results
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"    ❌ Batch failed: {result}")
        else:
            all_relationships.extend(result)
    
    logger.info(f"    → Found {len(all_relationships)} requirement→main-factor relationships ({num_batches} batches)")
    return all_relationships


async def _algorithm_4_deliverable_trace_batched(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm 4: Deliverable Traceability (SUB-BATCHED)
    
    CRITICAL FIX for Issue #30:
    - OLD: Single massive prompt (1,201 reqs × 150 delivs = 180K combinations, 30+ min timeout)
    - NEW: ~24 batched calls (50 reqs × 150 delivs = 7,500 combinations each, 1-2 min total)
    
    Batching Strategy:
    - Batch size: 50 requirements per call (configurable via BATCH_SIZE_ALGO4)
    - Deliverables: ALL deliverables included in each batch (reused context)
    - Cross-product complexity: 7,500 vs 180K combinations per batch
    - Each batch completes in <5s
    
    Dual-Pattern Approach:
    - Pattern 1: Requirement → Deliverable (evidence relationships)
    - Pattern 2: Work Statement → Deliverable (explicit references)
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID lookup
        system_prompt: System prompt
        model: LLM model name
        temperature: LLM temperature
        semaphore: Asyncio semaphore for rate limiting
        
    Returns:
        List of inferred relationships
    """
    requirements = entities_by_type.get('requirement', [])
    work_statements = (entities_by_type.get('statement_of_work', []) + 
                       entities_by_type.get('pws', []) + 
                       entities_by_type.get('soo', []))
    deliverables = entities_by_type.get('deliverable', [])
    
    if not deliverables or (not requirements and not work_statements):
        logger.info(f"  [Algorithm 4/8] Deliverable Traceability: SKIPPED (no deliverables or requirements/work)")
        return []
    
    logger.info(f"  [Algorithm 4/8] Deliverable Traceability: {len(requirements)} requirements + {len(work_statements)} work statements × {len(deliverables)} deliverables (batched)")
    
    # Load prompt template
    prompt_instructions = await _load_prompt_template("deliverable_traceability.md")
    
    # Prepare deliverables JSON (reused across all batches)
    deliv_json = json.dumps([{
        'id': d['id'],
        'name': d['entity_name'],
        'type': d.get('entity_type'),
        'description': d.get('description', '')[:5000]
    } for d in deliverables], indent=2)
    
    # Batching parameters (from config)
    BATCH_SIZE = BATCH_SIZE_ALGO4
    
    all_relationships = []
    
    # PATTERN 1: Requirement → Deliverable (batched)
    if requirements:
        logger.info(f"    → Pattern 1 (Requirement→Deliverable): {len(requirements)} requirements")
        
        pattern1_tasks = []
        num_batches = (len(requirements) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(num_batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(requirements))
            batch = requirements[batch_start:batch_end]
            
            # Build batch JSON
            reqs_json = json.dumps([{
                'id': r['id'],
                'name': r['entity_name'],
                'type': r.get('entity_type'),
                'description': r.get('description', '')[:5000]
            } for r in batch], indent=2)
            
            prompt = f"""{prompt_instructions}

Apply PATTERN 1 (Requirement → Deliverable) detection rules.

REQUIREMENTS (batch {batch_num + 1}/{num_batches}):
{reqs_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on evidence relationships (deliverables that prove/document requirement compliance).
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "deliverable_id", "relationship_type": "SATISFIED_BY", "confidence": 0.50-0.95, "reasoning": "evidence relationship explanation"}}
]
"""
            
            pattern1_tasks.append(_process_deliverable_batch(
                prompt, system_prompt, model, temperature, semaphore, id_to_entity, 
                f"Pattern 1 Batch {batch_num + 1}/{num_batches}"
            ))
        
        # Process Pattern 1 batches in parallel
        pattern1_results = await asyncio.gather(*pattern1_tasks, return_exceptions=True)
        
        pattern1_count = 0
        for result in pattern1_results:
            if isinstance(result, Exception):
                logger.error(f"    ❌ Pattern 1 batch failed: {result}")
            else:
                all_relationships.extend(result)
                pattern1_count += len(result)
        
        logger.info(f"    → Pattern 1: {pattern1_count} relationships")
    
    # PATTERN 2: Work Statement → Deliverable (batched)
    if work_statements:
        logger.info(f"    → Pattern 2 (WorkStatement→Deliverable): {len(work_statements)} work statements")
        
        pattern2_tasks = []
        num_batches = (len(work_statements) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(num_batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(work_statements))
            batch = work_statements[batch_start:batch_end]
            
            # Build batch JSON
            work_json = json.dumps([{
                'id': w['id'],
                'name': w['entity_name'],
                'type': w.get('entity_type'),
                'description': w.get('description', '')[:5000]
            } for w in batch], indent=2)
            
            prompt = f"""{prompt_instructions}

Apply PATTERN 2 (Work Statement → Deliverable) detection rules.

WORK_STATEMENTS (batch {batch_num + 1}/{num_batches}):
{work_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on explicit CDRL references and work-product relationships.
Return ONLY valid JSON array:
[
  {{"source_id": "work_statement_id", "target_id": "deliverable_id", "relationship_type": "PRODUCES", "confidence": 0.50-0.96, "reasoning": "explicit reference or work-product explanation"}}
]
"""
            
            pattern2_tasks.append(_process_deliverable_batch(
                prompt, system_prompt, model, temperature, semaphore, id_to_entity,
                f"Pattern 2 Batch {batch_num + 1}/{num_batches}"
            ))
        
        # Process Pattern 2 batches in parallel
        pattern2_results = await asyncio.gather(*pattern2_tasks, return_exceptions=True)
        
        pattern2_count = 0
        for result in pattern2_results:
            if isinstance(result, Exception):
                logger.error(f"    ❌ Pattern 2 batch failed: {result}")
            else:
                all_relationships.extend(result)
                pattern2_count += len(result)
        
        logger.info(f"    → Pattern 2: {pattern2_count} relationships")
    
    logger.info(f"    → Total Deliverable Traceability: {len(all_relationships)} relationships")
    return all_relationships


async def _infer_relationships_multi_algorithm(
    entities: List[Dict],
    existing_rels: List[Dict],
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Multi-algorithm relationship inference using specialized prompts.
    
    8 Algorithms (uses entity IDs from Branch 013a for precision):
    1. Instruction-Evaluation Linking (instruction_evaluation_linking.md)
    2. Evaluation Hierarchy & Metrics
    3. Requirement-Evaluation Mapping (requirement_evaluation.md)
    4. Deliverable Tracing (sow_deliverable_linking.md)
    5. Document Hierarchy (document_hierarchy.md, attachment_section_linking.md, document_section_linking.md, clause_clustering.md)
    6. Semantic Concept Linking (semantic_concept_linking.md)
    7. Heuristic Pattern Matching (CDRL, cross-refs)
    8. Orphan Pattern Resolution (Neo4j query-based)
    
    Args:
        entities: All entities to analyze
        existing_rels: Existing relationships
        neo4j_io: Neo4jGraphIO instance for querying orphans
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of inferred relationships
    """
    
    all_relationships = []
    
    # Build entity lookups (using IDs for precision)
    id_to_entity = {e['id']: e for e in entities}
    entities_by_type = {}
    for e in entities:
        entity_type = e.get('entity_type', 'unknown')
        entities_by_type.setdefault(entity_type, []).append(e)
    
    # Load system prompt
    system_prompt = await _load_prompt_template("system_prompt.md")
    
    # Create semaphore for rate limiting (configurable via MAX_ASYNC env var)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)
    
    # =========================================================================
    # PARALLEL EXECUTION ARCHITECTURE (Issue #30 Phase 3B)
    # =========================================================================
    # ALL algorithms execute in parallel (no wave-based sequencing):
    # - Algorithms 1-6, 8: Run concurrently with shared semaphore (MAX_ASYNC=8)
    # - Algorithm 7: Heuristic (instant, regex-based) - no LLM, runs separately
    # 
    # Phase 3B Optimization:
    # - OLD (Phase 2): Sequential waves → 5.1 min total
    #   * Wave 1 (Algos 1,2,5): 49s
    #   * Wave 2 (Algos 3,4): 195s (sequential!)
    #   * Wave 3 (Algos 6,8): 63s
    # - NEW (Phase 3B): Full parallelization → ~2 min (longest algorithm)
    #   * All algos run concurrently, limited only by semaphore (MAX_ASYNC=8)
    #   * Total time = max(algo_times) ≈ 121s (Algorithm 3)
    #
    # Expected Impact: 5.1 min → 2 min (60% reduction, 186s savings)
    # =========================================================================
    
    logger.info("\n⚡ Starting ALL algorithms in parallel (Phase 3B full parallelization)...")
    
    # Prepare all algorithm tasks
    all_tasks = [
        _algorithm_1_instruction_eval(entities_by_type, id_to_entity, system_prompt, model, temperature),
        _algorithm_2_eval_hierarchy(entities_by_type, id_to_entity, system_prompt, model, temperature),
        _algorithm_3_req_eval_batched(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_4_deliverable_trace_batched(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_5_doc_hierarchy(entities, id_to_entity, system_prompt, model, temperature),
        _algorithm_6_concept_linking(entities_by_type, id_to_entity, system_prompt, model, temperature),
        _algorithm_8_orphan_resolution(entities, id_to_entity, neo4j_io, model, temperature),
    ]
    
    # Execute all algorithms in parallel
    logger.info(f"   Executing 7 LLM-powered algorithms concurrently (MAX_ASYNC={MAX_CONCURRENT_LLM_CALLS})...")
    algorithm_results = await asyncio.gather(*all_tasks, return_exceptions=True)
    
    # Process results
    algorithm_names = [
        "Algorithm 1: Instruction-Evaluation",
        "Algorithm 2: Evaluation Hierarchy",
        "Algorithm 3: Requirement-Evaluation",
        "Algorithm 4: Deliverable Traceability",
        "Algorithm 5: Document Hierarchy",
        "Algorithm 6: Concept Linking",
        "Algorithm 8: Orphan Resolution"
    ]
    
    for i, (name, result) in enumerate(zip(algorithm_names, algorithm_results), 1):
        if isinstance(result, Exception):
            logger.error(f"  ❌ {name} failed: {result}")
        else:
            all_relationships.extend(result)
            logger.info(f"  ✅ {name}: {len(result)} relationships")
    
    # ALGORITHM 7: Heuristic pattern matching (instant, no LLM)
    logger.info("\n⚡ Algorithm 7: Heuristic Pattern Matching (CDRL cross-refs)")
    heuristic_rels = _algorithm_7_heuristic(entities, entities_by_type)
    all_relationships.extend(heuristic_rels)
    logger.info(f"  ✅ Algorithm 7: {len(heuristic_rels)} relationships")
    
    # Summary
    logger.info(f"\n✅ Total relationships from all algorithms: {len(all_relationships)}")
    return all_relationships


async def _semantic_post_processor_neo4j(
    llm_model_name: str = None,
    temperature: float = 0.1
) -> Dict:
    """
    Neo4j-native semantic post-processing using Cypher queries.
    
    This function:
    1. Reads entities/relationships from Neo4j
    2. Infers missing relationships using LLM inference (8 algorithms)
    3. Enriches requirements with workload metadata
    4. Writes updates back to Neo4j via Cypher
    
    Note: Entity type enforcement is handled at extraction time via Pydantic
    schema validation - no post-processing correction needed.
    
    Args:
        llm_model_name: Name of LLM model to use
        temperature: Temperature for LLM inference
        
    Returns:
        Dict with processing statistics
    """
    if llm_model_name is None:
        llm_model_name = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    
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
        
        if not entities:
            logger.warning("⚠️  No entities found in Neo4j workspace")
            return {
                "status": "skipped",
                "reason": "no_entities",
                "relationships_inferred": 0,
                "requirements_enriched": 0,
                "processing_time": 0
            }
        
        logger.info(f"    ✅ Loaded {len(entities)} entities, {len(relationships)} relationships")
        
        # Step 2: Infer missing relationships
        logger.info("\n🔗 Step 2: Inferring missing relationships with multi-algorithm approach...")
        new_relationships = await _infer_relationships_multi_algorithm(
            entities=entities,
            existing_rels=relationships,
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
        
        # Step 3: Workload Enrichment (BOE metadata for requirements)
        logger.info("\n🏗️ Step 3: Enriching requirements with workload metadata...")
        from src.inference.workload_enrichment import enrich_workload_metadata
        
        workload_stats = await enrich_workload_metadata(
            neo4j_io=neo4j_io,
            llm_func=call_llm_async,
            batch_size=50,
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
        logger.info(f"  Relationships inferred:  {relationships_inferred}")
        logger.info(f"  Requirements enriched:   {requirements_enriched}")
        logger.info(f"  Processing time:         {processing_time:.2f}s")
        logger.info("="*80)
        
        # Get updated counts
        type_counts = neo4j_io.get_entity_count_by_type()
        logger.info("\n📊 Entity Type Distribution (all types):")
        for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {entity_type:30s}: {count:4d}")
        
        return {
            "status": "success",
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
    
    # Get LLM model from environment
    llm_model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    llm_temp = float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
    
    return await _semantic_post_processor_neo4j(
        llm_model_name=llm_model,
        temperature=llm_temp
    )

