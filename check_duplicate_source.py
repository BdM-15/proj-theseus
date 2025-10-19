"""
Check WHERE the duplicate edges are coming from
"""
import xml.etree.ElementTree as ET

tree = ET.parse('./rag_storage/graph_chunk_entity_relation.graphml')
root = tree.getroot()
ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}

# Get all edges
edges = root.findall('.//g:edge', ns)

# Group by source-target pair
edge_pairs = {}
for edge in edges:
    src = edge.get('source')
    tgt = edge.get('target')
    key = tuple(sorted([src, tgt]))
    
    if key not in edge_pairs:
        edge_pairs[key] = []
    
    # Get the source_id (which chunks created this edge)
    source_id = None
    for data in edge.findall('.//g:data', ns):
        if data.get('key') == 'd9':  # d9 is source_id
            source_id = data.text
            break
    
    edge_pairs[key].append({
        'id': edge.get('id'),
        'source_id': source_id
    })

# Find duplicates
print("=" * 70)
print("Analyzing duplicate edges")
print("=" * 70)

duplicates = {k: v for k, v in edge_pairs.items() if len(v) > 1}
print(f"\nTotal edge pairs with duplicates: {len(duplicates)}")

print("\n" + "=" * 70)
print("Sample duplicate edges:")
print("=" * 70)

for i, ((src, tgt), edges_list) in enumerate(list(duplicates.items())[:5]):
    print(f"\n{i+1}. {src} <-> {tgt}")
    print(f"   Number of duplicate edges: {len(edges_list)}")
    for j, edge_info in enumerate(edges_list):
        source_id = edge_info['source_id']
        if source_id:
            chunks = source_id.split('<|>')
            print(f"   Edge {j+1}: Created by {len(chunks)} chunks")
            if 'semantic_post_processing' in source_id:
                print(f"           ⚠️ FROM PHASE 6 POST-PROCESSING")
            else:
                print(f"           ✓ From LightRAG extraction")
        else:
            print(f"   Edge {j+1}: No source_id")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("If duplicates are from different chunks during LightRAG extraction,")
print("this is a LIGHTRAG BUG - it should merge them in nx.Graph()")
print("\nIf duplicates are from Phase 6, that's OUR bug to fix.")
