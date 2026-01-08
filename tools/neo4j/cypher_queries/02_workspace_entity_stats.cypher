// =============================================================================
// Workspace: Entity Statistics
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// =============================================================================
// Count by entity type
MATCH (n:dla_tire_ont1)
RETURN n.entity_type AS entity_type, count(n) AS count
ORDER BY count DESC;