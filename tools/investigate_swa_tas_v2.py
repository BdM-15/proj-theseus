#!/usr/bin/env python3
"""Comprehensive swa_tas workspace quality investigation."""

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
print('SWA_TAS WORKSPACE - COMPREHENSIVE QUALITY INVESTIGATION')
print('=' * 70)

# Basic counts
entities = q('MATCH (n:swa_tas) RETURN count(n) as c')[0]['c']
rels = q('MATCH (a:swa_tas)-[r]->(b:swa_tas) RETURN count(r) as c')[0]['c']
print(f'\n📊 TOTALS: {entities} entities, {rels} relationships')

# Entity type distribution
print('\n📋 ENTITY TYPE DISTRIBUTION:')
types = q('MATCH (n:swa_tas) RETURN n.entity_type as t, count(n) as c ORDER BY c DESC')
for t in types:
    print(f"  {str(t['t']):<30}: {t['c']:>4}")

# Orphan analysis (using entity_id)
print('\n👻 ORPHAN ANALYSIS:')
orphan_count = q('MATCH (n:swa_tas) WHERE NOT (n)-[]-(:swa_tas) RETURN count(n) as c')[0]['c']
print(f'  Orphan count: {orphan_count}')

orphans = q('''
    MATCH (n:swa_tas) 
    WHERE NOT (n)-[]-(:swa_tas) 
    RETURN n.entity_id as name, n.entity_type as type
    LIMIT 20
''')
if orphans:
    print('  Sample orphans:')
    for o in orphans:
        name = str(o['name'])[:50] if o['name'] else 'N/A'
        print(f"    - {name} ({o['type']})")

# Relationship analysis
print('\n🔗 RELATIONSHIP TYPES:')
rel_types = q('MATCH (a:swa_tas)-[r]->(b:swa_tas) RETURN type(r) as t, count(r) as c ORDER BY c DESC')
for r in rel_types:
    print(f"  {str(r['t']):<40}: {r['c']:>4}")

# CHILD_OF in keywords
print('\n📁 CHILD_OF RELATIONSHIPS (in keywords):')
child_of_count = q('''
    MATCH (a:swa_tas)-[r]->(b:swa_tas) 
    WHERE r.keywords CONTAINS 'CHILD_OF'
    RETURN count(r) as c
''')[0]['c']
print(f'  Count: {child_of_count}')

child_of_samples = q('''
    MATCH (a:swa_tas)-[r]->(b:swa_tas) 
    WHERE r.keywords CONTAINS 'CHILD_OF'
    RETURN a.entity_id as child, b.entity_id as parent
    LIMIT 15
''')
if child_of_samples:
    print('  Sample hierarchies:')
    for s in child_of_samples:
        child = str(s['child'])[:35] if s['child'] else 'N/A'
        parent = str(s['parent'])[:35] if s['parent'] else 'N/A'
        print(f"    {child} → {parent}")

# Numbered entities for hierarchy
print('\n📝 NUMBERED ENTITIES (for hierarchy detection):')
numbered = q('''
    MATCH (n:swa_tas)
    WHERE n.entity_id =~ '.*[0-9]+\\\\.[0-9]+.*'
    RETURN n.entity_id as name, n.entity_type as type
    ORDER BY n.entity_id
    LIMIT 30
''')
print(f'  Found: {len(numbered)}')
for n in numbered[:20]:
    print(f"    - {n['name'][:60]} ({n['type']})")

# Workload enrichment check
print('\n💼 WORKLOAD ENRICHMENT:')
total_reqs = q('MATCH (n:swa_tas {entity_type: "requirement"}) RETURN count(n) as c')[0]['c']
enriched = q('MATCH (n:swa_tas {entity_type: "requirement"}) WHERE n.complexity_score IS NOT NULL RETURN count(n) as c')[0]['c']
print(f'  Total requirements: {total_reqs}')
print(f'  Enriched: {enriched} ({100*enriched/total_reqs:.1f}%)' if total_reqs else '  No requirements')

# Sample enriched requirement
sample = q('''
    MATCH (n:swa_tas {entity_type: "requirement"})
    WHERE n.complexity_score IS NOT NULL
    RETURN n.entity_id as name, n.complexity_score as score, n.labor_drivers as labor
    LIMIT 3
''')
if sample:
    print('  Sample enriched:')
    for s in sample:
        name = str(s['name'])[:50] if s['name'] else 'N/A'
        labor = str(s['labor'])[:50] if s['labor'] else 'none'
        print(f"    - {name} (complexity: {s['score']})")
        print(f"      Labor: {labor}...")

# Evaluation factors
print('\n📋 EVALUATION FACTORS:')
factors = q('MATCH (n:swa_tas {entity_type: "evaluation_factor"}) RETURN n.entity_id as name ORDER BY name')
print(f'  Count: {len(factors)}')
for f in factors:
    print(f"    - {f['name']}")

# CDRLs/Deliverables
print('\n📦 DELIVERABLES & CDRLs:')
delivs = q('MATCH (n:swa_tas {entity_type: "deliverable"}) RETURN count(n) as c')[0]['c']
cdrls = q('MATCH (n:swa_tas) WHERE n.entity_id CONTAINS "CDRL" RETURN n.entity_id as name LIMIT 20')
print(f'  Total deliverables: {delivs}')
print(f'  CDRLs found: {len(cdrls)}')
for c in cdrls[:15]:
    print(f"    - {c['name']}")

# Sample INFERRED relationships
print('\n⚙️ INFERRED RELATIONSHIPS (post-processing):')
inferred = q('''
    MATCH (a:swa_tas)-[r:INFERRED_RELATIONSHIP]->(b:swa_tas) 
    RETURN a.entity_id as src, r.keywords as kw, b.entity_id as tgt
    LIMIT 15
''')
print(f'  Total: {q("MATCH ()-[r:INFERRED_RELATIONSHIP]->() WHERE (startNode(r)):swa_tas RETURN count(r) as c")[0]["c"]}')
for i in inferred[:10]:
    src = str(i['src'])[:25] if i['src'] else 'N/A'
    tgt = str(i['tgt'])[:25] if i['tgt'] else 'N/A'
    kw = str(i['kw'])[:25] if i['kw'] else 'N/A'
    print(f"    {src} --[{kw}]--> {tgt}")

# Document structure
print('\n📄 DOCUMENT STRUCTURE:')
docs = q('MATCH (n:swa_tas {entity_type: "document"}) RETURN count(n) as c')[0]['c']
sections = q('MATCH (n:swa_tas {entity_type: "section"}) RETURN count(n) as c')[0]['c']
print(f'  Documents: {docs}')
print(f'  Sections: {sections}')

# Appendices
print('\n📑 APPENDICES:')
appendices = q('''
    MATCH (n:swa_tas) 
    WHERE n.entity_id STARTS WITH "Appendix"
    RETURN n.entity_id as name, n.entity_type as type
    ORDER BY name
''')
for a in appendices:
    print(f"    - {a['name']} ({a['type']})")

driver.close()
print('\n' + '=' * 70)
print('INVESTIGATION COMPLETE')
print('=' * 70)
