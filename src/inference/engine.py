"""
Relationship Inference Engine

Orchestrates LLM-powered semantic relationship inference across the knowledge graph.
Uses external prompt templates from prompts/relationship_inference/ directory.

This replaces brittle regex patterns with semantic understanding via LLM.
"""

import json
import logging
from typing import List, Dict, Tuple
from pathlib import Path

from src.inference.graph_io import group_entities_by_type
from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


async def deduplicate_entities(
    nodes: List[Dict],
    edges: List[Dict],
    llm_func
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
3. Title additions: "SECTION C.4 - SUPPLY" == "Section C.4 Supply" == "Section C.4"
4. Abbreviations: "Sec C.4" == "Section C.4"
5. Must be SAME section/clause/document - C.4 ≠ C.5, FAR 52.212-1 ≠ FAR 52.212-2

OUTPUT FORMAT (STRICT JSON):
Return a JSON array of duplicate pair objects:
[
  {
    "pair_number": 1,
    "is_duplicate": true,
    "canonical_name": "Section C.4 Supply",
    "reasoning": "Both refer to Section C subsection 4 on supply, just formatting differs"
  },
  {
    "pair_number": 2,
    "is_duplicate": false,
    "reasoning": "Different sections (C.3 vs C.4)"
  }
]

OUTPUT ONLY THE JSON ARRAY, NO OTHER TEXT."""
                
                try:
                    response = await llm_func(prompt, system_prompt="You are an expert at identifying duplicate entities in government contracting documents.")
                    
                    # Parse JSON response
                    response_clean = response.strip()
                    if response_clean.startswith('```'):
                        lines = response_clean.split('\n')
                        json_lines = [l for l in lines if not l.startswith('```')]
                        response_clean = '\n'.join(json_lines)
                    
                    results = json.loads(response_clean)
                    
                    # Process results
                    for result in results:
                        if not isinstance(result, dict):
                            continue
                        
                        if result.get('is_duplicate'):
                            pair_idx = result.get('pair_number', 0) - 1
                            if 0 <= pair_idx < len(batch):
                                entity1, entity2 = batch[pair_idx]
                                canonical = result.get('canonical_name', entity1.get('entity_name'))
                                
                                # Map both old names to canonical name
                                old_name1 = entity1.get('entity_name')
                                old_name2 = entity2.get('entity_name')
                                canonical_mapping[old_name1] = canonical
                                canonical_mapping[old_name2] = canonical
                                
                                logger.info(f"      Merging: '{old_name1}' + '{old_name2}' → '{canonical}'")
                
                except Exception as e:
                    logger.warning(f"    ⚠️ Deduplication batch failed: {e}")
                    continue
    
    # Apply canonical mapping to nodes and edges
    if canonical_mapping:
        # Merge nodes with same canonical name
        canonical_nodes = {}
        for node in nodes:
            name = node.get('entity_name')
            canonical = canonical_mapping.get(name, name)
            
            if canonical in canonical_nodes:
                # Merge descriptions
                existing = canonical_nodes[canonical]
                existing_desc = existing.get('description', '')
                new_desc = node.get('description', '')
                if new_desc and new_desc not in existing_desc:
                    existing['description'] = f"{existing_desc}<SEP>{new_desc}"
                
                # Merge source IDs
                existing_sources = existing.get('source_id', '').split('<SEP>')
                new_sources = node.get('source_id', '').split('<SEP>')
                all_sources = list(set(existing_sources + new_sources))
                existing['source_id'] = '<SEP>'.join([s for s in all_sources if s])
            else:
                # First occurrence - use as canonical
                node['entity_name'] = canonical
                node['id'] = canonical  # Update node ID
                canonical_nodes[canonical] = node
        
        deduplicated_nodes = list(canonical_nodes.values())
        
        # Update edge source/target references
        updated_edges = []
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            
            # Apply canonical mapping
            new_source = canonical_mapping.get(source, source)
            new_target = canonical_mapping.get(target, target)
            
            edge['source'] = new_source
            edge['target'] = new_target
            updated_edges.append(edge)
        
        return deduplicated_nodes, updated_edges, canonical_mapping
    
    # No duplicates found
    return nodes, edges, {}


def create_relationship_inference_prompt(
    source_entities: List[Dict],
    target_entities: List[Dict],
    relationship_context: str
) -> str:
    """
    Create LLM prompt for semantic relationship inference.
    
    Args:
        source_entities: List of source entity dicts
        target_entities: List of target entity dicts
        relationship_context: Context about relationship type and patterns
        
    Returns:
        Formatted prompt for LLM
    """
    prompt = f"""You are analyzing a government RFP knowledge graph to infer missing relationships between entities.

{relationship_context}

SOURCE ENTITIES ({len(source_entities)}):
{json.dumps([{
    'id': e.get('id'),
    'name': e.get('entity_name'),
    'type': e.get('entity_type'),
    'description': e.get('description', '')[:200]  # Truncate long descriptions
} for e in source_entities], indent=2)}

TARGET ENTITIES ({len(target_entities)}):
{json.dumps([{
    'id': e.get('id'),
    'name': e.get('entity_name'),
    'type': e.get('entity_type'),
    'description': e.get('description', '')[:200]
} for e in target_entities], indent=2)}

TASK:
Determine which source entities have meaningful relationships with which target entities based on:

1. **Naming Conventions**: Standard government contracting patterns
2. **Content Similarity**: Semantic overlap between descriptions
3. **Logical Document Structure**: Standard RFP organization
4. **Confidence Thresholds**: HIGH (>0.8), MEDIUM (0.5-0.8), LOW (0.3-0.5)

OUTPUT FORMAT (STRICT JSON):
Return a JSON array of relationship objects. Each relationship must have:
- source_id: ID of source entity (string)
- target_id: ID of target entity (string)
- relationship_type: One of [CHILD_OF, GUIDES, EVALUATED_BY, REFERENCES, CONTAINS, RELATED_TO]
- confidence: Float 0.0-1.0 indicating relationship strength
- reasoning: Brief explanation (1-2 sentences)

OUTPUT ONLY THE JSON ARRAY, NO OTHER TEXT."""
    
    return prompt


async def infer_relationships_batch(
    source_entities: List[Dict],
    target_entities: List[Dict],
    relationship_context: str,
    llm_func
) -> List[Dict]:
    """
    Call LLM to infer relationships between two groups of entities.
    
    Args:
        source_entities: List of source entity dicts
        target_entities: List of target entity dicts
        relationship_context: Context about what relationships to infer
        llm_func: Async LLM function (Grok)
    
    Returns:
        List of relationship dicts with source_id, target_id, type, confidence, reasoning
    """
    prompt = create_relationship_inference_prompt(
        source_entities,
        target_entities,
        relationship_context
    )
    
    try:
        # Load system prompt from external file
        system_prompt = load_prompt("relationship_inference/system_prompt").strip()
        
        # Call LLM
        response = await llm_func(
            prompt,
            system_prompt=system_prompt,
        )
        
        # Parse JSON response (handle markdown code blocks)
        response_clean = response.strip()
        if response_clean.startswith('```'):
            # Extract JSON from code block
            lines = response_clean.split('\n')
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not line.startswith('```'):
                    json_lines.append(line)
            response_clean = '\n'.join(json_lines)
        
        relationships = json.loads(response_clean)
        
        if not isinstance(relationships, list):
            logger.warning(f"  ⚠️ LLM returned non-list: {type(relationships)}")
            return []
        
        # Filter by confidence threshold and validate structure
        filtered_rels = []
        for i, r in enumerate(relationships):
            # Strict validation - LLM must follow prompt format exactly
            required_keys = {'source_id', 'target_id', 'relationship_type', 'confidence'}
            missing_keys = required_keys - set(r.keys())
            
            if missing_keys:
                logger.error(f"  ❌ Relationship {i+1} missing required keys: {missing_keys}")
                logger.error(f"     Got keys: {list(r.keys())}")
                logger.error(f"     Full relationship: {r}")
                continue
            
            confidence = r['confidence']
            # Handle string confidence values (LLM sometimes returns "0.85" instead of 0.85)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except (ValueError, TypeError):
                    logger.warning(f"  ⚠️ Invalid confidence value: {confidence}, defaulting to 0.0")
                    confidence = 0.0
            
            if confidence >= 0.3:
                # Ensure reasoning exists
                r['reasoning'] = r.get('reasoning', 'No reasoning provided')
                r['confidence'] = confidence  # Use normalized float value
                filtered_rels.append(r)
        
        logger.info(f"    ✅ Inferred {len(filtered_rels)} relationships (filtered from {len(relationships)})")
        
        return filtered_rels
        
    except json.JSONDecodeError as e:
        logger.error(f"  ❌ JSON parse error: {e}")
        logger.error(f"  Response preview: {response[:500]}")
        return []
    except KeyError as e:
        logger.error(f"  ❌ Missing required key in relationship: {e}")
        logger.error(f"  Relationship keys: {list(relationships[0].keys()) if relationships else 'empty'}")
        return []
    except Exception as e:
        logger.error(f"  ❌ Error in relationship inference: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
        return []


async def infer_all_relationships(
    nodes: List[Dict],
    existing_edges: List[Dict],
    llm_func
) -> List[Dict]:
    """
    Infer all missing relationships using LLM semantic understanding.
    
    Implements 5 core relationship inference algorithms:
    1. Document hierarchy: CHILD_OF relationships (documents, clauses → sections)
    2. Clause clustering: CHILD_OF relationships (clauses → sections)
    3. Section L↔M mapping: GUIDES relationships (instructions → factors)
    4. Requirement evaluation: EVALUATED_BY relationships (requirements → factors)
    5. Work-deliverable linking: PRODUCES relationships (SOW → deliverables)
    
    Args:
        nodes: List of entity nodes from GraphML
        existing_edges: List of existing relationships
        llm_func: Async LLM function for inference
        
    Returns:
        List of new relationship dicts
    """
    logger.info("=" * 80)
    logger.info("🤖 SEMANTIC RELATIONSHIP INFERENCE: LLM-Powered Analysis")
    logger.info("=" * 80)
    
    # Group entities by type BEFORE deduplication
    grouped = group_entities_by_type(nodes)
    
    logger.info(f"  📊 Entity type distribution (before deduplication):")
    for entity_type, entities in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"    {entity_type}: {len(entities)}")
    
    # Algorithm 0: Entity Deduplication & Normalization (runs first!)
    logger.info(f"\n  [0/7] Entity Deduplication: LLM-powered formatting normalization...")
    nodes, existing_edges, canonical_mapping = await deduplicate_entities(nodes, existing_edges, llm_func)
    
    if canonical_mapping:
        logger.info(f"    ✅ Merged {len(canonical_mapping)} duplicate entities")
        for old_name, new_name in list(canonical_mapping.items())[:5]:
            logger.info(f"      • '{old_name}' → '{new_name}'")
        if len(canonical_mapping) > 5:
            logger.info(f"      ... and {len(canonical_mapping) - 5} more")
    else:
        logger.info(f"    ✅ No duplicates found - entity naming is clean")
    
    # Re-group entities after deduplication
    grouped = group_entities_by_type(nodes)
    
    logger.info(f"\n  📊 Entity type distribution (after deduplication):")
    for entity_type, entities in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"    {entity_type}: {len(entities)}")
    
    # Track all inferred relationships
    all_new_relationships = []
    
    # Create set of existing relationships for deduplication
    existing_pairs = set()
    for edge in existing_edges:
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
    
    # Algorithm 4: REQUIREMENT → EVALUATION_FACTOR (Requirement Evaluation)
    if 'requirement' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [4/7] Requirement Evaluation: REQUIREMENT → EVALUATION_FACTOR...")
        relationship_context = load_prompt("relationship_inference/requirement_evaluation")
        requirement_factor_rels = await infer_relationships_batch(
            source_entities=grouped['requirement'],
            target_entities=grouped['evaluation_factor'],
            relationship_context=relationship_context,
            llm_func=llm_func
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
    heuristic_rels = apply_type_based_heuristics(grouped, existing_edges)
    all_new_relationships.extend(heuristic_rels)
    logger.info(f"    ✅ Added {len(heuristic_rels)} deterministic relationships")
    
    logger.info(f"\n  🎯 Total relationships inferred: {len(all_new_relationships)}")
    logger.info("=" * 80)
    
    return all_new_relationships


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
                        'reasoning': 'SOW/PWS typically located in Section C or Section J attachments'
                    })
    
    return new_relationships
