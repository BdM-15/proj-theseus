#!/usr/bin/env python3
"""
Source of Truth Validation Script
Validates the knowledge graph is being built effectively for capture intelligence
"""

from dotenv import load_dotenv
import os
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME')
pwd = os.getenv('NEO4J_PASSWORD')
driver = GraphDatabase.driver(uri, auth=(user, pwd))

print('='*70)
print('SOURCE OF TRUTH VALIDATION - Knowledge Graph Assessment')
print('='*70)

with driver.session() as session:
    # 4. Evaluation Factor connections
    print()
    print('4. EVALUATION FACTORS AND CONNECTIONS')
    print('-'*50)
    query = """
        MATCH (ef:swa_tas)
        WHERE ef.entity_type = 'evaluation_factor'
        OPTIONAL MATCH (ef)-[r]->(c)
        RETURN ef.entity_id as factor, count(r) as connections
        ORDER BY connections DESC
    """
    result = session.run(query)
    for r in result:
        factor = r['factor'] or 'NULL'
        print(f"   {factor[:55]:57} {r['connections']}")

    # 5. Check BOE enrichment
    print()
    print('5. BOE ENRICHMENT STATUS')
    print('-'*50)
    # Correct property name: has_workload_metric (not boe_categories)
    query = """
        MATCH (r:swa_tas)
        WHERE r.entity_type = 'requirement' AND r.has_workload_metric = true
        RETURN count(r) as enriched
    """
    result = session.run(query)
    enriched = result.single()['enriched']
    print(f"   Requirements with workload enrichment: {enriched}/315")
    
    # Sample enriched data (actual property names from workload_enrichment.py)
    query = """
        MATCH (r:swa_tas)
        WHERE r.entity_type = 'requirement' AND r.has_workload_metric = true
        RETURN r.entity_id as req, r.workload_categories as cats, r.complexity_score as score
        LIMIT 5
    """
    result = session.run(query)
    print()
    print('   Sample enriched requirements:')
    for r in result:
        req = r['req'] or ''
        cats = str(r['cats'])[:40] if r['cats'] else 'N/A'
        score = r['score'] or 'N/A'
        print(f"   - {req[:35]:37} score:{score} cats:{cats}")

    # 6. Deliverable to Requirement traceability
    print()
    print('6. DELIVERABLE TRACEABILITY')
    print('-'*50)
    query = """
        MATCH (d:swa_tas)-[r]->(req:swa_tas)
        WHERE d.entity_type = 'deliverable' AND req.entity_type = 'requirement'
        RETURN count(r) as traces
    """
    result = session.run(query)
    traces = result.single()['traces']
    print(f"   Deliverable->Requirement links: {traces}")
    
    query = """
        MATCH (req:swa_tas)-[r]->(d:swa_tas)
        WHERE d.entity_type = 'deliverable' AND req.entity_type = 'requirement'
        RETURN count(r) as traces
    """
    result = session.run(query)
    traces2 = result.single()['traces']
    print(f"   Requirement->Deliverable links: {traces2}")
    print(f"   Total traceability links: {traces + traces2}")

    # 7. Document hierarchy (parent-child)
    print()
    print('7. DOCUMENT HIERARCHY (CHILD_OF relationships)')
    print('-'*50)
    query = """
        MATCH (:swa_tas)-[r:INFERRED_RELATIONSHIP]->(:swa_tas)
        WHERE r.relationship_type = 'CHILD_OF'
        RETURN count(r) as child_of_count
    """
    result = session.run(query)
    child_of = result.single()['child_of_count']
    print(f"   CHILD_OF relationships: {child_of}")

    # 8. Workload table connectivity
    print()
    print('8. WORKLOAD TABLE CONNECTIVITY')
    print('-'*50)
    query = """
        MATCH (t:swa_tas)
        WHERE t.entity_id CONTAINS 'table_p' AND 
              (t.description CONTAINS 'workload' OR t.description CONTAINS 'Workload' OR
               t.description CONTAINS 'aircraft' OR t.description CONTAINS 'Aircraft' OR
               t.description CONTAINS '760')
        OPTIONAL MATCH (t)-[r]->(connected)
        RETURN t.entity_id as table_name, count(r) as connections
        ORDER BY connections DESC
        LIMIT 10
    """
    result = session.run(query)
    print("   Workload tables and their connections:")
    for r in result:
        print(f"   - {r['table_name']:20} -> {r['connections']} connections")

    # 9. Location to requirement mapping
    print()
    print('9. LOCATION COVERAGE')
    print('-'*50)
    query = """
        MATCH (loc:swa_tas)
        WHERE loc.entity_type = 'location'
        OPTIONAL MATCH (loc)-[r]->(other)
        RETURN loc.entity_id as location, count(r) as connections
        ORDER BY connections DESC
        LIMIT 10
    """
    result = session.run(query)
    for r in result:
        loc = r['location'] or 'NULL'
        print(f"   {loc[:45]:47} {r['connections']} connections")

    # 10. Orphan check
    print()
    print('10. GRAPH CONNECTIVITY (Orphan Check)')
    print('-'*50)
    query = """
        MATCH (n:swa_tas)
        WHERE NOT (n)-[]-()
        RETURN count(n) as orphans
    """
    result = session.run(query)
    orphans = result.single()['orphans']
    print(f"   Completely isolated entities: {orphans}/985")
    print(f"   Connectivity rate: {round((985-orphans)/985*100, 1)}%")

driver.close()

print()
print('='*70)
print('ASSESSMENT COMPLETE')
print('='*70)
