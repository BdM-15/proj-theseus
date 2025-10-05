"""
Ontology Integration - Government Contracting Entity Types

Injects domain-specific ontology into LightRAG extraction prompts.
Replaces generic entity types with government contracting concepts.

Key Modifications:
- Entity types: SECTION, REQUIREMENT, CLIN, FAR_CLAUSE (not 'person', 'location')
- Relationship patterns: LM, CB, Iapplicable sections
- Domain examples: Government contracting use cases
- Validation constraints: Only valid RFP patterns

References:
- src/core/ontology.py (EntityType, RelationshipType enums)
- Shipley Proposal Guide p.50-55 (Requirements methodology)
- FAR 15.210 (Uniform Contract Format)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# Import our existing ontology
from core.ontology import EntityType, RelationshipType, VALID_RELATIONSHIPS

logger = logging.getLogger(__name__)


class OntologyInjector:
    """
    Injects government contracting ontology into LightRAG extraction prompts
    
    Transforms generic LightRAG extraction into domain-specific intelligence by:
    1. Replacing default entity types with government contracting types
    2. Providing domain-specific extraction examples
    3. Constraining relationships to valid patterns
    4. Adding validation guidance
    """
    
    def __init__(self):
        """Initialize with government contracting ontology"""
        self.entity_types = self._get_government_entity_types()
        self.relationship_patterns = self._get_relationship_patterns()
        self.extraction_examples = self._get_extraction_examples()
        
        logger.info(f"Ontology injector initialized with {len(self.entity_types)} entity types")
    
    def _get_government_entity_types(self) -> List[Tuple[str, str]]:
        """
        Government contracting entity types with descriptions
        Replaces LightRAG's DEFAULT_ENTITY_TYPES
        
        Maps domain concepts to actual EntityType enum values from src/core/ontology.py:
        - CLINs, evaluation factors, specifications → CONCEPT
        - FAR clauses → CLAUSE
        - Personnel → PERSON
        - Security/performance requirements → REQUIREMENT
        """
        return [
            (EntityType.SECTION.value, "RFP sections (A-M) and subsections (L.3.1, M.2.5)"),
            (EntityType.REQUIREMENT.value, "Contractor obligations (shall/must statements), security clearances, performance standards"),
            (EntityType.EVALUATION_FACTOR.value, "Section M evaluation criteria (basis for award) + Section L response instructions (Technical Approach, Management, Past Performance, Price)"),
            (EntityType.CONCEPT.value, "Contract Line Item Numbers (CLINs), technical specifications, budget/pricing concepts"),
            (EntityType.CLAUSE.value, "Federal Acquisition Regulation clauses (FAR 52.XXX, DFARS 252.XXX)"),
            (EntityType.DELIVERABLE.value, "Required deliverables, reports, documentation"),
            (EntityType.ORGANIZATION.value, "Government agencies, contractors, entities"),
            (EntityType.PERSON.value, "Key personnel, contracting officers, POCs"),
            (EntityType.LOCATION.value, "Performance locations, sites, facilities"),
            (EntityType.DOCUMENT.value, "Referenced documents, standards, manuals"),
            (EntityType.EVENT.value, "Milestones, deadlines, key events"),
            (EntityType.TECHNOLOGY.value, "Systems, tools, platforms, software"),
        ]
    
    def _get_relationship_patterns(self) -> Dict[str, str]:
        """
        Valid government contracting relationship patterns
        Guides LLM to create domain-appropriate connections
        
        CRITICAL L↔M RELATIONSHIPS (Most Important):
        - Section L provides INSTRUCTIONS on what to submit
        - Section M provides EVALUATION METHOD for how government will score submissions
        - These are bidirectional and THE most important for winning contracts
        """
        return {
            # CRITICAL L↔M Relationships (Highest Priority)
            "Section L ↔ Section M": "Section L instructions tell HOW to submit; Section M factors tell HOW government will score (CRITICAL bidirectional relationship for award)",
            "Evaluation Factor → Section L": "Evaluation factors reference specific Section L submission instructions (page limits, format, content requirements)",
            "Section L → Evaluation Factor": "Section L instructions specify requirements that map to Section M evaluation factors",
            "Evaluation Factor → Requirement": "Evaluation factors assess compliance with specific requirements",
            "Requirement → Evaluation Factor": "Requirements trace to evaluation factors that will score them",
            
            # Core RFP Structure Relationships
            "Section C → Section B": "Statement of Work references Contract Line Items (CLINs)",
            "Section C → Deliverable": "SOW specifies required deliverables",
            "Section I → Sections A-H": "Contract clauses apply to various sections",
            "Section M → Section L": "Evaluation factors reference submission instructions (backward reference)",
            
            # Requirement Relationships
            "Requirement → Deliverable": "Requirements generate specific deliverables",
            "FAR Clause → Requirement": "FAR clauses impose requirements",
            "Personnel → Requirement": "Key personnel requirements specified",
            
            # CLIN Relationships
            "CLIN → Deliverable": "CLINs define deliverable quantities/costs",
            "CLIN → Requirement": "CLINs implement specific requirements",
            
            # Supporting Relationships
            "Section L → Document": "Instructions reference required documents",
            "Organization → Location": "Agencies associated with performance sites",
        }
    
    def _get_extraction_examples(self) -> List[Dict[str, str]]:
        """
        Domain-specific extraction examples for LLM training
        Shows proper entity/relationship extraction for government RFPs
        """
        return [
            {
                "text": "Section L.3.1 states that proposals shall not exceed 25 pages for the technical volume.",
                "entities": "SECTION|L.3.1, REQUIREMENT|25 page limit, DELIVERABLE|technical volume",
                "relationships": "[SECTION|L.3.1]->(references)->[REQUIREMENT|25 page limit], [REQUIREMENT|25 page limit]->(applies_to)->[DELIVERABLE|technical volume]",
                "explanation": "Section reference, page limit requirement, and deliverable type identified"
            },
            {
                "text": "CLIN 0001 covers base year operations support services at a firm-fixed price of ,500,000.",
                "entities": "CLIN|0001, REQUIREMENT|operations support services, PERFORMANCE_METRIC|base year, SPECIFICATION|firm-fixed price .5M",
                "relationships": "[CLIN|0001]->(covers)->[REQUIREMENT|operations support services], [CLIN|0001]->(has_price)->[SPECIFICATION|firm-fixed price .5M]",
                "explanation": "CLIN identification with associated requirements and pricing"
            },
            {
                "text": "Section M.2 states that Factor 1 - Technical Approach will be evaluated as significantly more important than Cost/Price.",
                "entities": "SECTION|M.2, EVALUATION_FACTOR|Technical Approach, EVALUATION_FACTOR|Cost/Price",
                "relationships": "[SECTION|M.2]->(defines)->[EVALUATION_FACTOR|Technical Approach], [EVALUATION_FACTOR|Technical Approach]->(more_important_than)->[EVALUATION_FACTOR|Cost/Price]",
                "explanation": "Section M evaluation factors with relative weights - CRITICAL for proposal strategy"
            },
            {
                "text": "Section L.3.2 requires that the Technical Volume shall not exceed 25 pages and must address all sub-factors in Section M.2.",
                "entities": "SECTION|L.3.2, EVALUATION_FACTOR|Technical Volume, REQUIREMENT|25 page limit, SECTION|M.2",
                "relationships": "[SECTION|L.3.2]->(specifies)->[EVALUATION_FACTOR|Technical Volume], [EVALUATION_FACTOR|Technical Volume]->(limited_by)->[REQUIREMENT|25 page limit], [SECTION|L.3.2]->(references)->[SECTION|M.2]",
                "explanation": "Section L submission instructions linked to Section M evaluation - CRITICAL L↔M relationship"
            },
            {
                "text": "Per Section M.2.1, sub-factors for Technical Approach include: (1) Staffing Approach, (2) Maintenance Execution, and (3) Supply Chain Resilience.",
                "entities": "SECTION|M.2.1, EVALUATION_FACTOR|Technical Approach, EVALUATION_FACTOR|Staffing Approach, EVALUATION_FACTOR|Maintenance Execution, EVALUATION_FACTOR|Supply Chain Resilience",
                "relationships": "[SECTION|M.2.1]->(defines)->[EVALUATION_FACTOR|Technical Approach], [EVALUATION_FACTOR|Technical Approach]->(has_subfactor)->[EVALUATION_FACTOR|Staffing Approach], [EVALUATION_FACTOR|Technical Approach]->(has_subfactor)->[EVALUATION_FACTOR|Maintenance Execution], [EVALUATION_FACTOR|Technical Approach]->(has_subfactor)->[EVALUATION_FACTOR|Supply Chain Resilience]",
                "explanation": "Section M hierarchical evaluation structure - factors and sub-factors that determine award"
            },
            {
                "text": "FAR 52.204-7 System for Award Management applies to this solicitation.",
                "entities": "FAR_CLAUSE|52.204-7, REQUIREMENT|System for Award Management registration",
                "relationships": "[FAR_CLAUSE|52.204-7]->(requires)->[REQUIREMENT|System for Award Management registration]",
                "explanation": "FAR clause identification and its imposed requirement"
            },
            {
                "text": "The contractor shall submit monthly status reports to the Contracting Officer at NAVFAC SE.",
                "entities": "REQUIREMENT|monthly status reports, DELIVERABLE|status reports, PERSONNEL|Contracting Officer, ORGANIZATION|NAVFAC SE",
                "relationships": "[REQUIREMENT|monthly status reports]->(generates)->[DELIVERABLE|status reports], [DELIVERABLE|status reports]->(submitted_to)->[PERSONNEL|Contracting Officer], [PERSONNEL|Contracting Officer]->(works_at)->[ORGANIZATION|NAVFAC SE]",
                "explanation": "Requirement chain with deliverable, recipient, and organization"
            },
        ]
    
    def enhance_extraction_prompt(
        self,
        base_prompt: str,
        section_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Inject government contracting ontology into extraction prompt
        
        Args:
            base_prompt: LightRAG's base extraction prompt
            section_context: Optional RFP section context
        
        Returns:
            Enhanced prompt with ontology injection
        """
        
        # Build entity types section
        entity_types_text = "\\n".join([
            f"- {entity_type}: {description}"
            for entity_type, description in self.entity_types
        ])
        
        # Build relationship patterns section
        relationship_text = "\\n".join([
            f"- {pattern}: {description}"
            for pattern, description in self.relationship_patterns.items()
        ])
        
        # Build examples section
        examples_text = "\\n\\n".join([
            f"Example {i+1}:\\n"
            f"Text: {ex['text']}\\n"
            f"Entities: {ex['entities']}\\n"
            f"Relationships: {ex['relationships']}\\n"
            f"Explanation: {ex['explanation']}"
            for i, ex in enumerate(self.extraction_examples[:3])  # Use top 3 examples
        ])
        
        # Build context section if provided
        context_text = ""
        if section_context:
            context_text = f"""
            
            CURRENT SECTION CONTEXT:
            - Section ID: {section_context.get('section_id', 'Unknown')}
            - Section Title: {section_context.get('section_title', 'Unknown')}
            - Expected Entity Types: {', '.join(section_context.get('expected_entities', []))}
            """
        
        # Construct enhanced prompt with full ontology guidance
        enhanced_prompt = f"""
{base_prompt}

═══════════════════════════════════════════════════════════════
GOVERNMENT CONTRACTING ONTOLOGY - DOMAIN-SPECIFIC EXTRACTION
═══════════════════════════════════════════════════════════════

ENTITY TYPES (extract ONLY these government contracting entities):

{entity_types_text}

RELATIONSHIP PATTERNS (create ONLY these valid relationships):

{relationship_text}

EXTRACTION RULES:
• Extract ONLY entities/relationships present in the text below
• Use ONLY entity types listed above (no generic person/location/organization)
• Section references MUST be valid RFP format (A-M, J-1, L.3.1, M.2.5, etc.)
• ALL extracted text MUST exist verbatim in source document
• NO external knowledge, training data, or fictional entities{context_text}

Now extract government contracting entities and relationships from the RFP text:
"""
        
        return enhanced_prompt
    
    def get_entity_types_for_lightrag(self) -> List[str]:
        """
        Get entity type list in format for LightRAG's addon_params
        
        Returns:
            List of entity type strings for LightRAG configuration
        """
        return [entity_type for entity_type, _ in self.entity_types]
    
    def validate_extraction(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate extracted entities/relationships against ontology
        
        Checks:
        - Entity types match valid types
        - Relationships match valid patterns
        - Section references are valid
        
        Returns:
            Validation report with errors, warnings, and statistics
        """
        
        errors = []
        warnings = []
        
        valid_entity_types = set([et for et, _ in self.entity_types])
        valid_sections = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'])
        
        # Validate entities
        for entity in entities:
            entity_type = entity.get('entity_type', '').upper()
            entity_name = entity.get('entity_name', '')
            
            # Check entity type validity
            if entity_type not in valid_entity_types:
                errors.append(f"Invalid entity type '{entity_type}' for entity '{entity_name}'")
            
            # Check section references
            if entity_type == 'SECTION':
                section_id = entity_name.split()[0] if ' ' in entity_name else entity_name
                base_section = section_id.split('.')[0].split('-')[0]
                
                if base_section not in valid_sections:
                    errors.append(f"Invalid section reference '{section_id}' in entity '{entity_name}'")
        
        # Validate relationships
        for relationship in relationships:
            rel_type = relationship.get('relationship_type', '')
            source = relationship.get('source', '')
            target = relationship.get('target', '')
            
            # Check if relationship pattern is valid
            # (For now, just log warnings - full validation in next phase)
            if not rel_type:
                warnings.append(f"Missing relationship type for {source}  {target}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "entity_type_distribution": self._get_entity_distribution(entities),
        }
    
    def _get_entity_distribution(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of entity types"""
        distribution = {}
        for entity in entities:
            entity_type = entity.get('entity_type', 'UNKNOWN').upper()
            distribution[entity_type] = distribution.get(entity_type, 0) + 1
        return distribution


# Example usage
if __name__ == "__main__":
    injector = OntologyInjector()
    
    # Show available entity types
    print("Government Contracting Entity Types:")
    for entity_type, description in injector._get_government_entity_types():
        print(f"  {entity_type}: {description}")
    
    # Show relationship patterns
    print("\\nValid Relationship Patterns:")
    for pattern, description in injector.relationship_patterns.items():
        print(f"  {pattern}: {description}")
    
    # Test prompt enhancement
    base_prompt = "Extract entities and relationships from the following text:"
    enhanced = injector.enhance_extraction_prompt(
        base_prompt,
        section_context={
            'section_id': 'L',
            'section_title': 'Instructions to Offerors',
            'expected_entities': ['REQUIREMENT', 'DELIVERABLE', 'SECTION']
        }
    )
    
    print("\\nEnhanced Prompt Length:", len(enhanced))
    print("Ontology injection successful!")
