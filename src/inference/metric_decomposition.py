"""
Metric Decomposition for Government Contracting Requirements
============================================================

Decomposes mixed REQUIREMENT entities that contain both work definitions
and performance metrics into separate entities.

Problem:
"Contractor shall clean floors daily with 95% accuracy" is often extracted
as a single REQUIREMENT. This contaminates workload analysis because
"95% accuracy" is a quality standard (surveillance), not a workload driver.

Solution:
This module scans REQUIREMENT entities for metric-like language and uses
LLM to split them into:
1. REQUIREMENT (Action): "Contractor shall clean floors daily"
2. PERFORMANCE_METRIC (Standard): "95% accuracy"

Linked via: REQUIREMENT --MEASURED_BY--> PERFORMANCE_METRIC
"""

import os
import logging
import json
from typing import Dict, List, Callable, Awaitable
from pathlib import Path

from src.inference.neo4j_graph_io import Neo4jGraphIO

logger = logging.getLogger(__name__)

# Keywords that suggest a requirement might contain a hidden metric
METRIC_KEYWORDS = [
    "%", "percent", "rate", "threshold", "AQL", "acceptable quality level",
    "error", "accuracy", "timeliness", "response time", "within", "exceed",
    "less than", "more than", "zero defects", "100%", "99.", "98.", "95."
]

