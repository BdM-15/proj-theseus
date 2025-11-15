"""
Semantic Post-Processing for Government Contracting RFPs
========================================================

Coordinates all LLM-powered enhancements to the extracted knowledge graph:

1. **Entity Type Correction**: Fix UNKNOWN/forbidden entity types
2. **Relationship Inference**: Infer missing semantic relationships

This replaces the confusing "Phase 6" and "Phase 7" terminology with
clear, operation-based naming.

Usage:
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    
    stats = await enhance_knowledge_graph(
        graphml_path="path/to/graph.graphml",
        llm_func=my_llm_function
    )
"""

import logging
import time
from typing import Dict, Callable, Awaitable, List
from pathlib import Path

from src.inference.graph_io import parse_graphml, save_enhanced_graphml
from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type
from src.inference.entity_operations import ALLOWED_TYPES, FORBIDDEN_TYPES
from lightrag.llm.openai import openai_complete_if_cache
import os

logger = logging.getLogger(__name__)


async def _call_llm_async(prompt: str, system_prompt: str = None, model: str = "grok-4-fast-reasoning", temperature: float = 0.1) -> str:
    """Async wrapper for LLM calls"""
    return await openai_complete_if_cache(
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        hashing_kv=None,  # No caching for post-processing
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST"),
        temperature=temperature
    )


