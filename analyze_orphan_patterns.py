"""
Analyze WHY orphaned entities weren't linked by Phase 6/7
==========================================================

Now that we know orphans were processed by Phase 6/7 (created at same time as connected entities),
the question is: WHY didn't Phase 6/7 create relationships for them?

Possible reasons:
1. LLM failed to identify valid relationships
2. Batch processing overlapped poorly
3. Entity descriptions too vague
4. These are truly standalone entities (admin/minor ones)
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("="*80)
print("ORPHAN RELATIONSHIP OPPORTUNITY ANALYSIS")
print("="*80)

with driver.session(database=db) as session:
    # Get orphaned entities with full context
    result = session.run(f"""
        MATCH (orphan:{workspace})
        WHERE NOT (orphan)-[]-()
        RETURN orphan.entity_id as name,
               orphan.entity_type as type,
               orphan.description as desc,
               orphan.source_id as chunk
        ORDER BY orphan.entity_type, orphan.entity_id
    """)
    
    orphans = [dict(r) for r in result]
    
    print(f"\n1. ORPHANED ENTITIES BY TYPE\n")
    
    # Group by type
    by_type = {}
    for o in orphans:
        t = o['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(o)
    
    for entity_type, entities in sorted(by_type.items()):
        print(f"\n{entity_type.upper()} ({len(entities)} orphaned):")
        for e in entities:
            print(f"  - {e['name']}")
            desc_preview = (e['desc'] or '')[:100]
            print(f"    Desc: {desc_preview}")
            print(f"    Chunk: {e['chunk']}")
            
            print()

print("\n" + "="*80)
print("2. POTENTIAL LINKING PATTERNS")
print("="*80)

# Check if orphans share chunks with well-connected entities
with driver.session(database=db) as session:
    for orphan in orphans[:10]:  # Sample first 10
        result = session.run(f"""
            MATCH (orphan:{workspace})
            WHERE orphan.entity_id = $name
            
            MATCH (neighbor:{workspace})
            WHERE neighbor.source_id = orphan.source_id
              AND neighbor <> orphan
              AND (neighbor)-[]-()
            
            RETURN neighbor.entity_id as neighbor_name,
                   neighbor.entity_type as neighbor_type,
                   count{{(neighbor)-[]-()}} as rel_count
            ORDER BY rel_count DESC
            LIMIT 5
        """, name=orphan['name'])
        
        neighbors = [dict(r) for r in result]
        if neighbors:
            print(f"\n{orphan['name']} ({orphan['type']})")
            print(f"  Same-chunk entities that ARE linked:")
            for n in neighbors:
                print(f"    → {n['neighbor_name']} ({n['neighbor_type']}) - {n['rel_count']} relationships")

driver.close()

print("\n" + "="*80)
print("HYPOTHESIS")
print("="*80)
print("""
If orphans share chunks with well-linked entities:
  → Phase 6 processed the chunk but LLM didn't infer relationships for these specific entities
  → Likely because:
    a) Descriptions too vague/generic
    b) Names ambiguous
    c) Truly administrative/minor entities
    d) Batch window excluded potential targets

If orphans are isolated in their chunks:
  → Chunks contain only peripheral information
  → No semantic links to main RFP entities
""")
