"""Analyze orphaned nodes and entity type compliance."""

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

# Our 17 mandated government contracting entity types
VALID_TYPES = {
    "requirement", "evaluation_factor", "submission_instruction",
    "clause", "section", "document", "deliverable", "statement_of_work",
    "strategic_theme", "program", "equipment", "organization",
    "concept", "event", "technology", "person", "location"
}

print("="*80)
print("1. ORPHANED NODES ANALYSIS")
print("="*80)

with driver.session(database=db) as session:
    # Find orphaned nodes
    result = session.run(f'''
        MATCH (n:{workspace})
        WHERE NOT EXISTS {{
            MATCH (n)-[]-()
        }}
        RETURN n.entity_type as type, n.entity_id as name, 
               n.description as desc
        ORDER BY type, name
    ''')
    
    orphans = list(result)
    
    # Group by type
    by_type = {}
    for r in orphans:
        t = r['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append({'name': r['name'], 'desc': r['desc']})
    
    print(f"\nTotal orphaned nodes: {len(orphans)}")
    print(f"Types affected: {len(by_type)}\n")
    
    for entity_type, nodes in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{entity_type.upper()} ({len(nodes)} orphaned):")
        print("-" * 80)
        for node in nodes[:5]:  # Show first 5 of each type
            desc_short = (node['desc'][:70] + '...') if node['desc'] and len(node['desc']) > 70 else (node['desc'] or 'No description')
            print(f"  • {node['name']}")
            print(f"    {desc_short}")
        if len(nodes) > 5:
            print(f"    ... and {len(nodes) - 5} more")

print("\n" + "="*80)
print("2. ENTITY TYPE COMPLIANCE CHECK")
print("="*80)

with driver.session(database=db) as session:
    # Get all entity types
    result = session.run(f'''
        MATCH (n:{workspace})
        RETURN DISTINCT n.entity_type as type
        ORDER BY type
    ''')
    
    all_types = [r['type'] for r in result]
    
    invalid_types = [t for t in all_types if t not in VALID_TYPES]
    
    print(f"\nTotal unique entity types found: {len(all_types)}")
    print(f"Expected (mandated): {len(VALID_TYPES)}")
    
    if invalid_types:
        print(f"\n⚠️  INVALID ENTITY TYPES DETECTED ({len(invalid_types)}):")
        print("-" * 80)
        
        for invalid_type in invalid_types:
            # Get count and examples
            result = session.run(f'''
                MATCH (n:{workspace})
                WHERE n.entity_type = $type
                RETURN count(n) as count, collect(n.entity_id)[..3] as examples
            ''', type=invalid_type)
            
            rec = result.single()
            print(f"\n'{invalid_type}' ({rec['count']} entities):")
            for ex in rec['examples']:
                print(f"  • {ex}")
    else:
        print("\n✅ All entity types comply with 17 mandated types")

print("\n" + "="*80)
print("3. POTENTIAL RELATIONSHIP OPPORTUNITIES")
print("="*80)

with driver.session(database=db) as session:
    # Look for orphaned nodes that mention other entities in their description
    result = session.run(f'''
        MATCH (orphan:{workspace})
        WHERE NOT EXISTS {{
            MATCH (orphan)-[]-()
        }}
        AND orphan.description IS NOT NULL
        WITH orphan
        MATCH (other:{workspace})
        WHERE orphan <> other
        AND (
            orphan.description CONTAINS other.entity_id
            OR other.description CONTAINS orphan.entity_id
        )
        RETURN orphan.entity_type as orphan_type, 
               orphan.entity_id as orphan_name,
               other.entity_type as other_type,
               other.entity_id as other_name,
               orphan.description as orphan_desc
        LIMIT 20
    ''')
    
    opportunities = list(result)
    
    if opportunities:
        print(f"\nFound {len(opportunities)} potential relationship opportunities:")
        print("-" * 80)
        for opp in opportunities[:10]:
            print(f"\nOrphan: {opp['orphan_type']} '{opp['orphan_name']}'")
            print(f"  Could link to: {opp['other_type']} '{opp['other_name']}'")
            desc_short = (opp['orphan_desc'][:70] + '...') if len(opp['orphan_desc']) > 70 else opp['orphan_desc']
            print(f"  Context: {desc_short}")
    else:
        print("\nNo obvious relationship opportunities found in descriptions")

driver.close()
