// =============================================================================
// GovCon Ontology: Evaluation Patterns
// =============================================================================
// Best value, LPTA, tradeoff patterns
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id = 'govcon_ontology_evaluation'
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;