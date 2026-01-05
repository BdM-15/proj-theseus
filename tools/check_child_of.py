"""Check CHILD_OF relationship structure in Neo4j"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME')
pwd = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(uri, auth=(user, pwd))

with driver.session() as session:
    print("=" * 60)
    print("RELATIONSHIP TYPES IN NEO4J")
    print("=" * 60)
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
    """)
    for r in result:
        print(f"  {r['type']:30} {r['count']:>6}")
    
    print()
    print("=" * 60)
    print("INFERRED_RELATIONSHIP PROPERTIES (sample)")
    print("=" * 60)
    result = session.run("""
        MATCH ()-[r:INFERRED_RELATIONSHIP]->()
        RETURN keys(r) as props
        LIMIT 1
    """)
    rec = result.single()
    if rec:
        print(f"  Properties: {rec['props']}")
    
    print()
    print("=" * 60)
    print("INFERRED_RELATIONSHIP by 'type' property (actual key)")
    print("=" * 60)
    result = session.run("""
        MATCH ()-[r:INFERRED_RELATIONSHIP]->()
        RETURN r.type as rel_type, count(r) as count
        ORDER BY count DESC
        LIMIT 15
    """)
    for r in result:
        print(f"  {str(r['rel_type']):30} {r['count']:>6}")
    
    print()
    print("=" * 60)
    print("SAMPLE INFERRED RELATIONSHIPS (first 5)")
    print("=" * 60)
    result = session.run("""
        MATCH (s)-[r:INFERRED_RELATIONSHIP]->(t)
        RETURN s.entity_id as src, r.type as rel, t.entity_id as tgt, r.source as algo
        LIMIT 5
    """)
    for r in result:
        print(f"  {r['src'][:25]:27} --[{r['rel']}]--> {r['tgt'][:25]} (source: {r['algo']})")

    print()
    print("=" * 60)
    print("CHILD_OF SPECIFIC CHECK")
    print("=" * 60)
    # Check if CHILD_OF is stored as relationship type or property
    result = session.run("""
        MATCH ()-[r:CHILD_OF]->()
        RETURN count(r) as count
    """)
    count1 = result.single()['count']
    print(f"  CHILD_OF as relationship TYPE: {count1}")
    
    result = session.run("""
        MATCH ()-[r:INFERRED_RELATIONSHIP]->()
        WHERE r.type = 'CHILD_OF'
        RETURN count(r) as count
    """)
    count2 = result.single()['count']
    print(f"  CHILD_OF as 'type' property:   {count2}")
    
    result = session.run("""
        MATCH ()-[r]->()
        WHERE r.description CONTAINS 'CHILD_OF' OR r.keywords CONTAINS 'CHILD_OF'
        RETURN count(r) as count
    """)
    count3 = result.single()['count']
    print(f"  CHILD_OF in description/kw:    {count3}")
    
    # Check what DIRECTED relationships look like
    print()
    print("=" * 60)
    print("DIRECTED RELATIONSHIP TYPES (by 'keywords' property)")
    print("=" * 60)
    result = session.run("""
        MATCH ()-[r:DIRECTED]->()
        WHERE r.keywords IS NOT NULL
        RETURN r.keywords as kw, count(r) as count
        ORDER BY count DESC
        LIMIT 15
    """)
    for r in result:
        print(f"  {str(r['kw'])[:45]:47} {r['count']:>6}")

driver.close()
