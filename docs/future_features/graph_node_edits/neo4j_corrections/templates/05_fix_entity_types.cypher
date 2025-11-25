// Template: Fix Entity Type Misclassifications
// Purpose: Correct entities that were assigned the wrong entity_type during extraction
// Usage: Replace {WORKSPACE} and entity names, specify correct entity type

// =============================================================================
// STEP 1: FIND MISCLASSIFIED ENTITIES - Diagnostic queries
// =============================================================================

// Find entities with UNKNOWN type
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'UNKNOWN' OR n.entity_type IS NULL
RETURN n.entity_name AS entity,
       n.entity_type AS current_type,
       n.description AS details
ORDER BY n.entity_name
LIMIT 25;

// Find entities that might be misclassified based on name patterns
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_name CONTAINS 'Section L'
  AND n.entity_type <> 'submission_instruction'
RETURN n.entity_name AS entity,
       n.entity_type AS current_type,
       'Should be: submission_instruction' AS recommendation,
       n.description AS details
LIMIT 25;

// Find entities that might be requirements but classified as concepts
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'concept'
  AND (n.description CONTAINS 'shall' OR n.description CONTAINS 'must' OR n.description CONTAINS 'will')
RETURN n.entity_name AS entity,
       n.entity_type AS current_type,
       'Should be: requirement' AS recommendation,
       n.description AS details
LIMIT 25;

// Find evaluation factors misclassified as sections
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_name CONTAINS 'Factor'
  AND n.entity_type <> 'evaluation_factor'
RETURN n.entity_name AS entity,
       n.entity_type AS current_type,
       'Should be: evaluation_factor' AS recommendation,
       n.description AS details;

// =============================================================================
// STEP 2: FIX SINGLE ENTITY TYPE
// =============================================================================

// Template: Change entity_type for one entity
MATCH (n:`{WORKSPACE}` {entity_name: 'ENTITY_NAME'})
SET n.entity_type = 'NEW_ENTITY_TYPE',               // Options: requirement, evaluation_factor, submission_instruction, etc.
    n.old_entity_type = n.entity_type,               // Preserve old type for audit
    n.corrected_by = 'USERNAME',
    n.corrected_at = datetime(),
    n.correction_reason = 'REASON_FOR_CHANGE'
RETURN n.entity_name,
       n.old_entity_type AS was,
       n.entity_type AS now,
       n.correction_reason;

// =============================================================================
// EXAMPLE: Fix entity types in MCPP RFP
// =============================================================================

// Example 1: Fix UNKNOWN entity to requirement
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Cloud Infrastructure Requirements'})
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'requirement',
    n.corrected_by = 'analyst',
    n.corrected_at = datetime(),
    n.correction_reason = 'Entity describes mandatory system requirements (contains "shall" statements)'
RETURN n.entity_name, n.old_entity_type AS was, n.entity_type AS now;

// Example 2: Fix concept to evaluation_factor
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 3: Price Evaluation'})
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'evaluation_factor',
    n.corrected_by = 'analyst',
    n.corrected_at = datetime(),
    n.correction_reason = 'Entity is a Section M evaluation criterion, not a concept'
RETURN n.entity_name, n.old_entity_type AS was, n.entity_type AS now;

// Example 3: Fix section to submission_instruction
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Section L.7: Past Performance Submission'})
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'submission_instruction',
    n.corrected_by = 'analyst',
    n.corrected_at = datetime(),
    n.correction_reason = 'Section L items are submission instructions, not generic sections'
RETURN n.entity_name, n.old_entity_type AS was, n.entity_type AS now;

// =============================================================================
// STEP 3: BULK ENTITY TYPE CORRECTIONS
// =============================================================================

// Batch template: Fix multiple entity types at once
UNWIND [
  {name: 'ENTITY_1', new_type: 'requirement', reason: 'REASON_1'},
  {name: 'ENTITY_2', new_type: 'evaluation_factor', reason: 'REASON_2'},
  {name: 'ENTITY_3', new_type: 'submission_instruction', reason: 'REASON_3'}
] AS correction
MATCH (n:`{WORKSPACE}` {entity_name: correction.name})
SET n.old_entity_type = n.entity_type,
    n.entity_type = correction.new_type,
    n.corrected_by = 'USERNAME',
    n.corrected_at = datetime(),
    n.correction_reason = correction.reason
