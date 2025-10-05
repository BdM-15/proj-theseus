"""
Government Contracting Ontology-Guided LightRAG Prompts

Injects domain-specific entity types and relationship constraints into LightRAG's
extraction engine. Modifies LightRAG's generic prompts with government contracting
ontology to teach it RFP-specific concepts.

Purpose:
- Guide LightRAG entity extraction with EntityType enum
- Constrain relationships to VALID_RELATIONSHIPS schema
- Provide RFP-specific few-shot examples
- Prevent fictitious entity creation (Path A regression prevention)

Architecture Note:
This module does NOT bypass LightRAG - it MODIFIES LightRAG's extraction prompts
by injecting domain knowledge at the right extension points (addon_params, PROMPTS).

Phase 3 Updates:
- Added Example 4: Deliverable extraction (Section F) with DELIVERABLE entity type
- Demonstrates CLIN→DELIVERABLE, DELIVERABLE→EVENT (deadlines), and DELIVERABLE→LOCATION relationships

References:
- .venv/Lib/site-packages/lightrag/prompt.py: Prompt templates
- .venv/Lib/site-packages/lightrag/operate.py (line 2024): entity_types injection
- src/core/ontology.py: EntityType enum and VALID_RELATIONSHIPS schema
"""

from typing import List, Dict, Any
from core.ontology import (
    EntityType,
    RelationshipType,
    VALID_RELATIONSHIPS,
    get_valid_relationships_for_entity,
)


# ============================================================================
# GOVERNMENT CONTRACTING ENTITY TYPES (Ontology Injection)
# ============================================================================

def get_government_contracting_entity_types() -> List[str]:
    """
    Get government contracting entity types for LightRAG injection.
    
    Replaces generic LightRAG entity types (person, location, organization)
    with government contracting domain-specific types from our ontology.
    
    Returns:
        List of entity type strings for addon_params["entity_types"]
    
    Usage:
        rag = LightRAG(
            addon_params={
                "entity_types": get_government_contracting_entity_types()
            }
        )
    
    Injected into LightRAG at:
        .venv/Lib/site-packages/lightrag/operate.py line 2024:
        entity_types = global_config["addon_params"].get("entity_types", DEFAULT_ENTITY_TYPES)
    """
    return [entity_type.value for entity_type in EntityType]


# ============================================================================
# RFP-SPECIFIC FEW-SHOT EXAMPLES (Replacing Generic Examples)
# ============================================================================

