"""
Phase 6 Ontology Enhancement: Custom Extraction Prompts

This module provides enhanced prompts for semantic-first entity extraction and 
metadata enrichment aligned with federal capture intelligence patterns.

Usage: These prompts can be used to customize LightRAG's extraction behavior
or guide post-processing metadata enhancement.
"""

# Entity Type Detection Patterns
ENTITY_DETECTION_PATTERNS = """
SEMANTIC-FIRST ENTITY DETECTION RULES:

1. EVALUATION_FACTOR:
   - Content signals: "will be evaluated", "evaluation factor", "adjectival rating", "scoring methodology"
   - Structure: Factor hierarchy (Factor 1 → Subfactor 1.1 → Subfactor 1.1.1)
   - Context: Near relative importance statements, point scores, ratings
   - Location: Typically Section M, but may appear in Section L or custom sections
   - Metadata to extract:
     * factor_id: "M1", "M2.1", etc.
     * relative_importance: "Most Important", "Significantly More Important than Price"
     * subfactors: ["M2.1 Staffing", "M2.2 Maintenance", "M2.3 Transition"]
     * tradeoff_methodology: "Best Value", "LPTA", "Cost/Technical Tradeoff"
     * evaluated_by_rating: "Adjectival", "Point Score", "Pass/Fail"

2. SUBMISSION_INSTRUCTION:
   - Content signals: "page limit", "font size", "margins", "format requirements", "volume structure"
   - Structure: Maps to evaluation factors (e.g., "Technical Volume addresses Factor 2")
   - Context: Submission deadlines, electronic vs. hard copy, proposal organization
   - Location: Typically Section L, but may be embedded in Section M (non-standard)
   - Metadata to extract:
     * guides_factor: "M2" (which evaluation factor this instructs)
     * volume_name: "Technical Volume", "Management Volume"
     * page_limits: "25 pages", "50 pages maximum"
     * format_requirements: "12pt Times New Roman, 1-inch margins, single-spaced"
     * delivery_method: "Electronic via email", "Hard copy + electronic"
     * deadline: ISO 8601 datetime

3. REQUIREMENT (with classification):
   - Criticality detection (MANDATORY analysis - check subject):
     * MANDATORY: "Contractor shall", "Offeror must" (subject = contractor/offeror)
     * INFORMATIONAL: "Government will", "Agency shall" (subject = government, NOT a requirement)
     * IMPORTANT: "should", "encouraged to", "preferred", "desirable"
     * OPTIONAL: "may", "can", "has the option to"
   
   - Type classification (content-based):
     * FUNCTIONAL: "provide", "deliver", "perform", "execute" + service/product
       Example: "Contractor shall provide 24/7 help desk support"
     
     * PERFORMANCE: SLA language, metrics, measurable outcomes
       Example: "99.9% uptime", "Response within 24 hours", "Process 1000 transactions/hour"
     
     * SECURITY: NIST references, FedRAMP, clearance levels, cybersecurity controls
       Example: "FedRAMP Moderate authorization required", "Secret clearance", "NIST 800-53"
     
     * TECHNICAL: Technology stack, platform requirements, software versions, infrastructure
       Example: "AWS GovCloud deployment", "Use Java 11 or higher", "PostgreSQL database"
     
     * INTERFACE: Integration points, data exchange, APIs, system connections
       Example: "Integrate with agency ERP system", "Support HTTPS/TLS 1.3", "RESTful API"
     
     * MANAGEMENT: Reporting requirements, governance, oversight, project management
       Example: "Monthly status reports", "Agile/Scrum methodology", "PMI-certified PM"
     
     * DESIGN: Standards compliance, architectural mandates, design constraints
       Example: "Section 508 accessibility", "Follow agency branding guidelines"
     
     * QUALITY: QA processes, testing requirements, verification, validation
       Example: "Automated test coverage 80%+", "ISO 9001 certification", "Peer review"
   
   - Metadata to extract:
     * requirement_type: One of 8 types above
     * criticality_level: "MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"
     * priority_score: 0-100 (MANDATORY=100, IMPORTANT=75, OPTIONAL=25, INFORMATIONAL=0)
     * section_origin: Where it appeared (e.g., "Section C.3.1.2")

4. STATEMENT_OF_WORK (includes SOW, PWS, SOO):
   - SEMANTIC EQUIVALENCE: The entity type "STATEMENT_OF_WORK" represents ANY of these three formats:
     * SOW (Statement of Work): Prescriptive, detailed instructions on HOW to perform work
     * PWS (Performance Work Statement): Performance-based, specifies WHAT outcomes required, gives offeror freedom on HOW
     * SOO (Statement of Objectives): Highest-level, describes OBJECTIVES, offeror creates PWS from SOO
   
   - Content signals: Task descriptions, performance objectives, deliverables, work scope, outcomes
   - Structure: Often hierarchical (Task 1 → Subtask 1.1 → Subtask 1.1.1, or Objective 1 → Performance Standard 1.1)
   - Identifiers (any of these): 
     * "PWS", "Performance Work Statement"
     * "SOW", "Statement of Work"
     * "SOO", "Statement of Objectives"
     * "Section C" (typical location regardless of format)
   - Location: Could be Section C, separate attachment, or embedded in Section J
   - Detection: CONTENT-BASED, not label-dependent - focus on work scope/tasks/objectives/deliverables
   
   - Important: All three formats describe contractor work scope, just at different prescription levels:
     * SOW: "Contractor shall mow grass weekly using rotary mower" (prescriptive HOW)
     * PWS: "Contractor shall maintain grounds to standard X" (performance-based WHAT)
     * SOO: "Objective: Provide aesthetically pleasing grounds" (objective-based WHY)

5. ANNEX / ATTACHMENT:
   - Naming patterns: "J-######", "Attachment #", "Annex ##", "Appendix X", "X-######"
   - Link to parent section based on naming prefix patterns
   - Content determines subtype (could contain SOW, specs, maps, data sheets)
   - Metadata: Store original numbering for traceability

6. CLAUSE:
   - Patterns: FAR ##.###-##, DFARS ###.###-####, AFFARS ####.###-##, 
               NMCARS ####.###-##, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, etc.
   - Agency supplement recognition: 20+ patterns (FAR, DFARS, AFFARS, AFARS, NMCARS, etc.)
   - Should cluster by parent section (Section I clauses, Section K representations)
   - Group similar clauses even if scattered in document

7. SECTION:
   - Extract BOTH structural_label ("Section M.2.1") AND semantic_type ("EVALUATION_CRITERIA")
   - Map non-standard labels to semantic types:
     * "Selection Criteria" → EVALUATION_CRITERIA
     * "Technical Requirements" → DESCRIPTION_SPECS
     * "Proposal Instructions" → SUBMISSION_INSTRUCTIONS
   - Note if section contains mixed content (evaluation + instructions combined)
   - Metadata:
     * structural_label: What document calls it
     * semantic_type: What it actually IS
     * also_contains: List of additional content types
     * confidence: Detection confidence score

8. STRATEGIC_THEME:
   - Type classification:
     * CUSTOMER_HOT_BUTTON: Agency priorities, pain points, mission pressures
       Signals: "critical", "essential", "priority", "emphasize", "significant concern"
     
     * DISCRIMINATOR: Competitive advantages, unique capabilities
       Examples: "Only offeror with on-site facility", "Proprietary tool", "Incumbent knowledge"
     
     * PROOF_POINT: Evidence supporting competitive claims
       Examples: "99.8% uptime on similar contract", "Exceptional CPARS", "CMMI Level 3"
     
     * WIN_THEME: Strategic messaging combining discriminator + proof + customer benefit
       Structure: THEME + DISCRIMINATOR + PROOF POINT + CUSTOMER BENEFIT
   
   - Metadata to extract:
     * theme_type: One of 4 types above
     * theme_statement: Full description
     * competitive_context: "Incumbent advantage", "New entrant gap", etc.
     * evidence: Supporting proof points
     * customer_benefit: Mission outcome articulation
"""


