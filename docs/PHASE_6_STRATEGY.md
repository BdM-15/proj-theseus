# Phase 6 Implementation Strategy: Adaptive Ontology Architecture

**Created**: 2025-01-06  
**Status**: ✅ APPROVED - Ready for Implementation  
**Approach**: Option A (Enhanced Entity Types) + Post-Processing Layer  
**Purpose**: Design scalable, customer-agnostic ontology that adapts to variable RFP structures  
**Challenge**: Federal RFPs vary wildly in structure while maintaining consistent underlying semantics

---

## 🚀 Quick Start Guide (For New Conversation)

**What to Implement**: Three-layer architecture to fix common RFP knowledge graph gaps (missing evaluation-to-instruction relationships, isolated attachments, fragmented clauses)

**Layer 1 - Enhanced Entity Types** (Week 1, `src/raganything_server.py` lines 85-99):

```python
entity_types = [
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",
    "REQUIREMENT", "CLAUSE", "SECTION", "DOCUMENT", "DELIVERABLE", "ANNEX",  # Added ANNEX
    "EVALUATION_FACTOR", "SUBMISSION_INSTRUCTION",  # NEW: Separates evaluation criteria from format/page instructions
    "STRATEGIC_THEME", "STATEMENT_OF_WORK"  # NEW: Capture planning + work scope
]
```

**Layer 2 - Metadata Fields** (Week 1, add to extraction logic):

- `REQUIREMENT`: requirement_type, criticality_level, priority_score, section_origin
- `EVALUATION_FACTOR`: factor_id, relative_importance, subfactors, section_l_reference
- `SUBMISSION_INSTRUCTION`: guides_factor, page_limits, format_requirements, volume_name

**Layer 3 - Post-Processing** (Week 3, add function after LightRAG extraction):

```python
def post_process_knowledge_graph(rag_storage_path):
    """Infers missing relationships after LightRAG builds graph"""
    # 1. Load existing entities/relationships from JSON
    # 2. Infer evaluation↔instruction links via semantic similarity
    # 3. Link numbered attachments to parent sections (pattern-based)
    # 4. Cluster contract clauses by regulation patterns
    # 5. Save enhanced relationships back to JSON
```

**Validation Approach**: Test on baseline RFP knowledge graph to measure improvements in relationship coverage, entity classification accuracy, and processing time.

**Key Implementation Notes**:

- ✅ Semantic-first detection: Content determines entity type, not section labels
- ✅ Agency-agnostic patterns: Support FAR, DFARS, and 20+ federal acquisition regulation supplements

---

## Problem Statement: The Variability Challenge

### Common Knowledge Graph Gaps in Federal RFPs

**What Current Ontology Handles Well** ✅:

- Extracts most standard sections (A-M)
- Identifies evaluation factor hierarchies (factors → subfactors)
- Captures numbered attachments and annexes
- Processes documents efficiently

**What Needs Enhancement** ❌:

- **Missing evaluation-to-instruction relationships**: Zero connections between evaluation criteria and format/page limit instructions when instructions embedded within evaluation sections (non-standard structure)
- **Root Cause**: Some RFPs place submission instructions within evaluation factor descriptions instead of separate instruction sections
- **Impact**: Cannot map page allocations to evaluation factors, strategic proposal planning broken
- **Isolated attachment entities**: Some numbered attachments not linked to parent sections
- **Clause fragmentation**: Contract clauses not grouped under parent sections

### Structural Variability Across Customers

| Variability Type         | Example                                                                                                                                                           | Impact on Ontology                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **SOW Location**         | Variation 1: PWS in Section C (100+ pages)<br>Variation 2: PWS as separate attachment                                                                             | Section C size varies dramatically                 |
| **Evaluation Structure** | Variation 1: Instructions embedded IN evaluation section<br>Variation 2: Instructions in separate section                                                         | Evaluation-to-instruction relationships fail       |
| **Document Formats**     | PDF, Word, PowerPoint, Excel (multi-tab), maps                                                                                                                    | Multimodal parsing complexity                      |
| **Nested Requirements**  | Large paragraphs with cross-section connections                                                                                                                   | Entity extraction misses nested "shall" statements |
| **Clause Grouping**      | Variation 1: Clauses grouped in Section I (Contract Clauses) and Section K (Representations/Certifications)<br>Variation 2: Clauses scattered throughout document | Graph topology varies, clustering logic differs    |
| **Supplement Types**     | Federal: FAR<br>DoD: DFARS<br>Agency-specific: AFFARS, AFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS<br>+ 20+ other acquisition regulation supplements        | Clause naming conventions differ by agency         |
| **Factor Naming**        | Traditional: Technical, Management, Past Performance<br>Non-traditional: Domain-specific terms                                                                    | Entity type matching breaks                        |
| **Award Vehicles**       | Standard RFP: Uniform Contract Format<br>Task Orders: Non-standard section naming                                                                                 | Section labels change entirely                     |

---

## Core Architectural Principle: **Semantic Over Structural**

### Current Approach (Fragile)

```
IF section_label == "Section L":
    entity_type = "SECTION"
    extract_instructions()
IF section_label == "Section M":
    entity_type = "EVALUATION_FACTOR"
    extract_factors()
```

**Problem**: Breaks when RFPs use non-standard structure (instructions embedded within evaluation sections)

### Proposed Approach (Adaptive)

