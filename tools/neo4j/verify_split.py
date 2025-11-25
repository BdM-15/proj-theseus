import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

import json
from pathlib import Path

def debug_query():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Load chunk store
    workspace = "afcapv_adab_iss_2025_pwstst" # Hardcoded for this test
    chunk_store_path = Path(f"rag_storage/{workspace}/kv_store_text_chunks.json")
    chunk_store = {}
    if chunk_store_path.exists():
        print(f"Loading text chunks from {chunk_store_path}...")
        with open(chunk_store_path, 'r', encoding='utf-8') as f:
            chunk_store = json.load(f)
        print(f"Loaded {len(chunk_store)} text chunks")
    
    print("\n1. Finding Appendix F Requirements and resolving text:")
    query = """
    MATCH (n:afcapv_adab_iss_2025_pwstst)
    WHERE (n.description CONTAINS 'Recreation' OR n.description CONTAINS 'Fitness' OR n.entity_id CONTAINS 'Appendix F')
    AND n.entity_type = 'requirement'
    RETURN n.entity_id as name, n.description as description, n.source_id as source_ids
    LIMIT 5
    """
    
    with driver.session(database="neo4j") as session:
        result = session.run(query)
        for record in result:
            print(f"\nName: {record['name']}")
            print(f"Description (Graph): {record['description']}")
            source_ids = record['source_ids']
            
            if source_ids and chunk_store:
                first_chunk_id = source_ids.split('<SEP>')[0]
                if first_chunk_id in chunk_store:
                    content = chunk_store[first_chunk_id].get('content', '')
                    print(f"Raw Text (KV Store): {content[:300]}...")
                    if "0700" in content or "hours" in content:
                        print("✅ FOUND METRICS IN RAW TEXT!")
                else:
                    print(f"Chunk {first_chunk_id} not found in KV store.")
            else:
                print("No source_ids or chunk store not loaded.")
            print("-" * 40)

    driver.close()

if __name__ == "__main__":
    debug_query()
