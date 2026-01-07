"""
GovCon Regulations Knowledge Module

Evergreen knowledge about federal contracting regulations:
- FAR (Federal Acquisition Regulation) compliance patterns
- DFARS (Defense FAR Supplement) requirements
- CMMC (Cybersecurity Maturity Model Certification)
- Section L/M best practices
- Compliance risk patterns

Entity types: requirement, concept, clause
Source: FAR.gov, DFARS, NIST SP 800-171

Note: These are PATTERNS and BEST PRACTICES, not specific clause text.
RFP-specific clauses come from document extraction.
"""

SOURCE_ID = "govcon_ontology_regulations"
FILE_PATH = "govcon_regulations"


# =============================================================================
# ENTITIES: Regulatory Knowledge
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # FAR Compliance
    # -------------------------------------------------------------------------
    {
        "entity_name": "FAR Compliance Best Practices",
        "entity_type": "concept",
        "description": (
            "Federal Acquisition Regulation compliance ensures proposals meet mandatory "
            "government contracting requirements. Best practices: (1) Map all incorporated "
            "FAR clauses early in proposal planning, (2) Identify clauses requiring specific "
            "proposal content (certifications, representations, past performance formats), "
            "(3) Flag clauses with post-award implications (reporting, subcontracting plans, "
            "IP rights), (4) Use compliance matrix to track clause-by-clause responsiveness. "
            "Non-compliance with mandatory clauses risks disqualification. Common pitfall: "
            "Overlooking clauses incorporated by reference in Section I."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "FAR Part 15 Competitive Negotiation",
        "entity_type": "concept",
        "description": (
            "FAR Part 15 governs competitive negotiated acquisitions, the primary method "
            "for complex government contracts. Key elements: (1) Formal source selection "
            "with evaluation factors, (2) Section L (Instructions) and Section M (Evaluation "
            "Criteria) structure, (3) Discussions and BAFOs permitted, (4) Best value "
            "tradeoff or LPTA award basis. Proposal strategy must align with stated "
            "evaluation approach - tradeoff procurements reward discriminators while "
            "LPTA rewards compliant low price. Understand FAR 15.305 evaluation guidance."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "FAR Part 12 Commercial Items",
        "entity_type": "concept",
        "description": (
            "FAR Part 12 provides streamlined acquisition procedures for commercial items "
            "and services. Simplified proposal requirements: may use commercial terms, "
            "limited cost/pricing data requirements, fewer certifications. However, "
            "commercial item determinations can be challenged. Strategy implications: "
            "Emphasize commercial availability and customary practices. Watch for "
            "FAR 52.212-4 (Contract Terms) modifications that add government-specific "
            "requirements negating commercial streamlining benefits."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # DFARS / Defense Contracting
    # -------------------------------------------------------------------------
    {
        "entity_name": "DFARS Cybersecurity Requirements",
        "entity_type": "requirement",
        "description": (
            "Defense Federal Acquisition Regulation Supplement cybersecurity requirements "
            "under DFARS 252.204-7012 mandate protection of Covered Defense Information (CDI). "
            "Contractors must: (1) Implement NIST SP 800-171 security controls, (2) Report "
            "cyber incidents within 72 hours, (3) Flow down requirements to subcontractors. "
            "Proposal implications: Describe SSP (System Security Plan), identify POA&Ms "
            "for control gaps, address FedRAMP for cloud services. Non-compliance is "
            "grounds for contract termination. CMMC certification increasingly required."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "criticality": "MANDATORY",
        "modal_verb": "shall"
    },
    {
        "entity_name": "CMMC Certification Framework",
        "entity_type": "concept",
        "description": (
            "Cybersecurity Maturity Model Certification (CMMC) replaces self-attestation "
            "with third-party verification of cybersecurity practices. CMMC 2.0 levels: "
            "Level 1 (foundational, 17 practices, self-assessment), Level 2 (advanced, "
            "110 practices from NIST 800-171, third-party assessment), Level 3 (expert, "
            "additional controls, government-led assessment). Solicitations specify required "
            "level. Proposal strategy: Document current certification status, assessment "
            "timeline for pending certifications, and flow-down to subcontractors. "
            "CMMC certification is becoming prerequisite for DoD contract eligibility."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "DFARS Subcontracting Requirements",
        "entity_type": "requirement",
        "description": (
            "DFARS and FAR subcontracting requirements for contracts exceeding thresholds. "
            "Key requirements: (1) Small Business Subcontracting Plan (FAR 52.219-9) with "
            "specific goals by category (SB, SDB, WOSB, HUBZone, SDVOSB), (2) Limitations "
            "on subcontracting (FAR 52.219-14) for set-aside contracts, (3) Consent to "
            "subcontract for certain subcontract types. Proposal must include realistic, "
            "achievable subcontracting goals with named subcontractors where possible. "
            "Small business participation often scored in evaluation."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "criticality": "MANDATORY",
        "modal_verb": "shall"
    },
    
    # -------------------------------------------------------------------------
    # Section L/M Structure
    # -------------------------------------------------------------------------
    {
        "entity_name": "Section L Proposal Instructions Analysis",
        "entity_type": "concept",
        "description": (
            "Section L contains proposal preparation instructions defining submission "
            "requirements. Analysis approach: (1) Extract all 'shall', 'must', 'will' "
            "requirements verbatim, (2) Identify page/volume limits per section, (3) Note "
            "format requirements (font, margins, file types), (4) Map required content "
            "elements to proposal outline, (5) Flag ambiguous instructions for clarification. "
            "Common pitfalls: Missing 'hidden' requirements buried in instructions, "
            "exceeding page limits, wrong file formats. Use compliance matrix to track "
            "every instruction. Section L drives proposal STRUCTURE."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Section M Evaluation Criteria Analysis",
        "entity_type": "concept",
        "description": (
            "Section M defines how proposals will be evaluated and the basis for award. "
            "Analysis approach: (1) Identify all evaluation factors and subfactors, "
            "(2) Note relative importance/weights if stated, (3) Understand rating scales "
            "(Outstanding/Good/Acceptable/Poor or Exceptional/Acceptable/Unacceptable), "
            "(4) Map evaluation criteria to Section L instructions, (5) Identify discriminating "
            "factors where exceeding requirements adds value. Section M drives proposal "
            "STRATEGY - allocate effort proportional to evaluation weights. Highest-weighted "
            "factors should receive most pages and strongest discriminators."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Best Value Tradeoff Analysis",
        "entity_type": "concept",
        "description": (
            "Best value tradeoff procurements allow government to pay more for proposals "
            "offering higher non-price value. Tradeoff analysis determines whether "
            "technical/management superiority justifies price premium over lower-priced "
            "offers. Strategy implications: (1) Emphasize discriminators justifying premium, "
            "(2) Quantify risk reduction and value-added benefits, (3) Ensure discriminators "
            "align with stated evaluation factors, (4) Price must be 'fair and reasonable' "
            "but need not be lowest. Contrast with LPTA where lowest compliant price wins."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Compliance Risk Patterns
    # -------------------------------------------------------------------------
    {
        "entity_name": "Organizational Conflict of Interest",
        "entity_type": "concept",
        "description": (
            "OCI occurs when contractor's relationships or activities impair objectivity "
            "or provide unfair competitive advantage. Three OCI types: (1) Biased ground "
            "rules - contractor sets requirements it will compete to meet, (2) Impaired "
            "objectivity - contractor evaluates its own work, (3) Unequal access to "
            "information - contractor has non-public data advantaging its proposal. "
            "Proposals must disclose potential OCIs and mitigation plans. FAR 9.5 governs. "
            "Undisclosed OCI can result in proposal rejection or contract termination."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Contractor Performance Assessment Reporting",
        "entity_type": "concept",
        "description": (
            "CPARS (Contractor Performance Assessment Reporting System) provides historical "
            "performance data accessed during proposal evaluation. Past performance ratings: "
            "Exceptional, Very Good, Satisfactory, Marginal, Unsatisfactory. Proposal "
            "implications: (1) Reference contracts with strong CPARS ratings, (2) Address "
            "any negative ratings with corrective action narrative, (3) For new contractors, "
            "emphasize relevant commercial experience. Past performance typically 20-30% "
            "of evaluation weight. Relevance and recency of references matter significantly."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# RELATIONSHIPS: Regulatory Connections
# =============================================================================

RELATIONSHIPS = [
    # L/M Mapping relationships
    {
        "src_id": "Section L Proposal Instructions Analysis",
        "tgt_id": "Section M Evaluation Criteria Analysis",
        "description": "Section L instructions must map to Section M evaluation criteria for compliance",
        "keywords": "MAPS_TO ALIGNS_WITH",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Section M Evaluation Criteria Analysis",
        "tgt_id": "Best Value Tradeoff Analysis",
        "description": "Section M criteria guide Best Value Tradeoff decisions",
        "keywords": "INFORMS GUIDES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # FAR relationships
    {
        "src_id": "FAR Compliance Best Practices",
        "tgt_id": "FAR Part 15 Competitive Negotiation",
        "description": "FAR compliance encompasses Part 15 competitive negotiation requirements",
        "keywords": "INCLUDES ENCOMPASSES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "FAR Compliance Best Practices",
        "tgt_id": "FAR Part 12 Commercial Items",
        "description": "FAR compliance encompasses Part 12 commercial item procedures",
        "keywords": "INCLUDES ENCOMPASSES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # DFARS/Security relationships
    {
        "src_id": "DFARS Cybersecurity Requirements",
        "tgt_id": "CMMC Certification Framework",
        "description": "DFARS cybersecurity requirements implemented through CMMC certification",
        "keywords": "IMPLEMENTED_BY VALIDATED_BY",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "DFARS Subcontracting Requirements",
        "tgt_id": "DFARS Cybersecurity Requirements",
        "description": "Cybersecurity requirements must flow down per subcontracting requirements",
        "keywords": "RELATED_TO FLOWS_TO",
        "weight": 0.8,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Compliance relationships
    {
        "src_id": "Contractor Performance Assessment Reporting",
        "tgt_id": "Section M Evaluation Criteria Analysis",
        "description": "CPARS ratings directly impact past performance evaluation factor scoring",
        "keywords": "IMPACTS EVALUATED_BY",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Organizational Conflict of Interest",
        "tgt_id": "FAR Compliance Best Practices",
        "description": "OCI management is critical FAR compliance requirement",
        "keywords": "COMPONENT_OF REQUIRES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Regulatory Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Section L/M Alignment Strategy: Before writing any proposal content, create "
            "a comprehensive mapping between Section L instructions and Section M evaluation "
            "criteria. Identify: (1) One-to-one mappings where instruction directly addresses "
            "criterion, (2) Many-to-one mappings where multiple instructions feed single "
            "criterion, (3) Orphan instructions with no evaluation criterion (compliance-only, "
            "minimize effort), (4) Orphan criteria with no explicit instructions (hidden "
            "requirements needing creative response). Allocate page budget and author effort "
            "proportional to evaluation weights. A factor worth 40% of evaluation should "
            "receive approximately 40% of proposal attention."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "DFARS Cybersecurity Compliance Checklist: (1) Identify if contract involves "
            "CUI/CDI - check DD Form 254 and contract clauses, (2) Verify DFARS 252.204-7012 "
            "applicability, (3) Document current NIST 800-171 implementation status, "
            "(4) Prepare System Security Plan (SSP) for proposal, (5) Identify POA&Ms "
            "for any control gaps with realistic remediation timelines, (6) Determine CMMC "
            "level required and certification status, (7) Map subcontractor flow-down "
            "requirements, (8) Address cloud services FedRAMP requirements if applicable. "
            "Inadequate cybersecurity response is increasingly common cause of proposal weakness."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Past Performance Evaluation Best Practices: (1) Select references matching "
            "RFP's relevance criteria (similar scope, size, complexity, customer type), "
            "(2) Prioritize contracts with documented CPARS ratings of 'Very Good' or higher, "
            "(3) Verify reference POCs will respond positively to questionnaires, (4) Pre-brief "
            "references on key themes you want them to emphasize, (5) For any negative "
            "performance history, prepare narrative explaining circumstances and corrective "
            "actions taken, (6) New entrants should emphasize relevant commercial experience "
            "and key personnel credentials. Past performance neutral is better than negative past."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
