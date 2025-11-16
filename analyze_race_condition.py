"""
Analyze Race Condition: Post-processing starting before extraction completes
=============================================================================

HYPOTHESIS: Post-processing (Phase 6/7) starts while LightRAG is still processing
chunks asynchronously, leading to:
1. Orphaned entities (created after Phase 6 completes)
2. Missing relationships (Phase 6 doesn't see late-arriving entities)
3. Entity type corrections missing some entities

INVESTIGATION POINTS:
1. Does insert_content_list() truly await ALL async processing?
2. Is Neo4j write queue still draining when Phase 6 starts?
3. Are there background workers still running?
"""

import asyncio
import json
from pathlib import Path

print("="*80)
print("RACE CONDITION ANALYSIS")
print("="*80)

# Check the LightRAG storage files for timing clues
storage_path = Path("rag_storage/afcapv_adab_iss_2025")

if storage_path.exists():
    # Check entity chunks - when were they created?
    entity_chunks_path = storage_path / "kv_store_entity_chunks.json"
    if entity_chunks_path.exists():
        with open(entity_chunks_path, 'r', encoding='utf-8') as f:
            entity_chunks = json.load(f)
        
        print(f"\n1. ENTITY CHUNKS STORAGE")
        print(f"   Total chunks: {len(entity_chunks)}")
        
        # Check if all chunks have entities
        chunks_with_entities = sum(1 for chunk in entity_chunks.values() if chunk)
        print(f"   Chunks with entities: {chunks_with_entities}/{len(entity_chunks)}")
        
    # Check full entities
    full_entities_path = storage_path / "kv_store_full_entities.json"
    if full_entities_path.exists():
        with open(full_entities_path, 'r', encoding='utf-8') as f:
            full_entities = json.load(f)
        
        print(f"\n2. FULL ENTITIES STORAGE (LightRAG)")
        print(f"   Total entities in LightRAG: {len(full_entities)}")
    
    # Check full relationships
    full_relations_path = storage_path / "kv_store_full_relations.json"
    if full_relations_path.exists():
        with open(full_relations_path, 'r', encoding='utf-8') as f:
            full_relations = json.load(f)
        
        print(f"\n3. FULL RELATIONSHIPS STORAGE (LightRAG)")
        print(f"   Total relationships in LightRAG: {len(full_relations)}")

# Now check Neo4j for comparison
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

with driver.session(database=db) as session:
    # Count entities
    result = session.run(f'MATCH (n:{workspace}) RETURN count(n) as count')
    neo4j_entities = result.single()['count']
    
    # Count relationships
    result = session.run(f'MATCH (:{workspace})-[r]->() RETURN count(r) as count')
    neo4j_rels = result.single()['count']
    
    print(f"\n4. NEO4J STORAGE (Post-Phase 6/7)")
    print(f"   Total entities in Neo4j: {neo4j_entities}")
    print(f"   Total relationships in Neo4j: {neo4j_rels}")

driver.close()

# Calculate discrepancy
if full_entities_path.exists():
    entity_diff = neo4j_entities - len(full_entities)
    print(f"\n5. DISCREPANCY ANALYSIS")
    print(f"   Entities in Neo4j but NOT in LightRAG storage: {entity_diff}")
    
    if entity_diff > 0:
        print(f"\n   ⚠️  RACE CONDITION DETECTED!")
        print(f"   → {entity_diff} entities were created AFTER LightRAG extraction")
        print(f"   → These are likely from Phase 6/7 semantic post-processing")
        print(f"   → But Phase 6/7 runs on LightRAG storage, so misses its own creations")
    
    if entity_diff < 0:
        print(f"\n   ⚠️  MISSING ENTITIES IN NEO4J!")
        print(f"   → {abs(entity_diff)} entities in LightRAG not persisted to Neo4j")
        print(f"   → Possible Neo4j write failure or timeout")

print("\n" + "="*80)
print("TIMING ANALYSIS")
print("="*80)

# Check processing.log for timing
log_path = Path("logs/processing.log")
if log_path.exists():
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find key timestamps
    insert_start = None
    insert_end = None
    phase6_start = None
    phase6_end = None
    
    for line in lines[-500:]:  # Check last 500 lines
        if "insert_content_list" in line.lower() or "inserting" in line.lower():
            if not insert_start:
                insert_start = line[:23]  # timestamp
        if "semantic knowledge graph enhancement" in line.lower():
            if not phase6_start:
                phase6_start = line[:23]
        if "semantic enhancement complete" in line.lower():
            if not phase6_end:
                phase6_end = line[:23]
    
    if insert_start and phase6_start:
        print(f"\n6. PROCESSING TIMELINE (from logs)")
        print(f"   Insert started:  {insert_start}")
        print(f"   Phase 6 started: {phase6_start}")
        if phase6_end:
            print(f"   Phase 6 ended:   {phase6_end}")
        
        print(f"\n   ⚠️  Check if Phase 6 started BEFORE all chunks were processed")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)
print("""
If entity_diff > 0 (entities in Neo4j but not LightRAG):
  → Add explicit completion wait after insert_content_list()
  → Ensure ALL async workers drain before Phase 6/7
  → Add Neo4j consistency check before post-processing

Potential fixes:
  1. Query Neo4j for entity count after insert, compare to expected
  2. Add configurable sleep/poll after insert_content_list()
  3. Check LightRAG's internal queue status before proceeding
  4. Add transaction barriers in Neo4j writes
""")
