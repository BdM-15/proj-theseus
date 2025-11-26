"""
Relationship Inference - Semantic Post-Processing Operation
============================================================

Purpose: Discover missing relationships between entities using LLM semantic understanding
Context: Multimodal extraction captures entities but misses many cross-references
Solution: Post-process extracted entities with 7 relationship inference algorithms

Architecture:
- Runs AFTER entity type correction (clean entities → better relationship detection)
- Uses unified BatchProcessor for efficient batching
- 7 algorithms: 5 LLM-powered + 2 heuristic
- Cost: ~$0.03 per RFP (5 LLM batches × ~$0.006/batch)

Integration: Called from semantic_post_processor.enhance_knowledge_graph()
"""

import json
import logging
from typing import List, Dict, Tuple, Callable, Awaitable
from pathlib import Path
from src.utils.logging_config import log_graceful_failure

from src.inference.batch_processor import BatchProcessor
from src.inference.neo4j_graph_io import group_entities_by_type
from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


async def deduplicate_entities(
    nodes: List[Dict],
    edges: List[Dict],
    llm_func: Callable
) -> Tuple[List[Dict], List[Dict], Dict[str, str]]:
    """
    Use LLM to identify and merge duplicate entities caused by formatting variations.
    
    Government RFPs use inconsistent formatting for the same entity:
    - "SECTION C.4 - SUPPLY" vs "Section C.4" vs "section c.4"
    - "FAR 52.212-1" vs "far 52.212-1" vs "FAR clause 52.212-1"
    
    This function uses semantic understanding to detect duplicates and create canonical names.
    
    Args:
        nodes: List of entity nodes
        edges: List of relationships
        llm_func: Async LLM function for deduplication
        
    Returns:
        Tuple of (deduplicated_nodes, updated_edges, canonical_mapping)
        where canonical_mapping is {old_name: canonical_name}
    """
    # Group entities by type for efficient comparison
    grouped = group_entities_by_type(nodes)
    
    canonical_mapping = {}  # old_name -> canonical_name
    entities_to_merge = []  # List of (canonical_entity, [duplicate_entities])
    
    # Focus on types most prone to formatting variations
    types_to_check = ['section', 'clause', 'deliverable', 'document']
    
    for entity_type in types_to_check:
        if entity_type not in grouped or len(grouped[entity_type]) < 2:
            continue
        
        entities = grouped[entity_type]
        
        # Build potential duplicate pairs using fuzzy matching
        potential_duplicates = []
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                name1 = entity1.get('entity_name', '').lower().strip()
                name2 = entity2.get('entity_name', '').lower().strip()
                
                # Quick heuristic: check if normalized names are very similar
                # Remove common variations: punctuation, case, "SECTION" vs "Section"
                norm1 = name1.replace('section', '').replace('sec', '').replace('.', '').replace('-', '').replace(':', '').replace(' ', '')
                norm2 = name2.replace('section', '').replace('sec', '').replace('.', '').replace('-', '').replace(':', '').replace(' ', '')
                
                # If normalized forms match or overlap significantly, flag for LLM review
                if norm1 == norm2 or (len(norm1) > 3 and norm1 in norm2) or (len(norm2) > 3 and norm2 in norm1):
                    potential_duplicates.append((entity1, entity2))
        
        # Batch LLM calls for efficiency (process up to 10 pairs at once)
        if potential_duplicates:
            logger.info(f"    Found {len(potential_duplicates)} potential {entity_type} duplicates to verify...")
            
            for i in range(0, len(potential_duplicates), 10):
                batch = potential_duplicates[i:i+10]
                
                # Create prompt for batch deduplication
                prompt = f"""You are analyzing a government RFP knowledge graph to identify duplicate entities caused by formatting variations.

TASK: Determine which entity pairs are duplicates (same concept, different formatting).

ENTITY PAIRS TO EVALUATE:
"""
                for idx, (e1, e2) in enumerate(batch, 1):
                    prompt += f"""
Pair {idx}:
  Entity A: "{e1.get('entity_name')}" (type: {e1.get('entity_type')})
    Description: {e1.get('description', '')[:150]}...
  Entity B: "{e2.get('entity_name')}" (type: {e2.get('entity_type')})
    Description: {e2.get('description', '')[:150]}...
"""
                
                prompt += """
RULES FOR IDENTIFYING DUPLICATES:
1. Case variations: "SECTION C.4" == "Section C.4" == "section c.4"
2. Punctuation: "Section C.4" == "Section C-4" == "Section C4"
3. Prefix/suffix variations: "FAR 52.212-1" == "FAR clause 52.212-1"
4. Semantic equivalence: "Cost Proposal" == "Price Proposal" (if descriptions match)

OUTPUT FORMAT (JSON):
{
  "duplicates": [
    {
      "canonical_name": "Section C.4 - Supply",
      "duplicates": ["section c.4", "SECTION C.4"],
      "reasoning": "Same section with case/punctuation variations"
    }
  ]
}

Only include pairs that are TRUE duplicates. If no duplicates found, return: {"duplicates": []}
"""
                
                try:
                    response = await llm_func(prompt, "You are an expert at identifying duplicate entities in government RFP documents.")
                    result = json.loads(response)
                    
                    for dup_group in result.get('duplicates', []):
                        canonical = dup_group.get('canonical_name')
                        duplicates = dup_group.get('duplicates', [])
                        
                        for dup_name in duplicates:
                            canonical_mapping[dup_name] = canonical
                
                except Exception as e:
                    logger.warning(f"Failed to process deduplication batch: {e}")
                    continue
    
    # If no duplicates found, return original data
    if not canonical_mapping:
        return nodes, edges, {}
    
    # Merge duplicate entities
    canonical_entities = {}  # canonical_name -> merged_entity
    
    for entity in nodes:
        name = entity.get('entity_name')
        
        # Check if this is a duplicate
        if name in canonical_mapping:
            canonical_name = canonical_mapping[name]
            
            # Merge into canonical entity
            if canonical_name not in canonical_entities:
                # Create canonical entity (use first occurrence as base)
                canonical_entities[canonical_name] = {
                    'id': entity.get('id'),  # Use first ID
                    'entity_name': canonical_name,
                    'entity_type': entity.get('entity_type'),
                    'description': entity.get('description', ''),
                    'source_id': entity.get('source_id', '')
                }
        else:
            # Not a duplicate - keep as-is
            canonical_entities[name] = entity
    
    # Update edges to use canonical names
    updated_edges = []
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        
        # Map to canonical names
        source = canonical_mapping.get(source, source)
        target = canonical_mapping.get(target, target)
        
        # Update edge
        updated_edge = edge.copy()
        updated_edge['source'] = source
        updated_edge['target'] = target
        updated_edges.append(updated_edge)
    
    # Convert canonical_entities back to list
    deduplicated_nodes = list(canonical_entities.values())
    
    return deduplicated_nodes, updated_edges, canonical_mapping


