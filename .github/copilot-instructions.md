# Copilot Instructions for GovCon-Capture-Vibe

## CRITICAL RULES

### Rule 1: Virtual Environment Required for Python Execution

**Before running Python, uv, or any project command**, you MUST activate the virtual environment as a separate command:

```powershell
.venv\Scripts\Activate.ps1
```

**Then** run your command:

```powershell
python app.py
# or
uv pip list
# or
python -m pytest
```

**Never** run Python commands without first activating `.venv` in a separate step.

### Rule 2: Use Workspace Tools for File Operations

**NEVER use PowerShell for file operations.** Always use workspace tools:

| Operation      | ✅ USE THIS                      | ❌ NOT THIS               |
| -------------- | -------------------------------- | ------------------------- |
| Read file      | `read_file`                      | `Get-Content`, `cat`      |
| Create file    | `create_file`                    | `New-Item`, `echo >`      |
| Edit file      | `replace_string_in_file`         | `(Get-Content).Replace()` |
| Search content | `grep_search`, `semantic_search` | `Select-String`           |
| List directory | `list_dir`                       | `Get-ChildItem`, `ls`     |

**Only use PowerShell for**:

- Running Python scripts: `python app.py`
- Package management: `uv pip list`, `uv sync`
- Git commands: `git status`, `git commit`

## Project Context

### Reference Resources

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
