"""Check table entities and their context awareness in Neo4j."""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'govcon-capture-2025'))

with driver.session() as session:
    print("=" * 80)
    print("TABLE ENTITIES - Checking for Context Awareness")
    print("=" * 80)
    
    # Get table entities
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE n.entity_type = 'table'
        RETURN n.entity_id as id, n.description as desc
        ORDER BY n.entity_id
        LIMIT 15
    ''')
    
    for record in result:
        print(f"\nID: {record['id']}")
        desc = record['desc'] or "No description"
        print(f"Description (first 500 chars):\n{desc[:500]}")
        # Check for context markers
        has_context = any(marker in desc.lower() for marker in ['appendix', 'section', 'attachment', 'pws', 'workload data'])
        print(f"Has Section Context: {'✅ YES' if has_context else '❌ NO'}")
        print("-" * 60)

    print("\n" + "=" * 80)
    print("ISOLATED NODES (no relationships)")
    print("=" * 80)
    
    # Find isolated nodes
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE NOT (n)-[:DIRECTED]-() AND NOT (n)-[:INFERRED_RELATIONSHIP]-()
        RETURN n.entity_id as id, n.entity_type as type, substring(n.description, 0, 100) as desc
        LIMIT 20
    ''')
    
    orphans = list(result)
    print(f"\nFound {len(orphans)} isolated nodes (showing first 20):")
    for record in orphans:
        print(f"  - [{record['type']}] {record['id']}: {record['desc']}")

    print("\n" + "=" * 80)
    print("TABLE RELATIONSHIPS")
    print("=" * 80)
    
    # Check table relationships
    result = session.run('''
        MATCH (t:swa_tas)-[r]-(other:swa_tas)
        WHERE t.entity_type = 'table'
        RETURN t.entity_id as table_id, type(r) as rel_type, other.entity_id as connected_to, other.entity_type as other_type
        LIMIT 30
    ''')
    
    rels = list(result)
    print(f"\nTable relationships: {len(rels)}")
    for record in rels:
        print(f"  {record['table_id']} --[{record['rel_type']}]--> {record['connected_to']} ({record['other_type']})")

driver.close()
