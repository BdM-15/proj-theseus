"""Check for CDRL duplicate entities."""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'govcon-capture-2025'))

with driver.session() as s:
    print("=" * 80)
    print("CDRL ENTITIES - Checking for Duplicates")
    print("=" * 80)
    
    r = s.run('''
        MATCH (n:swa_tas) 
        WHERE n.entity_id STARTS WITH "CDRL"
        RETURN n.entity_id as id, n.entity_type as type, substring(n.description, 0, 150) as desc
        ORDER BY n.entity_id
    ''')
    
    for rec in r:
        print(f"\n[{rec['type']}] {rec['id']}")
        print(f"  {rec['desc']}...")
    
    print("\n" + "=" * 80)
    print("POTENTIAL DUPLICATE PATTERNS")
    print("=" * 80)
    
    # Find entities that might be duplicates (one is prefix of another)
    r2 = s.run('''
        MATCH (a:swa_tas), (b:swa_tas)
        WHERE a.entity_id <> b.entity_id 
          AND (b.entity_id STARTS WITH a.entity_id + " " OR a.entity_id STARTS WITH b.entity_id + " ")
        RETURN DISTINCT a.entity_id as short, b.entity_id as long
        ORDER BY a.entity_id
    ''')
    
    pairs = list(r2)
    print(f"\nFound {len(pairs)} potential duplicate pairs:")
    for rec in pairs:
        print(f"  SHORT: {rec['short']}")
        print(f"  LONG:  {rec['long']}")
        print()

driver.close()
