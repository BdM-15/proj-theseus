"""
Relationship Inference Engine

Orchestrates LLM-powered semantic relationship inference across the knowledge graph.
Uses external prompt templates from prompts/relationship_inference/ directory.

This replaces brittle regex patterns with semantic understanding via LLM.
"""

import json
import logging
from typing import List, Dict
from pathlib import Path

from src.inference.graph_io import group_entities_by_type
from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


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
        
        # Filter by confidence threshold and normalize structure
        filtered_rels = []
        for r in relationships:
            # Validate required keys (handle variations in key names)
            source_id = r.get('source_id') or r.get('source') or r.get('src')
            target_id = r.get('target_id') or r.get('target') or r.get('tgt')
            rel_type = r.get('relationship_type') or r.get('type') or r.get('relation')
            
            if not source_id or not target_id or not rel_type:
                logger.warning(f"  ⚠️ Skipping malformed relationship (missing keys): {list(r.keys())}")
                continue
            
            confidence = r.get('confidence', 0)
            # Handle string confidence values
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except (ValueError, TypeError):
                    confidence = 0.0
            
            if confidence >= 0.3:
                # Normalize to expected structure
                normalized_rel = {
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': rel_type,
                    'confidence': confidence,
                    'reasoning': r.get('reasoning', 'No reasoning provided')
                }
                filtered_rels.append(normalized_rel)
        
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
    
    # Group entities by type
    grouped = group_entities_by_type(nodes)
    
    logger.info(f"  📊 Entity type distribution:")
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
        logger.info(f"\n  [1/5] Document Hierarchy: DOCUMENT → SECTION...")
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
        logger.info(f"\n  [2/5] Clause Clustering: CLAUSE → SECTION...")
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
        logger.info(f"\n  [3/5] Instruction-Evaluation Linking: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR...")
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
        logger.info(f"\n  [4/5] Requirement Evaluation: REQUIREMENT → EVALUATION_FACTOR...")
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
        logger.info(f"\n  [5/5] Work to Deliverables: STATEMENT_OF_WORK → DELIVERABLE...")
        relationship_context = load_prompt("relationship_inference/sow_deliverable_linking")
        sow_deliverable_rels = await infer_relationships_batch(
            source_entities=grouped['statement_of_work'],
            target_entities=grouped['deliverable'],
            relationship_context=relationship_context,
            llm_func=llm_func
        )
        all_new_relationships.extend(sow_deliverable_rels)
    
    logger.info(f"\n  🎯 Total relationships inferred: {len(all_new_relationships)}")
    logger.info("=" * 80)
    
    return all_new_relationships
