// Demo MCPP DRFP - Visualize knowledge graph for workspace 2_mcpp_drfp_2025
// Run this query to see all entities and their relationships
MATCH (n:`2_mcpp_drfp_2025`)
OPTIONAL MATCH (n)-[r]->(m:`2_mcpp_drfp_2025`)
RETURN n, r, m