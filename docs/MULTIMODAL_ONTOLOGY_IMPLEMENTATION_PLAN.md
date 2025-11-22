# Multimodal Ontology Implementation Plan

**Branch 022 Extension: Applying Custom Govcon Ontology to Tables & Images**

**Date**: November 22, 2025  
**Status**: Research & Planning Phase  
**Context**: Perfect Run achieved with text-only processing (368 entities, 428 relationships, 98%+ quality)

---

## Executive Summary

Your **Perfect Run success** is based on applying a **custom Pydantic government contracting ontology** to **TEXT-ONLY** content blocks from MinerU. The critical filter (`if item.get('type') == 'text'`) in `routes.py:111` excludes 53 non-text blocks (tables and images) that contain valuable RFP intelligence.

**The Challenge**: RAG-Anything's modal processors (`ImageModalProcessor`, `TableModalProcessor`) are designed for **generic multimodal RAG** with vanilla entity extraction, NOT domain-specific ontology-driven extraction.

**The Goal**: Extend your custom ontology (18 entity types: `requirement`, `evaluation_factor`, `performance_metric`, etc.) to tables and images WITHOUT breaking the perfect run baseline.

---

## Current Architecture Analysis

### ✅ What Works (Text Processing)

```python
# src/server/routes.py:105-120 (Perfect Run Code)
text_chunks = []
for item in filtered_content:
    if item.get('type') == 'text':  # ONLY text blocks (421 blocks)
        content_text = item.get('text', '')
        if content_text and content_text.strip():
            text_chunks.append(content_text)

# Result: 421 text blocks → JsonExtractor → ExtractionResult(entities, relationships)
# JsonExtractor uses YOUR custom Pydantic schema (src/ontology/schema.py)
```

**Key Success Factors**:

1. **Custom Pydantic Schema**: `ExtractionResult`, `Requirement`, `PerformanceMetric`, etc.
2. **Domain-Specific Prompts**: 284K chars of government contracting expertise
3. **Grok-4-fast-reasoning**: Native Pydantic structured outputs
4. **LightRAG Chunking**: 8192 tokens with 1200 overlap (4 chunks)

### ❌ What's Missing (Multimodal Processing)

RAG-Anything's modal processors are **generic**:

```python
# raganything/modalprocessors.py (RAG-Anything Library)
class TableModalProcessor(BaseModalProcessor):
    async def process_multimodal_content(self, modal_content, ...):
        # Generic table analysis - NO custom ontology
        response = await self.modal_caption_func(
            PROMPTS["table_prompt"],  # Generic prompt
            system_prompt=PROMPTS["TABLE_ANALYSIS_SYSTEM"]  # Generic system
        )
        # Returns: generic description + entity_info (name, type, summary)
        # Does NOT use Pydantic schema or government contracting rules
```

**The Gap**:

- Modal processors generate **descriptions**, not **structured entities**
- No awareness of `Requirement`, `PerformanceMetric`, `EvaluationFactor` types
- No criticality levels (MANDATORY/IMPORTANT/OPTIONAL)
- No modal verb extraction (shall/must/should)
- No workload driver capture (labor_drivers, material_needs)

---

## Research Findings: RAG-Anything Architecture

### 1. Modal Processor Design Pattern

From `raganything/raganything.py:175-220`:

```python
# RAG-Anything initializes processors per content type
if self.config.enable_table_processing:
    self.modal_processors["table"] = TableModalProcessor(
        lightrag=self.lightrag,
        modal_caption_func=self.llm_model_func,  # Generic LLM function
        context_extractor=self.context_extractor  # Surrounding text context
    )
```

**Each processor has**:

1. `generate_description_only()`: Creates natural language description
2. `process_multimodal_content()`: Generates description + creates entity + text chunk
3. `_parse_response()`: Extracts `entity_info` (name, type, summary) from LLM JSON

**Key Insight**: Processors use **generic prompts** from `raganything/prompt.py`, not custom domain prompts.

### 2. The Two-Stage Processing Flow

```
Stage 1: Description Generation (Modal Processor)
├─ Input: Raw table/image data + surrounding context
├─ Process: LLM analysis with generic prompts
└─ Output: Enhanced description (string)

Stage 2: Entity Creation (LightRAG)
├─ Input: Enhanced description from Stage 1
├─ Process: extract_entities() with LightRAG prompts
└─ Output: Generic entities + relationships
```

