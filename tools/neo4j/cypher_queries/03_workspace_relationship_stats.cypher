// =============================================================================
// Workspace: Relationship Statistics
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// =============================================================================
// Count by relationship type
MATCH (n:dla_tire_ont1)-[r]->(m:dla_tire_ont1)
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC;