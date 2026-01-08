// =============================================================================
// GovCon Ontology: Capture Intelligence
// =============================================================================
// Win themes, discriminators, competitive analysis
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id = 'govcon_ontology_capture'
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;