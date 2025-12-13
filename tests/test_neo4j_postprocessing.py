"""
Test Neo4j Semantic Post-Processing
====================================

Quick validation of Neo4j post-processing without full document upload.

Usage:
    python -m pytest tests/test_neo4j_postprocessing.py -v
    
    OR for quick manual test:
    python tests/test_neo4j_postprocessing.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.semantic_post_processor import (
    _call_llm_async,
    _infer_entity_type,
    _infer_relationships_batch,
    _semantic_post_processor_neo4j
)
from src.inference.neo4j_graph_io import Neo4jGraphIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


async def test_llm_call():
    """Test 1: Verify async LLM calls work"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Async LLM Call")
    logger.info("="*60)
    
    try:
        response = await _call_llm_async(
            prompt="What is 2+2? Answer with just the number.",
            model=os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"),
            temperature=0.1
        )
        logger.info(f"✅ LLM Response: {response.strip()}")
        return True
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        return False


async def test_entity_type_inference():
    """Test 2: Verify entity type inference works"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Entity Type Inference")
    logger.info("="*60)
    
    test_entities = [
        ("Navy", "United States Department of Navy"),
        ("MCPP II", "Multi-Cloud Platform Program Phase 2"),
        ("Section L", "Instructions to Offerors"),
    ]
    
    success_count = 0
    for entity_name, description in test_entities:
        try:
            logger.info(f"\n  Testing: {entity_name}")
            entity_type = await _infer_entity_type(
                entity_name=entity_name,
                description=description,
                model=os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"),
                temperature=0.1
            )
            logger.info(f"  ✅ Inferred type: {entity_type}")
            success_count += 1
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
    
    logger.info(f"\n  Result: {success_count}/{len(test_entities)} successful")
    return success_count == len(test_entities)


async def test_relationship_inference():
    """Test 3: Verify relationship inference works"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Relationship Inference")
    logger.info("="*60)
    
    # Create mock entities with IDs
    test_entities = [
        {
            'id': 'test:1',
            'entity_name': 'Section L',
            'entity_type': 'section',
            'description': 'Instructions to Offerors - submission requirements'
        },
        {
            'id': 'test:2',
            'entity_name': 'Technical Proposal',
            'entity_type': 'deliverable',
            'description': 'Required submission document containing technical approach'
        },
        {
            'id': 'test:3',
            'entity_name': 'Past Performance',
            'entity_type': 'evaluation_factor',
            'description': 'Evaluation criteria for contractor experience'
        }
    ]
    
    try:
        relationships = await _infer_relationships_batch(
            entities=test_entities,
            existing_rels=[],
            model=os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"),
            temperature=0.1
        )
        
        logger.info(f"✅ Inferred {len(relationships)} relationships:")
        for rel in relationships:
            logger.info(f"  - {rel['source_id']} --[{rel['relationship_type']}]--> {rel['target_id']}")
            logger.info(f"    Confidence: {rel['confidence']}, Reason: {rel['reasoning'][:60]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Relationship inference failed: {e}")
        return False


async def test_neo4j_connection():
    """Test 4: Verify Neo4j connection works"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Neo4j Connection")
    logger.info("="*60)
    
    try:
        neo4j_io = Neo4jGraphIO()
        
        # Try to fetch entities
        logger.info("  Fetching entities from Neo4j...")
        entities = neo4j_io.get_all_entities()
        logger.info(f"  ✅ Found {len(entities)} entities")
        
        # Try to fetch relationships
        logger.info("  Fetching relationships from Neo4j...")
        relationships = neo4j_io.get_all_relationships()
        logger.info(f"  ✅ Found {len(relationships)} relationships")
        
        # Get type distributions
        entity_types = neo4j_io.get_entity_count_by_type()
        logger.info(f"  ✅ Entity types: {len(entity_types)} types")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"    - {entity_type}: {count}")
        
        neo4j_io.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        logger.error(f"   Check: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD env vars")
        return False


async def test_full_postprocessing():
    """Test 5: Run full post-processing on existing Neo4j data"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Full Post-Processing Pipeline")
    logger.info("="*60)
    
    # Check if we have data in Neo4j
    try:
        neo4j_io = Neo4jGraphIO()
        entities = neo4j_io.get_all_entities()
        neo4j_io.close()
        
        if not entities:
            logger.warning("⚠️  No entities in Neo4j - skipping full pipeline test")
            logger.info("   Upload a document first to test full pipeline")
            return None
        
        logger.info(f"  Running post-processing on {len(entities)} existing entities...")
        
        result = await _semantic_post_processor_neo4j(
            llm_model_name=os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"),
            temperature=0.1
        )
        
        logger.info("\n  Results:")
        logger.info(f"  ✅ Status: {result.get('status')}")
        logger.info(f"  ✅ Entities corrected: {result.get('entities_corrected', 0)}")
        logger.info(f"  ✅ Relationships inferred: {result.get('relationships_inferred', 0)}")
        logger.info(f"  ✅ Processing time: {result.get('processing_time', 0):.2f}s")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        logger.error(f"❌ Full pipeline failed: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all tests sequentially"""
    logger.info("\n" + "="*80)
    logger.info("🧪 NEO4J SEMANTIC POST-PROCESSING TEST SUITE")
    logger.info("="*80)
    
    # Check environment
    logger.info("\n📋 Environment Check:")
    required_vars = [
        "GRAPH_STORAGE",
        "NEO4J_URI",
        "NEO4J_USERNAME", 
        "NEO4J_PASSWORD",
        "LLM_MODEL",
        "LLM_BINDING_API_KEY",
        "LLM_BINDING_HOST"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "PASSWORD" in var:
                display = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display = value
            logger.info(f"  ✅ {var}: {display}")
        else:
            logger.error(f"  ❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        logger.error(f"\n❌ Missing environment variables: {', '.join(missing)}")
        logger.error("   Set these in your .env file before running tests")
        return False
    
    # Run tests
    results = {}
    
    results['llm_call'] = await test_llm_call()
    results['entity_inference'] = await test_entity_type_inference()
    results['relationship_inference'] = await test_relationship_inference()
    results['neo4j_connection'] = await test_neo4j_connection()
    
    # Only run full pipeline if we have Neo4j data
    if results['neo4j_connection']:
        results['full_pipeline'] = await test_full_postprocessing()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result is True else ("❌ FAIL" if result is False else "⏭️  SKIP")
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\n  Passed:  {passed}/{total}")
    logger.info(f"  Failed:  {failed}/{total}")
    logger.info(f"  Skipped: {skipped}/{total}")
    
    if failed == 0:
        logger.info("\n✅ ALL TESTS PASSED - Neo4j post-processing is working!")
    else:
        logger.info("\n❌ SOME TESTS FAILED - Check logs above for details")
    
    logger.info("="*80)
    
    return failed == 0


def main():
    """Entry point for manual testing"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Run tests
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Test suite crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
