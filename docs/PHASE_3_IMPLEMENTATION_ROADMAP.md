# Phase 3 Implementation Roadmap: LightRAG Core Integration

**Date**: October 4, 2025
**Phase**: Integrate Phase 2 Components into LightRAG Extraction Pipeline
**Prerequisites**:  Phase 2 Complete (Semantic Analyzer + Ontology + Validation)

---

## Objective

Integrate Phase 2 components (semantic analyzer, ontology injector, PydanticAI validation) into LightRAG's core extraction engine to create a production-ready government contracting RFP analysis system.

**Success Criteria**:
-  All extractions use ontology-enhanced prompts
-  All extractions validated via PydanticAI pipeline
-  Navy MBOS RFP processing achieves targets: 850+ entities, 1000+ relationships, 0 contamination
-  Zero fictitious sections created
-  Quality gates pass

---

## Implementation Tasks

### Task 1: Create GovernmentRFPLightRAG Wrapper Class

**File**: src/lightrag_govcon/govcon_lightrag.py (NEW)
**Estimated Lines**: ~300
**Priority**: HIGH

**Purpose**: 
- Wrapper around LightRAG.insert() that integrates Phase 2 components
- Pre-processing: Semantic structure analysis
- Mid-processing: Ontology-enhanced extraction
- Post-processing: PydanticAI validation + QA

**Implementation**:

`python
"""
GovernmentRFPLightRAG - Production-Ready Government Contracting RAG

Extends LightRAG with:
- LLM-native semantic structure analysis (NO regex)
- Government contracting ontology injection (14 entity types, 13 relationships)
- PydanticAI validation pipeline (zero contamination guarantee)
- Production quality gates (850+ entities, 1000+ relationships)
"""

from lightrag import LightRAG
from .govcon.semantic_analyzer import SemanticRFPAnalyzer
from .govcon.ontology_integration import OntologyInjector
from .govcon.pydantic_validation import ExtractionValidator
from .govcon.quality_assurance import QualityAssuranceFramework

class GovernmentRFPLightRAG(LightRAG):
    """LightRAG extension for government contracting RFPs"""
    
    def __init__(self, *args, **kwargs):
        # Initialize LightRAG with government contracting ontology
        if 'addon_params' not in kwargs:
            kwargs['addon_params'] = {}
        
        # Inject government entity types into LightRAG config
        ontology_injector = OntologyInjector()
        entity_types = [et[0] for et in ontology_injector._get_government_entity_types()]
        kwargs['addon_params']['entity_types'] = entity_types
        
        super().__init__(*args, **kwargs)
        
        # Initialize Phase 2 components
        self.semantic_analyzer = SemanticRFPAnalyzer()
        self.ontology_injector = ontology_injector
        self.validator = ExtractionValidator()
        self.qa_framework = QualityAssuranceFramework()
        
        # Processing metrics
        self.processing_start_time = None
        self.chunks_processed = 0
        self.llm_calls = 0
    
    async def insert(self, text: str, **kwargs):
        """
        Insert RFP text with Phase 2 enhancements
        
        Pipeline:
        1. Semantic structure analysis (identify sections)
        2. Ontology-enhanced extraction (government entity types)
        3. PydanticAI validation (zero contamination)
        4. Quality assurance validation (production quality gates)
        """
        
        from datetime import datetime
        self.processing_start_time = datetime.now()
        
        # Step 1: Semantic structure analysis
        logger.info("Step 1: Analyzing RFP structure (LLM-native, NO regex)...")
        structure = await self.semantic_analyzer.analyze_structure(text)
        
        if structure.has_fictitious_sections:
            raise ValueError(
                f"Fictitious sections detected: {structure.fictitious_sections}. "
                f"Cannot proceed with extraction."
            )
        
        logger.info(
            f"Structure analysis complete: {len(structure.sections)} sections found, "
            f"confidence: {structure.structure_confidence:.2f}"
        )
        
        # Step 2: Process with ontology-enhanced extraction
        logger.info("Step 2: Processing with ontology-enhanced extraction...")
        
        # Enhance extraction prompts with ontology
        section_context = {
            'sections': [s.model_dump() for s in structure.sections],
            'structure_confidence': structure.structure_confidence
        }
        
        # Call parent insert with enhanced configuration
        result = await super().insert(text, **kwargs)
        
        self.chunks_processed += 1
        
        # Step 3: Post-processing validation (implemented in next phase)
        # TODO: Validate extracted entities against ontology
        # TODO: Check for contamination
        # TODO: Generate QA report
        
        return result
    
    async def query(self, query: str, **kwargs):
        """Query with ontology-aware retrieval"""
        
        # Enhance query with ontology context
        enhanced_query = self.ontology_injector.enhance_query(query)
        
        # Call parent query
        return await super().query(enhanced_query, **kwargs)
`