async def _infer_entity_type(entity_name: str, description: str, model: str, temperature: float) -> str:
    """Infer correct entity type for a single entity"""
    allowed_types_str = ", ".join(ALLOWED_TYPES)
    
    prompt = f"""You are a government contracting expert. Classify this entity into ONE of these types:
{allowed_types_str}

Entity Name: {entity_name}
Description: {description or 'No description'}

Return ONLY the entity type (lowercase with underscores). No explanation."""
    
    try:
        response = await _call_llm_async(prompt, model=model, temperature=temperature)
        new_type = response.strip().lower()
        
        # Validate it's an allowed type
        if new_type in ALLOWED_TYPES:
            return new_type
        else:
            logger.warning(f"  LLM returned invalid type '{new_type}' for {entity_name}, using 'concept'")
            return "concept"
    except Exception as e:
        logger.error(f"  Error inferring type for {entity_name}: {e}")
        return "concept"  # Default fallback


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
            f"{e['id']} | {e['entity_type']} | {e['entity_name']} | {e.get('description', '')[:80]}"
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
    
    Args:
        rels: List of relationship dicts from LLM
        id_to_entity: Mapping of entity IDs to entities
        algorithm_name: Name of algorithm for logging
        
    Returns:
        List of valid relationships with all required fields
    """
    valid_rels = []
    for rel in rels:
        if (rel.get('source_id') in id_to_entity and 
            rel.get('target_id') in id_to_entity and 
            rel.get('relationship_type')):
            valid_rels.append(rel)
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


async def _resolve_orphan_patterns(
    entities: List[Dict],
    id_to_entity: Dict[str, Dict],
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
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        List of relationships for orphan patterns
    """
    import json
    
    # Identify orphaned entities (entities with no relationships)
    # Note: In Neo4j, entities already have relationships stored, so we look for
    # entities that were never connected during Algorithms 1-7
    entity_ids_with_rels = set()
    
    # For each entity, check if it appears as source/target in any existing relationships
    # This is implicitly handled by Neo4j - entities without edges won't have relationship metadata
    # We rely on the fact that connected entities have relationship_type fields populated
    
    # Simple heuristic: Check if entity has minimal connections (0-1 relationships)
    # This catches true orphans and weakly connected entities that may need more links
    orphaned = []
    for entity in entities:
        # Count relationships this entity participates in
        # Neo4j entities store relationships in metadata
        rel_types = entity.get('relationships', [])
        if isinstance(rel_types, list) and len(rel_types) == 0:
            orphaned.append(entity)
    
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
        'description': o.get('description', '')[:300]
    } for o in orphaned], indent=2)
    
    candidate_json = json.dumps([{
        'id': c['id'],
        'name': c['entity_name'],
        'type': c.get('entity_type'),
        'description': c.get('description', '')[:200]
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

Use entity IDs from 'id' field. Focus on high-confidence relationships (>0.65).
Return ONLY valid JSON array:
[
  {{"source_id": "entity_id", "target_id": "entity_id", "relationship_type": "TYPE", "confidence": 0.65-0.95, "reasoning": "brief evidence"}}
]

If no relationships found, return []."""

    try:
        response = await _call_llm_async(prompt, model=model, temperature=temperature)
        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 8")
        logger.info(f"    → Found {len(valid_rels)} orphan relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 8 failed: {e}")
        return []


async def _infer_relationships_multi_algorithm(
    entities: List[Dict],
    existing_rels: List[Dict],
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Multi-algorithm relationship inference using specialized prompts.
    
    6 Algorithms (uses entity IDs from Branch 013a for precision):
    1. Instruction-Evaluation Linking (instruction_evaluation_linking.md)
    2. Requirement-Evaluation Mapping (requirement_evaluation.md)
    3. Deliverable Tracing (sow_deliverable_linking.md)
    4. Document Hierarchy (document_hierarchy.md, attachment_section_linking.md, document_section_linking.md, clause_clustering.md)
    5. Semantic Concept Linking (semantic_concept_linking.md)
    6. Heuristic Pattern Matching (CDRL, cross-refs)
    
    Args:
        entities: All entities to analyze
        existing_rels: Existing relationships
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
    
    # ALGORITHM 1: Instruction-Evaluation Linking (Submission Instructions → Evaluation Factors)
    # Content-based agnostic search: find instruction-like entities regardless of type
    
    # Traditional submission_instruction entities (UCF Section L)
    instructions = entities_by_type.get('instruction', []) + entities_by_type.get('submission_instruction', [])
    
    # Agnostic: Deliverables with submission requirements (Task Orders, CDRLs)
    deliverables_with_instructions = [
        e for e in entities_by_type.get('deliverable', [])
        if any(term in (e.get('description', '') + e.get('entity_name', '')).lower() 
               for term in ['submit', 'provide', 'page', 'format', 'volume', 'shall include', 
                           'maximum', 'minimum', 'font', 'address', 'respond'])
    ]
    
    # Agnostic: Requirements with submission verbs (embedded instructions)
    requirements_with_instructions = [
        e for e in entities_by_type.get('requirement', [])
        if e.get('modal_verb') in ['shall', 'must'] and 
           any(term in e.get('entity_name', '').lower() 
               for term in ['submit', 'provide', 'proposal', 'response', 'volume', 
                           'page limit', 'format', 'electronic', 'hard copy'])
    ]
    
    # Combine all instruction sources
    all_instruction_entities = instructions + deliverables_with_instructions + requirements_with_instructions
    
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if all_instruction_entities and eval_factors:
        logger.info(f"\n  [Algorithm 1/8] Instruction-Evaluation Linking: {len(all_instruction_entities)} instruction entities × {len(eval_factors)} eval factors")
        logger.info(f"      Sources: {len(instructions)} submission_instruction, {len(deliverables_with_instructions)} deliverables, {len(requirements_with_instructions)} requirements")
        
        prompt_instructions = await _load_prompt_template("instruction_evaluation_linking.md")
        
        inst_json = json.dumps([{
            'id': i['id'],
            'name': i['entity_name'],
            'type': i.get('entity_type'),
            'description': i.get('description', '')[:200]
        } for i in all_instruction_entities], indent=2)
        
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:200]
        } for f in eval_factors], indent=2)
        
        prompt = f"""{prompt_instructions}

SUBMISSION INSTRUCTIONS (and instruction-like entities):
{inst_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 1")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} instruction-evaluation relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 1 failed: {e}")
    
    # ALGORITHM 2: Evaluation Hierarchy & Metrics (Structure evaluation framework)
    if eval_factors:
        logger.info(f"\n  [Algorithm 2/8] Evaluation Hierarchy: {len(eval_factors)} evaluation entities")
        
        prompt_instructions = await _load_prompt_template("evaluation_hierarchy.md")
        
        # Build entity JSON with IDs
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:300]
        } for f in eval_factors], indent=2)
        
        prompt = f"""{prompt_instructions}

EVALUATION_FACTOR_ENTITIES:
{factors_json}

Apply the hierarchy inference patterns from the instructions above. Use entity IDs from 'id' field (NOT names).
Return ONLY valid JSON array:
[
  {{"source_id": "parent_id", "target_id": "child_id", "relationship_type": "HAS_SUBFACTOR|HAS_RATING_SCALE|MEASURED_BY|HAS_THRESHOLD|EVALUATED_USING|DEFINES_SCALE", "confidence": 0.75-0.95, "reasoning": "pattern explanation"}}
]
"""
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 2")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} evaluation hierarchy relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 2 failed: {e}")
    
    # ALGORITHM 3: Requirement-Evaluation Mapping (Requirements → Main Evaluation Factors ONLY)
    requirements = entities_by_type.get('requirement', [])
    
    # Filter to MAIN evaluation factors only (exclude rating scales, metrics, thresholds)
    # STRICT FILTERING (Branch 014/015): Aligned with validation - explicit main patterns only
    def is_main_evaluation_factor(entity):
        """
        Identify main evaluation factors vs supporting entities.
        
        CRITICAL: Government RFPs have 3-8 main factors BUT 40-100+ total eval factor entities.
        70-90% are supporting entities (rating scales, metrics, processes, tables).
        ONLY link main factors/subfactors to requirements for accurate coverage metrics.
        
        Returns:
            True if main factor/subfactor (linkable), False if supporting entity
        """
        name_lower = entity.get('entity_name', '').lower()
        
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
    
    main_eval_factors = [f for f in eval_factors if is_main_evaluation_factor(f)]
    
    if requirements and main_eval_factors:
        logger.info(f"\n  [Algorithm 3/8] Requirement-Evaluation Mapping: {len(requirements)} requirements × {len(main_eval_factors)} main factors (filtered from {len(eval_factors)} total)")
        
        prompt_instructions = await _load_prompt_template("requirement_evaluation.md")
        
        # Build entity JSON with IDs
        # ENHANCEMENT (Branch 015): Include full descriptions for semantic matching
        # Evaluation factor descriptions contain topic keywords (e.g., "evaluating management, staffing, quality")
        # This enables matching generic factor labels (Factor A, Factor B) to requirement content
        reqs_json = json.dumps([{
            'id': r['id'],
            'name': r['entity_name'],
            'type': r.get('entity_type'),
            'description': r.get('description', '')[:500]  # Increased from 200 to capture full semantic context
        } for r in requirements], indent=2)
        
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:500]  # Increased from 200 to capture evaluation criteria/topics
        } for f in main_eval_factors], indent=2)
        
        prompt = f"""{prompt_instructions}

REQUIREMENTS:
{reqs_json}

EVALUATION_FACTORS:
{factors_json}

CRITICAL INSTRUCTION - Use factor descriptions for semantic matching:
- Factor names may be generic (Factor A, Factor B, Factor 1, etc.)
- Factor descriptions contain evaluation criteria and topics (e.g., "evaluating management approach, staffing methodology")
- Match requirement CONTENT to factor DESCRIPTION topics, not just factor names
- Example: "Factor A" with description "evaluating management methodology" matches requirements about management/staffing

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field (NOT names).
Focus ONLY on main evaluation factors (Factor 1, Factor 2, Subfactors). Exclude rating scales, metrics, and thresholds.
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "factor_id", "relationship_type": "EVALUATED_BY", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            # Validate IDs exist
            valid_rels = []
            for rel in rels:
                if rel.get('source_id') in id_to_entity and rel.get('target_id') in id_to_entity:
                    valid_rels.append(rel)
                else:
                    logger.warning(f"  Invalid IDs in relationship: {rel}")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} requirement→main-factor relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 3 failed: {e}")
    
    # ALGORITHM 4: Deliverable Traceability (Dual-Pattern: Requirements + Work Statements)
    requirements = entities_by_type.get('requirement', [])
    work_statements = entities_by_type.get('statement_of_work', []) + entities_by_type.get('pws', []) + entities_by_type.get('soo', [])
    deliverables = entities_by_type.get('deliverable', [])
    
    if deliverables and (requirements or work_statements):
        logger.info(f"\n  [Algorithm 4/8] Deliverable Traceability: {len(requirements)} requirements + {len(work_statements)} work statements × {len(deliverables)} deliverables")
        
        prompt_instructions = await _load_prompt_template("deliverable_traceability.md")
        
        # Pattern 1: Requirement → Deliverable (PRIMARY - captures CDRL/clause/eval deliverables)
        pattern1_rels = []
        if requirements:
            reqs_json = json.dumps([{
                'id': r['id'],
                'name': r['entity_name'],
                'type': r.get('entity_type'),
                'description': r.get('description', '')[:300]
            } for r in requirements], indent=2)
            
            deliv_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:200]
            } for d in deliverables], indent=2)
            
            prompt = f"""{prompt_instructions}

