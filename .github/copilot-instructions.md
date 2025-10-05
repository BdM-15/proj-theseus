# Copilot Instructions for GovCon-Capture-Vibe Project

## ⚠️ ABSOLUTE REQUIREMENT: Virtual Environment Activation

**BEFORE running ANY terminal command that uses Python, uv, or project dependencies, you MUST activate the virtual environment:**

```powershell
# FIRST: Activate venv as standalone command
.venv\Scripts\Activate.ps1

# THEN: Run your command in the activated environment
<your command here>
```

**NO EXCEPTIONS.** Activate venv as a **separate command**, then run subsequent commands. Do NOT chain with semicolons. See "CRITICAL: Virtual Environment Activation" section below for details.

## ⚠️ ABSOLUTE REQUIREMENT: Use Workspace Tools, Not PowerShell

**ALWAYS prioritize workspace tools over PowerShell commands for file operations:**

**DO** (Use Workspace Tools):

- ✅ **Read files**: Use `read_file` tool, NOT `Get-Content` or `cat` in PowerShell
- ✅ **Create files**: Use `create_file` tool, NOT `New-Item` or `echo` in PowerShell
- ✅ **Edit files**: Use `replace_string_in_file` tool, NOT `(Get-Content).Replace()` in PowerShell
- ✅ **Search content**: Use `grep_search` or `semantic_search` tools, NOT `Select-String` in PowerShell
- ✅ **List directories**: Use `list_dir` tool, NOT `Get-ChildItem` in PowerShell

**ONLY use PowerShell when**:

- Running Python scripts or applications (`python app.py`)
- Using `uv` commands (`uv pip list`, `uv sync`)
- Git operations (`git status`, `git commit`)
- System commands that have no workspace equivalent

**Why This Matters**:

- Workspace tools provide better context to the agent
- Reduces unnecessary terminal command calls
- Prevents context loss from truncated terminal output
- More reliable for file operations in the conversation history

## ⚠️ CRITICAL: Ontology-Modified LightRAG Approach

### Primary Library

**Package**: `lightrag-hku==1.4.9` (installed in `/src/lightrag_govcon/`)

**Core Philosophy**: **Modify LightRAG's extraction engine with domain ontology, don't rely on generic processing.**

### Why Generic LightRAG Fails for Government Contracting

**Generic LightRAG cannot**:

- Distinguish CLIN (Contract Line Item Number) from generic line items
- Recognize Section L↔M evaluation relationships
- Identify "shall" vs "should" requirement classifications (Shipley methodology)
- Extract FAR/DFARS clause applicability
- Map SOW requirements to deliverables and evaluation criteria
- Understand Uniform Contract Format (A-M sections, J attachments)

**Our Ontology-Modified Approach**:

- **Injects government contracting entity types** into LightRAG's extraction prompts
- **Constrains relationships** to valid government contracting patterns (L↔M, requirement→evaluation)
- **Teaches domain terminology** through custom examples (PWS, SOW, CLIN, Section M factors)
- **Validates extractions** against ontology to ensure domain accuracy

**DO** (Modify LightRAG's Processing):

- ✅ **Inject ontology into `addon_params["entity_types"]`** - This modifies what LightRAG extracts
- ✅ **Customize extraction prompts** via `PROMPTS` dictionary with government contracting examples
- ✅ **Add domain-specific few-shot examples** showing RFP entity patterns
- ✅ **Post-process with ontology validation** to ensure domain accuracy
- ✅ **Constrain relationships** to valid government contracting patterns

**DO NOT** (Don't Bypass the Framework):

- ❌ Create custom preprocessing that bypasses LightRAG's semantic understanding
- ❌ Build parallel extraction mechanisms outside the framework
- ❌ Use deterministic regex for entity/section identification
- ❌ Modify LightRAG source files directly
- ❌ Assume generic LightRAG will "just figure out" government contracting concepts

### Package Management
Use `uv pip list` to verify package version, not `pip list`.

## Development Workflow

### **Critical Reference Artifacts**

When brainstorming enhancements or refining ontology, leverage these key resources alongside project artifacts:

**Project Artifacts** (Primary References):

- `/examples/` - Sample outputs (requirements, compliance matrices, QFG)
- `/prompts/` - Shipley methodology prompt templates
- `/docs/` - Shipley guides, capture plans, reference documentation
- `/src/models/` - Core Pydantic data models (RFPRequirement, ComplianceAssessment, etc.)
- `/src/agents/` - PydanticAI agents using models for structured extraction
- `/src/core/` - Ontology configuration bridging models to LightRAG

**External Repositories** (Ontology & Architecture Inspiration):

- **[LightRAG GitHub](https://github.com/HKUDS/LightRAG)** - Foundation codebase for all ontology modifications
- **[AI RFP Simulator](https://github.com/felixlkw/ai-rfp-simulator)** - Entity types, relationship patterns (Chinese, use translation)
- **[RFP Generation LangChain](https://github.com/abh2050/RFP_generation_langchain_agent_RAG)** - Automated clarification questions (Phase 6 inspiration)
- **[Awesome Procurement Data](https://github.com/makegov/awesome-procurement-data)** - Government data sources, terminology validation
