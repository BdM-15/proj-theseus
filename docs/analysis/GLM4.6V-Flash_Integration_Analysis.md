# GLM-4.6V-Flash Integration Analysis

**Date**: December 11, 2025  
**Purpose**: Evaluate GLM-4.6V-Flash (free local multimodal model) as alternative to MinerU or for Agent/Skills Framework

---

## Executive Summary

**Recommendation**: **GLM-4.6V-Flash is NOT a direct MinerU replacement** but offers **complementary value** for the Agent/Skills Framework (Issue #40).

| Use Case                  | MinerU (Current)              | GLM-4.6V-Flash                        | Verdict                |
| ------------------------- | ----------------------------- | ------------------------------------- | ---------------------- |
| **PDF Structure Parsing** | ✅ Native layout analysis     | ❌ VLM-based (less reliable)          | **Keep MinerU**        |
| **Table Extraction**      | ✅ Specialized table detector | ⚠️ VLM interpretation                 | **Keep MinerU**        |
| **Agent Tool Calling**    | ❌ Not applicable             | ✅ Native multimodal function calling | **Add GLM-4.6V-Flash** |
| **Visual Reasoning**      | ❌ Not applicable             | ✅ 128K context, visual QA            | **Add GLM-4.6V-Flash** |
| **Cost**                  | ✅ Free (local)               | ✅ Free (local)                       | **Tie**                |
| **Privacy**               | ✅ 100% local                 | ✅ 100% local                         | **Tie**                |

**Strategic Fit**: Use GLM-4.6V-Flash as the **multimodal agent brain** in Issue #40's Skills Pattern, NOT as a document parser.

---

## GLM-4.6V-Flash Overview

### Key Capabilities

**Model Specs**:

- **Size**: 9B parameters (optimized for local deployment)
- **Context**: 128K tokens (matches long RFP documents)
- **Modalities**: Text + images (native multimodal reasoning)
- **License**: MIT (open-source, commercial-friendly)
- **Deployment**: HuggingFace `zai-org/GLM-4.6V-Flash`

**Unique Features**:

1. **Native Multimodal Function Calling**: Tools can return visual outputs (charts, screenshots, tables) that feed back into reasoning chain
2. **Visual Tool Integration**: Processes tool-returned images without lossy text conversion
3. **Document Understanding**: Can interpret multi-page PDFs as images (up to 128K tokens)
4. **Agentic Workflows**: Designed for perception → reasoning → execution loops

### vs. MinerU Comparison

| Dimension       | MinerU 2.6.4                           | GLM-4.6V-Flash                             |
| --------------- | -------------------------------------- | ------------------------------------------ |
| **Purpose**     | Document structure extraction          | Multimodal reasoning                       |
| **Strength**    | Layout analysis, table detection       | Visual understanding, agent workflows      |
| **Output**      | Structured JSON (text, tables, images) | Natural language + tool calls              |
| **Accuracy**    | High for tables/structure              | Variable for structure, high for reasoning |
| **Speed**       | Fast (GPU-accelerated)                 | Medium (9B model inference)                |
| **Integration** | Pipeline component (RAG-Anything)      | Agent orchestrator                         |

**MinerU excels at**: "Parse this PDF and give me structured table data"  
**GLM-4.6V-Flash excels at**: "Analyze this chart, query the database, and explain the compliance gap"

---

## Current Architecture Context

### Your System Uses MinerU Via RAG-Anything

From [src/server/initialization.py](c:\Users\benma\govcon-capture-vibe\src\server\initialization.py#L93-L112):

```python
# MinerU configuration
parser = os.getenv("PARSER", "mineru")
parse_method = os.getenv("PARSE_METHOD", "auto")
enable_image = os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true"
enable_table = os.getenv("ENABLE_TABLE_PROCESSING", "true").lower() == "true"
enable_equation = os.getenv("ENABLE_EQUATION_PROCESSING", "true").lower() == "true"
device = os.getenv("MINERU_DEVICE_MODE", "auto")  # cuda, cpu, or auto

# RAG-Anything wraps MinerU
config = RAGAnythingConfig(
    working_dir=working_dir,
    parser=parser,  # "mineru"
    parse_method=parse_method,
    enable_image_processing=enable_image,
    enable_table_processing=enable_table,
    enable_equation_processing=enable_equation,
)
```

**Processing Flow**:

```
PDF Upload
  ↓
MinerU Parser (via RAG-Anything)
  ├─ Tables → Structured JSON
  ├─ Images → Base64 + captions
  └─ Text → Paragraphs with layout
  ↓
LightRAG Chunking (8192 tokens)
  ↓
Grok-4 Entity Extraction (18 types)
  ↓
Neo4j Knowledge Graph
```

**MinerU's Role**: **Structural parsing** (converts PDF binary → structured multimodal JSON)

---

## Integration Opportunities

### Option 1: GLM-4.6V-Flash for Skills Pattern Execution (Issue #40)

**Where It Fits**: Skills orchestration layer, NOT document parsing

From [GitHub Issue #40](https://github.com/BdM-15/govcon-capture-vibe/issues/40):

```python
# Current design uses cloud Grok-4 for skill execution
async def run_skill(
    skill_name: str,
    workspace: str,
    llm_override: Optional[str] = None  # Switch LLMs here
) -> dict:
    # ...
    response = await rag.aquery(prompt, param=QueryParam(mode="hybrid"))
```

**GLM-4.6V-Flash Enhancement**:

```python
# New: Local multimodal agent for visual deliverables
from transformers import AutoTokenizer, AutoModelForCausalLM

class LocalMultimodalAgent:
    """Local GLM-4.6V-Flash agent for visual deliverable generation"""

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("zai-org/GLM-4.6V-Flash")
        self.model = AutoModelForCausalLM.from_pretrained(
            "zai-org/GLM-4.6V-Flash",
            device_map="auto",  # Local GPU/CPU
            trust_remote_code=True
        )

    async def run_visual_skill(
        self,
        skill_instructions: str,
        context_data: dict,
        visual_inputs: List[str] = None  # Paths to graphs, org charts, etc.
    ) -> dict:
        """
        Execute skill with native multimodal reasoning.

        Example: Generate compliance matrix with embedded evaluation factor charts
        """
        # Build multimodal prompt
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": skill_instructions},
                    {"type": "text", "text": json.dumps(context_data)},
                ]
            }
        ]

        # Add visual context (e.g., evaluation factor charts from Neo4j visualizations)
        if visual_inputs:
            for img_path in visual_inputs:
                with open(img_path, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode()
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                })

        # Generate with tool calling support
        response = self.model.generate(
            **self.tokenizer.apply_chat_template(messages, return_tensors="pt"),
            max_new_tokens=2048,
            do_sample=False  # Deterministic
        )

        return {"output": self.tokenizer.decode(response[0])}
```

**Use Cases for Skills Framework**:

| Skill                 | Why GLM-4.6V-Flash Helps                            |
| --------------------- | --------------------------------------------------- |
| **Kickoff Deck**      | Interpret org chart images, embed visual win themes |
| **Compliance Matrix** | Analyze Section M evaluation tables visually        |
| **Risk Register**     | Reason over Gantt charts, identify schedule risks   |
| **BOE Worksheet**     | Understand labor mix charts, validate formulas      |

**Benefits**:

- ✅ **100% local** (no cloud costs for proprietary queries)
- ✅ **Native multimodal** (charts → reasoning → output)
- ✅ **Agent-ready** (function calling for tool use)
- ✅ **Fast iteration** (no API rate limits)

**Limitations**:

- ❌ **9B parameters** (less capable than Grok-4 for complex reasoning)
- ❌ **GPU required** (needs ~18GB VRAM for inference)
- ❌ **No RAG-Anything integration** (separate from MinerU pipeline)

### Option 2: Hybrid Architecture (Best of Both Worlds)

**Strategy**: Keep MinerU for parsing, add GLM-4.6V-Flash for agents

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Processing                      │
│  MinerU → Structured Extraction → Grok-4 Entity Extraction  │
│  (Parsing accuracy critical, use cloud LLM)                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
                   Neo4j Knowledge Graph
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Skills Execution                         │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Text-Only       │        │  Visual/Complex  │          │
│  │  Skills          │        │  Skills          │          │
│  │                  │        │                  │          │
│  │  GLM-4.6V-Flash  │        │  Grok-4          │          │
│  │  (Local, Free)   │        │  (Cloud, $$)     │          │
│  └──────────────────┘        └──────────────────┘          │
│                                                             │
│  Examples:                   Examples:                      │
│  - Outline generation        - Complex risk analysis        │
│  - Simple matrices           - Multi-source synthesis       │
│  - Deliverables list         - Strategic theme generation   │
└─────────────────────────────────────────────────────────────┘
```

**Configuration** (`.env`):

```properties
# Dual LLM setup
PRIMARY_LLM=grok-4-fast-reasoning  # Cloud (extraction + complex skills)
LOCAL_LLM=GLM-4.6V-Flash           # Local (simple skills + visual)

# Skill routing (in src/capture/runner.py)
SKILL_LLM_MAPPING={
    "proposal_outline": "local",      # GLM-4.6V-Flash
    "compliance_matrix": "local",     # GLM-4.6V-Flash
    "deliverables_list": "local",     # GLM-4.6V-Flash
    "win_themes": "primary",          # Grok-4 (strategic reasoning)
    "risk_register": "primary",       # Grok-4 (complex analysis)
    "kickoff_deck": "local"           # GLM-4.6V-Flash (visual charts)
}
```

---

## Implementation Roadmap

### Phase 1: Proof of Concept (Week 1)

**Goal**: Validate GLM-4.6V-Flash on one skill (proposal outline)

1. **Install GLM-4.6V-Flash**:

   ```powershell
   pip install transformers accelerate bitsandbytes
   # Download model (9B params, ~18GB)
   python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('zai-org/GLM-4.6V-Flash')"
   ```

2. **Create Local Agent Wrapper**:

   ```python
   # src/capture/local_agent.py
   from transformers import AutoTokenizer, AutoModelForCausalLM

   class GLM4VFlashAgent:
       def __init__(self):
           self.tokenizer = AutoTokenizer.from_pretrained("zai-org/GLM-4.6V-Flash")
           self.model = AutoModelForCausalLM.from_pretrained(
               "zai-org/GLM-4.6V-Flash",
               device_map="auto",
               trust_remote_code=True
           )

       async def run_skill(self, skill_md: str, context: dict) -> str:
           # Implementation
           pass
   ```

3. **Test on Simple Skill** (`proposal_outline.md`):

   ```python
   from src.capture.local_agent import GLM4VFlashAgent
   from src.capture.context_builder import CaptureContext

   agent = GLM4VFlashAgent()
   ctx = CaptureContext("2_mcpp_drfp_2025")
   context_data = await ctx.for_proposal_outline()

   result = await agent.run_skill(
       skill_md=Path("prompts/capture_skills/proposal_outline.md").read_text(),
       context=context_data
   )
   ```

4. **Compare Output**: GLM-4.6V-Flash vs. Grok-4 for same skill

**Success Criteria**:

- ✅ Loads model locally (<60 seconds)
- ✅ Generates valid JSON output (Pydantic validation)
- ✅ Quality within 80% of Grok-4 (manual review)

### Phase 2: Skills Framework Integration (Week 2)

**Prerequisite**: Issue #40 Phase 1 complete (context builder + runner)

1. **Add LLM Router** (`src/capture/llm_router.py`):

   ```python
   from enum import Enum
   from typing import Optional

   class LLMBackend(Enum):
       GROK_4 = "grok-4-fast-reasoning"
       GLM_4V_FLASH = "GLM-4.6V-Flash"

   class SkillLLMRouter:
       """Route skills to appropriate LLM backend"""

       SKILL_MAPPINGS = {
           # Local-first skills (simple, privacy-sensitive)
           "proposal_outline": LLMBackend.GLM_4V_FLASH,
           "compliance_matrix": LLMBackend.GLM_4V_FLASH,
           "deliverables_list": LLMBackend.GLM_4V_FLASH,

           # Cloud skills (complex reasoning required)
           "win_themes": LLMBackend.GROK_4,
           "risk_register": LLMBackend.GROK_4,
       }

       def get_backend(self, skill_name: str) -> LLMBackend:
           return self.SKILL_MAPPINGS.get(skill_name, LLMBackend.GROK_4)
   ```

2. **Update Runner** ([src/capture/runner.py](c:\Users\benma\govcon-capture-vibe\docs\future_features#40)):
   ```python
   async def run_skill(
       skill_name: str,
       workspace: str,
       llm_override: Optional[str] = None
   ) -> dict:
       # Determine LLM backend
       router = SkillLLMRouter()
       backend = router.get_backend(skill_name) if not llm_override else llm_override

       # Load skill + context
       skill_instructions = (SKILLS_DIR / f"{skill_name}.md").read_text()
       ctx = CaptureContext(workspace)
       context_data = await getattr(ctx, f"for_{skill_name}")()

       # Execute with appropriate LLM
       if backend == LLMBackend.GLM_4V_FLASH:
           from src.capture.local_agent import GLM4VFlashAgent
           agent = GLM4VFlashAgent()
           response = await agent.run_skill(skill_instructions, context_data)
       else:  # GROK_4
           rag = LightRAG(working_dir=f"rag_storage/{workspace}")
           prompt = f"{skill_instructions}\n\n{json.dumps(context_data)}"
           response = await rag.aquery(prompt, param=QueryParam(mode="hybrid"))

       # Parse and export...
   ```

### Phase 3: Visual Skills (Week 3)

**Goal**: Leverage multimodal capabilities for chart-heavy deliverables

**Example: Kickoff Deck with Embedded Charts**

```python
# prompts/capture_skills/kickoff_deck_visual.md

# Kickoff Deck Generation Skill (Multimodal)

You are creating a capture kickoff presentation.

## Visual Inputs Provided:
1. Evaluation factor breakdown chart (PNG)
2. Proposal volume structure diagram (PNG)
3. Win theme concept map (PNG)

## Task
Analyze the visual inputs and generate PowerPoint slides with:
- Embedded charts (reference provided images)
- Narrative text explaining each visual
- Compliance matrix summary

## Output Format
Return JSON with slide structure and image references.
```

**Agent Execution**:

```python
async def run_visual_skill(
    skill_name: str,
    workspace: str,
    visual_inputs: List[str]  # Paths to charts from Neo4j/analytics
) -> dict:
    agent = GLM4VFlashAgent()
    skill_md = (SKILLS_DIR / f"{skill_name}.md").read_text()
    context_data = await CaptureContext(workspace).for_kickoff_deck()

    # GLM-4.6V-Flash processes images natively
    result = await agent.run_skill(
        skill_md=skill_md,
        context=context_data,
        images=visual_inputs  # Charts, org diagrams, etc.
    )

    # Export to PowerPoint with embedded images
    from src.exporters.powerpoint import create_kickoff_deck_visual
    output_path = create_kickoff_deck_visual(result, output_dir)

    return {"output_file": output_path}
```

---

## Technical Considerations

### GPU Requirements

**GLM-4.6V-Flash Memory**:

- **Full Precision (FP32)**: ~36GB VRAM
- **Half Precision (FP16)**: ~18GB VRAM
- **4-bit Quantization**: ~5GB VRAM (acceptable quality)

**Your Hardware** (assumed from MinerU GPU acceleration):

- CUDA-capable GPU (verify: `nvidia-smi`)
- Likely 8-16GB VRAM → Use 4-bit quantization

**4-bit Loading** (`src/capture/local_agent.py`):

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    "zai-org/GLM-4.6V-Flash",
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True
)
```

### Integration Risks

| Risk                            | Mitigation                                            |
| ------------------------------- | ----------------------------------------------------- |
| **Quality degradation**         | Fallback to Grok-4 if GLM output fails validation     |
| **GPU memory exhaustion**       | Offload to CPU (slower) or quantize to 4-bit          |
| **Model download delays**       | Cache model in Docker volume (`~/.cache/huggingface`) |
| **Skills framework incomplete** | GLM integration blocks on Issue #40 Phase 1           |

---

## Recommended Next Steps

### Immediate Actions

1. **Verify GPU**: `nvidia-smi` to check VRAM availability
2. **Test Model Download**:
   ```python
   from transformers import AutoModelForCausalLM
   model = AutoModelForCausalLM.from_pretrained("zai-org/GLM-4.6V-Flash")
   print(f"Model loaded: {model.config}")
   ```
3. **Create POC Branch**: `040-glm4v-flash-integration` (follows naming convention)

### Decision Tree

```
Is GPU available with >5GB VRAM?
├─ YES → Proceed with GLM-4.6V-Flash integration
│         Target: Local agent for Issue #40 skills
│
└─ NO → Options:
        1. Use cloud GLM-4.6V API (Z.ai offers paid inference)
        2. CPU-only (slower, ~10x inference time)
        3. Wait for Issue #40 to use Grok-4 only
```

### Branch Strategy

**If Implementing**:

```powershell
# Create integration branch
git checkout main
git pull origin main
git checkout -b 040-glm4v-flash-agent

# Implement in phases
# Phase 1: Model loading + POC skill
# Phase 2: Router + Issue #40 integration
# Phase 3: Visual skills

# Merge only after Issue #40 Phase 1 complete
```

---

## Conclusion

**GLM-4.6V-Flash is NOT a MinerU replacement** for document parsing but offers **strategic value** as a **local multimodal agent** for the Skills Pattern (Issue #40).

**Strengths**:

- ✅ Free, local, open-source (MIT license)
- ✅ Native multimodal function calling (agent workflows)
- ✅ 128K context (long RFP documents)
- ✅ Privacy-preserving (100% local inference)

**Optimal Use Case**:
Execute simple-to-moderate complexity skills locally (proposal outlines, compliance matrices) while reserving Grok-4 for complex strategic reasoning (win themes, risk analysis).

**Timeline**:
Implement AFTER Issue #40 Phase 1 complete (depends on context builder + runner infrastructure).

**Resource**:
See [GLM-4.6V-Flash HuggingFace](https://huggingface.co/zai-org/GLM-4.6V-Flash) for implementation details.

---

## References

1. **GLM-4.6V Paper**: "GLM-4.1V-Thinking and GLM-4.5V: Towards Versatile Multimodal Reasoning" (Z.ai, 2025)
2. **HuggingFace Model**: https://huggingface.co/zai-org/GLM-4.6V-Flash
3. **Issue #40**: Skills Pattern framework (govcon-capture-vibe)
4. **Current Architecture**: [docs/ARCHITECTURE.md](c:\Users\benma\govcon-capture-vibe\docs\ARCHITECTURE.md)
5. **MinerU Integration**: [src/server/initialization.py](c:\Users\benma\govcon-capture-vibe\src\server\initialization.py#L93-L112)
