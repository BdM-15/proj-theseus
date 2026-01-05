"""Check entity distribution and find tables."""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'govcon-capture-2025'))

with driver.session() as s:
    # Count by entity type
    print("Entity Type Distribution:")
    r = s.run('MATCH (n:swa_tas) RETURN n.entity_type as type, count(*) as cnt ORDER BY cnt DESC')
    for rec in r:
        print(f"  {rec['type']}: {rec['cnt']}")
    
    # Check for table_p* pattern
    print("\nEntities with 'table' in ID:")
    r2 = s.run('MATCH (n:swa_tas) WHERE toLower(n.entity_id) CONTAINS "table" RETURN n.entity_id, n.entity_type LIMIT 15')
    for rec in r2:
        print(f"  {rec[0]} ({rec[1]})")
    
    # Check for workload tables specifically
    print("\nEntities with 'workload' in description:")
    r3 = s.run('MATCH (n:swa_tas) WHERE toLower(n.description) CONTAINS "workload" RETURN n.entity_id, n.entity_type, substring(n.description, 0, 150) LIMIT 10')
    for rec in r3:
        print(f"  [{rec[1]}] {rec[0]}")
        print(f"    {rec[2]}...")
    
    # Count isolated vs connected nodes
    print("\n--- Node Connectivity ---")
    r4 = s.run('''
        MATCH (n:swa_tas)
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as rel_count
        RETURN 
            CASE WHEN rel_count = 0 THEN 'isolated' ELSE 'connected' END as status,
            count(*) as cnt
    ''')
    for rec in r4:
        print(f"  {rec['status']}: {rec['cnt']}")

driver.close()