RETURN n.entity_name,
       n.old_entity_type AS was,
       n.entity_type AS now,
       n.correction_reason;

// =============================================================================
// STEP 4: PATTERN-BASED BULK CORRECTIONS
// =============================================================================

// Fix all entities with "Factor" in name to evaluation_factor
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_name CONTAINS 'Factor'
  AND n.entity_type <> 'evaluation_factor'
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'evaluation_factor',
    n.corrected_by = 'bulk_correction',
    n.corrected_at = datetime(),
    n.correction_reason = 'Name pattern match: contains "Factor"'
RETURN n.entity_name,
       n.old_entity_type AS was,
       n.entity_type AS now,
       count(*) AS entities_updated;

// Fix all entities with "Section L" in name to submission_instruction
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_name STARTS WITH 'Section L'
  AND n.entity_type <> 'submission_instruction'
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'submission_instruction',
    n.corrected_by = 'bulk_correction',
    n.corrected_at = datetime(),
    n.correction_reason = 'Name pattern match: starts with "Section L"'
RETURN n.entity_name,
       n.old_entity_type AS was,
       n.entity_type AS now,
       count(*) AS entities_updated;

// Fix all entities with "Section M" in name to evaluation_factor
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_name STARTS WITH 'Section M'
  AND n.entity_type <> 'evaluation_factor'
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'evaluation_factor',
    n.corrected_by = 'bulk_correction',
    n.corrected_at = datetime(),
    n.correction_reason = 'Name pattern match: starts with "Section M"'
RETURN n.entity_name,
       n.old_entity_type AS was,
       n.entity_type AS now,
       count(*) AS entities_updated;

// =============================================================================
// STEP 5: VERIFY CORRECTIONS
// =============================================================================

// Verify specific entity type correction
MATCH (n:`{WORKSPACE}` {entity_name: 'ENTITY_NAME'})
RETURN n.entity_name,
       n.old_entity_type AS previous_type,
       n.entity_type AS current_type,
       n.correction_reason,
       n.corrected_by,
       n.corrected_at;

// Count entities by type after corrections
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type IS NOT NULL
RETURN n.entity_type AS type,
       count(n) AS count
ORDER BY count DESC;

// Find remaining UNKNOWN entities
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'UNKNOWN' OR n.entity_type IS NULL
RETURN count(n) AS remaining_unknown,
       collect(n.entity_name)[..10] AS sample_entities;

// =============================================================================
// STEP 6: ROLLBACK (if needed)
// =============================================================================

// Rollback: Restore original entity types for entities corrected by specific user
MATCH (n:`{WORKSPACE}`)
WHERE n.corrected_by = 'USERNAME'
  AND n.old_entity_type IS NOT NULL
SET n.entity_type = n.old_entity_type
REMOVE n.old_entity_type, n.corrected_by, n.corrected_at, n.correction_reason
RETURN n.entity_name,
       n.entity_type AS restored_type,
       'Rollback successful' AS status;

// =============================================================================
// VALID ENTITY TYPES (Reference)
// =============================================================================
// - requirement: Technical, functional, performance, staffing requirements
// - evaluation_factor: Section M evaluation criteria
// - submission_instruction: Section L proposal submission requirements
// - section: Document sections (C, E, F, H, J, K, etc.)
// - document: Top-level document names (RFP, PWS, QASP, etc.)
// - contract_term: Pricing, payment, contract duration
// - deliverable: Work products, reports, software
// - concept: General ideas, methodologies, technologies
// - program_entity: Programs, systems, initiatives
// - agency: Government agencies, organizations
// - standard: Industry standards, regulations, compliance frameworks
// - technology: Specific technologies, tools, platforms
// - UNKNOWN: Entities that need classification

// =============================================================================
// NOTES
// =============================================================================
// - Always preserve old_entity_type for audit trail before changing
// - Document correction_reason for transparency
// - Test pattern-based corrections on small subset first
// - Use STEP 5 (VERIFY) after every correction
// - Rollback capability exists if corrections are incorrect (STEP 6)
// - Consider: Does the entity have relationships that validate its type?
