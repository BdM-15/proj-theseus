import networkx as nx

G = nx.read_graphml('./rag_storage/default/graph_chunk_entity_relation.graphml')

nodes = G.number_of_nodes()
edges = G.number_of_edges()
ratio = round(edges / nodes, 2) if nodes > 0 else 0

# Count entity types
types = {}
for node, data in G.nodes(data=True):
    entity_type = data.get('entity_type', 'UNKNOWN')
    types[entity_type] = types.get(entity_type, 0) + 1

unknown_count = types.get('UNKNOWN', 0)
other_count = types.get('other', 0)
custom_types = nodes - unknown_count - other_count
coverage = round((custom_types / nodes) * 100, 1) if nodes > 0 else 0

print('📊 ITERATION 8 RESULTS (Updated Prompts):')
print('=' * 55)
print(f'Nodes: {nodes:,}')
print(f'Edges: {edges:,}')
print(f'Edge/node ratio: {ratio}')
print(f'UNKNOWN: {unknown_count} ({round(unknown_count/nodes*100, 1)}%)')
print(f'other: {other_count} ({round(other_count/nodes*100, 1)}%)')
print(f'Untyped total: {unknown_count + other_count} ({round((unknown_count + other_count)/nodes*100, 1)}%)')
print(f'Custom types: {custom_types:,} ({coverage}% coverage)')

print(f'\n📈 TOP 15 ENTITY TYPES:')
for t, c in sorted(types.items(), key=lambda x: x[1], reverse=True)[:15]:
    pct = round(c/nodes*100, 1)
    marker = ' ⚠️ FORBIDDEN' if t in ['UNKNOWN', 'other'] else ''
    marker2 = ' ✅ ABSORBED' if t == 'concept' else ''
    print(f'  {t}: {c:,} ({pct}%){marker}{marker2}')

print(f'\n🎯 VS ITERATION 7 (Previous Best):')
print(f'  Nodes: {nodes:,} vs 2,742 ({nodes-2742:+,} = {round((nodes-2742)/2742*100, 1):+.1f}%)')
print(f'  Ratio: {ratio} vs 1.77 ({ratio-1.77:+.2f})')
print(f'  UNKNOWN: {unknown_count} vs 98 ({unknown_count-98:+,})')
print(f'  other: {other_count} vs 59 ({other_count-59:+,})')
print(f'  Untyped: {unknown_count + other_count} vs 157 ({(unknown_count + other_count)-157:+,})')
print(f'  Coverage: {coverage}% vs 96.4% ({coverage-96.4:+.1f}%)')
concept_count = types.get('concept', 0)
print(f'  concept: {concept_count} vs 210 ({concept_count-210:+,})')

print(f'\n⚖️ TARGET ASSESSMENT:')
unknown_status = '✅ SUCCESS' if unknown_count <= 5 else ('✅ GOOD' if unknown_count <= 50 else '❌ MISS')
other_status = '✅✅ PERFECT' if other_count == 0 else '❌ MISS'
ratio_status = '✅ SUCCESS' if ratio >= 1.6 else '⚠️ MISS'
coverage_status = '✅ SUCCESS' if coverage >= 98 else '⚠️ MISS'

print(f'  UNKNOWN: {unknown_count} (target: ≤5) - {unknown_status}')
print(f'  other: {other_count} (target: 0) - {other_status}')
print(f'  Ratio: {ratio} (target: ≥1.6) - {ratio_status}')
print(f'  Coverage: {coverage}% (target: ≥98%) - {coverage_status}')

print(f'\n🏆 OVERALL VERDICT:')
if unknown_count <= 5 and other_count == 0 and ratio >= 1.6 and coverage >= 98:
    print(f'  ✅✅✅ ALL TARGETS MET - ITERATION 8 SUCCESS!')
    print(f'  🎉 PRODUCTION READY - Branch 009 complete!')
elif unknown_count <= 50 and other_count <= 10 and ratio >= 1.6:
    print(f'  ✅ MAJOR SUCCESS - Minor refinement possible')
else:
    print(f'  ⚠️ Further refinement needed - analyze samples')