**Your Custom Ontology ONLY Exists in Text Processing**:

- Text blocks → `JsonExtractor` → Pydantic schema validation ✅
- Tables/Images → `ModalProcessor` → Generic entity creation ❌

### 3. Critical Discovery: Context Extraction

From `raganything/modalprocessors.py:61-360`:

```python
class ContextExtractor:
    """Universal context extractor supporting MinerU content format"""

    def extract_context(self, item_info: Dict[str, Any]) -> str:
        """Extract surrounding text for a multimodal item"""
        page_idx = item_info.get("page_idx", 0)
        item_index = item_info.get("index", 0)

        # Get text blocks BEFORE and AFTER the table/image
        before_items = [...]  # context_window blocks before
        after_items = [...]   # context_window blocks after

        return combined_context  # String with surrounding text
```

**This is GOLD for Government Contracting**:

- Tables often appear after requirement text (e.g., "Table 1 shows performance thresholds")
- Images reference section numbers (e.g., "Figure 3-1: Network Architecture")
- Context provides **semantic grounding** for entity classification

---

## Implementation Strategy

### Option A: Custom Modal Processors (RECOMMENDED)

**Create govcon-specific processors that inherit from RAG-Anything base classes**.

#### Advantages ✅

1. **Full control** over entity extraction logic
2. **Reuse your existing Pydantic schema** (`src/ontology/schema.py`)
3. **Inject your 284K custom prompts** directly into modal processing
4. **Leverage context extraction** from RAG-Anything
5. **Minimal changes** to perfect run baseline (text processing untouched)

#### Architecture

```python
# src/extraction/govcon_modal_processors.py (NEW FILE)

from raganything.modalprocessors import BaseModalProcessor, TableModalProcessor
from src.ontology.schema import ExtractionResult, Requirement, PerformanceMetric
from src.extraction.json_extractor import JsonExtractor  # Reuse your extractor!

class GovconTableProcessor(BaseModalProcessor):
    """Government contracting table processor with ontology awareness"""

    def __init__(self, lightrag, modal_caption_func, context_extractor, json_extractor):
        super().__init__(lightrag, modal_caption_func, context_extractor)
        self.json_extractor = json_extractor  # YOUR custom extractor

    async def generate_description_only(self, modal_content, content_type, item_info, entity_name):
        """
        Stage 1: Convert table to rich text description using GOVCON prompts
        """
        # Extract table structure
        table_body = modal_content.get("table_body", "")
        table_caption = modal_content.get("table_caption", [])

        # Get surrounding context (CRITICAL for entity classification)
        context = ""
        if item_info:
            context = self._get_context_for_item(item_info)

        # Build govcon-specific prompt (use YOUR 284K prompts)
        prompt = f"""
        You are analyzing a TABLE from a government RFP document.

        CONTEXT (text before/after table):
        {context[:2000]}

        TABLE CAPTION: {table_caption}
        TABLE DATA:
        {table_body}

        TASK: Convert this table to a structured text representation that can be parsed
        by government contracting entity extraction. Focus on:
        - Requirements (look for shall/must/will/should modal verbs)
        - Performance metrics (thresholds, measurements)
        - Evaluation factors (weights, subfactors)
        - Workload drivers (volumes, frequencies, quantities)

        Output ONLY the structured text representation, no JSON.
        """

        # Call LLM to generate description
        description = await self.modal_caption_func(
            prompt,
            system_prompt=self.json_extractor.system_prompt  # YOUR system prompt!
        )

        # Return description (will be processed by JsonExtractor in Stage 2)
        entity_info = {"entity_name": entity_name or "Table Content", "entity_type": "document"}
        return description, entity_info

    async def process_multimodal_content(self, modal_content, content_type, file_path, ...):
        """
        Stage 2: Extract ontology entities from description using YOUR Pydantic schema
        """
        # Generate description (Stage 1)
        description, entity_info = await self.generate_description_only(
            modal_content, content_type, item_info, entity_name
        )

        # Extract entities using YOUR JsonExtractor (same as text processing!)
        extraction_result = await self.json_extractor.extract_from_text(
            text=description,
            chunk_id=f"table-{item_info.get('page_idx', 0)}-{item_info.get('index', 0)}"
        )

        # Return entities + description for LightRAG storage
        return extraction_result, description


class GovconImageProcessor(BaseModalProcessor):
    """Government contracting image processor (diagrams, charts, architecture)"""

    async def generate_description_only(self, modal_content, content_type, item_info, entity_name):
        """
        Stage 1: Analyze image using vision model + GOVCON context
        """
        image_path = modal_content.get("img_path", "")
        image_caption = modal_content.get("image_caption", [])

        # Get surrounding context
        context = ""
        if item_info:
            context = self._get_context_for_item(item_info)

        # Encode image to base64 (required for vision models)
        image_base64 = self._encode_image_to_base64(image_path)

        # Build govcon-specific vision prompt
        vision_prompt = f"""
        Analyze this IMAGE from a government RFP document.

        CONTEXT (text before/after image):
        {context[:2000]}

        IMAGE CAPTION: {image_caption}

        TASK: Describe this image focusing on government contracting elements:
        - Technical requirements (equipment specs, performance criteria)
        - Organizational structures (org charts, reporting relationships)
        - Evaluation criteria (scoring rubrics, factor weights)
        - Deliverable examples (reports, diagrams, templates)
        - Performance metrics (charts, graphs showing thresholds)

        Output a detailed description that can be parsed for entities.
        """

        # Call vision model (Grok has vision capabilities)
        response = await self.modal_caption_func(
            vision_prompt,
            image_data=image_base64,
            system_prompt="You are analyzing government contracting RFP documents for entity extraction."
        )

        entity_info = {"entity_name": entity_name or "Image Content", "entity_type": "document"}
        return response, entity_info

    async def process_multimodal_content(self, modal_content, content_type, file_path, ...):
        # Same pattern as tables - generate description, then extract entities
        description, entity_info = await self.generate_description_only(...)
        extraction_result = await self.json_extractor.extract_from_text(description, chunk_id)
        return extraction_result, description
```