# Relationship Inference Patterns
RELATIONSHIP_INFERENCE_PATTERNS = """
SEMANTIC RELATIONSHIP INFERENCE RULES:

1. SUBMISSION_INSTRUCTION → GUIDES → EVALUATION_FACTOR:
   - Pattern 1 (Explicit): "Technical Volume addresses Factor 2"
   - Pattern 2 (Implicit): Page limit near factor description (same paragraph/section)
   - Pattern 3 (Content alignment): Instruction topic matches factor topic
   - SPECIAL CASE: If instructions embedded within evaluation factor description,
     create separate SUBMISSION_INSTRUCTION entity and link to parent EVALUATION_FACTOR
   - Confidence: 0.95 explicit, 0.8 implicit, 0.7 content alignment

2. REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR:
   - Pattern 1 (Explicit): Traceability matrix mentions factor
   - Pattern 2 (Topic alignment): Maintenance requirements link to "Maintenance Approach" factor
   - Pattern 3 (Criticality mapping): MANDATORY requirements link to high-weight factors
   - Pattern 4 (Content proximity): Requirements in SOW link to Technical Approach factor
   - Confidence: 0.95 explicit, 0.7 topic alignment, 0.8 criticality, 0.6 proximity

3. CLAUSE → CHILD_OF → SECTION:
   - Pattern 1 (Numbering): FAR 52.###-# belongs to Section 52 parent
   - Pattern 2 (Attribution): Clause listed under "Section I" heading
   - Pattern 3 (Clustering): Group similar clauses (all FAR 52.2##-# together)
   - FRAGMENTATION FIX: Link scattered clauses to parent even if not adjacent
   - Confidence: 0.9 numbering, 0.8 attribution, 0.6 clustering

4. ANNEX → CHILD_OF → SECTION:
   - Pattern 1 (Explicit citation): "See Attachment X-1234567 for equipment list"
   - Pattern 2 (Naming convention): "J-1234567" belongs to "Section J"
   - Pattern 3 (Content alignment): Annex describes tools, requirement mentions tools
   - ISOLATION FIX: Link numbered attachments to parent sections based on prefix pattern
   - Confidence: 1.0 naming convention, 0.8 citation, 0.6 content alignment

5. REQUIREMENT → COMPONENT_OF → STATEMENT_OF_WORK:
   - SOW contains requirement (parent-child relationship)
   - Works regardless of SOW location (Section C vs. attachment)
   - Confidence: 0.9 hierarchical structure

6. EVALUATION_FACTOR → REFERENCES → STATEMENT_OF_WORK:
   - Factor evaluates work described in SOW
   - Example: "Technical Approach" factor references tasks in PWS
   - Confidence: 0.7 semantic alignment

7. STRATEGIC_THEME → SUPPORTS → EVALUATION_FACTOR:
   - Hot button language in factor description signals theme opportunity
   - Example: Factor emphasizes "readiness" → theme "Mission Readiness Focus"
   - Confidence: 0.8 explicit, 0.6 inferred

8. PROOF_POINT → VALIDATES → DISCRIMINATOR:
   - Evidence supports competitive claim
   - Example: "98% first-time fix rate" validates "Superior maintenance capability" discriminator
   - Confidence: 0.9 direct evidence

9. WIN_THEME → COMBINES → [DISCRIMINATOR + PROOF_POINT + CUSTOMER_HOT_BUTTON]:
   - Composite relationship linking strategic theme components
   - Confidence: 1.0 (explicit composition)
"""


