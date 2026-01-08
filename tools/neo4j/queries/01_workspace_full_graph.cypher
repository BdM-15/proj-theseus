// =============================================================================
// Workspace: Full Graph Visualization
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// To list all workspaces: CALL db.labels() YIELD label RETURN label ORDER BY label;
// =============================================================================
// Full workspace graph - all entities and relationships
MATCH (n:dla_tire_ont1)
OPTIONAL MATCH (n)-[r]->(m:dla_tire_ont1)
RETURN n, r, m
LIMIT 200;