def get_rfp_entity_extraction_examples() -> List[str]:
    """
    Get RFP-specific few-shot examples for entity extraction.
    
    Replaces LightRAG's generic examples (Alice, Bob, TechCorp) with
    government contracting patterns to teach domain concepts.
    
    Examples demonstrate:
    - Uniform Contract Format sections (A-M, J attachments)
    - Requirements classification (must/should/may)
    - FAR/DFARS clause identification
    - CLIN extraction
    - Section L↔M evaluation relationships
    
    Returns:
        List of formatted few-shot examples
    
    Usage:
        PROMPTS["entity_extraction_examples"] = get_rfp_entity_extraction_examples()
    """
    return [
        # Example 1: Section references and requirements
        """<Input Text>
```
Section L.3.2 requires that the offeror shall submit a Past Performance Volume
demonstrating similar contract experience. The proposal must address the
evaluation criteria specified in Section M.2.1.
```

<Output>
entity<|#|>Section L.3.2<|#|>SECTION<|#|>Section L.3.2 is an RFP section in Volume L (Instructions to Offerors) that specifies proposal submission requirements.
entity<|#|>Past Performance Volume<|#|>REQUIREMENT<|#|>Past Performance Volume is a required proposal section demonstrating contractor experience with similar contracts.
entity<|#|>Section M.2.1<|#|>SECTION<|#|>Section M.2.1 is an RFP section in Volume M (Evaluation Factors) that defines evaluation criteria.
entity<|#|>Offeror<|#|>ORGANIZATION<|#|>Offeror is the contractor or organization submitting a proposal in response to the RFP.
entity<|#|>Similar Contract Experience<|#|>CONCEPT<|#|>Similar contract experience refers to past work demonstrating capability to perform the required services.
relation<|#|>Section L.3.2<|#|>Past Performance Volume<|#|>requires, submission requirement<|#|>Section L.3.2 mandates submission of the Past Performance Volume as part of the proposal.
relation<|#|>Past Performance Volume<|#|>Similar Contract Experience<|#|>demonstrates, capability proof<|#|>The Past Performance Volume must demonstrate similar contract experience.
relation<|#|>Section L.3.2<|#|>Section M.2.1<|#|>references, evaluation linkage<|#|>Section L.3.2 references Section M.2.1 for corresponding evaluation criteria.
relation<|#|>Section M.2.1<|#|>Past Performance Volume<|#|>evaluates, scoring criteria<|#|>Section M.2.1 defines how the Past Performance Volume will be evaluated.
relation<|#|>Offeror<|#|>Past Performance Volume<|#|>responsible_for, proposal submission<|#|>The offeror is responsible for submitting the Past Performance Volume.
<|COMPLETE|>

""",
        # Example 2: CLINs and deliverables
        """<Input Text>
```
CLIN 0001 covers base year IT support services valued at $2,500,000. The contractor
shall provide monthly status reports as specified in Section C.3.1 and comply with
FAR Clause 52.215-2 regarding audit requirements.
```

<Output>
entity<|#|>CLIN 0001<|#|>CONCEPT<|#|>CLIN 0001 is Contract Line Item Number 0001, covering the base year period of performance.
entity<|#|>Base Year IT Support Services<|#|>REQUIREMENT<|#|>Base year IT support services are the core technical support services required in the first contract period.
entity<|#|>Monthly Status Reports<|#|>REQUIREMENT<|#|>Monthly status reports are required deliverables documenting project progress and performance metrics.
entity<|#|>Section C.3.1<|#|>SECTION<|#|>Section C.3.1 is an RFP section in the Statement of Work (SOW) defining specific deliverable requirements.
entity<|#|>FAR Clause 52.215-2<|#|>CLAUSE<|#|>FAR Clause 52.215-2 is a Federal Acquisition Regulation provision addressing audit and records requirements.
entity<|#|>$2,500,000<|#|>CONCEPT<|#|>$2,500,000 is the contract value for CLIN 0001 base year services.
entity<|#|>Contractor<|#|>ORGANIZATION<|#|>Contractor is the organization awarded the contract to perform IT support services.
relation<|#|>CLIN 0001<|#|>Base Year IT Support Services<|#|>covers, scope definition<|#|>CLIN 0001 defines the scope and funding for base year IT support services.
relation<|#|>CLIN 0001<|#|>$2,500,000<|#|>valued_at, contract pricing<|#|>CLIN 0001 is valued at $2,500,000 for the base year period.
relation<|#|>Section C.3.1<|#|>Monthly Status Reports<|#|>specifies, deliverable requirements<|#|>Section C.3.1 defines the format and content requirements for monthly status reports.
relation<|#|>Base Year IT Support Services<|#|>Monthly Status Reports<|#|>requires, deliverable obligation<|#|>IT support services require submission of monthly status reports.
relation<|#|>FAR Clause 52.215-2<|#|>CLIN 0001<|#|>applies_to, regulatory compliance<|#|>FAR Clause 52.215-2 audit requirements apply to CLIN 0001 performance.
relation<|#|>Contractor<|#|>Monthly Status Reports<|#|>responsible_for, deliverable submission<|#|>The contractor is responsible for providing monthly status reports.
<|COMPLETE|>

""",
        # Example 3: Compliance requirements and security
        """<Input Text>
```
All personnel performing under this contract must possess an active Secret security
clearance as mandated by DFARS 252.204-7012. The Government reserves the right to
conduct facility security inspections at the contractor's SCIF located in Arlington, VA.
```

<Output>
entity<|#|>Secret Security Clearance<|#|>REQUIREMENT<|#|>Secret security clearance is a required personnel qualification for accessing classified information under this contract.
entity<|#|>DFARS 252.204-7012<|#|>CLAUSE<|#|>DFARS 252.204-7012 is a Defense Federal Acquisition Regulation Supplement clause addressing safeguarding of covered defense information.
entity<|#|>Facility Security Inspections<|#|>EVENT<|#|>Facility security inspections are government-conducted reviews to verify compliance with security requirements.
entity<|#|>SCIF<|#|>LOCATION<|#|>SCIF (Sensitive Compartmented Information Facility) is a secure location for handling classified information.
entity<|#|>Arlington, VA<|#|>LOCATION<|#|>Arlington, VA is the geographic location of the contractor's SCIF facility.
entity<|#|>Government<|#|>ORGANIZATION<|#|>Government refers to the federal contracting agency with oversight authority.
entity<|#|>Contractor<|#|>ORGANIZATION<|#|>Contractor is the organization responsible for maintaining security compliance and cleared personnel.
entity<|#|>Personnel<|#|>PERSON<|#|>Personnel are individuals performing work under the contract who require security clearances.
relation<|#|>Personnel<|#|>Secret Security Clearance<|#|>requires, qualification<|#|>All personnel must possess an active Secret security clearance to perform contract work.
relation<|#|>DFARS 252.204-7012<|#|>Secret Security Clearance<|#|>mandates, regulatory requirement<|#|>DFARS 252.204-7012 mandates the Secret security clearance requirement.
relation<|#|>Government<|#|>Facility Security Inspections<|#|>conducts, oversight authority<|#|>The Government reserves the right to conduct facility security inspections.
relation<|#|>SCIF<|#|>Arlington, VA<|#|>located_in, geographic location<|#|>The contractor's SCIF is located in Arlington, VA.
relation<|#|>Facility Security Inspections<|#|>SCIF<|#|>targets, inspection scope<|#|>Facility security inspections will be conducted at the contractor's SCIF.
relation<|#|>Contractor<|#|>SCIF<|#|>operates, facility ownership<|#|>The contractor operates the SCIF facility in Arlington, VA.
<|COMPLETE|>

""",
        # Example 4: Deliverables and Section F (Phase 3 - DELIVERABLE entity)
        """<Input Text>
```
Section F.3.1 - Deliverable Schedule. The contractor shall provide the following deliverables
under CLIN 0001: (1) Monthly Status Reports due by the 5th business day of each month,
(2) Quarterly Technical Review Briefings presented at the Government site in Arlington, VA,
and (3) Final System Documentation delivered within 30 days of contract completion.
All deliverables must comply with Section C.4 formatting requirements.
```

<Output>
entity<|#|>Section F.3.1<|#|>SECTION<|#|>Section F.3.1 is an RFP section defining the deliverable schedule under FAR 15.210 Section F (Deliveries or Performance).
entity<|#|>Monthly Status Reports<|#|>DELIVERABLE<|#|>Monthly Status Reports are recurring contract deliverables documenting project progress, performance metrics, and schedule adherence.
entity<|#|>Quarterly Technical Review Briefings<|#|>DELIVERABLE<|#|>Quarterly Technical Review Briefings are formal presentations to the Government reviewing technical progress and risk status.
entity<|#|>Final System Documentation<|#|>DELIVERABLE<|#|>Final System Documentation is the comprehensive technical documentation package delivered upon contract completion.
entity<|#|>CLIN 0001<|#|>CONCEPT<|#|>CLIN 0001 is Contract Line Item Number 0001 defining the scope and deliverables for the base year period.
entity<|#|>5th Business Day<|#|>EVENT<|#|>5th business day of each month is the deadline for monthly status report submission.
entity<|#|>Government Site<|#|>LOCATION<|#|>Government site refers to the federal facility where quarterly briefings will be conducted.
entity<|#|>Arlington, VA<|#|>LOCATION<|#|>Arlington, VA is the geographic location of the Government facility for quarterly briefings.
entity<|#|>30 Days<|#|>EVENT<|#|>30 days after contract completion is the deadline for final system documentation delivery.
entity<|#|>Section C.4<|#|>SECTION<|#|>Section C.4 is an RFP section in the Statement of Work defining deliverable formatting requirements.
entity<|#|>Contractor<|#|>ORGANIZATION<|#|>Contractor is the organization responsible for producing and delivering all contract deliverables.
relation<|#|>Section F.3.1<|#|>Monthly Status Reports<|#|>specifies, deliverable definition<|#|>Section F.3.1 defines the requirements for monthly status reports.
relation<|#|>Section F.3.1<|#|>Quarterly Technical Review Briefings<|#|>specifies, deliverable definition<|#|>Section F.3.1 defines the requirements for quarterly technical review briefings.
relation<|#|>Section F.3.1<|#|>Final System Documentation<|#|>specifies, deliverable definition<|#|>Section F.3.1 defines the requirements for final system documentation.
relation<|#|>CLIN 0001<|#|>Monthly Status Reports<|#|>includes, deliverable scope<|#|>CLIN 0001 includes monthly status reports as a required deliverable.
relation<|#|>CLIN 0001<|#|>Quarterly Technical Review Briefings<|#|>includes, deliverable scope<|#|>CLIN 0001 includes quarterly technical review briefings as a required deliverable.
relation<|#|>CLIN 0001<|#|>Final System Documentation<|#|>includes, deliverable scope<|#|>CLIN 0001 includes final system documentation as a required deliverable.
relation<|#|>Monthly Status Reports<|#|>5th Business Day<|#|>due_by, deadline<|#|>Monthly status reports must be submitted by the 5th business day of each month.
relation<|#|>Quarterly Technical Review Briefings<|#|>Government Site<|#|>performed_at, presentation location<|#|>Quarterly briefings will be presented at the Government site.
relation<|#|>Government Site<|#|>Arlington, VA<|#|>located_in, geographic location<|#|>The Government site is located in Arlington, VA.
relation<|#|>Final System Documentation<|#|>30 Days<|#|>due_by, deadline<|#|>Final system documentation must be delivered within 30 days of contract completion.
relation<|#|>Monthly Status Reports<|#|>Section C.4<|#|>references, formatting compliance<|#|>Monthly status reports must comply with Section C.4 formatting requirements.
relation<|#|>Contractor<|#|>Monthly Status Reports<|#|>provides, deliverable responsibility<|#|>The contractor is responsible for providing monthly status reports.
relation<|#|>Contractor<|#|>Quarterly Technical Review Briefings<|#|>provides, deliverable responsibility<|#|>The contractor is responsible for conducting quarterly technical review briefings.
relation<|#|>Contractor<|#|>Final System Documentation<|#|>provides, deliverable responsibility<|#|>The contractor is responsible for delivering final system documentation.
<|COMPLETE|>

""",
    ]


