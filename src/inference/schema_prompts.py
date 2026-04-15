"""
Schema-Driven LLM Prompt Utilities
===================================

Extract Pydantic schema metadata to generate LLM prompts that leverage
field descriptions for robust pattern discovery.

Issue #43: Replace brittle hardcoded keyword lists with schema-driven guidance.
Pattern: Use Pydantic field descriptions as semantic hints for LLM reasoning.

Usage:
    from src.inference.schema_prompts import get_schema_guidance, get_multi_schema_guidance
    from src.ontology.schema import EvaluationFactor, ProposalInstruction
    
    # Single schema guidance
    guidance = get_schema_guidance(EvaluationFactor)
    
    # Multiple schemas combined
    guidance = get_multi_schema_guidance(EvaluationFactor, ProposalInstruction)
    
    # Use in prompt
    prompt = f'''
    {guidance}
    
    Analyze these entities using the schema structure above:
    {entities_json}
    '''
"""

from typing import Type, List, Optional
from pydantic import BaseModel

from src.ontology.schema import VALID_ENTITY_TYPES


def get_schema_guidance(model_class: Type[BaseModel], include_examples: bool = True) -> str:
    """
    Extract field descriptions from Pydantic model for LLM prompt guidance.
    
    Converts Pydantic schema metadata into structured text that helps LLM
    understand entity structure and semantics without relying on hardcoded keywords.
    
    Args:
        model_class: Pydantic model class (e.g., EvaluationFactor, ProposalInstruction)
        include_examples: Whether to include example values from descriptions
        
    Returns:
        Formatted string with schema guidance for LLM prompt
        
    Example:
        >>> from src.ontology.schema import EvaluationFactor
        >>> guidance = get_schema_guidance(EvaluationFactor)
        >>> print(guidance)
        SCHEMA GUIDANCE: EvaluationFactor
        ==================================
        - weight: Numerical weight (e.g., '40%', '25 points').
        - importance: Relative importance (e.g., 'Most Important').
        - subfactors: List of sub-criteria or subfactors.
    """
    schema = model_class.model_json_schema()
    props = schema.get('properties', {})
    
    # Build guidance header
    model_name = model_class.__name__
    guidance_lines = [
        f"SCHEMA GUIDANCE: {model_name}",
        "=" * (len(model_name) + 18),
    ]
    
    # Extract field descriptions
    for field_name, field_info in props.items():
        # Skip internal fields
        if field_name in ('entity_name', 'entity_type'):
            continue
            
        description = field_info.get('description', '')
        field_type = field_info.get('type', 'any')
        
        if description:
            guidance_lines.append(f"- {field_name}: {description}")
        else:
            guidance_lines.append(f"- {field_name}: ({field_type})")
    
    # Add semantic hints based on model type
    if model_name == 'EvaluationFactor':
        guidance_lines.extend([
            "",
            "IDENTIFICATION HINTS:",
            "- Main factors typically have weight/importance fields populated",
            "- Subfactors reference parent factors or appear in subfactors list",
            "- Rating scales (Outstanding, Good, etc.) are NOT main factors",
            "- Processes/analyses (assessment, realism) are supporting entities",
        ])
    elif model_name == 'ProposalInstruction':
        guidance_lines.extend([
            "",
            "IDENTIFICATION HINTS:",
            "- Look for page limits, format requirements, volume assignments",
            "- Submission instructions guide proposal preparation",
            "- May appear as deliverables or requirements with submission verbs",
        ])
    elif model_name == 'Requirement':
        guidance_lines.extend([
            "",
            "IDENTIFICATION HINTS:",
            "- MANDATORY requirements use 'shall', 'must'",
            "- IMPORTANT requirements use 'should'",
            "- OPTIONAL requirements use 'may'",
            "- Labor drivers indicate staffing/workload implications",
        ])
    
    return "\n".join(guidance_lines)


