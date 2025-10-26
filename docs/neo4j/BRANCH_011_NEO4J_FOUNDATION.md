# Branch 011: Neo4j Foundation & Pre-Migration Cleanup

**Charter**: Prepare codebase for Neo4j migration through cleanup, optimization, and foundation work  
**Created**: October 26, 2025  
**Parent Branch**: 010-query-prompts-integration  
**Status**: 🚧 Active Development

---

## 🎯 Branch Objectives

### Primary Goal
Lay the **technical and architectural foundation** for Neo4j graph database migration while cleaning up existing codebase for optimal performance.

### Non-Goals
- ❌ Actual Neo4j installation/integration (deferred to later phase)
- ❌ Breaking changes to existing functionality
- ❌ Major feature additions (focus is cleanup + foundation)

---

## 📊 Key Decisions from Pre-Planning

### 1. **Database Strategy: Neo4j Primary**
**Decision**: Use Neo4j as primary graph store (PostgreSQL 18 plan archived)

**Rationale**:
- ✅ **Native LightRAG support**: `Neo4JStorage` is production-tested, first-class citizen
- ✅ **Workspace isolation**: Native via labels (`:navy_mbos_2025` = workspace)
- ✅ **Performance**: 10-100x faster graph traversal than PostgreSQL AGE
- ✅ **Simplicity**: Schema-free (no 17-table design needed)
- ✅ **Cost**: $0 (self-hosted) vs $71/month (AWS RDS PostgreSQL)

**Impact**: 68% reduction in database complexity (25 PostgreSQL tables → 8 optional for reports)

### 2. **Token Budget Strategy: Comprehensive Prompts**
**Decision**: Expand prompts from 5K → 50K tokens with domain knowledge libraries

**Rationale**:
- Current utilization: <1% of 2M token budget (wasteful)
- Government contracting = legal RAG (precision > brevity)
- Domain knowledge prevents hallucinations (FAR/DFARS interpretations)
- 50K chunks tested: caused LLM laziness (revert to 8K, expand prompts instead)

**Target Allocation**:
```
Document chunks: 8K tokens (embedding limit constraint)
Extraction prompt: 50K tokens (base + FAR library + Shipley patterns)
Relationship inference: 40K tokens (6 algorithms + agency precedents)
User query context: 20K tokens
Total: ~120K tokens (6% utilization - room for growth)
```

### 3. **Chunk Size Constraint: 8192 Token Hard Limit**
**Finding**: LightRAG uses same variable for chunking AND embedding max token size

**Technical Constraint**:
- `text-embedding-3-large` = 8192 token limit
- `chunk_token_size` = `embedding_max_token_size` (hardcoded in LightRAG)
- Cannot use 32K chunks without breaking embeddings

**Tested**: 50K chunks → LLM laziness, extraction quality regression  
**Conclusion**: Keep 8K chunks, invest token budget in comprehensive prompts

### 4. **Relationship Inference: EVALUATED_BY Issue**
**Problem**: Not all MANDATORY requirements mapping to evaluation factors

**Root Cause Analysis**:
- Prompt complexity (5K tokens with extensive examples)
- LLM token budget exhaustion on examples vs actual inference
- Over-constraining rules causing skipped relationships

**Solution Path** (Branch 011 scope):
1. Streamline prompts (reduce token waste)
2. Add debug logging to track skipped relationships
3. Test with simplified 1.5K prompt vs current 5K
4. Create validation queries for known requirement→factor pairs

---

## 🏗️ Phase 1: Codebase Cleanup (Week 1-2)

### Task 1.1: Prompt Library Consolidation
**Goal**: Organize prompts into modular libraries for maintenance

**Current State**:
```
prompts/
├── extraction/
│   └── entity_extraction_prompt.md (5K tokens)
└── relationship_inference/
    └── 6 algorithm prompts (5K each)
```

**Target State**:
```
prompts/
├── extraction/
│   ├── base_entity_extraction.md (5K tokens - core)
│   ├── far_dfars_library.md (30K tokens - clause interpretations)
│   └── shipley_methodology.md (15K tokens - compliance patterns)
└── relationship_inference/
    ├── base_algorithms.md (30K tokens - 6 algorithms)
    └── agency_factor_patterns.md (10K tokens - Navy/AF precedents)
```

**Deliverables**:
- [ ] Create `far_dfars_library.md` with top 100 clauses (web search synthesis)
- [ ] Create `shipley_methodology.md` with compliance matrix patterns
- [ ] Create `agency_factor_patterns.md` with Navy/Air Force/Army evaluation weights
- [ ] Update `src/server/config.py` with modular prompt loading
- [ ] Add token counting/logging per prompt component

