"""Check when orphaned entities were created vs connected entities"""

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

with driver.session(database=db) as session:
    # Get creation timestamps of orphaned entities
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE NOT (n)-[]-()
        RETURN n.entity_id, n.created_at
        ORDER BY n.created_at
    """)
    
    orphan_times = [(r['n.entity_id'], r['n.created_at']) for r in result]
    
    if orphan_times:
        print(f"\nOrphaned entities by creation time:")
        print(f"  First: {orphan_times[0][0]} at {orphan_times[0][1]}")
        print(f"  Last:  {orphan_times[-1][0]} at {orphan_times[-1][1]}")
        print(f"  Total: {len(orphan_times)}")
        
        # Check if orphans were created in a specific time window
        orphan_timestamp_set = set(r[1] for r in orphan_times if r[1])
        print(f"\n  Unique creation timestamps: {len(orphan_timestamp_set)}")
        if len(orphan_timestamp_set) <= 5:
            for ts in sorted(orphan_timestamp_set):
                count = sum(1 for r in orphan_times if r[1] == ts)
                print(f"    {ts}: {count} entities")
    
    # Compare with connected entities
    result = session.run(f"""
        MATCH (n:{workspace})-[]-()
        WITH DISTINCT n
        RETURN min(n.created_at) as first, max(n.created_at) as last, count(n) as total
    """)
    
    record = result.single()
    print(f"\nConnected entities:")
    print(f"  First created: {record['first']}")
    print(f"  Last created:  {record['last']}")
    print(f"  Total: {record['total']}")

driver.close()
