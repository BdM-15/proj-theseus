// =============================================================================
// GovCon Ontology: Module Breakdown
// =============================================================================
// Shows entity counts per knowledge module
// NOTE: Requires bootstrap! Run if empty:
//   python tools/bootstrap_ontology.py bootstrap <workspace_name>
// =============================================================================
MATCH (n)
WHERE n.source_id STARTS WITH 'govcon_ontology'
RETURN n.source_id AS knowledge_module, count(n) AS entity_count
ORDER BY entity_count DESC;