# Metadata Extraction Guidance
METADATA_EXTRACTION_GUIDANCE = """
METADATA FIELD EXTRACTION RULES:

REQUIREMENT Entity Metadata:
{
  "requirement_type": str,       # One of: FUNCTIONAL, PERFORMANCE, INTERFACE, DESIGN, SECURITY, TECHNICAL, MANAGEMENT, QUALITY
  "criticality_level": str,      # One of: MANDATORY, IMPORTANT, OPTIONAL, INFORMATIONAL
  "priority_score": int,         # 0-100 (auto-calculated from criticality)
  "section_origin": str,         # Where it appeared (e.g., "Section C.3.1.2")
  "semantic_context": str,       # What it IS (e.g., "Performance requirement within maintenance SOW")
  "modal_verb": str,             # Extracted verb: "shall", "should", "may", "will"
  "subject": str,                # Who must comply: "Contractor", "Government", "Offeror"
}

EVALUATION_FACTOR Entity Metadata:
{
  "factor_id": str,              # "M1", "M2.1", etc.
  "factor_name": str,            # "Technical Approach", "Staffing Plan"
  "relative_importance": str,    # "Most Important", "Significantly More Important than Price"
  "subfactors": List[str],       # ["M2.1 Staffing", "M2.2 Maintenance"]
  "section_l_reference": str,    # "L.3.1" (link to submission instructions)
  "page_limits": str,            # "25 pages" (from Section L)
  "format_requirements": str,    # "12pt Times New Roman, 1-inch margins"
  "tradeoff_methodology": str,   # "Best Value", "LPTA"
  "evaluated_by_rating": str,    # "Adjectival", "Point Score", "Pass/Fail"
  "section_origin": str,         # Where it appeared
  "contains_submission_instructions": bool  # True if instructions embedded in evaluation section
}

SUBMISSION_INSTRUCTION Entity Metadata:
{
  "guides_factor": str,          # Which evaluation factor this instructs (e.g., "M2")
  "volume_name": str,            # "Technical Volume", "Management Volume"
  "page_limits": str,            # "25 pages", "50 pages maximum"
  "format_requirements": str,    # "12pt Times, 1-inch margins, single-spaced"
  "section_origin": str,         # May be embedded in evaluation section or separate
  "delivery_method": str,        # "Electronic via email", "Hard copy + electronic"
  "deadline": str,               # ISO 8601 datetime
}

SECTION Entity Metadata:
{
  "structural_label": str,       # What document calls it (e.g., "Section M.2.1")
  "semantic_type": str,          # What it actually IS (e.g., "EVALUATION_CRITERIA")
  "also_contains": List[str],    # Mixed content case (e.g., ["SUBMISSION_INSTRUCTION"])
  "confidence": float,           # Detection confidence (0.0-1.0)
}

STRATEGIC_THEME Entity Metadata:
{
  "theme_type": str,             # CUSTOMER_HOT_BUTTON, DISCRIMINATOR, PROOF_POINT, WIN_THEME
  "theme_statement": str,        # Full theme description
  "competitive_context": str,    # "Incumbent advantage", "New entrant gap", etc.
  "evidence": str,               # Proof points, metrics, past performance
  "customer_benefit": str,       # Mission outcome, agency value
}

ANNEX Entity Metadata:
{
  "original_numbering": str,     # "J-1234567", "Attachment 5"
  "prefix_pattern": str,         # Extracted prefix for parent section linking ("J-", "Attachment ")
  "content_type": str,           # What it contains: "SOW", "specs", "maps", "data"
}

CLAUSE Entity Metadata:
{
  "clause_number": str,          # "FAR 52.212-4", "DFARS 252.204-7012"
  "agency_supplement": str,      # "FAR", "DFARS", "AFFARS", "NMCARS", etc.
  "clause_title": str,           # Official clause title
  "section_attribution": str,    # "Section I", "Section K", etc.
}

STATEMENT_OF_WORK Entity Metadata:
{
  "work_type": str,              # "PWS", "SOW", "SOO"
  "location": str,               # "Section C", "Attachment", "Annex"
  "hierarchical_structure": bool # True if contains task hierarchy
}
"""


