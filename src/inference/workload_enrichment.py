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

import os
import logging
import asyncio
import json
from typing import Dict, List, Callable, Awaitable, Optional
from pathlib import Path
from pydantic import ValidationError

from src.inference.neo4j_graph_io import Neo4jGraphIO
from src.ontology.schema import (
    BOECategory, 
    WorkloadEnrichmentItem, 
    WorkloadEnrichmentResponse,
    normalize_boe_category
)
from src.utils.llm_client import call_llm_structured

logger = logging.getLogger(__name__)

# Standard BOE categories (now imported from schema, kept here for reference)
BOE_CATEGORIES = [cat.value for cat in BOECategory]


async def enrich_workload_metadata(
    neo4j_io: Neo4jGraphIO,
    batch_size: int = 10,  # Reduced to stay under 128K tokens (~54K/batch) with full 20K text
    model: str = None,
    temperature: float = 0.1,
    llm_func: Callable[[str, str, str, float], Awaitable[str]] = None  # Deprecated, kept for compatibility
) -> Dict[str, any]:
    """
    Enrich all REQUIREMENT entities with workload metadata using Instructor.
    
    Uses Instructor library for schema-enforced structured outputs:
    - Automatic JSON extraction from markdown responses
    - Pydantic schema validation at API level  
    - Built-in retry with error feedback to LLM
    
    Args:
        neo4j_io: Neo4j graph I/O handler
        batch_size: Number of requirements to process per LLM call
        model: LLM model name (defaults to REASONING_LLM_NAME)
        temperature: LLM temperature
        llm_func: DEPRECATED - kept for backward compatibility, ignored
    
    Returns:
        Dict with enrichment statistics
    """
    if model is None:
        # Use reasoning model for inference/enrichment tasks
        model = os.getenv("REASONING_LLM_NAME", "grok-4-fast-reasoning")
    
    logger.info("🔧 Starting workload enrichment...")
    
    # Load enrichment prompt (shared across all workers)
    prompt_path = Path("prompts/relationship_inference/workload_enrichment.md")
    if not prompt_path.exists():
        logger.error(f"Workload enrichment prompt not found: {prompt_path}")
        return {"requirements_enriched": 0, "error": "Prompt file missing"}
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_instructions = f.read()
    
    # Load chunk store to access raw text (SHARED CACHE - loaded once)
    workspace = neo4j_io.workspace
    chunk_store_path = Path(f"rag_storage/{workspace}/kv_store_text_chunks.json")
    chunk_store = {}
    if chunk_store_path.exists():
        logger.info(f"Loading text chunks from {chunk_store_path}...")
        try:
            with open(chunk_store_path, 'r', encoding='utf-8') as f:
                chunk_store = json.load(f)
            logger.info(f"Loaded {len(chunk_store)} text chunks")
        except Exception as e:
            logger.error(f"Failed to load chunk store: {e}")
    else:
        logger.warning(f"Chunk store not found at {chunk_store_path}")
    
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
    
    # PHASE 3A: Parallel batch processing with semaphore control
    # With batch_size=25, we can run more workers in parallel (8 vs extraction's 16)
    max_workers = int(os.getenv("WORKLOAD_MAX_WORKERS", os.getenv("MAX_ASYNC", "8")))
    if max_workers < 1:
        max_workers = 4
    
    # Prepare all batches upfront
    batches = []
    total_batches = (total_requirements + batch_size - 1) // batch_size
    for i in range(0, total_requirements, batch_size):
        batch = requirements[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        batches.append({
            'batch': batch,
            'batch_num': batch_num,
            'total_batches': total_batches
        })
    
    logger.info(f"  Processing {total_batches} batches with {max_workers} parallel workers...")
    
    # Shared state for tracking progress (thread-safe via asyncio)
    enriched_count = 0
    category_distribution = {cat: 0 for cat in BOE_CATEGORIES}
    
    # Semaphore to limit concurrent workers
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_batch_with_semaphore(batch_info: Dict) -> int:
        """Process a single batch with semaphore control."""
        nonlocal enriched_count, category_distribution
        
        async with semaphore:
            batch = batch_info['batch']
            batch_num = batch_info['batch_num']
            total_batches = batch_info['total_batches']
            
            logger.info(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} requirements)...")
            
            # Initialize batch update list
            property_updates = []
            
            # Build entity lookup by INDEX (LLM returns results in order)
            # Using index is more reliable than asking LLM to echo complex Neo4j element IDs
            index_to_entity = {idx: req for idx, req in enumerate(batch)}
            
            # Build entity JSON with RAW TEXT from chunks
            batch_data = []
            for idx, req in enumerate(batch):
                # Resolve raw text from chunks (using shared chunk_store cache)
                raw_text = ""
                source_ids = req.get('source_id', '')
                if source_ids and chunk_store:
                    chunk_ids = source_ids.split('<SEP>')
                    # Take first 3 chunks to get enough context (usually sufficient)
                    selected_chunks = chunk_ids[:3] 
                    chunks_content = []
                    for cid in selected_chunks:
                        if cid in chunk_store:
                            chunks_content.append(chunk_store[cid].get('content', ''))
                    
                    if chunks_content:
                        raw_text = "\n---\n".join(chunks_content)
                
                # Fallback to description if no chunks found
                if not raw_text:
                    raw_text = req.get('description', '')
                
                # Truncate to reasonable limit while preserving detail for enrichment
                # 10 reqs × 20K chars = 200K chars (~50K tokens) + 4K prompt
                # Total: ~54K tokens per batch (well under 128K threshold)
                display_text = raw_text[:20000] + "..." if len(raw_text) > 20000 else raw_text

                batch_data.append({
                    'index': idx,  # Use simple index instead of complex Neo4j element ID
                    'name': req.get('entity_name', 'Unnamed'),
                    'type': 'requirement',
                    'text_content': display_text 
                })
                
            requirements_json = json.dumps(batch_data, indent=2)
            
            # Build prompt
            prompt = f"""{prompt_instructions}

---

## Requirements to Analyze

{requirements_json}

---

## Task

Analyze all {len(batch)} requirements above and return a JSON object with workload metadata for each.

**CRITICAL INSTRUCTIONS:**
1. Return ONLY the JSON object - no markdown code blocks, no explanations, no additional text
2. Use the EXACT 'index' field from the JSON above for each "entity_index" field in your response
3. Return results in the SAME ORDER as the input (index 0, 1, 2, ...)
4. Wrap the array in a "requirements" key

Return JSON object with {len(batch)} items (one per requirement above):
{{
  "requirements": [
    {{
      "entity_index": 0,
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
}}
"""
            
            # Call LLM using Instructor for Pydantic-enforced structured output
            # Instructor handles: JSON extraction, schema validation, retries with error feedback
            batch_enriched = 0
            try:
                max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "128000"))
                max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
                
                # Use Instructor's call_llm_structured for schema-enforced output
                # This eliminates manual JSON parsing and adds error feedback to LLM on retry
                enrichment_response = await call_llm_structured(
                    prompt=prompt,
                    response_model=WorkloadEnrichmentResponse,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_output_tokens,
                    max_retries=max_retries
                )
                
                # Instructor already validated the response - get the requirements list
                enrichment_items = enrichment_response.requirements
                
                # Process each validated enrichment item
                for enrichment in enrichment_items:
                    
                    entity_index = enrichment.entity_index
                    
                    # Validate entity_index exists in our batch
                    if entity_index not in index_to_entity:
                        logger.warning(f"  Batch {batch_num}: Invalid entity_index '{entity_index}' not in batch (0-{len(batch)-1}), skipping")
                        continue
                    
                    # Get the actual entity and its Neo4j element ID
                    entity = index_to_entity[entity_index]
                    entity_id = entity['id']  # The real Neo4j element ID
                    
                    # Get validated categories (Pydantic already normalized them)
                    categories = enrichment.get_category_values()
                    
                    # Update category distribution (thread-safe since we're in async context)
                    for cat in categories:
                        category_distribution[cat] += 1
                    
                    # Prepare properties for Neo4j (use Pydantic model attributes directly)
                    properties = {
                        'has_workload_metric': True,
                        'workload_categories': json.dumps(categories),  # Store as JSON string
                        'boe_relevance': json.dumps(enrichment.boe_relevance),
                        'labor_drivers': json.dumps(enrichment.labor_drivers),
                        'material_needs': json.dumps(enrichment.material_needs),
                        'complexity_score': enrichment.complexity_score,
                        'complexity_rationale': enrichment.complexity_rationale,
                        'effort_estimate': enrichment.effort_estimate,
                        'enriched_by': 'workload_analysis_v1'
                    }
                    
                    # Add to batch update list
                    property_updates.append({
                        'id': entity_id,  # Neo4j element ID from our index_to_entity lookup
                        'properties': properties,
                        'enriched_by': 'workload_analysis_v1',
                    })
                    batch_enriched += 1
                
                # Batch update all entities in Neo4j
                if property_updates:
                    neo4j_io.update_entity_properties(property_updates)
            
            except Exception as e:
                logger.error(f"  Batch {batch_num}: Error processing: {e}")
                return 0
            
            # Log what we accomplished (even if partial)
            if batch_enriched > 0:
                logger.info(f"    ✅ Batch {batch_num}: Enriched {batch_enriched}/{len(batch)} requirements")
            else:
                logger.warning(f"    ⚠️ Batch {batch_num}: No requirements enriched (0/{len(batch)})")
            
            return batch_enriched
    
    # Process all batches in parallel with semaphore control
    batch_tasks = [process_batch_with_semaphore(batch_info) for batch_info in batches]
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    # Count enriched requirements
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"  Batch processing failed with exception: {result}")
        elif isinstance(result, int):
            enriched_count += result
    
    # Summary
    logger.info(f"✅ Workload enrichment complete: {enriched_count}/{total_requirements} requirements")
    logger.info(f"  BOE category distribution: {dict(category_distribution)}")
    
    return {
        "requirements_enriched": enriched_count,
        "total_requirements": total_requirements,
        "category_distribution": category_distribution,
        "enrichment_rate": (enriched_count / total_requirements * 100) if total_requirements > 0 else 0
    }