```
# Extract based on SEMANTIC CONTENT, not labels
IF contains_evaluation_criteria_language("will be evaluated", "factor", "adjectival rating"):
    entity_type = "EVALUATION_FACTOR"
    section_origin = detect_section(context)  # Could be L, M, or custom

IF contains_submission_instructions("page limit", "font size", "format requirements"):
    entity_type = "SUBMISSION_INSTRUCTION"
    section_origin = detect_section(context)

# Relationship based on semantic connection, not section proximity
IF evaluation_factor.description mentions submission_instruction.volume_name:
    CREATE_RELATIONSHIP(submission_instruction → GUIDES → evaluation_factor)
```

---

## Phase 6 Ontology Enhancement Strategy

### 1. **Entity Type Architecture: Semantic + Structural**

**Current (12 types)**:

```python
entity_types = [
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",
    "REQUIREMENT", "CLAUSE", "SECTION", "DOCUMENT", "DELIVERABLE", "EVALUATION_FACTOR"
]
```

**Phase 6 Enhanced (18 types with semantic markers)**:

```python
entity_types = [
    # Core entities (existing)
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",

    # Requirement entities (NEW subtypes with semantic detection)
    "REQUIREMENT",              # Generic catch-all
    "REQUIREMENT_FUNCTIONAL",   # Detected by: "shall provide", "must deliver"
    "REQUIREMENT_PERFORMANCE",  # Detected by: SLA language, metrics, "within X time"
    "REQUIREMENT_SECURITY",     # Detected by: NIST, FedRAMP, clearance, cybersecurity

    # Structural entities (existing)
    "CLAUSE",                   # Detected by: FAR/DFARS/AFARS pattern, clause numbers
    "SECTION",                  # Detected by: "Section A/B/C" or structural position
    "DOCUMENT",                 # PDF/Word/Excel file references
    "DELIVERABLE",              # Detected by: CLIN/SLIN, deliverable schedules

    # Evaluation entities (NEW - semantically detected)
    "EVALUATION_FACTOR",        # Detected by: evaluation language, factor structure
    "SUBMISSION_INSTRUCTION",   # Detected by: page limits, format requirements (Section L content)
    "EVALUATION_CRITERION",     # Detected by: scoring methodology, adjectival ratings

    # Strategic entities (NEW from capture patterns)
    "STRATEGIC_THEME",          # Win themes, hot buttons (manual/AI-assisted)
    "COMPETITIVE_POSITION",     # Discriminators, proof points

    # Annexes/Attachments (enhanced detection)
    "ANNEX",                    # Detected by: J-###, Attachment patterns, Annex naming
    "STATEMENT_OF_WORK",        # Detected by: PWS/SOW/SOO content (regardless of section)
]
```

### 2. **Semantic Detection Patterns (LLM Prompts)**

**Instead of hardcoding section labels, use semantic extraction prompts**:

```python
# Entity extraction prompt enhancement
ENTITY_EXTRACTION_PROMPT = """
Extract entities based on SEMANTIC CONTENT, not just labels:

EVALUATION_FACTOR Detection:
- Language: "will be evaluated", "evaluation factor", "technical approach", "past performance"
- Structure: Factor hierarchy (Factor 1 → Subfactor 1.1 → Subfactor 1.1.1)
- Context: Near adjectival ratings, point scores, relative importance statements
- Source: Can appear in Section M, Section L, or custom sections

SUBMISSION_INSTRUCTION Detection:
- Language: "page limit", "font size", "margins", "format requirements", "volume structure"
- Structure: Maps to evaluation factors (e.g., "Technical Volume addresses Factor 2")
- Context: Submission deadlines, electronic vs. hard copy
- Source: May appear in instruction sections OR embedded within evaluation sections (non-standard)

REQUIREMENT Detection (Criticality-Based):
- MANDATORY: "shall", "must", "is required to", "will be required"
  * Subject analysis: "Contractor shall" = MANDATORY
  * Subject analysis: "Government will" = INFORMATIONAL (not a requirement)
- IMPORTANT: "should", "encouraged to", "desirable", "preferred"
- OPTIONAL: "may", "can", "has the option to"

REQUIREMENT Type Classification (Content-Based):
- FUNCTIONAL: "provide", "deliver", "perform", "execute" + service/product
- PERFORMANCE: SLA language, metrics (e.g., "99.9% uptime", "within 24 hours")
- SECURITY: NIST references, FedRAMP, clearance levels, cybersecurity controls
- TECHNICAL: Technology stack, platform requirements, software versions
- INTERFACE: Integration points, data exchange, APIs, system connections
- MANAGEMENT: Reporting requirements, governance, oversight, meetings
- DESIGN: Standards compliance (508, architectural mandates)
- QUALITY: QA processes, testing requirements, acceptance criteria

ANNEX Detection (Pattern-Based):
- Patterns: Numbered formats like "X-######", "Attachment #", "Annex ##", "Appendix X"
- Content: Could contain SOW, technical specs, maps, data sheets
- Connection: Link to parent section based on naming prefix patterns

STATEMENT_OF_WORK Detection (Content-Based, Not Label):
- Language: Task descriptions, performance objectives, deliverables
- Structure: Often hierarchical tasks (Task 1 → Subtask 1.1)
- Location: Could be Section C, separate attachment, or embedded in Section J
- Identifiers: "Performance Work Statement", "Statement of Work", "Statement of Objectives"
"""
```

### 3. **Relationship Inference (Semantic-Based)**

**Current Problem**: Some RFPs have zero evaluation-to-instruction relationships because LightRAG relies on proximity/explicit mentions.

**Phase 6 Solution**: **Semantic Relationship Inference** using pattern matching:

