// Template: Merge Duplicate Entities
// Purpose: Consolidate formatting variations (e.g., "Section C.6" vs "section c.6")
// WARNING: This operation is destructive - always backup or test in development first!

// =============================================================================
// STEP 1: FIND DUPLICATES - Identify potential duplicates
// =============================================================================

// Find entities with similar names (case-insensitive, normalized whitespace)
MATCH (n:`{WORKSPACE}`)
WITH n.entity_type AS type,
     trim(toLower(n.entity_name)) AS normalized_name,
     collect(n) AS entities
WHERE size(entities) > 1
RETURN type,
       normalized_name,
       size(entities) AS duplicate_count,
       [e IN entities | e.entity_name] AS variants
ORDER BY duplicate_count DESC, type;

// Find entities with exact name match but different cases
MATCH (n1:`{WORKSPACE}`), (n2:`{WORKSPACE}`)
WHERE id(n1) < id(n2)
  AND n1.entity_type = n2.entity_type
  AND toLower(n1.entity_name) = toLower(n2.entity_name)
  AND n1.entity_name <> n2.entity_name
RETURN n1.entity_type AS type,
       n1.entity_name AS variant1,
       n2.entity_name AS variant2,
       n1.description AS desc1,
       n2.description AS desc2;

// =============================================================================
// STEP 2: MERGE ENTITIES - Consolidate duplicates (USE WITH CAUTION!)
// =============================================================================

// Template: Merge two entities (keep primary, delete duplicate)
// Step 2a: Redirect all relationships from duplicate to primary
MATCH (duplicate:`{WORKSPACE}` {entity_name: 'DUPLICATE_NAME'})
MATCH (primary:`{WORKSPACE}` {entity_name: 'PRIMARY_NAME'})
MATCH (duplicate)-[r]->(other)
WHERE NOT (primary)-[]->(other)
CREATE (primary)-[r2:SAME_TYPE_AS_R]->(other)
SET r2 = properties(r)
DELETE r
RETURN 'Redirected outgoing relationships' AS status, count(r2) AS count;

// Step 2b: Redirect all incoming relationships from duplicate to primary
MATCH (duplicate:`{WORKSPACE}` {entity_name: 'DUPLICATE_NAME'})
MATCH (primary:`{WORKSPACE}` {entity_name: 'PRIMARY_NAME'})
MATCH (other)-[r]->(duplicate)
WHERE NOT (other)-[]->(primary)
CREATE (other)-[r2:SAME_TYPE_AS_R]->(primary)
SET r2 = properties(r)
DELETE r
RETURN 'Redirected incoming relationships' AS status, count(r2) AS count;

// Step 2c: Delete duplicate node (only after relationships redirected!)
MATCH (duplicate:`{WORKSPACE}` {entity_name: 'DUPLICATE_NAME'})
DETACH DELETE duplicate
RETURN 'Deleted duplicate' AS status;

// =============================================================================
// EXAMPLE: Merge "section c.6" into "Section C.6"
// =============================================================================

// Step 1: Verify entities exist
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_name IN ['section c.6', 'Section C.6']
RETURN n.entity_name, n.entity_type, n.description;

// Step 2: Redirect outgoing relationships
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
MATCH (primary:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
MATCH (duplicate)-[r]->(other)
WHERE NOT (primary)-[]->(other)
CREATE (primary)-[r2:SAME_TYPE]->(other)
SET r2 = properties(r),
    r2.merged_from = 'section c.6',
    r2.merged_at = datetime()
DELETE r;

// Step 3: Redirect incoming relationships
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
MATCH (primary:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
MATCH (other)-[r]->(duplicate)
WHERE NOT (other)-[]->(primary)
CREATE (other)-[r2:SAME_TYPE]->(primary)
SET r2 = properties(r),
    r2.merged_from = 'section c.6',
    r2.merged_at = datetime()
DELETE r;

// Step 4: Delete duplicate
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
DETACH DELETE duplicate;

// Step 5: Verify merge successful
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
OPTIONAL MATCH (n)-[r]-()
RETURN n.entity_name, count(r) AS relationship_count;

// =============================================================================
// SAFER ALTERNATIVE: Use MERGE to consolidate (doesn't delete, just redirects)
// =============================================================================

// Safe merge: Consolidate relationships without deleting nodes
MATCH (n1:`{WORKSPACE}` {entity_name: 'VARIANT_1'})
MATCH (n2:`{WORKSPACE}` {entity_name: 'VARIANT_2'})
MATCH (n1)-[r]->(other)
MERGE (n2)-[r2:SAME_TYPE_AS_R]->(other)
  ON CREATE SET r2 = properties(r),
                r2.consolidated_from = n1.entity_name,
                r2.consolidated_at = datetime()
RETURN 'Consolidated relationships' AS status, count(r2) AS count;

// Then manually review before deleting duplicates

// =============================================================================
// BULK MERGE - Consolidate multiple duplicates at once
// =============================================================================

// Batch template: Merge multiple duplicates (execute with caution!)
UNWIND [
  {duplicate: 'DUPLICATE_1', primary: 'PRIMARY_1'},
  {duplicate: 'DUPLICATE_2', primary: 'PRIMARY_2'},
  {duplicate: 'DUPLICATE_3', primary: 'PRIMARY_3'}
] AS merge_pair
MATCH (duplicate:`{WORKSPACE}` {entity_name: merge_pair.duplicate})
MATCH (primary:`{WORKSPACE}` {entity_name: merge_pair.primary})
// Redirect all relationships
OPTIONAL MATCH (duplicate)-[r_out]->(other_out)
FOREACH (_ IN CASE WHEN r_out IS NOT NULL THEN [1] ELSE [] END |
  CREATE (primary)-[:SAME_TYPE]->(other_out)
)
OPTIONAL MATCH (other_in)-[r_in]->(duplicate)
FOREACH (_ IN CASE WHEN r_in IS NOT NULL THEN [1] ELSE [] END |
  CREATE (other_in)-[:SAME_TYPE]->(primary)
)
// Delete duplicate
DETACH DELETE duplicate
RETURN merge_pair.duplicate AS merged_entity, 'SUCCESS' AS status;

// =============================================================================
// NOTES
// =============================================================================
// - ALWAYS run STEP 1 (FIND) to identify duplicates before merging
// - Test merge on one entity before bulk operations
// - Backup database before destructive operations (see Neo4j backup docs)
// - Use APOC procedures for advanced merging: apoc.refactor.mergeNodes()
// - Document merged entities in your workspace corrections file
// - Consider: Is this truly a duplicate or are there semantic differences?
