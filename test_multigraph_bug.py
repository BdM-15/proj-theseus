"""Test if MultiGraph has the same edge indexing bug as MultiDiGraph"""
import networkx as nx

# Test with regular Graph (should work)
print("=" * 60)
print("TEST 1: Regular Graph (undirected)")
print("=" * 60)
g = nx.Graph()
g.add_edge('A', 'B', weight=1.0)
g.add_edge('B', 'C', weight=2.0)
edges = list(g.edges())
print(f"Edge iteration: {edges}")
edge = edges[0]
print(f"First edge: {edge} (type: {type(edge)}, len: {len(edge)})")
try:
    data = g.edges[edge]
    print(f"✅ Edge data via indexing works: {data}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test with MultiGraph (undirected multi-edge)
print("\n" + "=" * 60)
print("TEST 2: MultiGraph (undirected, multi-edge)")
print("=" * 60)
mg = nx.MultiGraph()
mg.add_edge('A', 'B', weight=1.0)
mg.add_edge('B', 'C', weight=2.0)
edges = list(mg.edges())
print(f"Edge iteration: {edges}")
edge = edges[0]
print(f"First edge: {edge} (type: {type(edge)}, len: {len(edge)})")
try:
    data = mg.edges[edge]
    print(f"Edge data via indexing: {data}")
    print(f"Data type: {type(data)}")
    # Try to convert to dict
    data_dict = dict(data)
    print(f"✅ dict(data) works: {data_dict}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test with MultiDiGraph (directed multi-edge)  
print("\n" + "=" * 60)
print("TEST 3: MultiDiGraph (directed, multi-edge)")
print("=" * 60)
mdg = nx.MultiDiGraph()
mdg.add_edge('A', 'B', weight=1.0)
mdg.add_edge('B', 'C', weight=2.0)
edges = list(mdg.edges())
print(f"Edge iteration: {edges}")
edge = edges[0]
print(f"First edge: {edge} (type: {type(edge)}, len: {len(edge)})")
try:
    data = mdg.edges[edge]
    print(f"Edge data via indexing: {data}")
    print(f"Data type: {type(data)}")
    # Try to convert to dict
    data_dict = dict(data)
    print(f"✅ dict(data) works: {data_dict}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test the CORRECT way with .edges(data=True)
print("\n" + "=" * 60)
print("TEST 4: Correct iteration with .edges(data=True)")
print("=" * 60)
for graph_name, graph in [("Graph", g), ("MultiGraph", mg), ("MultiDiGraph", mdg)]:
    print(f"\n{graph_name}:")
    for src, tgt, data in graph.edges(data=True):
        print(f"  {src} -> {tgt}: {data}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("The .edges(data=True) pattern works correctly for ALL graph types.")
print("The .edges[edge] indexing pattern behavior depends on graph type.")
