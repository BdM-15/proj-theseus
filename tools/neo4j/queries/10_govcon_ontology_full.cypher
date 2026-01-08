// =============================================================================
// GovCon Ontology: Full Graph (Shipley, FAR, Evaluation, etc.)
// =============================================================================
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id STARTS WITH 'govcon_ontology'
OPTIONAL MATCH (n)-[r]->(m)
WHERE m.source_id STARTS WITH 'govcon_ontology'
RETURN n, r, m;