def get_multi_schema_guidance(*model_classes: Type[BaseModel]) -> str:
    """
    Combine schema guidance from multiple Pydantic models.
    
    Useful when an algorithm needs to understand multiple entity types
    for relationship inference (e.g., linking instructions to factors).
    
    Args:
        *model_classes: Variable number of Pydantic model classes
        
    Returns:
        Combined schema guidance string
        
    Example:
        >>> from src.ontology.schema import EvaluationFactor, ProposalInstruction
        >>> guidance = get_multi_schema_guidance(EvaluationFactor, ProposalInstruction)
    """
    guidance_parts = []
    
    for model_class in model_classes:
        guidance_parts.append(get_schema_guidance(model_class))
    
    return "\n\n".join(guidance_parts)


def get_entity_type_guidance(include_descriptions: bool = True) -> str:
    """
    Generate guidance text from VALID_ENTITY_TYPES for document hierarchy discovery.
    
    Provides LLM with the complete set of valid entity types from the ontology,
    enabling schema-aware hierarchy inference without hardcoded type categories.
    
    Args:
        include_descriptions: Whether to include type descriptions
        
    Returns:
        Formatted string listing valid entity types with categories
        
    Example:
        >>> guidance = get_entity_type_guidance()
        >>> print(guidance)
        VALID ENTITY TYPES (from ontology schema):
        ==========================================
        Document Types: document, document_section, amendment, clause
        ...
    """
    # Categorize entity types for better LLM understanding
    type_categories = {
        'Document Structure': ['document', 'document_section', 'amendment'],
        'Attachments': ['attachment'],  # exhibit, annex handled via entity names
        'Regulatory': ['clause', 'regulatory_reference', 'technical_specification'],
        'Work Items': ['requirement', 'deliverable', 'work_scope_item', 'transition_activity'],
        'Evaluation': ['evaluation_factor', 'subfactor', 'proposal_instruction', 'proposal_volume', 'performance_standard'],
        'Strategic': ['strategic_theme', 'customer_priority', 'pain_point', 'program'],
        'Commercial': ['contract_line_item', 'pricing_element', 'workload_metric', 'labor_category', 'past_performance_reference'],
        'Resources': ['organization', 'person', 'equipment', 'technology', 'location'],
        'Other': ['concept', 'event'],
    }
    
    guidance_lines = [
        "VALID ENTITY TYPES (from ontology schema):",
        "=" * 42,
    ]
    
    for category, types in type_categories.items():
        # Filter to only include types that exist in VALID_ENTITY_TYPES
        valid_types = [t for t in types if t in VALID_ENTITY_TYPES]
        if valid_types:
            guidance_lines.append(f"- {category}: {', '.join(valid_types)}")
    
    guidance_lines.extend([
        "",
        "HIERARCHY PATTERNS:",
        "- CHILD_OF: Document Section 1.1 → Document Section 1 (subsection to section)",
        "- ATTACHMENT_OF: Exhibit A → Document Section C (attachment to document)",
        "- AMENDS: Amendment 001 → base document",
        "- REFERENCES: Document Section L → Document Section M (cross-references)",
    ])
    
    return "\n".join(guidance_lines)


