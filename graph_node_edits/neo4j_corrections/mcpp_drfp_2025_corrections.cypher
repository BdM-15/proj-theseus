// =============================================================================
// MCPP II DRAFT RFP (M6700425R0007) - Neo4j Graph Corrections
// =============================================================================
// Workspace: mcpp_drfp_2025
// RFP: Marine Corps Platform and Portfolio II (MCPP II)
// Processing Date: 2025-01-XX
// Corrections Applied: 2025-01-XX by analyst
// 
// PURPOSE: This file documents all manual corrections made to the knowledge graph
// after initial processing. Corrections can be re-run after reprocessing the RFP.
//
// USAGE: Copy relevant queries into Neo4j Browser (http://localhost:7474) and execute
// =============================================================================

// -----------------------------------------------------------------------------
// CORRECTION 1: Fix Missing Section L ↔ M Link (Technical Approach)
// -----------------------------------------------------------------------------
// Issue: Section L.6 (Technical Proposal Format) was not linked to Factor 1 (Technical Approach)
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Created GUIDES relationship with confidence 0.98

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

// Verification:
// MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})-[r:GUIDES]->(m:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
// RETURN l.entity_name, r.confidence, m.entity_name;

// -----------------------------------------------------------------------------
// CORRECTION 2: Fix Missing Section L ↔ M Link (Past Performance)
// -----------------------------------------------------------------------------
// Issue: Section L.8 (Past Performance) was not linked to Factor 2 (Past Performance)
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Created GUIDES relationship with confidence 0.99

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

// -----------------------------------------------------------------------------
// CORRECTION 3: Add Missing Metadata to Requirement (Section C.6.1)
// -----------------------------------------------------------------------------
// Issue: System Architecture requirement missing requirement_type and criticality_level
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Added functional/mandatory metadata

