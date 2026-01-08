// =============================================================================
// GovCon Ontology: Color Team Reviews
// =============================================================================
// Pink, Red, Gold team review concepts
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE
  n.source_id = 'govcon_ontology_shipley' AND
  (n.entity_name CONTAINS 'Team' OR n.description CONTAINS 'color team')
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;