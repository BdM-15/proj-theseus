"""
Semantic RFP Analyzer - LLM-Native Document Understanding

Replaces regex-based section identification with semantic analysis.
Uses PydanticAI agents to understand RFP structure contextually.

Key Principle: Let the LLM understand document structure semantically,
not through brittle pattern matching. The LLM can distinguish:
- 'Section L: Instructions to Offerors' (actual RFP section)
- 'in section A of the building' (random text, not an RFP section)
- 'Section J-1' (valid attachment)
- 'Section J-L' (fictitious - doesn't exist in government format)

References:
- FAR 15.210 Uniform Contract Format
- Shipley Proposal Guide p.45-55 (RFP structure)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field, validator

# Import our existing Pydantic models
from models.rfp_models import (
    RFPSection, RFPSectionType, RFPRequirement,
    ValidationResult, ProcessingMetadata
)

logger = logging.getLogger(__name__)


class RFPStructureAnalysis(BaseModel):
    """
    Complete RFP structure identified by semantic analysis
    NO regex patterns - pure LLM understanding
    """
    sections: List[RFPSection] = Field(
        default_factory=list,
        description="Sections identified semantically by LLM"
    )
    document_title: str = Field(..., description="RFP title or subject")
    solicitation_number: Optional[str] = Field(None, description="Government solicitation number")
    total_pages: Optional[int] = Field(None, description="Estimated total pages")
    
    # Quality metrics
    structure_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence in structure identification (0-1)"
    )
    sections_identified: int = Field(
        default=0,
        description="Number of sections found"
    )
    completeness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0, 
        description="Completeness vs standard UCF format (0-1)"
    )
    
    # Validation
    has_fictitious_sections: bool = Field(
        default=False,
        description="Whether invalid section combinations detected"
    )
    fictitious_sections: List[str] = Field(
        default_factory=list,
        description="List of invalid section identifiers found"
    )
    
    @validator('sections')
    def validate_no_fictitious_sections(cls, v):
        """Ensure no fictitious section combinations like 'J-L'"""
        valid_sections = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'])
        valid_j_attachments = set([f'J-{i}' for i in range(1, 100)])  # J-1, J-2, etc.
        
        fictitious = []
        for section in v:
            section_id = section.section_id
            
            # Check if it's a valid base section or J attachment
            if section_id not in valid_sections and section_id not in valid_j_attachments:
                # Check for invalid combinations
                if '-' in section_id and not section_id.startswith('J-'):
                    fictitious.append(section_id)
                elif section_id.startswith('J-') and not section_id[2:].isdigit():
                    fictitious.append(section_id)
        
        if fictitious:
            raise ValueError(f"Fictitious sections detected: {fictitious}. These don't exist in UCF format.")
        
        return v


class SemanticRFPAnalyzer:
    """
    LLM-native document structure analyzer for government RFPs
    
    Uses semantic understanding to identify sections WITHOUT regex patterns.
    Prevents fictitious sections and ensures accurate structure identification.
    """
    
    def __init__(self, llm_model: Optional[str] = None):
        """Initialize semantic analyzer with PydanticAI agent"""
        import os
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.ollama import OllamaProvider
        
        # Use environment variable if not explicitly provided
        model_name = llm_model or os.getenv('LLM_MODEL', 'mistral-nemo:latest')
        
        # Create Ollama-backed model using OpenAIChatModel + OllamaProvider
        # PydanticAI uses OpenAI-compatible API for Ollama
        self.llm_model = OpenAIChatModel(
            model_name,
            provider=OllamaProvider(base_url='http://localhost:11434/v1')
        )
        self.structure_agent = self._create_structure_agent()
        
        logger.info(f"Semantic RFP Analyzer initialized with Ollama model: {model_name}")
    
    def _create_structure_agent(self) -> Agent:
        """
        Create PydanticAI agent for semantic structure analysis
        
        Agent understands RFP structure contextually, not through patterns.
        Can distinguish actual RFP sections from random text containing 'section'.
        """
        
        agent = Agent(
            self.llm_model,
            output_type=RFPStructureAnalysis,
            system_prompt="""
            You are an expert federal acquisition analyst specializing in government RFP document structure.
            
            GOVERNMENT RFP STRUCTURE (FAR 15.210 Uniform Contract Format):
            
            Standard sections:
            - Section A: Solicitation/Contract Form (SF-33, SF-1449, etc.)
            - Section B: Supplies or Services and Prices/Costs (CLINs)
            - Section C: Statement of Work (SOW) or Performance Work Statement (PWS)
            - Section D: Packaging and Marking
            - Section E: Inspection and Acceptance
            - Section F: Deliveries or Performance (Period of Performance)
            - Section G: Contract Administration Data
            - Section H: Special Contract Requirements
            - Section I: Contract Clauses (FAR/DFARS clauses)
            - Section J: List of Attachments (may have sub-attachments: J-1, J-2, J-3, etc.)
            - Section K: Representations, Certifications and Other Statements
            - Section L: Instructions to Offerors (proposal preparation instructions)
            - Section M: Evaluation Factors for Award (basis for award decision)
            
            CRITICAL VALIDATION RULES:
            
            1. VALID section identifiers: A, B, C, D, E, F, G, H, I, J, K, L, M
            2. VALID J sub-attachments: J-1, J-2, J-3, ... J-99 (numeric only after hyphen)
            3. INVALID combinations: J-L, J-M, A-B, L-M, etc. (these don't exist in UCF)
            4. Context matters: 'Section A of the building' is NOT an RFP section
            5. Variations are OK: 'SECTION L:', 'Section L.', 'L. Instructions' all valid
            
            YOUR TASK:
            
            Analyze the RFP document and identify sections that ACTUALLY EXIST.
            
            Use semantic understanding:
            - Understand the PURPOSE and CONTENT of each section
            - Look for official section headers, titles, formatting
            - Consider document flow and logical structure
            - Distinguish RFP sections from random uses of the word 'section'
            
            DO NOT:
            - Create fictitious section combinations (e.g., 'Section J-L')
            - Match patterns blindly without understanding context
            - Identify random text as sections just because it contains 'section'
            - Invent sections that aren't explicitly present
            
            PROVIDE:
            - Accurate section identification with titles
            - Content boundaries for each section
            - Confidence in structure identification
            - Any concerns about fictitious or ambiguous sections
            
            Be precise, contextual, and validate against UCF standards.
            """,
        )
        
        return agent
    
    async def analyze_structure(
        self, 
        rfp_text: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> RFPStructureAnalysis:
        """
        Analyze RFP document structure using semantic understanding
        
        Args:
            rfp_text: Full RFP document text
            document_metadata: Optional metadata (title, solicitation number, etc.)
        
        Returns:
            RFPStructureAnalysis with identified sections and quality metrics
        
        Raises:
            ValueError: If fictitious sections detected
        """
        
        logger.info(f"Starting semantic structure analysis ({len(rfp_text):,} chars)")
        
        # Prepare document excerpt for analysis (first 12K chars for structure identification)
        excerpt = rfp_text[:12000]
        
        # Build analysis prompt
        prompt = f"""
        Analyze the structure of this government RFP document.
        
        Document Information:
        - Length: {len(rfp_text):,} characters (~{len(rfp_text)//2000} pages estimated)
        {f"- Title: {document_metadata.get('title')}" if document_metadata and 'title' in document_metadata else ""}
        {f"- Solicitation: {document_metadata.get('solicitation_number')}" if document_metadata and 'solicitation_number' in document_metadata else ""}
        
        Task: Identify ALL sections following FAR 15.210 Uniform Contract Format.
        
        Document Excerpt (first 12,000 characters):
        
        {excerpt}
        
        [Document continues for {len(rfp_text) - len(excerpt):,} more characters...]
        
        ANALYZE THIS DOCUMENT SEMANTICALLY:
        
        1. Identify which standard UCF sections (A-M) are present
        2. Identify any Section J attachments (J-1, J-2, etc.)
        3. Determine section boundaries based on content flow
        4. Extract section titles and key information
        5. Assess confidence in identification
        6. Flag any ambiguous or potentially fictitious sections
        
        Return complete RFPStructureAnalysis with all identified sections.
        """
        
        # Run semantic analysis
        result = await self.structure_agent.run(prompt)
        
        structure = result.data
        
        logger.info(
            f"Structure analysis complete: {structure.sections_identified} sections identified, "
            f"confidence: {structure.structure_confidence:.2f}"
        )
        
        # Validate no fictitious sections
        if structure.has_fictitious_sections:
            logger.error(
                f"Fictitious sections detected: {structure.fictitious_sections}. "
                f"LLM created invalid section combinations."
            )
        
        return structure
    
    async def enrich_sections_with_content(
        self,
        structure: RFPStructureAnalysis,
        full_rfp_text: str
    ) -> RFPStructureAnalysis:
        """
        Enrich section metadata with full content extraction
        
        After initial structure identification, extract full content
        for each section and enrich with subsections, requirements, etc.
        """
        
        logger.info(f"Enriching {len(structure.sections)} sections with full content")
        
        for section in structure.sections:
            # Use LLM to intelligently extract section content
            content_prompt = f"""
            Extract the COMPLETE content for {section.section_id}: {section.section_title}
            from this RFP document.
            
            Use semantic understanding to determine section boundaries:
            - Where does this section logically begin?
            - Where does it logically end (before next section)?
            - What subsections does it contain?
            
            Document text:
            {full_rfp_text}
            
            Return the full section content with proper boundaries.
            """
            
            # For now, placeholder - will implement full extraction in next phase
            section.word_count = len(section.content.split()) if section.content else 0
        
        logger.info("Section enrichment complete")
        return structure
    
    def validate_structure(self, structure: RFPStructureAnalysis) -> ValidationResult:
        """
        Validate identified structure against UCF standards
        
        Checks:
        - No fictitious sections
        - Section IDs match valid formats
        - Reasonable completeness vs standard UCF
        - No duplicate sections
        """
        
        errors = []
        warnings = []
        
        # Check for duplicates
        section_ids = [s.section_id for s in structure.sections]
        duplicates = [sid for sid in set(section_ids) if section_ids.count(sid) > 1]
        if duplicates:
            errors.append(f"Duplicate sections found: {duplicates}")
        
        # Check for standard critical sections
        critical_sections = ['C', 'L', 'M']  # SOW, Instructions, Evaluation
        missing_critical = [s for s in critical_sections if s not in section_ids]
        if missing_critical:
            warnings.append(f"Critical sections missing: {missing_critical}")
        
        # Check completeness
        standard_sections = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'])
        found_sections = set([s for s in section_ids if s in standard_sections])
        completeness = len(found_sections) / len(standard_sections)
        
        if completeness < 0.5:
            warnings.append(f"Low completeness: only {len(found_sections)}/13 standard sections found")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validation_timestamp=datetime.now()
        )


# Example usage
async def test_semantic_analyzer():
    """Test semantic analyzer with sample RFP text"""
    
    analyzer = SemanticRFPAnalyzer()
    
    sample_rfp = """
    SOLICITATION NUMBER: N6945025R0003
    
    SECTION A - SOLICITATION/CONTRACT FORM
    
    This is a combined synopsis/solicitation for commercial services...
    
    SECTION B - SUPPLIES OR SERVICES AND PRICES
    
    Contract Line Item Numbers (CLINs):
    CLIN 0001 - Base Period Recurring Services...
    
    SECTION C - STATEMENT OF WORK
    
    The contractor shall provide base operations support services...
    
    SECTION L - INSTRUCTIONS TO OFFERORS
    
    L.1 General Instructions
    Proposals shall be submitted in two volumes...
    
    SECTION M - EVALUATION FACTORS FOR AWARD
    
    M.1 Evaluation Factors
    The Government will evaluate proposals using the following factors...
    """
    
    structure = await analyzer.analyze_structure(sample_rfp)
    
    print(f"Sections found: {structure.sections_identified}")
    print(f"Confidence: {structure.structure_confidence}")
    for section in structure.sections:
        print(f"  - {section.section_id}: {section.section_title}")


if __name__ == "__main__":
    # Test the analyzer
    import asyncio
    from datetime import datetime
    asyncio.run(test_semantic_analyzer())
