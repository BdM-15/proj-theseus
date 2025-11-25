// Template: Add Missing Metadata
// Purpose: Enrich entities with missing properties (requirement_type, criticality_level, compliance_method, etc.)
// Usage: Replace {WORKSPACE} and entity names, customize metadata values

// =============================================================================
// STEP 1: FIND ENTITIES MISSING METADATA - Diagnostic queries
// =============================================================================

// Count entities missing key properties by type
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type IN ['requirement', 'evaluation_factor', 'submission_instruction']
RETURN n.entity_type AS type,
       count(CASE WHEN n.requirement_type IS NULL THEN 1 END) AS missing_requirement_type,
       count(CASE WHEN n.criticality_level IS NULL THEN 1 END) AS missing_criticality,
       count(CASE WHEN n.compliance_method IS NULL THEN 1 END) AS missing_compliance_method,
       count(n) AS total
ORDER BY type;

// List specific requirements missing metadata
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'requirement'
  AND (n.requirement_type IS NULL OR n.criticality_level IS NULL)
RETURN n.entity_name AS requirement,
       n.requirement_type AS type,
       n.criticality_level AS criticality,
       n.description AS details
ORDER BY n.entity_name
LIMIT 25;

// =============================================================================
// STEP 2: ADD METADATA TO SINGLE ENTITY
// =============================================================================

// Template: Add metadata to one entity
MATCH (n:`{WORKSPACE}` {entity_name: 'ENTITY_NAME'})
SET n.requirement_type = 'REQUIREMENT_TYPE',         // Options: functional, performance, technical, staffing, etc.
    n.criticality_level = 'CRITICALITY_LEVEL',       // Options: mandatory, critical, important, desirable
    n.compliance_method = 'COMPLIANCE_METHOD',       // Options: demonstration, inspection, analysis, test
    n.source_section = 'SOURCE_SECTION',             // e.g., 'Section C.6.2.1'
    n.keywords = ['KEYWORD1', 'KEYWORD2'],
    n.updated_by = 'USERNAME',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// =============================================================================
// EXAMPLE: Add metadata to MCPP requirements
// =============================================================================

// Example 1: Functional requirement (mandatory, demonstration)
MATCH (n:`mcpp_drfp_2025` {entity_name: 'C.6.1: System Architecture'})
SET n.requirement_type = 'functional',
    n.criticality_level = 'mandatory',
    n.compliance_method = 'demonstration',
    n.source_section = 'Section C.6.1',
    n.keywords = ['architecture', 'system design', 'integration'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// Example 2: Performance requirement (critical, test)
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

// Example 3: Staffing requirement (mandatory, inspection)
MATCH (n:`mcpp_drfp_2025` {entity_name: 'C.9.1: Secret Clearance Required'})
SET n.requirement_type = 'staffing',
    n.criticality_level = 'mandatory',
    n.compliance_method = 'inspection',
    n.source_section = 'Section C.9.1',
    n.keywords = ['clearance', 'security', 'personnel'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// =============================================================================
// STEP 3: ADD METADATA TO EVALUATION FACTORS
// =============================================================================

// Template: Add importance weights and evaluation methods
MATCH (n:`{WORKSPACE}` {entity_name: 'FACTOR_NAME'})
SET n.weight_percentage = WEIGHT,                    // e.g., 35.0 for 35%
    n.evaluation_method = 'EVALUATION_METHOD',       // Options: adjectival, color-coded, point-based
    n.rating_scale = 'RATING_SCALE',                 // e.g., 'Outstanding/Good/Acceptable/Marginal/Unsatisfactory'
    n.updated_by = 'USERNAME',
    n.updated_at = datetime()
RETURN n.entity_name, n.weight_percentage, n.evaluation_method;

// Example: Add weight to Technical Approach factor
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
SET n.weight_percentage = 35.0,
    n.evaluation_method = 'adjectival',
    n.rating_scale = 'Outstanding/Good/Acceptable/Marginal/Unsatisfactory',
    n.evaluation_criteria = ['Soundness of approach', 'Risk mitigation', 'Innovation'],
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.weight_percentage, n.evaluation_method;

// =============================================================================
// STEP 4: ADD METADATA TO SUBMISSION INSTRUCTIONS
// =============================================================================

// Template: Add page limits and format requirements
MATCH (n:`{WORKSPACE}` {entity_name: 'INSTRUCTION_NAME'})
SET n.page_limit = PAGE_LIMIT,                       // e.g., 25
    n.format_requirements = 'FORMAT_REQUIREMENTS',   // e.g., 'Font: Times New Roman 12pt, Margins: 1 inch'
    n.required_content = ['CONTENT_1', 'CONTENT_2'],
    n.updated_by = 'USERNAME',
    n.updated_at = datetime()
RETURN n.entity_name, n.page_limit, n.format_requirements;

// Example: Add format requirements to Technical Proposal instruction
MATCH (n:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})
SET n.page_limit = 25,
    n.format_requirements = 'Font: Times New Roman 12pt, Margins: 1 inch, Line spacing: Single',
    n.required_content = ['Cover page', 'Executive summary', 'Technical approach narrative', 'Risk mitigation plan'],
    n.submission_deadline = datetime('2025-07-15T16:00:00'),
    n.updated_by = 'analyst',
    n.updated_at = datetime()
RETURN n.entity_name, n.page_limit, n.required_content;

// =============================================================================
// BULK METADATA ADDITION - Add properties to multiple entities at once
// =============================================================================

// Batch template: Add requirement_type to multiple requirements
UNWIND [
  {name: 'REQ_1', type: 'functional', criticality: 'mandatory'},
  {name: 'REQ_2', type: 'performance', criticality: 'critical'},
  {name: 'REQ_3', type: 'technical', criticality: 'important'}
] AS metadata
MATCH (n:`{WORKSPACE}` {entity_name: metadata.name})
SET n.requirement_type = metadata.type,
    n.criticality_level = metadata.criticality,
    n.updated_by = 'USERNAME',
    n.updated_at = datetime()
RETURN n.entity_name, n.requirement_type, n.criticality_level;

// Batch template: Add keywords to all requirements in a section
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'requirement'
  AND n.source_section STARTS WITH 'Section C.6'
SET n.keywords = n.keywords + ['technical', 'system requirements'],
    n.updated_by = 'USERNAME',
    n.updated_at = datetime()
RETURN n.entity_name, n.keywords;

// =============================================================================
// STEP 5: VERIFY METADATA - Check updates were applied
// =============================================================================

// Verify metadata on specific entity
MATCH (n:`{WORKSPACE}` {entity_name: 'ENTITY_NAME'})
RETURN n.entity_name,
       n.requirement_type,
       n.criticality_level,
       n.compliance_method,
       n.keywords,
       n.updated_by,
       n.updated_at;

// Count entities with complete metadata
MATCH (n:`{WORKSPACE}`)
WHERE n.entity_type = 'requirement'
  AND n.requirement_type IS NOT NULL
  AND n.criticality_level IS NOT NULL
RETURN n.requirement_type AS type,
       n.criticality_level AS criticality,
       count(n) AS count
ORDER BY type, criticality;

// =============================================================================
// NOTES
// =============================================================================
// - Always use controlled vocabularies for metadata values (document valid options)
// - Update updated_by and updated_at for audit trail
// - Use arrays for multi-valued properties (keywords, required_content)
// - DateTime format: datetime('2025-07-15T16:00:00') or datetime() for current time
// - Batch operations are faster for bulk updates
// - Verify metadata before and after updates with diagnostic queries
