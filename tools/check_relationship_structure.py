"""Check relationship structure in Neo4j to understand LightRAG's data model."""
import os
import re
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session(database='neo4j') as session:
    print("=" * 80)
    print("RELATIONSHIP STRUCTURE ANALYSIS")
    print("=" * 80)
    
    # Check what properties exist on relationships
    print("\n1. PROPERTIES ON RELATIONSHIPS:")
    result = session.run('''
        MATCH (n:swa_tas)-[r]->(m:swa_tas)
        RETURN keys(r) as props, type(r) as rel_type
        LIMIT 5
    ''')
    for rec in result:
        print(f"  Type: {rec['rel_type']}")
        print(f"  Props: {rec['props']}")
        print()
    
    # Check DIRECTED relationships (from LightRAG extraction)
    print("\n2. SAMPLE DIRECTED RELATIONSHIPS (LightRAG extraction):")
    result = session.run('''
        MATCH (n:swa_tas)-[r:DIRECTED]->(m:swa_tas)
        RETURN n.entity_id as src, m.entity_id as tgt, 
               r.description as desc, r.keywords as keywords,
               n.entity_type as src_type, m.entity_type as tgt_type
        LIMIT 5
    ''')
    for rec in result:
        print(f"  [{rec['src_type']}] {rec['src'][:50]}")
        print(f"    --DIRECTED-->")
        print(f"  [{rec['tgt_type']}] {rec['tgt'][:50]}")
        kw = rec['keywords'][:100] if rec['keywords'] else '(none)'
        desc = rec['desc'][:150] if rec['desc'] else '(none)'
        print(f"    Keywords: {kw}")
        print(f"    Description: {desc}")
        print()
    
    # Check INFERRED_RELATIONSHIP (from our post-processing)
    print("\n3. SAMPLE INFERRED_RELATIONSHIPS (post-processing):")
    result = session.run('''
        MATCH (n:swa_tas)-[r:INFERRED_RELATIONSHIP]->(m:swa_tas)
        RETURN n.entity_id as src, m.entity_id as tgt, 
               r.type as inferred_type, r.reasoning as reasoning,
               n.entity_type as src_type, m.entity_type as tgt_type
        LIMIT 5
    ''')
    for rec in result:
        print(f"  [{rec['src_type']}] {rec['src'][:50]}")
        print(f"    --INFERRED ({rec['inferred_type']})-->")
        print(f"  [{rec['tgt_type']}] {rec['tgt'][:50]}")
        reason = rec['reasoning'][:150] if rec['reasoning'] else '(none)'
        print(f"    Reasoning: {reason}")
        print()
    
    # Search for workload-related relationships
    print("\n4. RELATIONSHIPS MENTIONING 'WORKLOAD' OR 'APPENDIX H':")
    result = session.run('''
        MATCH (n:swa_tas)-[r]->(m:swa_tas)
        WHERE toLower(r.description) CONTAINS 'workload' 
           OR toLower(r.keywords) CONTAINS 'workload'
           OR toLower(n.entity_id) CONTAINS 'workload'
           OR toLower(m.entity_id) CONTAINS 'workload'
        RETURN n.entity_id as src, m.entity_id as tgt, type(r) as rel_type,
               r.description as desc, r.keywords as kw
        LIMIT 10
    ''')
    count = 0
    for rec in result:
        count += 1
        print(f"  {rec['src'][:40]} --[{rec['rel_type']}]--> {rec['tgt'][:40]}")
        if rec['kw']:
            print(f"    Keywords: {rec['kw'][:80]}")
        if rec['desc']:
            print(f"    Desc: {rec['desc'][:100]}")
        print()
    if count == 0:
        print("  (none found)")
    
    # Check entity descriptions for workload entities
    print("\n5. WORKLOAD-RELATED ENTITIES AND THEIR DESCRIPTIONS:")
    result = session.run('''
        MATCH (n:swa_tas)
        WHERE toLower(n.entity_id) CONTAINS 'workload'
           OR toLower(n.entity_id) CONTAINS 'aircraft operations'
           OR toLower(n.description) CONTAINS 'monthly workload'
        RETURN n.entity_id as name, n.entity_type as type, 
               n.description as desc, n.source_id as source
        LIMIT 10
    ''')
    for rec in result:
        print(f"  Entity: {rec['name']}")
        print(f"  Type: {rec['type']}")
        desc = rec['desc'][:300] if rec['desc'] else '(none)'
        print(f"  Description: {desc}")
        source = rec['source'][:100] if rec['source'] else '(none)'
        print(f"  Source chunks: {source}...")
        print()

driver.close()
print("\nDone.")
