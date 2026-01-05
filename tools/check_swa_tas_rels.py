#!/usr/bin/env python3
"""Check how relationships are stored in Neo4j for swa_tas."""

import os
from dotenv import load_dotenv
load_dotenv()
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'), 
    auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'neo4jpass'))
)

def q(query):
    with driver.session() as s:
        return [dict(r) for r in s.run(query)]

# Check relationship properties
print('Sample relationship properties:')
props = q('MATCH (a:swa_tas)-[r]->(b:swa_tas) RETURN keys(r) as keys LIMIT 1')
print(f"  Keys: {props[0]['keys'] if props else 'none'}")

# Check if CHILD_OF is in keywords property
print('\nChecking CHILD_OF in relationship keywords...')
child_of_rels = q('''
    MATCH (a:swa_tas)-[r]->(b:swa_tas) 
    WHERE r.keywords CONTAINS 'CHILD_OF'
    RETURN a.entity_name as src, b.entity_name as tgt, r.keywords as kw
    LIMIT 15
''')
print(f'Found {len(child_of_rels)} relationships with CHILD_OF in keywords')
for s in child_of_rels[:10]:
    src = str(s['src'])[:35] if s['src'] else 'N/A'
    tgt = str(s['tgt'])[:35] if s['tgt'] else 'N/A'
    print(f"  {src} --> {tgt}")

# Check INFERRED_RELATIONSHIP details
print('\nINFERRED_RELATIONSHIP samples:')
inferred = q('''
    MATCH (a:swa_tas)-[r:INFERRED_RELATIONSHIP]->(b:swa_tas) 
    RETURN a.entity_name as src, r.keywords as kw, b.entity_name as tgt
    LIMIT 10
''')
for i in inferred:
    src = str(i['src'])[:25] if i['src'] else 'N/A'
    tgt = str(i['tgt'])[:25] if i['tgt'] else 'N/A'
    kw = str(i['kw'])[:20] if i['kw'] else 'N/A'
    print(f"  {src} --[{kw}]--> {tgt}")

# Check orphans with names
print('\nOrphans with actual names:')
orphans = q('''
    MATCH (n:swa_tas) 
    WHERE NOT (n)-[]-(:swa_tas) AND n.entity_name IS NOT NULL
    RETURN n.entity_name as name, n.entity_type as type
    LIMIT 15
''')
for o in orphans:
    print(f"  - {o['name'][:50]} ({o['type']})")

# Check numbered entities that should have hierarchy
print('\nEntities with numbered prefixes (for hierarchy):')
numbered = q('''
    MATCH (n:swa_tas)
    WHERE n.entity_name =~ '.*[0-9]+\\\\.[0-9]+.*'
    RETURN n.entity_name as name, n.entity_type as type
    ORDER BY n.entity_name
    LIMIT 25
''')
print(f'Found {len(numbered)} numbered entities')
for n in numbered[:20]:
    print(f"  - {n['name'][:60]} ({n['type']})")

driver.close()