async def infer_relationships_batch(
    source_entities: List[Dict],
    target_entities: List[Dict],
    relationship_context: str,
    llm_func: Callable
) -> List[Dict]:
    """
    Infer relationships between source and target entities using LLM.
    
    Args:
        source_entities: List of source entity dicts
        target_entities: List of target entity dicts
        relationship_context: Prompt template with relationship rules
        llm_func: Async LLM function for inference
        
    Returns:
        List of relationship dicts
    """
    if not source_entities or not target_entities:
        return []
    
    # Build entity context for prompt
    source_context = "\n".join([
        f"- {e.get('entity_name')} (type: {e.get('entity_type')}): {e.get('description', '')[:100]}..."
        for e in source_entities[:20]  # Limit to first 20 to avoid token limits
    ])
    
    target_context = "\n".join([
        f"- {e.get('entity_name')} (type: {e.get('entity_type')}): {e.get('description', '')[:100]}..."
        for e in target_entities[:20]
    ])
    
    prompt = relationship_context.format(
        source_entities=source_context,
        target_entities=target_context
    )
    
    system_prompt = "You are an expert at analyzing government RFP documents and inferring relationships between entities."
    
    try:
        response = await llm_func(prompt, system_prompt)
        
        # Parse JSON response
        result = json.loads(response)
        relationships = result.get('relationships', [])
        
        # Convert to internal relationship format
        new_relationships = []
        for rel in relationships:
            new_relationships.append({
                'source_id': _find_entity_id(rel.get('source'), source_entities),
                'target_id': _find_entity_id(rel.get('target'), target_entities),
                'relationship_type': rel.get('type', 'RELATED_TO'),
                'confidence': rel.get('confidence', 0.7),
                'reasoning': rel.get('reasoning', '')
            })
        
        return new_relationships
    
    except Exception as e:
        log_graceful_failure(logger, "Relationship inference", e)
        return []


