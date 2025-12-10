"""
Generate schema-aligned entity type prompt sections from Pydantic models.

This tool ensures prompts stay in sync with the Pydantic schema (single source of truth).
Auto-generates entity-specific prompt files in prompts/extraction_v2/_schema_mirror/

Usage:
    python tools/generate_schema_prompts.py
"""

import os
import sys
from typing import get_args, get_origin, Union
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ontology.schema import (
    BaseEntity,
    Requirement,
    EvaluationFactor,
    SubmissionInstruction,
    StrategicTheme,
    Clause,
    PerformanceMetric,
    CriticalityLevel,
    RequirementType,
    ThemeType,
    BOECategory,
    VALID_ENTITY_TYPES
)


def format_field_type(field_annotation):
    """Format Pydantic field type annotation for prompt display."""
    origin = get_origin(field_annotation)
    
    if origin is Union:
        # Handle Optional[X] -> X | None
        args = get_args(field_annotation)
        if type(None) in args:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return f"Optional[{format_field_type(non_none[0])}]"
    
    if origin is list:
        args = get_args(field_annotation)
        if args:
            return f"List[{format_field_type(args[0])}]"
        return "List"
    
    # Handle Literal types
    if hasattr(field_annotation, '__origin__') and field_annotation.__origin__ is Union:
        return str(field_annotation)
    
    # Get class name
    if hasattr(field_annotation, '__name__'):
        return field_annotation.__name__
    
    return str(field_annotation)


