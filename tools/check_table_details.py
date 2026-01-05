"""Check specific table entity details."""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'govcon-capture-2025'))

with driver.session() as s:
    # Look at table entities
    for table_id in ['table_p5', 'table_p53', 'table_p54', 'table_p55']:
        r = s.run(f'MATCH (n:swa_tas) WHERE n.entity_id = "{table_id}" RETURN n.entity_id, n.entity_type, n.description')
        records = list(r)
        if records:
            rec = records[0]
            print(f"\n{'='*60}")
            print(f"ID: {rec[0]}")
            print(f"Type: {rec[1]}")
            print(f"Description:\n{rec[2][:800] if rec[2] else 'None'}...")
        else:
            print(f"\n{table_id}: NOT FOUND")
    
    # Check what's on page 53
    print(f"\n{'='*60}")
    print("Entities mentioning page 53 or AL JABER:")
    r2 = s.run('MATCH (n:swa_tas) WHERE toLower(n.description) CONTAINS "al jaber" OR toLower(n.entity_id) CONTAINS "p53" RETURN n.entity_id, n.entity_type, substring(n.description, 0, 200) LIMIT 10')
    for rec in r2:
        print(f"\n[{rec[1]}] {rec[0]}")
        print(f"  {rec[2]}")

driver.close()
