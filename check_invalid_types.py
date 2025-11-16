"""Check for specific invalid entity types from Neo4j Browser image."""

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

print('='*80)
print('CHECKING FOR INVALID TYPES FROM NEO4J BROWSER IMAGE')
print('='*80)
print('\nImage shows: other (20), table (55), UNKNOWN (13)')
print()

with driver.session(database=db) as session:
    # Check for each invalid type
    for check_type in ['other', 'table', 'UNKNOWN']:
        result = session.run(f'''
            MATCH (n:{workspace})
            WHERE n.entity_type = $type
            RETURN count(n) as count, collect(n.entity_id)[..5] as examples
        ''', type=check_type)
        
        rec = result.single()
        if rec['count'] > 0:
            print(f'\n{check_type}: {rec["count"]} entities')
            print('  Examples:')
            for ex in rec['examples']:
                print(f'    • {ex}')
        else:
            print(f'\n{check_type}: NOT FOUND in entity_type property')
    
    # Maybe these are Neo4j LABELS instead of entity_type values?
    print('\n' + '='*80)
    print('CHECKING IF THESE ARE NEO4J LABELS (not entity_type)')
    print('='*80)
    
    # Get all labels in the database
    result = session.run('''
        CALL db.labels() YIELD label
        RETURN label
        ORDER BY label
    ''')
    
    all_labels = [r['label'] for r in result]
    print(f'\nAll labels in database: {all_labels}')
    
    # Check if 'other', 'table', 'UNKNOWN' are labels
    suspicious_labels = [l for l in all_labels if l.lower() in ['other', 'table', 'unknown']]
    if suspicious_labels:
        print(f'\n⚠️  FOUND SUSPICIOUS LABELS: {suspicious_labels}')
        
        for label in suspicious_labels:
            result = session.run(f'''
                MATCH (n:{label})
                RETURN count(n) as count, collect(n.entity_type)[..5] as entity_types
            ''')
            rec = result.single()
            print(f'\n  Label "{label}": {rec["count"]} nodes')
            print(f'    Entity types: {set(rec["entity_types"])}')

driver.close()
