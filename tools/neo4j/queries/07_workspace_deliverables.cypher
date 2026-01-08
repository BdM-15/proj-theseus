// =============================================================================
// Workspace: Deliverables Traceability
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Shows deliverables and their source connections
// =============================================================================
MATCH (del:dla_tire_ont1 {entity_type: 'deliverable'})
OPTIONAL MATCH (source)-[r]->(del)
OPTIONAL MATCH (del)-[r2]->(target)
RETURN source, r, del, r2, target
LIMIT 75;