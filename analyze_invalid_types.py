"""Find and analyze invalid entity types."""

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

VALID_TYPES = {
    'requirement', 'evaluation_factor', 'submission_instruction',
    'clause', 'section', 'document', 'deliverable', 'statement_of_work',
    'strategic_theme', 'program', 'equipment', 'organization',
    'concept', 'event', 'technology', 'person', 'location'
}

with driver.session(database=db) as session:
    # Get all entity types
    result = session.run(f'''
        MATCH (n:{workspace})
        WHERE n.entity_type IS NOT NULL
        RETURN DISTINCT n.entity_type as type, count(*) as count
        ORDER BY type
    ''')
    
    all_types = [(r['type'], r['count']) for r in result]
    invalid_types = [(t, c) for t, c in all_types if t not in VALID_TYPES]
    
    print('='*80)
    print('INVALID ENTITY TYPES DETECTED')
    print('='*80)
    print(f'Total types: {len(all_types)}')
    print(f'Invalid types: {len(invalid_types)}')
    print()
    
    for invalid_type, count in invalid_types:
        print(f'\n{"="*80}')
        print(f'{invalid_type.upper()} ({count} entities)')
        print('='*80)
        
        result = session.run(f'''
            MATCH (n:{workspace})
            WHERE n.entity_type = $type
            RETURN n.entity_id as name, n.description as desc, n.source_id as source
            ORDER BY n.entity_id
            LIMIT 15
        ''', type=invalid_type)
        
        for r in result:
            desc = (r['desc'][:100] + '...') if r['desc'] and len(r['desc']) > 100 else (r['desc'] or 'No description')
            print(f'\n  • {r["name"]}')
            print(f'    Desc: {desc}')
            if r['source']:
                print(f'    Source: {r["source"][:100]}')

driver.close()