#### Integration Points

**1. Modify `src/server/routes.py` to use custom processors**

```python
# BEFORE (text-only filter)
for item in filtered_content:
    if item.get('type') == 'text':  # ONLY 421 text blocks
        text_chunks.append(item.get('text', ''))

# AFTER (multimodal processing)
from src.extraction.govcon_modal_processors import GovconTableProcessor, GovconImageProcessor

# Initialize custom processors
json_extractor = JsonExtractor()
table_processor = GovconTableProcessor(
    lightrag=None,  # Not using LightRAG storage directly
    modal_caption_func=llm_func,
    context_extractor=None,  # Create if needed
    json_extractor=json_extractor
)
image_processor = GovconImageProcessor(...)

# Process ALL content types
all_entities = []
all_relationships = []

for item in filtered_content:
    if item.get('type') == 'text':
        # Existing text processing (UNCHANGED - preserve perfect run)
        text_chunks.append(item.get('text', ''))

    elif item.get('type') == 'table':
        # NEW: Table processing with ontology
        item_info = {
            "page_idx": item.get("page_idx", 0),
            "index": filtered_content.index(item),
            "type": "table"
        }
        extraction_result, description = await table_processor.process_multimodal_content(
            modal_content=item,
            content_type="table",
            file_path=file_path,
            item_info=item_info
        )
        all_entities.extend(extraction_result.entities)
        all_relationships.extend(extraction_result.relationships)

    elif item.get('type') == 'image':
        # NEW: Image processing with ontology
        item_info = {...}
        extraction_result, description = await image_processor.process_multimodal_content(...)
        all_entities.extend(extraction_result.entities)
        all_relationships.extend(extraction_result.relationships)

# After processing all types, store in Neo4j (existing code works)
```

**2. Extend `JsonExtractor` to support standalone text input**

```python
# src/extraction/json_extractor.py (MODIFY)

class JsonExtractor:
    async def extract_from_text(self, text: str, chunk_id: str) -> ExtractionResult:
        """
        Extract entities from arbitrary text using govcon ontology.
        Used by modal processors to analyze table/image descriptions.
        """
        prompt = f"""
        You are extracting entities from government contracting RFP content.
        This text was generated from a table or image analysis.

        TEXT:
        {text}

        Extract all relevant entities following the government contracting ontology.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content

        # Parse and validate (existing code)
        data = json.loads(content)
        result = ExtractionResult(**data)
        return result
```

---

### Option B: Post-Processing Enhancement (FALLBACK)

If custom processors prove too complex, use RAG-Anything's vanilla processors and enhance the output.

#### Approach

