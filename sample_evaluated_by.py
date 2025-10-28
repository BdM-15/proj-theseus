#!/usr/bin/env python3
"""Extract EVALUATED_BY relationship samples for quality validation."""

import networkx as nx

# Load graph
G = nx.read_graphml('rag_storage/default/graph_chunk_entity_relation.graphml')

print('=' * 80)
print('EVALUATED_BY RELATIONSHIP SAMPLES')
print('=' * 80)
print()

# Find EVALUATED_BY relationships
eval_by_rels = []
for edge in G.edges():
    edge_data = G.edges[edge]
    if edge_data.get('keywords') == 'EVALUATED_BY':
        src_node = G.nodes[edge[0]]
        tgt_node = G.nodes[edge[1]]
        
        # Get node IDs (the actual entity names/descriptions)
        src_id = edge[0]
        tgt_id = edge[1]
        
        # Get descriptions
        rel_desc = edge_data.get('description', 'No description')
        src_type = src_node.get('entity_type', 'unknown')
        tgt_type = tgt_node.get('entity_type', 'unknown')
        
        eval_by_rels.append({
            'source': src_id,
            'target': tgt_id,
            'source_type': src_type,
            'target_type': tgt_type,
            'description': rel_desc
        })

print(f'Found {len(eval_by_rels)} EVALUATED_BY relationships\n')
print('First 20 samples:\n')

for i, rel in enumerate(eval_by_rels[:20], 1):
    print(f'{i}. [{rel["source_type"]}] {rel["source"][:50]}...')
    print(f'   --EVALUATED_BY-->')
    print(f'   [{rel["target_type"]}] {rel["target"][:50]}...')
    print(f'   Description: {rel["description"][:150]}...')
    print()
