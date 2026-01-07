"""
Evaluation Methodology Knowledge Module

Evergreen knowledge about proposal evaluation:
- Rating scales and scoring approaches
- Evaluation factor patterns
- LPTA vs Best Value distinctions
- Strengths/Weaknesses/Deficiencies framework

Entity types: evaluation_factor, concept
Source: GAO bid protest decisions, FAR guidance

Note: These are evaluation PATTERNS, not specific RFP evaluation criteria.
RFP-specific evaluation factors come from document extraction.
"""

SOURCE_ID = "govcon_ontology_evaluation"
FILE_PATH = "evaluation_methodology"


# =============================================================================
# ENTITIES: Evaluation Knowledge
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # Rating Scales
    # -------------------------------------------------------------------------
    {
        "entity_name": "Adjectival Rating Scale Patterns",
        "entity_type": "concept",
        "description": (
            "Government evaluators use standardized adjectival scales to rate proposals. "
            "Common 5-level scale: Outstanding (significantly exceeds requirements with "
            "exceptional benefit), Good (exceeds requirements with benefit), Acceptable "
            "(meets requirements), Marginal (fails to meet some requirements, correctable), "
            "Unacceptable (fails to meet requirements, not correctable). Alternative 4-level: "
            "Exceptional, Acceptable, Marginal, Unacceptable. Understanding rating definitions "
            "guides discriminator development - 'Acceptable' is minimum; 'Outstanding' requires "
            "exceeding requirements with quantified benefits. Target discriminators that move "
            "ratings from Acceptable to Good/Outstanding."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Confidence Rating Patterns",
        "entity_type": "concept",
        "description": (
            "Performance risk assessment uses confidence ratings indicating evaluator's "
            "belief in offeror's ability to perform. Scale: High Confidence (no doubt "
            "offeror can perform), Significant Confidence (little doubt), Satisfactory "
            "Confidence (some doubt but acceptable risk), Limited Confidence (substantial "
            "doubt, risk mitigation needed), No Confidence (extreme doubt, likely failure). "
            "Past performance and management approach primarily drive confidence ratings. "
            "Proposal strategy: Provide proof points reducing evaluator doubt about "
            "execution capability. Relevant past performance is strongest confidence builder."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Color Rating System",
        "entity_type": "concept",
        "description": (
            "Some agencies use color codes for evaluation ratings. Common pattern: "
            "Blue/Purple (Exceptional - exceeds requirements with significant benefit), "
            "Green (Acceptable - meets requirements), Yellow (Marginal - potentially "
            "correctable deficiencies), Red (Unacceptable - material deficiencies). "
            "May combine with risk colors: Green (low), Yellow (moderate), Red (high). "
            "Color ratings often converted to point scores for tradeoff analysis. "
            "Strategy: Target 'Blue' ratings on highest-weighted factors where "
            "discrimination justifies potential price premium."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Evaluation Factor Patterns
    # -------------------------------------------------------------------------
    {
        "entity_name": "Technical Approach Evaluation Factor",
        "entity_type": "evaluation_factor",
        "description": (
            "Technical Approach evaluates solution quality, methodology, and innovation. "
            "Common subfactors: Understanding of requirements (demonstrates grasp of customer "
            "needs), Technical solution (approach to meeting requirements), Staffing "
            "(qualifications and availability of proposed personnel), Management (organization, "
            "processes, quality control). Outstanding ratings require: innovative solutions "
            "beyond minimum requirements, quantified benefits, risk mitigation approaches, "
            "and proof points from similar work. This factor typically carries highest weight "
            "in best-value procurements (30-50%)."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "weight": "30-50%",
        "importance": "Often most heavily weighted"
    },
    {
        "entity_name": "Past Performance Evaluation Factor",
        "entity_type": "evaluation_factor",
        "description": (
            "Past Performance evaluates historical contractor performance as predictor of "
            "future performance. Evaluation criteria: relevance (similarity to current "
            "requirement in scope, size, complexity), recency (typically within 3-5 years), "
            "quality (CPARS ratings, customer satisfaction). Evaluators contact references "
            "and review CPARS database. Neutral rating given to offerors with no relevant "
            "past performance - not negative, but not positive. Strategy: Select most "
            "relevant references, pre-brief reference POCs, address any performance issues "
            "with corrective action narrative. Typically 15-30% of evaluation weight."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "weight": "15-30%",
        "importance": "Critical predictor of future success"
    },
    {
        "entity_name": "Management Approach Evaluation Factor",
        "entity_type": "evaluation_factor",
        "description": (
            "Management Approach evaluates organizational capability to execute contract. "
            "Common subfactors: Program management (structure, reporting, governance), "
            "Quality assurance (QC/QA processes, continuous improvement), Risk management "
            "(identification, mitigation, monitoring), Transition planning (mobilization, "
            "knowledge transfer). Outstanding ratings require: detailed management plans "
            "with proven processes, organizational charts with named personnel, risk "
            "registers with quantified mitigation, realistic schedules with dependencies. "
            "Often evaluated alongside Technical Approach or as separate factor (15-25%)."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "weight": "15-25%",
        "importance": "Demonstrates execution capability"
    },
    {
        "entity_name": "Price Cost Evaluation Factor",
        "entity_type": "evaluation_factor",
        "description": (
            "Price/Cost evaluation assesses proposed pricing for reasonableness, realism, "
            "and balance. Not rated adjectivally - evaluated numerically and analyzed for: "
            "Price reasonableness (comparison to IGCE, other offers, market rates), Cost "
            "realism (for cost-reimbursement - can work be done for proposed cost?), Price "
            "balance (no front-loading or material unbalancing). For LPTA: lowest technically "
            "acceptable price wins. For tradeoff: price premium must be justified by technical "
            "superiority. Include credible Basis of Estimate (BOE) documentation. Unrealistically "
            "low prices raise performance risk concerns."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "weight": "Varies by award type",
        "importance": "LPTA: Determines winner; Tradeoff: Weighed against technical"
    },
    
    # -------------------------------------------------------------------------
    # Strengths/Weaknesses/Deficiencies
    # -------------------------------------------------------------------------
    {
        "entity_name": "Evaluation Strengths",
        "entity_type": "concept",
        "description": (
            "Strengths are proposal aspects that exceed requirements or increase confidence "
            "in successful performance. Evaluators document strengths with specific citations "
            "to proposal content. Types: Significant Strengths (appreciably exceed requirements "
            "with substantial benefit), Strengths (exceed requirements or offer some benefit). "
            "Strategy for earning strengths: (1) Exceed stated requirements with quantified "
            "benefits, (2) Offer innovative approaches reducing risk, (3) Provide exceptional "
            "proof points from past performance, (4) Demonstrate deep customer understanding. "
            "Strengths justify higher adjectival ratings and price premiums in tradeoff."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Evaluation Weaknesses",
        "entity_type": "concept",
        "description": (
            "Weaknesses are proposal aspects that increase risk but do not preclude award. "
            "Weakness indicates lack of information or documentation, or unclear approach "
            "that raises evaluator concern. Weaknesses may be discussed during negotiations "
            "and corrected in final proposal revisions. Categories: Significant Weakness "
            "(appreciably increases risk of unsuccessful performance), Weakness (flaw or "
            "concern increasing risk). Strategy: Review proposal from evaluator perspective "
            "to identify potential weaknesses before submission. Address concerns preemptively "
            "with additional detail, proof points, or risk mitigation plans."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Evaluation Deficiencies",
        "entity_type": "concept",
        "description": (
            "Deficiencies are material failures to meet requirements that are not correctable "
            "or would require major proposal revision. A single deficiency typically results "
            "in 'Unacceptable' rating for that factor. Types of deficiencies: (1) Non-responsive - "
            "fails to address requirement, (2) Non-compliant - violates stated requirement, "
            "(3) Material misrepresentation - false or misleading information. Deficiencies "
            "usually cannot be discussed during negotiations without creating unfair advantage. "
            "Prevention: Rigorous compliance review at Pink Team ensuring every requirement "
            "is addressed. Red Team should flag any potential deficiencies for correction."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Award Types
    # -------------------------------------------------------------------------
    {
        "entity_name": "LPTA Award Methodology",
        "entity_type": "concept",
        "description": (
            "Lowest Price Technically Acceptable (LPTA) awards contract to lowest-priced "
            "offeror meeting minimum technical standards. No tradeoff between price and "
            "technical quality - either you meet the bar or you don't. LPTA appropriate when: "
            "requirements are well-defined, risk is minimal, and little value in exceeding "
            "requirements. Strategy: (1) Focus on compliance - meet but don't exceed, "
            "(2) Price to win - lowest compliant price wins, (3) Eliminate discriminators "
            "that add cost without evaluation benefit, (4) Ensure no weaknesses/deficiencies "
            "that would render proposal unacceptable. Innovation unrewarded in LPTA."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Best Value Tradeoff Methodology",
        "entity_type": "concept",
        "description": (
            "Best Value Tradeoff allows government to pay more for higher-quality proposals "
            "when benefits justify premium. Source Selection Authority (SSA) conducts tradeoff "
            "analysis comparing offers' strengths, weaknesses, and prices. Higher-rated but "
            "higher-priced offer may win if SSA documents that benefits warrant cost delta. "
            "Strategy: (1) Maximize strengths on highest-weighted factors, (2) Develop clear "
            "discriminators with quantified benefits, (3) Price realistically - not necessarily "
            "lowest but must be fair/reasonable, (4) Help evaluators justify your selection "
            "with concrete benefit statements. Understanding evaluation weights critical."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# RELATIONSHIPS: Evaluation Connections
# =============================================================================

RELATIONSHIPS = [
    # Rating relationships
    {
        "src_id": "Adjectival Rating Scale Patterns",
        "tgt_id": "Evaluation Strengths",
        "description": "Strengths drive higher adjectival ratings on evaluation factors",
        "keywords": "DETERMINES INFLUENCES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Adjectival Rating Scale Patterns",
        "tgt_id": "Evaluation Weaknesses",
        "description": "Weaknesses lower adjectival ratings and increase risk assessment",
        "keywords": "DETERMINES INFLUENCES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Evaluation Deficiencies",
        "tgt_id": "Adjectival Rating Scale Patterns",
        "description": "Deficiencies result in Unacceptable ratings",
        "keywords": "RESULTS_IN CAUSES",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Factor relationships
    {
        "src_id": "Technical Approach Evaluation Factor",
        "tgt_id": "Evaluation Strengths",
        "description": "Technical approach strengths from innovation and risk mitigation",
        "keywords": "EVALUATED_BY GENERATES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Past Performance Evaluation Factor",
        "tgt_id": "Confidence Rating Patterns",
        "description": "Past performance primarily drives confidence/risk ratings",
        "keywords": "DETERMINES INFLUENCES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Management Approach Evaluation Factor",
        "tgt_id": "Confidence Rating Patterns",
        "description": "Management approach affects confidence in execution capability",
        "keywords": "INFLUENCES SUPPORTS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Award methodology relationships
    {
        "src_id": "LPTA Award Methodology",
        "tgt_id": "Price Cost Evaluation Factor",
        "description": "LPTA awards based on lowest price among acceptable offers",
        "keywords": "DETERMINED_BY PRIORITIZES",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Best Value Tradeoff Methodology",
        "tgt_id": "Evaluation Strengths",
        "description": "Tradeoff analysis weighs strengths against price premium",
        "keywords": "WEIGHS CONSIDERS",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Best Value Tradeoff Methodology",
        "tgt_id": "Technical Approach Evaluation Factor",
        "description": "Best value tradeoff rewards technical superiority",
        "keywords": "REWARDS ENABLES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Evaluation Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Achieving Outstanding Ratings: To receive 'Outstanding' or 'Exceptional' ratings, "
            "proposals must significantly exceed requirements with quantified benefits and "
            "minimal risk. Strategies: (1) Exceed stated metrics by measurable amounts "
            "(e.g., '99.9% availability vs. required 99%'), (2) Offer innovative approaches "
            "that reduce customer risk or cost, (3) Provide exceptional past performance "
            "demonstrating similar achievements, (4) Include value-adds not required but "
            "beneficial to customer. Each strength must be specific, provable, and aligned "
            "with evaluation criteria. Generic claims without proof points won't generate "
            "documented strengths in evaluation reports."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Evaluation Factor Weighting Strategy: When RFP states evaluation weights, allocate "
            "proposal resources proportionally. Example: Technical Approach 50%, Past Performance "
            "25%, Price 25%. This means: (1) Technical volume gets most pages and strongest "
            "writers, (2) Past performance references carefully selected for relevance, "
            "(3) Price competitive but not necessarily lowest if technical superiority "
            "justifies premium. When weights unstated but order given (Technical more important "
            "than Past Performance more important than Price), apply decreasing weight estimate. "
            "When factors are 'equal,' treat Technical and Past Performance as 35-40% each, "
            "Price 20-30%. Always optimize for highest-weighted factors first."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "LPTA vs Best Value Decision Framework: Before developing proposal strategy, "
            "determine award basis from Section M. LPTA indicators: 'lowest price technically "
            "acceptable,' 'no tradeoff,' requirements clearly defined, commodity-like services. "
            "Best Value indicators: 'may pay more for higher quality,' 'tradeoff analysis,' "
            "technical factors 'significantly more important' than price, complex requirements. "
            "Hybrid approaches possible - some factors LPTA-like (meet threshold) while others "
            "allow tradeoff. Misreading award basis causes strategic errors: over-investing in "
            "LPTA (wasted cost) or under-investing in tradeoff (missed discriminators)."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
