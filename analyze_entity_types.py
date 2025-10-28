import networkx as nx

# Load graph
G = nx.read_graphml('rag_storage/default/graph_chunk_entity_relation.graphml')

# Count entity types
entity_types = {}
for node, data in G.nodes(data=True):
    et = data.get('entity_type', 'UNKNOWN')
    entity_types[et] = entity_types.get(et, 0) + 1

# Count relationship types
relationship_types = {}
for u, v, data in G.edges(data=True):
    rt = data.get('keywords', 'UNKNOWN')
    relationship_types[rt] = relationship_types.get(rt, 0) + 1

print(f'Entity Type Distribution ({len(entity_types)} unique types):')
print('='*80)
for et in sorted(entity_types.keys()):
    print(f'{et:30} : {entity_types[et]:5}')
print('='*80)
print(f'TOTAL ENTITIES: {G.number_of_nodes()}')
print()

print(f'Relationship Type Distribution ({len(relationship_types)} unique types):')
print('='*80)
for rt in sorted(relationship_types.keys()):
    print(f'{rt:30} : {relationship_types[rt]:5}')
print('='*80)
print(f'TOTAL RELATIONSHIPS: {G.number_of_edges()}')
