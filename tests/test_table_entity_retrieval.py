#!/usr/bin/env python
"""
Test script to verify table entity storage and retrieval in Neo4j.

This test validates:
1. Table entities are stored in Neo4j with correct provenance tags
2. Table entities link properly to text chunks
3. Table-specific queries retrieve table entities (equipment, frequencies, quantities)
4. Knowledge graph traversal includes table-sourced data

Usage:
    python tests/test_table_entity_retrieval.py
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import RAGAnything for query testing
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc


class TableEntityTester:
    """Test harness for table entity storage and retrieval."""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
        self.workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025_pwstst_4mod")
        self.working_dir = f"./rag_storage/{self.workspace}"
        
        self.driver = None
        self.rag = None
        
    def connect_neo4j(self):
        """Establish Neo4j connection."""
        print(f"🔌 Connecting to Neo4j at {self.neo4j_uri}")
        print(f"   Workspace: {self.workspace}")
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Test connection
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS test")
            print("✅ Neo4j connection successful")
            
    def close_neo4j(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")
    
    def run_cypher_query(self, query, params=None):
        """Execute Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    
    def test_1_entity_counts(self):
        """Test 1: Verify total entity counts (text + tables)."""
        print("\n" + "="*80)
        print("TEST 1: Entity Count Verification")
        print("="*80)
        
        # Count all entities in workspace (using label, not property)
        query = f"""
        MATCH (n:{self.workspace})
        RETURN count(n) as total_entities
        """
        result = self.run_cypher_query(query)
        total = result[0]["total_entities"] if result else 0
        
        print(f"📊 Total entities in workspace: {total}")
        print(f"   Expected: ~795 (368 text + 427 table)")
        
        if 750 <= total <= 850:
            print("✅ PASS: Entity count within expected range")
            return True
        else:
            print(f"⚠️  WARNING: Entity count {total} outside expected range 750-850")
            return False
    
    def test_2_table_entity_identification(self):
        """Test 2: Identify entities sourced from tables via provenance tags."""
        print("\n" + "="*80)
        print("TEST 2: Table Entity Identification")
        print("="*80)
        
        # Find entities with table provenance tags [TABLE-P{page}]
        query = f"""
        MATCH (n:{self.workspace})
        WHERE n.source_id CONTAINS '[TABLE-P'
        RETURN 
            count(n) as table_entity_count,
            collect(DISTINCT n.entity_type)[0..10] as entity_types_sample,
            collect(n.entity_name)[0..5] as entity_names_sample
        """
        result = self.run_cypher_query(query)
        
        if not result:
            print("❌ FAIL: No results returned from query")
            return False
            
        data = result[0]
        count = data.get("table_entity_count", 0)
        types = data.get("entity_types_sample", [])
        names = data.get("entity_names_sample", [])
        
        print(f"📊 Table-sourced entities: {count}")
        print(f"   Expected: ~427")
        print(f"   Entity types (sample): {types}")
        print(f"   Entity names (sample): {names}")
        
        if 400 <= count <= 450:
            print("✅ PASS: Table entity count within expected range")
            return True
        else:
            print(f"❌ FAIL: Table entity count {count} outside expected range 400-450")
            return False
    
    def test_3_workload_relevant_tables(self):
        """Test 3: Find table entities related to workload drivers."""
        print("\n" + "="*80)
        print("TEST 3: Workload-Relevant Table Entities")
        print("="*80)
        
        # Search for equipment, frequency, quantity, staffing entities from tables
        query = f"""
        MATCH (n:{self.workspace})
        WHERE n.source_id CONTAINS '[TABLE-P'
          AND (
            n.entity_name CONTAINS 'equipment' OR
            n.entity_name CONTAINS 'frequency' OR
            n.entity_name CONTAINS 'quantity' OR
            n.entity_name CONTAINS 'staffing' OR
            n.entity_name CONTAINS 'service' OR
            n.entity_name CONTAINS 'meal' OR
            n.description CONTAINS 'equipment' OR
            n.description CONTAINS 'frequency' OR
            n.description CONTAINS 'staffing' OR
            n.entity_type = 'EQUIPMENT' OR
            n.entity_type = 'WORKLOAD_DRIVER'
          )
        RETURN 
            count(n) as workload_table_entities,
            collect(DISTINCT n.entity_type) as entity_types,
            n.entity_name as name,
            n.entity_type as type,
            substring(n.source_id, 0, 50) as source
        LIMIT 10
        """
        result = self.run_cypher_query(query)
        
        if not result:
            print("⚠️  No workload-relevant table entities found")
            return False
            
        count = len(result)
        types = set(r.get("type") for r in result)
        
        print(f"📊 Workload-relevant table entities: {count}")
        print(f"   Entity types: {list(types)}")
        print(f"\n   Sample entities:")
        for entity in result[:10]:
            print(f"   - {entity['name']} ({entity['type']})")
            print(f"     Source: {entity['source']}")
        
        if count > 0:
            print(f"✅ PASS: Found {count} workload-relevant table entities")
            return True
        else:
            print("⚠️  WARNING: No workload-relevant table entities found")
            return False
    
    def test_4_table_to_chunk_linkage(self):
        """Test 4: Verify table entities link to text chunks."""
        print("\n" + "="*80)
        print("TEST 4: Table→Chunk Linkage Verification")
        print("="*80)
        
        # Check if table entities have source_id references to chunks
        query = f"""
        MATCH (n:{self.workspace})
        WHERE n.source_id CONTAINS '[TABLE-P'
        WITH n LIMIT 10
        RETURN 
            n.entity_name as name,
            n.entity_type as type,
            n.source_id as chunk_references
        """
        result = self.run_cypher_query(query)
        
        print(f"📊 Sample table entities with chunk references:")
        for record in result:
            print(f"   - {record['name']} ({record['type']})")
            print(f"     References: {record['chunk_references'][:100]}...")
        
        if result and all(r['chunk_references'] for r in result):
            print("✅ PASS: Table entities have chunk references")
            return True
        else:
            print("❌ FAIL: Some table entities lack chunk references")
            return False
    
    async def test_5_table_specific_query(self):
        """Test 5: Execute table-specific query via RAGAnything."""
        print("\n" + "="*80)
        print("TEST 5: Table-Specific Query Execution")
        print("="*80)
        
        # Initialize RAG instance with existing LightRAG data
        print("🔧 Initializing RAGAnything with existing workspace...")
        
        # Import LightRAG to load existing instance
        from lightrag import LightRAG
        
        config = RAGAnythingConfig(
            working_dir=self.working_dir,
            enable_image_processing=False,
            enable_table_processing=False,  # Already processed
            enable_equation_processing=False,
        )
        
        # LLM function
        async def llm_model_func(
            prompt, system_prompt=None, history_messages=[], **kwargs
        ) -> str:
            return await openai_complete_if_cache(
                "grok-4-fast-reasoning",
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=os.getenv("LLM_BINDING_API_KEY"),
                base_url="https://api.x.ai/v1",
                **kwargs,
            )
        
        # Embedding function
        async def embedding_func(texts: list[str]) -> list[list[float]]:
            return await openai_embed(
                texts,
                model="text-embedding-3-large",
                api_key=os.getenv("EMBEDDING_BINDING_API_KEY"),
                base_url="https://api.openai.com/v1",
            )
        
        # Load existing LightRAG instance
        lightrag_instance = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
        )
        
        self.rag = RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
            lightrag_instance=lightrag_instance,  # Pass existing instance
        )
        
        print("✅ RAGAnything initialized")
        
        # Test queries
        queries = [
            "What equipment types, quantities, and service frequencies are specified in Appendix H tables?",
            "List all equipment inventories, staffing requirements, and service schedules from the tables.",
            "What meal service frequencies and dining facility equipment are required?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 80)
            
            try:
                result = await self.rag.aquery(query, mode="hybrid")
                print(f"Response length: {len(result)} characters")
                print(f"\nResponse preview (first 500 chars):")
                print(result[:500])
                
                # Check if response mentions tables or structured data
                has_table_indicators = any(keyword in result.lower() for keyword in [
                    'table', 'equipment', 'frequency', 'quantity', 'appendix h',
                    'staffing', 'inventory', 'schedule'
                ])
                
                if has_table_indicators:
                    print("✅ Response includes table-related content")
                else:
                    print("⚠️  Response may not include table entities")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        print("\n✅ PASS: Table-specific queries executed successfully")
        return True
    
    def test_6_relationship_traversal(self):
        """Test 6: Verify relationships connect table entities to text entities."""
        print("\n" + "="*80)
        print("TEST 6: Table↔Text Relationship Traversal")
        print("="*80)
        
        # Find relationships where one entity is from table, other from text
        query = f"""
        MATCH (t:{self.workspace})-[r]-(n:{self.workspace})
        WHERE t.source_id CONTAINS '[TABLE-P'
          AND NOT n.source_id CONTAINS '[TABLE-P'
        RETURN 
            t.entity_name as table_entity,
            n.entity_name as text_entity,
            r.description as relationship
        LIMIT 10
        """
        result = self.run_cypher_query(query)
        
        if not result:
            print("⚠️  No cross-modal relationships found")
            return False
            
        count = len(result)
        
        print(f"📊 Table↔Text relationships: {count}")
        print(f"\n   Sample relationships:")
        for rel in result:
            print(f"   - {rel['table_entity']} ↔ {rel['text_entity']}")
            print(f"     Relationship: {rel['relationship'][:100] if rel['relationship'] else 'None'}...")
        
        if count > 0:
            print(f"✅ PASS: Found {count} cross-modal relationships")
            return True
        else:
            print("⚠️  WARNING: No cross-modal relationships found")
            print("   This may indicate table entities are isolated from text entities")
            return False
    
    async def run_all_tests(self):
        """Execute all tests in sequence."""
        print("="*80)
        print("TABLE ENTITY RETRIEVAL TEST SUITE")
        print("="*80)
        print(f"Workspace: {self.workspace}")
        print(f"Working Directory: {self.working_dir}")
        print(f"Neo4j URI: {self.neo4j_uri}")
        print("="*80)
        
        results = {}
        
        try:
            self.connect_neo4j()
            
            results['test_1_counts'] = self.test_1_entity_counts()
            results['test_2_table_identification'] = self.test_2_table_entity_identification()
            results['test_3_workload_relevance'] = self.test_3_workload_relevant_tables()
            results['test_4_chunk_linkage'] = self.test_4_table_to_chunk_linkage()
            results['test_5_query_execution'] = await self.test_5_table_specific_query()
            results['test_6_relationships'] = self.test_6_relationship_traversal()
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_neo4j()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("-" * 80)
        print(f"Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - Review results above")
            return False


async def main():
    """Main entry point."""
    tester = TableEntityTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