**Testing**: 
- Unit test: Verify semantic analysis runs before extraction
- Unit test: Verify ontology types injected into LightRAG config
- Integration test: Process small RFP sample, validate structure analysis

---

### Task 2: Modify LightRAG Extraction Pipeline

**File**: src/lightrag_govcon/operate.py (MODIFY)
**Lines to Modify**: ~50-100 lines
**Priority**: HIGH

**Changes Required**:

**2a. Inject Ontology Entity Types** (Line ~2024):

`python
# BEFORE (original LightRAG):
entity_types = global_config["addon_params"].get("entity_types", DEFAULT_ENTITY_TYPES)

# AFTER (with ontology injection):
from .govcon.ontology_integration import OntologyInjector

ontology_injector = OntologyInjector()
entity_types = global_config["addon_params"].get(
    "entity_types",
    [et[0] for et in ontology_injector._get_government_entity_types()]
)
`

**2b. Enhance Extraction Prompt** (Line ~2069):

`python
# BEFORE (original LightRAG):
extraction_prompt = PROMPTS["entity_extraction_system_prompt"].format(
    entity_types=entity_types
)

# AFTER (with ontology enhancement):
# Load section context if available
section_context = kwargs.get('section_context', None)

# Enhance prompt with ontology
extraction_prompt = ontology_injector.enhance_extraction_prompt(
    PROMPTS["entity_extraction_system_prompt"],
    section_context
)
`

**2c. Add PydanticAI Validation** (Line ~2080, after LLM call):

`python
# BEFORE (original LightRAG):
entities_and_relations = await llm_model.acall(extraction_prompt, text)

# AFTER (with validation):
from .govcon.pydantic_validation import ExtractionValidator

validator = ExtractionValidator()

# Get raw extraction
raw_extraction = await llm_model.acall(extraction_prompt, text)

# Validate extraction
validated_extraction = await validator.validate_extraction(
    raw_extraction,
    text,
    section_context
)

# Use validated extraction
entities_and_relations = validated_extraction
`

**Testing**:
- Unit test: Verify entity types injected correctly
- Unit test: Verify extraction prompt enhanced with ontology
- Unit test: Verify validation runs after LLM call
- Integration test: Process sample text, check validation runs

---

### Task 3: Update Extraction Prompts

**File**: src/lightrag_govcon/prompt.py (MODIFY)
**Lines to Modify**: ~20-30 lines
**Priority**: MEDIUM

**Changes Required**:

**3a. Replace Generic Examples with Government Contracting**:

`python
# BEFORE (original LightRAG):
PROMPTS["entity_extraction_examples"] = [
    ("Alice manages the TechCorp project", "PERSON|ORGANIZATION|PROJECT"),
    # ... generic examples
]

# AFTER (with government contracting examples):
from .govcon.ontology_integration import OntologyInjector

ontology_injector = OntologyInjector()
PROMPTS["entity_extraction_examples"] = ontology_injector._get_extraction_examples()
`

**3b. Add Ontology Instructions**:

`python
# BEFORE (original LightRAG):
PROMPTS["entity_extraction_system_prompt"] = """
You are an expert entity extractor...
{entity_types}
"""

# AFTER (with ontology instructions):
PROMPTS["entity_extraction_system_prompt"] = """
You are an expert entity extractor specialized in government contracting RFPs.

CRITICAL INSTRUCTIONS:
1. Extract ONLY from provided RFP text
2. DO NOT use external knowledge or introduce entities not in the text
3. USE ONLY the following government contracting entity types:
{entity_types}

4. CREATE relationships matching these valid patterns:
{relationship_patterns}

5. VALIDATE section references (A-M valid, J-1/J-2 valid, J-L INVALID)

{extraction_examples}
"""
`

**Testing**:
- Unit test: Verify examples replaced with government contracting
- Unit test: Verify ontology instructions added to prompt
- Integration test: Check prompt formatting with ontology injection

---

### Task 4: Quality Assurance Integration

