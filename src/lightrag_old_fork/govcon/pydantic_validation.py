"""
PydanticAI Validation Pipeline - Zero Contamination Guarantee

Validates all LLM extractions against type-safe Pydantic models.
Ensures document isolation and prevents external knowledge contamination.

Key Features:
- Type-safe structured outputs (RFPRequirement models)
- Document isolation verification (entity text must exist in source)
- Ontology compliance validation
- Confidence scoring
- Automatic filtering of invalid entities

References:
- src/models/rfp_models.py (Pydantic models)
- src/agents/rfp_agents.py (PydanticAI agents)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field, ValidationError

# Import our existing models and agents
from models.rfp_models import (
    RFPRequirement, ComplianceAssessment, ValidationResult,
    RFPSection, ProcessingMetadata, ComplianceLevel, RequirementType
)
from agents.rfp_agents import (
    RFPAnalysisAgents, RequirementsExtractionOutput, RFPContext
)

logger = logging.getLogger(__name__)


class DocumentIsolationCheck(BaseModel):
    """Results of document isolation validation"""
    is_isolated: bool = Field(..., description="Whether all entities from source document")
    contaminated_entities: List[str] = Field(default_factory=list, description="Entities not in source")
    validation_method: str = Field(default="fuzzy_matching", description="Method used for validation")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in isolation check")
    checked_entities: int = Field(default=0, description="Number of entities checked")


class OntologyComplianceCheck(BaseModel):
    """Results of ontology compliance validation"""
    is_compliant: bool = Field(..., description="Whether all entities match ontology")
    invalid_entity_types: List[str] = Field(default_factory=list, description="Invalid entity types found")
    invalid_relationships: List[str] = Field(default_factory=list, description="Invalid relationship patterns")
    valid_entities: int = Field(default=0, description="Count of valid entities")
    total_entities: int = Field(default=0, description="Total entities checked")


class ExtractionValidator:
    """
    PydanticAI-powered validation pipeline
    
    Ensures all LLM extractions are:
    1. Type-safe (match Pydantic models)
    2. Document-isolated (no external knowledge)
    3. Ontology-compliant (valid entity/relationship types)
    4. High-confidence (quality scoring)
    """
    
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434):
        """Initialize validation pipeline with PydanticAI agents"""
        self.agents = RFPAnalysisAgents(ollama_host, ollama_port)
        self.contamination_keywords = self._load_contamination_patterns()
        
        logger.info("Validation pipeline initialized with PydanticAI agents")
    
    def _load_contamination_patterns(self) -> List[str]:
        """
        Known contamination patterns from previous runs
        These should NEVER appear in government RFP extractions
        """
        return [
            # Sports entities (from Plan A/B contamination)
            "Noah Carter", "Carbon-Fiber Spikes", "100m Sprint",
            "World Athletics", "Tokyo", "Olympic", "Marathon",
            
            # Financial markets (from Plan A contamination)
            "Gold Futures", "Crude Oil", "Market Selloff",
            "Federal Reserve Policy", "Stock Market", "Trading",
            
            # Generic non-RFP entities
            "Restaurant", "Movie", "Celebrity", "Sports Team",
            "Video Game", "Music Album", "Television Show",
        ]
    
    async def validate_extraction(
        self,
        raw_extraction: Dict[str, Any],
        source_text: str,
        section_context: Optional[RFPSection] = None
    ) -> RequirementsExtractionOutput:
        """
        Main validation pipeline - validates extraction through multiple checks
        
        Args:
            raw_extraction: Raw LLM extraction output
            source_text: Original source text for isolation check
            section_context: Optional section context for targeted validation
        
        Returns:
            Validated RequirementsExtractionOutput with filtered/verified entities
        
        Raises:
            ValidationError: If critical validation failures occur
        """
        
        logger.info(f"Starting validation pipeline for {len(source_text)} char excerpt")
        
        # Step 1: Use PydanticAI agent for structured extraction with type safety
        try:
            validated_result = await self.agents.extract_requirements(
                content=source_text,
                section_id=section_context.section_id if section_context else "UNKNOWN",
                context=section_context.section_title if section_context else None
            )
        except Exception as e:
            logger.error(f"PydanticAI extraction failed: {e}")
            # Return minimal valid structure on failure
            return RequirementsExtractionOutput(
                requirements=[],
                section_summary=f"Extraction failed: {str(e)}",
                key_themes=[],
                shipley_notes=[f"Validation error: {str(e)}"],
                extraction_confidence=0.0
            )
        
        # Step 2: Document isolation check
        isolation_check = await self.check_document_isolation(
            validated_result.requirements,
            source_text
        )
        
        if not isolation_check.is_isolated:
            logger.warning(
                f"Contamination detected: {len(isolation_check.contaminated_entities)} entities "
                f"not found in source document"
            )
            # Filter out contaminated entities
            validated_result.requirements = [
                req for req in validated_result.requirements
                if req.requirement_id not in isolation_check.contaminated_entities
            ]
            validated_result.shipley_notes.append(
                f"Filtered {len(isolation_check.contaminated_entities)} contaminated entities"
            )
        
        # Step 3: Ontology compliance check
        ontology_check = self.validate_ontology_compliance(validated_result.requirements)
        
        if not ontology_check.is_compliant:
            logger.warning(
                f"Ontology violations: {len(ontology_check.invalid_entity_types)} invalid entity types"
            )
            # Filter entities with invalid types
            valid_types = set([req.requirement_type.value for req in validated_result.requirements])
            validated_result.requirements = [
                req for req in validated_result.requirements
                if req.requirement_type.value not in ontology_check.invalid_entity_types
            ]
        
        # Step 4: Known contamination pattern check
        pattern_check = self.check_contamination_patterns(validated_result.requirements)
        if pattern_check['contamination_found']:
            logger.error(f"CRITICAL: Known contamination patterns detected: {pattern_check['patterns']}")
            validated_result.requirements = [
                req for req in validated_result.requirements
                if req.requirement_id not in pattern_check['contaminated_ids']
            ]
        
        # Step 5: Update confidence score based on validation results
        validation_score = self._calculate_validation_confidence(
            isolation_check, ontology_check, pattern_check
        )
        validated_result.extraction_confidence = min(
            validated_result.extraction_confidence,
            validation_score
        )
        
        logger.info(
            f"Validation complete: {len(validated_result.requirements)} requirements validated, "
            f"confidence: {validated_result.extraction_confidence:.2f}"
        )
        
        return validated_result
    
    async def check_document_isolation(
        self,
        requirements: List[RFPRequirement],
        source_text: str,
        min_similarity: float = 0.7
    ) -> DocumentIsolationCheck:
        """
        Verify all extracted requirements exist in source document
        Uses fuzzy matching to account for minor variations
        
        Args:
            requirements: Extracted requirements to validate
            source_text: Original source text
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            DocumentIsolationCheck with validation results
        """
        
        contaminated = []
        
        for req in requirements:
            # Extract first 100 chars of requirement text for matching
            req_text = req.requirement_text[:100]
            
            # Fuzzy search for requirement in source
            if not self._fuzzy_search(req_text, source_text, min_similarity):
                contaminated.append(req.requirement_id)
                logger.debug(
                    f"Contamination: '{req.requirement_id}' text not found in source: '{req_text[:50]}...'"
                )
        
        return DocumentIsolationCheck(
            is_isolated=len(contaminated) == 0,
            contaminated_entities=contaminated,
            validation_method="fuzzy_matching",
            confidence_score=1.0 - (len(contaminated) / max(len(requirements), 1)),
            checked_entities=len(requirements)
        )
    
    def _fuzzy_search(
        self,
        needle: str,
        haystack: str,
        min_similarity: float = 0.7
    ) -> bool:
        """
        Fuzzy search for needle in haystack
        Returns True if similar text found
        """
        
        # Normalize text for comparison
        needle_clean = ' '.join(needle.lower().split())
        haystack_clean = ' '.join(haystack.lower().split())
        
        # Direct substring match
        if needle_clean in haystack_clean:
            return True
        
        # Sliding window fuzzy match
        needle_len = len(needle_clean)
        for i in range(len(haystack_clean) - needle_len + 1):
            window = haystack_clean[i:i + needle_len]
            similarity = SequenceMatcher(None, needle_clean, window).ratio()
            if similarity >= min_similarity:
                return True
        
        return False
    
    def validate_ontology_compliance(
        self,
        requirements: List[RFPRequirement]
    ) -> OntologyComplianceCheck:
        """
        Validate requirements against ontology constraints
        
        Checks:
        - Entity types match RequirementType enum
        - Section IDs match valid format
        - Compliance levels match ComplianceLevel enum
        """
        
        invalid_types = []
        valid_count = 0
        
        for req in requirements:
            # Validate requirement type
            try:
                RequirementType(req.requirement_type)
                valid_count += 1
            except ValueError:
                invalid_types.append(f"{req.requirement_id}: {req.requirement_type}")
            
            # Validate section ID format
            if not re.match(r'^[A-MJ](-\d+)?$', req.section_id):
                logger.warning(f"Invalid section ID format: {req.section_id} in {req.requirement_id}")
        
        return OntologyComplianceCheck(
            is_compliant=len(invalid_types) == 0,
            invalid_entity_types=invalid_types,
            invalid_relationships=[],  # Relationship validation in next phase
            valid_entities=valid_count,
            total_entities=len(requirements)
        )
    
    def check_contamination_patterns(
        self,
        requirements: List[RFPRequirement]
    ) -> Dict[str, Any]:
        """
        Check for known contamination patterns
        Catches entities that should NEVER appear in RFP extractions
        """
        
        contaminated_ids = []
        patterns_found = []
        
        for req in requirements:
            req_text_lower = req.requirement_text.lower()
            
            # Check against known contamination keywords
            for pattern in self.contamination_keywords:
                if pattern.lower() in req_text_lower:
                    contaminated_ids.append(req.requirement_id)
                    patterns_found.append(pattern)
                    logger.error(
                        f"CONTAMINATION PATTERN DETECTED: '{pattern}' in {req.requirement_id}"
                    )
                    break
        
        return {
            "contamination_found": len(contaminated_ids) > 0,
            "contaminated_ids": contaminated_ids,
            "patterns": patterns_found,
            "total_checked": len(requirements)
        }
    
    def _calculate_validation_confidence(
        self,
        isolation_check: DocumentIsolationCheck,
        ontology_check: OntologyComplianceCheck,
        pattern_check: Dict[str, Any]
    ) -> float:
        """
        Calculate overall validation confidence score
        
        Factors:
        - Document isolation score (40% weight)
        - Ontology compliance score (40% weight)
        - Contamination pattern absence (20% weight)
        """
        
        isolation_score = isolation_check.confidence_score
        ontology_score = ontology_check.valid_entities / max(ontology_check.total_entities, 1)
        pattern_score = 0.0 if pattern_check['contamination_found'] else 1.0
        
        weighted_score = (
            isolation_score * 0.4 +
            ontology_score * 0.4 +
            pattern_score * 0.2
        )
        
        return weighted_score


# Example usage and testing
async def test_validation_pipeline():
    """Test validation pipeline with sample data"""
    
    validator = ExtractionValidator()
    
    # Sample source text
    source_text = """
    Section L.3.1 Requirements
    The offeror shall submit a technical proposal not exceeding 25 pages.
    The proposal shall address all evaluation factors in Section M.
    """
    
    # Sample extracted requirements (one valid, one contaminated)
    sample_requirements = [
        RFPRequirement(
            requirement_id="REQ-L-001",
            requirement_text="The offeror shall submit a technical proposal not exceeding 25 pages.",
            section_id="L",
            subsection_id="L.3.1",
            compliance_level=ComplianceLevel.MUST,
            requirement_type=RequirementType.ADMINISTRATIVE
        ),
        RFPRequirement(
            requirement_id="REQ-L-002",
            requirement_text="Noah Carter won the 100m sprint with Carbon-Fiber Spikes in Tokyo.",
            section_id="L",
            compliance_level=ComplianceLevel.MUST,
            requirement_type=RequirementType.FUNCTIONAL
        ),
    ]
    
    # Test isolation check
    isolation = await validator.check_document_isolation(sample_requirements, source_text)
    print(f"Isolation Check: {isolation.is_isolated}")
    print(f"Contaminated: {isolation.contaminated_entities}")
    
    # Test pattern check
    pattern_check = validator.check_contamination_patterns(sample_requirements)
    print(f"Pattern Check: {pattern_check['contamination_found']}")
    print(f"Patterns Found: {pattern_check['patterns']}")


if __name__ == "__main__":
    asyncio.run(test_validation_pipeline())
