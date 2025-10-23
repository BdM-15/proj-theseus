import networkx as nx
from collections import Counter

G = nx.read_graphml('./rag_storage/default/graph_chunk_entity_relation.graphml')

# Get all entity types
all_types = []
for node, data in G.nodes(data=True):
    entity_type = data.get('entity_type', 'MISSING')
    if entity_type:
        all_types.append(entity_type)
    else:
        all_types.append('MISSING')

type_counts = Counter(all_types)

print("🔍 ALL ENTITY TYPES (including weird ones):")
print("=" * 60)
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    marker = ""
    if t in ['UNKNOWN', 'other']:
        marker = " ⚠️ FORBIDDEN"
    elif '#' in str(t):
        marker = " 🔴 CORRUPTED"
    elif t == 'MISSING':
        marker = " 🔴 NULL"
    print(f"  {t}: {count}{marker}")

print(f"\n📊 SUMMARY:")
print(f"  Total nodes: {G.number_of_nodes()}")
print(f"  Unique types: {len(type_counts)}")
print(f"  UNKNOWN: {type_counts.get('UNKNOWN', 0)}")
print(f"  other: {type_counts.get('other', 0)}")
print(f"  #concept: {type_counts.get('#concept', 0)}")
print(f"  MISSING/None: {type_counts.get('MISSING', 0)}")