**File**: src/lightrag_govcon/govcon_lightrag.py (UPDATE)
**Lines to Add**: ~50
**Priority**: MEDIUM

**Purpose**: Generate quality gate reports after RFP processing

**Implementation**:

`python
class GovernmentRFPLightRAG(LightRAG):
    # ... (existing code)
    
    async def insert_and_validate(self, text: str, **kwargs):
        """
        Insert RFP text and generate quality gate report
        """
        
        from datetime import datetime
        start_time = datetime.now()
        
        # Process RFP
        result = await self.insert(text, **kwargs)
        
        end_time = datetime.now()
        
        # Generate quality gate report
        # TODO: Extract entities/relationships from storage
        entities = self._get_extracted_entities()
        relationships = self._get_extracted_relationships()
        sections = self._get_identified_sections()
        
        # Run QA validations
        section_val = self.qa_framework.validate_section_hierarchy(sections)
        rel_val = self.qa_framework.validate_relationship_patterns(relationships)
        completeness = self.qa_framework.assess_completeness(
            entities, relationships, sections
        )
        performance = self.qa_framework.benchmark_performance(
            start_time, end_time,
            self.chunks_processed,
            self.llm_calls,
            len(entities)
        )
        
        # Generate report
        qa_report = self.qa_framework.generate_quality_gate_report(
            section_val, rel_val, completeness, performance
        )
        
        # Print report
        self.qa_framework.print_report_summary(qa_report)
        
        # Save report
        from pathlib import Path
        report_path = Path(self.working_dir) / "qa_reports" / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.qa_framework.save_report(qa_report, report_path)
        
        # Check if quality gates passed
        if not qa_report.overall_pass:
            logger.error(f"Quality gates FAILED: {qa_report.critical_failures}")
            raise ValueError(
                f"Processing failed quality gates. Critical failures: {qa_report.critical_failures}"
            )
        
        return result, qa_report
`

**Testing**:
- Integration test: Process RFP, verify QA report generated
- Integration test: Verify quality gates block on critical failures
- Integration test: Verify report saved to disk

---

### Task 5: Navy MBOS RFP Benchmark Testing

**File**: 	est_navy_mbos_benchmark.py (NEW)
**Estimated Lines**: ~200
**Priority**: HIGH

**Purpose**: Validate production fork against Navy MBOS RFP, compare to Plan A/B

**Implementation**:

`python
"""
Navy MBOS RFP Benchmark Test

Processes Navy MBOS RFP with production fork and validates:
- Entities: 850+ (vs Plan A's 772)
- Relationships: 1000+ (vs Plan A's 697)
- Contamination: 0 (vs Plan A's 11, Plan B's 6)
- Fictitious sections: 0
- Section coverage: 100%
"""

import asyncio
from pathlib import Path
from datetime import datetime

from src.lightrag_govcon.govcon_lightrag import GovernmentRFPLightRAG

async def test_navy_mbos_benchmark():
    """Process Navy MBOS RFP and generate benchmark report"""
    
    print("="*80)
    print("NAVY MBOS RFP BENCHMARK TEST")
    print("="*80)
    
    # Load Navy MBOS RFP
    rfp_path = Path("inputs/uploaded/Navy_MBOS_RFP.pdf")
    # TODO: Extract text from PDF
    rfp_text = extract_text_from_pdf(rfp_path)
    
    # Initialize production fork
    rag = GovernmentRFPLightRAG(
        working_dir="./rag_storage_phase3",
        llm_model="ollama/qwen2.5-coder:7b",
        embedding_model="ollama/bge-m3:latest"
    )
    
    # Process RFP with quality gates
    print("\\nProcessing Navy MBOS RFP with production fork...")
    result, qa_report = await rag.insert_and_validate(rfp_text)
    
    print("\\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)
    
    # Compare to targets
    print(f"\\nEntities: {qa_report.completeness.entity_count} (target: 850+)")
    print(f"Relationships: {qa_report.completeness.relationship_count} (target: 1000+)")
    print(f"Contamination: {len(qa_report.validation.contaminated_entities)} (target: 0)")
    print(f"Fictitious Sections: {len(qa_report.section_validation.fictitious_sections)} (target: 0)")
    print(f"Section Coverage: {qa_report.section_validation.section_coverage_percent:.1f}% (target: 100%)")
    
    # Compare to Plan A/B
    print(f"\\n" + "="*80)
    print("COMPARISON TO PLAN A & PLAN B")
    print("="*80)
    print(f"{'Metric':<25} {'Plan A':<10} {'Plan B':<10} {'Phase 3':<10} {'Status'}")
    print(f"{'-'*70}")
    print(f\"{'Entities':<25} {772:<10} {569:<10} {qa_report.completeness.entity_count:<10} {'' if qa_report.completeness.entity_count >= 850 else ''}\")
    print(f\"{'Relationships':<25} {697:<10} {426:<10} {qa_report.completeness.relationship_count:<10} {'' if qa_report.completeness.relationship_count >= 1000 else ''}\")
    # ... (continue comparison)
    
    return qa_report

if __name__ == \"__main__\":
    asyncio.run(test_navy_mbos_benchmark())
`

