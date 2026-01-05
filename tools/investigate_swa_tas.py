#!/usr/bin/env python3
"""Investigate swa_tas workspace quality in Neo4j."""

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

print('=' * 70)
print('SWA_TAS WORKSPACE QUALITY INVESTIGATION')
print('=' * 70)

# Counts
entities = q('MATCH (n:swa_tas) RETURN count(n) as c')[0]['c']
rels = q('MATCH (a:swa_tas)-[r]->(b:swa_tas) RETURN count(r) as c')[0]['c']
print(f'\nEntities: {entities}')
print(f'Relationships: {rels}')

# Entity types
print('\n📋 ENTITY TYPE DISTRIBUTION:')
types = q('MATCH (n:swa_tas) RETURN n.entity_type as t, count(n) as c ORDER BY c DESC')
for t in types:
    print(f"  {str(t['t']):<30}: {t['c']:>4}")

# Orphans - entities with NO relationships at all within workspace
print('\n👻 ORPHAN ANALYSIS:')
orphan_count = q('''
    MATCH (n:swa_tas) 
    WHERE NOT (n)-[]-(:swa_tas) 
    RETURN count(n) as c
''')[0]['c']
print(f'  Orphan count: {orphan_count}')

orphan_samples = q('''
    MATCH (n:swa_tas) 
    WHERE NOT (n)-[]-(:swa_tas) 
    RETURN n.entity_name as name, n.entity_type as type 
    LIMIT 15
''')
if orphan_samples:
    print('  Sample orphans:')
    for o in orphan_samples:
        name = str(o['name'])[:50] if o['name'] else 'N/A'
        print(f"    - {name} ({o['type']})")

# Relationship types
print('\n🔗 RELATIONSHIP TYPES:')
rel_types = q('MATCH (a:swa_tas)-[r]->(b:swa_tas) RETURN type(r) as t, count(r) as c ORDER BY c DESC')
for r in rel_types:
    print(f"  {str(r['t']):<40}: {r['c']:>4}")

# CHILD_OF check
child_of = q('MATCH (a:swa_tas)-[r:CHILD_OF]->(b:swa_tas) RETURN count(r) as c')
print(f"\n📁 CHILD_OF relationships: {child_of[0]['c'] if child_of else 0}")

# Sample CHILD_OF
samples = q('MATCH (a:swa_tas)-[r:CHILD_OF]->(b:swa_tas) RETURN a.entity_name as child, b.entity_name as parent LIMIT 15')
if samples:
    print('  Sample CHILD_OF hierarchies:')
    for s in samples:
        child = str(s['child'])[:40] if s['child'] else 'N/A'
        parent = str(s['parent'])[:40] if s['parent'] else 'N/A'
        print(f"    {child} → {parent}")

# Numbered hierarchy check
print('\n📝 NUMBERED SECTION HIERARCHY:')
numbered = q('''
    MATCH (n:swa_tas)
    WHERE n.entity_name =~ '^[A-Z]\\\\.[0-9].*|^[0-9]+\\\\.[0-9].*'
    RETURN n.entity_name as name, n.entity_type as type
    ORDER BY n.entity_name
    LIMIT 20
''')
print(f'  Numbered entities: {len(numbered)}')
for n in numbered[:15]:
    print(f"    - {n['name'][:60]} ({n['type']})")

# Workload enrichment
print('\n💼 WORKLOAD ENRICHMENT:')
enriched = q('MATCH (n:swa_tas {entity_type: "requirement"}) WHERE n.complexity_score IS NOT NULL RETURN count(n) as c')[0]['c']
total_reqs = q('MATCH (n:swa_tas {entity_type: "requirement"}) RETURN count(n) as c')[0]['c']
print(f'  Requirements: {total_reqs}')
print(f'  Enriched: {enriched} ({100*enriched/total_reqs:.1f}% if total_reqs else 0)')

# Sample enriched requirement
sample_enriched = q('''
    MATCH (n:swa_tas {entity_type: "requirement"})
    WHERE n.complexity_score IS NOT NULL
    RETURN n.entity_name as name, n.complexity_score as complexity, n.labor_drivers as labor
    LIMIT 3
''')
if sample_enriched:
    print('  Sample enriched requirements:')
    for r in sample_enriched:
        print(f"    - {r['name'][:50]} (complexity: {r['complexity']})")

# Evaluation factors
print('\n📋 EVALUATION FACTORS:')
eval_factors = q('MATCH (n:swa_tas {entity_type: "evaluation_factor"}) RETURN n.entity_name as name ORDER BY name')
print(f'  Count: {len(eval_factors)}')
for ef in eval_factors:
    print(f"    - {ef['name']}")

# Deliverables
print('\n📦 DELIVERABLES:')
delivs = q('MATCH (n:swa_tas {entity_type: "deliverable"}) RETURN count(n) as c')[0]['c']
print(f'  Count: {delivs}')

# CDRLs specifically
cdrls = q('MATCH (n:swa_tas) WHERE n.entity_name CONTAINS "CDRL" RETURN n.entity_name as name LIMIT 15')
print(f'  CDRLs found:')
for c in cdrls:
    print(f"    - {c['name']}")

driver.close()
print('\n' + '=' * 70)
print('INVESTIGATION COMPLETE')
print('=' * 70)
