"""
Entity Type Correction - Semantic Post-Processing Operation
============================================================

Purpose: Eliminate UNKNOWN/forbidden entity types using LLM retyping
Context: LLM extraction may produce non-standard entity types
Solution: Post-process extracted entities with strict type enforcement

Architecture:
- Runs BEFORE relationship inference (clean entities → better relationships)
- Uses unified BatchProcessor for efficient batching
- Simple prompt: "Retype these entities using ONLY these 17 types"
- Cost: ~$0.005-0.01 per RFP (200 entities × 100 tokens = ~20K tokens)

Integration: Called from semantic_post_processor.enhance_knowledge_graph()
"""

import logging
from typing import List, Dict, Tuple, Callable, Awaitable
from src.inference.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)

# 17 allowed entity types (lowercase with underscores)
ALLOWED_TYPES = [
    "organization",
    "concept",
    "event",
    "technology",
    "person",
    "location",
    "requirement",
    "clause",
    "section",
    "document",
    "deliverable",
    "program",
    "equipment",
    "evaluation_factor",
    "submission_instruction",
    "strategic_theme",
    "statement_of_work",
    "performance_metric",
]

# Forbidden types that must be eliminated
FORBIDDEN_TYPES = [
    "UNKNOWN",
    "other",
    "process",
    "table",
    "image",
    "plan",
    "policy",
    "standard",
    "instruction",
    "system",
    "regulation",
    "framework",
    "objective",
    "methodology",
    "approach",
    "strategy",
    "model",
]


def identify_forbidden_entities(entities: List[Dict]) -> List[Dict]:
    """
    Scan entities and identify those with forbidden types.
    Also fixes corrupted types (e.g., #concept → concept).
    
    Args:
        entities: List of entity dicts with 'entity_type', 'entity_name', 'description'
    
    Returns:
        List of entities with forbidden types that need retyping
    """
    forbidden = []
    fixed_corruption = 0
    
    for entity in entities:
        entity_type = entity.get("entity_type", "UNKNOWN")
        
        # FIX CORRUPTION: Remove # prefix (LightRAG internal marker)
        if entity_type and isinstance(entity_type, str) and entity_type.startswith("#"):
            clean_type = entity_type[1:]  # Remove '#' prefix
            entity["entity_type"] = clean_type
            entity_type = clean_type
            fixed_corruption += 1
            logger.debug(f"Fixed corruption: {entity.get('entity_name')} - #{clean_type} → {clean_type}")
        
        # Handle None/empty types
        if not entity_type or entity_type == "":
            entity["entity_type"] = "UNKNOWN"
            entity_type = "UNKNOWN"
        
        # Check if forbidden
        if entity_type in FORBIDDEN_TYPES:
            forbidden.append(entity)
    
    if fixed_corruption > 0:
        logger.info(f"  ✅ Fixed {fixed_corruption} corrupted types (removed # prefix)")
    
    logger.info(f"  Found {len(forbidden)} entities with forbidden types (out of {len(entities)} total)")
    return forbidden


def create_retyping_prompt(entities_batch: List[Dict]) -> str:
    """
    Create a focused prompt for retyping a batch of entities.
    
    Args:
        entities_batch: List of entities to retype (max 50 for efficiency)
    
    Returns:
        Prompt string for LLM
    """
    allowed_types_str = ", ".join(ALLOWED_TYPES)
    
    prompt = f"""You are an entity type classifier for government contracting documents.

TASK: Retype these entities using ONLY the allowed entity types below.

ALLOWED ENTITY TYPES (use EXACTLY these, lowercase with underscores):
{allowed_types_str}

FORBIDDEN TYPES (NEVER use these):
UNKNOWN, other, process, table, image, plan, policy, standard, instruction, system, regulation, framework, objective, methodology, approach, strategy, model

TYPING GUIDELINES:
- concept: Abstract ideas, business concepts, accounts, codes, processes
- document: Plans, policies, standards, regulations, manuals, reports
- deliverable: Contract deliverables with reference numbers (CDRLs, DIDs)
- technology: Systems, software, platforms, tools
- equipment: Physical assets, hardware, model numbers
- organization: Companies, agencies, departments, military units
- person: Individuals, job titles, roles
- location: Bases, facilities, geographic locations
- requirement: Must/should/may obligations from RFP
- clause: FAR/DFARS/agency supplement clauses
- section: RFP sections (A-M, J attachments)
- program: Government programs (e.g., MCPP II)
- event: Milestones, deadlines, reviews
- evaluation_factor: Section M scoring criteria
- submission_instruction: Section L instructions (page limits, format)
- strategic_theme: High-level themes, objectives
- statement_of_work: SOW/PWS sections
- performance_metric: QASP thresholds, AQLs, error rates, inspection criteria

ENTITIES TO RETYPE:
"""
    
    for i, entity in enumerate(entities_batch, 1):
        name = entity.get("entity_name", "Unknown")
        # Use entity_name as the primary content identifier
        source = name[:150]  # Truncate long content
        current_type = entity.get("entity_type", "UNKNOWN")
        prompt += f"\n{i}. Name: {name}\n   Current type: {current_type}\n"
    
    prompt += f"""
OUTPUT FORMAT (one line per entity, NO explanations):
1. <entity_type>
2. <entity_type>
...

Use ONLY lowercase entity types with underscores. NO other text.
"""
    
    return prompt


