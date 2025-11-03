// Template: Delete Bad Relationships
// Purpose: Remove incorrect or spurious relationships from the knowledge graph
// WARNING: Deletion is permanent - always verify relationships before deleting!

// =============================================================================
// STEP 1: FIND SUSPICIOUS RELATIONSHIPS - Diagnostic queries
// =============================================================================

// Find relationships with low confidence scores
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.confidence IS NOT NULL
  AND r.confidence < 0.5
RETURN type(r) AS relationship_type,
       r.confidence AS confidence,
       a.entity_name AS from_entity,
       b.entity_name AS to_entity,
       r.reasoning AS reasoning
ORDER BY r.confidence ASC
LIMIT 25;

// Find duplicate relationships (same type between same entities)
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WITH a, b, type(r) AS rel_type, count(r) AS rel_count
WHERE rel_count > 1
MATCH (a)-[r]->(b)
WHERE type(r) = rel_type
RETURN a.entity_name AS from_entity,
       rel_type AS relationship,
       b.entity_name AS to_entity,
       rel_count AS duplicate_count,
       collect(r.reasoning) AS reasons
ORDER BY rel_count DESC;

// Find relationships with empty or null reasoning
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.reasoning IS NULL OR trim(r.reasoning) = ''
RETURN type(r) AS relationship_type,
       a.entity_name AS from_entity,
       b.entity_name AS to_entity,
       r.confidence AS confidence
LIMIT 25;

// Find relationships that violate ontology rules (e.g., submission_instruction -> requirement)
MATCH (a:`{WORKSPACE}`)-[r:GUIDES]->(b:`{WORKSPACE}`)
WHERE a.entity_type <> 'submission_instruction'
   OR b.entity_type <> 'evaluation_factor'
RETURN a.entity_name AS from_entity,
       a.entity_type AS from_type,
       type(r) AS relationship,
       b.entity_name AS to_entity,
       b.entity_type AS to_type,
       'Violates ontology: GUIDES should be submission_instruction -> evaluation_factor' AS issue;

// Find self-referencing relationships (entity pointing to itself)
MATCH (n:`{WORKSPACE}`)-[r]->(n)
RETURN n.entity_name AS entity,
       type(r) AS relationship,
       'Self-referencing relationship' AS issue;

// =============================================================================
// STEP 2: DELETE SINGLE RELATIONSHIP
// =============================================================================

// Template: Delete one specific relationship
MATCH (a:`{WORKSPACE}` {entity_name: 'FROM_ENTITY'})-[r:RELATIONSHIP_TYPE]->(b:`{WORKSPACE}` {entity_name: 'TO_ENTITY'})
// OPTIONAL: Add additional filters for precision
WHERE r.confidence < 0.5  // Example filter
DELETE r
RETURN 'Deleted relationship' AS status,
       a.entity_name AS from_entity,
       type(r) AS relationship_type,
       b.entity_name AS to_entity;

// =============================================================================
// EXAMPLE: Delete bad relationships in MCPP RFP
// =============================================================================

