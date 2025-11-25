# Branch 022b: Proper Multimodal Ontology Integration Plan

## Executive Summary

Branch 022b will properly integrate government contracting ontology with RAG-Anything's multimodal pipeline by creating a **single custom processor** that extends `BaseModalProcessor`. This approach leverages MinerU's vision capabilities (which already textualize all content) and applies our domain-specific entity extraction to both text and multimodal chunks before they merge into the unified knowledge graph.

## Background: The Architecture Discovery

### MinerU's Role (Vision Model - Runs Once)

- **Repository**: https://github.com/opendatalab/MinerU
- **Function**: Multimodal PDF parser with vision models
- **Key Insight**: MinerU IS the vision model - it converts everything to text during parsing
- **Output Format**:

```json
[
  {"type": "text", "text": "paragraph content...", "page_idx": 1},
  {"type": "table", "table_body": "<html>...</html>", "table_caption": [...], "page_idx": 2},
  {"type": "image", "text": "OCR extracted text", "image_caption": [...], "page_idx": 3}
]
```

### RAG-Anything's Role (Orchestration Layer)

- **Repository**: https://github.com/HKUDS/RAG-Anything
- **Function**: Coordinates MinerU parsing + LightRAG knowledge graph construction
- **Key Components**:
  - `parse_document()`: Calls MinerU, caches results
  - `separate_content()`: Splits text vs multimodal items
  - Modal Processors: Process multimodal items with LLM analysis
  - Native merging: Combines text + multimodal entities into unified graph

### LightRAG's Role (Knowledge Graph Engine)

- **Repository**: https://github.com/HKUDS/LightRAG
- **Function**: Entity extraction, relationship inference, vector indexing
- **Key Methods**:
  - `ainsert()`: Insert text with custom extraction prompts (our ontology)
  - `merge_nodes_and_edges()`: Merge text + multimodal entities
  - Knowledge graph storage (NetworkX or Neo4j)

## The Problem with Branch 022a

Branch 022a **bypassed RAG-Anything's pipeline entirely**:

- ❌ Manually extracted table entities outside RAG-Anything
- ❌ Created synthetic chunks as a workaround
- ❌ Custom merging logic duplicating RAG-Anything's functionality
- ❌ Missed automatic context extraction, chunk management, and proper provenance

**Root Cause**: We didn't understand that RAG-Anything's `TableModalProcessor` and `ImageModalProcessor` are **extension points**, not hard-coded behaviors.

## The Correct Solution: Branch 022b

### Core Principle

**Extend RAG-Anything, don't bypass it.**

Create ONE custom processor that:

