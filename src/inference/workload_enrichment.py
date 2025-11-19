"""
Workload Enrichment for Government Contracting Requirements
============================================================

Enriches REQUIREMENT entities with workload metadata for:
- Labor staffing analysis and FTE estimation
- Bill of Materials (BOM) development
- Basis of Estimate (BOE) cost categorization
- Complexity and effort assessment

Uses LLM analysis to extract 7 BOE categories:
1. Labor - Direct labor, contractors, FTEs
2. Materials - Equipment, supplies, consumables
3. ODCs - Travel, subcontractors, licenses
4. QA - Quality assurance, inspections, compliance verification
5. Logistics - Transportation, delivery, warehousing
6. Lifecycle - Maintenance, sustainment, operations
7. Compliance - Regulatory, policy, documentation

Output properties added to REQUIREMENT entities:
- has_workload_metric: Boolean (always true after enrichment)
- workload_categories: Array of BOE category names
- boe_relevance: Dict of category -> confidence scores (0.0-1.0)
- labor_drivers: Array of labor-specific details
- material_needs: Array of material-specific details
- complexity_score: Integer 1-10
- complexity_rationale: String explaining complexity
- effort_estimate: String with effort description
- enriched_by: String identifier ("workload_analysis_v1")
"""

import logging
import json
from typing import Dict, List, Callable, Awaitable
from pathlib import Path

from src.inference.neo4j_graph_io import Neo4jGraphIO

logger = logging.getLogger(__name__)

# Standard BOE categories (validation enforces these exact names)
BOE_CATEGORIES = [
    "Labor", "Materials", "ODCs", "QA",
    "Logistics", "Lifecycle", "Compliance"
]