### Task 1.2: Relationship Inference Debugging
**Goal**: Diagnose and fix EVALUATED_BY relationship gaps

**Implementation**:
```python
# src/inference/engine.py - Add detailed logging
async def infer_relationships_batch(...):
    logger.info(f"📊 Input: {len(source_entities)} requirements, {len(target_entities)} factors")
    
    # Call LLM
    result = await llm_func(messages, response_format={"type": "json_object"})
    
    # DEBUG: Log raw LLM response
    logger.debug(f"🤖 LLM Raw Response:\n{result}")
    
    # Parse relationships
    relationships = json.loads(result)
    logger.info(f"✅ Parsed {len(relationships)} relationships")
    
    # DEBUG: Log what was skipped
    mapped_req_ids = {r['source_id'] for r in relationships}
    skipped = [r for r in source_entities if r['entity_name'] not in mapped_req_ids]
    if skipped:
        logger.warning(f"⚠️ Skipped {len(skipped)} requirements:")
        for req in skipped[:5]:
            logger.warning(f"  - {req['entity_name']}: {req['description'][:100]}")
```

**Deliverables**:
- [ ] Add debug logging to `infer_relationships_batch()`
- [ ] Create test suite: `tests/test_evaluated_by_relationships.py`
- [ ] Streamline `requirement_evaluation.md` prompt (5K → 1.5K tokens)
- [ ] Run baseline test: Navy MBOS EVALUATED_BY coverage
- [ ] Document findings in `docs/bug-fixes/EVALUATED_BY_COVERAGE_FIX.md`

### Task 1.3: Dead Code Removal
**Goal**: Remove unused code identified in Branch 004 audit

**Files to Review**:
- `src/raganything_server.py` - Remove commented-out code
- `src/inference/` - Consolidate duplicate algorithms
- `prompts/user_queries/` - Archive failed output prompt experiments (Branch 010)

**Deliverables**:
- [ ] Archive `prompts/user_queries/*.md` (except README.md) to `docs/archive/`
- [ ] Remove commented-out Phase 6 code from Branch 003-004
- [ ] Consolidate duplicate prompt loading functions
- [ ] Update `.gitignore` for archived files

---

## 🧪 Phase 2: Neo4j Foundation (Week 2-3)

### Task 2.1: Workspace Selection UI Design
**Goal**: Design workspace dropdown for WebUI (implementation deferred to Neo4j integration)

**Research Tasks**:
- [x] Confirm LightRAG WebUI uses React 19 + AsyncSelect component (GitHub search completed)
- [ ] Design workspace manager pattern for Neo4j labels
- [ ] Document API endpoints needed: `/workspaces`, `/insert` with workspace param
- [ ] Create wireframe for workspace dropdown in DocumentManager

**Deliverables**:
- [ ] `docs/neo4j/WORKSPACE_SELECTION_DESIGN.md` - UI/UX design doc
- [ ] `docs/neo4j/API_SPECIFICATION.md` - Endpoint contracts
- [ ] Decision: Extend existing LightRAG endpoints vs custom routes

### Task 2.2: Neo4j Local Setup Guide
**Goal**: Document Neo4j installation for development/testing

**Deliverables**:
- [ ] `docs/neo4j/TASK_01_NEO4J_SETUP.md` - Docker installation guide
- [ ] `.env.example.neo4j` - Neo4j configuration template
- [ ] Test queries: Verify workspace isolation with sample data
- [ ] Performance baseline: Compare Neo4j vs current JSON storage

### Task 2.3: Migration Strategy Document
**Goal**: Plan incremental migration from JSON → Neo4j

**Key Questions**:
1. Can LightRAG run in "hybrid mode" (JSON + Neo4j simultaneously)?
2. Data migration script: GraphML → Neo4j Cypher imports
3. Rollback strategy if Neo4j underperforms
4. Testing criteria before full cutover

**Deliverables**:
- [ ] `docs/neo4j/MIGRATION_STRATEGY.md` - Phased migration plan
- [ ] `scripts/migrate_graphml_to_neo4j.py` - Migration utility (draft)
- [ ] Test plan: 5-10 RFPs in Neo4j vs JSON (A/B comparison)

---

## 📏 Success Criteria

### Code Quality Metrics
- [ ] **LOC Reduction**: Net negative delta (remove > add)
- [ ] **Prompt Token Budget**: Document usage per component (target: 50K extraction, 40K inference)
- [ ] **Test Coverage**: >80% for relationship inference algorithms
- [ ] **No Regressions**: Navy MBOS baseline (594 entities, 69s processing) maintained