```python
# Relationship extraction prompt enhancement
RELATIONSHIP_EXTRACTION_PROMPT = """
Extract relationships based on SEMANTIC CONNECTIONS, not just co-occurrence:

EVALUATION_FACTOR ← GUIDES ← SUBMISSION_INSTRUCTION:
- Pattern 1: Explicit mention ("Technical Volume addresses Factor 2")
- Pattern 2: Implicit mapping (page limits near factor descriptions)
- Pattern 3: Content alignment (submission instruction topics match factor topics)
- Note: Even if instructions embedded within evaluation sections, create separate
  SUBMISSION_INSTRUCTION entity and link to EVALUATION_FACTOR

REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR:
- Pattern 1: Explicit traceability matrix mentions
- Pattern 2: Topic alignment (maintenance requirements link to "Maintenance Approach" factor)
- Pattern 3: Criticality mapping (high-importance requirements link to high-weight factors)

CLAUSE → CHILD_OF → SECTION:
- Pattern 1: Clause numbering (52.###-# belongs to FAR Section 52)
- Pattern 2: Section attribution (clauses listed under "Section I" heading)
- Pattern 3: Clause type clustering (similar clauses grouped even if scattered)

ANNEX → REFERENCED_BY → REQUIREMENT:
- Pattern 1: Explicit citation ("See Attachment X-1234567 for equipment list")
- Pattern 2: Content alignment (annex describes tools, requirement mentions tool usage)
- Pattern 3: Naming convention (annex number appears in requirement text)

STRATEGIC_THEME → SUPPORTS → EVALUATION_FACTOR:
- Pattern: Hot button language in factor descriptions signals theme opportunity
- Example: Factor emphasizes "readiness" → STRATEGIC_THEME("Mission Readiness Focus")
"""
```

### 4. **Adaptive Section Detection**

**Problem**: Task Orders use different section labels than standard RFPs.

**Solution**: **Section Normalization Layer**

```python
# Section normalization mapping
SECTION_SEMANTIC_MAPPING = {
    # Standard Uniform Contract Format
    "Section A": {"semantic_type": "SOLICITATION_FORM", "aliases": ["SF 1449", "Cover Page"]},
    "Section B": {"semantic_type": "SUPPLIES_SERVICES", "aliases": ["CLIN Structure", "SLIN"]},
    "Section C": {"semantic_type": "DESCRIPTION_SPECS", "aliases": ["SOW", "PWS", "SOO"]},
    "Section D": {"semantic_type": "PACKAGING_MARKING", "aliases": ["Shipping Instructions"]},
    "Section E": {"semantic_type": "INSPECTION_ACCEPTANCE", "aliases": ["Quality Assurance"]},
    "Section F": {"semantic_type": "DELIVERIES_PERFORMANCE", "aliases": ["Schedule", "PoP"]},
    "Section G": {"semantic_type": "CONTRACT_ADMIN", "aliases": ["Admin Data", "CAGE codes"]},
    "Section H": {"semantic_type": "SPECIAL_REQUIREMENTS", "aliases": ["H-clauses", "Special Terms"]},
    "Section I": {"semantic_type": "CONTRACT_CLAUSES", "aliases": ["FAR Clauses", "I-clauses"]},
    "Section J": {"semantic_type": "ATTACHMENTS", "aliases": ["List of Attachments", "Annexes"]},
    "Section K": {"semantic_type": "REPRESENTATIONS", "aliases": ["Reps and Certs", "K-clauses"]},
    "Section L": {"semantic_type": "SUBMISSION_INSTRUCTIONS", "aliases": ["Instructions to Offerors", "Proposal Format"]},
    "Section M": {"semantic_type": "EVALUATION_CRITERIA", "aliases": ["Evaluation Factors", "Source Selection"]},

    # Task Order / Fair Opportunity variations
    "Request for Quote": {"semantic_type": "SOLICITATION_FORM", "maps_to": "Section A"},
    "Technical Requirements": {"semantic_type": "DESCRIPTION_SPECS", "maps_to": "Section C"},
    "Proposal Instructions": {"semantic_type": "SUBMISSION_INSTRUCTIONS", "maps_to": "Section L"},
    "Selection Criteria": {"semantic_type": "EVALUATION_CRITERIA", "maps_to": "Section M"},
}

# Detection logic
def detect_section_semantic_type(text_chunk):
    """
    Determine section type based on content, not just label.
    Returns both structural_label and semantic_type.
    """
    # Check for explicit label first
    if matches_section_pattern(text_chunk):  # "Section A", etc.
        structural_label = extract_section_label(text_chunk)
        semantic_type = SECTION_SEMANTIC_MAPPING[structural_label]["semantic_type"]

    # Fallback to content-based detection (for non-standard structures)
    else:
        if contains_evaluation_language(text_chunk):
            semantic_type = "EVALUATION_CRITERIA"
            structural_label = detect_custom_label(text_chunk)  # "Part III", "Criteria", etc.

        elif contains_submission_instructions(text_chunk):
            semantic_type = "SUBMISSION_INSTRUCTIONS"
            structural_label = detect_custom_label(text_chunk)

        elif contains_clause_patterns(text_chunk):
            semantic_type = "CONTRACT_CLAUSES"
            structural_label = detect_custom_label(text_chunk)

        # etc...

    return {
        "structural_label": structural_label,  # What document calls it
        "semantic_type": semantic_type,        # What it actually IS
        "confidence": calculate_confidence()   # How sure are we?
    }
```

---

## Phase 6 Implementation Plan

### Step 1: Enhance Entity Type Definitions (In `raganything_server.py`)

**Current**:

```python
global_args.entity_types = [
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",
    "REQUIREMENT", "CLAUSE", "SECTION", "DOCUMENT", "DELIVERABLE", "EVALUATION_FACTOR"
]
```