**Testing**:
- Process Navy MBOS RFP
- Validate entities 850
- Validate relationships 1000
- Validate contamination = 0
- Validate fictitious sections = 0
- Generate comparison report vs Plan A/B

---

## Implementation Timeline

### Week 1: Core Integration

**Days 1-2**: Task 1 - Create GovernmentRFPLightRAG wrapper
- Implement wrapper class
- Unit tests for semantic analysis integration
- Unit tests for ontology injection

**Days 3-4**: Task 2 - Modify LightRAG extraction pipeline
- Modify operate.py (entity types, prompt enhancement, validation)
- Unit tests for modifications
- Integration tests

**Day 5**: Task 3 - Update extraction prompts
- Modify prompt.py (examples, instructions)
- Unit tests

### Week 2: Testing & Validation

**Days 6-7**: Task 4 - Quality assurance integration
- Implement QA report generation
- Integration tests

**Days 8-10**: Task 5 - Navy MBOS RFP benchmark
- Process Navy MBOS RFP
- Validate against production targets
- Generate comparison report

---

## Success Criteria

### Phase 3 Completion Checklist

- [ ] GovernmentRFPLightRAG wrapper class implemented
- [ ] Semantic structure analysis integrated (pre-processing)
- [ ] Ontology entity types injected into LightRAG config
- [ ] Extraction prompts enhanced with ontology
- [ ] PydanticAI validation integrated (post-processing)
- [ ] Extraction prompt examples replaced with government contracting
- [ ] QA report generation implemented
- [ ] Quality gates block on critical failures
- [ ] Navy MBOS RFP processed successfully
- [ ] Production targets achieved:
  - [ ] Entities 850 (vs Plan A's 772)
  - [ ] Relationships 1000 (vs Plan A's 697)
  - [ ] Contamination = 0 (vs Plan A's 11, Plan B's 6)
  - [ ] Fictitious sections = 0
  - [ ] Section coverage = 100%
- [ ] Comparison report generated (Phase 3 vs Plan A vs Plan B)
- [ ] Documentation updated

### Critical Quality Gates

**CANNOT PROCEED TO PHASE 4 WITHOUT**:

1.  Zero fictitious sections created
2.  Zero contamination detected
3.  All entity types match ontology (100% compliance)
4.  All relationships match valid patterns
5.  Entities 850 (exceeds Plan A)
6.  Relationships 1000 (exceeds Plan A)
7.  Quality gate report passes all critical checks

---

## Risk Mitigation

### Potential Risks

1. **Risk**: LightRAG API changes prevent clean integration
   - **Mitigation**: Wrapper class isolates modifications, minimizes LightRAG core changes

2. **Risk**: Validation overhead slows processing significantly
   - **Mitigation**: Profile validation steps, optimize fuzzy matching, cache ontology lookups

3. **Risk**: Navy MBOS RFP processing doesn't meet targets
   - **Mitigation**: Iterative tuning of extraction prompts, chunk size, ontology examples

4. **Risk**: Integration breaks existing LightRAG functionality
   - **Mitigation**: Comprehensive unit/integration tests, maintain backward compatibility in wrapper

---

## Next Phase Preview: Phase 4

**Objective**: Production deployment and continuous improvement

**Tasks**:
- Package as lightrag-govcon distribution
- Version tagging (v1.0.0)
- API documentation
- Usage tutorials
- Performance optimization
- Production monitoring

---

**Prepared by**: AI Agent (Beast Mode 3.1)
**Date**: October 4, 2025
**Version**: 1.0.0
**Status**:  Awaiting User Approval to Proceed