async def decompose_metrics(
    neo4j_io: Neo4jGraphIO,
    llm_func: Callable[[str, str, str, float], Awaitable[str]],
    batch_size: int = 20,
    model: str = None,
    temperature: float = 0.0
) -> Dict[str, any]:
    """
    Scan requirements for embedded metrics and decompose them.
    
    Args:
        neo4j_io: Neo4j graph I/O handler
        llm_func: Async LLM function
        batch_size: Number of requirements to process per LLM call
        model: LLM model name
        temperature: LLM temperature
    
    Returns:
        Dict with decomposition statistics
    """
    if model is None:
        model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    
    logger.info("🔬 Starting metric decomposition...")
    
    # Get all requirement entities
    all_entities = neo4j_io.get_all_entities()
    requirements = [e for e in all_entities if e.get('entity_type') == 'requirement']
    
    # Filter for candidates that likely contain metrics
    candidates = []
    for req in requirements:
        desc = req.get('description', '')
        name = req.get('entity_name', '')
        
        # Handle None values safely
        if desc is None: desc = ""
        if name is None: name = ""
        
        text = f"{name} {desc}".lower()
        
        if any(kw in text for kw in METRIC_KEYWORDS):
            candidates.append(req)
            
    logger.info(f"Found {len(candidates)}/{len(requirements)} requirements with potential embedded metrics")
    
    if not candidates:
        return {"decomposed_count": 0, "candidates_count": 0}
        
    # Process in batches
    decomposed_count = 0
    new_metrics_created = 0
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(candidates) + batch_size - 1) // batch_size
        
        logger.info(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} candidates)...")
        
        # Build entity JSON
        candidates_json = json.dumps([{
            'id': req['id'],
            'name': req.get('entity_name', 'Unnamed'),
            'description': req.get('description', '')
        } for req in batch], indent=2)
        
        # Build prompt
        prompt = f"""
You are a Government Contracting Ontology Specialist.
Your task is to separate WORKLOAD (Actions) from SURVEILLANCE (Metrics).

Input: A list of REQUIREMENT entities that may contain embedded performance metrics.

For each entity, determine if it contains BOTH an action AND a metric.
If yes, split it. If no (or if it's purely one or the other), return null.

**Rules for Splitting:**
1. **REQUIREMENT (Action)**: The work to be done (e.g., "Clean floors", "Provide help desk").
2. **PERFORMANCE_METRIC (Standard)**: The measurement of success (e.g., "95% clean", "response < 4 hours").

**Example 1 (Needs Split):**
Input: "Contractor shall clean floors daily with 95% accuracy."
Output:
- Split: Yes
- Requirement: "Contractor shall clean floors daily"
- Metric: "95% accuracy" (Threshold: "95%")

**Example 2 (No Split - Pure Requirement):**
Input: "Contractor shall submit monthly reports."
Output: Split: No

**Example 3 (No Split - Pure Metric):**
Input: "Error rate shall not exceed 1%."
Output: 
- Split: Yes (Retype)
- Requirement: null (Delete original if it was purely a metric, or keep as metric)
- Metric: "Error rate shall not exceed 1%" (Threshold: "1%")

**JSON Output Format:**
Return a JSON array of objects. Only include objects where a change is needed.
[
  {{
    "original_id": "NEO4J_ID_FROM_INPUT",
    "action": "SPLIT", // or "RETYPE_AS_METRIC"
    "updated_requirement": {{
        "name": "New Name for Requirement",
        "description": "New Description (Action only)"
    }},
    "new_metric": {{
        "name": "Name of Metric",
        "description": "Description of Metric",
        "threshold": "Specific value (e.g. 95%)"
    }}
  }}
]

If "action" is "RETYPE_AS_METRIC", the original entity will be converted to PERFORMANCE_METRIC type.
If "action" is "SPLIT", the original entity is updated to be the Requirement, and a NEW entity is created for the Metric.

**Entities to Analyze:**
{candidates_json}
"""
        
        try:
            # Do not pass model as kwarg to avoid collision with LightRAG's bound model
            response = await llm_func(prompt, temperature=temperature)
            
            # Parse JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            changes = json.loads(response_clean.strip())
            
            if not isinstance(changes, list):
                continue
                
            # Apply changes
            entity_updates = [] # For retyping
            property_updates = [] # For updating descriptions
            new_relationships = [] # For linking
            # We need a way to create new entities. Neo4jGraphIO doesn't have a simple create_entity method exposed yet
            # but we can use a custom query or add a method.
            # For now, let's assume we can add a method or use a raw query.
            
            # Actually, let's add a create_entities method to Neo4jGraphIO first or use a direct query here if possible.
            # Since I can't edit Neo4jGraphIO easily while inside this function, I'll assume I can add it or use a workaround.
            # I'll use a raw query via the driver if needed, but better to extend the class.
            # For this file, I will assume `neo4j_io.create_entities` exists or I will implement a local helper.
            
            # Let's implement a local helper for creation since I can't modify the class in the same step.
            
            for change in changes:
                orig_id = change.get('original_id')
                action = change.get('action')
                
                if action == "RETYPE_AS_METRIC":
                    # Update type to performance_metric
                    entity_updates.append({
                        'id': orig_id,
                        'new_entity_type': 'performance_metric'
                    })
                    # Update properties if provided
                    if 'new_metric' in change:
                        props = change['new_metric']
                        property_updates.append({
                            'id': orig_id,
                            'properties': {
                                'entity_name': props.get('name'),
                                'description': props.get('description'),
                                'threshold': props.get('threshold')
                            }
                        })
                    decomposed_count += 1
                    
                elif action == "SPLIT":
                    # 1. Update original requirement (remove metric part)
                    if 'updated_requirement' in change:
                        req_props = change['updated_requirement']
                        property_updates.append({
                            'id': orig_id,
                            'properties': {
                                'entity_name': req_props.get('name'),
                                'description': req_props.get('description')
                            }
                        })
                    
                    # 2. Create new metric entity
                    if 'new_metric' in change:
                        metric_props = change['new_metric']
                        # We need to create this entity and link it.
                        # Since we don't have a create_entity method, we'll collect these 
                        # and run a custom Cypher query at the end of the batch.
                        metric_props['source_id'] = orig_id # Link back to source
                        # Add to a list to be processed
                        # We'll handle creation below
                        
                        # Define the creation query
                        create_query = f"""
                        MATCH (req) WHERE elementId(req) = $source_id
                        CREATE (m:`{neo4j_io.workspace}`:performance_metric {{
                            entity_id: $name,
                            entity_name: $name,
                            entity_type: 'performance_metric',
                            description: $description,
                            threshold: $threshold,
                            created_at: datetime(),
                            created_by: 'metric_decomposition'
                        }})
                        MERGE (req)-[:MEASURED_BY {{
                            source: 'metric_decomposition',
                            created_at: datetime()
                        }}]->(m)
                        """
                        
                        # Execute creation immediately for simplicity
                        with neo4j_io.driver.session(database=neo4j_io.database) as session:
                            session.run(create_query, 
                                source_id=orig_id,
                                name=metric_props.get('name'),
                                description=metric_props.get('description'),
                                threshold=metric_props.get('threshold')
                            )
                        new_metrics_created += 1
                    
                    decomposed_count += 1

            # Apply batch updates
            if entity_updates:
                neo4j_io.update_entity_types(entity_updates)
            if property_updates:
                neo4j_io.update_entity_properties(property_updates)
                
        except Exception as e:
            logger.error(f"Error in metric decomposition batch: {e}")
            continue
            
    logger.info(f"✓ Decomposition complete. Processed {decomposed_count} entities, created {new_metrics_created} new metrics.")
    return {
        "candidates_count": len(candidates),
        "decomposed_count": decomposed_count,
        "new_metrics_created": new_metrics_created
    }
