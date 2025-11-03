// Template: Find Orphaned Nodes
// Purpose: Identify entities with no relationships (potential data quality issues)
// Usage: Replace {WORKSPACE} with your workspace label (e.g., mcpp_drfp_2025)

// =============================================================================
// DIAGNOSTIC QUERIES - Find orphaned entities by type
// =============================================================================

// Count orphaned nodes by entity type
MATCH (n:`{WORKSPACE}`)
WHERE NOT (n)-[]-()
RETURN n.entity_type AS type, 
       count(n) AS orphaned_count
ORDER BY orphaned_count DESC;

// List all orphaned submission instructions (Section L items missing Section M links)
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'submission_instruction'
  AND NOT (n)-[:GUIDES]->()
RETURN n.entity_name AS instruction,
       n.description AS details
ORDER BY n.entity_name;

// List all orphaned evaluation factors (Section M items missing Section L links)
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'evaluation_factor'
  AND NOT (n)<-[:GUIDES]-()
RETURN n.entity_name AS factor,
       n.description AS details
ORDER BY n.entity_name;

// List all orphaned requirements (missing evaluation factor links)
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'requirement'
  AND NOT (n)-[:EVALUATED_BY]->()
RETURN n.entity_name AS requirement,
       n.description AS details
LIMIT 25;

// List all orphaned documents (missing parent section links)
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'document'
  AND NOT (n)-[:CHILD_OF]->()
RETURN n.entity_name AS document,
       n.description AS details
LIMIT 25;

// =============================================================================
// SUMMARY - Overall graph health metrics
// =============================================================================

// Graph health summary
MATCH (n:`{WORKSPACE}`)
OPTIONAL MATCH (n)-[r]-()
WITH n.entity_type AS type,
     count(DISTINCT n) AS total_entities,
     count(DISTINCT CASE WHEN r IS NULL THEN n END) AS orphaned,
     count(DISTINCT r) AS total_relationships
RETURN type,
       total_entities,
       orphaned,
       total_relationships,
       round(100.0 * orphaned / total_entities, 1) AS orphaned_pct
ORDER BY orphaned_pct DESC, total_entities DESC;

// =============================================================================
// NOTES
// =============================================================================
// - Orphaned nodes are not necessarily errors (some entities may be standalone)
// - Focus on high-value entity types first: submission_instruction, evaluation_factor, requirement
// - Use the results to populate correction scripts (templates 02-06)
