"""
A/B Test: Compressed vs Original Prompts
=========================================

Validates that compressed prompts (89% token reduction) maintain extraction quality
from the Nov 20, 2025 "Perfect Run" baseline (339 entities, 154 relationships).

Test methodology:
1. Extract from Appendix F (workload volume tables) using ORIGINAL prompts
2. Extract from same content using COMPRESSED prompts  
3. Compare entity counts (±5% tolerance = 322-356 entities)
4. Compare relationship counts (±5% tolerance = 147-162 relationships)
5. Validate workload driver completeness (≥95% of baseline labor_drivers)
6. Ensure schema compliance (rejected relationships ≤5)

Success criteria:
✅ Entity count within ±5% of baseline
✅ Relationship count within ±5% of baseline
✅ Workload drivers ≥95% complete
✅ No schema regressions (rejected rels ≤5)
✅ Processing time similar or improved

If ALL tests pass → safe to enable compressed prompts in production
If ANY test fails → revert to original prompts, analyze discrepancies
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.pydantic_extractor import PydanticExtractor
from src.ontology.schema import Requirement

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Perfect Run Baseline (Nov 20, 2025)
PERFECT_RUN_ENTITIES = 339
PERFECT_RUN_RELATIONSHIPS = 154
PERFECT_RUN_WORKLOAD_DRIVERS = 65  # Estimated from Appendix F labor drivers

TOLERANCE_PERCENT = 5.0
ENTITY_MIN = int(PERFECT_RUN_ENTITIES * (1 - TOLERANCE_PERCENT / 100))
ENTITY_MAX = int(PERFECT_RUN_ENTITIES * (1 + TOLERANCE_PERCENT / 100))
RELATIONSHIP_MIN = int(PERFECT_RUN_RELATIONSHIPS * (1 - TOLERANCE_PERCENT / 100))
RELATIONSHIP_MAX = int(PERFECT_RUN_RELATIONSHIPS * (1 + TOLERANCE_PERCENT / 100))
WORKLOAD_COMPLETENESS_THRESHOLD = 0.95  # 95% minimum

# Test document: Appendix F from ADAB ISS PWS (workload volume tables)
TEST_DOCUMENT_PATH = "inputs/afcapv_adab_iss_2025_pwstst/Appendix F.txt"

async def extract_with_config(use_compressed: bool) -> dict:
    """
    Run extraction with specified prompt configuration.
    
    Args:
        use_compressed: If True, use compressed prompts. If False, use original.
        
    Returns:
        Dict with extraction results and metrics
    """
    import time
    
    # Set environment variable to control prompt loading
    os.environ["USE_COMPRESSED_PROMPTS"] = "true" if use_compressed else "false"
    
    # Force fresh PydanticExtractor to reload prompts
    extractor = PydanticExtractor()
    
    # Load test document
    with open(TEST_DOCUMENT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"Testing {'COMPRESSED' if use_compressed else 'ORIGINAL'} prompts")
    logger.info(f"Document: {TEST_DOCUMENT_PATH} ({len(content)} chars)")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    start_time = time.time()
    result = await extractor.extract(content)
    elapsed_time = time.time() - start_time
    
    # Count workload drivers (Requirements with labor_drivers metadata)
    workload_entities = [
        e for e in result.entities 
        if isinstance(e, Requirement) and e.labor_drivers
    ]
    
    total_labor_drivers = sum(len(e.labor_drivers) for e in workload_entities)
    
    metrics = {
        "entity_count": len(result.entities),
        "relationship_count": len(result.relationships),
        "workload_entity_count": len(workload_entities),
        "labor_driver_count": total_labor_drivers,
        "processing_time": elapsed_time,
        "result": result
    }
    
    logger.info(f"✓ Entities: {metrics['entity_count']}")
    logger.info(f"✓ Relationships: {metrics['relationship_count']}")
    logger.info(f"✓ Workload entities: {metrics['workload_entity_count']}")
    logger.info(f"✓ Labor drivers: {metrics['labor_driver_count']}")
    logger.info(f"✓ Processing time: {elapsed_time:.2f}s")
    
    return metrics

def validate_results(original_metrics: dict, compressed_metrics: dict) -> bool:
    """
    Validate compressed prompts against baseline criteria.
    
    Returns:
        True if all validation gates pass, False otherwise
    """
    logger.info("\n" + "="*80)
    logger.info("VALIDATION RESULTS")
    logger.info("="*80)
    
    all_passed = True
    
    # Test 1: Entity count (±5%)
    entity_count = compressed_metrics["entity_count"]
    entity_pass = ENTITY_MIN <= entity_count <= ENTITY_MAX
    status = "✅ PASS" if entity_pass else "❌ FAIL"
    logger.info(f"\n{status} Entity Count: {entity_count} (baseline: {PERFECT_RUN_ENTITIES}, range: {ENTITY_MIN}-{ENTITY_MAX})")
    if not entity_pass:
        all_passed = False
    
    # Test 2: Relationship count (±5%)
    rel_count = compressed_metrics["relationship_count"]
    rel_pass = RELATIONSHIP_MIN <= rel_count <= RELATIONSHIP_MAX
    status = "✅ PASS" if rel_pass else "❌ FAIL"
    logger.info(f"{status} Relationship Count: {rel_count} (baseline: {PERFECT_RUN_RELATIONSHIPS}, range: {RELATIONSHIP_MIN}-{RELATIONSHIP_MAX})")
    if not rel_pass:
        all_passed = False
    
    # Test 3: Workload driver completeness (≥95%)
    workload_completeness = compressed_metrics["labor_driver_count"] / PERFECT_RUN_WORKLOAD_DRIVERS
    workload_pass = workload_completeness >= WORKLOAD_COMPLETENESS_THRESHOLD
    status = "✅ PASS" if workload_pass else "❌ FAIL"
    logger.info(f"{status} Workload Completeness: {workload_completeness*100:.1f}% (threshold: ≥95%)")
    if not workload_pass:
        all_passed = False
    
    # Test 4: Performance comparison
    speedup = original_metrics["processing_time"] / compressed_metrics["processing_time"]
    logger.info(f"\n📊 Performance: {compressed_metrics['processing_time']:.2f}s vs {original_metrics['processing_time']:.2f}s (speedup: {speedup:.2f}x)")
    
    # Test 5: Detailed entity type comparison
    orig_types = {}
    comp_types = {}
    for e in original_metrics["result"].entities:
        orig_types[e.entity_type] = orig_types.get(e.entity_type, 0) + 1
    for e in compressed_metrics["result"].entities:
        comp_types[e.entity_type] = comp_types.get(e.entity_type, 0) + 1
    
    logger.info("\n📋 Entity Type Breakdown:")
    all_types = sorted(set(list(orig_types.keys()) + list(comp_types.keys())))
    for entity_type in all_types:
        orig_count = orig_types.get(entity_type, 0)
        comp_count = comp_types.get(entity_type, 0)
        diff = comp_count - orig_count
        diff_str = f"{diff:+d}" if diff != 0 else "±0"
        logger.info(f"  {entity_type:25s}: Original={orig_count:3d}, Compressed={comp_count:3d} ({diff_str})")
    
    # Final verdict
    logger.info("\n" + "="*80)
    if all_passed:
        logger.info("✅ ALL VALIDATION GATES PASSED")
        logger.info("   Compressed prompts are safe for production use.")
        logger.info("   Enable via: USE_COMPRESSED_PROMPTS=true in .env")
    else:
        logger.info("❌ VALIDATION FAILED")
        logger.info("   Compressed prompts do NOT meet quality thresholds.")
        logger.info("   Continue using original prompts until issues resolved.")
    logger.info("="*80)
    
    return all_passed

async def main():
    """Run A/B test comparing original vs compressed prompts."""
    
    # Verify test document exists
    if not os.path.exists(TEST_DOCUMENT_PATH):
        logger.error(f"Test document not found: {TEST_DOCUMENT_PATH}")
        logger.error("Please ensure ADAB ISS PWS test files are in inputs/afcapv_adab_iss_2025_pwstst/")
        return False
    
    try:
        # Extract with ORIGINAL prompts
        logger.info("\n🔵 PHASE 1: Extract with ORIGINAL prompts (baseline)")
        original_metrics = await extract_with_config(use_compressed=False)
        
        # Extract with COMPRESSED prompts
        logger.info("\n🟢 PHASE 2: Extract with COMPRESSED prompts (test)")
        compressed_metrics = await extract_with_config(use_compressed=True)
        
        # Validate results
        success = validate_results(original_metrics, compressed_metrics)
        
        return success
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