def expand_enum(enum_type, enum_name: str) -> str:
    """Expand enum values into Grok-4 decision tree format."""
    if enum_name == "CriticalityLevel":
        return """
CRITICALITY_LEVEL_DETECTION:
  MANDATORY:
    - modal_verb: shall | must | will
    - subject: Contractor | Offeror | Personnel
    - pattern: "[Subject] shall [action]"
    - examples:
      * "Contractor shall provide 24/7 support"
      * "Offeror must submit past performance"
      * "Personnel will complete training"
  
  IMPORTANT:
    - modal_verb: should
    - subject: Contractor | Offeror | Personnel
    - pattern: "[Subject] should [action]"
    - examples:
      * "Contractor should maintain 99.9% uptime"
      * "Offeror should demonstrate certifications"
  
  OPTIONAL:
    - modal_verb: may
    - subject: Contractor | Offeror
    - pattern: "[Subject] may [action]"
    - examples:
      * "Contractor may use open-source tools"
      * "Offeror may propose alternative approaches"
  
  INFORMATIONAL:
    - modal_verb: shall | must | will
    - subject: Government | Program Manager | COR
    - pattern: "Government [action]" (NOT a contractor obligation)
    - action: Extract as 'concept', NOT 'requirement'
    - examples:
      * "Government shall provide office space"
      * "COR will conduct weekly reviews"
"""
    
    elif enum_name == "RequirementType":
        return """
REQUIREMENT_TYPE_CLASSIFICATION:
  FUNCTIONAL:
    - definition: What the system/service must do (capabilities, features)
    - patterns: "shall provide", "shall support", "shall enable"
    - examples:
      * "System shall generate daily reports"
      * "Service shall support 1,000 concurrent users"
  
  PERFORMANCE:
    - definition: Speed, capacity, throughput, efficiency standards
    - patterns: timeframes, volumes, rates, response times
    - examples:
      * "System shall respond within 2 seconds"
      * "Service shall handle 10,000 transactions/hour"
  
  SECURITY:
    - definition: Protection, access control, compliance safeguards
    - patterns: "clearance", "encryption", "authentication", "NIST", "FedRAMP"
    - examples:
      * "Personnel shall have Secret clearances"
      * "Data shall be encrypted using AES-256"
  
  TECHNICAL:
    - definition: Technology stack, platforms, standards, protocols
    - patterns: specific technologies, frameworks, operating systems
    - examples:
      * "Application shall run on Windows Server 2022"
      * "Interface shall use RESTful APIs"
  
  INTERFACE:
    - definition: Integration points, data exchange, interoperability
    - patterns: "integrate with", "interface to", "compatible with"
    - examples:
      * "System shall integrate with Active Directory"
      * "Service shall interface to existing COTS tools"
  
  MANAGEMENT:
    - definition: Administration, oversight, reporting, governance
    - patterns: "management plan", "oversight", "governance", "reporting"
    - examples:
      * "Contractor shall submit monthly status reports"
      * "Contractor shall maintain risk management plan"
  
  DESIGN:
    - definition: Architecture, structure, usability, user experience
    - patterns: "user interface", "architecture", "design", "usability"
    - examples:
      * "Interface shall follow Section 508 guidelines"
      * "System architecture shall use microservices"
  
  QUALITY:
    - definition: Testing, validation, quality assurance, defect tracking
    - patterns: "quality assurance", "testing", "validation", "defect"
    - examples:
      * "Software shall undergo IV&V testing"
      * "Contractor shall maintain defect tracking system"
  
  OTHER:
    - definition: Requirements not fitting other categories
    - use_when: Cannot classify into above 8 types
"""
    
    elif enum_name == "ThemeType":
        return """
THEME_TYPE_CLASSIFICATION:
  CUSTOMER_HOT_BUTTON:
    - definition: Government's explicit priority or concern revealed in RFP
    - detection_signals:
      * "The Government places emphasis on..."
      * "Critical to mission success..."
      * "Of paramount importance..."
      * "Essential to successful performance..."
      * Evaluation factors weighted >30%
      * Repeated emphasis (3+ mentions across sections)
    - examples:
      * "Mission Readiness Priority" (45% weighted factor)
      * "Austere Environment Experience Requirement"
      * "Cultural Sensitivity in Host Nation Operations"
  
  DISCRIMINATOR:
    - definition: Key differentiator between competitors (favors specific approaches)
    - detection_signals:
      * Unique capability requirements
      * Specific technology or methodology preferences
      * Innovation emphasis
      * Specialized certifications or clearances
    - examples:
      * "Cloud-Native Architecture Requirement"
      * "DevSecOps Automation Emphasis"
      * "Small Business Set-Aside Preference"
  
  PROOF_POINT:
    - definition: Evidence validating capability (past performance, certifications)
    - detection_signals:
      * "Offerors must demonstrate..."
      * Past performance requirements
      * Certification mandates (ISO, CMMI, FedRAMP)
      * Relevant experience emphasis
    - examples:
      * "Austere Environment Past Performance Requirement"
      * "CMMI Level 3 Certification Mandate"
      * "Relevant DoD Contract Experience"
  
  WIN_THEME:
    - definition: Overarching proposal positioning and value proposition
    - detection_signals:
      * Alignment language ("in accordance with", "supports")
      * Value proposition indicators
      * Strategic goals mentioned in background section
    - examples:
      * "Total Force Readiness Alignment"
      * "Cost Efficiency Through Automation"
      * "Incumbent Knowledge Transfer Value"
"""
    
    elif enum_name == "BOECategory":
        return """
BOE_CATEGORY_CLASSIFICATION (Basis of Estimate for Workload Enrichment):
  LABOR:
    - definition: Human resource requirements (direct labor, not roles)
    - patterns: volumes, frequencies, shifts, customer counts, ticket volumes
    - examples:
      * "500 calls per month" → Labor
      * "24/7 coverage" → Labor
      * "Support 10,000 users" → Labor
  
  MATERIALS:
    - definition: Equipment, supplies, consumables
    - patterns: physical items, quantities, equipment lists
    - examples:
      * "50 laptops" → Materials
      * "Office supplies" → Materials
      * "Forklift" → Materials
  
  ODCS:
    - definition: Other Direct Costs (travel, licenses, utilities, training)
    - patterns: recurring costs not labor or materials
    - examples:
      * "Travel to CONUS sites" → ODCs
      * "Software licenses" → ODCs
  
  QA:
    - definition: Quality assurance, testing, validation activities
    - patterns: inspection, testing, surveillance, quality control
    - examples:
      * "Periodic inspections" → QA
      * "IV&V testing" → QA
  
  LOGISTICS:
    - definition: Transportation, warehousing, distribution
    - patterns: shipping, storage, distribution, supply chain
    - examples:
      * "Ship equipment to remote sites" → Logistics
      * "Warehouse management" → Logistics
  
  LIFECYCLE:
    - definition: Maintenance, sustainment, upgrades over time
    - patterns: maintenance schedules, O&M, lifecycle support
    - examples:
      * "Annual equipment maintenance" → Lifecycle
      * "Software updates and patches" → Lifecycle
  
  COMPLIANCE:
    - definition: Regulatory, security, policy adherence
    - patterns: clearances, certifications, regulations, audits
    - examples:
      * "Secret clearances required" → Compliance
      * "FedRAMP authorization" → Compliance
"""
    
    return ""


