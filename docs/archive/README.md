# Archive Directory - Historical Documentation

This directory contains historical documentation, implementation records, and resolved issues from the GovCon-Capture-Vibe project evolution.

---

## 📚 Quick Navigation

### **Start Here: Consolidated Summaries**

| Document                | Description                          | Use Case                     |
| ----------------------- | ------------------------------------ | ---------------------------- |
| **BRANCH_HISTORY.md**   | All branch implementations (003-010) | "What happened in Branch X?" |
| **PROMPT_EVOLUTION.md** | Prompt engineering history           | "How did prompts evolve?"    |
| **TECHNICAL_FIXES.md**  | Major bugs and resolutions           | "How was issue X fixed?"     |

### **Detailed Reference Documents**

| Category                   | Files                                                       | Purpose                                 |
| -------------------------- | ----------------------------------------------------------- | --------------------------------------- |
| **Branch Implementations** | BRANCH*00X*\*.md (17 files)                                 | Detailed implementation logs per branch |
| **Prompts**                | PROMPT\_\*.md, prompts_branch_002/                          | Historical prompt templates and audits  |
| **Technical Issues**       | LIGHTRAG*\*.md, GROK*_.md, MINERU\__.md                     | Specific technical problem resolutions  |
| **Architecture**           | ARCHITECTURE_DECISION_RECORDS.md, HANDOFF_SUMMARY.md        | Major architectural decisions           |
| **Assessments**            | PROGRAM_ENTITY_ASSESSMENT.md, metadata_schemas_reference.md | Entity type and schema analysis         |

---

## 🗂️ Complete File Listing

### Branch Implementations (17 files)

```
BRANCH_003_IMPLEMENTATION.md          # Fully local processing (8 hours/RFP)
BRANCH_004_BASELINE.md                # Performance baselines
BRANCH_004_CODE_OPTIMIZATION.md       # Optimization strategy
BRANCH_004_COMPLETION.md              # Branch 004 final results
BRANCH_004_DEAD_CODE_AUDIT.md         # Code cleanup audit
BRANCH_004_IMPLEMENTATION.md          # Branch 004 implementation log
BRANCH_005_COMPLETION.md              # Entity type fix results
BRANCH_005_ENTITY_TYPE_FIX.md         # 16 entity type standardization
BRANCH_005_HANDOFF.md                 # Branch 005 handoff
BRANCH_005_OPTIMIZATION_HANDOFF.md    # Optimization guidance
BRANCH_006_COMPLETION.md              # Cloud processing results
BRANCH_006_IMPLEMENTATION_PLAN.md     # xAI Grok migration plan
BRANCH_008_KNOWLEDGE_GRAPH_FIX.md     # MultiDiGraph resolution
BRANCH_009_COMPLETION.md              # Phase 6 semantic inference results
BRANCH_009_IMPLEMENTATION_PLAN.md     # Phase 6 architecture
BRANCH_010_QUERY_INTELLIGENCE.md      # Current branch implementation
```

### Prompt Engineering (5 files + 1 directory)

```
PROMPT_AUDIT_ANALYSIS.md              # Prompt audit findings
PROMPT_CENTRALIZATION_SUMMARY.md      # Prompt consolidation record
PHASE_6_IMPLEMENTATION_HISTORY.md     # Phase 6 prompt evolution
phase6_prompts_historical.py          # Historical Phase 6 templates (now embedded)
prompts_branch_002/                   # Snapshot before centralization
```

### Technical Fixes (6 files)

```
LIGHTRAG_MULTIDIGRAPH_FIX.md          # Graph structure fix (Branch 008)
GROK_DIAGNOSTIC_FEEDBACK.md           # xAI Grok optimization insights
MINERU_HANDOFF.md                     # MinerU parser integration
MINERU_SETUP_GUIDE.md                 # MinerU installation
OLLAMA_WORKER_REFRESH.md              # Local LLM worker (deprecated)
metadata_schemas_reference.md         # Metadata schema reference
```

### Architecture & Decisions (2 files)

```
ARCHITECTURE_DECISION_RECORDS.md      # Major architectural choices
HANDOFF_SUMMARY.md                    # Project handoffs between sessions
```

### Assessments (1 file)

```
PROGRAM_ENTITY_ASSESSMENT.md          # PROGRAM entity type analysis
```

---

## 🎯 Common Use Cases

### "I need to understand what happened in Branch X"

→ Check `BRANCH_HISTORY.md` for summary, then specific `BRANCH_00X_*.md` files for details

### "How did we solve problem Y?"

→ Check `TECHNICAL_FIXES.md` for summary, then specific fix documents

### "What were the prompt templates before centralization?"

→ Check `PROMPT_EVOLUTION.md`, then `prompts_branch_002/` for old templates

### "What were the major architectural decisions?"

→ Read `ARCHITECTURE_DECISION_RECORDS.md`

### "Why do we use entity type Z?"

→ Check `PROGRAM_ENTITY_ASSESSMENT.md` or entity-specific sections in branch docs

---

## 📊 Project Timeline

```
Branch 002: Prompt Centralization
    ↓
Branch 003: LightRAG + Govcon Ontology (fully local, 8 hours/RFP)
    ↓
Branch 004: Code Optimization (performance baselines)
    ↓
Branch 005: Entity Type Fix (16 standardized types)
    ↓
Branch 006: Cloud Processing (xAI Grok, 417x speedup → 69 seconds/RFP)
    ↓
Branch 008: Knowledge Graph Fix (MultiDiGraph resolution)
    ↓
Branch 009: Phase 6 Semantic Inference (5 LLM algorithms)
    ↓
Branch 010: Query Intelligence + Phase 7 Metadata (CURRENT)
    ↓
Branch 011+: PostgreSQL 18 Data Warehouse (PLANNED)
```

---

## ⚠️ Important Notes

1. **Do not modify archived files** - They are historical records
2. **For current implementation**, see main `docs/` directory:
   - `docs/ARCHITECTURE.md` - Current system architecture
   - `docs/capture-intelligence/` - Current Shipley methodology
   - `docs/bug-fixes/` - Active bug documentation
3. **Archived bugs** in this directory are RESOLVED - current bugs tracked in `docs/bug-fixes/`

---

**Last Updated:** October 2025  
**Total Archived Documents:** 30+ files  
**Status:** All archived work is COMPLETE or DEPRECATED
