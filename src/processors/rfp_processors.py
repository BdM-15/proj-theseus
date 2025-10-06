"""
Government Contracting RFP Processors for RAG-Anything
========================================================

Comprehensive section-by-section entity extraction covering FAR 15.210 Uniform Contract Format (Sections A-M).

These processors handle the ENTIRE RFP structure, not just evaluation sections.
Critical cross-section relationships preserved: L↔M, C↔B, Section I clauses, Section F deliverables.

Reference artifacts:
- prompts/shipley_requirements_extraction.txt: Shipley methodology for requirements
- examples/sample_requirements.json: Reference entity examples
- examples/sample_compliance_assessment.json: Compliance assessment patterns
- docs/ONTOLOGY_EVOLUTION.md: Entity type definitions and relationship patterns
"""

from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass

# Import ontology types
from src.core.ontology import EntityType, RelationshipType, is_valid_relationship
from src.models.rfp_models import (
    RFPRequirement,
    ComplianceLevel,
    RequirementType,
    RFPSectionType,
    RiskLevel,
)


# ============================================================================
# Base Processor with Govcon Ontology Integration
# ============================================================================

class GovconBaseProcessor:
    """
    Base class for all government contracting processors.
    
    Provides:
    - Entity type validation against 12 govcon types
    - Relationship validation using VALID_RELATIONSHIPS
    - Shipley methodology compliance
    - Metadata preservation for traceability
    """
    
    def __init__(self, processor_name: str, description: str):
        self.processor_name = processor_name
        self.description = description
        self.entity_counter = 0
        self.relationship_counter = 0
    
    def create_entity(
        self,
        entity_name: str,
        entity_type: EntityType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an entity with ontology validation."""
        self.entity_counter += 1
        
        entity = {
            "entity_id": f"{self.processor_name}_{self.entity_counter:04d}",
            "entity_name": entity_name,
            "entity_type": entity_type.value,
            "description": description,
            "metadata": metadata or {},
            "processor": self.processor_name
        }
        
        return entity
    
    def create_relationship(
        self,
        source: str,
        relationship_type: RelationshipType,
        target: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship with ontology validation."""
        self.relationship_counter += 1
        
        relationship = {
            "relationship_id": f"{self.processor_name}_rel_{self.relationship_counter:04d}",
            "source": source,
            "relationship_type": relationship_type.value,
            "target": target,
            "description": description,
            "metadata": metadata or {},
            "processor": self.processor_name
        }
        
        return relationship


# ============================================================================
# PROCESSOR 1: Section Metadata Processor (ALL Sections A-M)
# ============================================================================

class RFPSectionMetadataProcessor(GovconBaseProcessor):
    """
    Extracts section-level metadata for FAR 15.210 Uniform Contract Format.
    
    Handles:
    - Section A: Solicitation/Contract Form (SF-33)
    - Section B: Supplies/Services and Prices (CLINs/ELINs)
    - Section C: Description/Specs/Work Statement (SOW/PWS)
    - Section D: Packaging and Marking
    - Section E: Inspection and Acceptance
    - Section F: Deliveries or Performance (DPDs)
    - Section G: Contract Administration Data (POCs, reports)
    - Section H: Special Contract Requirements
    - Section I: Contract Clauses (FAR/DFARS)
    - Section J: List of Attachments (J-1, J-2, etc.)
    - Section K: Representations, Certifications
    - Section L: Instructions, Conditions, Notices to Offerors
    - Section M: Evaluation Factors for Award
    
    Examples from sample_requirements.json:
    - A001 (eligibility), A002 (incumbent), A003 (deadlines)
    - L001 (format requirements), L002 (validity period)
    - M001 (evaluation method), M002 (sub-factors)
    - H001 (key personnel restrictions)
    """
    
    def __init__(self):
        super().__init__(
            processor_name="section_metadata",
            description="Extract RFP section metadata and hierarchy per FAR 15.210"
        )
        
        # Section identification patterns
        self.section_patterns = {
            "A": [
                r"Section\s+A[\s:\.]*(?:Solicitation|Contract\s+Form)",
                r"SF-?33",
                r"Solicitation.*Contract.*Form"
            ],
            "B": [
                r"Section\s+B[\s:\.]*(?:Supplies|Services|Prices)",
                r"CLIN.*Schedule",
                r"Contract.*Line.*Item"
            ],
            "C": [
                r"Section\s+C[\s:\.]*(?:Description|Specifications|Work\s+Statement|SOW|PWS)",
                r"Statement\s+of\s+Work",
                r"Performance\s+Work\s+Statement"
            ],
            "D": [
                r"Section\s+D[\s:\.]*(?:Packaging|Marking)"
            ],
            "E": [
                r"Section\s+E[\s:\.]*(?:Inspection|Acceptance)"
            ],
            "F": [
                r"Section\s+F[\s:\.]*(?:Deliveries|Performance|DPD)",
                r"Delivery.*Schedule"
            ],
            "G": [
                r"Section\s+G[\s:\.]*(?:Contract\s+Administration|Admin)"
            ],
            "H": [
                r"Section\s+H[\s:\.]*(?:Special\s+Contract\s+Requirements)"
            ],
            "I": [
                r"Section\s+I[\s:\.]*(?:Contract\s+Clauses|FAR|DFARS)"
            ],
            "J": [
                r"Section\s+J[\s:\.]*(?:List\s+of\s+Attachments|Attachments)",
                r"Attachment.*List"
            ],
            "K": [
                r"Section\s+K[\s:\.]*(?:Representations|Certifications)"
            ],
            "L": [
                r"Section\s+L[\s:\.]*(?:Instructions|Conditions|Notices)",
                r"Instructions.*Offerors"
            ],
            "M": [
                r"Section\s+M[\s:\.]*(?:Evaluation\s+Factors|Evaluation\s+Criteria)",
                r"Evaluation.*Award"
            ]
        }
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract section entities and hierarchical relationships."""
        entities = []
        
        # Identify section from text
        for section_id, patterns in self.section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, document_chunk, re.IGNORECASE)
                if match:
                    # Extract section title
                    section_title = match.group(0)
                    
                    # Identify subsections (e.g., L.3.1, M.2.1)
                    subsection_pattern = rf"{section_id}\.\d+(?:\.\d+)*"
                    subsections = list(set(re.findall(subsection_pattern, document_chunk)))
                    
                    # Create SECTION entity
                    section_entity = self.create_entity(
                        entity_name=f"Section {section_id}",
                        entity_type=EntityType.SECTION,
                        description=section_title,
                        metadata={
                            "section_id": section_id,
                            "section_type": f"SECTION_{section_id}",
                            "subsections": subsections,
                            "page_number": metadata.get("page_number"),
                            "chunk_id": metadata.get("chunk_id")
                        }
                    )
                    entities.append(section_entity)
                    
                    # Create subsection entities and relationships
                    for subsection in subsections:
                        subsection_entity = self.create_entity(
                            entity_name=f"Section {subsection}",
                            entity_type=EntityType.SECTION,
                            description=f"Subsection {subsection}",
                            metadata={
                                "parent_section": section_id,
                                "subsection_id": subsection
                            }
                        )
                        entities.append(subsection_entity)
                        
                        # Parent→Child relationship
                        parent_child_rel = self.create_relationship(
                            source=f"Section {section_id}",
                            relationship_type=RelationshipType.CONTAINS,
                            target=f"Section {subsection}",
                            description=f"Section {section_id} contains subsection {subsection}"
                        )
                        entities.append(parent_child_rel)
                    
                    break  # Found match, move to next section
        
        return entities


# ============================================================================
# PROCESSOR 2: Requirements Processor (Shipley Methodology)
# ============================================================================

class ShipleyRequirementsProcessor(GovconBaseProcessor):
    """
    Extracts requirements using Shipley Proposal Guide methodology.
    
    References prompts/shipley_requirements_extraction.txt:
    - Compliance levels: Must/Shall, Should, May, Will
    - Requirement types: Functional, Performance, Interface, Design, Security, etc.
    - Cross-references evaluation factors (Section M)
    - Traceability to original RFP sections
    
    Examples from sample_requirements.json:
    - C001: Performance requirement (24-hour maintenance response)
    - H001: Personnel requirement (Key Personnel restrictions)
    - L001: Format requirement (page limits, font, margins)
    """
    
    def __init__(self):
        super().__init__(
            processor_name="shipley_requirements",
            description="Extract requirements per Shipley methodology with compliance levels"
        )
        
        # Shipley compliance level patterns
        self.compliance_patterns = {
            "MANDATORY": [
                r'\bshall\b', r'\bmust\b', r'\brequired\b', r'\bmandatory\b', 
                r'\bis\s+required\b', r'\bare\s+required\b'
            ],
            "IMPORTANT": [
                r'\bshould\b', r'\brecommended\b', r'\bis\s+recommended\b'
            ],
            "OPTIONAL": [
                r'\bmay\b', r'\boptional\b', r'\bdesirable\b', r'\bpreferred\b'
            ],
            "INFORMATIONAL": [
                r'\bwill\s+(?:provide|furnish|be)\b', r'\bgovernment\s+will\b'
            ]
        }
        
        # Requirement type classification keywords
        self.requirement_type_keywords = {
            "performance": [r'\bperformance\b', r'\bspeed\b', r'\btime\b', r'\bwithin\s+\d+\s+(hour|day|week)'],
            "security": [r'\bsecurity\b', r'\bencrypt', r'\bauthorization\b', r'\bauthentication\b'],
            "management": [r'\breport\b', r'\bmanage', r'\btrack\b', r'\bmonitor\b'],
            "technical": [r'\btechnical\b', r'\bsystem\b', r'\bsoftware\b', r'\bhardware\b'],
            "format": [r'\bpage\s+limit', r'\bfont\b', r'\bmargin', r'\bformat\b'],
            "schedule": [r'\bdeadline\b', r'\bdue\s+date', r'\bschedule\b', r'\btimeline\b'],
            "personnel": [r'\bpersonnel\b', r'\bstaff', r'\bkey\s+person', r'\bresume\b']
        }
    
    def _classify_requirement_type(self, text: str) -> str:
        """Classify requirement type per Shipley taxonomy."""
        for req_type, patterns in self.requirement_type_keywords.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                return req_type
        return "functional"
    
    def _determine_compliance_level(self, text: str) -> Optional[str]:
        """Determine Shipley compliance level from text."""
        for level, patterns in self.compliance_patterns.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                return level
        return None
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract requirements with Shipley classification."""
        entities = []
        
        # Split into sentences for requirement detection
        sentences = re.split(r'[.!?]\s+', document_chunk)
        
        for sentence in sentences:
            if len(sentence) < 20:  # Skip very short fragments
                continue
            
            # Determine compliance level
            compliance_level = self._determine_compliance_level(sentence)
            
            if compliance_level:
                # Classify requirement type
                req_type = self._classify_requirement_type(sentence)
                
                # Generate unique requirement ID
                req_id = f"REQ-{self.entity_counter + 1:04d}"
                
                # Create REQUIREMENT entity
                requirement_entity = self.create_entity(
                    entity_name=req_id,
                    entity_type=EntityType.REQUIREMENT,
                    description=sentence.strip()[:500],  # Truncate for description
                    metadata={
                        "requirement_id": req_id,
                        "full_text": sentence.strip(),
                        "compliance_level": compliance_level,
                        "requirement_type": req_type,
                        "source_section": metadata.get("section_id"),
                        "page_number": metadata.get("page_number"),
                        "shipley_methodology": True
                    }
                )
                entities.append(requirement_entity)
                
                # Relationship: SECTION → CONTAINS → REQUIREMENT
                if metadata.get("section_id"):
                    section_req_rel = self.create_relationship(
                        source=f"Section {metadata['section_id']}",
                        relationship_type=RelationshipType.CONTAINS,
                        target=req_id,
                        description=f"Requirement from Section {metadata['section_id']}"
                    )
                    entities.append(section_req_rel)
        
        return entities


# ============================================================================
# PROCESSOR 3: Evaluation Factor Processor (Section L↔M Critical Relationships)
# ============================================================================

class EvaluationFactorProcessor(GovconBaseProcessor):
    """
    Extracts Section M evaluation factors and maps to Section L instructions.
    
    CRITICAL from ONTOLOGY_EVOLUTION.md:
    - "Section L↔M relationships" mentioned 8 times as critical
    - L.3.1 instructions → M.2 Technical Approach evaluation
    - Page limits (L) → Factor weights (M)
    - "CRITICAL for Section M scoring"
    
    Examples from sample_requirements.json:
    - M001: Best Value tradeoff (Technical, Past Performance, Cost)
    - M002: Technical sub-factors (Staffing, Maintenance, Supply Chain)
    - L001: Technical Volume page limits
    """
    
    def __init__(self):
        super().__init__(
            processor_name="evaluation_factors",
            description="Extract Section M factors and map L↔M relationships"
        )
        
        # Evaluation factor patterns
        self.factor_patterns = {
            "technical": r"Technical\s+(?:Factor|Approach|Capability|Proposal)",
            "past_performance": r"Past\s+Performance",
            "cost_price": r"(?:Cost|Price|Pricing)\s+(?:Factor|Proposal|Evaluation)?",
            "management": r"Management\s+(?:Approach|Plan|Factor|Capability)",
            "key_personnel": r"Key\s+Personnel",
            "experience": r"(?:Corporate|Company|Organizational)\s+Experience",
            "staffing": r"Staffing\s+(?:Approach|Plan)",
            "transition": r"Transition\s+(?:Plan|Approach)"
        }
        
        # Importance keywords
        self.importance_patterns = [
            r'significantly\s+more\s+important',
            r'more\s+important\s+than',
            r'equal\s+(?:in\s+)?importance',
            r'equally\s+important',
            r'less\s+important'
        ]
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract evaluation factors and L↔M mappings."""
        entities = []
        
        # Only process Section M and Section L
        section_id = metadata.get("section_id")
        if section_id not in ["M", "L"]:
            return entities
        
        # Extract evaluation factors (Section M)
        if section_id == "M":
            for factor_key, pattern in self.factor_patterns.items():
                matches = re.finditer(pattern, document_chunk, re.IGNORECASE)
                for match in matches:
                    factor_name = match.group(0).strip()
                    
                    # Create EVALUATION_FACTOR entity
                    factor_entity = self.create_entity(
                        entity_name=factor_name,
                        entity_type=EntityType.EVALUATION_FACTOR,
                        description=f"Evaluation factor from Section M",
                        metadata={
                            "factor_type": factor_key,
                            "section_source": "M",
                            "page_number": metadata.get("page_number")
                        }
                    )
                    entities.append(factor_entity)
                    
                    # Extract relative importance
                    for importance_pattern in self.importance_patterns:
                        importance_match = re.search(
                            importance_pattern,
                            document_chunk[max(0, match.start()-200):min(len(document_chunk), match.end()+200)],
                            re.IGNORECASE
                        )
                        if importance_match:
                            factor_entity["metadata"]["relative_importance"] = importance_match.group(0)
                            break
                    
                    # Extract sub-factors (e.g., M.2.1, M.2.2)
                    subfactor_context = document_chunk[match.start():min(len(document_chunk), match.end()+500)]
                    subfactor_pattern = r"[Mm]\.\d+\.\d+[:\s]+([\w\s]+?)(?:\.|;|\n)"
                    submatches = re.findall(subfactor_pattern, subfactor_context)
                    
                    for subfactor in submatches[:5]:  # Limit to 5 sub-factors
                        subfactor_clean = subfactor.strip()
                        if len(subfactor_clean) > 5:
                            subfactor_entity = self.create_entity(
                                entity_name=subfactor_clean,
                                entity_type=EntityType.EVALUATION_FACTOR,
                                description=f"Sub-factor of {factor_name}",
                                metadata={
                                    "parent_factor": factor_key,
                                    "factor_level": "subfactor"
                                }
                            )
                            entities.append(subfactor_entity)
                            
                            # Parent→Child relationship
                            parent_subfactor_rel = self.create_relationship(
                                source=factor_name,
                                relationship_type=RelationshipType.CONTAINS,
                                target=subfactor_clean,
                                description="Parent evaluation factor contains sub-factor"
                            )
                            entities.append(parent_subfactor_rel)
        
        # Extract Section L instructions and map to Section M (CRITICAL!)
        elif section_id == "L":
            # Page limit instructions
            page_limit_match = re.search(r'(?:limited\s+to\s+|not\s+exceed\s+)?(\d+)\s+pages?', document_chunk, re.IGNORECASE)
            if page_limit_match:
                page_limit = int(page_limit_match.group(1))
                page_limit_entity = self.create_entity(
                    entity_name=f"Page Limit: {page_limit} pages",
                    entity_type=EntityType.REQUIREMENT,
                    description=f"Section L page limit requirement",
                    metadata={
                        "page_limit": page_limit,
                        "requirement_type": "format",
                        "section_source": "L",
                        "compliance_level": "MANDATORY"
                    }
                )
                entities.append(page_limit_entity)
                
                # L→M EVALUATES relationship (CRITICAL!)
                # Map to corresponding evaluation factor
                for factor_keyword in ["technical", "management", "past performance"]:
                    if re.search(factor_keyword, document_chunk, re.IGNORECASE):
                        l_to_m_rel = self.create_relationship(
                            source="Section L",
                            relationship_type=RelationshipType.EVALUATES,
                            target=f"{factor_keyword.title()} Factor",
                            description=f"Section L instructions govern Section M {factor_keyword} evaluation"
                        )
                        entities.append(l_to_m_rel)
        
        return entities


# ============================================================================
# PROCESSOR 4: CLIN/Pricing Processor (Section B)
# ============================================================================

class CLINPricingProcessor(GovconBaseProcessor):
    """
    Extracts Contract Line Item Numbers (CLINs) and pricing from Section B.
    
    Examples from sample_requirements.json:
    - B001: CLIN 0001 Firm-Fixed-Price base operations (366 days + 60 transition)
    
    CLINs are CONCEPT entities with financial attributes (per budget decision).
    """
    
    def __init__(self):
        super().__init__(
            processor_name="clin_pricing",
            description="Extract CLINs, ELINs, pricing from Section B"
        )
        
        self.clin_pattern = r'CLIN\s+(\d{4})'
        self.elin_pattern = r'ELIN\s+(\d{4})'
        self.price_pattern = r'\$\s*[\d,]+(?:\.\d{2})?'
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract CLIN entities and pricing relationships."""
        entities = []
        
        # Only process Section B (and potentially Section H for options)
        if metadata.get("section_id") not in ["B", "H"]:
            return entities
        
        # Extract CLINs
        clin_matches = re.finditer(self.clin_pattern, document_chunk)
        for match in clin_matches:
            clin_num = match.group(1)
            clin_id = f"CLIN {clin_num}"
            
            # Extract context around CLIN
            context_start = max(0, match.start() - 100)
            context_end = min(len(document_chunk), match.end() + 200)
            context = document_chunk[context_start:context_end]
            
            # Extract pricing
            price_match = re.search(self.price_pattern, context)
            price_value = price_match.group(0) if price_match else None
            
            # Extract contract type
            contract_type = None
            if re.search(r'Firm[- ]Fixed[- ]Price', context, re.IGNORECASE):
                contract_type = "FFP"
            elif re.search(r'Cost[- ]Plus', context, re.IGNORECASE):
                contract_type = "CPFF"
            elif re.search(r'Time[- ]and[- ]Materials', context, re.IGNORECASE):
                contract_type = "T&M"
            
            # Create CONCEPT entity (CLINs are contract concepts)
            clin_entity = self.create_entity(
                entity_name=clin_id,
                entity_type=EntityType.CONCEPT,
                description=context.strip()[:200],
                metadata={
                    "clin_number": clin_num,
                    "price": price_value,
                    "contract_type": contract_type,
                    "section_source": "B",
                    "page_number": metadata.get("page_number")
                }
            )
            entities.append(clin_entity)
            
            # Relationship: Section B CONTAINS CLIN
            section_clin_rel = self.create_relationship(
                source="Section B",
                relationship_type=RelationshipType.CONTAINS,
                target=clin_id,
                description="Section B pricing includes CLIN"
            )
            entities.append(section_clin_rel)
        
        return entities


# ============================================================================
# PROCESSOR 5: Deliverable Processor (Section F)
# ============================================================================

class DeliverableProcessor(GovconBaseProcessor):
    """
    Extracts deliverables from Section F (Deliveries or Performance).
    
    Added in Phase 3 per ONTOLOGY_EVOLUTION.md:
    - DELIVERABLE entity type explicitly required
    - Korean AI RFP Simulator tracks deliverables[] separately
    - Shipley methodology treats deliverables as key evaluation factors
    
    Examples from sample_qfg.json:
    - J001: GFFE (Government Furnished Facilities and Equipment)
    - Section F deliverables with due dates
    """
    
    def __init__(self):
        super().__init__(
            processor_name="deliverables",
            description="Extract deliverables and delivery schedules from Section F"
        )
        
        self.deliverable_keywords = [
            r'deliverable', r'report', r'documentation', r'plan', 
            r'manual', r'specification', r'design\s+document',
            r'(?:data\s+)?submission', r'product', r'item'
        ]
        
        # Date patterns for due dates
        self.date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4})'
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract DELIVERABLE entities."""
        entities = []
        
        # Process Section F or any section mentioning deliverables
        for keyword_pattern in self.deliverable_keywords:
            matches = re.finditer(keyword_pattern, document_chunk, re.IGNORECASE)
            for match in matches:
                # Extract context (sentence containing deliverable)
                start = max(0, match.start() - 150)
                end = min(len(document_chunk), match.end() + 150)
                context = document_chunk[start:end]
                
                # Extract deliverable name (look for capitalized phrases or numbered items)
                name_match = re.search(
                    r'(?:^|\n|\.\s+)([A-Z][A-Za-z\s]{5,50})(?:\.|:|,|\n)',
                    context
                )
                deliverable_name = name_match.group(1).strip() if name_match else match.group(0)
                
                # Skip if too generic
                if deliverable_name.lower() in ['deliverable', 'report', 'plan']:
                    continue
                
                # Extract due date if present
                due_date_match = re.search(self.date_pattern, context, re.IGNORECASE)
                due_date = due_date_match.group(0) if due_date_match else None
                
                # Create DELIVERABLE entity
                deliverable_entity = self.create_entity(
                    entity_name=deliverable_name,
                    entity_type=EntityType.DELIVERABLE,
                    description=context.strip()[:300],
                    metadata={
                        "section_source": metadata.get("section_id", "F"),
                        "page_number": metadata.get("page_number"),
                        "due_date": due_date
                    }
                )
                entities.append(deliverable_entity)
                
                # Relationship: Section F CONTAINS DELIVERABLE
                if metadata.get("section_id") == "F":
                    section_deliverable_rel = self.create_relationship(
                        source="Section F",
                        relationship_type=RelationshipType.CONTAINS,
                        target=deliverable_name,
                        description="Section F specifies deliverable"
                    )
                    entities.append(section_deliverable_rel)
        
        return entities


# ============================================================================
# PROCESSOR 6: Clause Processor (Section I FAR/DFARS)
# ============================================================================

class ClauseProcessor(GovconBaseProcessor):
    """
    Extracts FAR and DFARS clauses from Section I.
    
    Clauses are CLAUSE entities that APPLY_TO sections and requirements.
    """
    
    def __init__(self):
        super().__init__(
            processor_name="contract_clauses",
            description="Extract FAR/DFARS clauses from Section I"
        )
        
        self.clause_pattern = r'(FAR|DFARS)\s+(\d+\.\d+(?:-\d+)?)'
        self.clause_title_pattern = r'(FAR|DFARS)\s+\d+\.\d+(?:-\d+)?\s+([A-Z][A-Za-z\s]{10,80})'
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract CLAUSE entities."""
        entities = []
        
        # Only process Section I
        if metadata.get("section_id") != "I":
            return entities
        
        # Extract clauses with titles if available
        clause_matches = re.finditer(self.clause_title_pattern, document_chunk)
        processed_clauses = set()
        
        for match in clause_matches:
            clause_type = match.group(1)
            clause_title = match.group(2).strip()
            
            # Extract full clause reference
            full_match = re.search(r'(FAR|DFARS)\s+(\d+\.\d+(?:-\d+)?)', match.group(0))
            clause_num = full_match.group(2) if full_match else ""
            clause_id = f"{clause_type} {clause_num}"
            
            if clause_id in processed_clauses:
                continue
            processed_clauses.add(clause_id)
            
            # Create CLAUSE entity
            clause_entity = self.create_entity(
                entity_name=clause_id,
                entity_type=EntityType.CLAUSE,
                description=f"{clause_type} clause {clause_num}: {clause_title}",
                metadata={
                    "clause_number": clause_num,
                    "clause_type": clause_type,
                    "clause_title": clause_title,
                    "section_source": "I"
                }
            )
            entities.append(clause_entity)
            
            # Relationship: Section I CONTAINS CLAUSE
            section_clause_rel = self.create_relationship(
                source="Section I",
                relationship_type=RelationshipType.CONTAINS,
                target=clause_id,
                description="Contract clauses in Section I"
            )
            entities.append(section_clause_rel)
        
        # Fallback: Extract clauses without titles
        if not processed_clauses:
            simple_matches = re.findall(self.clause_pattern, document_chunk)
            for clause_type, clause_num in simple_matches:
                clause_id = f"{clause_type} {clause_num}"
                
                if clause_id in processed_clauses:
                    continue
                processed_clauses.add(clause_id)
                
                clause_entity = self.create_entity(
                    entity_name=clause_id,
                    entity_type=EntityType.CLAUSE,
                    description=f"{clause_type} clause {clause_num}",
                    metadata={
                        "clause_number": clause_num,
                        "clause_type": clause_type,
                        "section_source": "I"
                    }
                )
                entities.append(clause_entity)
        
        return entities


