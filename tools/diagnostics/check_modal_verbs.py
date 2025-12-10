"""Check modal verb semantic validation in requirements."""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)
database = os.getenv('NEO4J_DATABASE', 'neo4j')

workspace = '37c_test_mcpp'

with driver.session(database=database) as session:
    # Get requirements with modal verbs
    query = f"""
    MATCH (r:`{workspace}`)
    WHERE r.entity_type = 'requirement' AND r.modal_verb IS NOT NULL
    RETURN r.modal_verb as modal, r.criticality as crit, r.name as name
    LIMIT 30
    """
    
    result = session.run(query)
    records = list(result)
    
    print(f"Found {len(records)} requirements with modal verbs:\n")
    print(f"{'Modal Verb':<25} | {'Criticality':<15} | Requirement Name")
    print("=" * 120)
    
    for r in records:
        modal = r['modal'] or 'None'
        crit = r['crit'] or 'None'
        name = r['name'][:70] if r['name'] else 'N/A'
        print(f"{modal:<25} | {crit:<15} | {name}")
    
    # Get criticality distribution
    query2 = f"""
    MATCH (r:`{workspace}`)
    WHERE r.entity_type = 'requirement'
    RETURN r.criticality as crit, count(*) as count
    ORDER BY count DESC
    """
    
    result2 = session.run(query2)
    records2 = list(result2)
    
    print("\n" + "=" * 60)
    print("CRITICALITY DISTRIBUTION:")
    print("=" * 60)
    for r in records2:
        crit = r['crit'] or 'None'
        count = r['count']
        print(f"{crit:<20} : {count:>5}")

driver.close()