**Phase 6 Enhanced**:

```python
global_args.entity_types = [
    # Core entities
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",

    # Requirements (keep generic + add semantic detection in prompts)
    "REQUIREMENT",  # LLM will classify subtype via requirement_type metadata

    # Structural
    "CLAUSE", "SECTION", "DOCUMENT", "DELIVERABLE", "ANNEX",

    # Evaluation (semantic detection via prompts)
    "EVALUATION_FACTOR",          # Scoring criteria (Section M content)
    "SUBMISSION_INSTRUCTION",     # Format/page limits (Section L content, may be IN Section M)

    # Strategic (NEW)
    "STRATEGIC_THEME",            # Win themes, hot buttons, discriminators

    # Work Scope (NEW - semantic detection regardless of location)
    "STATEMENT_OF_WORK",          # PWS/SOW/SOO content (may be Section C or attachment)
]
```

**Key Change**: We keep entity types somewhat generic, but add **metadata fields** that capture semantic nuances:

```python
# REQUIREMENT entity metadata (from CAPTURE_INTELLIGENCE_PATTERNS.md)
requirement_metadata = {
    "requirement_type": ["FUNCTIONAL", "PERFORMANCE", "INTERFACE", "DESIGN",
                         "SECURITY", "TECHNICAL", "MANAGEMENT", "QUALITY"],
    "criticality_level": ["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"],
    "priority_score": 0-100,
    "section_origin": "Section C.3.1.2",  # Where it appeared (structural)
    "semantic_context": "Performance requirement within maintenance SOW",  # What it IS
}

# EVALUATION_FACTOR entity metadata
evaluation_factor_metadata = {
    "factor_id": "M2.1",
    "factor_name": "Staffing Approach",
    "relative_importance": "Most Important",
    "subfactors": ["M2.1.1 Surge Capacity", "M2.1.2 Retention"],
    "section_l_reference": "L.3.1",  # Link to submission instructions
    "page_limits": "25 pages",
    "format_requirements": "12pt Times New Roman, 1-inch margins",
    "tradeoff_methodology": "Best Value",
    "section_origin": "Section M.2.1",  # Where it appeared
    "contains_submission_instructions": True,  # Non-standard: instructions embedded in evaluation section
}

# SUBMISSION_INSTRUCTION entity metadata (NEW type)
submission_instruction_metadata = {
    "guides_factor": "M2",  # Which evaluation factor this instructs
    "volume_name": "Technical Volume",
    "page_limits": "25 pages",
    "format": "12pt Times, 1-inch margins, single-spaced",
    "section_origin": "Section M.2.1",  # May be embedded in evaluation section or separate
    "delivery_method": "Electronic via email",
    "deadline": "2025-01-15 14:00 EST",
}

# SECTION entity metadata (adaptive)
section_metadata = {
    "structural_label": "Section M.2.1",     # What document calls it
    "semantic_type": "EVALUATION_CRITERIA",   # What it actually IS
    "also_contains": ["SUBMISSION_INSTRUCTION"],  # Mixed content case
    "confidence": 0.98,                        # Detection confidence
}
```

### Step 2: Enhance Extraction Prompts (Semantic-First)

**Location**: `raganything_server.py` uses LightRAG's default prompts. We need to customize.

**Current LightRAG approach**: Relies on entity co-occurrence and proximity for relationships.

**Phase 6 Enhancement**: Add **semantic relationship inference** via custom prompts.

**Implementation Options within RAG-Anything/LightRAG**:

**Option A: Custom Entity Extraction Prompt (Best for Phase 6)**

