"""
Minimal monkey patch for LightRAG v1.4.9.3 MultiDiGraph edge access bug.

ISSUE: networkx_impl.py line 454 uses `subgraph.edges[edge]` which fails 
for MultiDiGraph when edge is a 2-tuple from iteration.

FIX: Replace with `.edges(data=True)` iteration to avoid indexing.

This is a targeted fix for ONE line of code in LightRAG's get_knowledge_graph method.
"""

import networkx as nx
from lightrag.types import KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge
from lightrag.utils import logger


async def fixed_get_knowledge_graph(
    self,
    node_label: str,
    max_depth: int = 3,
    max_nodes: int = None,
) -> KnowledgeGraph:
    """
    Fixed version of NetworkXStorage.get_knowledge_graph() that properly handles MultiDiGraph.
    
    Only change: Line 454 replacement
    OLD: edge_data = dict(subgraph.edges[edge])  # Fails for MultiDiGraph
    NEW: for source, target, edge_data in subgraph.edges(data=True):  # Works for all graph types
    """
    # Get max_nodes from global_config if not provided
    if max_nodes is None:
        max_nodes = self.global_config.get("max_graph_nodes", 1000)
    else:
        max_nodes = min(max_nodes, self.global_config.get("max_graph_nodes", 1000))

    graph = await self._get_graph()
    result = KnowledgeGraph()

    # Handle special case for "*" label
    if node_label == "*":
        degrees = dict(graph.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_nodes) > max_nodes:
            result.is_truncated = True
            logger.info(
                f"[{self.workspace}] Graph truncated: {len(sorted_nodes)} nodes found, limited to {max_nodes}"
            )
        
        limited_nodes = [node for node, _ in sorted_nodes[:max_nodes]]
        subgraph = graph.subgraph(limited_nodes)
    else:
        if node_label not in graph:
            logger.warning(
                f"[{self.workspace}] Node {node_label} not found in the graph"
            )
            return KnowledgeGraph()

        # BFS with degree-based prioritization (unchanged from original)
        bfs_nodes = []
        visited = set()
        queue = [(node_label, 0, graph.degree(node_label))]
        has_unexplored_neighbors = False

        while queue and len(bfs_nodes) < max_nodes:
            current_depth = queue[0][1]
            current_level_nodes = []
            
            while queue and queue[0][1] == current_depth:
                current_level_nodes.append(queue.pop(0))
            
            current_level_nodes.sort(key=lambda x: x[2], reverse=True)
            
            for current_node, depth, degree in current_level_nodes:
                if current_node not in visited:
                    bfs_nodes.append(current_node)
                    visited.add(current_node)
                    
                    if depth < max_depth:
                        for neighbor in graph.neighbors(current_node):
                            if neighbor not in visited:
                                neighbor_degree = graph.degree(neighbor)
                                queue.append((neighbor, depth + 1, neighbor_degree))
                    else:
                        neighbors = list(graph.neighbors(current_node))
                        unvisited_neighbors = [n for n in neighbors if n not in visited]
                        if unvisited_neighbors:
                            has_unexplored_neighbors = True
                
                if len(bfs_nodes) >= max_nodes:
                    break

        if (queue and len(bfs_nodes) >= max_nodes) or has_unexplored_neighbors:
            if len(bfs_nodes) >= max_nodes:
                result.is_truncated = True
                logger.info(
                    f"[{self.workspace}] Graph truncated: max_nodes limit {max_nodes} reached"
                )
            else:
                logger.info(
                    f"[{self.workspace}] Graph truncated: found {len(bfs_nodes)} nodes within max_depth {max_depth}"
                )

        subgraph = graph.subgraph(bfs_nodes)

    # Add nodes to result (unchanged)
    seen_nodes = set()
    seen_edges = set()
    
    for node in subgraph.nodes():
        if str(node) in seen_nodes:
            continue
        node_data = dict(subgraph.nodes[node])
        
        labels = []
        if "entity_type" in node_data:
            if isinstance(node_data["entity_type"], list):
                labels.extend(node_data["entity_type"])
            else:
                labels.append(node_data["entity_type"])
        
        node_properties = {k: v for k, v in node_data.items()}
        result.nodes.append(
            KnowledgeGraphNode(
                id=str(node), labels=[str(node)], properties=node_properties
            )
        )
        seen_nodes.add(str(node))

    # ═══════════════════════════════════════════════════════════════════════
    # FIX: Use .edges(data=True) iteration instead of edge indexing
    # ═══════════════════════════════════════════════════════════════════════
    for source, target, edge_data in subgraph.edges(data=True):
        # Ensure unique edge_id for undirected graph
        if str(source) > str(target):
            source, target = target, source
        edge_id = f"{source}-{target}"
        if edge_id in seen_edges:
            continue

        # edge_data is already a dict from .edges(data=True)
        # No need for: edge_data = dict(subgraph.edges[edge])  # ❌ OLD LINE 454

        result.edges.append(
            KnowledgeGraphEdge(
                id=edge_id,
                type="DIRECTED",
                source=str(source),
                target=str(target),
                properties=edge_data,
            )
        )
        seen_edges.add(edge_id)

    logger.info(
        f"[{self.workspace}] Subgraph query successful | Node count: {len(result.nodes)} | Edge count: {len(result.edges)}"
    )
    
    return result


def apply_multidigraph_fix():
    """
    Apply minimal monkey patch to fix MultiDiGraph edge access in LightRAG.
    
    This replaces ONLY the get_knowledge_graph method in NetworkXStorage.
    """
    from lightrag.kg.networkx_impl import NetworkXStorage
    
    # Store original method for potential rollback
    if not hasattr(NetworkXStorage, '_original_get_knowledge_graph'):
        NetworkXStorage._original_get_knowledge_graph = NetworkXStorage.get_knowledge_graph
    
    # Apply fix
    NetworkXStorage.get_knowledge_graph = fixed_get_knowledge_graph
    
    logger.info("Applied MultiDiGraph fix to LightRAG NetworkXStorage.get_knowledge_graph()")
