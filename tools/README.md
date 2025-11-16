# Utility Tools

Helper scripts for managing and testing the GovCon Capture Vibe system.

## Directory Structure

```
tools/
├── neo4j/              # Neo4j workspace management
│   ├── clear_neo4j.py          # Clear/delete workspaces
│   └── duplicate_workspace.py  # Duplicate baseline workspaces
│
├── validation/         # Production readiness validation
│   ├── validate_rfp_processing.py   # Main validation script
│   ├── deliverable_traceability.py  # Deliverable coverage checks
│   ├── query_quality.py             # Query effectiveness scoring
│   ├── section_l_m_coverage.py      # Section L↔M mapping analysis
│   └── workload_completeness.py     # Workload enrichment checks
│
└── diagnostics/        # Debugging & quality analysis
    ├── assess_quality.py            # Overall quality metrics
    ├── check_neo4j_props.py         # Property schema inspection
    ├── check_eval_factors.py        # Evaluation factor analysis
    ├── check_eval_factor_filtering.py # Factor filtering validation
    └── check_pattern_counts.py      # Pattern matching statistics
```

---

## Quick Reference

### Neo4j Management (`tools/neo4j/`)

**`clear_neo4j.py`** - Clear Neo4j workspace for fresh testing

```powershell
python tools/neo4j/clear_neo4j.py                  # Clear current workspace
python tools/neo4j/clear_neo4j.py --list           # List all workspaces
python tools/neo4j/clear_neo4j.py --workspace NAME # Clear specific workspace
python tools/neo4j/clear_neo4j.py --all            # Delete EVERYTHING (dangerous!)
```

**`duplicate_workspace.py`** - Duplicate baseline workspace ✨ NEW

```powershell
python tools/neo4j/duplicate_workspace.py
```

Interactive prompts guide you through:

- Select source workspace (e.g., baseline RFP)
- Name new workspace (e.g., baseline + technical docs)
- Dry-run mode (preview before copying)
- Copies Neo4j nodes/relationships + rag_storage folder
- Option to update `.env` to point to new workspace

**Use case**: Preserve processed RFP baseline, extend with additional documents without reprocessing.

---

### Validation (`tools/validation/`)

**`validate_rfp_processing.py`** - Production readiness validation 🎯 PRIMARY TOOL

```powershell
python tools/validation/validate_rfp_processing.py              # Validate current workspace
python tools/validation/validate_rfp_processing.py WORKSPACE    # Validate specific workspace
```

Generates comprehensive validation report with:

- Query quality scoring (30% weight)
- Section L↔M coverage (25% weight)
- Workload enrichment completeness (25% weight)
- Deliverable traceability (20% weight)
- Overall production readiness score (0-100%)

**Quality Gates:**

- 85%+ = ✅ PRODUCTION READY (deploy with confidence)
- 70-85% = ⚠️ PASS (minor gaps, document limitations)
- < 70% = ❌ FAIL (needs reprocessing)

---

### Diagnostics (`tools/diagnostics/`)

**`assess_quality.py`** - Analyze Neo4j data quality

```powershell
python tools/diagnostics/assess_quality.py
```

Shows:

- Entity/relationship counts
- Type distributions
- Correction statistics
- Sample inferred relationships
- Quality metrics

**`check_neo4j_props.py`** - Inspect Neo4j node properties

```powershell
python tools/diagnostics/check_neo4j_props.py
```

Useful for debugging property name issues and schema validation.

**`check_eval_factors.py`** - Evaluation factor analysis

```powershell
python tools/diagnostics/check_eval_factors.py
```

Analyzes evaluation factor hierarchy and filtering logic.

---

## Common Workflows

### Testing Workflow (Fresh RFP Processing)

```powershell
# 1. Clear Neo4j workspace
python tools/neo4j/clear_neo4j.py

# 2. Upload RFP via WebUI (http://localhost:9621/webui)

# 3. Validate production readiness
python tools/validation/validate_rfp_processing.py

# 4. (Optional) Assess detailed quality metrics
python tools/diagnostics/assess_quality.py
```

### Baseline Extension Workflow (Add Documents to Existing Graph)

```powershell
# 1. Duplicate baseline workspace
python tools/neo4j/duplicate_workspace.py
# Select source: afcapv_adab_iss_2025
# Enter new name: afcapv_adab_iss_2025_extended

# 2. Update .env to point to new workspace (script prompts for this)

# 3. Restart server

# 4. Upload additional documents via WebUI
# New entities/relationships added to duplicated baseline

# 5. Validate extended workspace
python tools/validation/validate_rfp_processing.py afcapv_adab_iss_2025_extended
```

### Debugging Workflow

```powershell
# 1. Check workspace exists
python tools/neo4j/clear_neo4j.py --list

# 2. Inspect node properties
python tools/diagnostics/check_neo4j_props.py

# 3. Check evaluation factors
python tools/diagnostics/check_eval_factors.py

# 4. Assess overall quality
python tools/diagnostics/assess_quality.py
```

---

## Tool Comparison Matrix

| Tool                                    | Category    | Use When                                | Time      |
| --------------------------------------- | ----------- | --------------------------------------- | --------- |
| `neo4j/clear_neo4j.py`                  | Management  | Starting fresh test                     | 5 sec     |
| `neo4j/duplicate_workspace.py`          | Management  | Extending baseline without reprocessing | 10-30 sec |
| `validation/validate_rfp_processing.py` | Validation  | After processing (PRIMARY)              | 15 sec    |
| `diagnostics/assess_quality.py`         | Diagnostics | Detailed metrics                        | 10 sec    |
| `diagnostics/check_neo4j_props.py`      | Diagnostics | Debugging schema                        | 2 sec     |
| `diagnostics/check_eval_factors.py`     | Diagnostics | Evaluation factor issues                | 5 sec     |

---

## Installation

These tools are already configured and ready to use. They:

- Auto-load `.env` configuration
- Connect to Neo4j using project settings
- Work with workspace isolation

No additional setup needed!