MATCH (n:`mcpp_drfp_2025` {entity_name: 'C.6.1: System Architecture'})
SET n.requirement_type = 'functional',
    n.criticality_level = 'mandatory',
    n.compliance_method = 'demonstration',
    n.source_section = 'Section C.6.1',
    n.keywords = ['architecture', 'system design', 'integration'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// -----------------------------------------------------------------------------
// CORRECTION 4: Add Missing Metadata to Requirement (Section C.7.2)
// -----------------------------------------------------------------------------
// Issue: Response Time requirement missing requirement_type and criticality_level
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Added performance/critical metadata with acceptance criteria

MATCH (n:`mcpp_drfp_2025` {entity_name: 'C.7.2: Response Time < 2 seconds'})
SET n.requirement_type = 'performance',
    n.criticality_level = 'critical',
    n.compliance_method = 'test',
    n.source_section = 'Section C.7.2',
    n.keywords = ['performance', 'latency', 'response time'],
    n.acceptance_criteria = 'System response time must be under 2 seconds for 95% of requests',
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// -----------------------------------------------------------------------------
// CORRECTION 5: Fix Entity Type (Factor 3 misclassified as concept)
// -----------------------------------------------------------------------------
// Issue: "Factor 3: Price Evaluation" was classified as concept instead of evaluation_factor
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Changed entity_type from concept to evaluation_factor

MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 3: Price Evaluation'})
SET n.old_entity_type = n.entity_type,
    n.entity_type = 'evaluation_factor',
    n.corrected_by = 'analyst',
    n.corrected_at = datetime(),
    n.correction_reason = 'Entity is a Section M evaluation criterion, not a concept'
RETURN n.entity_name, n.old_entity_type AS was, n.entity_type AS now;

// -----------------------------------------------------------------------------
// CORRECTION 6: Delete Low-Confidence Relationship
// -----------------------------------------------------------------------------
// Issue: Spurious GUIDES relationship between Section L.5 (Cost Proposal) and Factor 1 (Technical Approach)
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Deleted relationship (confidence 0.35, incorrect mapping)

MATCH (a:`mcpp_drfp_2025` {entity_name: 'Section L.5: Cost Proposal'})-[r:GUIDES]->(b:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
WHERE r.confidence < 0.4
DELETE r
RETURN 'Deleted low-confidence GUIDES relationship' AS status;

// -----------------------------------------------------------------------------
// CORRECTION 7: Merge Duplicate Entities (Section C.6 formatting variants)
// -----------------------------------------------------------------------------
// Issue: Two entities for same section: "section c.6" and "Section C.6"
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Merged "section c.6" into "Section C.6" (standardized formatting)

// Step 1: Redirect outgoing relationships
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
MATCH (primary:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
MATCH (duplicate)-[r]->(other)
WHERE NOT (primary)-[]->(other)
CREATE (primary)-[r2:SAME_TYPE]->(other)
SET r2 = properties(r),
    r2.merged_from = 'section c.6',
    r2.merged_at = datetime()
DELETE r;

// Step 2: Redirect incoming relationships
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
MATCH (primary:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
MATCH (other)-[r]->(duplicate)
WHERE NOT (other)-[]->(primary)
CREATE (other)-[r2:SAME_TYPE]->(primary)
SET r2 = properties(r),
    r2.merged_from = 'section c.6',
    r2.merged_at = datetime()
DELETE r;

// Step 3: Delete duplicate
MATCH (duplicate:`mcpp_drfp_2025` {entity_name: 'section c.6'})
DETACH DELETE duplicate;

// Step 4: Verify merge
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
OPTIONAL MATCH (n)-[r]-()
RETURN n.entity_name, count(r) AS relationship_count;

// -----------------------------------------------------------------------------
// CORRECTION 8: Add Evaluation Weights to Factors
// -----------------------------------------------------------------------------
// Issue: Evaluation factors missing weight_percentage and evaluation_method
// Date: 2025-01-XX
// Analyst: analyst
// Resolution: Added weights and evaluation methods from Section M

// Factor 1: Technical Approach (35%)
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
SET n.weight_percentage = 35.0,
    n.evaluation_method = 'adjectival',
    n.rating_scale = 'Outstanding/Good/Acceptable/Marginal/Unsatisfactory',
    n.evaluation_criteria = ['Soundness of approach', 'Risk mitigation', 'Innovation'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.weight_percentage, n.evaluation_method;

// Factor 2: Past Performance (30%)
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 2: Past Performance'})
SET n.weight_percentage = 30.0,
    n.evaluation_method = 'adjectival',
    n.rating_scale = 'Exceptional/Very Good/Satisfactory/Neutral/Unsatisfactory',
    n.evaluation_criteria = ['Relevance', 'Quality', 'Recency'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.weight_percentage, n.evaluation_method;

// Factor 3: Price (35%)
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 3: Price Evaluation'})
SET n.weight_percentage = 35.0,
    n.evaluation_method = 'point-based',
    n.rating_scale = 'Lowest evaluated price receives maximum points',
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.weight_percentage, n.evaluation_method;

// =============================================================================
// VERIFICATION QUERIES - Run to validate all corrections
// =============================================================================

// 1. Count Section L ↔ M links
MATCH (l:`mcpp_drfp_2025`)-[r:GUIDES]->(m:`mcpp_drfp_2025`)
WHERE l.entity_type = 'submission_instruction'
  AND m.entity_type = 'evaluation_factor'
RETURN count(r) AS section_l_m_links;

// 2. Count requirements with complete metadata
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'requirement'
  AND n.requirement_type IS NOT NULL
  AND n.criticality_level IS NOT NULL
RETURN count(n) AS requirements_with_metadata;

// 3. Count evaluation factors with weights
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'evaluation_factor'
  AND n.weight_percentage IS NOT NULL
RETURN count(n) AS factors_with_weights;

// 4. Check for remaining duplicates
MATCH (n:`mcpp_drfp_2025`)
WITH toLower(n.entity_name) AS normalized_name, collect(n) AS entities
WHERE size(entities) > 1
RETURN count(*) AS remaining_duplicates;

// 5. Summary of corrections applied
MATCH (n:`mcpp_drfp_2025`)
WHERE n.corrected_by IS NOT NULL OR n.updated_by IS NOT NULL
RETURN n.entity_type AS type,
       count(n) AS corrected_entities
ORDER BY corrected_entities DESC;

// =============================================================================
// END OF CORRECTIONS
// =============================================================================
// Total Corrections: 8
// Last Updated: 2025-01-XX
// Next Review: After RFP reprocessing or major updates
// =============================================================================
