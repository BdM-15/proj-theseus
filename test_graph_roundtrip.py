"""Test Graph roundtrip behavior"""
import networkx as nx
import os

print("=" * 70)
print("TEST: What happens when we write/read a simple Graph?")
print("=" * 70)

# Create a simple Graph (like LightRAG does)
g = nx.Graph()
g.add_node('A', entity_type='ORGANIZATION')
g.add_node('B', entity_type='PERSON')
g.add_edge('A', 'B', description='works for', weight=1.0)

print(f"\n1. Created graph: {type(g).__name__}")
print(f"   Nodes: {g.number_of_nodes()}")
print(f"   Edges: {g.number_of_edges()}")

# Write to GraphML (like LightRAG does)
test_file = 'test_roundtrip.graphml'
nx.write_graphml(g, test_file)
print(f"\n2. Wrote to GraphML: {test_file}")

# Read it back (like LightRAG does)
loaded = nx.read_graphml(test_file)
print(f"\n3. Loaded graph: {type(loaded).__name__}")
print(f"   Nodes: {loaded.number_of_nodes()}")
print(f"   Edges: {loaded.number_of_edges()}")

# Check the XML content
print(f"\n4. GraphML file content:")
with open(test_file, 'r') as f:
    for i, line in enumerate(f):
        if i < 5 or 'edgedefault' in line or '<graph' in line:
            print(f"   {line.rstrip()}")

# Test the iteration pattern that's failing
print(f"\n5. Testing edge iteration:")
print(f"   Using .edges():")
for edge in loaded.edges():
    print(f"      {edge}")
    
print(f"\n   Using .edges(data=True):")
for src, tgt, data in loaded.edges(data=True):
    print(f"      {src} -> {tgt}: {data}")

# Test if the indexing bug exists
print(f"\n6. Testing edge indexing (the bug):")
edges = list(loaded.edges())
if edges:
    edge = edges[0]
    print(f"   First edge: {edge}")
    try:
        data = loaded.edges[edge]
        print(f"   ✅ Indexing works: {data}")
    except ValueError as e:
        print(f"   ❌ ERROR: {e}")

# Clean up
os.remove(test_file)

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("If nx.Graph() -> write -> read -> MultiGraph happens,")
print("this is a NetworkX behavior change, NOT our ontology causing it!")
