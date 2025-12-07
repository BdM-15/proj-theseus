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
import json
import os
import re
import asyncio
from typing import Dict, Callable, Awaitable, List

from openai import AsyncOpenAI

from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type
from src.ontology.schema import VALID_ENTITY_TYPES

logger = logging.getLogger(__name__)

# Convert set to list for prompt generation
ALLOWED_TYPES = list(VALID_ENTITY_TYPES)

# Configuration for semantic post-processing optimization (Issue #30)
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_ASYNC", 4))
BATCH_SIZE_ALGO3 = int(os.getenv("BATCH_SIZE_ALGORITHM_3", 100))
BATCH_OVERLAP_ALGO3 = int(os.getenv("BATCH_OVERLAP_ALGORITHM_3", 20))
BATCH_SIZE_ALGO4 = int(os.getenv("BATCH_SIZE_ALGORITHM_4", 50))


async def _call_llm_async(prompt: str, system_prompt: str = None, model: str = None, temperature: float = 0.1) -> str:
    """Async wrapper for LLM calls using xAI endpoint directly
    
    Args:
        prompt: The user prompt to send
        system_prompt: Optional system prompt (if None, only sends user message)
        model: LLM model name (defaults to LLM_MODEL env var)
        temperature: Sampling temperature (default: 0.1)
    
    Returns:
        LLM response text
    """
    if model is None:
        model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    
    # Create AsyncOpenAI client with xAI endpoint
    client = AsyncOpenAI(
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    )
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    
    return response.choices[0].message.content


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
            response = await _call_llm_async(prompt, model=model, temperature=temperature)
            
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
    Validate and filter relationships to ensure required fields are present.
    
    Trust LLM semantic quality like LightRAG does - no confidence required.
    
    Args:
        rels: List of relationship dicts from LLM
        id_to_entity: Mapping of entity IDs to entities
        algorithm_name: Name of algorithm for logging
        
    Returns:
        List of valid relationships with required fields only
    """
    valid_rels = []
    for rel in rels:
        if (rel.get('source_id') in id_to_entity and 
            rel.get('target_id') in id_to_entity and 
            rel.get('relationship_type')):
            # Include only required fields - trust LLM inference quality
            valid_rel = {
                'source_id': rel['source_id'],
                'target_id': rel['target_id'],
                'relationship_type': rel['relationship_type'],
                'reasoning': rel.get('reasoning', '')
            }
            valid_rels.append(valid_rel)
        else:
            missing = []
            if not rel.get('source_id') or rel.get('source_id') not in id_to_entity:
                missing.append('source_id')
            if not rel.get('target_id') or rel.get('target_id') not in id_to_entity:
                missing.append('target_id')
            if not rel.get('relationship_type'):
                missing.append('relationship_type')
            logger.warning(f"    ⚠️ {algorithm_name}: Skipping malformed relationship (missing: {', '.join(missing)})")
    
    if len(rels) > len(valid_rels):
        logger.warning(f"    ⚠️ {algorithm_name}: Filtered out {len(rels) - len(valid_rels)} of {len(rels)} relationships")
    
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
    """Process single batch for Algorithm 3 (Requirement→Evaluation Mapping)"""
    try:
        async with semaphore:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        
        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 3 Batch {batch_num}/{total_batches}")
        return valid_rels
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
    """Process single batch for Algorithm 4 (Deliverable Traceability)"""
    try:
        async with semaphore:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        
        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 4 {batch_label}")
        return valid_rels
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
        return await _process_orphan_batch(orphaned, priority_candidates, id_to_entity, model, temperature)
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
                orphan_batch, priority_candidates, id_to_entity, model, temperature
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
    temperature: float
) -> List[Dict]:
    """
    Process a single batch of orphaned entities.
    
    Helper function for conditional batching in _resolve_orphan_patterns.
    """
    import json
    
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
    } for c in candidates], indent=2)
    
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
        response = await _call_llm_async(prompt, model=model, temperature=temperature)
        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, "Orphan Batch")
        return valid_rels
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
    ALGORITHM 1: Instruction-Evaluation Linking (PHASE 2 OPTIMIZED)
    
    Maps submission instructions → evaluation factors.
    Content-based agnostic search across instruction, deliverable, and requirement entities.
    
    PHASE 2 OPTIMIZATION:
    - Batch by instruction type (submission, deliverable, requirement)
    - Process batches in parallel
    - Expected: 15-30s → 10s
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with GUIDES edges
    """
    # Traditional submission_instruction entities (UCF Section L)
    instructions = entities_by_type.get('instruction', []) + entities_by_type.get('submission_instruction', [])
    
    # Agnostic: Deliverables with submission requirements
    deliverables_with_instructions = [
        e for e in entities_by_type.get('deliverable', [])
        if any(term in (str(e.get('description', '')) + str(e.get('entity_name', ''))).lower() 
               for term in ['submit', 'provide', 'page', 'format', 'volume', 'shall include', 
                           'maximum', 'minimum', 'font', 'address', 'respond'])
    ]
    
    # Agnostic: Requirements with submission verbs
    requirements_with_instructions = [
        e for e in entities_by_type.get('requirement', [])
        if e.get('modal_verb') in ['shall', 'must'] and 
           any(term in str(e.get('entity_name', '')).lower() 
               for term in ['submit', 'provide', 'proposal', 'response', 'volume', 
                           'page limit', 'format', 'electronic', 'hard copy'])
    ]
    
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if not (instructions or deliverables_with_instructions or requirements_with_instructions) or not eval_factors:
        return []
    
    total_instruction_entities = len(instructions) + len(deliverables_with_instructions) + len(requirements_with_instructions)
    logger.info(f"\n  [Algorithm 1/8] Instruction-Evaluation Linking (TYPE-BATCHED): {total_instruction_entities} instruction entities × {len(eval_factors)} eval factors")
    logger.info(f"      Batches: {len(instructions)} submission_instruction, {len(deliverables_with_instructions)} deliverables, {len(requirements_with_instructions)} requirements")
    
    try:
        prompt_instructions = await _load_prompt_template("instruction_evaluation_linking.md")
        
        # Prepare evaluation factors JSON (reused across all batches)
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:5000]
        } for f in eval_factors], indent=2)
        
        # Create parallel tasks for each instruction type batch
        batch_tasks = []
        
        # Batch 1: Traditional submission instructions
        if instructions:
            inst_json = json.dumps([{
                'id': i['id'],
                'name': i['entity_name'],
                'type': i.get('entity_type'),
                'description': i.get('description', '')[:5000]
            } for i in instructions], indent=2)
            
            prompt = f"""{prompt_instructions}

SUBMISSION INSTRUCTIONS (traditional):
{inst_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Batch 2: Deliverable-based instructions
        if deliverables_with_instructions:
            deliv_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:5000]
            } for d in deliverables_with_instructions], indent=2)
            
            prompt = f"""{prompt_instructions}

