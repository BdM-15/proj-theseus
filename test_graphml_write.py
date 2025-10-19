"""Test what NetworkX writes to GraphML for different graph types"""
import networkx as nx

# Test 1: Simple Graph (undirected)
print("=" * 60)
print("TEST 1: nx.Graph() - Simple undirected graph")
print("=" * 60)
g = nx.Graph()
g.add_node('A', test='value')
g.add_edge('A', 'B', weight=1.0)
nx.write_graphml(g, 'test_graph.graphml')

with open('test_graph.graphml', 'r') as f:
    for line in f:
        if 'edgedefault' in line or '<graph' in line:
            print(f"Graph line: {line.strip()}")

# Test 2: DiGraph (directed)
print("\n" + "=" * 60)
print("TEST 2: nx.DiGraph() - Simple directed graph")
print("=" * 60)
dg = nx.DiGraph()
dg.add_node('A', test='value')
dg.add_edge('A', 'B', weight=1.0)
nx.write_graphml(dg, 'test_digraph.graphml')

with open('test_digraph.graphml', 'r') as f:
    for line in f:
        if 'edgedefault' in line or '<graph' in line:
            print(f"DiGraph line: {line.strip()}")

# Test 3: Load and check type
print("\n" + "=" * 60)
print("TEST 3: Loading back from GraphML")
print("=" * 60)
loaded_g = nx.read_graphml('test_graph.graphml')
loaded_dg = nx.read_graphml('test_digraph.graphml')
print(f"nx.Graph() -> write -> read -> {type(loaded_g).__name__}")
print(f"nx.DiGraph() -> write -> read -> {type(loaded_dg).__name__}")

# Test 4: Check our actual graph
print("\n" + "=" * 60)
print("TEST 4: Our actual graph file")
print("=" * 60)
actual = nx.read_graphml('./rag_storage/graph_chunk_entity_relation.graphml')
print(f"Loaded type: {type(actual).__name__}")
print(f"Nodes: {actual.number_of_nodes()}")
print(f"Edges: {actual.number_of_edges()}")

# Check if any parallel edges exist (which would require MultiGraph)
print("\nChecking for parallel edges (multiple edges between same node pair)...")
edge_counts = {}
for u, v in actual.edges():
    key = tuple(sorted([u, v]))  # Undirected, so normalize
    edge_counts[key] = edge_counts.get(key, 0) + 1

parallel_edges = {k: v for k, v in edge_counts.items() if v > 1}
if parallel_edges:
    print(f"❌ Found {len(parallel_edges)} node pairs with parallel edges:")
    for (u, v), count in list(parallel_edges.items())[:5]:
        print(f"  {u} <-> {v}: {count} edges")
else:
    print("✅ No parallel edges found - simple Graph should work!")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
if not parallel_edges:
    print("🚨 CRITICAL: We don't need MultiGraph!")
    print("   Our data has NO parallel edges.")
    print("   NetworkX is loading as MultiGraph because of 'edgedefault=undirected'")
    print("   but we could use a simple Graph() instead!")
