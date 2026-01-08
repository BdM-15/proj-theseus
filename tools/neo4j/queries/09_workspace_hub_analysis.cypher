// =============================================================================
// Workspace: Most Connected Entities (Hub Analysis)
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Key entities with many relationships
// =============================================================================
MATCH (n:dla_tire_ont1)
OPTIONAL MATCH (n)-[r]-()
WITH n, count(r) AS connections
WHERE connections > 3
RETURN n.entity_name AS entity, n.entity_type AS type, connections
ORDER BY connections DESC
LIMIT 20;