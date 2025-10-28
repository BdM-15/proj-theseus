import networkx as nx

G = nx.read_graphml('rag_storage/default/graph_chunk_entity_relation.graphml')

et = {}
for n, d in G.nodes(data=True):
    t = d.get('entity_type', 'UNKNOWN')
    et[t] = et.get(t, 0) + 1

print('='*80)
print('ENTITY TYPE DISTRIBUTION')
print('='*80)
for t in sorted(et.keys()):
    print(f'{t:35} : {et[t]:5}')
print('='*80)
print(f'UNIQUE ENTITY TYPES: {len(et)}')
print(f'TOTAL ENTITIES: {sum(et.values())}')
