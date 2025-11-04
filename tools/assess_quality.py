"""Quick quality assessment of Neo4j data"""
from dotenv import load_dotenv
load_dotenv()

from src.inference.neo4j_graph_io import Neo4jGraphIO

io = Neo4jGraphIO()

print("\n" + "="*60)
print("📊 NEO4J DATA QUALITY ASSESSMENT")
print("="*60)

# 1. Total counts
with io.driver.session(database=io.database) as session:
    # Node count
    result = session.run(f"MATCH (n:`{io.workspace}`) RETURN count(n) as count")
    node_count = result.single()['count']
    
    # Relationship count
    result = session.run(f"MATCH (:`{io.workspace}`)-[r]->(:`{io.workspace}`) RETURN count(r) as count")
    rel_count = result.single()['count']
    
    print(f"\n✅ Total Nodes: {node_count:,}")
    print(f"✅ Total Relationships: {rel_count:,}")
    
    # 2. Entity type distribution
    print(f"\n📋 Entity Type Distribution:")
    type_counts = io.get_entity_count_by_type()
    for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {entity_type:30s}: {count:4d}")
    
    # 3. Check for corrected entities
    result = session.run(f"""
        MATCH (n:`{io.workspace}`)
        WHERE n.corrected_by IS NOT NULL
        RETURN count(n) as count
    """)
    corrected_count = result.single()['count']
    print(f"\n✅ Entities Corrected (with provenance): {corrected_count}")
    
    # 4. Check for inferred relationships
    result = session.run(f"""
        MATCH (:`{io.workspace}`)-[r:INFERRED_RELATIONSHIP]->(:`{io.workspace}`)
        RETURN count(r) as count
    """)
    inferred_rel_count = result.single()['count']
    print(f"✅ Inferred Relationships: {inferred_rel_count}")
    
    # 5. Sample inferred relationships
    if inferred_rel_count > 0:
        print(f"\n🔗 Sample Inferred Relationships:")
        result = session.run(f"""
            MATCH (a:`{io.workspace}`)-[r:INFERRED_RELATIONSHIP]->(b:`{io.workspace}`)
            RETURN a.entity_id as source, 
                   r.type as rel_type, 
                   b.entity_id as target,
                   r.confidence as confidence,
                   r.reasoning as reasoning
            LIMIT 5
        """)
        for i, record in enumerate(result, 1):
            print(f"\n   {i}. {record['source'][:40]} --[{record['rel_type']}]--> {record['target'][:40]}")
            print(f"      Confidence: {record['confidence']:.2f}")
            print(f"      Reasoning: {record['reasoning'][:80]}...")
    
    # 6. Check relationship type distribution
    print(f"\n📊 Relationship Type Distribution:")
    rel_types = io.get_relationship_count_by_type()
    for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {rel_type:30s}: {count:4d}")
    
    # 7. Sample entities by type
    print(f"\n📝 Sample Entities (one per major type):")
    for entity_type in ['requirement', 'deliverable', 'section', 'clause', 'organization']:
        result = session.run(f"""
            MATCH (n:`{io.workspace}`)
            WHERE n.entity_type = $type
            RETURN n.entity_id as name, n.description as desc
            LIMIT 1
        """, type=entity_type)
        record = result.single()
        if record:
            name = record['name'][:50]
            desc = record['desc'][:60] if record['desc'] else 'No description'
            print(f"   {entity_type:15s}: {name}")
            print(f"                    → {desc}...")

print("\n" + "="*60)
print("✅ QUALITY ASSESSMENT COMPLETE")
print("="*60 + "\n")

io.close()
