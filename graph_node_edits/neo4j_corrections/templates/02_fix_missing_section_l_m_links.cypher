// Template: Fix Missing Section L ↔ M Links
// Purpose: Create GUIDES relationships between submission instructions (Section L) and evaluation factors (Section M)
// Usage: Replace {WORKSPACE} with your workspace label, customize entity names and reasoning

// =============================================================================
// STEP 1: FIND POTENTIAL LINKS - Run this first to identify missing relationships
// =============================================================================

// Find submission instructions that might guide specific evaluation factors
MATCH (l:`{WORKSPACE}`), (m:`{WORKSPACE}`)
WHERE l.entity_type = 'submission_instruction'
  AND m.entity_type = 'evaluation_factor'
  AND NOT (l)-[:GUIDES]->(m)
  AND (
    // Case-insensitive keyword matching in descriptions
    toLower(l.description) CONTAINS toLower(m.entity_name)
    OR toLower(m.description) CONTAINS toLower(l.entity_name)
  )
RETURN l.entity_name AS section_l,
       m.entity_name AS section_m,
       l.description AS l_description,
       m.description AS m_description
LIMIT 50;

// =============================================================================
// STEP 2: CREATE RELATIONSHIP - Run after identifying correct pairs
// =============================================================================

// Template: Create single GUIDES relationship with metadata
MATCH (l:`{WORKSPACE}` {entity_name: 'INSTRUCTION_NAME'})
MATCH (m:`{WORKSPACE}` {entity_name: 'FACTOR_NAME'})
CREATE (l)-[r:GUIDES {
  confidence: 0.95,
  reasoning: 'EXPLAIN_WHY_THESE_ARE_RELATED',
  source: 'manual_correction',
  corrected_by: 'USERNAME',
  corrected_at: datetime()
}]->(m)
RETURN l.entity_name, type(r), m.entity_name, r.reasoning;

// =============================================================================
// EXAMPLE: Actual correction from MCPP RFP
// =============================================================================

// Example 1: Technical Proposal format guides Technical Approach evaluation
MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})
MATCH (m:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
CREATE (l)-[r:GUIDES {
  confidence: 0.98,
  reasoning: 'Section L.6 specifies the required format and content structure for the Technical Proposal, which is evaluated under Factor 1 (Technical Approach). The submission instructions directly guide how responses are structured for this evaluation criterion.',
  source: 'manual_correction',
  corrected_by: 'analyst',
  corrected_at: datetime()
}]->(m)
RETURN l.entity_name, type(r), m.entity_name, r.reasoning;

// Example 2: Past Performance references guide Past Performance evaluation
MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.8: Past Performance'})
MATCH (m:`mcpp_drfp_2025` {entity_name: 'Factor 2: Past Performance'})
CREATE (l)-[r:GUIDES {
  confidence: 0.99,
  reasoning: 'Section L.8 defines the required past performance submissions (contracts, questionnaires, narratives) that are directly evaluated under Factor 2 (Past Performance). Clear 1:1 mapping between submission instruction and evaluation criterion.',
  source: 'manual_correction',
  corrected_by: 'analyst',
  corrected_at: datetime()
}]->(m)
RETURN l.entity_name, type(r), m.entity_name, r.reasoning;

// =============================================================================
// STEP 3: VERIFY RELATIONSHIP - Run after creating relationships
// =============================================================================

// Verify the new relationship exists
MATCH (l:`{WORKSPACE}` {entity_name: 'INSTRUCTION_NAME'})-[r:GUIDES]->(m:`{WORKSPACE}` {entity_name: 'FACTOR_NAME'})
RETURN l.entity_name AS section_l,
       r.confidence AS confidence,
       r.reasoning AS reasoning,
       m.entity_name AS section_m;

// Visualize the relationship in graph view
MATCH path = (l:`{WORKSPACE}` {entity_name: 'INSTRUCTION_NAME'})-[:GUIDES]->(m:`{WORKSPACE}` {entity_name: 'FACTOR_NAME'})
RETURN path;

// =============================================================================
// BULK CREATION - Create multiple relationships at once
// =============================================================================

// Batch template: Create multiple GUIDES relationships
UNWIND [
  {l_name: 'INSTRUCTION_1', m_name: 'FACTOR_1', reason: 'REASONING_1'},
  {l_name: 'INSTRUCTION_2', m_name: 'FACTOR_2', reason: 'REASONING_2'},
  {l_name: 'INSTRUCTION_3', m_name: 'FACTOR_3', reason: 'REASONING_3'}
] AS link
MATCH (l:`{WORKSPACE}` {entity_name: link.l_name})
MATCH (m:`{WORKSPACE}` {entity_name: link.m_name})
CREATE (l)-[r:GUIDES {
  confidence: 0.90,
  reasoning: link.reason,
  source: 'manual_correction',
  corrected_by: 'USERNAME',
  corrected_at: datetime()
}]->(m)
RETURN l.entity_name, type(r), m.entity_name;

// =============================================================================
// NOTES
// =============================================================================
// - Always run STEP 1 (FIND) before STEP 2 (CREATE) to avoid duplicates
// - Confidence score: 0.95-1.0 for obvious links, 0.80-0.94 for inferred links
// - Reasoning should explain WHY the instruction guides the evaluation factor
// - Use bulk creation for multiple similar corrections
// - Always verify with STEP 3 after creating relationships
