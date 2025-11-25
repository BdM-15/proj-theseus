import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.kg.neo4j_impl import Neo4JStorage

async def main():
    # Use the LightRAG/Neo4j storage layer directly
    working_dir = "./rag_storage/afcapv_adab_iss_2025_pwstst_4mod"
    
    rag = LightRAG(
        working_dir=working_dir,
        enable_llm_cache=True,
        graph_storage="Neo4JStorage"
    )
    
    # Get the Neo4j storage instance
    kg_storage = rag.chunk_entity_relation_graph
    
    if not isinstance(kg_storage, Neo4JStorage):
        print("ERROR: Not using Neo4JStorage - check .env GRAPH_STORAGE setting")
        return
    
    # Query via Neo4j storage
    workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025_pwstst_4mod")
    
    print(f"\nQuerying workspace: {workspace}")
    print("=" * 100)
    
    # Get all nodes (entities)
    query = f"""
    MATCH (n:`{workspace}`)
    RETURN n.entity_name AS name, n.source_id AS sid, n.entity_type AS type
    LIMIT 20
    """
    
    # Use storage's driver directly
    with kg_storage._driver.session(database=kg_storage._database) as session:
        result = session.run(query)
        
        print("\nFirst 20 entities:")
        print(f"{'#':>3} | {'Entity Name':50} | {'Type':20} | {'Source ID':30}")
        print("-" * 110)
        
        for i, record in enumerate(result, 1):
            name = (record.get('name', 'N/A') or 'N/A')[:48]
            etype = (record.get('type', 'N/A') or 'N/A')[:18]
            sid = (record.get('sid', 'UNKNOWN') or 'UNKNOWN')[:28]
            print(f"{i:3} | {name:50} | {etype:20} | {sid:30}")
    
    # Count by source_id pattern
    count_query = f"""
    MATCH (n:`{workspace}`)
    RETURN
        count(CASE WHEN n.source_id STARTS WITH 'chunk-' THEN 1 END) AS chunk_based,
        count(CASE WHEN n.source_id = 'UNKNOWN' OR n.source_id IS NULL THEN 1 END) AS unknown,
        count(n) AS total
    """
    
    with kg_storage._driver.session(database=kg_storage._database) as session:
        result = session.run(count_query)
        record = result.single()
        
        chunk_based = record['chunk_based']
        unknown = record['unknown']
        total = record['total']
        other = total - chunk_based - unknown
        
        print(f"\n{'=' * 100}")
        print(f"Source ID Analysis:")
        print(f"  Chunk-based (chunk-...): {chunk_based:4} ({chunk_based/total*100:.1f}%)")
        print(f"  UNKNOWN/missing:         {unknown:4} ({unknown/total*100:.1f}%)")
        print(f"  Other formats:           {other:4} ({other/total*100:.1f}%)")
        print(f"  Total entities:          {total:4}")
        
        if chunk_based == total:
            print(f"\n✅ SUCCESS: 100% of entities have chunk-based source_id!")
        elif chunk_based > 0:
            print(f"\n⚠️  PARTIAL: {chunk_based/total*100:.1f}% have chunk-based source_id")
        else:
            print(f"\n❌ FAILURE: No entities have chunk-based source_id")

if __name__ == "__main__":
    asyncio.run(main())

