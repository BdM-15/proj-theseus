# Production Fork Specification: lightrag-govcon

**Version**: 1.0.0  
**Date**: October 4, 2025  
**Based On**: lightrag-hku==1.4.9  
**Approach**: LLM-Native Semantic Understanding + PydanticAI Validation

---

## Executive Summary

This fork transforms Light RAG into a government contracting-specific RAG system through:
1. **Semantic RFP Understanding** (LLM-native, NO regex)
2. **Ontology-Enhanced Extraction** (government contracting domain knowledge)
3. **PydanticAI Validation** (guaranteed structure + zero contamination)

**Key Principle**: Let LLMs understand document structure semantically. Use PydanticAI to ensure quality and prevent contamination.

---

## Why This Fork Exists

### Problem with Generic LightRAG

Generic LightRAG cannot understand government contracting because:
- Never seen RFPs in training data
- Doesn't know what CLINs, FAR clauses, or Section LM relationships are
- Extracts generic entities ("person", "location") not domain concepts
- Can't distinguish contractor requirements ("shall") from suggestions ("may")

### Problem with Regex Preprocessing (Path A)

Plan A's regex-based chunking created MORE problems:
- Generated fictitious entities ("RFP Section J-L" doesn't exist)
- Cut content at arbitrary regex boundaries
- Created brittle patterns that failed on real-world variations
- Over-extraction (772 entities) was noise, not quality

### Solution: LLM-Native + Ontology + Validation

**Let the LLM understand semantically**, then:
1. Inject government contracting ontology into extraction prompts
2. Validate all outputs with PydanticAI type-safe models
3. Verify document isolation (no external knowledge contamination)

---

## Architecture Overview

\\\
RFP PDF
  
[LLM: Semantic Structure Analysis]
  - Understands "Section L: Instructions" semantically
  - Knows "Section J-L" is fictitious
  - Distinguishes RFP sections from random text
  
[Ontology-Enhanced LightRAG]
  - Custom entity types: SECTION, REQUIREMENT, CLIN, FAR_CLAUSE
  - Government contracting relationship patterns
  - Domain-specific extraction prompts
  
[PydanticAI Validation Pipeline]
  - RFPRequirement models enforce structure
  - Validators catch invalid entities
  - Document isolation verification
  
[Clean Knowledge Graph]
  - Zero contamination
  - Type-safe entities
  - Domain-valid relationships
  - Traceable to source
\\\

---

## Fork Structure

\\\
src/lightrag_govcon/
 __init__.py                 # Fork identification + version
 lightrag.py                 # Modified main class
 operate.py                  # Enhanced extraction with ontology
 prompt.py                   # Government contracting prompts
 govcon/                     # Government contracting extensions
    __init__.py
    semantic_analyzer.py   # LLM-native document understanding
    ontology_integration.py # Ontology injection into prompts
    pydantic_validation.py  # PydanticAI validation pipeline
    quality_assurance.py    # Document isolation checks
 api/                        # Original LightRAG API (preserved)
 kg/                         # Knowledge graph (preserved)
 llm/                        # LLM integrations (preserved)
 tools/                      # Utilities (preserved)
\\\

---

## Key Modifications

### 1. Semantic Structure Analyzer (NO Regex)

**File**: \src/lightrag_govcon/govcon/semantic_analyzer.py\

\\\python
class SemanticRFPAnalyzer:
    \"\"\"
    LLM-native document structure understanding
    Replaces regex-based section identification with semantic analysis
    \"\"\"
    
    async def analyze_structure(self, rfp_text: str) -> RFPStructure:
        \"\"\"
        Let LLM understand document structure semantically
        
        CRITICAL: NO regex patterns. LLM understands:
        - "Section L: Instructions to Offerors" = RFP section
        - "in section A of the building" = not an RFP section
        - "Section J-1" = valid attachment
        - "Section J-L" = fictitious (doesn't exist)
        \"\"\"
        
        prompt = f\"\"\"
        Analyze this government RFP document structure.
        
        Government RFPs follow FAR 15.210 Uniform Contract Format:
        Section A: Solicitation/Contract Form
        Section B: Supplies or Services
        Section C: Statement of Work (SOW/PWS)
        Section D: Packaging and Marking
        Section E: Inspection and Acceptance
        Section F: Deliveries or Performance
        Section G: Contract Administration Data
        Section H: Special Contract Requirements
        Section I: Contract Clauses
        Section J: List of Attachments (may have J-1, J-2 sub-attachments)
        Section K: Representations, Certifications
        Section L: Instructions to Offerors
        Section M: Evaluation Factors for Award
        
        IDENTIFY sections that ACTUALLY EXIST in this document.
        DO NOT create fictitious combinations like "Section J-L".
        UNDERSTAND context semantically.
        
        Document excerpt:
        {rfp_text[:8000]}
        \"\"\"
        
        # LLM returns validated structure
        result = await self.structure_agent.run(
            prompt,
            result_type=RFPStructure  # PydanticAI validation
        )
        
        return result.data
\\\

### 2. Ontology-Enhanced Extraction

**File**: \src/lightrag_govcon/govcon/ontology_integration.py\

\\\python
class OntologyInjector:
    \"\"\"
    Injects government contracting ontology into LightRAG extraction prompts
    Replaces generic entity types with domain-specific concepts
    \"\"\"
    
    GOVERNMENT_ENTITY_TYPES = [
        "SECTION",              # RFP sections (A-M)
        "REQUIREMENT",          # Contractor obligations (shall/must)
        "CLIN",                 # Contract Line Item Numbers
        "FAR_CLAUSE",           # Federal Acquisition Regulation clauses
        "DELIVERABLE",          # Required deliverables/reports
        "EVALUATION_FACTOR",    # Section M evaluation criteria
        "ORGANIZATION",         # Agencies, contractors
        "SECURITY_REQUIREMENT", # Compliance mandates
        "PERFORMANCE_METRIC",   # Performance standards
    ]
    
    RELATIONSHIP_PATTERNS = {
        "Section L  Section M": "Instructions reference evaluation factors",
        "Section C  Section B": "SOW references CLINs",
        "Section I  Sections A-H": "Clauses apply to contract sections",
        "Requirement  Deliverable": "Requirements generate deliverables",
        "Requirement  Evaluation Factor": "Requirements map to evaluation",
    }
    
    def enhance_extraction_prompt(self, base_prompt: str, section_context: RFPSection) -> str:
        \"\"\"
        Inject ontology into LightRAG extraction prompt
        Teaches LLM government contracting concepts
        \"\"\"
        
        enhanced = f\"\"\"
        {base_prompt}
        
        GOVERNMENT CONTRACTING ONTOLOGY:
        
        Extract entities of these types ONLY:
        {chr(10).join(f'- {et}: {self.get_type_description(et)}' for et in self.GOVERNMENT_ENTITY_TYPES)}
        
        Valid relationship patterns:
        {chr(10).join(f'- {pattern}: {desc}' for pattern, desc in self.RELATIONSHIP_PATTERNS.items())}
        
        Current section context: {section_context.section_id} - {section_context.title}
        
        CRITICAL:
        - Extract ONLY from provided text (NO external knowledge)
        - Use government contracting entity types (NOT generic "person", "location")
        - Create relationships that match valid patterns above
        - Validate section references (A-M are valid, "J-L" is not)
        \"\"\"
        
        return enhanced
\\\

### 3. PydanticAI Validation Pipeline

**File**: \src/lightrag_govcon/govcon/pydantic_validation.py\

\\\python
class ExtractionValidator:
    \"\"\"
    PydanticAI-powered validation ensures quality and prevents contamination
    Every extracted entity/relationship validated against Pydantic models
    \"\"\"
    
    async def validate_extraction(
        self,
        raw_extraction: Dict[str, Any],
        source_text: str,
        section_context: RFPSection
    ) -> RequirementsExtractionOutput:
        \"\"\"
        Validate extraction against Pydantic models
        Catch contamination, invalid entities, structural issues
        \"\"\"
        
        # Step 1: Use PydanticAI agent for structured extraction
        validated_result = await self.extraction_agent.run(
            f\"Extract requirements from: {source_text}\",
            ctx=RFPContext(section_id=section_context.section_id),
            result_type=RequirementsExtractionOutput  #  Type safety here
        )
        
        # Step 2: Document isolation check
        contamination_check = await self.check_document_isolation(
            validated_result.requirements,
            source_text
        )
        
        if not contamination_check.is_valid:
            logger.warning(f\"Contamination detected: {contamination_check.errors}\")
            # Filter out contaminated entities
            validated_result.requirements = [
                req for req in validated_result.requirements
                if req.requirement_id not in contamination_check.invalid_ids
            ]
        
        # Step 3: Ontology compliance check
        ontology_check = self.validate_ontology_compliance(validated_result)
        
        if not ontology_check.is_valid:
            logger.error(f\"Ontology violations: {ontology_check.errors}\")
            raise ValidationError(ontology_check.errors)
        
        return validated_result
    
    async def check_document_isolation(
        self,
        requirements: List[RFPRequirement],
        source_text: str
    ) -> ValidationResult:
        \"\"\"
        Ensure all entities exist in source document
        Prevents LLM from injecting external knowledge
        \"\"\"
        
        invalid_ids = []
        errors = []
        
        for req in requirements:
            # Fuzzy search for requirement text in source
            if not self.fuzzy_search(req.requirement_text[:50], source_text):
                invalid_ids.append(req.requirement_id)
                errors.append(f\"Entity '{req.requirement_id}' not found in source\")
        
        return ValidationResult(
            is_valid=len(invalid_ids) == 0,
            errors=errors,
            invalid_ids=invalid_ids
        )
\\\

### 4. Modified LightRAG Operate

**File**: \src/lightrag_govcon/operate.py\

**Modifications**:
1. Line ~2024: Inject ontology entity types instead of DEFAULT_ENTITY_TYPES
2. Line ~2069: Use enhanced prompts with government contracting examples
3. Line ~2080: Add PydanticAI validation after LLM extraction
4. Post-processing: Validate against ontology before graph insertion

\\\python
# Modified extraction flow
async def extract_entities_relationships(
    chunks,
    global_config,
    validation_pipeline  #  NEW: PydanticAI validator
):
    # Inject ontology entity types
    entity_types = get_government_entity_types()  #  Instead of DEFAULT_ENTITY_TYPES
    
    # Use enhanced prompts
    prompts = get_ontology_enhanced_prompts(entity_types)
    
    # Extract with LLM
    raw_extraction = await llm_call(prompts, chunks)
    
    # Validate with PydanticAI
    validated_extraction = await validation_pipeline.validate_extraction(
        raw_extraction,
        source_text=chunks['content'],
        section_context=chunks['metadata']['section']
    )
    
    return validated_extraction
\\\

---

## Implementation Roadmap

###  Phase 1: Fork Setup (COMPLETE)
- [x] Copy LightRAG 1.4.9 to \src/lightrag_govcon/\
- [x] Create \govcon/\ extension directory
- [x] Set up fork identification

### Phase 2: Semantic Analyzer (Week 1)
- [ ] Implement \SemanticRFPAnalyzer\
- [ ] Create PydanticAI agent for structure understanding
- [ ] Test against Navy MBOS RFP
- [ ] Validate NO fictitious entities created

### Phase 3: Ontology Integration (Week 1-2)
- [ ] Create \OntologyInjector\
- [ ] Define government entity types
- [ ] Map relationship patterns
- [ ] Enhance extraction prompts
- [ ] Test entity type compliance

### Phase 4: PydanticAI Validation (Week 2)
- [ ] Implement \ExtractionValidator\
- [ ] Document isolation checks
- [ ] Ontology compliance validation
- [ ] Confidence scoring
- [ ] Test zero contamination goal

### Phase 5: Quality Assurance (Week 3)
- [ ] Build QA framework
- [ ] Section hierarchy validation
- [ ] Relationship pattern validation
- [ ] Completeness checks
- [ ] Performance benchmarking

### Phase 6: Integration Testing (Week 3)
- [ ] Process Navy MBOS RFP
- [ ] Compare to Plan A/B results
- [ ] Validate metrics (entities, relationships, contamination)
- [ ] Benchmark processing time
- [ ] Quality assessment

### Phase 7: Production Deployment (Week 4)
- [ ] Package as \lightrag-govcon\
- [ ] Documentation
- [ ] API examples
- [ ] Performance tuning
- [ ] Production release

---

## Success Metrics

| Metric | Plan A | Plan B | **Target (Fork)** | Status |
|--------|--------|--------|-------------------|--------|
| Entities | 772 (noisy) | 569 | 600-700 (validated) | TBD |
| Relationships | 697 | 426 | 500-600 (domain-valid) | TBD |
| Contamination | 11 | 6 | **0** (must achieve) | TBD |
| Fictitious Entities | Yes | No | **No** (must achieve) | TBD |
| Section Coverage | 90% | 60% | **100%** (A-M all) | TBD |
| Isolated Entities | ~25% | 19% | <10% | TBD |
| Processing Time | ~76 min | ~76 min | <60 min | TBD |

---

## Quality Gates

**Cannot proceed to next phase until**:
1.  Zero fictitious entities (e.g., "Section J-L")
2.  Zero contamination (e.g., "Noah Carter")
3.  100% entity type compliance (all entities match ontology)
4.  All relationships match valid patterns
5.  Document isolation verified

---

## Next Steps

1. **Implement SemanticRFPAnalyzer** - LLM-native structure understanding
2. **Test structure analysis** - Validate NO regex artifacts
3. **Inject ontology** - Enhance extraction prompts
4. **Add PydanticAI validation** - Guarantee quality
5. **Test against Navy MBOS RFP** - Full integration test

Ready to begin Phase 2 implementation!