### Relationship Quality Metrics
- [ ] **EVALUATED_BY Coverage**: Improve from 38% → 75% (MANDATORY requirements)
- [ ] **Debug Visibility**: Log shows skipped relationships with reasoning
- [ ] **Prompt Efficiency**: Simplified prompts (1.5K) match or exceed 5K prompt quality

### Documentation Metrics
- [ ] **Neo4j Setup**: Complete Docker installation guide with test queries
- [ ] **Workspace Design**: API specification + UI wireframes
- [ ] **Migration Plan**: Phased rollout with rollback strategy

---

## 🚫 Out of Scope (Future Branches)

### Deferred to Branch 012: Neo4j Integration
- Actual Neo4j installation/configuration in production
- LightRAG `Neo4JStorage` configuration
- Data migration execution (GraphML → Cypher)
- Workspace selection UI implementation
- Performance benchmarking (Neo4j vs JSON)

### Deferred to Branch 013+: Advanced Features
- Multi-workspace event sourcing (RFP → Amendment → Proposal)
- Cross-RFP intelligence queries
- Agent architecture (PydanticAI for deliverable generation)
- PostgreSQL integration for agent outputs (Excel, compliance reports)

---

## 📋 Implementation Checklist

### Week 1: Prompt Library + Debugging
- [ ] Create FAR/DFARS clause library (30K tokens)
- [ ] Create Shipley methodology patterns (15K tokens)
- [ ] Create agency evaluation factor precedents (10K tokens)
- [ ] Add debug logging to relationship inference
- [ ] Streamline requirement_evaluation prompt (5K → 1.5K)
- [ ] Run baseline EVALUATED_BY coverage test
- [ ] Archive failed output prompts from Branch 010

### Week 2: Neo4j Foundation Design
- [ ] Document workspace selection UI design
- [ ] Design workspace manager API
- [ ] Create Neo4j setup guide (Docker)
- [ ] Draft migration strategy document
- [ ] Test LightRAG Neo4JStorage compatibility

### Week 3: Validation + Handoff
- [ ] Test comprehensive prompts with Navy MBOS RFP
- [ ] Measure EVALUATED_BY coverage improvement
- [ ] Validate no performance regressions
- [ ] Document findings and recommendations
- [ ] Create Branch 012 charter (Neo4j Integration)

---

## 🔗 Related Documentation

**Current Branch Context**:
- `docs/BRANCH_010_PIVOT.md` - Output prompts abandoned, extraction prompts kept
- `docs/postgresql18/README.md` - PostgreSQL 18 plan (archived, replaced by Neo4j)

**Neo4j Planning**:
- `docs/postgresql18/TASK_02_WORKSPACE_SELECTION_UI.md` - Original PostgreSQL UI design (adapt for Neo4j)

**Architecture**:
- `docs/ARCHITECTURE.md` - System architecture (update for Neo4j)
- `docs/ontology/` - 17 government contracting entity types (foundation for Neo4j labels)

**GitHub Research**:
- [LightRAG Neo4JStorage](https://github.com/HKUDS/LightRAG/blob/main/lightrag/kg/neo4j_impl.py) - Native implementation
- [LightRAG WebUI](https://github.com/HKUDS/LightRAG/tree/main/lightrag_webui) - React 19 AsyncSelect component

**Web Research Synthesis**:
- FAR/DFARS compliance requirements (Acquisition.gov, USFCR)
- Shipley compliance matrix methodology (Shipley Associates)
- NIST 800-171 cybersecurity requirements (DFARS 252.204-7012)

---

## 🎓 Key Learnings (To Document)

### Technical Insights
1. **8K Chunk Limit is Architectural**: LightRAG conflates chunking with embedding (cannot bypass without library fork)
2. **50K Chunks = Lazy LLMs**: "Lost in the Middle" problem confirmed in production
3. **Legal RAG ≠ Generic RAG**: Ontology-based extraction is foundation, not optional

### Strategic Insights
1. **Neo4j > PostgreSQL AGE**: Native performance, workspace labels, schema-free flexibility
2. **Comprehensive Prompts > Large Chunks**: Use 2M token budget for domain knowledge, not raw text
3. **Web Search = Valid Training Data**: Public FAR/DFARS knowledge synthesizable until real RFP corpus built

### Process Insights
1. **Incremental Migration**: Test Neo4j with 5-10 RFPs before full cutover
2. **Modular Prompts**: Separate base logic (5K) from domain libraries (40K) for maintainability
3. **Debug Visibility**: Log skipped relationships to diagnose inference gaps

---

**Last Updated**: October 26, 2025  
**Next Milestone**: Week 1 - Prompt library consolidation + EVALUATED_BY debugging  
**Branch Owner**: Development Team  
**Review Cycle**: Weekly check-ins, final review before Branch 012 creation
