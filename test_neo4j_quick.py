"""
Quick Neo4j Post-Processing Test
=================================

Minimal test to verify Neo4j post-processing works.
Run this instead of waiting 45 minutes for full document processing.

Usage:
    python test_neo4j_quick.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment FIRST
from dotenv import load_dotenv
load_dotenv()

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Test imports
try:
    from src.inference.semantic_post_processor import _call_llm_async, _infer_entity_type
    from src.inference.neo4j_graph_io import Neo4jGraphIO
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def quick_test():
    """Quick validation test"""
    print("\n" + "="*60)
    print("🧪 QUICK NEO4J POST-PROCESSING TEST")
    print("="*60)
    
    # Test 1: LLM call
    print("\n1️⃣  Testing async LLM call...")
    try:
        response = await _call_llm_async("What is 2+2? Answer with just the number.", temperature=0.1)
        print(f"   ✅ LLM responded: {response.strip()}")
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        return False
    
    # Test 2: Entity type inference
    print("\n2️⃣  Testing entity type inference...")
    try:
        entity_type = await _infer_entity_type(
            entity_name="US Navy",
            description="United States Department of Navy",
            model=os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
            temperature=0.1
        )
        print(f"   ✅ Inferred type: {entity_type}")
    except Exception as e:
        print(f"   ❌ Entity inference failed: {e}")
        return False
    
    # Test 3: Neo4j connection
    print("\n3️⃣  Testing Neo4j connection...")
    try:
        neo4j_io = Neo4jGraphIO()
        entities = neo4j_io.get_all_entities()
        rels = neo4j_io.get_all_relationships()
        print(f"   ✅ Connected to Neo4j")
        print(f"   ✅ Found {len(entities)} entities, {len(rels)} relationships")
        
        if entities:
            types = neo4j_io.get_entity_count_by_type()
            print(f"   ✅ Entity types: {', '.join(list(types.keys())[:5])}")
        
        neo4j_io.close()
    except Exception as e:
        print(f"   ❌ Neo4j connection failed: {e}")
        print(f"      Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return False
    
    # Test 4: Full pipeline (if data exists)
    if entities:
        print("\n4️⃣  Testing full post-processing pipeline...")
        print(f"   Running on existing {len(entities)} entities...")
        try:
            from src.inference.semantic_post_processor import _semantic_post_processor_neo4j
            
            result = await _semantic_post_processor_neo4j(
                llm_model_name=os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
                temperature=0.1
            )
            
            print(f"   ✅ Status: {result.get('status')}")
            print(f"   ✅ Entities corrected: {result.get('entities_corrected', 0)}")
            print(f"   ✅ Relationships inferred: {result.get('relationships_inferred', 0)}")
            print(f"   ✅ Time: {result.get('processing_time', 0):.2f}s")
            
        except Exception as e:
            print(f"   ❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n4️⃣  Skipping full pipeline test (no data in Neo4j)")
        print("   Upload a document first to test full pipeline")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n💡 Next steps:")
    print("   1. Restart your app: python app.py")
    print("   2. Upload an RFP via http://localhost:9621/webui")
    print("   3. Check Neo4j Browser: http://localhost:7474")
    print("")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
