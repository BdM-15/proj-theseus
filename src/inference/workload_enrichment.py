"""
Workload Metadata Enrichment - Semantic Post-Processing Enhancement
====================================================================

Purpose: Enrich REQUIREMENT entities with workload metadata for BOE development
Methodology: LLM-powered analysis using Shipley Capture principles
Integration: Runs after entity type correction, before relationship inference

Architecture:
- Analyzes REQUIREMENT entities only (451 in ISS RFP baseline)
- Adds Neo4j properties: has_workload_metric, workload_categories, labor_drivers, boe_relevance
- Uses 7 BOE categories: Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance
- Cost: ~$0.01-0.02 per RFP (451 requirements × 150 tokens avg = ~67K tokens)

Usage:
    from src.inference.workload_enrichment import enrich_workload_metadata
    
    stats = await enrich_workload_metadata(
        neo4j_io=neo4j_graph_io_instance,
        llm_func=async_llm_function
    )
"""

import logging
import json
from typing import Dict, List, Callable, Awaitable

logger = logging.getLogger(__name__)

# 7 BOE Categories (Shipley Methodology + Federal Contracting)
BOE_CATEGORIES = {
    "Labor": "FTE calculations, shift coverage, staffing ratios, skill mix, training requirements",
    "Materials": "Consumables, capital equipment, spare parts, GFE tracking, inventory levels",
    "ODCs": "Travel, facilities, subcontractor services, licenses, subscriptions",
    "QA": "Inspections, certifications, testing, regulatory compliance, audit requirements",
    "Logistics": "Delivery frequencies, distribution, warehousing, transportation, storage",
    "Lifecycle": "Preventive maintenance, warranties, technology refresh, replacement cycles",
    "Compliance": "Regulatory requirements (Berry, TAA, ITAR), security clearances, host nation"
}


def create_workload_analysis_prompt(requirement_entities: List[Dict]) -> str:
    """
    Create prompt for LLM to analyze workload metrics in requirements.
    
    Args:
        requirement_entities: List of REQUIREMENT entities to analyze (max 20 per batch)
    
    Returns:
        Prompt string for LLM
    """
    categories_desc = "\n".join([f"- **{cat}**: {desc}" for cat, desc in BOE_CATEGORIES.items()])
    
    prompt = f"""You are a government contracting cost estimator analyzing RFP requirements for Basis of Estimate (BOE) development.

TASK: Analyze these REQUIREMENT entities and extract workload metrics for cost proposal planning.

BOE CATEGORIES:
{categories_desc}

REQUIREMENTS TO ANALYZE:
"""
    
    for i, req in enumerate(requirement_entities, 1):
        name = req.get("entity_name", "Unknown")
        desc = req.get("description", "No description")[:300]  # Truncate long descriptions
        
        prompt += f"""
{i}. REQUIREMENT: {name}
   Description: {desc}
"""
    
    prompt += """
OUTPUT FORMAT (JSON array, one object per requirement):
[
  {
    "requirement_name": "24/7 Fitness Center Coverage",
    "has_workload_metric": true,
    "workload_categories": ["Labor", "Lifecycle"],
    "labor_drivers": {
      "shift_coverage": "24/7",
      "estimated_fte": 5.2,
      "shift_pattern": "3-shift rotation",
      "rationale": "Continuous coverage implies 5.2 FTEs (168 hrs/week ÷ 40 hrs/FTE)"
    },
    "materials_drivers": null,
    "odcs_drivers": null,
    "qa_drivers": {
      "inspection_frequency": "monthly",
      "compliance_requirements": ["95% uptime target"]
    },
    "logistics_drivers": null,
    "lifecycle_drivers": {
      "maintenance_frequency": "weekly equipment cleaning",
      "replacement_cycle": "annual equipment evaluation"
    },
    "compliance_drivers": null,
    "boe_relevance": {
      "labor": 0.95,
      "materials": 0.10,
      "qa": 0.30,
      "logistics": 0.05,
      "lifecycle": 0.60
    }
  }
]

EXTRACTION RULES:
1. Set has_workload_metric=true ONLY if the requirement contains quantifiable workload (FTE, frequency, quantity, SLA)
2. workload_categories: List all applicable BOE categories (1-3 typically)
3. For each category with workload, populate its _drivers object with specific metrics
4. Set _drivers=null if category not applicable
5. boe_relevance: Score 0.0-1.0 for each category's importance to this requirement
6. Extract implicit workload (e.g., "24/7 coverage" → calculate FTE)
7. Preserve exact quantities from requirement (e.g., "96 pallets/week", "95% uptime")

Return ONLY the JSON array. No explanations.
"""
    
    return prompt


async def analyze_requirements_batch(
    requirements: List[Dict],
    llm_func: Callable[[str, str], Awaitable[str]],
    batch_size: int = 20
) -> Dict[str, Dict]:
    """
    Analyze a batch of requirements and extract workload metadata.
    
    Args:
        requirements: List of REQUIREMENT entities
        llm_func: Async LLM function
        batch_size: Number of requirements per LLM call
    
    Returns:
        Dict mapping requirement_name → workload_metadata
    """
    if not requirements:
        return {}
    
    # Process in batches
    all_metadata = {}
    
    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        
        prompt = create_workload_analysis_prompt(batch)
        system_prompt = "You are an expert cost estimator for government contracting. Output ONLY valid JSON, no other text."
        
        try:
            response = await llm_func(prompt, system_prompt)
            
            # Parse JSON response
            metadata_list = json.loads(response)
            
            # Map to requirement names
            for metadata in metadata_list:
                req_name = metadata.get("requirement_name")
                if req_name:
                    all_metadata[req_name] = metadata
            
            logger.info(f"  ✅ Analyzed batch {i // batch_size + 1}: {len(metadata_list)} requirements processed")
        
        except json.JSONDecodeError as e:
            logger.error(f"  ❌ Failed to parse LLM response as JSON: {e}")
            logger.debug(f"  Response: {response[:500]}")
        except Exception as e:
            logger.error(f"  ❌ Error analyzing requirements batch: {e}")
    
    return all_metadata