def get_document_hierarchy_guidance() -> str:
    """
    Generate specialized guidance for document hierarchy inference.
    
    Combines entity type information with specific hierarchy patterns
    for Algorithm 5 (Document Hierarchy) to use instead of hardcoded
    type-based batching.
    
    Returns:
        Comprehensive document hierarchy guidance string
    """
    guidance_lines = [
        "DOCUMENT HIERARCHY SCHEMA GUIDANCE",
        "=" * 35,
        "",
        "DOCUMENT ENTITY TYPES (from schema):",
        f"- Valid types: {', '.join(sorted([t for t in VALID_ENTITY_TYPES if t in ['document', 'document_section', 'clause', 'amendment', 'attachment']]))}",
        "- Attachments may be labeled: Exhibit, Annex, Appendix, Enclosure",
        "- Amendments modify base documents",
        "",
        "HIERARCHY RELATIONSHIP TYPES:",
        "- CHILD_OF: Nested structure (Document Section 1.1 is CHILD_OF Document Section 1)",
        "- ATTACHMENT_OF: Document attachments (Exhibit A ATTACHMENT_OF Document Section C)",
        "- AMENDS: Modifications (Amendment 001 AMENDS base RFP)",
        "- INCORPORATES: Standard references (Contract INCORPORATES FAR clause)",
        "",
        "IDENTIFICATION PATTERNS:",
        "- Heading numbering: 1, 1.1, 1.1.1, A, B, C, I, II, III",
        "- Attachment naming: Exhibit/Annex/Appendix + letter/number",
        "- Amendment references: 'Amendment', 'Modification', 'Change'",
        "- Cross-references: 'See Section X', 'per Attachment Y'",
        "",
        "INFERENCE RULES:",
        "- Identify parent-child by numbering patterns (1.1 → 1)",
        "- Link attachments to their parent sections",
        "- Connect amendments to documents they modify",
        "- Discover cross-type relationships regardless of entity type",
    ]
    
    return "\n".join(guidance_lines)


def get_evaluation_hierarchy_guidance() -> str:
    """
    Generate specialized guidance for evaluation factor hierarchy inference.
    
    Provides schema-aware guidance for Algorithm 2 to discover factor
    hierarchies (Factor A → Subfactor A.1) without keyword matching.
    
    Returns:
        Evaluation hierarchy guidance string
    """
    # Import here to avoid circular dependency
    from src.ontology.schema import EvaluationFactor
    
    # Get base schema guidance
    base_guidance = get_schema_guidance(EvaluationFactor)
    
    additional_guidance = """
EVALUATION HIERARCHY PATTERNS:
- Main Factors: Factor A, Factor B, Technical Factor, Management Factor
- Subfactors: Subfactor A.1, Factor A - Technical Approach
- Rating Scales: Outstanding, Good, Acceptable (NOT factors - exclude)
- Metrics: CEI, SEI, KPI (NOT factors - exclude)

RELATIONSHIP TYPES:
- HAS_SUBFACTOR: Main factor → subfactor relationship
- HAS_RATING_SCALE: Factor → rating scale definition
- MEASURED_BY: Factor → performance metric
- HAS_THRESHOLD: Metric → threshold value

DISCOVERY APPROACH:
- Use weight/importance fields to identify main factors
- Use subfactors field to identify hierarchies
- Ignore entity names - focus on structural relationships
- Include ALL factors regardless of naming (e.g., "Small Business Participation")
"""
    
    return base_guidance + "\n" + additional_guidance


def get_instruction_evaluation_guidance() -> str:
    """
    Generate specialized guidance for instruction-evaluation linking.
    
    Provides schema-aware guidance for Algorithm 1 to link proposal
    instructions to evaluation factors without hardcoded keyword matching.
    
    Returns:
        Instruction-evaluation linking guidance string
    """
    # Import here to avoid circular dependency
    from src.ontology.schema import ProposalInstruction, EvaluationFactor
    
    guidance = get_multi_schema_guidance(ProposalInstruction, EvaluationFactor)
    
    additional_guidance = """
INSTRUCTION-EVALUATION LINKING PATTERNS:
- Proposal instructions GUIDE evaluation factors
- Page limits, format requirements affect how proposals are evaluated
- Volume assignments (Volume I, II, III) map to specific factors

ENTITY IDENTIFICATION (without keywords):
- Submission instructions have: page_limit, format_reqs, volume fields
- Look for entities describing HOW to respond, not WHAT to deliver
- May appear as deliverables or requirements with submission semantics

RELATIONSHIP TYPE:
- GUIDES: Instruction → Factor (submission instruction guides evaluation)

DISCOVERY APPROACH:
- Identify instruction entities by schema field presence, not name keywords
- Link to factors based on content/volume alignment
- Include agnostic detection across entity types
"""
    
    return guidance + "\n" + additional_guidance