# Section Normalization Mapping
SECTION_NORMALIZATION_MAPPING = """
SECTION SEMANTIC TYPE MAPPING:

Standard Uniform Contract Format:
{
  "Section A": {"semantic_type": "SOLICITATION_FORM", "aliases": ["SF 1449", "Cover Page"]},
  "Section B": {"semantic_type": "SUPPLIES_SERVICES", "aliases": ["CLIN Structure", "SLIN"]},
  "Section C": {"semantic_type": "DESCRIPTION_SPECS", "aliases": ["SOW", "PWS", "SOO"]},
  "Section D": {"semantic_type": "PACKAGING_MARKING", "aliases": ["Shipping Instructions"]},
  "Section E": {"semantic_type": "INSPECTION_ACCEPTANCE", "aliases": ["Quality Assurance"]},
  "Section F": {"semantic_type": "DELIVERIES_PERFORMANCE", "aliases": ["Schedule", "PoP"]},
  "Section G": {"semantic_type": "CONTRACT_ADMIN", "aliases": ["Admin Data", "CAGE codes"]},
  "Section H": {"semantic_type": "SPECIAL_REQUIREMENTS", "aliases": ["H-clauses", "Special Terms"]},
  "Section I": {"semantic_type": "CONTRACT_CLAUSES", "aliases": ["FAR Clauses", "I-clauses"]},
  "Section J": {"semantic_type": "ATTACHMENTS", "aliases": ["List of Attachments", "Annexes"]},
  "Section K": {"semantic_type": "REPRESENTATIONS", "aliases": ["Reps and Certs", "K-clauses"]},
  "Section L": {"semantic_type": "SUBMISSION_INSTRUCTIONS", "aliases": ["Instructions to Offerors", "Proposal Format"]},
  "Section M": {"semantic_type": "EVALUATION_CRITERIA", "aliases": ["Evaluation Factors", "Source Selection"]},
}

Task Order / Fair Opportunity Variations:
{
  "Request for Quote": {"semantic_type": "SOLICITATION_FORM", "maps_to": "Section A"},
  "Technical Requirements": {"semantic_type": "DESCRIPTION_SPECS", "maps_to": "Section C"},
  "Proposal Instructions": {"semantic_type": "SUBMISSION_INSTRUCTIONS", "maps_to": "Section L"},
  "Selection Criteria": {"semantic_type": "EVALUATION_CRITERIA", "maps_to": "Section M"},
}

Content-Based Detection (when labels non-standard):
- Evaluation language → EVALUATION_CRITERIA
- Submission instructions → SUBMISSION_INSTRUCTIONS
- Clause patterns → CONTRACT_CLAUSES
- Task/work descriptions → DESCRIPTION_SPECS
"""