async def enrich_workload_metadata(
    neo4j_io,
    llm_func: Callable[[str, str], Awaitable[str]],
    batch_size: int = 20
) -> Dict:
    """
    Main workload metadata enrichment operation.
    
    Steps:
    1. Load all REQUIREMENT entities from Neo4j
    2. Analyze each requirement with LLM to extract workload metrics
    3. Add metadata properties to Neo4j (has_workload_metric, workload_categories, etc.)
    4. Return statistics
    
    Args:
        neo4j_io: Neo4jGraphIO instance
        llm_func: Async LLM function
        batch_size: Number of requirements to process per LLM call
    
    Returns:
        Stats dict with enrichment results
    """
    logger.info("=" * 80)
    logger.info("📊 WORKLOAD METADATA ENRICHMENT")
    logger.info("=" * 80)
    
    # Step 1: Load REQUIREMENT entities
    logger.info("\n📥 Step 1: Loading REQUIREMENT entities from Neo4j...")
    all_entities = neo4j_io.get_all_entities()
    requirements = [e for e in all_entities if e.get("entity_type") == "requirement"]
    
    if not requirements:
        logger.warning("⚠️  No REQUIREMENT entities found - skipping enrichment")
        return {
            "status": "skipped",
            "reason": "no_requirements",
            "requirements_enriched": 0
        }
    
    logger.info(f"  ✅ Found {len(requirements)} REQUIREMENT entities")
    
    # Step 2: Analyze requirements with LLM
    logger.info(f"\n🔍 Step 2: Analyzing requirements for workload metrics...")
    logger.info(f"  Batch size: {batch_size} requirements per LLM call")
    
    workload_metadata = await analyze_requirements_batch(
        requirements=requirements,
        llm_func=llm_func,
        batch_size=batch_size
    )
    
    logger.info(f"\n  ✅ Analyzed {len(workload_metadata)} requirements")
    
    # Step 3: Update Neo4j with metadata
    logger.info(f"\n💾 Step 3: Updating Neo4j with workload metadata...")
    
    updates = []
    for req in requirements:
        req_name = req.get("entity_name")
        metadata = workload_metadata.get(req_name)
        
        if metadata:
            # Convert metadata to Neo4j properties (flatten nested dicts to JSON strings)
            props = {
                "has_workload_metric": metadata.get("has_workload_metric", False),
                "workload_categories": json.dumps(metadata.get("workload_categories", [])),
                "labor_drivers": json.dumps(metadata.get("labor_drivers")) if metadata.get("labor_drivers") else None,
                "materials_drivers": json.dumps(metadata.get("materials_drivers")) if metadata.get("materials_drivers") else None,
                "odcs_drivers": json.dumps(metadata.get("odcs_drivers")) if metadata.get("odcs_drivers") else None,
                "qa_drivers": json.dumps(metadata.get("qa_drivers")) if metadata.get("qa_drivers") else None,
                "logistics_drivers": json.dumps(metadata.get("logistics_drivers")) if metadata.get("logistics_drivers") else None,
                "lifecycle_drivers": json.dumps(metadata.get("lifecycle_drivers")) if metadata.get("lifecycle_drivers") else None,
                "compliance_drivers": json.dumps(metadata.get("compliance_drivers")) if metadata.get("compliance_drivers") else None,
                "boe_relevance": json.dumps(metadata.get("boe_relevance", {}))
            }
            
            updates.append({
                "id": req["id"],
                "properties": props
            })
    
    enriched_count = 0
    if updates:
        enriched_count = neo4j_io.update_entity_properties(updates)
        logger.info(f"  ✅ Updated {enriched_count} requirements with workload metadata")
    else:
        logger.info("  ⚠️  No requirements to update")
    
    # Step 4: Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("✅ WORKLOAD METADATA ENRICHMENT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"  Requirements analyzed:  {len(requirements)}")
    logger.info(f"  Requirements enriched:  {enriched_count}")
    logger.info(f"  Enrichment rate:        {enriched_count / len(requirements) * 100:.1f}%")
    logger.info("=" * 80)
    
    # Category breakdown
    category_counts = {cat: 0 for cat in BOE_CATEGORIES.keys()}
    for metadata in workload_metadata.values():
        for cat in metadata.get("workload_categories", []):
            if cat in category_counts:
                category_counts[cat] += 1
    
    logger.info("\n📊 BOE Category Distribution:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            logger.info(f"  {cat:15s}: {count:4d} requirements")
    
    return {
        "status": "success",
        "requirements_analyzed": len(requirements),
        "requirements_enriched": enriched_count,
        "enrichment_rate": enriched_count / len(requirements) if requirements else 0,
        "category_distribution": category_counts
    }