def _find_entity_id(entity_name: str, entities: List[Dict]) -> str:
    """Helper to find entity ID by name."""
    for entity in entities:
        if entity.get('entity_name') == entity_name:
            return entity.get('id')
    return None


def apply_type_based_heuristics(
    grouped: Dict[str, List[Dict]],
    existing_edges: List[Dict]
) -> List[Dict]:
    """
    Apply deterministic type-based relationship rules based on government contracting patterns.
    
    These are high-confidence structural relationships that don't require LLM inference:
    - DELIVERABLE entities → Section J (standard UCF location)
    - CLAUSE entities → Section I (standard UCF location)
    - EVALUATION_FACTOR entities → Section M (standard UCF location)
    - SUBMISSION_INSTRUCTION entities → Section L (standard UCF location)
    
    Args:
        grouped: Entity dictionary grouped by type
        existing_edges: List of existing relationships (for deduplication)
        
    Returns:
        List of new relationship dicts
    """
    new_relationships = []
    
    # Create deduplication set
    existing_pairs = set()
    for edge in existing_edges:
        source = edge.get('source')
        target = edge.get('target')
        if source and target:
            existing_pairs.add((source, target))
            existing_pairs.add((target, source))
    
    # Helper function to find section by name pattern
    def find_section(section_name_pattern: str) -> Dict:
        """Find section entity by name pattern (case-insensitive)."""
        if 'section' not in grouped:
            return None
        for section in grouped['section']:
            name = section.get('entity_name', '').lower()
            if section_name_pattern.lower() in name:
                return section
        return None
    
    # Pattern 1: DELIVERABLE → Section J
    section_j = find_section('section j')
    if section_j and 'deliverable' in grouped:
        for deliverable in grouped['deliverable']:
            source_id = deliverable.get('id')
            target_id = section_j.get('id')
            if source_id and target_id and (source_id, target_id) not in existing_pairs:
                new_relationships.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': 'CHILD_OF',
                    'confidence': 0.90,
                    'reasoning': 'Deliverables are typically listed in Section J attachments per UCF standard'
                })
    
    # Pattern 2: CLAUSE → Section I
    section_i = find_section('section i')
    if section_i and 'clause' in grouped:
        for clause in grouped['clause']:
            source_id = clause.get('id')
            target_id = section_i.get('id')
            if source_id and target_id and (source_id, target_id) not in existing_pairs:
                new_relationships.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': 'CHILD_OF',
                    'confidence': 0.95,
                    'reasoning': 'FAR/DFARS clauses are incorporated in Section I per UCF standard'
                })
    
    # Pattern 3: EVALUATION_FACTOR → Section M
    section_m = find_section('section m')
    if section_m and 'evaluation_factor' in grouped:
        for factor in grouped['evaluation_factor']:
            source_id = factor.get('id')
            target_id = section_m.get('id')
            if source_id and target_id and (source_id, target_id) not in existing_pairs:
                new_relationships.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': 'CHILD_OF',
                    'confidence': 0.95,
                    'reasoning': 'Evaluation factors are defined in Section M per UCF standard'
                })
    
    # Pattern 4: SUBMISSION_INSTRUCTION → Section L
    section_l = find_section('section l')
    if section_l and 'submission_instruction' in grouped:
        for instruction in grouped['submission_instruction']:
            source_id = instruction.get('id')
            target_id = section_l.get('id')
            if source_id and target_id and (source_id, target_id) not in existing_pairs:
                new_relationships.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': 'CHILD_OF',
                    'confidence': 0.95,
                    'reasoning': 'Submission instructions are provided in Section L per UCF standard'
                })
    
    # Pattern 5: STATEMENT_OF_WORK → Section C (or Section J if in attachments)
    section_c = find_section('section c')
    if section_c and 'statement_of_work' in grouped:
        for sow in grouped['statement_of_work']:
            # Check if SOW is in Section C or Section J (look for J- pattern in description)
            description = sow.get('description', '').lower()
            name = sow.get('entity_name', '').lower()
            
            # If name contains J- or attachment patterns, link to Section J
            if 'j-' in name or 'attachment' in name.lower() or 'annex' in name.lower():
                target_section = find_section('section j')
                if not target_section:
                    target_section = section_c  # Fallback to Section C
            else:
                target_section = section_c
            
            if target_section:
                source_id = sow.get('id')
                target_id = target_section.get('id')
                if source_id and target_id and (source_id, target_id) not in existing_pairs:
                    new_relationships.append({
                        'source_id': source_id,
                        'target_id': target_id,
                        'relationship_type': 'CHILD_OF',
                        'confidence': 0.85,
                        'reasoning': 'Statement of Work typically in Section C or Section J attachments per UCF standard'
                    })
    
    return new_relationships