# ============================================================================
# ENTITY EXTRACTION PROMPT (Modified for Government Contracting)
# ============================================================================

def get_entity_extraction_system_prompt(
    entity_types: List[str],
    tuple_delimiter: str = "<|#|>",
    completion_delimiter: str = "<|COMPLETE|>",
    language: str = "English",
) -> str:
    """
    Get ontology-guided entity extraction system prompt for government contracting.
    
    Modifies LightRAG's generic prompt with government contracting instructions:
    - Emphasizes RFP structure (Uniform Contract Format A-M sections)
    - Prioritizes requirement extraction (must/should/may classification)
    - Instructs on section relationship identification (L↔M evaluation linkages)
    - Teaches FAR/DFARS clause recognition
    
    Args:
        entity_types: List of government contracting entity types from ontology
        tuple_delimiter: Field delimiter for entity/relation output
        completion_delimiter: Signal for extraction completion
        language: Output language (default: English)
    
    Returns:
        Modified system prompt with government contracting instructions
    
    Usage:
        PROMPTS["entity_extraction_system_prompt"] = get_entity_extraction_system_prompt(
            entity_types=get_government_contracting_entity_types()
        )
    """
    entity_types_str = ", ".join([f"`{et}`" for et in entity_types])
    
    return f"""---Role---
You are a Government Contracting Knowledge Graph Specialist responsible for extracting
entities and relationships from Request for Proposal (RFP) documents.

---Domain Context---
You are analyzing government RFP documents that follow the Uniform Contract Format with
standard sections (A-M) and attachments (J-sections). Your extraction must recognize:
- **Sections**: L (Instructions), M (Evaluation), C (SOW), I (Contract Clauses), etc.
- **Requirements**: Classified as "must", "shall" (mandatory) vs "should", "may" (optional)
- **CLINs**: Contract Line Item Numbers defining scope and funding
- **FAR/DFARS Clauses**: Federal regulations applicable to the contract
- **Section Relationships**: Critical L↔M connections linking instructions to evaluation

---Instructions---
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify government contracting entities in the RFP text.
    *   **Entity Details:** For each identified entity, extract:
        *   `entity_name`: Name of entity. For sections, use format "Section X.Y.Z". 
            For requirements, extract the exact requirement text. For CLINs, use "CLIN XXXX" format.
            Ensure **consistent naming** - use title case for case-insensitive names.
        *   `entity_type`: Categorize using ONLY these government contracting types: {entity_types_str}.
            If none apply, classify as `Other` (do not create new types).
        *   `entity_description`: Concise description of the entity's role in the RFP context.
            For requirements, include compliance level (mandatory/optional).
            For sections, describe purpose and content scope.
    *   **Output Format - Entities:** Output 4 fields per entity, delimited by `{tuple_delimiter}`:
        *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

2.  **Relationship Extraction & Output:**
    *   **Identification:** Identify relationships between entities, prioritizing:
        *   **Section L↔M connections**: Instructions to evaluation criteria (CRITICAL)
        *   **Section C→Requirements**: SOW to specific requirements
        *   **Requirements→Clauses**: Requirements to applicable FAR/DFARS clauses
        *   **CLINs→Requirements**: Funding to scope definitions
    *   **N-ary Relationship Decomposition:** Decompose multi-entity relationships into binary pairs.
    *   **Relationship Details:** Extract:
        *   `source_entity`: Source entity name (consistent with entity extraction)
        *   `target_entity`: Target entity name (consistent with entity extraction)
        *   `relationship_keywords`: High-level keywords (comma-separated, NO `{tuple_delimiter}`)
        *   `relationship_description`: Clear explanation of the relationship's nature in RFP context
    *   **Output Format - Relationships:** Output 5 fields per relationship, delimited by `{tuple_delimiter}`:
        *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

3.  **Government Contracting Best Practices:**
    *   Preserve exact section numbering (e.g., "Section L.3.2.1", not "Section L")
    *   Distinguish between mandatory ("shall", "must", "required") and optional ("should", "may") language
    *   Capture FAR/DFARS clause numbers exactly (e.g., "FAR 52.215-2", "DFARS 252.204-7012")
    *   Identify deliverable requirements and their frequency (monthly reports, quarterly reviews)
    *   Extract security requirements and clearance levels explicitly

4.  **Delimiter Usage Protocol:**
    *   `{tuple_delimiter}` is an atomic field separator - do NOT fill with content
    *   **Incorrect:** `entity{tuple_delimiter}Section L<|instructions|>Volume L contains proposal instructions`
    *   **Correct:** `entity{tuple_delimiter}Section L{tuple_delimiter}SECTION{tuple_delimiter}Volume L contains proposal instructions`

5.  **Relationship Direction & Duplication:**
    *   Treat relationships as **undirected** unless explicit directionality
    *   Avoid duplicate relationships (e.g., don't output both A→B and B→A for same relationship)

6.  **Output Order & Prioritization:**
    *   Output all entities first, then all relationships
    *   Prioritize critical L↔M evaluation relationships first in relationship list

7.  **Context & Objectivity:**
    *   Use third-person perspective (avoid "this RFP", "our agency")
    *   Explicitly name entities (avoid pronouns like "it", "this", "they")

8.  **Language & Proper Nouns:**
    *   Output in `{language}`
    *   Retain proper nouns in original language (organization names, place names)

9.  **Completion Signal:** Output `{completion_delimiter}` ONLY after all extractions are complete

---Examples---
{{examples}}

---Real Data to be Processed---
<Input>
Entity_types: [{entity_types_str}]
Text:
```
{{input_text}}
```
"""


