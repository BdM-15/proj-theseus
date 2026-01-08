"""
Lessons Learned Knowledge Module

Evergreen knowledge from 20+ years federal contracting experience:
- Agency-specific tendencies and patterns
- Common RFP pitfalls and red flags
- What Outstanding ratings actually require
- Industry vertical insights
- Recompete vs new business distinctions

Entity types: concept, strategic_theme
Source: Industry experience, GAO protest decisions, FPDS data patterns

Note: These are PATTERNS from experience, not specific contract details.
RFP-specific requirements come from document extraction.
"""

SOURCE_ID = "govcon_ontology_lessons"
FILE_PATH = "lessons_learned"


# =============================================================================
# ENTITIES: Lessons Learned
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # Proposal Pitfalls
    # -------------------------------------------------------------------------
    {
        "entity_name": "Common Proposal Disqualification Causes",
        "entity_type": "concept",
        "description": (
            "Frequent reasons proposals are rejected as non-responsive or unacceptable. "
            "Top causes: (1) Missing required content - failing to address specific Section L "
            "requirements, (2) Page limit violations - even one page over can disqualify, "
            "(3) Late submission - no exceptions regardless of reason, (4) Wrong format - "
            "file types, fonts, margins not per instructions, (5) Missing certifications - "
            "required representations not included, (6) Non-compliant pricing - wrong CLINs, "
            "missing elements, arithmetic errors. Prevention: Compliance matrix validated at "
            "Pink Team, production checklist at Gold Team, early submission with confirmation."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Ambiguous Requirement Red Flags",
        "entity_type": "concept",
        "description": (
            "RFP language patterns indicating risk requiring clarification or strategic response. "
            "Red flags: (1) Contradictory requirements - conflicting instructions between sections, "
            "(2) Undefined terms - acronyms or jargon without definitions, (3) Open-ended scope - "
            "'as needed' or 'to be determined' without bounds, (4) Unrealistic timelines - "
            "delivery dates inconsistent with scope, (5) Undefined evaluation criteria - "
            "factors without rating descriptions, (6) Missing data - workload drivers not "
            "provided for pricing. Strategy: Submit questions during Q&A period, document "
            "assumptions prominently, propose boundaries where scope unclear."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Hidden Requirement Patterns",
        "entity_type": "concept",
        "description": (
            "Requirements not explicitly stated but expected by evaluators. Common sources: "
            "(1) Referenced documents - standards, DIDs, regulations incorporated by reference "
            "but not quoted, (2) Section M criteria without Section L instructions - evaluators "
            "expect content not explicitly required, (3) Industry standard practices - 'best "
            "practices' assumed without specification, (4) Customer history - expectations from "
            "prior contracts not documented in RFP, (5) Attachment/exhibit content - requirements "
            "buried in data tables or reference documents. Strategy: Read ALL referenced documents, "
            "map Section M to L to find gaps, leverage customer engagement for historical context."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Evaluation Reality
    # -------------------------------------------------------------------------
    {
        "entity_name": "Outstanding Rating Reality",
        "entity_type": "concept",
        "description": (
            "What actually earns 'Outstanding' or 'Exceptional' ratings in government evaluation. "
            "It requires: (1) Exceeding requirements with QUANTIFIED benefits - vague claims "
            "don't count, (2) Innovation that reduces risk or cost for government - not just "
            "different, demonstrably better, (3) Exceptional relevant past performance - recent, "
            "similar, documented success, (4) Proof points substantiating every major claim, "
            "(5) Clear linkage to evaluation criteria - evaluator must easily trace your "
            "strengths to scoring factors. 'Outstanding' is rare - most proposals score "
            "'Good' or 'Acceptable'. Achieving it requires investment in discriminator "
            "development and substantiation, not just good writing."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Evaluator Perspective Understanding",
        "entity_type": "concept",
        "description": (
            "Understanding government evaluator mindset improves proposal effectiveness. "
            "Evaluator reality: (1) They have many proposals to review under time pressure, "
            "(2) They score based on criteria - if your strength isn't in criteria, it won't "
            "help, (3) They need easy-to-find evidence - buried proof points get missed, "
            "(4) They document findings with proposal citations - make their job easy, "
            "(5) They compare across proposals - relative strength matters, (6) They are "
            "risk-averse - unsubstantiated claims raise concerns. Write to help evaluators "
            "find your strengths quickly. Use clear headings, call-out boxes, and explicit "
            "criteria mapping. Don't make them hunt for compliance."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Past Performance Relevance Reality",
        "entity_type": "concept",
        "description": (
            "What makes past performance truly 'relevant' in government evaluation. Relevance "
            "factors: (1) Similar scope - same type of work, not just same industry, "
            "(2) Similar complexity - comparable technical challenges, (3) Similar size - "
            "within same order of magnitude (can you scale up?), (4) Similar customer - "
            "government preferred over commercial, same agency best, (5) Recency - typically "
            "within 3-5 years, (6) Same key personnel - performance follows people, not just "
            "companies. Partial relevance can be addressed with explanation: 'While contract "
            "X was 50% smaller, the technical approach and challenges were identical.' "
            "Completely irrelevant references waste evaluation space."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Contract Type Insights
    # -------------------------------------------------------------------------
    {
        "entity_name": "Recompete Strategy Distinctions",
        "entity_type": "concept",
        "description": (
            "Strategic differences between competing as incumbent vs. challenger. As incumbent: "
            "(1) Emphasize continuity and mission knowledge, (2) Highlight performance record "
            "with specific metrics, (3) Propose retained staff for seamless transition, "
            "(4) Address any negative CPARS proactively with corrective actions, (5) Don't be "
            "complacent - many incumbents lose to hungrier challengers. As challenger: "
            "(1) Emphasize fresh perspective and innovation, (2) Ghost incumbent weaknesses "
            "subtly, (3) Recruit key incumbent staff for your team, (4) Provide detailed "
            "transition plan reducing risk, (5) Offer competitive pricing (incumbents often "
            "price high). Incumbents win ~60-70% of recompetes - advantage but not guarantee."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Set-Aside Strategy Considerations",
        "entity_type": "concept",
        "description": (
            "Strategic considerations for small business set-aside competitions. Set-aside "
            "types: 8(a), HUBZone, WOSB/EDWOSB, SDVOSB, small business general. Key strategies: "
            "(1) Verify and document size status/certifications before proposal, (2) Understand "
            "limitations on subcontracting (typically 50%+ prime must perform), (3) Teaming "
            "with large business mentor can strengthen capability without violating rules, "
            "(4) Focus on relevant small business past performance - large company experience "
            "of principals often doesn't transfer, (5) Price competitively - other small "
            "businesses are likely pricing aggressively. Small business evaluations often "
            "emphasize capability/experience due to limited track records."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "IDIQ Task Order Strategy",
        "entity_type": "concept",
        "description": (
            "Strategy distinctions for IDIQ task order competitions vs. standalone contracts. "
            "IDIQ advantages: Faster procurement (pre-qualified), smaller competition pool "
            "(only contract holders). Task order strategies: (1) Win the umbrella IDIQ first - "
            "you can't compete for TOs without it, (2) Track upcoming TOs through forecasts "
            "and customer engagement, (3) Short response times demand ready-to-go content "
            "library, (4) Build relationships across ordering agencies, (5) Accumulate task "
            "order performance for umbrella recompete. Fair Opportunity requirements still "
            "apply - don't assume easy wins. Many agencies have 'go-to' contractors on their "
            "vehicles based on prior TO performance."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Industry-Specific Insights
    # -------------------------------------------------------------------------
    {
        "entity_name": "IT Services Proposal Patterns",
        "entity_type": "concept",
        "description": (
            "Patterns specific to IT services federal proposals. Common evaluation focus areas: "
            "(1) Cybersecurity compliance (CMMC, NIST 800-171, FedRAMP) - often mandatory, "
            "(2) Agile/DevSecOps methodology - demonstrate iterative approach with CI/CD, "
            "(3) Cloud migration experience - show AWS/Azure GovCloud expertise, (4) Modernization "
            "approach - legacy system migration and technical debt reduction, (5) Automation - "
            "AI/ML, RPA for efficiency gains. IT-specific staffing: Show current certifications "
            "(Security+, AWS, Scrum), technical screening processes, retention programs for "
            "cleared personnel. Price realism important - unrealistic rates suggest misunderstanding "
            "of cleared IT labor market."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Professional Services Proposal Patterns",
        "entity_type": "concept",
        "description": (
            "Patterns specific to professional/advisory services federal proposals. Common focus: "
            "(1) Key personnel qualifications - specific individuals matter more than company "
            "capability, (2) Domain expertise - agency-specific knowledge, policy understanding, "
            "(3) Methodology - structured approaches to analysis, facilitation, reporting, "
            "(4) Deliverable quality - writing samples, report examples demonstrate capability, "
            "(5) Stakeholder management - experience with senior government leadership. "
            "Professional services often use labor-hour contracts with ceiling prices. "
            "Demonstrate value through past deliverable impact, not just activity completion. "
            "Strong resumes and client references particularly important."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# RELATIONSHIPS: Lessons Learned Connections
# =============================================================================

RELATIONSHIPS = [
    # Proposal pitfall relationships
    {
        "src_id": "Common Proposal Disqualification Causes",
        "tgt_id": "Ambiguous Requirement Red Flags",
        "description": "Ambiguous requirements increase risk of disqualification if misinterpreted",
        "keywords": "INCREASES_RISK RELATED_TO",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Hidden Requirement Patterns",
        "tgt_id": "Common Proposal Disqualification Causes",
        "description": "Missing hidden requirements can cause disqualification",
        "keywords": "CAUSES CONTRIBUTES_TO",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Evaluation reality relationships
    {
        "src_id": "Outstanding Rating Reality",
        "tgt_id": "Evaluator Perspective Understanding",
        "description": "Understanding evaluator perspective essential for achieving outstanding ratings",
        "keywords": "REQUIRES INFORMED_BY",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Past Performance Relevance Reality",
        "tgt_id": "Evaluator Perspective Understanding",
        "description": "Evaluators assess relevance - understanding their criteria improves reference selection",
        "keywords": "INFORMED_BY SUPPORTS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Contract type relationships
    {
        "src_id": "Recompete Strategy Distinctions",
        "tgt_id": "Past Performance Relevance Reality",
        "description": "Recompete strategy leverages incumbent past performance advantage",
        "keywords": "LEVERAGES USES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Set-Aside Strategy Considerations",
        "tgt_id": "Past Performance Relevance Reality",
        "description": "Set-aside past performance must come from small business entity",
        "keywords": "CONSTRAINS AFFECTS",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "IDIQ Task Order Strategy",
        "tgt_id": "Recompete Strategy Distinctions",
        "description": "Task order performance affects umbrella contract recompete positioning",
        "keywords": "RELATED_TO INFORMS",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Industry pattern relationships
    {
        "src_id": "IT Services Proposal Patterns",
        "tgt_id": "Outstanding Rating Reality",
        "description": "IT proposals need IT-specific discriminators for outstanding ratings",
        "keywords": "APPLIES_TO SPECIALIZES",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Professional Services Proposal Patterns",
        "tgt_id": "Outstanding Rating Reality",
        "description": "Professional services proposals need domain expertise discriminators",
        "keywords": "APPLIES_TO SPECIALIZES",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Lessons Learned Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Compliance Review Checklist - Top 10 Disqualification Risks: Before final "
            "submission, verify: (1) Every Section L 'shall' requirement addressed with "
            "proposal page reference, (2) Page counts within limits for ALL volumes, "
            "(3) File formats exactly as specified (PDF, Word, Excel), (4) Font size, "
            "margins, spacing per RFP instructions, (5) All required forms included and "
            "properly completed, (6) Certifications and representations signed and dated, "
            "(7) Pricing in correct CLIN format with accurate arithmetic, (8) Past performance "
            "questionnaires sent to references with adequate response time, (9) Proposal "
            "uploaded to correct portal before deadline (not at deadline), (10) Confirmation "
            "receipt obtained and saved. One missed item can eliminate an otherwise winning proposal."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "The Evaluator's Day Reality: Government evaluators typically review 5-15 proposals "
            "over 2-4 weeks while maintaining their regular job duties. They score using "
            "evaluation sheets with specific criteria and must document findings with proposal "
            "citations. What this means for you: (1) Make compliance obvious - use RFP section "
            "numbers as your headings, (2) Put key points first in each section - they may skim, "
            "(3) Use call-out boxes and bold text for discriminators - help them find strengths, "
            "(4) Provide specific page references in your compliance matrix, (5) Avoid marketing "
            "fluff that wastes their time - they want facts and evidence, (6) Number your "
            "paragraphs for easy citation in their notes. Help evaluators help you win."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Incumbent Trap Warning: Many incumbents lose recompetes due to overconfidence. "
            "Danger signs: (1) Assuming past performance speaks for itself without explicit "
            "documentation, (2) Proposing same approach without innovation or improvement, "
            "(3) Pricing high based on 'they know our value' assumption, (4) Dismissing "
            "challenger capabilities without proper Black Hat analysis, (5) Relying on "
            "relationships that may have changed with customer personnel turnover, (6) Not "
            "addressing any performance issues head-on with corrective action narrative. "
            "Winning strategy as incumbent: Treat recompete like new business opportunity "
            "while leveraging incumbent advantages (mission knowledge, staff continuity, "
            "performance metrics). Never be complacent - hungry challengers are working harder."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