async def infer_relationships(
    entities: List[Dict],
    existing_relationships: List[Dict],
    llm_func: Callable,
    batch_size: int = 50
) -> List[Dict]:
    """
    Main relationship inference operation using unified BatchProcessor.
    
    Implements 7 core relationship inference algorithms:
    0. Entity Deduplication (LLM-powered formatting normalization)
    1. Document hierarchy: CHILD_OF relationships (documents → sections)
    2. Clause clustering: CHILD_OF relationships (clauses → sections)
    3. Section L↔M mapping: GUIDES relationships (instructions ↔ factors)
    4. Requirement evaluation: EVALUATED_BY relationships (requirements → factors)
    5. Work-deliverable linking: PRODUCES relationships (SOW → deliverables)
    6. Type-based heuristics: Deterministic UCF patterns
    
    Args:
        entities: List of entity nodes from GraphML
        existing_relationships: List of existing relationships
        llm_func: Async LLM function for inference
        batch_size: Number of items to process per LLM call (default: 50)
        
    Returns:
        List of new relationship dicts
    """
    logger.info("🔗 Relationship Inference Operation")
    logger.info("=" * 80)
    
    # Group entities by type BEFORE deduplication
    grouped = group_entities_by_type(entities)
    
    logger.info(f"  📊 Entity type distribution (before deduplication):")
    for entity_type, entity_list in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"    {entity_type}: {len(entity_list)}")
    
    # Algorithm 0: Entity Deduplication & Normalization (runs first!)
    logger.info(f"\n  [0/7] Entity Deduplication: LLM-powered formatting normalization...")
    entities, existing_relationships, canonical_mapping = await deduplicate_entities(
        entities, existing_relationships, llm_func
    )
    
    if canonical_mapping:
        logger.info(f"    ✅ Merged {len(canonical_mapping)} duplicate entities")
        for old_name, new_name in list(canonical_mapping.items())[:5]:
            logger.info(f"      • '{old_name}' → '{new_name}'")
        if len(canonical_mapping) > 5:
            logger.info(f"      ... and {len(canonical_mapping) - 5} more")
    else:
        logger.info(f"    ✅ No duplicates found - entity naming is clean")
    
    # Re-group entities after deduplication
    grouped = group_entities_by_type(entities)
    
    logger.info(f"\n  📊 Entity type distribution (after deduplication):")
    for entity_type, entity_list in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"    {entity_type}: {len(entity_list)}")
    
    # Track all inferred relationships
    all_new_relationships = []
    
    # Create unified BatchProcessor
    processor = BatchProcessor(batch_size=batch_size)
    
    # Create set of existing relationships for deduplication
    existing_pairs = set()
    for edge in existing_relationships:
        source = edge.get('source')
        target = edge.get('target')
        if source and target:
            existing_pairs.add((source, target))
            existing_pairs.add((target, source))  # Bidirectional
    
    logger.info(f"  Existing relationships: {len(existing_pairs) // 2}")
    
    # Algorithm 1: DOCUMENT → SECTION (Document Hierarchy)
    if 'document' in grouped and 'section' in grouped:
        logger.info(f"\n  [1/7] Document Hierarchy: DOCUMENT → SECTION...")
        relationship_context = load_prompt("relationship_inference/document_section_linking")
        document_section_rels = await infer_relationships_batch(
            source_entities=grouped['document'],
            target_entities=grouped['section'],
            relationship_context=relationship_context,
            llm_func=llm_func
        )
        all_new_relationships.extend(document_section_rels)
    
    # Algorithm 2: CLAUSE → SECTION (Clause Clustering)
    if 'clause' in grouped and 'section' in grouped:
        logger.info(f"\n  [2/7] Clause Clustering: CLAUSE → SECTION...")
        relationship_context = load_prompt("relationship_inference/clause_clustering")
        clause_section_rels = await infer_relationships_batch(
            source_entities=grouped['clause'],
            target_entities=grouped['section'],
            relationship_context=relationship_context,
            llm_func=llm_func
        )
        all_new_relationships.extend(clause_section_rels)
    
    # Algorithm 3: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR (Instruction-Evaluation Linking)
    if 'submission_instruction' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [3/7] Instruction-Evaluation Linking: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR...")
        relationship_context = load_prompt("relationship_inference/instruction_evaluation_linking")
        instruction_factor_rels = await infer_relationships_batch(
            source_entities=grouped['submission_instruction'],
            target_entities=grouped['evaluation_factor'],
            relationship_context=relationship_context,
            llm_func=llm_func
        )
        all_new_relationships.extend(instruction_factor_rels)
    
    # Algorithm 4: REQUIREMENT → EVALUATION_FACTOR (Requirement Evaluation) - WITH BATCHING
    if 'requirement' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [4/7] Requirement Evaluation: REQUIREMENT → EVALUATION_FACTOR...")
        relationship_context = load_prompt("relationship_inference/requirement_evaluation")
        
        requirements = grouped['requirement']
        evaluation_factors = grouped['evaluation_factor']
        
        # Use BatchProcessor for large requirement sets
        async def process_requirement_batch(batch: List[Dict]) -> List[Dict]:
            return await infer_relationships_batch(
                source_entities=batch,
                target_entities=evaluation_factors,
                relationship_context=relationship_context,
                llm_func=llm_func
            )
        
        requirement_factor_rels = await processor.process_batches(
            items=requirements,
            process_fn=process_requirement_batch,
            batch_name="Requirement→Factor Inference",
            aggregate_fn=processor.flatten_list_results
        )
        
        all_new_relationships.extend(requirement_factor_rels)
    
    # Algorithm 5: STATEMENT_OF_WORK → DELIVERABLE (Work to Deliverables)
    if 'statement_of_work' in grouped and 'deliverable' in grouped:
        logger.info(f"\n  [5/7] Work to Deliverables: STATEMENT_OF_WORK → DELIVERABLE...")
        relationship_context = load_prompt("relationship_inference/sow_deliverable_linking")
        sow_deliverable_rels = await infer_relationships_batch(
            source_entities=grouped['statement_of_work'],
            target_entities=grouped['deliverable'],
            relationship_context=relationship_context,
            llm_func=llm_func
        )
        all_new_relationships.extend(sow_deliverable_rels)
    
    # Algorithm 6: Type-Based Heuristics (Deterministic UCF Patterns)
    logger.info(f"\n  [6/7] Type-Based Heuristics: Domain-Specific Patterns...")
    heuristic_rels = apply_type_based_heuristics(grouped, existing_relationships)
    all_new_relationships.extend(heuristic_rels)
    logger.info(f"    ✅ Added {len(heuristic_rels)} deterministic relationships")
    
    logger.info(f"\n  🎯 Total relationships inferred: {len(all_new_relationships)}")
    logger.info("=" * 80)
    
    return all_new_relationships
