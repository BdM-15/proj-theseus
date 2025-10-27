#!/usr/bin/env python3
"""Analyze Option A extraction results and compare to baseline."""

import networkx as nx
from collections import Counter

# Load the new graph
G = nx.read_graphml('rag_storage/default/graph_chunk_entity_relation.graphml')

print('=' * 80)
print('OPTION A EXTRACTION RESULTS - MCPP II RFP')
print('=' * 80)
print()

# Entity counts
entity_types = [G.nodes[n].get('entity_type', 'unknown') for n in G.nodes()]
entity_counter = Counter(entity_types)
total_entities = len(G.nodes())

print(f'📊 TOTAL ENTITIES: {total_entities}')
print()
print('Entity Type Distribution:')
for entity_type, count in sorted(entity_counter.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total_entities) * 100
    print(f'  {entity_type:25s} {count:5d} ({pct:5.2f}%)')
print()

# Relationship counts
relationships = [(G.edges[e].get('keywords', ''), G.edges[e].get('description', '')) for e in G.edges()]
rel_types = [kw for kw, desc in relationships]
rel_counter = Counter(rel_types)
total_rels = len(G.edges())

print(f'🔗 TOTAL RELATIONSHIPS: {total_rels}')
print()
print('Top 20 Relationship Types:')
for rel_type, count in rel_counter.most_common(20):
    pct = (count / total_rels) * 100
    print(f'  {rel_type:30s} {count:5d} ({pct:5.2f}%)')
print()

# Description quality
entities_with_desc = sum(1 for n in G.nodes() if G.nodes[n].get('description', '').strip())
desc_lengths = [len(G.nodes[n].get('description', '')) for n in G.nodes() if G.nodes[n].get('description', '').strip()]
avg_desc_len = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0

rels_with_desc = sum(1 for e in G.edges() if G.edges[e].get('description', '').strip())
rel_desc_lengths = [len(G.edges[e].get('description', '')) for e in G.edges() if G.edges[e].get('description', '').strip()]
avg_rel_desc_len = sum(rel_desc_lengths) / len(rel_desc_lengths) if rel_desc_lengths else 0

print('📝 DESCRIPTION QUALITY:')
print(f'  Entities with descriptions: {entities_with_desc}/{total_entities} ({(entities_with_desc/total_entities)*100:.1f}%)')
print(f'  Average entity description: {avg_desc_len:.1f} characters')
print(f'  Relationships with descriptions: {rels_with_desc}/{total_rels} ({(rels_with_desc/total_rels)*100:.1f}%)')
print(f'  Average relationship description: {avg_rel_desc_len:.1f} characters')
print()

# Key metrics for comparison
print('🎯 KEY METRICS (for baseline comparison):')
print(f'  EVALUATED_BY relationships: {rel_counter.get("EVALUATED_BY", 0)}')
print(f'  GUIDES relationships: {rel_counter.get("GUIDES", 0)}')
print(f'  Evaluation factors: {entity_counter.get("evaluation_factor", 0)}')
print(f'  Strategic themes: {entity_counter.get("strategic_theme", 0)}')
print(f'  Requirements: {entity_counter.get("requirement", 0)}')
print(f'  Clauses: {entity_counter.get("clause", 0)}')
print()

# Comparison with baseline
print('=' * 80)
print('COMPARISON WITH BRANCH 010 BASELINE')
print('=' * 80)
print()
baseline_entities = 4793
baseline_rels = 5932
baseline_evaluated_by = 34
baseline_guides = 22
baseline_eval_factors = 83
baseline_themes = 26

print(f'Entities:         {total_entities:5d} vs {baseline_entities:5d} baseline ({total_entities - baseline_entities:+5d}, {((total_entities - baseline_entities)/baseline_entities)*100:+6.2f}%)')
print(f'Relationships:    {total_rels:5d} vs {baseline_rels:5d} baseline ({total_rels - baseline_rels:+5d}, {((total_rels - baseline_rels)/baseline_rels)*100:+6.2f}%)')
print()
print('Key Relationship Improvements:')
evaluated_by_count = rel_counter.get("EVALUATED_BY", 0)
guides_count = rel_counter.get("GUIDES", 0)
print(f'  EVALUATED_BY:   {evaluated_by_count:5d} vs {baseline_evaluated_by:5d} baseline ({evaluated_by_count - baseline_evaluated_by:+5d}, {((evaluated_by_count - baseline_evaluated_by)/baseline_evaluated_by)*100:+6.2f}%)')
print(f'  GUIDES:         {guides_count:5d} vs {baseline_guides:5d} baseline ({guides_count - baseline_guides:+5d}, {((guides_count - baseline_guides)/baseline_guides)*100:+6.2f}%)')
print()
print('Key Entity Improvements:')
eval_factor_count = entity_counter.get("evaluation_factor", 0)
theme_count = entity_counter.get("strategic_theme", 0)
print(f'  Eval Factors:   {eval_factor_count:5d} vs {baseline_eval_factors:5d} baseline ({eval_factor_count - baseline_eval_factors:+5d}, {((eval_factor_count - baseline_eval_factors)/baseline_eval_factors)*100:+6.2f}%)')
print(f'  Strategic Themes: {theme_count:5d} vs {baseline_themes:5d} baseline ({theme_count - baseline_themes:+5d}, {((theme_count - baseline_themes)/baseline_themes)*100:+6.2f}%)')
print()
