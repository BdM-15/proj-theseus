"""
Capture Management Knowledge Module

Evergreen knowledge about capture strategy:
- Bid/No-Bid decision frameworks
- Win theme development
- Customer hot buttons and discriminators
- Competitive positioning
- Pwin calculation

Entity types: strategic_theme, concept
Source: Shipley methodology, APMP, industry best practices

Note: These are FRAMEWORKS and APPROACHES, not specific capture plans.
RFP-specific capture intelligence comes from document extraction.
"""

SOURCE_ID = "govcon_ontology_capture"
FILE_PATH = "capture_management"


# =============================================================================
# ENTITIES: Capture Management Knowledge
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # Bid/No-Bid Decision
    # -------------------------------------------------------------------------
    {
        "entity_name": "Bid No-Bid Decision Framework",
        "entity_type": "concept",
        "description": (
            "Structured decision process for opportunity qualification. Key criteria: "
            "(1) Strategic fit - aligns with corporate capabilities and growth strategy, "
            "(2) Customer relationship - existing intimacy and access for shaping, "
            "(3) Competitive position - realistic chance of winning vs. field, "
            "(4) Resource availability - can staff pursuit and execution, "
            "(5) Contract profitability - acceptable terms and pricing opportunity, "
            "(6) Pwin assessment - probability of win exceeds threshold (typically 40-50%). "
            "Gate review typically requires executive approval. Decline decisions should "
            "be documented for lessons learned. Avoid 'hope' bids consuming B&P resources."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Pwin Probability Assessment",
        "entity_type": "concept",
        "description": (
            "Probability of Win (Pwin) quantifies likelihood of contract award. Assessment "
            "factors: (1) Customer relationship strength (25-30% weight) - access, incumbency, "
            "past performance rating, (2) Solution fit (25-30%) - technical capability, "
            "understanding of requirements, innovation, (3) Competitive position (20-25%) - "
            "discriminators, ghosting opportunities, incumbent vulnerabilities, (4) Price "
            "competitiveness (15-20%) - realistic pricing vs. likely competition. Pwin scale: "
            "<30% = unlikely pursue, 30-50% = pursue with mitigation, >50% = strong pursuit. "
            "Re-assess Pwin at each gate as intelligence improves."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Opportunity Shaping Strategy",
        "entity_type": "concept",
        "description": (
            "Pre-RFP activities to influence requirements in your favor. Shaping tactics: "
            "(1) Customer engagement - meetings, capability briefings, white papers to seed "
            "requirements favoring your solution, (2) Draft RFP comments - formal submission "
            "suggesting requirement changes, (3) Industry day participation - demonstrate "
            "capabilities and build relationships, (4) Teaming announcements - signal strength "
            "to customer and competitors, (5) Competitive intelligence - understand likely "
            "competition to position differentiators. Best shaping occurs 12-18 months before "
            "RFP. Opportunities 'wired' for competitors may require shaping to level playing field."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Win Themes and Discriminators
    # -------------------------------------------------------------------------
    {
        "entity_name": "Customer Hot Button Identification",
        "entity_type": "customer_priority",
        "description": (
            "Hot buttons are customer's highest-priority concerns driving evaluation decisions. "
            "Identification methods: (1) RFP emphasis analysis - words like 'critical', "
            "'essential', 'paramount' signal priorities, (2) Evaluation weight analysis - "
            "highest-weighted factors indicate hot buttons, (3) Customer interaction - direct "
            "statements of concerns and priorities, (4) Historical patterns - issues on prior "
            "contracts, audit findings, mission failures. Win themes must address hot buttons "
            "directly. Example hot buttons: mission continuity, cyber security, small business "
            "participation, transition risk, innovation. Validate hot button assumptions through "
            "customer engagement."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Discriminator Development",
        "entity_type": "strategic_theme",
        "description": (
            "Discriminators are unique strengths that differentiate from competitors. "
            "Effective discriminators are: (1) Customer-valued - addresses hot buttons or "
            "evaluation criteria, (2) Differentiating - competitors cannot easily claim same, "
            "(3) Provable - supported by evidence (past performance, certifications, metrics), "
            "(4) Believable - credible given your organization's capabilities. Discriminator "
            "sources: proprietary technology, unique past performance, key personnel, "
            "teaming arrangements, innovative approaches, price advantages. Validate "
            "discriminators through Black Hat review - if competitors can neutralize, "
            "it's not a true discriminator. Each proposal should have 3-5 strong discriminators."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "theme_type": "DISCRIMINATOR"
    },
    {
        "entity_name": "Proof Point Development",
        "entity_type": "strategic_theme",
        "description": (
            "Proof points are concrete evidence supporting claims in win themes. Types: "
            "(1) Past performance examples - specific contracts demonstrating capability "
            "with quantified results, (2) Metrics and statistics - measurable achievements "
            "(e.g., '99.7% on-time delivery'), (3) Certifications and credentials - CMMI, "
            "ISO, professional certifications, (4) Customer testimonials - quotes or letters "
            "from satisfied customers, (5) Third-party validation - analyst reports, awards, "
            "industry recognition. Every claim needs supporting proof. Weak proof points: "
            "generic statements, unquantified claims, outdated examples. Strong proof points: "
            "recent, relevant, quantified, from similar customers."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "theme_type": "PROOF_POINT"
    },
    
    # -------------------------------------------------------------------------
    # Competitive Positioning
    # -------------------------------------------------------------------------
    {
        "entity_name": "Incumbent Analysis Strategy",
        "entity_type": "concept",
        "description": (
            "Incumbent contractors have significant advantages requiring specific counter-"
            "strategies. Incumbent advantages: customer relationships, performance history, "
            "staff familiarity, no transition risk, inside knowledge. Counter-strategies: "
            "(1) Ghosting incumbent weaknesses (delays, quality issues, customer complaints), "
            "(2) Emphasizing fresh perspective and innovation, (3) Offering key incumbent staff "
            "on your team, (4) Reducing transition risk with detailed plans, (5) Highlighting "
            "relevant past performance from similar environments. If you are incumbent: "
            "emphasize continuity, mission knowledge, and performance record while ghosting "
            "challenger risks. Research incumbent performance through CPARS, protests, news."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Teaming Strategy Development",
        "entity_type": "concept",
        "description": (
            "Teaming arrangements to fill capability gaps and strengthen competitive position. "
            "Teaming types: Prime-Sub (most common), Joint Venture, Mentor-Protégé, CTA "
            "(Contractor Team Arrangement). Selection criteria: (1) Complementary capabilities "
            "filling your gaps, (2) Compatible cultures and working relationships, (3) Past "
            "performance relevance, (4) Price competitiveness, (5) Small business status if "
            "set-aside. Teaming agreement terms: exclusivity, work share, IP rights, B&P cost "
            "sharing. Announce teaming strategically to signal strength. Avoid over-teaming "
            "that dilutes prime capability or creates management complexity."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Price to Win Analysis",
        "entity_type": "concept",
        "description": (
            "Price-to-Win (PTW) estimates competitive price point needed to win. PTW inputs: "
            "(1) Government estimate (IGCE) if known or estimable, (2) Incumbent pricing from "
            "contract data or estimates, (3) Competitor cost structures and pricing behaviors, "
            "(4) Award basis (LPTA requires lowest; best value allows premium). PTW process: "
            "Estimate total evaluated price for top 2-3 competitors, determine price point "
            "to beat best competitor by 5-10% for LPTA or establish competitive range for "
            "tradeoff. PTW drives staffing efficiency decisions and teaming cost targets. "
            "Update PTW as intelligence improves. Balance PTW with realistic cost/execution."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Capture Planning
    # -------------------------------------------------------------------------
    {
        "entity_name": "Capture Plan Development",
        "entity_type": "concept",
        "description": (
            "Capture Plan documents strategy for winning specific opportunity. Key sections: "
            "(1) Executive Summary - opportunity overview and win strategy synopsis, "
            "(2) Opportunity Analysis - requirements, timeline, evaluation approach, "
            "(3) Customer Analysis - hot buttons, relationships, buying history, "
            "(4) Competitive Analysis - Black Hat results, ghosting strategy, "
            "(5) Win Strategy - themes, discriminators, solution approach, "
            "(6) Team Strategy - teaming partners, work allocation, key personnel, "
            "(7) Price Strategy - PTW, cost targets, pricing approach, "
            "(8) Action Plan - milestones, gate reviews, customer engagement calendar. "
            "Living document updated as intelligence evolves."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Customer Call Planning",
        "entity_type": "concept",
        "description": (
            "Structured customer engagement during capture phase. Call planning elements: "
            "(1) Objectives - specific intelligence or relationship goals, (2) Attendees - "
            "appropriate seniority matching customer, (3) Key messages - 2-3 themes to convey, "
            "(4) Questions - intelligence gaps to fill, (5) Materials - leave-behinds, capability "
            "briefs, (6) Follow-up - documented outcomes and next steps. Call etiquette: "
            "focus on customer needs not sales pitch, listen more than talk, avoid procurement "
            "sensitive topics during blackout. Track all customer interactions in capture log. "
            "Pre-RFP customer access is competitive advantage - use it strategically."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# RELATIONSHIPS: Capture Management Connections
# =============================================================================

RELATIONSHIPS = [
    # Bid decision relationships
    {
        "src_id": "Bid No-Bid Decision Framework",
        "tgt_id": "Pwin Probability Assessment",
        "description": "Bid/No-Bid decision relies on Pwin assessment as key criterion",
        "keywords": "REQUIRES USES",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Opportunity Shaping Strategy",
        "tgt_id": "Pwin Probability Assessment",
        "description": "Effective shaping increases Pwin by improving competitive position",
        "keywords": "IMPROVES INFLUENCES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Win theme relationships
    {
        "src_id": "Customer Hot Button Identification",
        "tgt_id": "Discriminator Development",
        "description": "Discriminators must address customer hot buttons to be effective",
        "keywords": "GUIDES INFORMS",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Discriminator Development",
        "tgt_id": "Proof Point Development",
        "description": "Every discriminator requires supporting proof points",
        "keywords": "REQUIRES SUPPORTED_BY",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Proof Point Development",
        "tgt_id": "Pwin Probability Assessment",
        "description": "Strong proof points increase credibility and Pwin",
        "keywords": "SUPPORTS IMPROVES",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Competitive relationships
    {
        "src_id": "Incumbent Analysis Strategy",
        "tgt_id": "Discriminator Development",
        "description": "Incumbent analysis identifies discriminator opportunities",
        "keywords": "INFORMS IDENTIFIES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Teaming Strategy Development",
        "tgt_id": "Discriminator Development",
        "description": "Teaming can create discriminators through complementary capabilities",
        "keywords": "ENABLES CREATES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Price to Win Analysis",
        "tgt_id": "Incumbent Analysis Strategy",
        "description": "PTW requires understanding incumbent pricing and cost structure",
        "keywords": "REQUIRES USES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Capture planning relationships
    {
        "src_id": "Capture Plan Development",
        "tgt_id": "Customer Hot Button Identification",
        "description": "Capture Plan documents customer hot buttons and response strategy",
        "keywords": "INCLUDES DOCUMENTS",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Capture Plan Development",
        "tgt_id": "Teaming Strategy Development",
        "description": "Capture Plan defines teaming approach and partner roles",
        "keywords": "INCLUDES DOCUMENTS",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Customer Call Planning",
        "tgt_id": "Customer Hot Button Identification",
        "description": "Customer calls validate and refine hot button understanding",
        "keywords": "VALIDATES DISCOVERS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Capture Management Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Pwin Assessment Scoring Example: Use weighted criteria to calculate Pwin. "
            "Customer Relationship (30%): Strong relationship from prior work = 0.8 × 30 = 24. "
            "Solution Fit (30%): Good fit with minor gaps = 0.7 × 30 = 21. "
            "Competitive Position (25%): Incumbent has advantage, we have discriminators = "
            "0.5 × 25 = 12.5. Price Competitiveness (15%): Likely competitive = 0.7 × 15 = 10.5. "
            "Total Pwin = 68%. Above 50% threshold, recommend pursuit. Document assumptions "
            "and re-assess at each gate as intelligence improves. Key risks: incumbent "
            "relationship strength, unknown competitor teaming."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Discriminator Validation Checklist: Before claiming a discriminator in your proposal, "
            "validate against these criteria: (1) Is it TRUE? Can you prove it with evidence? "
            "(2) Is it RELEVANT? Does it address evaluation criteria or hot buttons? "
            "(3) Is it UNIQUE? Can competitors credibly claim the same thing? "
            "(4) Is it BELIEVABLE? Will evaluators accept it given your track record? "
            "(5) Is it SUSTAINABLE? Can you maintain this advantage through contract execution? "
            "If any answer is 'No', either strengthen the discriminator or remove it. False or "
            "unsubstantiated discriminators undermine credibility when evaluators check claims."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Ghosting Techniques Best Practices: Ghosting raises evaluator concerns about "
            "competitors without naming them. Effective ghosting patterns: (1) Positive "
            "positioning: 'Our proven team delivers Day 1 capability without the learning "
            "curve risks of a transition' (ghosts lack of incumbent staff), (2) Comparative "
            "contrast: 'Unlike approaches requiring extensive customization, our COTS-based "
            "solution reduces risk' (ghosts competitor's custom development), (3) Risk "
            "highlighting: 'We mitigate key personnel risk through deep bench strength' "
            "(ghosts small company reliance on few key people). Never directly name or "
            "disparage competitors. Let evaluators draw conclusions from your strengths."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