```python
# In raganything_server.py, after global_args initialization

# Custom entity extraction prompt with semantic detection
CUSTOM_ENTITY_EXTRACTION_PROMPT = """
You are extracting entities from federal government RFP documents.

CRITICAL: Extract based on SEMANTIC CONTENT, not just labels or section headings.

Entity Types and Detection Rules:

1. EVALUATION_FACTOR:
   - Detect by content: "will be evaluated", "evaluation factor", "adjectival rating"
   - May appear in Section M, Section L, or custom sections
   - Extract factor hierarchy: Factor 1 → Subfactor 1.1 → Subfactor 1.1.1
   - Include relative importance: "Most Important", "Significantly More Important than Price"
   - Note: Some RFPs embed submission instructions within evaluation factor descriptions

2. SUBMISSION_INSTRUCTION:
   - Detect by content: "page limit", "font size", "margins", "volume structure"
   - Typically Section L, but may be embedded in Section M (non-standard structure)
   - Map to evaluation factors they guide (e.g., "Technical Volume addresses Factor 2")
   - Extract format requirements, deadlines, delivery method

3. REQUIREMENT (with subtype classification):
   - Criticality detection:
     * MANDATORY: "Contractor shall", "Offeror must" (subject = contractor)
     * INFORMATIONAL: "Government will" (subject = government, NOT a requirement)
     * IMPORTANT: "should", "encouraged to", "preferred"
     * OPTIONAL: "may", "can", "has the option"

   - Type classification:
     * FUNCTIONAL: "shall provide service", "must deliver system"
     * PERFORMANCE: SLA language, metrics ("99.9% uptime", "within 24 hours")
     * SECURITY: NIST, FedRAMP, clearance, cybersecurity terms
     * TECHNICAL: Technology stack, platform, software versions
     * INTERFACE: Integration, data exchange, API, system connections
     * MANAGEMENT: Reporting, governance, meetings, project management
     * DESIGN: Standards compliance (508 accessibility, architectural mandates)
     * QUALITY: QA processes, testing, acceptance criteria

4. STATEMENT_OF_WORK:
   - Detect by content, NOT location (may be Section C, attachment, or numbered annex)
   - Language: Task descriptions, performance objectives, deliverables, work scope
   - Identifiers: "PWS", "Performance Work Statement", "SOW", "SOO", "Statement of"
   - Structure: Often hierarchical (Task 1 → Subtask 1.1 → Subtask 1.1.1)

5. ANNEX / Attachment:
   - Patterns: Numbered formats ("X-######", "Attachment #", "Annex ##", "Appendix X")
   - Always link to parent section based on naming prefix
   - Content determines subtype (could contain SOW, specs, maps, data)

6. CLAUSE:
   - Patterns: FAR ##.###-##, DFARS ###.###-####, AFFARS ####.###-##, NMCARS ####.###-##, and 20+ other agency supplement patterns
   - Should cluster by section (Section I clauses, Section K representations)
   - Group similar clauses even if scattered in document

7. SECTION:
   - Extract both structural_label ("Section M.2.1") AND semantic_type ("EVALUATION_CRITERIA")
   - Map non-standard labels to semantic types ("Selection Criteria" = EVALUATION_CRITERIA)
   - Note if section contains mixed content (evaluation + instructions combined)

Entity metadata to extract:
- All entities: source_section, page_number, confidence_score
- REQUIREMENT: requirement_type, criticality_level, priority_score
- EVALUATION_FACTOR: factor_id, relative_importance, subfactors, section_l_reference
- SUBMISSION_INSTRUCTION: guides_factor, page_limits, format_requirements
- SECTION: structural_label, semantic_type, also_contains[]

Return entities in JSON format with all metadata fields.
"""

# Custom relationship extraction prompt with semantic inference
CUSTOM_RELATIONSHIP_EXTRACTION_PROMPT = """
You are extracting relationships between entities in federal RFP documents.

CRITICAL: Infer relationships based on SEMANTIC CONNECTIONS, not just co-occurrence.

Relationship Types and Detection Rules:

1. SUBMISSION_INSTRUCTION → GUIDES → EVALUATION_FACTOR:
   - Explicit: "Technical Volume addresses Factor 2"
   - Implicit: Page limit near factor description (same paragraph/section)
   - Content alignment: Instruction topic matches factor topic
   - SPECIAL CASE: If instructions embedded within evaluation factor description,
     create separate SUBMISSION_INSTRUCTION entity and link to parent EVALUATION_FACTOR

2. REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR:
   - Explicit: Traceability matrix mentions ("Req 45 evaluated under Factor 2.1")
   - Topic alignment: Maintenance requirements link to "Maintenance Approach" factor
   - Criticality mapping: MANDATORY requirements link to high-weight factors
   - Content proximity: Requirements in SOW section link to Technical Approach factor

3. CLAUSE → CHILD_OF → SECTION:
   - Numbering: FAR 52.###-# belongs to Section 52 parent
   - Attribution: Clause listed under "Section I" heading
   - Clustering: Group similar clauses (all FAR 52.2##-# together)
   - FRAGMENTATION FIX: Link scattered clauses to parent even if not adjacent

4. ANNEX → REFERENCED_BY → REQUIREMENT | SECTION:
   - Explicit citation: "See Attachment X-1234567 for equipment list"
   - Content alignment: Annex describes tools, requirement mentions tool usage
   - Naming convention: Annex identifier appears in requirement text
   - ISOLATION FIX: Link numbered attachments to parent sections based on prefix pattern

5. REQUIREMENT → COMPONENT_OF → STATEMENT_OF_WORK:
   - SOW contains requirement (parent-child relationship)
   - Works regardless of SOW location (Section C vs. attachment)

6. EVALUATION_FACTOR → REFERENCES → STATEMENT_OF_WORK:
   - Factor evaluates work described in SOW
   - Example: "Technical Approach" factor references tasks in PWS

7. STRATEGIC_THEME → SUPPORTS → EVALUATION_FACTOR:
   - Hot button language in factor description signals theme opportunity
   - Example: Factor emphasizes "readiness" → theme "Mission Readiness Focus"

8. SECTION → CONTAINS → [ENTITY]:
   - Standard parent-child for any entity within a section
   - Include semantic_type for adaptive mapping

Relationship metadata to extract:
- All relationships: confidence_score, detection_method (explicit/implicit/inferred)
- EVALUATED_BY: evaluation_weight, importance_level
- GUIDES: volume_mapping, page_allocation
- CHILD_OF: hierarchical_level, position_in_parent

Return relationships as entity pairs with relationship type and metadata.

PRIORITY RELATIONSHIP PATTERNS:
1. Create SUBMISSION_INSTRUCTION → GUIDES → EVALUATION_FACTOR even when instructions embedded in evaluation sections
2. Link scattered numbered attachments to parent sections based on naming patterns (ANNEX → CHILD_OF → SECTION)
3. Cluster contract clauses under parent sections (CLAUSE → CHILD_OF → SECTION)
4. Infer REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR via topic alignment
"""

# Apply custom prompts to LightRAG
# NOTE: RAG-Anything uses lightrag-hku's default prompts
# We need to override these in the initialization

# This is a SIMPLIFIED example - actual implementation needs lightrag prompt customization
global_args.entity_extraction_prompt = CUSTOM_ENTITY_EXTRACTION_PROMPT
global_args.relationship_extraction_prompt = CUSTOM_RELATIONSHIP_EXTRACTION_PROMPT
```

**IMPLEMENTATION DECISION: Option A + Post-Processing (APPROVED)**

