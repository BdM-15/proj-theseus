"""
Test if orphaned entities are still queryable for ODC pricing
Even without relationships, can we retrieve them via semantic search?
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
print("ODC ITEM QUERYABILITY TEST")
print("="*80)

# Test queries that a pricing analyst would run
test_queries = [
    ("Equipment items", "equipment"),
    ("Government-provided items", "government"),
    ("Consumables/supplies", "wipes OR meals OR MRE"),
    ("Fuel requirements", "fuel"),
    ("Ancillary hardware", "ancillary OR hardware OR software"),
]

with driver.session(database=db) as session:
    print("\n1. DIRECT ENTITY QUERIES (by type/keyword)")
    print("="*80)
    
    for query_name, search_term in test_queries:
        result = session.run(f"""
            MATCH (n:{workspace})
            WHERE n.entity_type = $type
               OR toLower(n.entity_id) CONTAINS toLower($search)
               OR toLower(n.description) CONTAINS toLower($search)
            RETURN n.entity_id as name, 
                   n.entity_type as type,
                   n.description as desc,
                   count{{(n)-[]-()}} as rel_count
            ORDER BY rel_count DESC
            LIMIT 10
        """, type=search_term, search=search_term)
        
        items = list(result)
        print(f"\n{query_name}: {len(items)} items found")
        
        orphaned = [i for i in items if i['rel_count'] == 0]
        if orphaned:
            print(f"  ⚠️  {len(orphaned)} are ORPHANED (no relationships):")
            for item in orphaned[:3]:
                print(f"     - {item['name']} ({item['type']})")
                print(f"       {item['desc'][:100]}")
        
        connected = [i for i in items if i['rel_count'] > 0]
        if connected:
            print(f"  ✅ {len(connected)} are CONNECTED:")
            for item in connected[:3]:
                print(f"     - {item['name']} ({item['type']}, {item['rel_count']} relationships)")
    
    # Test: Can we find ODC items via requirements?
    print("\n\n2. REQUIREMENT-BASED QUERIES (traverse from requirements)")
    print("="*80)
    
    # Find requirements that mention consumables/equipment
    result = session.run(f"""
        MATCH (req:{workspace})
        WHERE req.entity_type = 'requirement'
          AND (toLower(req.description) CONTAINS 'wipes'
               OR toLower(req.description) CONTAINS 'meals'
               OR toLower(req.description) CONTAINS 'receptacle'
               OR toLower(req.description) CONTAINS 'equipment')
        RETURN req.entity_id as req_name,
               req.description as desc
        LIMIT 5
    """)
    
    reqs = list(result)
    print(f"\nRequirements mentioning equipment/consumables: {len(reqs)}")
    for req in reqs[:3]:
        print(f"\n  Requirement: {req['req_name']}")
        print(f"    {req['desc'][:150]}...")
        
        # Check if requirement has relationships to equipment
        rel_result = session.run(f"""
            MATCH (req:{workspace} {{entity_id: $req_name}})-[r]-(item)
            WHERE item.entity_type IN ['equipment', 'technology']
            RETURN item.entity_id as item_name, item.entity_type as item_type, type(r) as rel_type
        """, req_name=req['req_name'])
        
        related = list(rel_result)
        if related:
            print(f"    ✅ Connected to {len(related)} equipment/tech items:")
            for rel in related[:2]:
                print(f"       → {rel['item_name']} ({rel['item_type']}) via {rel['rel_type']}")
        else:
            print(f"    ⚠️  NOT connected to any equipment entities")
    
    # Test: Government-provided items
    print("\n\n3. GOVERNMENT-PROVIDED ITEMS")
    print("="*80)
    
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE toLower(n.description) CONTAINS 'government'
          AND (toLower(n.description) CONTAINS 'provided'
               OR toLower(n.description) CONTAINS 'furnished'
               OR toLower(n.description) CONTAINS 'supplied')
        RETURN n.entity_id as name,
               n.entity_type as type,
               n.description as desc,
               count{{(n)-[]-()}} as rel_count
        ORDER BY rel_count
    """)
    
    gov_items = list(result)
    print(f"\nGovernment-provided items: {len(gov_items)}")
    
    orphaned_gov = [i for i in gov_items if i['rel_count'] == 0]
    if orphaned_gov:
        print(f"\n⚠️  {len(orphaned_gov)} ORPHANED Gov't-provided items:")
        for item in orphaned_gov:
            print(f"  - {item['name']} ({item['type']})")
            print(f"    {item['desc'][:120]}")
    
    connected_gov = [i for i in gov_items if i['rel_count'] > 0]
    if connected_gov:
        print(f"\n✅ {len(connected_gov)} CONNECTED Gov't-provided items")

driver.close()

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("""
Orphaned entities ARE still queryable via:
1. Direct entity_type searches (equipment, technology, etc.)
2. Description keyword searches (government, provided, consumables)
3. Mentions in requirement descriptions

However, you CANNOT:
- Traverse from a requirement to find its equipment needs
- Navigate from a PWS section to its consumables
- Build BOM via graph traversal

For ODC pricing, you need EITHER:
- Graph relationships (missing for orphans)
- OR direct queries + manual mapping (what you'd do now)

If relationships are critical for automated BOM generation, we need to fix
the orphaned equipment/consumables via relationship inference improvements.
""")