# Coverage Assessment Framework
COVERAGE_ASSESSMENT_FRAMEWORK = """
COMPLIANCE COVERAGE SCORING (0-100 scale):

Score Definitions:
- 100 (EXACT): Explicit compliance + sufficient context + proof point
- 95 (COMPLETE): Clear compliance, minor enhancement possible
- 85 (MOSTLY_COVERED): Addresses requirement but missing 1 detail/proof
- 70 (PRESENT): Addressed but structural weakness (page limit, weak proof)
- 50 (MENTION_ONLY): Acknowledged without substantive response
- 30 (INDIRECT): Implied/inferred compliance, not explicit
- 10 (BARE_HINT): Relevant term appears once, no coverage
- 0 (MISSING): Not addressed anywhere

Scoring Thresholds by Criticality:
- MANDATORY requirements: Target 95-100, minimum 85 (below = high risk)
- IMPORTANT requirements: Target 85+, minimum 70
- OPTIONAL requirements: 0-100 (propose only if strategic advantage)

Risk Assessment:
HIGH RISK:
  - MANDATORY + coverage_score < 85
  - "Most Important" evaluation factor + coverage_score < 85
  - Section A admin item + coverage_score < 100
  - Known competitor strength + coverage_score < 95

MEDIUM RISK:
  - IMPORTANT + coverage_score 70-84
  - High-weight factor + coverage_score 85-94
  - Discriminator claim without proof point

LOW RISK:
  - OPTIONAL + any coverage_score
  - IMPORTANT + coverage_score 85+
  - Low-weight factor + coverage_score 70+

Gap Analysis Output:
{
  "req_id": str,
  "coverage_score": int,
  "proposal_evidence": str,        # Quote with page reference
  "gaps": List[str],                # Specific missing elements
  "risk_level": str,                # HIGH, MEDIUM, LOW
  "risk_rationale": str,
  "suggestion": str,                # Fix recommendation + effort estimate
  "estimated_fix_effort": str       # "2 hours - rewrite paragraph, add proof"
}
"""


