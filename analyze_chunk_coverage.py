"""
Analyze Chunk Coverage: Are all chunks being processed by Phase 6/7?
=====================================================================

The real question: If Phase 6/7 creates 1,405/1,410 entities (99.6%),
why are there 34 orphaned nodes?

HYPOTHESIS REVISION:
- LightRAG creates minimal chunk-level entities (5 found)
- Phase 6/7 extracts 1,405 entities from 368 chunks
- Some chunks may be processed AFTER Phase 6 completes
- OR Phase 6 misses some entity extractions from certain chunks
"""

import json
from pathlib import Path
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

storage_path = Path("rag_storage/afcapv_adab_iss_2025")

print("="*80)
print("CHUNK COVERAGE ANALYSIS")
print("="*80)

# Load entity chunks
entity_chunks_path = storage_path / "kv_store_entity_chunks.json"
with open(entity_chunks_path, 'r', encoding='utf-8') as f:
    entity_chunks = json.load(f)

print(f"\n1. CHUNK-LEVEL ENTITIES")
print(f"   Total chunks: {len(entity_chunks)}")

# Analyze chunk entity distribution
chunk_entity_counts = {}
for chunk_id, entities in entity_chunks.items():
    if isinstance(entities, list):
        count = len(entities)
    else:
        count = 1 if entities else 0
    chunk_entity_counts[chunk_id] = count

total_chunk_entities = sum(chunk_entity_counts.values())
chunks_with_entities = sum(1 for c in chunk_entity_counts.values() if c > 0)

print(f"   Chunks with entities: {chunks_with_entities}/{len(entity_chunks)}")
print(f"   Total chunk-level entity refs: {total_chunk_entities}")

# Now check if all chunks are represented in Neo4j
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

with driver.session(database=db) as session:
    # Get all chunk IDs referenced by entities in Neo4j
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE n.source_id IS NOT NULL
        RETURN DISTINCT n.source_id as chunk_id
    """)
    
    neo4j_chunks = {record['chunk_id'] for record in result if record['chunk_id']}
    
    print(f"\n2. CHUNK COVERAGE IN NEO4J")
    print(f"   Chunks referenced in Neo4j: {len(neo4j_chunks)}")
    
    # Find chunks NOT in Neo4j
    missing_chunks = set(entity_chunks.keys()) - neo4j_chunks
    print(f"   Chunks NOT in Neo4j: {len(missing_chunks)}")
    
    if missing_chunks and len(missing_chunks) < 10:
        print(f"\n   Missing chunks: {list(missing_chunks)[:10]}")
    
    # Get entity counts by chunk
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE n.source_id IS NOT NULL
        RETURN n.source_id as chunk_id, count(n) as entity_count
        ORDER BY entity_count DESC
        LIMIT 10
    """)
    
    print(f"\n3. TOP 10 CHUNKS BY ENTITY COUNT")
    for record in result:
        print(f"   {record['chunk_id']}: {record['entity_count']} entities")
    
    # Check orphaned nodes specifically
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE NOT (n)-[]-()
        RETURN n.entity_name as name, n.entity_type as type, n.source_id as chunk_id
        LIMIT 34
    """)
    
    print(f"\n4. ORPHANED NODES SOURCE ANALYSIS")
    orphan_chunks = {}
    for record in result:
        chunk_id = record['chunk_id'] or 'NO_CHUNK'
        if chunk_id not in orphan_chunks:
            orphan_chunks[chunk_id] = []
        orphan_chunks[chunk_id].append(f"{record['name']} ({record['type']})")
    
    print(f"   Orphaned entities by source chunk:")
    for chunk_id, entities in sorted(orphan_chunks.items()):
        print(f"\n   Chunk: {chunk_id}")
        for entity in entities[:5]:  # Limit to 5 per chunk
            print(f"     - {entity}")
        if len(entities) > 5:
            print(f"     ... and {len(entities) - 5} more")

driver.close()

print("\n" + "="*80)
print("HYPOTHESIS VALIDATION")
print("="*80)
print("""
If missing_chunks > 0:
  → Some chunks processed AFTER Phase 6 completed
  → Entities from these chunks are orphaned
  → Need to wait for chunk queue to drain before Phase 6

If missing_chunks = 0 but orphans exist:
  → Phase 6 IS processing all chunks
  → Orphans are from failed relationship inference
  → Issue is in semantic_post_processor.py logic, not timing
""")
