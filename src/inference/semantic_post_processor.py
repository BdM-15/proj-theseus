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
- EVALUATES: Section M evaluation criteria → Section L requirements
- FULFILLS: Deliverable → Requirement it satisfies
- REQUIRES: Requirement → Equipment/Resource needed
- REFERENCES: Document/Section → Another document/section
- APPLIES_TO: Clause/Regulation → Program/Contract
- PART_OF: Sub-component → Parent component

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
    instructions = entities_by_type.get('instruction', []) + entities_by_type.get('submission_instruction', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if instructions and eval_factors:
        logger.info(f"\n  [Algorithm 1/7] Instruction-Evaluation Linking: {len(instructions)} instructions × {len(eval_factors)} eval factors")
        
        prompt_instructions = await _load_prompt_template("instruction_evaluation_linking.md")
        
        inst_json = json.dumps([{
            'id': i['id'],
            'name': i['entity_name'],
            'type': i.get('entity_type'),
            'description': i.get('description', '')[:200]
        } for i in instructions], indent=2)
        
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:200]
        } for f in eval_factors], indent=2)
        
        prompt = f"""{prompt_instructions}

SUBMISSION INSTRUCTIONS:
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
            valid_rels = [r for r in rels if r.get('source_id') in id_to_entity and r.get('target_id') in id_to_entity]
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} instruction-evaluation relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 1 failed: {e}")
    
    # ALGORITHM 2A: Evaluation Hierarchy & Metrics (Structure evaluation framework)
    if eval_factors:
        logger.info(f"\n  [Algorithm 2a/7] Evaluation Hierarchy: {len(eval_factors)} evaluation entities")
        
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
            # Validate IDs exist
            valid_rels = []
            for rel in rels:
                if rel.get('source_id') in id_to_entity and rel.get('target_id') in id_to_entity:
                    valid_rels.append(rel)
                else:
                    logger.warning(f"  Invalid IDs in relationship: {rel}")
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} evaluation hierarchy relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 2a failed: {e}")
    
    # ALGORITHM 2B: Requirement-Evaluation Mapping (Requirements → Main Evaluation Factors ONLY)
    requirements = entities_by_type.get('requirement', [])
    
    # Filter to MAIN evaluation factors only (exclude rating scales, metrics, thresholds)
    def is_main_evaluation_factor(entity):
        """Identify main evaluation factors vs supporting entities (metrics, ratings, etc.)"""
        name = entity.get('entity_name', '').lower()
        desc = entity.get('description', '').lower()
        
        # Main factor patterns
        if any(pattern in name for pattern in ['factor 1', 'factor 2', 'factor 3', 'subfactor', 'technical factor', 'price factor']):
            return True
        if 'tomp' in name or 'mission essential' in name or 'quality control plan' in name:
            return True
        
        # Exclude supporting entities
        rating_terms = ['outstanding', 'good', 'acceptable', 'marginal', 'unacceptable', 'pass', 'fail']
        if any(term in name for term in rating_terms):
            return False
        
        # Exclude metrics (contains % or numeric thresholds)
        if '%' in name or 'rate' in name or 'threshold' in name or 'level' in name:
            return False
        
        # Exclude processes/tables
        if 'evaluation' in name or 'analysis' in name or 'table' in name or '(table)' in name:
            return False
        
        # Default: keep if not clearly a supporting entity
        return True
    
    main_eval_factors = [f for f in eval_factors if is_main_evaluation_factor(f)]
    
    if requirements and main_eval_factors:
        logger.info(f"\n  [Algorithm 2b/7] Requirement-Evaluation Mapping: {len(requirements)} requirements × {len(main_eval_factors)} main factors (filtered from {len(eval_factors)} total)")
        
        prompt_instructions = await _load_prompt_template("requirement_evaluation.md")
        
        # Build entity JSON with IDs
        reqs_json = json.dumps([{
            'id': r['id'],
            'name': r['entity_name'],
            'type': r.get('entity_type'),
            'description': r.get('description', '')[:200]
        } for r in requirements], indent=2)
        
        factors_json = json.dumps([{
            'id': f['id'],
            'name': f['entity_name'],
            'type': f.get('entity_type'),
            'description': f.get('description', '')[:200]
        } for f in main_eval_factors], indent=2)
        
        prompt = f"""{prompt_instructions}