Apply PATTERN 1 (Requirement → Deliverable) detection rules.

REQUIREMENTS:
{reqs_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on evidence relationships (deliverables that prove/document requirement compliance).
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "deliverable_id", "relationship_type": "SATISFIED_BY", "confidence": 0.50-0.95, "reasoning": "evidence relationship explanation"}}
]
"""
            
            try:
                response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
                rels = json.loads(response.strip())
                pattern1_rels = _validate_relationships(rels, id_to_entity, "Algorithm 4 Pattern 1")
                logger.info(f"    → Pattern 1 (Requirement→Deliverable): {len(pattern1_rels)} relationships")
            except Exception as e:
                logger.error(f"    ❌ Pattern 1 failed: {e}")
        
        # Pattern 2: Work Statement → Deliverable (SECONDARY - captures explicit SOW references)
        pattern2_rels = []
        if work_statements:
            work_json = json.dumps([{
                'id': w['id'],
                'name': w['entity_name'],
                'type': w.get('entity_type'),
                'description': w.get('description', '')[:300]
            } for w in work_statements], indent=2)
            
            deliv_json = json.dumps([{
                'id': d['id'],
                'name': d['entity_name'],
                'type': d.get('entity_type'),
                'description': d.get('description', '')[:200]
            } for d in deliverables], indent=2)
            
            prompt = f"""{prompt_instructions}

