"""
Shipley Methodology Knowledge Module

Evergreen knowledge from Shipley Associates Business Development methodology:
- 7-Phase BD Lifecycle
- Color Team Reviews (Pink, Red, Gold)
- Capture Tools (Black Hat, Win Themes, Compliance Matrix)
- Proposal Planning & Management

Entity types: concept, strategic_theme
Source: Shipley Capture Guide, APMP Body of Knowledge

Note: These are PATTERNS and FRAMEWORKS, not canonical instances.
RFP-specific content comes from document extraction.
"""

# Source identifier for provenance tracking
SOURCE_ID = "govcon_ontology_shipley"
FILE_PATH = "shipley_methodology"


# =============================================================================
# ENTITIES: Shipley Methodology Concepts
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # Business Development Lifecycle (7 Phases)
    # -------------------------------------------------------------------------
    {
        "entity_name": "Shipley Business Development Lifecycle",
        "entity_type": "concept",
        "description": (
            "Shipley Associates' 7-phase process for winning government contracts: "
            "(1) Opportunity Identification - assess strategic fit and market alignment; "
            "(2) Pursuit Decision - bid/no-bid analysis with Pwin threshold evaluation; "
            "(3) Capture Planning - develop win strategy, customer relationships, teaming; "
            "(4) Proposal Planning - create outline, compliance matrix, schedule; "
            "(5) Proposal Development - writing, reviews, graphics, production; "
            "(6) Negotiation - pricing discussions, BAFOs, contract negotiations; "
            "(7) Contract Execution - transition planning, performance delivery. "
            "Key principle: Win before the RFP through early positioning and customer intimacy."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Opportunity Identification Phase",
        "entity_type": "concept",
        "description": (
            "Phase 1 of Shipley BD Lifecycle. Evaluate new opportunities against strategic "
            "criteria: Does this align with our core competencies? Is the customer in our "
            "target market? Do we have or can we build the required past performance? "
            "Outputs: Opportunity assessment, initial Pwin estimate, resource requirements. "
            "Gate decision: Pursue to qualification or decline early to conserve resources."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Pursuit Decision Phase",
        "entity_type": "concept",
        "description": (
            "Phase 2 of Shipley BD Lifecycle. Formal bid/no-bid decision using structured "
            "criteria: Pwin threshold (typically >40-50%), resource availability, competitive "
            "landscape analysis, customer relationship strength, contract value vs. B&P cost. "
            "Involves Bid/No-Bid Checklist scoring. Gate decision: Commit capture resources "
            "or decline with documented rationale for lessons learned."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Capture Planning Phase",
        "entity_type": "concept",
        "description": (
            "Phase 3 of Shipley BD Lifecycle. Develop comprehensive capture strategy: "
            "customer engagement plan, competitive analysis (Black Hat), teaming strategy, "
            "win theme development, price-to-win analysis, solution shaping. Key activities: "
            "customer calls, industry days, draft RFP comments, teammate selection, "
            "capability demonstrations. Outputs: Capture Plan, Win Strategy, Ghost Plan."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Proposal Planning Phase",
        "entity_type": "concept",
        "description": (
            "Phase 4 of Shipley BD Lifecycle. Translate capture strategy into proposal "
            "execution plan: annotated outline mapping to Section L/M, compliance matrix, "
            "proposal schedule with color team milestones, author assignments, "
            "graphics concepts, data calls for past performance and resumes. "
            "Pink Team readiness check ensures outline addresses all requirements."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Proposal Development Phase",
        "entity_type": "concept",
        "description": (
            "Phase 5 of Shipley BD Lifecycle. Execute proposal writing with iterative "
            "reviews: draft sections per annotated outline, integrate graphics and proof "
            "points, conduct color team reviews (Pink→Red→Gold), resolve action items, "
            "final production and compliance verification. Focus on evaluation criteria "
            "responsiveness and discriminator emphasis. Outputs: Compliant, compelling proposal."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Color Team Reviews
    # -------------------------------------------------------------------------
    {
        "entity_name": "Color Team Reviews",
        "entity_type": "concept",
        "description": (
            "Shipley proposal quality gates using color-coded review milestones: "
            "Pink Team (compliance review of outline/storyboards), Red Team (strategy "
            "review of full draft for persuasiveness and win theme integration), "
            "Gold Team (final polish review for production readiness). Each review has "
            "specific criteria, independent reviewers, and mandatory action item resolution. "
            "Best practice: Schedule reviews with adequate recovery time before submission."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Pink Team Review",
        "entity_type": "concept",
        "description": (
            "First color team review focused on COMPLIANCE. Reviews annotated outline, "
            "section storyboards, and compliance matrix against Section L instructions "
            "and Section M evaluation criteria. Questions: Does outline address every "
            "requirement? Are win themes planned for each section? Is page allocation "
            "appropriate for evaluation weights? Occurs before writing begins. "
            "Deliverable: Pink Team Report with compliance gaps and outline revisions."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Red Team Review",
        "entity_type": "concept",
        "description": (
            "Primary color team review focused on STRATEGY and PERSUASIVENESS. Reviews "
            "complete proposal draft as evaluators would see it. Criteria: Is solution "
            "compliant? Are win themes compelling and substantiated? Do discriminators "
            "differentiate us? Is pricing realistic? Would this score Outstanding/Excellent? "
            "Red Team simulates Source Selection Evaluation Board perspective. "
            "Deliverable: Red Team Report with section scores and improvement actions."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Gold Team Review",
        "entity_type": "concept",
        "description": (
            "Final color team review focused on PRODUCTION QUALITY. Reviews camera-ready "
            "proposal for professional presentation: formatting consistency, graphics "
            "quality, cross-reference accuracy, page count compliance, executive summary "
            "impact. No substantive content changes at this stage. Also reviews pricing "
            "volume for arithmetic accuracy and cost narrative consistency. "
            "Deliverable: Gold Team signoff for production and submission."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Capture Tools
    # -------------------------------------------------------------------------
    {
        "entity_name": "Black Hat Review",
        "entity_type": "concept",
        "description": (
            "Competitive analysis tool simulating competitors' likely proposal strategies. "
            "Team role-plays as each major competitor answering: What are their strengths? "
            "What solution will they propose? How will they price? What are their weaknesses "
            "we can ghost? Results inform win themes, discriminators, and price-to-win. "
            "Conduct mid-capture with updated intel. Ideation prompt: 'If I were [Competitor], "
            "what would I bid and how would I attack the incumbent?'"
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Compliance Matrix",
        "entity_type": "concept",
        "description": (
            "Traceability tool mapping RFP requirements to proposal responses. Columns: "
            "Requirement ID, Section L instruction, Section M criterion, Proposal section, "
            "Page number, Compliance status (Full/Partial/Exception). Critical for avoiding "
            "disqualification from non-responsiveness. Pink Team validates completeness. "
            "Maintained throughout proposal development. Links to requirements database "
            "for large proposals. Also called Requirements Traceability Matrix (RTM)."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Section L M Mapping",
        "entity_type": "concept",
        "description": (
            "Analysis technique aligning proposal submission instructions (Section L) with "
            "evaluation criteria (Section M) to identify: (1) Requirements with no evaluation "
            "criteria - compliance-only, (2) Evaluation criteria with no instructions - hidden "
            "requirements, (3) Weight mismatches - instructions emphasize different content "
            "than evaluation weights suggest. Informs page allocation and emphasis strategy. "
            "Best practice: Create mapping table before writing annotated outline."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Annotated Outline",
        "entity_type": "concept",
        "description": (
            "Detailed proposal outline with embedded guidance for writers. Includes: "
            "section number and title per RFP, assigned author, page allocation, applicable "
            "requirements/instructions (verbatim), evaluation criteria addressed, win themes "
            "to emphasize, proof points to include, graphics concepts, boilerplate references. "
            "Serves as writing blueprint ensuring consistent messaging. Created during "
            "Proposal Planning, validated at Pink Team, guides all subsequent writing."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Win Theme Development",
        "entity_type": "strategic_theme",
        "description": (
            "Shipley methodology for creating compelling proposal messages. Win themes follow "
            "Feature-Benefit-Proof pattern: Feature (what we offer), Benefit (value to customer), "
            "Proof (evidence/past performance). Effective themes are customer-focused, "
            "discriminating, provable, and evaluation-criteria aligned. Typically 3-5 themes "
            "per proposal, woven throughout all volumes. Themes answer: 'Why should we win?'"
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "theme_type": "WIN_THEME"
    },
    {
        "entity_name": "Ghost Strategy",
        "entity_type": "strategic_theme",
        "description": (
            "Technique for neutralizing competitor strengths without naming them. Ghosting "
            "raises evaluator concerns about competitors through positive self-positioning: "
            "'Unlike approaches that require lengthy transition periods, our proven team "
            "delivers Day 1 capability.' Effective ghosting is factual, professional, and "
            "highlights discriminators. Identified through Black Hat analysis. Never disparage "
            "competitors directly - focus on our superior approach to customer hot buttons."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "theme_type": "DISCRIMINATOR"
    },
]


# =============================================================================
# RELATIONSHIPS: Shipley Methodology Connections
# =============================================================================

RELATIONSHIPS = [
    # BD Lifecycle flow
    {
        "src_id": "Shipley Business Development Lifecycle",
        "tgt_id": "Opportunity Identification Phase",
        "description": "BD Lifecycle begins with Opportunity Identification as Phase 1",
        "keywords": "CONTAINS PHASE_OF",
        "weight": 1.0,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Shipley Business Development Lifecycle",
        "tgt_id": "Pursuit Decision Phase",
        "description": "BD Lifecycle includes Pursuit Decision as Phase 2 gate",
        "keywords": "CONTAINS PHASE_OF",
        "weight": 1.0,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Shipley Business Development Lifecycle",
        "tgt_id": "Capture Planning Phase",
        "description": "BD Lifecycle includes Capture Planning as Phase 3",
        "keywords": "CONTAINS PHASE_OF",
        "weight": 1.0,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Shipley Business Development Lifecycle",
        "tgt_id": "Proposal Planning Phase",
        "description": "BD Lifecycle includes Proposal Planning as Phase 4",
        "keywords": "CONTAINS PHASE_OF",
        "weight": 1.0,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Shipley Business Development Lifecycle",
        "tgt_id": "Proposal Development Phase",
        "description": "BD Lifecycle includes Proposal Development as Phase 5",
        "keywords": "CONTAINS PHASE_OF",
        "weight": 1.0,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Color Team relationships
    {
        "src_id": "Color Team Reviews",
        "tgt_id": "Pink Team Review",
        "description": "Pink Team is first color review in sequence",
        "keywords": "INCLUDES SEQUENCE",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Color Team Reviews",
        "tgt_id": "Red Team Review",
        "description": "Red Team is primary color review after Pink Team",
        "keywords": "INCLUDES SEQUENCE",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Color Team Reviews",
        "tgt_id": "Gold Team Review",
        "description": "Gold Team is final color review before submission",
        "keywords": "INCLUDES SEQUENCE",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Proposal Development Phase",
        "tgt_id": "Color Team Reviews",
        "description": "Proposal Development phase requires Color Team Reviews for quality",
        "keywords": "REQUIRES USES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Tool relationships
    {
        "src_id": "Capture Planning Phase",
        "tgt_id": "Black Hat Review",
        "description": "Capture Planning uses Black Hat Review for competitive analysis",
        "keywords": "USES INFORMS",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Black Hat Review",
        "tgt_id": "Ghost Strategy",
        "description": "Black Hat Review identifies competitor weaknesses for ghosting",
        "keywords": "INFORMS SUPPORTS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Black Hat Review",
        "tgt_id": "Win Theme Development",
        "description": "Black Hat Review informs discriminators for win themes",
        "keywords": "INFORMS SUPPORTS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Proposal Planning Phase",
        "tgt_id": "Compliance Matrix",
        "description": "Proposal Planning creates Compliance Matrix for traceability",
        "keywords": "CREATES USES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Proposal Planning Phase",
        "tgt_id": "Annotated Outline",
        "description": "Proposal Planning creates Annotated Outline for writers",
        "keywords": "CREATES PRODUCES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Proposal Planning Phase",
        "tgt_id": "Section L M Mapping",
        "description": "Proposal Planning requires Section L/M Mapping for compliance",
        "keywords": "REQUIRES USES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Pink Team Review",
        "tgt_id": "Compliance Matrix",
        "description": "Pink Team validates Compliance Matrix completeness",
        "keywords": "VALIDATES USES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Pink Team Review",
        "tgt_id": "Annotated Outline",
        "description": "Pink Team reviews Annotated Outline for requirements coverage",
        "keywords": "VALIDATES REVIEWS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Win Theme Development",
        "tgt_id": "Red Team Review",
        "description": "Red Team evaluates Win Theme persuasiveness and integration",
        "keywords": "EVALUATED_BY VALIDATED_BY",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Supporting Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Shipley Business Development Lifecycle Overview: The Shipley methodology "
            "defines a structured 7-phase process for pursuing and winning government "
            "contracts. Phases progress from Opportunity Identification through Contract "
            "Execution, with gate reviews at each transition. Key principle: 'Win before "
            "the RFP' through early positioning, customer engagement, and solution shaping "
            "during the pre-RFP capture phases. Organizations that engage customers early "
            "have 60-80% higher win rates than those who wait for RFP release."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Color Team Review Best Practices: Pink Team (compliance focus) should occur "
            "when annotated outline is complete but before significant writing begins. "
            "Red Team (strategy focus) requires 80% complete draft with integrated graphics. "
            "Gold Team (production focus) reviews camera-ready final document. Allow "
            "minimum 3-5 days between Red Team and submission for action item resolution. "
            "Independent reviewers from outside the proposal team provide most valuable "
            "feedback. Document all action items and track to closure."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Win Theme Formula (Feature-Benefit-Proof): Effective win themes follow a "
            "structured pattern: FEATURE (specific capability or approach you offer) → "
            "BENEFIT (quantified value to the customer) → PROOF (evidence from past "
            "performance or credentials). Example: 'Our CMMI Level 3 certified development "
            "process [Feature] reduces defect rates by 40% compared to industry average "
            "[Benefit], as demonstrated on the XYZ program where we delivered 99.2% "
            "defect-free code [Proof].' Themes must address customer hot buttons and "
            "discriminate from competitors."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Black Hat Competitive Analysis Process: (1) Identify 2-4 most likely "
            "competitors based on incumbent status, announced teaming, and market "
            "intelligence. (2) Assign team members to role-play each competitor. "
            "(3) Each 'competitor team' develops their likely win strategy, solution "
            "approach, pricing strategy, and strengths/weaknesses. (4) Present findings "
            "to capture team. (5) Identify ghosting opportunities and discriminator "
            "emphasis areas. Update Black Hat analysis when new intelligence emerges. "
            "Use findings to refine price-to-win and solution differentiation."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