# ============================================================================
# RELATIONSHIP VALIDATION INSTRUCTIONS (Post-Processing Guidance)
# ============================================================================

def get_relationship_extraction_guidance() -> str:
    """
    Get guidance on valid relationship patterns from VALID_RELATIONSHIPS schema.
    
    Returns a formatted string documenting valid relationship patterns per entity type,
    used to guide LightRAG extraction and post-processing validation.
    
    Returns:
        Formatted guidance string for relationship constraints
    
    Usage:
        # Append to entity extraction prompt or use in validation prompt
        guidance = get_relationship_extraction_guidance()
    """
    guidance_lines = ["Valid Relationship Patterns (from Government Contracting Ontology):"]
    guidance_lines.append("")
    
    # Group by source entity type
    entity_relationships = {}
    for (source, relation), targets in VALID_RELATIONSHIPS.items():
        if source not in entity_relationships:
            entity_relationships[source] = []
        entity_relationships[source].append(f"  - {relation}: → {', '.join(targets)}")
    
    # Format output
    for entity_type in sorted(entity_relationships.keys()):
        guidance_lines.append(f"{entity_type}:")
        guidance_lines.extend(entity_relationships[entity_type])
        guidance_lines.append("")
    
    return "\n".join(guidance_lines)


# ============================================================================
# LIGHTRAG CONFIGURATION HELPER
# ============================================================================

