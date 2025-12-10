"""
Compare two Neo4j workspaces for entity/relationship analysis.
Useful for A/B testing prompt changes.

Note: Workspaces are stored as NODE LABELS in Neo4j, not as properties.
Query syntax: MATCH (n:`workspace_name`)
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)
database = os.getenv('NEO4J_DATABASE', 'neo4j')

workspaces = ['37a_test_mcpp', '37c_test_mcpp']

print("=" * 80)
print("WORKSPACE COMPARISON: V2 Baseline (37a) vs V2 + All Fixes (37c)")
print("=" * 80)

results = {}

with driver.session(database=database) as session:
    for ws in workspaces:
        print(f'\n{"=" * 40}')
        print(f'WORKSPACE: {ws}')
        print(f'{"=" * 40}')
        
        ws_data = {}
        
        # Total entities - using label syntax
        result = session.run(f'MATCH (n:`{ws}`) RETURN count(n) as count')
        entities = result.single()['count']
        ws_data['entities'] = entities
        print(f'Total Entities: {entities}')
        
        # Total relationships
        result = session.run(f'''
            MATCH (a:`{ws}`)-[r]->(b:`{ws}`)
            RETURN count(r) as count
        ''')
        rels = result.single()['count']
        ws_data['relationships'] = rels
        print(f'Total Relationships: {rels}')
        
        # Ratio
        ratio = rels / entities if entities > 0 else 0
        ws_data['ratio'] = ratio
        print(f'Relationship:Entity Ratio: {ratio:.2f}')
        
        # Orphan entities (no relationships)
        result = session.run(f'''
            MATCH (n:`{ws}`)
            WHERE NOT (n)-[]-()
            RETURN count(n) as count
        ''')
        orphans = result.single()['count']
        ws_data['orphans'] = orphans
        orphan_pct = 100 * orphans / entities if entities > 0 else 0
        ws_data['orphan_pct'] = orphan_pct
        print(f'Orphan Entities: {orphans} ({orphan_pct:.1f}%)')
        
        # Connected entities
        connected = entities - orphans
        ws_data['connected'] = connected
        print(f'Connected Entities: {connected} ({100 - orphan_pct:.1f}%)')
        
        # Entity types breakdown
        result = session.run(f'''
            MATCH (n:`{ws}`)
            RETURN n.entity_type as type, count(n) as count
            ORDER BY count DESC
        ''')
        print('\nEntity Type Distribution:')
        type_counts = {}
        for record in result:
            etype = record["type"] or "unknown"
            count = record["count"]
            type_counts[etype] = count
            print(f'  {etype}: {count}')
        ws_data['type_counts'] = type_counts
        
        # Relationship types breakdown
        result = session.run(f'''
            MATCH (a:`{ws}`)-[r]->(b:`{ws}`)
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            LIMIT 20
        ''')
        print('\nRelationship Type Distribution (Top 20):')
        rel_counts = {}
        for record in result:
            rtype = record["rel_type"]
            count = record["count"]
            rel_counts[rtype] = count
            print(f'  {rtype}: {count}')
        ws_data['rel_counts'] = rel_counts
        
        results[ws] = ws_data

driver.close()

# Comparison summary
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

old = results.get('36_test_mcpp', {})
new = results.get('37a_test_mcpp', {})

if old and new:
    print(f"\n{'Metric':<30} {'Old (36)':<15} {'New (37a)':<15} {'Change':<15}")
    print("-" * 75)
    
    # Entities
    old_e = old.get('entities', 0)
    new_e = new.get('entities', 0)
    change_e = ((new_e - old_e) / old_e * 100) if old_e > 0 else 0
    print(f"{'Total Entities':<30} {old_e:<15} {new_e:<15} {change_e:+.1f}%")
    
    # Relationships
    old_r = old.get('relationships', 0)
    new_r = new.get('relationships', 0)
    change_r = ((new_r - old_r) / old_r * 100) if old_r > 0 else 0
    print(f"{'Total Relationships':<30} {old_r:<15} {new_r:<15} {change_r:+.1f}%")
    
    # Ratio
    old_ratio = old.get('ratio', 0)
    new_ratio = new.get('ratio', 0)
    print(f"{'Rel:Entity Ratio':<30} {old_ratio:<15.2f} {new_ratio:<15.2f} {'WORSE' if new_ratio < old_ratio else 'BETTER'}")
    
    # Orphans
    old_o = old.get('orphans', 0)
    new_o = new.get('orphans', 0)
    old_o_pct = old.get('orphan_pct', 0)
    new_o_pct = new.get('orphan_pct', 0)
    print(f"{'Orphan Entities':<30} {old_o} ({old_o_pct:.1f}%)   {new_o} ({new_o_pct:.1f}%)   {'WORSE' if new_o_pct > old_o_pct else 'BETTER'}")
    
    # Connected
    old_c = old.get('connected', 0)
    new_c = new.get('connected', 0)
    print(f"{'Connected Entities':<30} {old_c:<15} {new_c:<15}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if new_o_pct > old_o_pct:
        print(f"\n⚠️  PROBLEM: Orphan rate INCREASED from {old_o_pct:.1f}% to {new_o_pct:.1f}%")
        print("   This suggests V2 prompts are extracting MORE entities but FEWER relationships.")
        print("   The relationship extraction rules may not be working as intended.")
    
    if new_ratio < old_ratio:
        print(f"\n⚠️  PROBLEM: Relationship:Entity ratio DECREASED from {old_ratio:.2f} to {new_ratio:.2f}")
        print("   This confirms the relationship extraction is underperforming.")
    
    if new_e > old_e * 1.5:
        print(f"\n📊 NOTE: Entity count increased by {change_e:.1f}%")
        print("   More entities isn't necessarily better if they're not connected.")