def generate_entity_prompt(model_class, entity_type_name: str) -> str:
    """Generate prompt section for a specific entity type from Pydantic model."""
    
    # Start with entity type header
    prompt = f"ENTITY_TYPE: {entity_type_name}\n"
    prompt += "=" * 80 + "\n\n"
    
    # Check if specialized model exists
    if model_class != BaseEntity:
        prompt += f"Pydantic Model: {model_class.__name__}\n\n"
        
        # Extract field information
        fields = model_class.model_fields
        
        if len(fields) > 2:  # More than just entity_name and entity_type
            prompt += "REQUIRED FIELDS:\n"
            for name, field_info in fields.items():
                if name in ['entity_name', 'entity_type']:
                    continue  # Skip base fields
                
                field_type = format_field_type(field_info.annotation)
                description = field_info.description or "No description"
                default = field_info.default if field_info.default is not None else "Required"
                
                prompt += f"  - {name}: {field_type}\n"
                prompt += f"    Description: {description}\n"
                if default != "Required":
                    prompt += f"    Default: {default}\n"
                prompt += "\n"
            
            # Add enum expansions if applicable
            if model_class == Requirement:
                prompt += expand_enum(CriticalityLevel, "CriticalityLevel")
                prompt += "\n"
                prompt += expand_enum(RequirementType, "RequirementType")
                prompt += "\n"
            
            elif model_class == StrategicTheme:
                prompt += expand_enum(ThemeType, "ThemeType")
                prompt += "\n"
    
    else:
        # Generic BaseEntity type
        prompt += "Pydantic Model: BaseEntity (generic entity)\n\n"
        prompt += "REQUIRED FIELDS:\n"
        prompt += "  - entity_name: str (canonical name in Title Case)\n"
        prompt += "  - entity_type: EntityType (must be one of 18 valid types)\n\n"
    
    return prompt


def generate_all_entity_prompts():
    """Generate prompt files for all 18 entity types."""
    
    # Create output directory
    output_dir = project_root / "prompts" / "extraction_v2" / "_schema_mirror"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Map entity types to their specialized models
    entity_model_map = {
        "requirement": Requirement,
        "evaluation_factor": EvaluationFactor,
        "submission_instruction": SubmissionInstruction,
        "strategic_theme": StrategicTheme,
        "clause": Clause,
        "performance_metric": PerformanceMetric,
        # Generic BaseEntity types (no specialized fields)
        "organization": BaseEntity,
        "concept": BaseEntity,
        "event": BaseEntity,
        "technology": BaseEntity,
        "person": BaseEntity,
        "location": BaseEntity,
        "document": BaseEntity,
        "deliverable": BaseEntity,
        "section": BaseEntity,
        "program": BaseEntity,
        "equipment": BaseEntity,
        "statement_of_work": BaseEntity,
    }
    
    print("=" * 80)
    print("GENERATING SCHEMA-ALIGNED ENTITY TYPE PROMPTS")
    print("=" * 80)
    print(f"Output directory: {output_dir}\n")
    
    for entity_type in sorted(VALID_ENTITY_TYPES):
        model_class = entity_model_map.get(entity_type, BaseEntity)
        prompt_content = generate_entity_prompt(model_class, entity_type)
        
        output_file = output_dir / f"{entity_type}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)
        
        print(f"✅ Generated: {entity_type}.txt ({len(prompt_content)} chars)")
    
    print(f"\n{'=' * 80}")
    print(f"Generated {len(VALID_ENTITY_TYPES)} entity type prompt files")
    print(f"{'=' * 80}")
    
    # Generate index file
    index_content = "ENTITY TYPE REFERENCE - Auto-Generated from Pydantic Schema\n"
    index_content += "=" * 80 + "\n\n"
    index_content += "This directory contains schema-aligned prompt sections for each entity type.\n"
    index_content += "Generated by: tools/generate_schema_prompts.py\n"
    index_content += f"Total entity types: {len(VALID_ENTITY_TYPES)}\n\n"
    index_content += "SPECIALIZED MODELS (with extra fields):\n"
    index_content += "  - requirement (criticality, modal_verb, req_type, labor_drivers, material_needs)\n"
    index_content += "  - evaluation_factor (weight, importance, subfactors)\n"
    index_content += "  - submission_instruction (page_limit, format_reqs, volume)\n"
    index_content += "  - strategic_theme (theme_type)\n"
    index_content += "  - clause (clause_number, regulation)\n"
    index_content += "  - performance_metric (threshold, measurement_method)\n\n"
    index_content += "GENERIC MODELS (BaseEntity only):\n"
    generic_types = [t for t in VALID_ENTITY_TYPES if t not in entity_model_map or entity_model_map[t] == BaseEntity]
    for entity_type in sorted(generic_types):
        index_content += f"  - {entity_type}\n"
    
    index_file = output_dir / "README.txt"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"\n✅ Generated README.txt\n")


if __name__ == "__main__":
    generate_all_entity_prompts()