async def enrich_workload_metadata(
    neo4j_io: Neo4jGraphIO,
    llm_func: Callable[[str, str, str, float], Awaitable[str]],
    batch_size: int = 50,
    model: str = "grok-4-fast-reasoning",
    temperature: float = 0.1
) -> Dict[str, any]:
    """
    Enrich all REQUIREMENT entities with workload metadata.
    
    Args:
        neo4j_io: Neo4j graph I/O handler
        llm_func: Async LLM function (prompt, system_prompt, model, temperature) -> response
        batch_size: Number of requirements to process per LLM call
        model: LLM model name
        temperature: LLM temperature
    
    Returns:
        Dict with enrichment statistics
    """
    logger.info("🏗️ Starting workload enrichment...")
    
    # Load enrichment prompt
    prompt_path = Path("prompts/relationship_inference/workload_enrichment.md")
    if not prompt_path.exists():
        logger.error(f"Workload enrichment prompt not found: {prompt_path}")
        return {"requirements_enriched": 0, "error": "Prompt file missing"}
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_instructions = f.read()
    
    # Get all requirement entities
    all_entities = neo4j_io.get_all_entities()
    # STRICTLY filter for 'requirement' type.
    # 'performance_metric' entities (QASP thresholds) are intentionally EXCLUDED
    # as they represent standards/constraints, not the workload itself.
    requirements = [e for e in all_entities if e.get('entity_type') == 'requirement']
    
    total_requirements = len(requirements)
    logger.info(f"Found {total_requirements} requirement entities to enrich")
    
    if total_requirements == 0:
        logger.warning("No requirements found - skipping workload enrichment")
        return {"requirements_enriched": 0, "category_distribution": {}}
    
    # Process in batches
    enriched_count = 0
    category_distribution = {cat: 0 for cat in BOE_CATEGORIES}
    
    for i in range(0, total_requirements, batch_size):
        batch = requirements[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_requirements + batch_size - 1) // batch_size
        
        logger.info(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} requirements)...")
        
        # Initialize batch update list
        property_updates = []
        
        # Build entity lookup by elementId (same pattern as other algorithms)
        id_to_entity = {req['id']: req for req in batch}
        
        # Build entity JSON (matching pattern from Algorithms 1-6)
        requirements_json = json.dumps([{
            'id': req['id'],  # Neo4j elementId
            'name': req.get('entity_name', 'Unnamed'),
            'type': 'requirement',
            'description': req.get('description', '')[:300]
        } for req in batch], indent=2)
        
        # Build prompt
        prompt = f"""{prompt_instructions}

---

## Requirements to Analyze

{requirements_json}

---

## Task

Analyze all {len(batch)} requirements above and return a JSON array with workload metadata for each.

**CRITICAL INSTRUCTIONS:**
1. Return ONLY the JSON array - no markdown code blocks, no explanations, no additional text
2. Use the EXACT 'id' field from the JSON above for each "entity_id" field in your response
3. The 'id' field contains the Neo4j element ID - copy it exactly as shown

Return JSON array with {len(batch)} objects (one per requirement above):
[
  {{
    "entity_id": "COPY_EXACT_ID_FROM_JSON_ABOVE",
    "has_workload_metric": true,
    "workload_categories": ["Labor", "Materials"],
    "boe_relevance": {{"Labor": 0.95, "Materials": 0.80}},
    "labor_drivers": ["..."],
    "material_needs": ["..."],
    "complexity_score": 6,
    "complexity_rationale": "...",
    "effort_estimate": "...",
    "enriched_by": "workload_analysis_v1"
  }},
  ...
]
"""
        
        # Call LLM
        try:
            response = await llm_func(prompt, model=model, temperature=temperature)
            
            # Parse JSON response (handle markdown code blocks if present)
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            enrichments = json.loads(response_clean)
            
            if not isinstance(enrichments, list):
                logger.error(f"  LLM returned non-array response: {type(enrichments)}")
                continue
            
            # Update Neo4j with enrichment data
            for enrichment in enrichments:
                entity_id = enrichment.get('entity_id')
                if not entity_id:
                    logger.warning("  Enrichment missing entity_id, skipping")
                    continue
                
                # Validate entity_id exists in our batch (using id_to_entity lookup)
                if entity_id not in id_to_entity:
                    logger.warning(f"  Invalid entity_id '{entity_id}' not in batch, skipping")
                    continue
                
                # Validate BOE categories
                categories = enrichment.get('workload_categories', [])
                invalid_cats = [cat for cat in categories if cat not in BOE_CATEGORIES]
                if invalid_cats:
                    logger.warning(f"  Invalid BOE categories for {entity_id}: {invalid_cats}")
                    categories = [cat for cat in categories if cat in BOE_CATEGORIES]
                
                # Update category distribution
                for cat in categories:
                    category_distribution[cat] += 1
                
                # Prepare properties for Neo4j
                properties = {
                    'has_workload_metric': True,
                    'workload_categories': json.dumps(categories),  # Store as JSON string
                    'boe_relevance': json.dumps(enrichment.get('boe_relevance', {})),
                    'labor_drivers': json.dumps(enrichment.get('labor_drivers', [])),
                    'material_needs': json.dumps(enrichment.get('material_needs', [])),
                    'complexity_score': enrichment.get('complexity_score', 5),
                    'complexity_rationale': enrichment.get('complexity_rationale', ''),
                    'effort_estimate': enrichment.get('effort_estimate', ''),
                    'enriched_by': 'workload_analysis_v1'
                }
                
                # Add to batch update list
                property_updates.append({
                    'id': entity_id,  # entity_id IS the elementId (from LLM response)
                    'properties': properties
                })
                enriched_count += 1
            
            # Batch update all entities in Neo4j
            if property_updates:
                neo4j_io.update_entity_properties(property_updates)
            
            logger.info(f"    ✓ Enriched {len(enrichments)} requirements")
        
        except json.JSONDecodeError as e:
            logger.error(f"  Failed to parse LLM response as JSON: {e}")
            logger.debug(f"  Response: {response[:500]}")
            continue
        
        except Exception as e:
            logger.error(f"  Error processing batch {batch_num}: {e}")
            continue
    
    # Summary
    logger.info(f"✓ Workload enrichment complete: {enriched_count}/{total_requirements} requirements")
    logger.info(f"  BOE category distribution: {dict(category_distribution)}")
    
    return {
        "requirements_enriched": enriched_count,
        "total_requirements": total_requirements,
        "category_distribution": category_distribution,
        "enrichment_rate": (enriched_count / total_requirements * 100) if total_requirements > 0 else 0
    }
