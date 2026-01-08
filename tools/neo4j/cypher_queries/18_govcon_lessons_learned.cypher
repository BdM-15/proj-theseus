// =============================================================================
// GovCon Ontology: Lessons Learned
// =============================================================================
// Common proposal pitfalls and best practices
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id = 'govcon_ontology_lessons'
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;