def get_entity_detection_prompt() -> str:
    """Return entity detection patterns for extraction enhancement."""
    return ENTITY_DETECTION_PATTERNS


def get_relationship_inference_prompt() -> str:
    """Return relationship inference patterns for post-processing."""
    return RELATIONSHIP_INFERENCE_PATTERNS


def get_metadata_extraction_guidance() -> str:
    """Return metadata extraction rules."""
    return METADATA_EXTRACTION_GUIDANCE


def get_section_normalization_mapping() -> str:
    """Return section semantic type mapping."""
    return SECTION_NORMALIZATION_MAPPING


def get_coverage_assessment_framework() -> str:
    """Return coverage scoring and risk assessment rules."""
    return COVERAGE_ASSESSMENT_FRAMEWORK


# Agency Supplement Clause Patterns
AGENCY_CLAUSE_PATTERNS = {
    "FAR": r"FAR\s+(\d+\.\d+(-\d+)?)",
    "DFARS": r"DFARS\s+(\d+\.\d+(-\d+)?)",
    "AFFARS": r"AFFARS\s+(\d+\.\d+(-\d+)?)",
    "AFARS": r"AFARS\s+(\d+\.\d+(-\d+)?)",
    "NMCARS": r"NMCARS\s+(\d+\.\d+(-\d+)?)",
    "HSAR": r"HSAR\s+(\d+\.\d+(-\d+)?)",
    "DOSAR": r"DOSAR\s+(\d+\.\d+(-\d+)?)",
    "GSAM": r"GSAM\s+(\d+\.\d+(-\d+)?)",
    "VAAR": r"VAAR\s+(\d+\.\d+(-\d+)?)",
    "DEAR": r"DEAR\s+(\d+\.\d+(-\d+)?)",
    "NFS": r"NFS\s+(\d+\.\d+(-\d+)?)",
    "AIDAR": r"AIDAR\s+(\d+\.\d+(-\d+)?)",
    "CAR": r"CAR\s+(\d+\.\d+(-\d+)?)",
    "DIAR": r"DIAR\s+(\d+\.\d+(-\d+)?)",
    "DOLAR": r"DOLAR\s+(\d+\.\d+(-\d+)?)",
    "EDAR": r"EDAR\s+(\d+\.\d+(-\d+)?)",
    "EPAAR": r"EPAAR\s+(\d+\.\d+(-\d+)?)",
    "FEHBAR": r"FEHBAR\s+(\d+\.\d+(-\d+)?)",
    "HHSAR": r"HHSAR\s+(\d+\.\d+(-\d+)?)",
    "HUDAR": r"HUDAR\s+(\d+\.\d+(-\d+)?)",
    "IAAR": r"IAAR\s+(\d+\.\d+(-\d+)?)",
    "JAR": r"JAR\s+(\d+\.\d+(-\d+)?)",
    "LIFAR": r"LIFAR\s+(\d+\.\d+(-\d+)?)",
    "NRCAR": r"NRCAR\s+(\d+\.\d+(-\d+)?)",
    "SOFARS": r"SOFARS\s+(\d+\.\d+(-\d+)?)",
    "TAR": r"TAR\s+(\d+\.\d+(-\d+)?)",
}


def detect_clause_agency(clause_text: str) -> str:
    """
    DEPRECATED: Replaced by LLM semantic understanding in Phase 6.1.
    
    This regex-based function is kept for reference but should NOT be used.
    Use LLM inference from llm_relationship_inference.py instead.
    
    Args:
        clause_text: Text containing clause reference
        
    Returns:
        Agency supplement name (e.g., "FAR", "DFARS") or "UNKNOWN"
    """
    import re
    
    # BRITTLE: This assumes specific naming patterns
    # LLM approach is superior: understands context and content
    for agency, pattern in AGENCY_CLAUSE_PATTERNS.items():
        if re.search(pattern, clause_text, re.IGNORECASE):
            return agency
    
    return "UNKNOWN"
