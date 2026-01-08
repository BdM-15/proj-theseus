// =============================================================================
// Workspace: Requirements Graph
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Shows requirement entities and their connections
// =============================================================================
MATCH (req:dla_tire_ont1 {entity_type: 'requirement'})
OPTIONAL MATCH (req)-[r]->(related:dla_tire_ont1)
RETURN req, r, related
LIMIT 50;