// Demo ADAB ISS - Visualize knowledge graph for workspace 1_adab_iss_2025
// Run this query to see all entities and their relationships
MATCH (n:`1_adab_iss_2025`)
OPTIONAL MATCH (n)-[r]-(m:`1_adab_iss_2025`)
RETURN n, r, m