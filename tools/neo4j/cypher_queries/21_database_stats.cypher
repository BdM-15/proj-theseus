// =============================================================================
// Utility: Database Statistics
// =============================================================================
// Overall Neo4j database statistics
// =============================================================================

// Total nodes
MATCH (n) RETURN count(n) AS total_nodes;

// Total relationships
MATCH ()-[r]->() RETURN count(r) AS total_relationships;

// Nodes per label
CALL db.labels() YIELD label
 CALL {
   WITH label
   MATCH (n) WHERE label IN labels(n)
   RETURN count(n) AS count
 }
 RETURN label, count
 ORDER BY count DESC;