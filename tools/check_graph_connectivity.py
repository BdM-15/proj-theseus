"""Check graph connectivity for H.2.0 workload entities - diagnose retrieval gap."""
import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
user = os.getenv('NEO4J_USERNAME', 'neo4j')
pwd = os.getenv('NEO4J_PASSWORD', 'govcon-capture-2025')

driver = GraphDatabase.driver(uri, auth=(user, pwd))

with driver.session() as session:
    # ADAB entities
    print('=== ADAB/DHAFRA ENTITIES ===')
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE toLower(n.entity_id) CONTAINS 'adab' 
           OR toLower(n.entity_id) CONTAINS 'dhafra'
        RETURN n.entity_id
    ''')
    adab_entities = [r[0] for r in result]
    print(f'Found {len(adab_entities)} entities')
    for e in adab_entities[:10]:
        print(f'  - {e}')
    print()
    
    # 1-hop from key ADAB entity
    print('=== 1-HOP FROM AL DHAFRA AIR BASE ===')
    result = session.run('''
        MATCH (adab:swa_tas)-[r]->(target:swa_tas)
        WHERE toLower(adab.entity_id) = 'al dhafra air base'
        RETURN target.entity_id as tgt
        LIMIT 25
    ''')
    targets = [r[0] for r in result]
    print(f'Found {len(targets)} targets:')
    for t in targets[:15]:
        print(f'  --> {t}')
    print()
    
    # Path from ADAB to table_p53
    print('=== PATH FROM ADAB TO table_p53 (1-3 hops) ===')
    result = session.run('''
        MATCH path = (adab:swa_tas)-[*1..3]->(tgt:swa_tas)
        WHERE (toLower(adab.entity_id) CONTAINS 'dhafra' OR toLower(adab.entity_id) CONTAINS 'adab')
        AND tgt.entity_id = 'table_p53'
        RETURN [n in nodes(path) | n.entity_id] as path_nodes
        LIMIT 5
    ''')
    count = 0
    for r in result:
        print(f'  Path: {r[0]}')
        count += 1
    print(f'Found: {count} paths')
    print()
    
    # Appendix H connections
    print('=== APPENDIX H CONNECTIONS ===')
    result = session.run('''
        MATCH (app:swa_tas)-[r]->(tgt:swa_tas)
        WHERE toLower(app.entity_id) CONTAINS 'appendix h'
        RETURN app.entity_id as src, tgt.entity_id as tgt
        LIMIT 20
    ''')
    count = 0
    for r in result:
        print(f'  {r[0][:40]:40} --> {r[1][:40]}')
        count += 1
    print(f'Found: {count}')
    print()
    
    # Check what entities mention ADAB in description (semantic)
    print('=== ENTITIES MENTIONING ADAB IN DESCRIPTION ===')
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE toLower(n.description) CONTAINS 'adab' OR toLower(n.description) CONTAINS 'dhafra'
        RETURN n.entity_id, size(n.description) as len
        ORDER BY len DESC
        LIMIT 20
    ''')
    for r in result:
        print(f'  {r[1]:5d} chars: {r[0]}')

driver.close()