1. Extends `BaseModalProcessor` (RAG-Anything's abstract class)
2. Overrides `generate_description_only()` to apply govcon ontology
3. Lets RAG-Anything handle chunking, storage, indexing, and merging
4. Works for ALL multimodal types (tables, images, equations)

### The Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MinerU Parsing (Vision Model - ONCE)                    │
│    PDF → content_list (all content textualized)            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. RAG-Anything Separation                                  │
│    content_list → text_content + multimodal_items          │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
┌───────────────────────┐     ┌─────────────────────────────┐
│ 3a. TEXT CHUNKING     │     │ 3b. MULTIMODAL CHUNKING     │
│ (LightRAG native)     │     │ (Custom Processor)          │
│                       │     │                             │
│ Uses OUR custom       │     │ GovconMultimodalProcessor   │
│ extraction prompts ✅ │     │ .generate_description_only()│
│                       │     │                             │
│ Extracts:             │     │ Extracts:                   │
│ - Requirements        │     │ - Requirements              │
│ - Metrics             │     │ - Metrics                   │
│ - Deliverables        │     │ - Deliverables              │
│ - Resources           │     │ - Resources                 │
└───────────────────────┘     │                             │
                              │ Uses SAME JsonExtractor ✅  │
                              └─────────────────────────────┘
        │                                   │
        └─────────────────┬─────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. AUTOMATIC MERGING (RAG-Anything native)                  │
│    Text entities + Multimodal entities → Knowledge Graph    │
│    - Vector indexing                                        │
│    - Chunk storage with provenance                          │
│    - Relationship inference                                 │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### File Structure

```
src/
  processors/
    __init__.py                      ← NEW: Package initialization
    govcon_multimodal_processor.py   ← NEW: Single unified processor

  extraction/
    json_extractor.py                ← EXISTING: Ontology-aware extraction

  server/
    routes.py                        ← MODIFY: Register custom processor
```

### Core Implementation: GovconMultimodalProcessor

```python
# src/processors/govcon_multimodal_processor.py

from typing import Dict, Any, Tuple
from raganything.modalprocessors import BaseModalProcessor
from src.extraction.json_extractor import JsonExtractor
from lightrag.utils import logger

class GovconMultimodalProcessor(BaseModalProcessor):
    """
    Extends RAG-Anything's BaseModalProcessor to apply government
    contracting ontology to multimodal content from MinerU.

    Handles: tables (HTML), images (OCR text), equations (LaTeX)
    All content is already textualized by MinerU's vision models.

    Key Architecture Decision:
    - MinerU = Vision model (runs once, outputs text)
    - This processor = Text analysis with domain ontology
    - No separate vision model needed at extraction time
    """

    def __init__(self, lightrag, modal_caption_func, context_extractor):
        """
        Initialize with RAG-Anything's standard components.

        Args:
            lightrag: LightRAG instance for storage/indexing
            modal_caption_func: LLM function (Grok-4 for text analysis)
            context_extractor: RAG-Anything's context extraction utility
        """
        super().__init__(lightrag, modal_caption_func, context_extractor)
        self.json_extractor = JsonExtractor()
        logger.info("🏛️ GovconMultimodalProcessor initialized with ontology awareness")

    async def generate_description_only(
        self,
        modal_content: Dict[str, Any],
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        OVERRIDE: Apply govcon ontology instead of generic description.

        This is the ONLY method we override - RAG-Anything handles:
        - Chunk creation
        - Entity storage
        - Vector indexing
        - Graph merging

        Args:
            modal_content: MinerU output (textualized content)
            content_type: "table", "image", "equation"
            item_info: Page/index info for context extraction
            entity_name: Optional predefined entity name

        Returns:
            (description, entity_info) for RAG-Anything's pipeline
        """

        # Extract textualized content (MinerU already did vision work)
        text_content, caption = self._extract_text_content(
            modal_content, content_type
        )

        # Get document context (RAG-Anything's context extractor)
        doc_context = ""
        if item_info and self.context_extractor:
            doc_context = self._get_context_for_item(item_info)

        # Build ontology-aware prompt
        ontology_prompt = self._build_ontology_prompt(
            doc_context, caption, text_content, content_type
        )

        # Extract govcon entities using our JsonExtractor
        extraction_result = await self.json_extractor.extract_from_text(
            ontology_prompt,
            source_context=content_type
        )

        # Format for RAG-Anything's pipeline
        description, entity_info = self._format_for_raganything(
            extraction_result,
            entity_name,
            content_type,
            modal_content
        )

        logger.info(
            f"✅ Extracted {len(extraction_result.entities)} govcon entities "
            f"from {content_type}"
        )

        return description, entity_info

    def _extract_text_content(
        self, modal_content: Dict[str, Any], content_type: str
    ) -> Tuple[str, str]:
        """Extract textualized content from MinerU output."""

        if content_type == "table":
            # MinerU already converted table to HTML text
            text_content = modal_content.get("table_body", "")
            caption = ", ".join(modal_content.get("table_caption", []))

        elif content_type == "image":
            # MinerU already OCR'd the image
            text_content = modal_content.get("text", "")
            caption = ", ".join(modal_content.get("image_caption", []))

        elif content_type == "equation":
            # MinerU already extracted LaTeX
            text_content = modal_content.get("latex", "")
            caption = modal_content.get("equation_caption", "")

        else:
            text_content = str(modal_content)
            caption = ""

        return text_content, caption

    def _build_ontology_prompt(
        self,
        doc_context: str,
        caption: str,
        text_content: str,
        content_type: str
    ) -> str:
        """Build ontology-aware prompt for entity extraction."""

        context_section = f"Document Context:\n{doc_context}\n\n" if doc_context else ""
        caption_section = f"{content_type.title()}: {caption}\n\n" if caption else ""

        return f"""
{context_section}{caption_section}Content:
{text_content}

Extract government contracting entities from this {content_type}:

1. REQUIREMENTS - Compliance criteria, specifications, constraints
   - Include frequencies, standards, completion criteria
   - Tag with requirement type (performance, technical, delivery)

2. METRICS - Quantifiable measures for estimation
   - Quantities (counts, volumes, capacities)
   - Frequencies (daily, weekly, monthly, yearly)
   - Coverage (hours, days, locations)
   - Thresholds (minimums, maximums, ranges)

3. DELIVERABLES - Work outputs, reports, schedules
   - Document types and formats
   - Submission frequencies and deadlines
   - Review/approval processes

4. RESOURCES - Equipment, personnel, facilities, materials
   - Specific models/types
   - Quantities required
   - Qualifications/certifications

5. RELATIONSHIPS - How entities connect
   - Requirements ↔ Metrics (compliance measurement)
   - Deliverables ↔ Requirements (evidence of compliance)
   - Resources ↔ Requirements (capability enablers)

Focus on workload drivers and basis of estimate elements.
"""

    def _format_for_raganything(
        self,
        extraction_result,
        entity_name: str,
        content_type: str,
        modal_content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Format extraction results for RAG-Anything's pipeline."""

        # Create description from extracted entities
        entity_summaries = []
        for entity in extraction_result.entities:
            entity_summaries.append(
                f"{entity.entity_type}: {entity.entity_name} - {entity.description}"
            )

        description = "\n".join(entity_summaries) if entity_summaries else f"No govcon entities found in {content_type}"

        # Create entity_info compatible with RAG-Anything
        page_idx = modal_content.get("page_idx", 0)
        entity_info = {
            "entity_name": entity_name or f"govcon_{content_type}_p{page_idx}",
            "entity_type": f"govcon_{content_type}",
            "summary": description,
            # Preserve our extraction results for downstream use
            "govcon_entities": [
                {
                    "name": e.entity_name,
                    "type": e.entity_type,
                    "description": e.description
                } for e in extraction_result.entities
            ],
            "govcon_relationships": [
                {
                    "source": r.source_entity,
                    "target": r.target_entity,
                    "type": r.relationship_type,
                    "description": r.description
                } for r in extraction_result.relationships
            ]
        }

        return description, entity_info
```

### Integration Point: routes.py

```python
# src/server/routes.py (key sections)

from raganything import RAGAnything, RAGAnythingConfig
from src.processors.govcon_multimodal_processor import GovconMultimodalProcessor

async def process_document_endpoint(file_path: str):
    """
    Process document using RAG-Anything with custom govcon ontology.

    Flow:
    1. RAG-Anything calls MinerU (vision model extracts text)
    2. Text chunks processed with LightRAG (our custom prompts)
    3. Multimodal chunks processed with GovconMultimodalProcessor (our ontology)
    4. RAG-Anything merges everything into unified knowledge graph
    """

    # Initialize RAG-Anything with standard configuration
    config = RAGAnythingConfig(
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
        content_format="mineru"  # Use MinerU parser
    )

    rag = RAGAnything(
        config=config,
        llm_model_func=llm_func,      # Grok-4 for text analysis
        embedding_func=embed_func,
        working_dir=global_args.working_dir
    )

    # Register OUR custom processor for ALL multimodal types
    govcon_processor = GovconMultimodalProcessor(
        lightrag=rag.lightrag,
        modal_caption_func=llm_func,  # Same Grok-4 (MinerU already textualized)
        context_extractor=rag.context_extractor
    )

    # Override default processors with our ontology-aware processor
    rag.modal_processors["table"] = govcon_processor
    rag.modal_processors["image"] = govcon_processor
    rag.modal_processors["equation"] = govcon_processor

    logger.info("🏛️ Custom govcon processors registered")

    # Process document - RAG-Anything handles everything!
    # - Calls MinerU for parsing
    # - Processes text with our prompts
    # - Processes multimodal with our processor
    # - Merges into knowledge graph
    # - Stores in Neo4j
    await rag.process_document_complete(file_path=file_path)

    logger.info("✅ Document processing complete with govcon ontology")
```

## Changes from Branch 022a

### Files to REMOVE

- ❌ `src/extraction/govcon_table_processor.py` - Replaced by unified processor
- ❌ Synthetic chunk creation logic in `routes.py`
- ❌ Manual entity merging logic in `routes.py`
- ❌ Custom table bypass in `routes.py`

### Files to ADD

- ✅ `src/processors/__init__.py`
- ✅ `src/processors/govcon_multimodal_processor.py`

### Files to MODIFY

- 🔧 `src/server/routes.py` - Simplified to use RAG-Anything properly
- 🔧 `src/extraction/json_extractor.py` - Ensure compatible with async calls

## Expected Results

### Processing Output

```
📄 Processing: Atch 1 ADAB ISS PWS_4 April 25.pdf
🔍 MinerU parsing: 70 pages
  - 45 tables detected
  - 12 images detected
  - Vision models extracting text...

📝 Text chunking: 4 chunks
  ✅ Extracted 24 govcon entities from text

📊 Multimodal chunking: 57 items
  ✅ Extracted 489 govcon entities from tables
  ✅ Extracted 15 govcon entities from images

🔗 Merging: 528 total entities, 463 relationships
  ✅ Inserted into Neo4j knowledge graph

⏱️ Total time: 45 seconds (417x faster than local processing)
```

### Appendix H Query Results

**Query**: "Provide complete maintenance schedules for fitness equipment including frequencies and specific tasks."

**Expected Response**:

```
Summary of Appendix H: Fitness Equipment Maintenance

Maintenance Requirements by Frequency:

WEEKLY Tasks (15 requirements):
- Requirement: Visually inspect all machines (Metric: Weekly frequency)
- Requirement: Clean machine housing (Metric: Weekly frequency)
- Requirement: Inspect mechanical parts (Metric: Weekly frequency)
- Requirement: Clean bed and frame with damp cloth on treadmills (Metric: Weekly)
- Requirement: Clean housing and inspect screws on treadmills (Metric: Weekly)
- Requirement: Inspect belt alignment on treadmills (Metric: Weekly)
- Requirement: Clean housing on stationary cycles (Metric: Weekly)
- Requirement: Clean seat with protectant spray on cycles (Metric: Weekly)
...

MONTHLY Tasks (8 requirements):
- Requirement: Clean & lubricate pedals/shaft with 30W oil (Metric: Monthly)
- Requirement: Clean and lubricate seat post (Metric: Monthly)
- Requirement: Inspect belt brushings on treadmills (Metric: Monthly)
- Requirement: Add axle grease to step axle on stair climbers (Metric: Monthly)
...

QUARTERLY Tasks (5 requirements):
- Requirement: Lubricate bed on treadmills (Metric: Quarterly)
- Requirement: Clean & lubricate chain with 30W oil (Metric: Quarterly)
- Requirement: Stay current with maintenance updates (Metric: Quarterly)
...

YEARLY Tasks (3 requirements):
- Requirement: Lubricate all moving parts semiannually (Metric: 2x/year)
- Requirement: Conduct in-house preventive maintenance training (Metric: Yearly)
- Requirement: Inspect belt alignment on treadmills (Metric: Yearly)

Equipment Categories (from Table H.1):
- General Equipment (7 tasks)
- Treadmills (6 tasks)
- Stationary Cycles (9 tasks)
- Stair Climbing Machines (5 tasks)
- Chin Up/Dip Machines (1 task)
- Free Weight Equipment (6 tasks)
- Strength Machines (3 tasks)

Workload Drivers:
- Total maintenance events: 37 unique tasks × frequencies ≈ 500+ events/year
- Task distribution: 40% Weekly, 22% Monthly, 14% Quarterly, 8% Yearly
- Requires certified preventive maintenance personnel per DAFI 34-101
```

## Validation Checklist

- [ ] MinerU parses document once (vision models extract all text)
- [ ] Text chunks processed with govcon ontology (Requirements, Metrics, etc.)
- [ ] Table chunks processed with govcon ontology (same entity types)
- [ ] Image chunks processed with govcon ontology (same entity types)
- [ ] All entities merged into unified Neo4j knowledge graph
- [ ] Query results include detailed workload drivers from tables
- [ ] Provenance tracking works (can identify table vs text sources)
- [ ] No synthetic chunk workarounds needed
- [ ] Processing time similar to branch 022a (~45 seconds)
- [ ] Code is clean extension of RAG-Anything (no bypasses)

## Key Repositories

1. **MinerU** (Vision Model): https://github.com/opendatalab/MinerU

   - Multimodal PDF parsing
   - Vision models for table/image text extraction
   - Outputs textualized `content_list`

2. **RAG-Anything** (Orchestration): https://github.com/HKUDS/RAG-Anything

   - Coordinates MinerU + LightRAG
   - Modal processors (extension points for our ontology)
   - Automatic chunking and merging

3. **LightRAG** (Knowledge Graph): https://github.com/HKUDS/LightRAG
   - Entity extraction with custom prompts
   - Relationship inference
   - Neo4j integration

## Environment Configuration (.env)

The system requires proper configuration in `.env` for cloud-based processing with xAI Grok and OpenAI embeddings. **Key variables that affect multimodal processing**:

```bash
# xAI Grok LLM (OpenAI-compatible API)
# LOCKED: grok-4-fast-reasoning - PROVEN perfect run configuration
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4-fast-reasoning
EXTRACTION_LLM_NAME=grok-4-fast-reasoning
REASONING_LLM_NAME=grok-4-fast-reasoning
LLM_MODEL_TEMPERATURE=0.1

# OpenAI Embeddings (CRITICAL: Use OpenAI endpoint, NOT xAI!)
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072

# Cloud-Optimized Chunking (Branch 005)
# CRITICAL: 8K chunks = multiple focused extraction passes
# 50K chunks caused catastrophic failure (63 entities vs 400-600 expected)
CHUNK_SIZE=8192
CHUNK_OVERLAP_SIZE=1200

# Maximum Concurrency
MAX_ASYNC=32
EMBEDDING_FUNC_MAX_ASYNC=32

# Compressed Prompts (Branch 022a - 73% token reduction)
USE_COMPRESSED_PROMPTS=true

# MinerU Multimodal Configuration
PARSER=mineru
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=true

# Table Ontology Processing (Branch 022a+)
# ENABLED: Apply govcon ontology to tables
ENABLE_TABLE_ONTOLOGY=true

# MinerU Advanced Settings (Optimized for Government Contracting)
MINERU_FORMULA_ENABLE=1            # Improved numeric extraction
MINERU_TABLE_MERGE_ENABLE=1        # Cross-page table continuation
MINERU_PDF_RENDER_TIMEOUT=600      # 10 minutes for complex diagrams
MINERU_DEVICE_MODE=cuda            # Force GPU (RTX 4060)

# Neo4j Graph Database (Branch 010+ Enterprise)
GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=govcon-capture-2025
NEO4J_DATABASE=neo4j

# Workspace Isolation
WORKSPACE=afcapv_adab_iss_2025_pwstst_4mod
NEO4J_WORKSPACE=afcapv_adab_iss_2025_pwstst_4mod
```

**Key Configuration Notes**:

1. **LLM Model**: `grok-4-fast-reasoning` is LOCKED as proven configuration

   - Baseline: 368 entities, 154 relationships
   - MinerU already textualized content, so regular LLM works for all types

2. **Chunking**: 8192 tokens is critical for comprehensive extraction

   - 50K chunks = 1 LLM pass = catastrophic entity loss (63 vs 400+ entities)
   - 8K chunks = 5-6 focused passes = complete coverage
   - LightRAG automatically merges entities across chunks

3. **Compressed Prompts**: 73% token reduction (294K→80K chars)

   - Preserves 100% intelligence
   - Validation target: 368±13 entities, 154±8 relationships

4. **MinerU Settings**:

   - `MINERU_TABLE_MERGE_ENABLE=1`: Critical for cross-page requirement matrices
   - `MINERU_FORMULA_ENABLE=1`: Improved OCR for numeric extraction
   - `MINERU_DEVICE_MODE=cuda`: Use RTX 4060 GPU for 417x speedup

5. **Security**: Only use cloud processing for PUBLIC government RFPs

## Success Metrics

1. **Entity Extraction Quality**

   - Text entities: 24 (same as branch 022a) ✅
   - Table entities: 489 (same as branch 022a) ✅
   - Image entities: 15+ (NEW - branch 022a didn't process images)
   - Total: 528+ govcon entities

2. **Query Quality**

   - Appendix F query: Matches perfect run baseline ✅
   - Appendix H query: Rich table details (maintenance schedules) ✅
   - Cross-appendix queries: Unified knowledge graph enables ✅

3. **Code Quality**

   - Single custom processor class (~200 lines)
   - Clean extension of RAG-Anything (no bypasses)
   - Reuses existing JsonExtractor (no duplication)
   - Minimal changes to routes.py (~20 lines)

4. **Performance**
   - Processing time: ~45 seconds (same as 022a)
   - 417x faster than local processing
   - Cloud processing with xAI Grok-4

## Next Steps

1. Create branch 022b from 022-ontology-split-performance-metric parent
2. Implement `GovconMultimodalProcessor`
3. Modify `routes.py` to register custom processor
4. Remove branch 022a workarounds
5. Test with full RFP document
6. Validate Appendix H query results
7. Merge to parent branch if successful

---

**Document Version**: 1.0  
**Created**: 2025-11-23  
**Branch**: 022b-multimodal-ontology-integration  
**Parent**: 022-ontology-split-performance-metric
