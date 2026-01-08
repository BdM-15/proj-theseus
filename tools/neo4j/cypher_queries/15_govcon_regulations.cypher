// =============================================================================
// GovCon Ontology: FAR/DFARS Regulations
// =============================================================================
// Federal Acquisition Regulation knowledge
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id = 'govcon_ontology_regulations'
OPTIONAL MATCH (n)-[r]->(m)
WHERE m.source_id = 'govcon_ontology_regulations'
RETURN n, r, m;