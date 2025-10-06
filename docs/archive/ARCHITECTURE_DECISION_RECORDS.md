# Architecture Decision Records

**Project**: GovCon-Capture-Vibe  
**Status**: Living Document  
**Last Updated**: October 5, 2025

This document consolidates architectural decisions made during the development of the government contracting RAG system, specifically the analysis of Plan A vs Plan B approaches and the specification for the production fork.

---

## ADR-001: LLM-Native Semantic Approach Over Regex Preprocessing

**Date**: October 4, 2025  
**Status**: Accepted  
**Decision Makers**: Development Team

### Context

During initial development, we explored two approaches:
- **Plan A**: Regex-based section identification with `ShipleyRFPChunker`
- **Plan B**: Generic LightRAG with surface ontology integration

Plan A showed superior metrics (772 entities, 697 relationships) vs Plan B (569 entities, 426 relationships), but both suffered from contamination issues.

### Decision

Adopt an **LLM-Native Semantic Understanding** approach that eliminates regex preprocessing in favor of letting LLMs understand document structure semantically, enhanced with ontology injection and PydanticAI validation.

### Rationale

**Critical Insight**: Regex was creating problems, not solving them:

❌ **Regex Issues**:
- Fictitious entities: "RFP Section J-L" (doesn't exist in Uniform Contract Format)
- False boundaries: Cut content mid-paragraph when patterns matched
- Over-extraction: 772 entities included regex artifacts
- Pattern fragility: Failed on real-world RFP variations

✅ **LLM-Native Benefits**:
- Semantic understanding: Distinguishes "Section L: Instructions" from "in section A of the building"
- Context awareness: Knows "Section J-L" is fictitious
- Handles variations: Robust to different RFP formatting styles
- Leverages pre-training: Government contracting knowledge already in model

### Consequences

**Positive**:
- No more fictitious entities from regex pattern matching
- Better handling of real-world RFP variations
- Cleaner, more maintainable codebase
- Leverages full LLM capabilities

**Negative**:
- Requires careful prompt engineering
- Need strong validation to prevent contamination
- May need more context/tokens per extraction

**Mitigation**:
- Implement PydanticAI validation pipeline
- Add document isolation checks
- Inject government contracting ontology into prompts

---

## ADR-002: Plan A vs Plan B Comparative Analysis

**Date**: October 4, 2025  
**Status**: Historical Reference  
**Decision Makers**: Development Team

### Context

Two architectural approaches were tested against the Navy MBOS RFP:

**Plan A**: Regex-based preprocessing with section-aware chunking
**Plan B**: Generic LightRAG with surface ontology integration

### Results

| Metric | Plan A | Plan B | Difference |
|--------|--------|--------|------------|
| **Entities Extracted** | 772 | 569 | Plan A +35.7% |
| **Relationships Found** | 697 | 426 | Plan A +63.6% |
| **Relationship Density** | 0.90 per entity | 0.75 per entity | Plan A +20% |
| **Contamination** | 11 foreign entities | 6 foreign entities | Both FAILED |
| **Section Coverage** | 90% (A-M) | 60% (partial) | Plan A |
| **Isolated Entities** | ~25% | 19% | Plan B (slight edge) |

### Analysis

**Plan A Strengths**:
1. **Section-Aware Chunking**: Sophisticated regex patterns identified all RFP sections (A-M) with subsections, preserving "Section L.3.1" as context
2. **Requirement-Based Splitting**: Split requirement-heavy sections into manageable chunks (3 requirements max), preventing LLM timeouts
3. **Relationship Mapping**: Pre-populated valid RFP relationships (L→M, C→B), creating 63.6% more relationships than Plan B

**Plan B Strengths**:
1. **Lower Contamination**: 6 entities vs 11 (though both failed to achieve zero)
2. **Cleaner Entities**: Fewer regex artifacts in extracted entities
3. **Better Isolation**: 19% isolated entities vs 25%

**Shared Failure: Contamination**

Both plans suffered contamination from LLM introducing external knowledge:
- **Plan A**: Noah Carter, Carbon-Fiber Spikes, Gold Futures, Crude Oil, Market Selloff, Federal Reserve Policy, Tokyo, 100m Sprint, World Athletics (11 total)
- **Plan B**: Noah Carter, Carbon-Fiber Spikes, Tokyo, 100m Sprint, World Athletics Championship, World Athletics Federation (6 total)

**Root Cause**: No structured validation of LLM outputs, no type safety, no automated quality control.

### Conclusion

**Your Instinct Was Correct**: Plan A's superior performance validated that preprocessing + structure preservation is essential. However, regex preprocessing created more problems than it solved. The correct path forward is to combine the best of both approaches with PydanticAI validation.

---

## ADR-003: Triple Hybrid Architecture

**Date**: October 4, 2025  
**Status**: Accepted  
**Decision Makers**: Development Team

### Context

Neither Plan A (regex preprocessing) nor Plan B (generic LightRAG) achieved production quality. Plan A had better metrics but created fictitious entities. Plan B was cleaner but missed structure.

### Decision

Implement a **Triple Hybrid Architecture** combining:
1. **LLM-Native Semantic Understanding** (replaces Plan A regex)
2. **Ontology-Enhanced LightRAG** (deep integration, not surface)
3. **PydanticAI Validation** (ensures quality + zero contamination)

### Architecture

```
RFP PDF
↓
[LLM: Semantic Structure Analysis]
  - Understands "Section L: Instructions" semantically
  - Knows "Section J-L" is fictitious
  - Distinguishes RFP sections from random text
↓
[Ontology-Enhanced LightRAG]
  - Custom entity types: SECTION, REQUIREMENT, CLIN, FAR_CLAUSE
  - Government contracting relationship patterns
  - Domain-specific extraction prompts
↓
[PydanticAI Validation Pipeline]
  - RFPRequirement models enforce structure
  - Validators catch invalid entities
  - Document isolation verification
↓
[Clean Knowledge Graph]
  - Zero contamination
  - Type-safe entities
  - Domain-valid relationships
  - Traceable to source
```

### Components

**1. Semantic RFP Analyzer** (`src/lightrag/govcon/semantic_analyzer.py`)
```python
class SemanticRFPAnalyzer:
    """
    LLM-native document structure understanding
    NO regex patterns - pure semantic analysis
    """
    async def analyze_structure(self, rfp_text: str) -> RFPStructure:
        # LLM understands:
        # - "Section L: Instructions to Offerors" = RFP section
        # - "in section A of the building" = not an RFP section
        # - "Section J-1" = valid attachment
        # - "Section J-L" = fictitious (doesn't exist)
```

**2. Ontology Injector** (`src/lightrag/govcon/ontology_integration.py`)
```python
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
    "Section L ↔ Section M": "Instructions reference evaluation factors",
    "Section C ↔ Section B": "SOW references CLINs",
    "Requirement → Deliverable": "Requirements generate deliverables",
    "Requirement → Evaluation Factor": "Requirements map to evaluation",
}
```

**3. PydanticAI Validation** (`src/lightrag/govcon/pydantic_validation.py`)
```python
class ExtractionValidator:
    async def validate_extraction(self, raw_extraction, source_text):
        # Step 1: PydanticAI agent for structured extraction
        validated_result = await self.extraction_agent.run(
            context=source_text,
            result_type=RequirementsExtractionOutput  # Type safety
        )
        
        # Step 2: Document isolation check
        contamination_check = await self.check_document_isolation(
            validated_result.requirements,
            source_text
        )
        
        # Step 3: Filter contamination
        if not contamination_check.is_valid:
            validated_result.requirements = [
                req for req in validated_result.requirements
                if req.requirement_id not in contamination_check.invalid_ids
            ]
```

### Expected Outcomes

| Metric | Plan A | Plan B | **Target (Triple Hybrid)** |
|--------|--------|--------|---------------------------|
| Entities | 772 (noisy) | 569 (clean) | **600-700** (validated) |
| Relationships | 697 | 426 | **500-600** (domain-valid) |
| Rel/Entity Ratio | 0.90 | 0.75 | **1.2+** (denser graph) |
| **Contamination** | 11 | 6 | **0** (must achieve) |
| **Fictitious Entities** | Yes | No | **No** (must achieve) |
| Section Coverage | 90% | 60% | **100%** (A-M all captured) |
| Isolated Entities | ~25% | 19% | **<10%** |
| Processing Time | ~76 min | ~76 min | **<60 min** |

### Rationale

**Why Triple Hybrid Wins**:

❌ **Plan A alone**: Great preprocessing, but no validation → contamination  
❌ **Plan B alone**: LightRAG power, but loses structure → fewer entities  
❌ **PydanticAI alone**: Perfect structure, but needs good chunking → timeouts

✅ **Triple Hybrid**:
- LLM-native semantic understanding provides optimal context
- LightRAG discovers relationships Plan A might miss
- PydanticAI ensures every output is validated, structured, traceable
- **Result**: Best of all three worlds

### Consequences

**Positive**:
- Zero contamination (PydanticAI validation)
- No fictitious entities (semantic understanding)
- Better relationship discovery (LightRAG + ontology)
- Type-safe outputs (Pydantic models)
- Production-ready quality

**Negative**:
- More complex architecture
- Requires forking LightRAG repository
- Higher maintenance burden
- Longer initial implementation

**Mitigation**:
- Fork LightRAG as `src/lightrag/` for full control
- Comprehensive testing against Navy MBOS RFP
- Quality gates at each phase (zero contamination required)
- Clear separation: core LightRAG vs govcon extensions

---

## ADR-004: LightRAG Fork Strategy

**Date**: October 4, 2025  
**Status**: Accepted  
**Decision Makers**: Development Team

### Context

To implement the Triple Hybrid architecture, we need deep modifications to LightRAG that go beyond configuration:
- Custom entity types (not generic "person", "location")
- Ontology-injected extraction prompts
- PydanticAI validation pipeline
- Government contracting relationship patterns

### Decision

Fork LightRAG as `src/lightrag/` with government contracting extensions in `src/lightrag/govcon/`.

### Structure

```
src/lightrag/
├── __init__.py                 # Fork identification + version
├── lightrag.py                 # Modified main class
├── operate.py                  # Enhanced extraction with ontology
├── prompt.py                   # Government contracting prompts
├── govcon/                     # Government contracting extensions
│   ├── __init__.py
│   ├── semantic_analyzer.py   # LLM-native document understanding
│   ├── ontology_integration.py # Ontology injection into prompts
│   ├── pydantic_validation.py  # PydanticAI validation pipeline
│   └── quality_assurance.py    # Document isolation checks
├── api/                        # Original LightRAG API (preserved)
├── kg/                         # Knowledge graph (preserved)
├── llm/                        # LLM integrations (preserved)
└── tools/                      # Utilities (preserved)
```

### Key Modifications

**1. operate.py** (Line ~2024, ~2069, ~2080):
- Inject ontology entity types instead of `DEFAULT_ENTITY_TYPES`
- Use enhanced prompts with government contracting examples
- Add PydanticAI validation after LLM extraction
- Validate against ontology before graph insertion

**2. prompt.py**:
- Add government contracting entity type definitions
- Include RFP-specific examples
- Document relationship patterns

**3. govcon/** (New Extensions):
- Semantic analyzer (replaces regex chunking)
- Ontology integration (entity types + relationship patterns)
- PydanticAI validation (quality control)
- Quality assurance (document isolation checks)

### Rationale

**Why Fork vs Configuration**:
- Ontology integration requires prompt modifications
- PydanticAI validation needs pipeline integration
- Custom entity types need core changes
- Government contracting logic is domain-specific

**Why `src/lightrag/` vs pip package**:
- Full control over modifications
- Easy debugging and testing
- No version conflicts
- Can cherry-pick upstream updates

**Why `govcon/` subdirectory**:
- Clear separation: core LightRAG vs government contracting
- Easier to maintain upstream compatibility
- Government contracting logic isolated and testable

### Consequences

**Positive**:
- Full control over LightRAG behavior
- Can implement deep ontology integration
- Easy to test and debug modifications
- No dependency on upstream release cycle

**Negative**:
- Must manually merge upstream updates
- Larger repository size
- Additional maintenance burden

**Mitigation**:
- Document all modifications clearly
- Keep `govcon/` separate from core LightRAG
- Track upstream LightRAG releases
- Test thoroughly before merging updates

---

## ADR-005: PydanticAI for Structured Extraction

**Date**: October 4, 2025  
**Status**: Accepted  
**Decision Makers**: Development Team

### Context

Both Plan A and Plan B suffered from contamination (external entities like "Noah Carter", "Tokyo") because LLM outputs were unvalidated. We need guaranteed structure + quality control.

### Decision

Use **PydanticAI** for all entity extraction with type-safe `RFPRequirement` models and automated validation.

### Implementation

```python
from pydantic_ai import Agent
from src.models.rfp_models import RFPRequirement, RequirementsExtractionOutput

requirements_agent = Agent(
    'ollama:qwen2.5-coder:7b',
    result_type=RequirementsExtractionOutput,  # GUARANTEED STRUCTURE
    system_prompt='''
    Extract ONLY requirements from RFP content.
    CRITICAL: Extract entities that appear in the provided text ONLY.
    DO NOT use external knowledge or training data.
    '''
)

# Agent returns VALIDATED structure or fails - no garbage entities
result = await requirements_agent.run(prompt, ctx=rfp_context)
# result.data.requirements: List[RFPRequirement] - type-safe, validated
```

### Benefits

1. **Guaranteed Structure**: Can't return 'Noah Carter' when entity_type is limited to RFPSectionType enum
2. **Automated Validation**: Pydantic validators catch invalid requirement_ids, section_ids immediately
3. **Type Safety**: No runtime surprises - 'compliance_level' MUST be ComplianceLevel enum
4. **Quality Metrics**: Built-in confidence scores, validation results
5. **Zero Contamination**: Document isolation checks filter external entities

### Example Prevention

```python
class RFPRequirement(BaseModel):
    section_id: str

    @validator('section_id')
    def validate_section_id(cls, v):
        if not re.match(r'^[A-MJ](-\w+)?$', v):
            raise ValueError('Invalid RFP section')  # ← 'Tokyo' gets rejected
        return v
```

### Quality Gates

**Cannot proceed without**:
1. ✅ Zero contamination (no external entities)
2. ✅ Type safety (all fields validated)
3. ✅ Document isolation (entities exist in source)
4. ✅ Ontology compliance (entity types match GOVERNMENT_ENTITY_TYPES)
5. ✅ Confidence scoring (quality metrics tracked)

### Consequences

**Positive**:
- Zero contamination achieved
- Production-ready quality control
- Type-safe outputs (no runtime errors)
- Automated validation (no manual checks)
- Clear error messages (debugging easier)

**Negative**:
- Additional dependency (pydantic-ai)
- Slightly slower extraction (validation overhead)
- More complex error handling

**Mitigation**:
- PydanticAI is lightweight and well-maintained
- Validation overhead negligible vs contamination cost
- Comprehensive error logging and recovery

---

## Implementation Roadmap

### ✅ Phase 1: Fork Setup (COMPLETE)
- [x] Copy LightRAG 1.4.9 to `src/lightrag/`
- [x] Create `govcon/` extension directory
- [x] Set up fork identification

### ⏳ Phase 2: Semantic Analyzer (Week 1)
- [ ] Implement `SemanticRFPAnalyzer`
- [ ] Create PydanticAI agent for structure understanding
- [ ] Test against Navy MBOS RFP
- [ ] Validate NO fictitious entities created

### ⏳ Phase 3: Ontology Integration (Week 1-2)
- [ ] Create `OntologyInjector`
- [ ] Define government entity types
- [ ] Map relationship patterns
- [ ] Enhance extraction prompts
- [ ] Test entity type compliance

### ⏳ Phase 4: PydanticAI Validation (Week 2)
- [ ] Implement `ExtractionValidator`
- [ ] Document isolation checks
- [ ] Ontology compliance validation
- [ ] Confidence scoring
- [ ] Test zero contamination goal

### ⏳ Phase 5: Quality Assurance (Week 3)
- [ ] Build QA framework
- [ ] Section hierarchy validation
- [ ] Relationship pattern validation
- [ ] Completeness checks
- [ ] Performance benchmarking

### ⏳ Phase 6: Integration Testing (Week 3)
- [ ] Process Navy MBOS RFP
- [ ] Compare to Plan A/B results
- [ ] Validate metrics (entities, relationships, contamination)
- [ ] Benchmark processing time
- [ ] Quality assessment

### ⏳ Phase 7: Production Deployment (Week 4)
- [ ] Package as production system
- [ ] Documentation
- [ ] API examples
- [ ] Performance tuning
- [ ] Production release

---

## Success Criteria

### Quality Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Entities** | 600-700 (validated) | TBD |
| **Relationships** | 500-600 (domain-valid) | TBD |
| **Rel/Entity Ratio** | 1.2+ (denser graph) | TBD |
| **Contamination** | **0** (MUST ACHIEVE) | TBD |
| **Fictitious Entities** | **0** (MUST ACHIEVE) | TBD |
| **Section Coverage** | 100% (A-M all) | TBD |
| **Isolated Entities** | <10% | TBD |
| **Processing Time** | <60 min | TBD |

### Quality Gates

**Phase 2 Gate**:
- ✅ Zero fictitious entities (e.g., "Section J-L")
- ✅ Semantic understanding validated
- ✅ All sections identified correctly

**Phase 4 Gate**:
- ✅ Zero contamination (e.g., "Noah Carter")
- ✅ 100% entity type compliance
- ✅ Document isolation verified

**Phase 6 Gate**:
- ✅ All metrics meet or exceed targets
- ✅ Navy MBOS RFP processed successfully
- ✅ No quality regressions vs Plan A/B

**Production Gate**:
- ✅ All quality gates passed
- ✅ Performance benchmarks met
- ✅ Documentation complete
- ✅ Production deployment validated

---

## Key Lessons Learned

### 1. Regex is Not the Answer
Regex preprocessing created more problems than it solved:
- Fictitious entities from pattern matching
- Brittle patterns that failed on variations
- Over-extraction that appeared better but was actually noise

**Lesson**: Let LLMs understand semantically, not through pattern matching.

### 2. Preprocessing Doesn't Replace RAG
Plan A's preprocessing ENHANCED LightRAG, didn't bypass it:
- Better chunk boundaries → better extraction
- Preserved context → better relationships
- Reduced cognitive load → fewer timeouts

**Lesson**: Preprocessing + RAG + Validation = Production Quality

### 3. Validation is Non-Negotiable
Both Plan A and Plan B had contamination because:
- No type-safe structured outputs
- No document isolation verification
- No automated quality control

**Lesson**: PydanticAI validation is ESSENTIAL for production.

### 4. Domain Knowledge Matters
Generic LightRAG cannot understand government contracting:
- Never seen RFPs in training
- Doesn't know CLINs, FAR clauses, Section L-M relationships
- Extracts generic entities, not domain concepts

**Lesson**: Ontology injection is CRITICAL for domain-specific RAG.

---

## References

- **Navy MBOS RFP**: Primary test document (1,051 pages)
- **LightRAG**: https://github.com/HKUDS/LightRAG (v1.4.9)
- **PydanticAI**: https://ai.pydantic.dev/
- **Shipley Methodology**: `docs/Shipley Capture Guide.pdf`, `docs/Shipley Proposal Guide.pdf`
- **Plan A Analysis**: Original findings that led to ADR-001
- **Plan B Results**: Comparative metrics that led to ADR-003

---

**Document Status**: Living document - will be updated as implementation progresses and new architectural decisions are made.

**Version History**:
- v1.0.0 (October 5, 2025): Initial consolidation of Plan A/B analysis and production fork specification into ADR format