**Chosen Approach**: Enhance entity_types parameter + Post-processing relationship inference layer

**Why Option A**:

- ✅ Faster to implement and test (no deep diving into lightrag-hku internals)
- ✅ Less maintenance burden (fewer breaking changes on lightrag-hku updates)
- ✅ Agency-agnostic patterns easier to maintain in post-processing code than LLM prompts
- ✅ Regex libraries for clause patterns (FAR, DFARS, AFFARS, NMCARS, etc.) faster than LLM inference
- ✅ Can add new agencies without retraining prompt logic
- ✅ Post-processing can evolve independently of LightRAG core

**Knowledge Graph Construction Timeline (Option A)**:

```
1. Document Upload (t=0s)
2. LightRAG Extraction (t=0-70s) → Knowledge Graph Built (initial entities + relationships extracted)
3. Post-Processing Layer (t=70-75s) → Knowledge Graph Enhanced (additional relationships inferred)
4. Ready for Querying (t=75s)
```

**Post-processing is additive**: Loads existing graph, adds relationships, saves back (non-destructive enhancement).

**Note**: Option B (custom LightRAG prompts) remains available as contingency if Option A validation shows <5 L↔M relationships after post-processing. Evaluate need during Week 4 testing.

### Step 3: Post-Processing Relationship Inference Layer

**Problem**: LightRAG may not catch semantic relationships that aren't explicit.

**Solution**: Add post-processing step after LightRAG extraction to infer missing relationships.

**Workflow**:

1. LightRAG builds initial knowledge graph (entities + relationships)
2. Post-processing LOADS existing graph, ADDS missing relationships, SAVES back
3. Knowledge graph files updated in-place (non-destructive enhancement)
4. Total time: LightRAG extraction (69s) + post-processing (5-10s) = ~75-80s

```python
# Add to raganything_server.py after document processing

def post_process_knowledge_graph(rag_storage_path):
    """
    Post-processing layer to infer semantic relationships LightRAG may have missed.
    Runs AFTER LightRAG builds initial knowledge graph.
    Loads existing entities/relationships, adds missing connections, saves back.

    Typical Timeline:
    - t=0-70s: LightRAG extraction (entities + initial relationships)
    - t=70s: Knowledge graph files written (kv_store_full_entities.json, etc.)
    - t=70-75s: This function runs (infers additional relationships)
    - t=75s: Knowledge graph files UPDATED (enhanced relationship coverage)
    """
    # Load entities and relationships
    entities = load_entities(rag_storage_path)
    relationships = load_relationships(rag_storage_path)

    # Infer missing evaluation↔instruction relationships
    evaluation_factors = [e for e in entities if e.type == "EVALUATION_FACTOR"]
    submission_instructions = [e for e in entities if e.type == "SUBMISSION_INSTRUCTION"]

    for factor in evaluation_factors:
        for instruction in submission_instructions:
            # Check if relationship already exists
            if not relationship_exists(instruction, factor, "GUIDES"):
                # Infer relationship based on semantic similarity
                if semantic_similarity(instruction.text, factor.text) > 0.7:
                    create_relationship(instruction, factor, "GUIDES", confidence=0.8)

                # Check for explicit references
                if factor.factor_id in instruction.text or instruction.volume_name in factor.text:
                    create_relationship(instruction, factor, "GUIDES", confidence=0.95)

    # Link scattered clauses to parent sections
    clauses = [e for e in entities if e.type == "CLAUSE"]
    sections = [e for e in entities if e.type == "SECTION"]

    for clause in clauses:
        # Find parent section based on clause number or content
        parent_section = find_parent_section(clause, sections)
        if parent_section and not relationship_exists(clause, parent_section, "CHILD_OF"):
            create_relationship(clause, parent_section, "CHILD_OF", confidence=0.9)

    # Link isolated numbered attachments to parent sections
    annexes = [e for e in entities if e.type == "ANNEX"]

    for annex in annexes:
        # Extract prefix pattern (e.g., "J-" from "J-1234567")
        prefix = extract_prefix_pattern(annex.name)
        parent_section = find_section_by_prefix(sections, prefix)

        if parent_section and not relationship_exists(annex, parent_section, "CHILD_OF"):
            create_relationship(annex, parent_section, "CHILD_OF", confidence=1.0)

    # Infer REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR via topic matching
    requirements = [e for e in entities if e.type == "REQUIREMENT"]

    for requirement in requirements:
        # Find relevant evaluation factors based on topic similarity
        relevant_factors = find_relevant_factors(requirement, evaluation_factors, threshold=0.6)
        for factor in relevant_factors:
            if not relationship_exists(requirement, factor, "EVALUATED_BY"):
                create_relationship(requirement, factor, "EVALUATED_BY",
                                   confidence=calculate_confidence(requirement, factor))

    # Save enhanced knowledge graph
    save_entities(entities, rag_storage_path)
    save_relationships(relationships, rag_storage_path)

    return {
        "relationships_added": count_new_relationships(),
        "sections_normalized": count_normalized_sections(),
        "annexes_linked": count_linked_annexes()
    }
```

---

## Scalability & Flexibility: Key Design Principles

### Principle 1: **Content Over Labels**

- Detect entity types by semantic content, not section headings
- "Evaluation Criteria" in Section M = EVALUATION_FACTOR, even if not labeled "Factor"
- PWS in Section C vs. attachment = same STATEMENT_OF_WORK entity type

### Principle 2: **Metadata-Rich Entities**

- Store both `structural_label` ("Section M.2.1") and `semantic_type` ("EVALUATION_CRITERIA")
- Capture `section_origin` so we know where it appeared
- Add `also_contains[]` for mixed-content sections (e.g., sections with both evaluation + instructions)

