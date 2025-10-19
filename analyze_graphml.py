"""Check if our GraphML file actually has parallel edges in the XML"""
import xml.etree.ElementTree as ET
import networkx as nx

print("=" * 70)
print("Analyzing our actual GraphML file")
print("=" * 70)

# Parse the XML directly
tree = ET.parse('./rag_storage/graph_chunk_entity_relation.graphml')
root = tree.getroot()
ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}

# Count edges in XML
edges = root.findall('.//g:edge', ns)
print(f"\n1. Total <edge> elements in XML: {len(edges)}")

# Check for duplicate source-target pairs
edge_pairs = {}
for edge in edges:
    src = edge.get('source')
    tgt = edge.get('target')
    # Normalize for undirected graph
    key = tuple(sorted([src, tgt]))
    if key not in edge_pairs:
        edge_pairs[key] = []
    edge_pairs[key].append(edge)

duplicates = {k: v for k, v in edge_pairs.items() if len(v) > 1}
print(f"\n2. Node pairs with multiple <edge> elements: {len(duplicates)}")

if duplicates:
    print(f"\n3. Examples of parallel edges in XML:")
    for i, ((src, tgt), edge_list) in enumerate(list(duplicates.items())[:5]):
        print(f"\n   Pair #{i+1}: {src} <-> {tgt} ({len(edge_list)} edges)")
        for j, edge in enumerate(edge_list[:2]):
            # Get edge data
            data_elements = edge.findall('.//g:data', ns)
            keywords = None
            for data_elem in data_elements:
                if 'keywords' in data_elem.get('key', ''):
                    keywords = data_elem.text
            print(f"      Edge {j+1}: keywords='{keywords[:60] if keywords else 'N/A'}...'")

# Load with NetworkX and compare
print(f"\n" + "=" * 70)
g = nx.read_graphml('./rag_storage/graph_chunk_entity_relation.graphml')
print(f"4. NetworkX loaded as: {type(g).__name__}")
print(f"   Nodes: {g.number_of_nodes()}")
print(f"   Edges: {g.number_of_edges()}")
print(f"   XML edges: {len(edges)}")

print(f"\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
if len(duplicates) > 0:
    print(f"✅ Parallel edges EXIST in the XML ({len(duplicates)} pairs)")
    print(f"✅ MultiGraph is CORRECT for this data")
    print(f"\n🔍 ROOT CAUSE:")
    print(f"   - Something is writing duplicate edges to GraphML")
    print(f"   - This forces NetworkX to use MultiGraph on read")
    print(f"   - The .edges[edge] pattern doesn't work with MultiGraph")
else:
    print(f"❌ NO parallel edges in XML")
    print(f"   NetworkX shouldn't be using MultiGraph!")