Apply PATTERN 2 (Work Statement → Deliverable) detection rules.

WORK_STATEMENTS:
{work_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on explicit CDRL references and work-product relationships.
Return ONLY valid JSON array:
[
  {{"source_id": "work_statement_id", "target_id": "deliverable_id", "relationship_type": "PRODUCES", "confidence": 0.50-0.96, "reasoning": "explicit reference or work-product explanation"}}
]
"""
            
            try:
                response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
                rels = json.loads(response.strip())
                pattern2_rels = _validate_relationships(rels, id_to_entity, "Algorithm 4 Pattern 2")
                logger.info(f"    → Pattern 2 (WorkStatement→Deliverable): {len(pattern2_rels)} relationships")
            except Exception as e:
                logger.error(f"    ❌ Pattern 2 failed: {e}")
        
        # Combine both patterns (no deduplication - different relationship types serve different purposes)
        all_relationships.extend(pattern1_rels)
        all_relationships.extend(pattern2_rels)
        logger.info(f"    → Total Deliverable Traceability: {len(pattern1_rels) + len(pattern2_rels)} relationships (Pattern 1: {len(pattern1_rels)}, Pattern 2: {len(pattern2_rels)})")
    
    # ALGORITHM 5: Document Hierarchy (comprehensive - attachments, sections, clauses, standards)
    documents = [e for e in entities if e.get('entity_type') in ['document', 'section', 'attachment', 'annex', 'amendment', 'clause', 'standard', 'specification', 'regulation', 'exhibit']]
    
    if len(documents) > 1:
        logger.info(f"\n  [Algorithm 5/8] Document Hierarchy (All Document Types): {len(documents)} document entities")
        
        prompt_instructions = await _load_prompt_template("document_hierarchy.md")
        
        docs_json = json.dumps([{
            'id': d['id'],
            'name': d['entity_name'],
            'type': d.get('entity_type'),
            'description': d.get('description', '')[:200]
        } for d in documents], indent=2)
        
        prompt = f"""{prompt_instructions}

DOCUMENTS (all types - attachments, sections, annexes, clauses, standards):
{docs_json}

Apply the inference patterns from the instructions above to identify ALL document relationships.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "child_id", "target_id": "parent_id", "relationship_type": "CHILD_OF|ATTACHMENT_OF", "confidence": 0.7-1.0, "reasoning": "pattern explanation"}}
]
"""
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 5")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} document hierarchy relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 5 failed: {e}")
    
    # ALGORITHM 6: Semantic Concept Linking
    concepts = entities_by_type.get('concept', [])[:50]  # Limit to 50 concepts
    strategic_themes = entities_by_type.get('strategic_theme', [])
    
    if (concepts or strategic_themes) and eval_factors:
        concept_pool = concepts + strategic_themes
        logger.info(f"\n  [Algorithm 6/8] Semantic Concept Linking: {len(concept_pool)} concepts/themes")
        
        prompt_instructions = await _load_prompt_template("semantic_concept_linking.md")
        
        # Build mixed entity pool (concepts + high-value entities)
        high_value_entities = requirements[:30] + deliverables[:20] + eval_factors[:20]
        
        prompt_json = json.dumps([{
            'id': e['id'],
            'name': e['entity_name'],
            'type': e.get('entity_type'),
            'description': e.get('description', '')[:150]
        } for e in concept_pool + high_value_entities], indent=2)
        
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
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            valid_rels = _validate_relationships(rels, id_to_entity, "Algorithm 5")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} semantic concept relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 6 failed: {e}")
    
    # ALGORITHM 7: Heuristic Pattern Matching (CDRL cross-refs)
    logger.info(f"\n  [Algorithm 7/8] Heuristic CDRL Pattern Matching")
    
    heuristic_count = 0
    for entity in entities:
        desc = entity.get('description', '').lower()
        name = entity.get('entity_name', '').lower()
        
        # Pattern: CDRL cross-reference (e.g., "CDRL A001")
        import re
        cdrl_pattern = r'cdrl\s+[a-z]\d{3,4}'
        matches = re.findall(cdrl_pattern, desc + ' ' + name)
        
        for match in matches:
            cdrl_id = match.replace(' ', '').upper()
            for deliv in deliverables:
                if cdrl_id in deliv.get('entity_name', '').upper() or cdrl_id in deliv.get('description', '').upper():
                    all_relationships.append({
                        'source_id': entity['id'],
                        'target_id': deliv['id'],
                        'relationship_type': 'REFERENCES',
                        'confidence': 0.95,
                        'reasoning': f"Heuristic: Explicit CDRL cross-reference '{match}'"
                    })
                    heuristic_count += 1
                    break
    
    logger.info(f"    → Found {heuristic_count} heuristic relationships")
    
    # ALGORITHM 8: Orphan Pattern Resolution (Equipment, Gov't-Provided, Person-Deliverable, Table-Field)
    logger.info(f"\n  [Algorithm 8/8] Orphan Pattern Resolution")
    orphan_rels = await _resolve_orphan_patterns(entities, id_to_entity, model=model, temperature=temperature)
    all_relationships.extend(orphan_rels)
    logger.info(f"    → Found {len(orphan_rels)} orphan pattern relationships")
    
    # Summary
    logger.info(f"\n  ✅ Total relationships from all algorithms: {len(all_relationships)}")
    return all_relationships


async def _semantic_post_processor_neo4j(
    llm_model_name: str = "grok-4-fast-reasoning",
    temperature: float = 0.1
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
                "entities_corrected": 0,
                "relationships_inferred": 0,
                "processing_time": 0
            }
        
        # Step 2: Correct entity types
        logger.info("\n🔧 Step 2: Correcting entity types with LLM...")
        entity_updates = []
        grouped = group_entities_by_type(entities)
        
        # Normalize FORBIDDEN_TYPES to lowercase for case-insensitive matching
        forbidden_types_lower = [t.lower() for t in FORBIDDEN_TYPES]
        
        for entity_type, entity_group in grouped.items():
            entity_type_clean = entity_type.lower()
            has_hash_prefix = entity_type_clean.startswith('#')
            
            # Strip # prefix if present (LightRAG internal marker)
            if has_hash_prefix:
                entity_type_clean = entity_type_clean[1:]
            
            # Process entities that need correction:
            # 1. UNKNOWN types (always need LLM inference)
            # 2. Forbidden types (need retyping to allowed types)
            # 3. Hash-prefixed types (corrupted, need cleaning even if underlying type is allowed)
            needs_correction = (
                entity_type_clean == 'unknown' or
                entity_type_clean in forbidden_types_lower or
                has_hash_prefix
            )
            
            if needs_correction:
                logger.info(f"  Processing {len(entity_group)} {entity_type} entities...")
                
                for entity in entity_group:
                    # For hash-prefixed allowed types, just remove prefix without LLM call
                    if has_hash_prefix and entity_type_clean in ALLOWED_TYPES:
                        entity_updates.append({
                            'id': entity['id'],
                            'new_entity_type': entity_type_clean  # Use cleaned type (no LLM needed)
                        })
                    else:
                        # Call LLM to infer correct type (for UNKNOWN or forbidden types)
                        new_type = await _infer_entity_type(
                            entity_name=entity['entity_name'],
                            description=entity.get('description', ''),
                            model=llm_model_name,
                            temperature=temperature
                        )
                        
                        if new_type and new_type.lower() != entity_type_clean:
                            entity_updates.append({
                                'id': entity['id'],
                                'new_entity_type': new_type
                            })
        
        entities_corrected = 0
        if entity_updates:
            logger.info(f"\n💾 Updating {len(entity_updates)} entity types in Neo4j...")
            entities_corrected = neo4j_io.update_entity_types(entity_updates)
        else:
            logger.info("\n✅ No entity type corrections needed")
        
        # Step 3: Infer missing relationships
        logger.info("\n🔗 Step 3: Inferring missing relationships with multi-algorithm approach...")
        new_relationships = await _infer_relationships_multi_algorithm(
            entities=entities,
            existing_rels=relationships,
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
        logger.info(f"  Entities corrected:      {entities_corrected}")
        logger.info(f"  Relationships inferred:  {relationships_inferred}")
        logger.info(f"  Requirements enriched:   {requirements_enriched}")
        logger.info(f"  Processing time:         {processing_time:.2f}s")
        logger.info("="*80)
        
        # Get updated counts
        type_counts = neo4j_io.get_entity_count_by_type()
        logger.info("\n📊 Entity Type Distribution:")
        for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {entity_type:30s}: {count:4d}")
        
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
    Run all semantic post-processing on extracted knowledge graph.
    
    Steps:
    1. Load entities/relationships from GraphML
    2. Correct entity types (UNKNOWN -> proper types)
    3. Infer missing relationships (semantic understanding)
    4. Save enhanced graph back to GraphML
    
    Args:
        rag_storage_path: Path to rag_storage directory (e.g., "./rag_storage")
        llm_func: Async LLM function for semantic operations
        batch_size: Batch size for LLM calls (default: 50)
    
    Returns:
        Stats dict with:
        - entities_corrected: Number of entities retyped
        - relationships_inferred: Number of new relationships
        - processing_time: Total time in seconds
    """
    logger.info("=" * 80)
    logger.info("🧠 SEMANTIC POST-PROCESSING: LLM-Powered Graph Enhancement")
    logger.info("=" * 80)
    
    # Check if Neo4j storage is enabled - use Cypher-based processing
    import os
    if os.getenv("GRAPH_STORAGE") == "Neo4JStorage":
        logger.info("\n  📊 Neo4j storage detected - using Cypher-based semantic enhancement")
        # Get LLM model from environment
        llm_model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
        llm_temp = float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
        return await _semantic_post_processor_neo4j(
            llm_model_name=llm_model,
            temperature=llm_temp
        )
    
    import time
    start_time = time.time()
    
    # Construct GraphML path from rag_storage_path
    graphml_path = Path(rag_storage_path) / "default" / "graph_chunk_entity_relation.graphml"
    
    # Step 1: Load graph
    logger.info("\n  [1/3] Loading knowledge graph from GraphML...")
    nodes, edges = parse_graphml(graphml_path)
    logger.info(f"    ✅ Loaded {len(nodes)} entities, {len(edges)} relationships")
    
    if not nodes:
        logger.warning("    ⚠️  No entities found - skipping post-processing")
        return {
            "status": "skipped",
            "reason": "no_entities",
            "entities_corrected": 0,
            "relationships_inferred": 0,
            "processing_time": 0
        }
    
    # Step 2: Entity Type Correction
    logger.info("\n  [2/3] Entity Type Correction...")
    from src.inference.entity_operations import correct_entity_types
    
    nodes, corrections = await correct_entity_types(
        entities=nodes,
        llm_func=llm_func,
        batch_size=batch_size
    )
    
    logger.info(f"    ✅ Corrected {len(corrections)} entity types")
    
    # Save corrected entities immediately
    if corrections:
        save_enhanced_graphml(graphml_path, nodes, edges)
        logger.info(f"    ✅ Saved corrected entities to GraphML")
    
    # Step 3: Relationship Inference
    logger.info("\n  [3/3] Relationship Inference...")
    from src.inference.relationship_operations import infer_relationships
    
    new_relationships = await infer_relationships(
        entities=nodes,
        existing_relationships=edges,
        llm_func=llm_func,
        batch_size=batch_size
    )
    
    logger.info(f"    ✅ Inferred {len(new_relationships)} new relationships")
    
    # Save enhanced graph
    if new_relationships:
        edges.extend(new_relationships)
        save_enhanced_graphml(graphml_path, nodes, edges)
        logger.info(f"    ✅ Saved enhanced graph to GraphML")
    
    # Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("✅ SEMANTIC POST-PROCESSING COMPLETE")
    logger.info(f"   Entities corrected: {len(corrections)}")
    logger.info(f"   Relationships inferred: {len(new_relationships)}")
    logger.info(f"   Processing time: {elapsed:.1f}s")
    logger.info("=" * 80)
    
    return {
        "status": "success",
        "entities_corrected": len(corrections),
        "relationships_inferred": len(new_relationships),
        "processing_time": elapsed
    }
