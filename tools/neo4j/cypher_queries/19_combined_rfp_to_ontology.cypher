// =============================================================================
// Combined: RFP Entities Connected to Ontology
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Shows how extracted RFP content connects to methodology knowledge
// =============================================================================
MATCH (rfp:dla_tire_ont1)-[r]->(ontology)
WHERE ontology.source_id STARTS WITH 'govcon_ontology'
RETURN rfp, r, ontology
LIMIT 100;