async def retype_entities_batch(
    entities_batch: List[Dict],
    llm_func: Callable[[str, str], Awaitable[str]],
) -> Dict[str, str]:
    """
    Retype a batch of entities using LLM.
    
    Args:
        entities_batch: List of entities to retype
        llm_func: LLM function (async) that takes (prompt, system_prompt) and returns response
    
    Returns:
        Dict mapping entity_name → new_entity_type
    """
    if not entities_batch:
        return {}
    
    prompt = create_retyping_prompt(entities_batch)
    system_prompt = "You are an expert entity type classifier for government contracting documents. Output ONLY entity types, one per line, using the exact allowed types provided."
    
    try:
        response = await llm_func(prompt, system_prompt)
        
        # Parse response: expect numbered lines like "1. concept"
        lines = response.strip().split("\n")
        retyped = {}
        
        for i, line in enumerate(lines):
            if i >= len(entities_batch):
                break  # More responses than entities (shouldn't happen)
            
            # Extract type from line (handle "1. concept" or just "concept")
            line = line.strip()
            if ". " in line:
                line = line.split(". ", 1)[1]
            
            entity_type = line.strip().lower()
            
            # Validate it's an allowed type
            if entity_type in ALLOWED_TYPES:
                entity_name = entities_batch[i].get("entity_name")
                retyped[entity_name] = entity_type
            else:
                # LLM output invalid type - fallback to concept
                entity_name = entities_batch[i].get("entity_name")
                retyped[entity_name] = "concept"
                logger.warning(f"LLM returned invalid type '{entity_type}' for '{entity_name}', using 'concept'")
        
        return retyped
    
    except Exception as e:
        logger.error(f"Failed to retype entities batch: {e}")
        # Fallback: retype all to 'concept'
        return {entity.get("entity_name"): "concept" for entity in entities_batch}


async def correct_entity_types(
    entities: List[Dict],
    llm_func: Callable[[str, str], Awaitable[str]],
    batch_size: int = 50,
) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Main entity type correction operation using unified BatchProcessor.
    
    Identifies entities with forbidden types and retypes them using LLM.
    Uses the centralized batching infrastructure for consistent processing.
    
    Args:
        entities: List of all entities from GraphML
        llm_func: LLM function for retyping
        batch_size: Number of entities to process per LLM call (default: 50)
    
    Returns:
        Tuple of (updated_entities_list, retyping_map)
        - updated_entities_list: All entities with forbidden types fixed
        - retyping_map: Dict of entity_name → new_type (for logging)
    """
    logger.info("🔧 Entity Type Correction Operation")
    
    # Identify entities with forbidden types
    forbidden = identify_forbidden_entities(entities)
    
    if not forbidden:
        logger.info("✅ No forbidden types found - correction not needed")
        return entities, {}
    
    # Use unified BatchProcessor for retyping
    processor = BatchProcessor(batch_size=batch_size)
    
    # Define batch processing function
    async def process_batch(batch: List[Dict]) -> Dict[str, str]:
        return await retype_entities_batch(batch, llm_func)
    
    # Process all forbidden entities in batches
    all_retypings = await processor.process_batches(
        items=forbidden,
        process_fn=process_batch,
        batch_name="Entity Type Correction",
        aggregate_fn=processor.merge_dict_results
    )
    
    # Apply retypings to entities list
    updated_count = 0
    for entity in entities:
        entity_name = entity.get("entity_name")
        if entity_name in all_retypings:
            old_type = entity.get("entity_type")
            new_type = all_retypings[entity_name]
            entity["entity_type"] = new_type
            updated_count += 1
            logger.debug(f"Retyped: '{entity_name}' from '{old_type}' → '{new_type}'")
    
    logger.info(f"✅ Entity Type Correction complete: {updated_count} entities retyped")
    logger.info(f"   Type distribution: {_count_types(all_retypings)}")
    
    return entities, all_retypings


def _count_types(retyping_map: Dict[str, str]) -> Dict[str, int]:
    """Helper to count distribution of new types after retyping."""
    counts = {}
    for new_type in retyping_map.values():
        counts[new_type] = counts.get(new_type, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


# Validation function for testing
def validate_no_forbidden_types(entities: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate that no forbidden types remain after cleanup.
    
    Args:
        entities: List of entities to validate
    
    Returns:
        Tuple of (is_valid, list_of_violations)
        - is_valid: True if no forbidden types found
        - list_of_violations: List of entity names still using forbidden types
    """
    violations = []
    for entity in entities:
        entity_type = entity.get("entity_type", "UNKNOWN")
        if entity_type in FORBIDDEN_TYPES:
            entity_name = entity.get("entity_name", "Unknown")
            violations.append(f"{entity_name} ({entity_type})")
    
    is_valid = len(violations) == 0
    return is_valid, violations
