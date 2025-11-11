#!/usr/bin/env python3
"""Assess ISS RFP baseline entity extraction"""

from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'govcon-capture-2025'))

# Use default 'neo4j' database, filter by workspace label
with driver.session(database='neo4j') as session:
    # Total nodes in afcapv_adab_iss_2025 workspace
    result = session.run('''
        MATCH (n:`afcapv_adab_iss_2025`) 
        RETURN count(n) as total
    ''')
    total = result.single()['total']
    print(f'BASELINE ASSESSMENT: ISS RFP (afcapv_adab_iss_2025)')
    print(f'=' * 60)
    print(f'Total entities: {total}')
    
    # Entity type breakdown
    result = session.run('''
        MATCH (n:`afcapv_adab_iss_2025`) 
        RETURN n.entity_type as type, count(*) as count 
        ORDER BY count DESC
    ''')
    print(f'\nEntity type breakdown:')
    for record in result:
        print(f'  {record["type"]}: {record["count"]}')
    
    # Total relationships
    result = session.run('''
        MATCH (:`afcapv_adab_iss_2025`)-[r]->() 
        RETURN count(r) as total
    ''')
    rel_total = result.single()['total']
    print(f'\nTotal relationships: {rel_total}')
    
    # Avg relationships per entity
    if total > 0:
        avg_rel = rel_total / total
        print(f'Avg relationships per entity: {avg_rel:.2f}')
    
    # Check for prohibited entity types
    result = session.run('''
        MATCH (n:`afcapv_adab_iss_2025`)
        WHERE n.entity_type IN ['UNKNOWN', '#document', '#organization', '#requirement']
        RETURN n.entity_type as type, count(*) as count
        ORDER BY count DESC
    ''')
    prohibited = list(result)
    if prohibited:
        print(f'\n⚠️  PROHIBITED ENTITY TYPES DETECTED:')
        for record in prohibited:
            print(f'  {record["type"]}: {record["count"]} entities')
    
    # Sample REQUIREMENT entities
    result = session.run('''
        MATCH (n:`afcapv_adab_iss_2025`)
        WHERE n.entity_type = 'requirement'
        RETURN n.description as desc
        LIMIT 5
    ''')
    print(f'\nSample REQUIREMENT entities:')
    for i, record in enumerate(result, 1):
        desc = record['desc'][:100] + '...' if len(record['desc']) > 100 else record['desc']
        print(f'  {i}. {desc}')

driver.close()
