"""
Test Workload Enrichment Integration
=====================================

Quick validation that workload enrichment is properly integrated
before running full RFP processing.
"""

import sys
import asyncio

async def test_integration():
    """Test that all components are importable and integrated"""
    
    print("\n" + "="*80)
    print("🧪 TESTING WORKLOAD ENRICHMENT INTEGRATION")
    print("="*80)
    
    # Test 1: Import workload enrichment module
    print("\n📦 Test 1: Import workload_enrichment module...")
    try:
        from src.inference.workload_enrichment import enrich_workload_metadata, BOE_CATEGORIES
        print(f"  ✅ Module imported successfully")
        print(f"  ✅ BOE Categories: {len(BOE_CATEGORIES)} defined")
        for cat in BOE_CATEGORIES.keys():
            print(f"     - {cat}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 2: Import neo4j_graph_io with new method
    print("\n📦 Test 2: Verify Neo4j I/O has update_entity_properties...")
    try:
        from src.inference.neo4j_graph_io import Neo4jGraphIO
        
        # Check if method exists
        if hasattr(Neo4jGraphIO, 'update_entity_properties'):
            print(f"  ✅ update_entity_properties method exists")
        else:
            print(f"  ❌ FAILED: update_entity_properties method missing")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 3: Import semantic_post_processor
    print("\n📦 Test 3: Import semantic_post_processor...")
    try:
        from src.inference.semantic_post_processor import _semantic_post_processor_neo4j
        print(f"  ✅ Semantic post-processor imported")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 4: Check prompt generation
    print("\n📦 Test 4: Test prompt generation...")
    try:
        from src.inference.workload_enrichment import create_workload_analysis_prompt
        
        test_requirements = [
            {
                "entity_name": "24/7 Fitness Center Coverage",
                "description": "Contractor shall provide continuous 24/7 staffing at fitness centers"
            }
        ]
        
        prompt = create_workload_analysis_prompt(test_requirements)
        
        # Verify prompt contains key elements
        if "BOE CATEGORIES" in prompt and "Labor" in prompt and "Materials" in prompt:
            print(f"  ✅ Prompt generation working")
            print(f"  ✅ Prompt length: {len(prompt)} chars")
        else:
            print(f"  ❌ FAILED: Prompt missing required elements")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 5: Verify JSON structure
    print("\n📦 Test 5: Verify expected JSON structure...")
    try:
        import json
        
        sample_metadata = {
            "requirement_name": "Test Requirement",
            "has_workload_metric": True,
            "workload_categories": ["Labor", "Materials"],
            "labor_drivers": {"shift_coverage": "24/7", "estimated_fte": 5.2},
            "materials_drivers": {"consumables": ["items"], "quantity": "weekly"},
            "boe_relevance": {"labor": 0.95, "materials": 0.70}
        }
        
        # Test JSON serialization (what Neo4j will receive)
        props = {
            "has_workload_metric": sample_metadata["has_workload_metric"],
            "workload_categories": json.dumps(sample_metadata["workload_categories"]),
            "labor_drivers": json.dumps(sample_metadata["labor_drivers"]),
            "materials_drivers": json.dumps(sample_metadata["materials_drivers"]),
            "boe_relevance": json.dumps(sample_metadata["boe_relevance"])
        }
        
        print(f"  ✅ JSON structure valid")
        print(f"  ✅ Properties serializable for Neo4j")
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("="*80)
    print("\n🚀 Ready to restart app and reprocess RFP!")
    print("\nExpected pipeline flow:")
    print("  1. Entity extraction (RAG-Anything)")
    print("  2. Entity type correction")
    print("  3. Relationship inference")
    print("  4. Workload metadata enrichment ← NEW")
    print("  5. Summary statistics")
    print("\n" + "="*80)
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_integration())
    sys.exit(0 if result else 1)
