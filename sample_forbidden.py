import networkx as nx
import random

G = nx.read_graphml('./rag_storage/default/graph_chunk_entity_relation.graphml')

unknown_entities = [(node, data.get('description', 'N/A')[:100]) for node, data in G.nodes(data=True) if data.get('entity_type') == 'UNKNOWN']
other_entities = [(node, data.get('description', 'N/A')[:100]) for node, data in G.nodes(data=True) if data.get('entity_type') == 'other']

print('🔍 SAMPLE UNKNOWN ENTITIES (10 random):')
print('=' * 80)
for name, desc in random.sample(unknown_entities, min(10, len(unknown_entities))):
    print(f'  Entity: {name}')
    print(f'  Desc: {desc}')
    print()

print('\n🔍 SAMPLE other ENTITIES (10 random):')
print('=' * 80)
for name, desc in random.sample(other_entities, min(10, len(other_entities))):
    print(f'  Entity: {name}')
    print(f'  Desc: {desc}')
    print()
