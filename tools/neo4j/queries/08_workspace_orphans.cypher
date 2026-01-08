// =============================================================================
// Workspace: Orphan Entities (No Relationships)
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Entities that might need relationship inference
// =============================================================================
MATCH (n:dla_tire_ont1)
WHERE NOT (n)-[]-()
RETURN n.entity_name AS orphan_entity, n.entity_type AS type
ORDER BY type, orphan_entity;