REQUIREMENTS:
{reqs_json}

EVALUATION_FACTORS:
{factors_json}

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
            logger.error(f"    ❌ Algorithm 2b failed: {e}")
    
    # ALGORITHM 3: Deliverable Tracing (SOW → Deliverables)
    sow_entities = entities_by_type.get('statement_of_work', []) + entities_by_type.get('pws', []) + entities_by_type.get('soo', [])
    deliverables = entities_by_type.get('deliverable', [])
    
    if sow_entities and deliverables:
        logger.info(f"\n  [Algorithm 3/7] Deliverable Tracing: {len(sow_entities)} work statements × {len(deliverables)} deliverables")
        
        prompt_instructions = await _load_prompt_template("sow_deliverable_linking.md")
        
        sow_json = json.dumps([{
            'id': s['id'],
            'name': s['entity_name'],
            'type': s.get('entity_type'),
            'description': s.get('description', '')[:200]
        } for s in sow_entities], indent=2)
        
        deliv_json = json.dumps([{
            'id': d['id'],
            'name': d['entity_name'],
            'type': d.get('entity_type'),
            'description': d.get('description', '')[:200]
        } for d in deliverables], indent=2)
        
        prompt = f"""{prompt_instructions}

WORK_STATEMENTS:
{sow_json}

DELIVERABLES:
{deliv_json}

Apply the detection rules from the instructions above. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "sow_id", "target_id": "deliverable_id", "relationship_type": "PRODUCES", "confidence": 0.3-0.96, "reasoning": "detection rule explanation"}}
]
"""
        
        try:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = json.loads(response.strip())
            valid_rels = [r for r in rels if r.get('source_id') in id_to_entity and r.get('target_id') in id_to_entity]
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} SOW→Deliverable relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 3 failed: {e}")
    
    # ALGORITHM 4: Document Hierarchy (comprehensive - attachments, sections, clauses, standards)
    documents = [e for e in entities if e.get('entity_type') in ['document', 'section', 'attachment', 'annex', 'amendment', 'clause', 'standard', 'specification', 'regulation', 'exhibit']]
    
    if len(documents) > 1:
        logger.info(f"\n  [Algorithm 4/7] Document Hierarchy (All Document Types): {len(documents)} document entities")
        
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
            valid_rels = [r for r in rels if r.get('source_id') in id_to_entity and r.get('target_id') in id_to_entity]
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} document hierarchy relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 4 failed: {e}")
    
    # ALGORITHM 5: Semantic Concept Linking
    # ALGORITHM 5: Semantic Concept Linking
    concepts = entities_by_type.get('concept', [])[:50]  # Limit to 50 concepts
    strategic_themes = entities_by_type.get('strategic_theme', [])
    
    if (concepts or strategic_themes) and eval_factors:
        concept_pool = concepts + strategic_themes
        logger.info(f"\n  [Algorithm 5/7] Semantic Concept Linking: {len(concept_pool)} concepts/themes")
        
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
            valid_rels = [r for r in rels if r.get('source_id') in id_to_entity and r.get('target_id') in id_to_entity]
            all_relationships.extend(valid_rels)
            logger.info(f"    → Found {len(valid_rels)} semantic concept relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 5 failed: {e}")
    
    # ALGORITHM 6: Heuristic Pattern Matching (CDRL cross-refs)
    logger.info(f"\n  [Algorithm 6/7] Heuristic CDRL Pattern Matching")
    
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