```python
# Let RAG-Anything process tables/images generically
table_description = await TableModalProcessor().generate_description_only(...)

# Then run YOUR ontology extraction on the description
extraction_result = await json_extractor.extract_from_text(table_description, chunk_id)

# Store entities with provenance marker
for entity in extraction_result.entities:
    entity.source_text = f"[TABLE] {entity.source_text}"
```

**Disadvantages**:

- Less control over prompt engineering
- Two-pass processing (slower)
- Harder to leverage context extraction

---

## Expected Results

### Baseline (Current Perfect Run)

- **Text-only**: 421 blocks → 368 entities, 428 relationships
- **Quality**: 98%+ workload query accuracy
- **Error Rate**: 1.0%

### With Multimodal Ontology Processing

- **Text**: 421 blocks → 368 entities (UNCHANGED)
- **Tables**: ~30 blocks → estimated 40-60 entities (performance metrics, evaluation factors)
- **Images**: ~23 blocks → estimated 15-30 entities (technical requirements, deliverables)
- **Total**: 474 blocks → **420-460 entities** (+14-25%)
- **Relationships**: +50-100 additional (table↔requirement, image↔deliverable)

**Key Metrics to Preserve**:

- ✅ Workload query quality (98%+)
- ✅ Error rate (<2%)
- ✅ Entity correction count (0)
- ✅ Processing speed (<35 min)

---

## Implementation Phases

### Phase 1: Proof of Concept (1-2 days)

1. Create `src/extraction/govcon_modal_processors.py` with `GovconTableProcessor`
2. Modify `JsonExtractor.extract_from_text()` to accept arbitrary input
3. Test on **5-10 tables** from Navy RFP
4. Validate entity extraction quality vs. manual review

**Success Criteria**:

- Extract ≥80% of table entities correctly classified
- No degradation in text processing quality
- Pydantic validation passes for all table entities

### Phase 2: Full Table Integration (2-3 days)

1. Integrate `GovconTableProcessor` into `routes.py`
2. Process all 30 table blocks
3. Run full workload query validation
4. Compare Neo4j graph before/after

**Success Criteria**:

- Total entities: 420-460 (vs. 368 baseline)
- Workload query: ≥95% accuracy
- No ghost relationships (all validate against Pydantic schema)

### Phase 3: Image Processing (3-4 days)

1. Implement `GovconImageProcessor` with vision model support
2. Test on organizational charts, architecture diagrams
3. Validate entity extraction from images

**Success Criteria**:

- Extract technical requirements from diagrams
- Identify deliverable examples from image templates
- Entity types correctly classified (equipment, technical, etc.)

### Phase 4: Production Baseline (1 day)

1. Create comprehensive test suite
2. Document new perfect run metrics
3. Update `.env.perfect_run_backup` with multimodal config
4. Lock in multimodal ontology processing as new baseline

---

## Risk Mitigation

### Risk 1: Modal Processors Break Text Processing

**Mitigation**: Keep text processing code path COMPLETELY SEPARATE. Use `if type == 'text'` branch unchanged.

### Risk 2: LLM Can't Extract Entities from Descriptions

**Mitigation**: Test with sample table descriptions first. Grok-4 has shown strong structured output capabilities.

### Risk 3: Context Window Overflow

**Mitigation**: Truncate context to 2000 chars (similar to compressed prompts). Focus on immediate surrounding text.

### Risk 4: Increased Cost/Processing Time

**Mitigation** (REVISED - Based on actual xAI pricing):

- **grok-4-fast-reasoning**: $0.20 per 1M input tokens, $0.50 per 1M output tokens
- **Current 425-page RFP cost**: ~$1.00 total (user confirmed)
- **Per-table cost estimate**: ~$0.005-0.01 per table (assuming 2K input + 500 output tokens)
- **30 tables**: ~$0.15-0.30 additional per RFP
- **Total projected cost**: $1.15-1.30 per 425-page RFP (15-30% increase)
- **Processing time**: +2-3 minutes for 30 tables (minimal impact)

---

## Alternative Approaches Considered

### ❌ Forking RAG-Anything Library

**Rejected**: Maintenance burden, breaks pip installation, violates "stay grounded" rule.

### ❌ Modifying LightRAG Extraction Prompts

**Rejected**: LightRAG uses generic entity/relationship model. Would require deep fork.

### ❌ Converting Tables to Markdown First

**Rejected**: Loses semantic structure (header rows, data types). Better to analyze as table objects.

