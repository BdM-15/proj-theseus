"""Check what entities were extracted from the ADAB workload table chunk."""
import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(uri, auth=(user, password))

# The chunk containing ADAB aircraft operations table
chunk_id = 'chunk-47b716c14e6a8ac8bc737dda903f8369'

print(f'ENTITIES EXTRACTED FROM THE ADAB AIRCRAFT TABLE CHUNK')
print(f'Chunk ID: {chunk_id}')
print('='*80)

with driver.session(database='neo4j') as session:
    # Find entities from this specific chunk
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE n.source_id CONTAINS $chunk_id
        RETURN n.entity_id as name, n.entity_type as type, n.description as desc
    ''', chunk_id=chunk_id)
    
    count = 0
    for rec in result:
        count += 1
        print(f'{count}. [{rec["type"]}] {rec["name"]}')
        desc = rec['desc'][:250] if rec['desc'] else '(none)'
        print(f'   Description: {desc}')
        print()
    
    if count == 0:
        print('(no entities found from this specific chunk)')
        print()
        print('Let me search for any ADAB-related entities...')
        result = session.run('''
            MATCH (n:swa_tas)
            WHERE toLower(n.entity_id) CONTAINS 'dhafra' 
               OR toLower(n.entity_id) CONTAINS 'adab'
               OR toLower(n.description) CONTAINS 'al dhafra'
            RETURN n.entity_id as name, n.entity_type as type, 
                   n.description as desc, n.source_id as source
        ''')
        for rec in result:
            print(f'  [{rec["type"]}] {rec["name"]}')
            source = rec['source'][:80] if rec['source'] else '(none)'
            print(f'    Source: {source}')
            print()

    # Check: Is "Appendix H" mentioned in any entity description?
    print('='*80)
    print('ENTITIES THAT MENTION "Appendix H" IN DESCRIPTION:')
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE toLower(n.description) CONTAINS 'appendix h'
        RETURN n.entity_id as name, n.entity_type as type, n.description as desc
        LIMIT 10
    ''')
    for rec in result:
        print(f'  [{rec["type"]}] {rec["name"]}')
        desc = rec['desc'][:200] if rec['desc'] else '(none)'
        print(f'    Desc: {desc}')
        print()

    # Check relationships FROM the ADAB location entity
    print('='*80)
    print('RELATIONSHIPS FROM "Al Dhafra Air Base ADAB" ENTITY:')
    result = session.run('''
        MATCH (n:swa_tas)-[r]->(m:swa_tas)
        WHERE n.entity_id = 'Al Dhafra Air Base ADAB'
        RETURN type(r) as rel, m.entity_id as target, m.entity_type as ttype, 
               r.description as rdesc, r.keywords as kw
        LIMIT 15
    ''')
    for rec in result:
        kw = rec['kw'][:50] if rec['kw'] else ''
        print(f'  --[{rec["rel"]} ({kw})]-->')
        print(f'    [{rec["ttype"]}] {rec["target"]}')
        print()

    # Check relationships for the actual workload table entity
    print('='*80)
    print('RELATIONSHIPS FOR "Al Dhafra Aircraft Operations Table":')
    result = session.run('''
        MATCH (n:swa_tas)-[r]-(m:swa_tas)
        WHERE n.entity_id = 'Al Dhafra Aircraft Operations Table'
        RETURN n.entity_id as src, type(r) as rel, m.entity_id as tgt, m.entity_type as ttype
    ''')
    count = 0
    for rec in result:
        count += 1
        print(f'  {rec["src"]} --[{rec["rel"]}]--> {rec["tgt"]} ({rec["ttype"]})')
    if count == 0:
        print('  (NO RELATIONSHIPS FOUND - THIS IS THE PROBLEM!)')
    
    print()
    print('RELATIONSHIPS FOR "Estimated Monthly Workload Data ADAB":')
    result = session.run('''
        MATCH (n:swa_tas)-[r]-(m:swa_tas)
        WHERE n.entity_id = 'Estimated Monthly Workload Data ADAB'
        RETURN n.entity_id as src, type(r) as rel, m.entity_id as tgt, m.entity_type as ttype
    ''')
    count = 0
    for rec in result:
        count += 1
        print(f'  {rec["src"]} --[{rec["rel"]}]--> {rec["tgt"]} ({rec["ttype"]})')
    if count == 0:
        print('  (NO RELATIONSHIPS FOUND - THIS IS THE PROBLEM!)')

driver.close()
print('Done.')
