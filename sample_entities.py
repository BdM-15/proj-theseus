#!/usr/bin/env python3
"""Sample entities to check quality."""

import networkx as nx
import random

G = nx.read_graphml('rag_storage/default/graph_chunk_entity_relation.graphml')

# Sample evaluation factors
eval_factors = [n for n in G.nodes() if G.nodes[n].get('entity_type') == 'evaluation_factor']
print('=' * 80)
print(f'EVALUATION FACTORS (Total: {len(eval_factors)})')
print('=' * 80)
for n in random.sample(eval_factors, min(5, len(eval_factors))):
    print(f'\n{G.nodes[n].get("entity_name", n)}')
    print(f'Description: {G.nodes[n].get("description", "NO DESC")[:400]}...')
    print('-' * 80)

# Sample strategic themes
themes = [n for n in G.nodes() if G.nodes[n].get('entity_type') == 'strategic_theme']
print('\n' + '=' * 80)
print(f'STRATEGIC THEMES (Total: {len(themes)})')
print('=' * 80)
for n in themes:  # Show all since there are only 9
    print(f'\n{G.nodes[n].get("entity_name", n)}')
    print(f'Description: {G.nodes[n].get("description", "NO DESC")[:400]}...')
    print('-' * 80)

# Sample requirements
requirements = [n for n in G.nodes() if G.nodes[n].get('entity_type') == 'requirement']
print('\n' + '=' * 80)
print(f'REQUIREMENTS (Total: {len(requirements)})')
print('=' * 80)
for n in random.sample(requirements, min(5, len(requirements))):
    print(f'\n{G.nodes[n].get("entity_name", n)}')
    desc = G.nodes[n].get("description", "NO DESC")
    print(f'Description: {desc[:400]}{"..." if len(desc) > 400 else ""}')
    print('-' * 80)

# Check EVALUATED_BY relationships
eval_by_rels = [e for e in G.edges() if G.edges[e].get('keywords') == 'EVALUATED_BY']
print('\n' + '=' * 80)
print(f'EVALUATED_BY RELATIONSHIPS (Total: {len(eval_by_rels)})')
print('=' * 80)
for source, target in eval_by_rels[:5]:
    source_name = G.nodes[source].get('entity_name', source)
    target_name = G.nodes[target].get('entity_name', target)
    rel_desc = G.edges[(source, target)].get('description', 'NO DESC')
    print(f'\n{source_name} --> {target_name}')
    print(f'Description: {rel_desc[:300]}...')
    print('-' * 80)