SUBMISSION INSTRUCTIONS (from deliverables):
{deliv_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Batch 3: Requirement-based instructions
        if requirements_with_instructions:
            req_json = json.dumps([{
                'id': r['id'],
                'name': r['entity_name'],
                'type': r.get('entity_type'),
                'description': r.get('description', '')[:5000]
            } for r in requirements_with_instructions], indent=2)
            
            prompt = f"""{prompt_instructions}

SUBMISSION INSTRUCTIONS (from requirements):
{req_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Batch {i} failed: {result}")
            else:
                try:
                    rels = json.loads(result.strip())
                    valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 1 Batch {i}")
                    all_rels.extend(valid_rels)
                except Exception as e:
                    logger.error(f"    ❌ Batch {i} parsing failed: {e}")
        
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
    ALGORITHM 2: Evaluation Hierarchy & Metrics (PHASE 2 OPTIMIZED)
    
    Structures evaluation framework with HAS_SUBFACTOR, MEASURED_BY, HAS_THRESHOLD edges.
    
    PHASE 2 OPTIMIZATION:
    - Group by root factor (Factor A, B, C hierarchies)
    - Process hierarchies independently in parallel
    - Expected: 10-20s → 5-8s
    
    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with hierarchy edges
    """
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if not eval_factors:
        return []
    
    logger.info(f"\n  [Algorithm 2/8] Evaluation Hierarchy (BATCHED BY ROOT FACTOR): {len(eval_factors)} evaluation entities")
    
    try:
        prompt_instructions = await _load_prompt_template("evaluation_hierarchy.md")
        
        # Group factors by root parent (e.g., "Factor A", "Factor 1", "Technical Factor")
        # Use simple heuristics: look for single-letter/number factors or top-level keywords
        hierarchies = {}
        orphan_factors = []
        
        for factor in eval_factors:
            name = factor.get('entity_name', '').strip()
            desc = factor.get('description', '').lower()
            
            # Try to identify root factor patterns
            root_key = None
            
            # Pattern 1: "Factor A", "Factor B", etc.
            if re.match(r'^Factor [A-Z]$', name, re.I):
                root_key = name.upper()
            # Pattern 2: "Factor 1", "Factor 2", etc.
            elif re.match(r'^Factor \d+$', name, re.I):
                root_key = name.upper()
            # Pattern 3: "Technical Factor", "Management Factor", etc.
            elif any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
                root_key = name.split()[0].upper()  # Use first word as key
            # Pattern 4: Sub-factors (contains "Sub", digit suffix, or is very long)
            elif 'sub' in name.lower() or re.search(r'[A-Z]\.\d+', name) or len(name) > 50:
                orphan_factors.append(factor)
                continue
            else:
                # Default: treat as independent root factor
                root_key = name[:20]  # Truncate for grouping
            
            hierarchies.setdefault(root_key, []).append(factor)
        
        # If we have orphans, add them as their own group
        if orphan_factors:
            hierarchies['_orphans_'] = orphan_factors
        
        logger.info(f"      Found {len(hierarchies)} root factor hierarchies: {list(hierarchies.keys())[:5]}...")
        
        # Create parallel tasks for each hierarchy
        batch_tasks = []
        
        for hierarchy_name, hierarchy_factors in hierarchies.items():
            factors_json = json.dumps([{
                'id': f['id'],
                'name': f['entity_name'],
                'type': f.get('entity_type'),
                'description': f.get('description', '')[:5000]
            } for f in hierarchy_factors], indent=2)
            
            prompt = f"""{prompt_instructions}

EVALUATION_FACTOR_ENTITIES (hierarchy: {hierarchy_name}):
{factors_json}

Apply the hierarchy inference patterns from the instructions above. Use entity IDs from 'id' field (NOT names).
Return ONLY valid JSON array:
[
  {{"source_id": "parent_id", "target_id": "child_id", "relationship_type": "HAS_SUBFACTOR|HAS_RATING_SCALE|MEASURED_BY|HAS_THRESHOLD|EVALUATED_USING|DEFINES_SCALE", "confidence": 0.75-0.95, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all hierarchies in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Hierarchy batch {i} failed: {result}")
            else:
                try:
                    rels = json.loads(result.strip())
                    valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 2 Batch {i}")
                    all_rels.extend(valid_rels)
                except Exception as e:
                    logger.error(f"    ❌ Hierarchy batch {i} parsing failed: {e}")
        
        logger.info(f"    → Found {len(all_rels)} evaluation hierarchy relationships ({len(batch_tasks)} parallel hierarchies)")
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
    ALGORITHM 5: Document Hierarchy (PHASE 2 OPTIMIZED)
    
    Maps document structure (attachments, sections, clauses, standards) with CHILD_OF edges.
    
    PHASE 2 OPTIMIZATION:
    - Group documents by type (attachments, sections, clauses, standards)
    - Process types in parallel
    - Expected: 10-15s → 5-8s
    
    Args:
        entities: All entities
        id_to_entity: Entity lookup dict
        system_prompt: System prompt for LLM
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationship dicts with CHILD_OF edges
    """
    # Document type taxonomy
    document_types = {
        'core_documents': ['document'],
        'sections': ['section'],
        'attachments': ['attachment', 'annex', 'exhibit'],
        'amendments': ['amendment'],
        'clauses': ['clause', 'standard', 'specification', 'regulation']
    }
    
    # Group documents by type category
    doc_groups = {}
    for category, types in document_types.items():
        docs = [e for e in entities if e.get('entity_type') in types]
        if docs:
            doc_groups[category] = docs
    
    if not doc_groups:
        return []
    
    total_docs = sum(len(docs) for docs in doc_groups.values())
    logger.info(f"\n  [Algorithm 5/8] Document Hierarchy (TYPE-BATCHED): {total_docs} document entities across {len(doc_groups)} type groups")
    logger.info(f"      Groups: {', '.join(f'{k}:{len(v)}' for k, v in doc_groups.items())}")
    
    try:
        prompt_instructions = await _load_prompt_template("document_hierarchy.md")
        
        # Create parallel tasks for each document type group
        batch_tasks = []
        
        for category, docs in doc_groups.items():
            docs_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:5000]
            } for d in docs], indent=2)
            
            prompt = f"""{prompt_instructions}

DOCUMENTS ({category}):
{docs_json}

Apply the inference patterns from the instructions above to identify document relationships within this type group.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "child_id", "target_id": "parent_id", "relationship_type": "CHILD_OF|ATTACHMENT_OF", "confidence": 0.7-1.0, "reasoning": "pattern explanation"}}
]
"""
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all document type groups in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Document type batch {i} failed: {result}")
            else:
                try:
                    rels = json.loads(result.strip())
                    valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 5 Batch {i}")
                    all_rels.extend(valid_rels)
                except Exception as e:
                    logger.error(f"    ❌ Document type batch {i} parsing failed: {e}")
        
        logger.info(f"    → Found {len(all_rels)} document hierarchy relationships ({len(batch_tasks)} parallel type groups)")
        return all_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 5 failed: {e}")
        return []
        return valid_rels
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
            batch_tasks.append(_call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature))
        
        # Process all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine and validate results
        all_rels = []
        for i, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                logger.error(f"    ❌ Concept batch {i} failed: {result}")
            else:
                try:
                    rels = json.loads(result.strip())
                    valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 6 Batch {i}")
                    all_rels.extend(valid_rels)
                except Exception as e:
                    logger.error(f"    ❌ Concept batch {i} parsing failed: {e}")
        
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
    ALGORITHM 7: Heuristic Pattern Matching (CDRL cross-refs)
    
    Detects explicit CDRL references using regex patterns. Non-async (no LLM calls).
    
    Args:
        entities: All entities
        entities_by_type: Entities grouped by type
        
    Returns:
        List of relationship dicts with REFERENCES edges
    """
    logger.info(f"\n  [Algorithm 7/8] Heuristic CDRL Pattern Matching")
    
    deliverables = entities_by_type.get('deliverable', [])
    heuristic_rels = []
    
    for entity in entities:
        desc = (entity.get('description') or '').lower()
        name = (entity.get('entity_name') or '').lower()
        
        # Pattern: CDRL cross-reference (e.g., "CDRL A001")
        cdrl_pattern = r'cdrl\s+[a-z]\d{3,4}'
        matches = re.findall(cdrl_pattern, desc + ' ' + name)
        
        for match in matches:
            cdrl_id = match.replace(' ', '').upper()
            for deliv in deliverables:
                if cdrl_id in (deliv.get('entity_name') or '').upper() or cdrl_id in (deliv.get('description') or '').upper():
                    heuristic_rels.append({
                        'source_id': entity['id'],
                        'target_id': deliv['id'],
                        'relationship_type': 'REFERENCES',
                        'confidence': 0.95,
                        'reasoning': f"Heuristic: Explicit CDRL cross-reference '{match}'"
                    })
                    break
    
    logger.info(f"    → Found {len(heuristic_rels)} heuristic relationships")
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
    import json
    
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
            llm_func=_call_llm_async,
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
        llm_func: Async LLM function (unused - we use internal _call_llm_async)
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

