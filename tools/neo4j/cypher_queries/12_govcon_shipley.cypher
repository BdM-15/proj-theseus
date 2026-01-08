// =============================================================================
// GovCon Ontology: Shipley Methodology Only
// =============================================================================
// Capture/proposal methodology concepts
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id = 'govcon_ontology_shipley'
OPTIONAL MATCH (n)-[r]->(m)
WHERE m.source_id = 'govcon_ontology_shipley'
RETURN n, r, m;