# ============================================================================
# PROCESSOR 7: Attachment/Document Processor (Section J)
# ============================================================================

class AttachmentProcessor(GovconBaseProcessor):
    """
    Extracts attachments from Section J (List of Attachments).
    
    Examples from sample_requirements.json:
    - J001: Attachment 0014 (GFFE list)
    
    Attachments are DOCUMENT entities that SUPPORT sections and requirements.
    """
    
    def __init__(self):
        super().__init__(
            processor_name="attachments",
            description="Extract attachments from Section J"
        )
        
        self.attachment_patterns = [
            r'Attachment\s+(\d{4}|[A-Z]-?\d+)',
            r'Exhibit\s+([A-Z]|\d+)',
            r'Appendix\s+([A-Z]|\d+)'
        ]
    
    def process(self, document_chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract DOCUMENT entities for attachments."""
        entities = []
        
        # Process Section J
        if metadata.get("section_id") != "J":
            return entities
        
        processed_attachments = set()
        
        # Extract attachments
        for pattern in self.attachment_patterns:
            attachment_matches = re.finditer(pattern, document_chunk, re.IGNORECASE)
            for match in attachment_matches:
                attachment_num = match.group(1)
                attachment_id = f"{match.group(0)}"
                
                if attachment_id in processed_attachments:
                    continue
                processed_attachments.add(attachment_id)
                
                # Extract context for description
                context_start = max(0, match.start() - 50)
                context_end = min(len(document_chunk), match.end() + 150)
                context = document_chunk[context_start:context_end]
                
                # Extract title if present (usually follows colon or dash)
                title_match = re.search(
                    rf'{re.escape(match.group(0))}[\s:–-]+([A-Za-z][A-Za-z0-9\s]{{5,80}})',
                    context
                )
                title = title_match.group(1).strip() if title_match else None
                
                # Create DOCUMENT entity
                document_entity = self.create_entity(
                    entity_name=attachment_id,
                    entity_type=EntityType.DOCUMENT,
                    description=title if title else f"RFP Attachment {attachment_num}",
                    metadata={
                        "attachment_number": attachment_num,
                        "attachment_title": title,
                        "section_source": "J"
                    }
                )
                entities.append(document_entity)
                
                # Relationship: Section J REFERENCES DOCUMENT
                section_attachment_rel = self.create_relationship(
                    source="Section J",
                    relationship_type=RelationshipType.REFERENCES,
                    target=attachment_id,
                    description="Section J lists attachment"
                )
                entities.append(section_attachment_rel)
        
        return entities