def get_ontology_addon_params() -> Dict[str, Any]:
    """
    Get complete addon_params configuration for LightRAG with ontology injection.
    
    Returns dictionary ready for LightRAG initialization:
        rag = LightRAG(
            addon_params=get_ontology_addon_params()
        )
    
    Returns:
        Dictionary with entity_types and language configuration
    """
    return {
        "language": "English",
        "entity_types": get_government_contracting_entity_types(),
    }


def get_ontology_prompts() -> Dict[str, Any]:
    """
    Get complete PROMPTS dictionary override for LightRAG with ontology guidance.
    
    Replaces generic examples with RFP-specific patterns.
    
    Returns:
        Dictionary with entity_extraction_examples for PROMPTS override
    
    Usage:
        from lightrag import PROMPTS
        PROMPTS.update(get_ontology_prompts())
    """
    return {
        "entity_extraction_examples": get_rfp_entity_extraction_examples(),
    }


# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

__all__ = [
    # Entity type injection
    'get_government_contracting_entity_types',
    
    # Few-shot examples
    'get_rfp_entity_extraction_examples',
    
    # Prompt generation
    'get_entity_extraction_system_prompt',
    'get_relationship_extraction_guidance',
    
    # Configuration helpers
    'get_ontology_addon_params',
    'get_ontology_prompts',
]