### ✅ Creating Standalone Processors (SELECTED)

**Rationale**:

- Reuses your battle-tested JsonExtractor
- Preserves perfect run baseline
- Follows RAG-Anything's own design patterns
- Minimal dependencies on external library internals

---

## Technical Dependencies

### Python Libraries (Already Installed)

- ✅ `raganything[all]` - Base modal processor classes
- ✅ `pydantic` - Schema validation
- ✅ `openai` - LLM client (xAI compatible)
- ✅ `lightrag-hku` - Text chunking utilities

### New Requirements

- None! All dependencies already satisfied.

### Configuration Changes

```bash
# .env additions for multimodal processing
ENABLE_TABLE_ONTOLOGY=true   # Enable govcon table processing
ENABLE_IMAGE_ONTOLOGY=true   # Enable govcon image processing
TABLE_CONTEXT_WINDOW=5       # Blocks before/after table to include
IMAGE_CONTEXT_WINDOW=3       # Blocks before/after image to include
```

---

## Code Examples

### Minimal Working Example

```python
# test_table_processor.py
import asyncio
from src.extraction.govcon_modal_processors import GovconTableProcessor
from src.extraction.json_extractor import JsonExtractor

async def test_table_extraction():
    # Sample table from Navy RFP
    table_content = {
        "table_body": """
        | Performance Metric | Threshold | Measurement |
        |--------------------|-----------|-------------|
        | Response Time      | < 2 hours | Avg monthly |
        | Customer Satisfaction | ≥ 95% | Survey score |
        """,
        "table_caption": ["Table 3-1: Service Level Requirements"],
        "page_idx": 42
    }

    # Initialize processor
    json_extractor = JsonExtractor()
    processor = GovconTableProcessor(
        lightrag=None,
        modal_caption_func=json_extractor.client.chat.completions.create,
        context_extractor=None,
        json_extractor=json_extractor
    )

    # Process table
    extraction_result, description = await processor.process_multimodal_content(
        modal_content=table_content,
        content_type="table",
        file_path="navy_rfp.pdf",
        item_info={"page_idx": 42, "index": 15, "type": "table"}
    )

    # Validate results
    print(f"Entities: {len(extraction_result.entities)}")
    for entity in extraction_result.entities:
        if entity.entity_type == "performance_metric":
            print(f"  - {entity.entity_name}: {entity.threshold}")

if __name__ == "__main__":
    asyncio.run(test_table_extraction())
```

---

## Next Steps

1. **Review this plan** with user to confirm approach
2. **Create branch** `023-multimodal-ontology-processing` from `022-ontology-split-performance-metric`
3. **Implement Phase 1** (Proof of Concept with tables)
4. **Validate** against perfect run baseline
5. **Iterate** based on results

---

## Questions Answered (Nov 22, 2025)

1. ✅ **Cost Estimates**: User confirmed 425-page docs cost ~$1, making my original estimates way off. Revised to $0.15-0.30 additional for tables.
2. ✅ **Vision Model Access**: xAI Grok-4 and Grok-4.1 support multimodal (text + images) via base64 encoding. User confirms previous multimodal usage.
3. ✅ **Priority**: **Tables first** - most important and frequently seen. Images later after table success.
4. ✅ **Testing**: Continue with ISS PWS only. Full RFP (Word/Excel/PDF) testing after table success.
5. ✅ **Branch Isolation**: Created `022a-table-ontology-processing` subbranch to protect perfect run baseline.

---

## Revised Cost Analysis (Accurate Pricing)

### xAI Grok Pricing (Nov 2025)

- **grok-4-fast-reasoning**: $0.20/1M input, $0.50/1M output
- **User's actual cost**: $1.00 per 425-page RFP (confirmed)

### Table Processing Cost Breakdown

**Per Table Estimate**:

- Input: ~2,000 tokens (table data + context + system prompt)
- Output: ~500 tokens (entity extraction JSON)
- Cost: (2K × $0.20 + 500 × $0.50) / 1M = **$0.0006 per table**

**30 Tables in ISS PWS**:

- Total cost: 30 × $0.0006 = **$0.018** (~$0.02)
- **Total RFP cost**: $1.00 + $0.02 = **$1.02** (2% increase, not 800%!)

**My original estimates were wrong by 400x** - you were absolutely right. The actual additional cost is negligible.

---

**STATUS**: Implementation in progress on branch `022a-table-ontology-processing`.