// Example 1: Delete low-confidence GUIDES relationship
MATCH (a:`mcpp_drfp_2025` {entity_name: 'Section L.5: Cost Proposal'})-[r:GUIDES]->(b:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
WHERE r.confidence < 0.4
DELETE r
RETURN 'Deleted low-confidence GUIDES relationship' AS status;

// Example 2: Delete self-referencing relationship
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Section C.6'})-[r:CHILD_OF]->(n)
DELETE r
RETURN 'Deleted self-referencing CHILD_OF relationship' AS status;

// Example 3: Delete incorrect EVALUATED_BY relationship
MATCH (a:`mcpp_drfp_2025` {entity_name: 'Concept: Agile Methodology'})-[r:EVALUATED_BY]->(b:`mcpp_drfp_2025` {entity_name: 'Factor 2: Past Performance'})
DELETE r
RETURN 'Deleted incorrect EVALUATED_BY relationship (concepts are not evaluated)' AS status;

// =============================================================================
// STEP 3: DELETE RELATIONSHIPS BY PATTERN
// =============================================================================

// Delete all relationships with confidence below threshold
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.confidence IS NOT NULL
  AND r.confidence < 0.3
DELETE r
RETURN 'Deleted low-confidence relationships' AS status,
       count(r) AS deleted_count;

// Delete all duplicate relationships (keep one, delete rest)
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WITH a, b, type(r) AS rel_type, collect(r) AS rels
WHERE size(rels) > 1
FOREACH (rel IN tail(rels) | DELETE rel)  // Keep first, delete rest
RETURN 'Deleted duplicate relationships' AS status,
       count(rels) - 1 AS deleted_per_pair;

// Delete all relationships with empty reasoning
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.reasoning IS NULL OR trim(r.reasoning) = ''
DELETE r
RETURN 'Deleted relationships with empty reasoning' AS status,
       count(r) AS deleted_count;

// Delete all self-referencing relationships
MATCH (n:`{WORKSPACE}`)-[r]->(n)
DELETE r
RETURN 'Deleted self-referencing relationships' AS status,
       count(r) AS deleted_count;

// =============================================================================
// STEP 4: DELETE RELATIONSHIPS BY TYPE
// =============================================================================

// Template: Delete all relationships of a specific type between entity types
MATCH (a:`{WORKSPACE}`)-[r:RELATIONSHIP_TYPE]->(b:`{WORKSPACE}`)
WHERE a.entity_type = 'ENTITY_TYPE_A'
  AND b.entity_type = 'ENTITY_TYPE_B'
DELETE r
RETURN 'Deleted relationships' AS status,
       count(r) AS deleted_count;

// Example: Delete all GUIDES relationships where source is not submission_instruction
MATCH (a:`mcpp_drfp_2025`)-[r:GUIDES]->(b:`mcpp_drfp_2025`)
WHERE a.entity_type <> 'submission_instruction'
DELETE r
RETURN 'Deleted invalid GUIDES relationships' AS status,
       count(r) AS deleted_count;

// Example: Delete all EVALUATED_BY relationships from concepts (concepts aren't evaluated)
MATCH (a:`mcpp_drfp_2025`)-[r:EVALUATED_BY]->(b:`mcpp_drfp_2025`)
WHERE a.entity_type = 'concept'
DELETE r
RETURN 'Deleted EVALUATED_BY relationships from concepts' AS status,
       count(r) AS deleted_count;

// =============================================================================
// STEP 5: BULK DELETE BY LIST
// =============================================================================

// Batch template: Delete multiple specific relationships
UNWIND [
  {from: 'ENTITY_1', to: 'ENTITY_2', type: 'RELATIONSHIP_TYPE_1'},
  {from: 'ENTITY_3', to: 'ENTITY_4', type: 'RELATIONSHIP_TYPE_2'},
  {from: 'ENTITY_5', to: 'ENTITY_6', type: 'RELATIONSHIP_TYPE_3'}
] AS deletion
MATCH (a:`{WORKSPACE}` {entity_name: deletion.from})-[r]->(b:`{WORKSPACE}` {entity_name: deletion.to})
WHERE type(r) = deletion.type
DELETE r
RETURN deletion.from AS from_entity,
       deletion.type AS relationship,
       deletion.to AS to_entity,
       'DELETED' AS status;

// =============================================================================
// STEP 6: VERIFY DELETION
// =============================================================================

// Verify relationship no longer exists
MATCH (a:`{WORKSPACE}` {entity_name: 'FROM_ENTITY'})-[r:RELATIONSHIP_TYPE]->(b:`{WORKSPACE}` {entity_name: 'TO_ENTITY'})
RETURN count(r) AS relationship_count,
       CASE WHEN count(r) = 0 THEN 'Successfully deleted' ELSE 'Still exists!' END AS status;

// Check remaining relationship counts after bulk deletion
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
RETURN type(r) AS relationship_type,
       count(r) AS count
ORDER BY count DESC;

// Count remaining low-confidence relationships
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.confidence IS NOT NULL
RETURN 
  count(CASE WHEN r.confidence < 0.3 THEN 1 END) AS very_low_confidence,
  count(CASE WHEN r.confidence >= 0.3 AND r.confidence < 0.5 THEN 1 END) AS low_confidence,
  count(CASE WHEN r.confidence >= 0.5 AND r.confidence < 0.7 THEN 1 END) AS medium_confidence,
  count(CASE WHEN r.confidence >= 0.7 THEN 1 END) AS high_confidence;

// =============================================================================
// STEP 7: SAFE DELETION ALTERNATIVE - Mark for review instead of deleting
// =============================================================================

// Instead of deleting, mark relationships for review
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.confidence IS NOT NULL
  AND r.confidence < 0.5
SET r.flagged_for_review = true,
    r.flagged_reason = 'Low confidence score',
    r.flagged_by = 'USERNAME',
    r.flagged_at = datetime()
RETURN 'Flagged relationships for review' AS status,
       count(r) AS flagged_count;

// Query flagged relationships for manual review
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.flagged_for_review = true
RETURN a.entity_name AS from_entity,
       type(r) AS relationship,
       b.entity_name AS to_entity,
       r.flagged_reason AS reason,
       r.confidence AS confidence,
       r.reasoning AS relationship_reasoning
ORDER BY r.confidence ASC
LIMIT 25;

// Delete relationships after manual review
MATCH (a:`{WORKSPACE}`)-[r]->(b:`{WORKSPACE}`)
WHERE r.flagged_for_review = true
  AND r.approved_for_deletion = true  // Set this property after manual review
DELETE r
RETURN 'Deleted reviewed relationships' AS status,
       count(r) AS deleted_count;

// =============================================================================
// NOTES
// =============================================================================
// - ALWAYS run STEP 1 (FIND) before STEP 2/3/4/5 (DELETE) to verify what will be deleted
// - Test deletions on small subset first
// - Document deletion reason in your workspace corrections file
// - Consider marking for review instead of immediate deletion (STEP 7)
// - Backup database before bulk deletions (see Neo4j backup docs)
// - Deletion is permanent - no undo without backup!
// - Use DETACH DELETE to also remove relationships when deleting nodes
// - Verify with STEP 6 after deletion