### Principle 3: **Relationship Inference**

- Don't rely only on explicit mentions or proximity
- Use semantic similarity, topic alignment, and domain patterns
- Post-processing layer fills gaps LightRAG misses

### Principle 4: **Adaptive Section Mapping**

- Normalize non-standard section labels to semantic types
- Task Order "Selection Criteria" → maps_to "EVALUATION_CRITERIA"
- Fair Opportunity Request "Technical Requirements" → maps_to "DESCRIPTION_SPECS"

### Principle 5: **Hierarchical Clustering**

- Group related entities even if scattered (clauses, annexes, requirements)
- Use naming patterns (J-######, FAR 52.###) to infer relationships
- Create parent-child hierarchies that match semantic structure

---

## Implementation Priority (Phase 6 Roadmap)

### **Week 1: Core Ontology Enhancement**

1. ✅ Add new entity types: SUBMISSION_INSTRUCTION, STRATEGIC_THEME, ANNEX, STATEMENT_OF_WORK
2. ✅ Add metadata fields to existing types (requirement_type, criticality_level, etc.)
3. ✅ Update entity_types array in raganything_server.py

### **Week 2: Test Enhanced Entity Types**

1. 🔨 Re-run baseline RFP with enhanced entity_types (no post-processing yet)
2. 🔨 Measure baseline improvement: Entity count, new types detected (SUBMISSION_INSTRUCTION, ANNEX, etc.)
3. 🔨 Validate metadata extraction: Check requirement_type, criticality_level fields populated
4. 🔨 Identify remaining gaps for post-processing layer to address

### **Week 3: Post-Processing Layer**

1. 🔨 Implement post_process_knowledge_graph() function
2. 🔨 Add relationship inference for L↔M, clauses→sections, annexes→sections
3. 🔨 Add semantic similarity matching for REQUIREMENT → EVALUATED_BY

### **Week 4: Validation & Testing**

1. 🔨 Re-run baseline RFP with enhanced ontology (full Phase 6 implementation)
2. 🔨 Measure: Evaluation↔instruction relationships present? Annexes linked? Clauses grouped?
3. 🔨 Test on large RFP (100+ pages, PWS in Section C)
4. 🔨 Test on Task Order (non-standard structure)
5. 🔨 Document improvements vs. baseline

---

## Success Metrics (Baseline RFP Validation)

| Metric                         | Baseline (5 Oct) | Phase 6 Target | Measurement Method                                 |
| ------------------------------ | ---------------- | -------------- | -------------------------------------------------- |
| **Entities**                   | Baseline count   | +10% increase  | Count after extraction                             |
| **Relationships**              | Baseline count   | +30% increase  | Count after extraction + post-processing           |
| **L↔M Relationships**          | 0 ❌             | ≥5 ✅          | Grep "SUBMISSION_INSTRUCTION.\*EVALUATION_FACTOR"  |
| **Annex Linkage**              | ~80%             | 100%           | Count annexes with CHILD_OF → parent section       |
| **Clause Clustering**          | Fragmented       | Grouped        | Count Section I/K clauses with parent links        |
| **Requirement Classification** | 0%               | ≥90%           | Count requirements with requirement_type metadata  |
| **Criticality Parsing**        | 0%               | ≥95%           | Count requirements with criticality_level metadata |
| **Processing Time**            | 60-70 seconds    | ≤80 seconds    | Allow +10s for post-processing overhead            |
| **Cost**                       | $0.042           | ≤$0.05         | Token usage for enhanced prompts                   |

---

## Answers to Your Specific Concerns

### Q1: "How do we make this RFP and customer agnostic?"

**A**: Semantic-first detection instead of label matching. Content determines entity type, not section heading.

### Q2: "PWS in Section C vs. separate attachment?"

**A**: New STATEMENT_OF_WORK entity type detected by content ("Performance Work Statement", task structure), regardless of location. Metadata stores `section_origin` for traceability.

### Q3: "Nested requirements across multiple sections?"

**A**: Enhanced REQUIREMENT extraction with `requirement_type` classification. Post-processing layer infers cross-section relationships via semantic similarity.

### Q4: "Scattered clauses not grouped?"

**A**: Post-processing clusters clauses by parent section (CLAUSE → CHILD_OF → SECTION) using clause numbering patterns and content proximity.

### Q5: "Non-traditional evaluation factors (Total Compensation, Reliability)?"

**A**: EVALUATION_FACTOR detection based on evaluation language ("will be evaluated", "factor", ratings), not predefined factor names. Works with any factor label.

### Q6: "Fair Opportunity Proposal Requests (non-standard structure)?"

**A**: Section normalization layer maps custom labels to semantic types ("Selection Criteria" → EVALUATION_CRITERIA). Ontology adapts to any structure.

### Q7: "Scalable within RAG-Anything/LightRAG framework?"

**A**: Yes. Three-layer approach:

1. **LightRAG Core**: Enhanced entity types + metadata fields (no code changes to lightrag-hku)
2. **Custom Prompts**: Semantic detection instructions (can override default prompts)
3. **Post-Processing**: Relationship inference layer (runs after LightRAG extraction)

This keeps us within RAG-Anything/LightRAG architecture while adding needed flexibility.

---

## Next Steps

1. **Review this strategy document** - Does this approach address your concerns?
2. **Begin implementation** - Start with core ontology enhancements (entity types + metadata)
3. **Test incrementally** - Baseline RFP → Large RFP → Task Order (increasing complexity)
4. **Iterate based on results** - Refine semantic detection and post-processing rules

**Key Insight**: We're not fighting LightRAG's structure - we're augmenting it with semantic intelligence that makes it customer-agnostic. The ontology becomes a flexible framework that adapts to content, not rigid rules that break on non-standard structures.

Ready to proceed with implementation?

---

## Implementation Summary (Ready to Code)

**Approved Approach**: Option A + Post-Processing Layer

**Three-Layer Architecture**:

1. **Enhanced Entity Types** (Week 1): Add SUBMISSION_INSTRUCTION, STRATEGIC_THEME, ANNEX, STATEMENT_OF_WORK to `entity_types` array in `src/raganything_server.py`
2. **Metadata Fields** (Week 1): Add requirement_type, criticality_level, factor_id, relative_importance, etc. to entity extraction logic
3. **Post-Processing Layer** (Week 3): Implement `post_process_knowledge_graph()` function that runs after LightRAG extraction to infer missing L↔M, clause clustering, annex linkage

**Key Files to Modify**:

- `src/raganything_server.py`: Lines 85-99 (entity_types array), add post-processing function
- Baseline for validation: Stored baseline RFP knowledge graph (before Phase 6 enhancements)

**Success Criteria (Baseline RFP Re-run)**:

- ≥5 L↔M relationships (currently 0)
- 100% numbered annex linkage to parent sections
- 90%+ requirements classified by type and criticality
- ≤80 seconds total processing time
- ≤$0.05 cost per run

**Agency Supplement Patterns to Support**:
FAR, DFARS, AFFARS, AFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, plus 20+ other agency-specific supplements

**Next Steps**:

1. Begin Week 1: Enhance entity_types array with 6 new types
2. Add metadata extraction logic for requirement_type, criticality_level, factor_id
3. Test incremental changes on baseline RFP knowledge graph
4. Implement post-processing layer with relationship inference algorithms
5. Validate improvements against success metrics

---

**Document Status**: ✅ APPROVED - Ready for Implementation  
**Implementation Branch**: `003-phase6-ontology-enhancement`  
**Start Date**: January 6, 2025  
**Estimated Completion**: 4 weeks (February 3, 2025)

---

## 📋 Implementation Checklist (Copy to New Conversation)

**Week 1 Tasks**:

- [ ] Modify `src/raganything_server.py` lines 85-99: Add 6 new entity types (SUBMISSION_INSTRUCTION, STRATEGIC_THEME, ANNEX, STATEMENT_OF_WORK)
- [ ] Add metadata extraction logic for requirement_type (8 types: FUNCTIONAL, PERFORMANCE, INTERFACE, DESIGN, SECURITY, TECHNICAL, MANAGEMENT, QUALITY)
- [ ] Add metadata extraction logic for criticality_level (4 levels: MANDATORY, IMPORTANT, OPTIONAL, INFORMATIONAL)
- [ ] Add metadata extraction logic for EVALUATION_FACTOR (factor_id, relative_importance, subfactors)
- [ ] Test incremental changes: Upload baseline RFP, verify new entity types detected

**Week 2 Tasks**:

- [ ] Re-run baseline RFP with enhanced entity_types (delete baseline knowledge graph directory, re-upload)
- [ ] Count new entities extracted: Target +10% increase over baseline
- [ ] Validate metadata populated: Check requirement_type, criticality_level fields in JSON
- [ ] Document gaps remaining for post-processing layer

**Week 3 Tasks**:

- [ ] Implement `post_process_knowledge_graph()` function in `src/raganything_server.py`
- [ ] Add L↔M relationship inference via semantic similarity (threshold >0.7)
- [ ] Add clause clustering algorithm (FAR/DFARS/AFFARS/NMCARS patterns)
- [ ] Add numbered annex linkage to parent sections (pattern-based prefix extraction)
- [ ] Add REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR topic matching
- [ ] Integrate post-processing into upload workflow (automatic after LightRAG extraction)

**Week 4 Tasks**:

- [ ] Validate baseline RFP improvements: Count evaluation↔instruction relationships (target ≥5)
- [ ] Measure processing time (target ≤80 seconds) and cost (target ≤$0.05)
- [ ] Test on large RFP (100+ pages, PWS in Section C)
- [ ] Test on Task Order (non-standard format, "Selection Criteria" instead of "Section M")
- [ ] Document improvements vs. baseline in validation report
- [ ] If <5 L↔M relationships after post-processing, evaluate Option B (custom LightRAG prompts)

**Critical Implementation Notes**:

1. Post-processing runs AFTER LightRAG builds knowledge graph (t=69-75s), loads existing JSON, adds relationships, saves back
2. Agency supplements to support: FAR, DFARS, AFFARS, AFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, + 20+ others
3. Baseline RFP knowledge graph: Stored in examples/ directory for validation comparison
4. Knowledge graph files: `rag_storage/kv_store_full_entities.json`, `kv_store_full_relations.json`, `graph_chunk_entity_relation.graphml`
5. Semantic-first principle: Detect entity types by CONTENT ("page limit" → SUBMISSION_INSTRUCTION), not labels ("Section L")

**Reference Documents**:

- `docs/CAPTURE_INTELLIGENCE_PATTERNS.md`: 5 pattern categories (requirement classification, criticality levels, evaluation↔instruction mapping, competitive positioning, coverage assessment)
- `examples/`: Baseline RFP knowledge graph for validation (stored in subdirectory)
- `src/raganything_server.py`: Main server file with entity_types configuration

**Command to Activate Virtual Environment** (Required before running Python):

```powershell
.venv\Scripts\Activate.ps1
```
