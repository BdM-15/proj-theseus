"""
Compare Raw Extraction vs Final Entity Counts
==============================================

Check if entity loss happened during extraction or post-processing.
"""

import json
import os

rag_storage_path = "rag_storage/afcapv_adab_iss_2025"

print("\n" + "="*80)
print("🔍 ENTITY COUNT INVESTIGATION")
print("="*80)

# Check vector DB entity count (raw extraction before Neo4j)
vdb_entities_file = os.path.join(rag_storage_path, "vdb_entities.json")

if os.path.exists(vdb_entities_file):
    with open(vdb_entities_file, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    # Count unique entities
    entity_names = set()
    for entry in vdb_data:
        if 'content' in entry:
            # Content format: "entity_name<SEP>entity_type<SEP>description"
            parts = entry['content'].split('<SEP>')
            if len(parts) >= 1:
                entity_names.add(parts[0].strip())
    
    print(f"\n📊 RAW EXTRACTION (vdb_entities.json):")
    print(f"  Total vector entries: {len(vdb_data)}")
    print(f"  Unique entity names: {len(entity_names)}")
else:
    print(f"\n❌ File not found: {vdb_entities_file}")

# Check relationships
vdb_rels_file = os.path.join(rag_storage_path, "vdb_relationships.json")

if os.path.exists(vdb_rels_file):
    with open(vdb_rels_file, 'r', encoding='utf-8') as f:
        vdb_rels = json.load(f)
    
    print(f"\n📊 RAW RELATIONSHIPS (vdb_relationships.json):")
    print(f"  Total relationship entries: {len(vdb_rels)}")
else:
    print(f"\n❌ File not found: {vdb_rels_file}")

# Now compare with Neo4j final count
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

try:
    with driver.session(database=neo4j_database) as session:
        # Total entities
        query_total = f"""
        MATCH (n:`{workspace}`)
        RETURN count(n) AS total
        """
        result = session.run(query_total)
        neo4j_total = result.single()["total"]
        
        # Requirements only
        query_reqs = f"""
        MATCH (n:`{workspace}`)
        WHERE n.entity_type = 'requirement'
        RETURN count(n) AS total
        """
        result = session.run(query_reqs)
        neo4j_reqs = result.single()["total"]
        
        # Total relationships
        query_rels = f"""
        MATCH (:`{workspace}`)-[r]->(:`{workspace}`)
        RETURN count(r) AS total
        """
        result = session.run(query_rels)
        neo4j_rels = result.single()["total"]
        
        print(f"\n📊 FINAL NEO4J (after post-processing):")
        print(f"  Total entities: {neo4j_total}")
        print(f"  Requirements: {neo4j_reqs}")
        print(f"  Relationships: {neo4j_rels}")
        
finally:
    driver.close()

# Analysis
print("\n" + "="*80)
print("📊 ANALYSIS")
print("="*80)

if os.path.exists(vdb_entities_file):
    raw_count = len(entity_names)
    final_count = neo4j_total
    loss = raw_count - final_count
    loss_pct = (loss / raw_count * 100) if raw_count > 0 else 0
    
    print(f"\n🔍 Entity Loss Analysis:")
    print(f"  Raw extraction: {raw_count} unique entities")
    print(f"  Final Neo4j: {final_count} entities")
    print(f"  Loss: {loss} entities ({loss_pct:.1f}%)")
    
    if loss > 0:
        print(f"\n⚠️  Entities were lost during processing!")
        print(f"  Possible causes:")
        print(f"    1. Neo4j deduplication (good if duplicates)")
        print(f"    2. Entity type correction removed UNKNOWN entities (check logs)")
        print(f"    3. Extraction variability (Grok-4 reasoning inconsistency)")
        print(f"    4. Workload enrichment bug (unlikely - enriches, doesn't delete)")
    else:
        print(f"\n✅ No entity loss - counts match!")

print("\n" + "="*80)
