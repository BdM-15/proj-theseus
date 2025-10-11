# Graph Node Editing Tools

This folder contains all tools for editing the knowledge graph after processing.

## Folder Structure

```
graph_node_edits/
├── README.md                    # This file - Overview
├── auto_bulk/                   # Automated bulk editing tools
│   ├── README.md               # Bulk tool documentation
│   └── bulk_graph_fixes.py     # Pattern-based automation (PRIMARY)
├── manual/                      # Manual/interactive editing tools
│   ├── README.md               # Manual tool documentation
│   ├── interactive_graph_edit.ps1  # PowerShell CLI (SECONDARY)
│   ├── WEBUI_NODE_EDITING_GUIDE.md # Web UI Properties Panel guide
│   └── edit_graph_example.py   # Python API examples
└── archive/                     # Deprecated/superseded scripts
    ├── check_sincgars.py       # Old: SINCGARS-specific checker
    └── fix_sincgars_relationships.py  # Old: Entity-specific fix
```

## Quick Start

### Method 1: Automated Bulk Fixes (PRIMARY)

**Best for**: Common patterns, 10+ similar issues

```powershell
# Preview fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run

# Apply fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --apply
```

**See**: `auto_bulk/README.md` for full documentation

---

### Method 2: Interactive Manual CLI (SECONDARY)

**Best for**: One-off edits, controversial items, custom relationships

```powershell
# Launch interactive editor
.\graph_node_edits\manual\interactive_graph_edit.ps1
```

**See**: `manual/README.md` for full documentation

---

### Method 3: Web UI Properties Panel

**Best for**: Single node edits with visual context

1. Click node in graph visualization
2. Open Properties Panel
3. Click pencil icon to edit
4. Modify description, keywords, etc.

**See**: `manual/WEBUI_NODE_EDITING_GUIDE.md` for screenshots and details

---

### Method 4: Entity Corruption Cleanup (Branch 005)

**Best for**: Fixing LLM reasoning artifact corruption (~2% of entities)

**Context**: Grok-4-fast-reasoning occasionally outputs entity names with chain-of-thought prefixes:

- `#>|LOCATION` instead of valid `LOCATION` type
- `#|PROGRAM` instead of valid `PROGRAM` type
- `#>|evaluation_factor` (lowercase) instead of `EVALUATION_FACTOR`

**Baseline Corruption Rate**: 2.2% (13/594 entities in Navy MBOS)

**Detection**: Check server logs during processing for warnings like:

```
WARNING: Invalid entity type '#>|LOCATION' for entity 'San Diego Naval Base' (expected one of 17 valid types)
WARNING: Invalid entity type '#|PROGRAM' for entity 'MCPP II' (expected one of 17 valid types)
```

**Manual Cleanup Workflow**:

```powershell
# Step 1: Identify corrupted entities in logs
# Look for "WARNING: Invalid entity type" during processing

# Step 2: Find affected entities in GraphML
python -c "
from llm_relationship_inference import parse_graphml
entities, _ = parse_graphml('./rag_storage/graph_chunk_entity_relation.graphml')
corrupted = [e for e in entities if e['entity_type'].startswith('#')]
print(f'Found {len(corrupted)} corrupted entities:')
for e in corrupted: print(f'  - {e[\"entity_name\"]}: {e[\"entity_type\"]}')"

# Step 3: Fix using bulk corruption tool (RECOMMENDED)
# ⚠️  CRITICAL: Web UI CANNOT edit entity_type field - only description/keywords
# ⚠️  CRITICAL: Web UI limited to 1000 nodes - unusable for 4000+ node graphs

# ONLY option: Automated bulk corruption cleanup
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --dry-run

# ⚠️  WARNING: DO NOT apply without dedicated branch and backup!
# python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --apply
```

**Common Corruption Patterns**:

| Corrupted Type          | Expected Type        | Frequency (Navy MBOS) | Fix Priority |
| ----------------------- | -------------------- | --------------------- | ------------ |
| `#>\|LOCATION`          | `LOCATION`           | 3 instances           | Medium       |
| `#>\|DELIVERABLE`       | `DELIVERABLE`        | 2 instances           | Medium       |
| `#>\|DOCUMENT`          | `DOCUMENT`           | 2 instances           | Low          |
| `#>\|CONCEPT`           | `CONCEPT`            | 2 instances           | Low          |
| `#>\|REQUIREMENT`       | `REQUIREMENT`        | 1 instance            | High         |
| `#\|PROGRAM`            | `PROGRAM`            | 1 instance            | High         |
| `#\|EQUIPMENT`          | `EQUIPMENT`          | 1 instance            | Medium       |
| `#\|DOCUMENT`           | `DOCUMENT`           | 1 instance            | Low          |
| `#>\|Other`             | _(invalid - delete)_ | 1 instance            | High         |
| `#>\|evaluation_factor` | `EVALUATION_FACTOR`  | 1 instance            | **CRITICAL** |

**Priority Guidance**:

- **CRITICAL**: `EVALUATION_FACTOR` corruption affects Section M analysis (proposal scoring)
- **HIGH**: `REQUIREMENT` and `PROGRAM` are core RFP entities
- **MEDIUM**: Other corruptions impact queries but aren't blocking
- **LOW**: `DOCUMENT`/`CONCEPT` are generic types with less impact

**Automated Cleanup Tool** (Branch 005 - EXPERIMENTAL):

- `python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --dry-run`
- Detects #>|TYPE, #|TYPE, lowercase types, invalid types
- Auto-fixes high-confidence patterns (≥0.80 confidence)
- Flags low-confidence items for manual review
- **⚠️ NOT TESTED YET** - requires dedicated branch for implementation
- **⚠️ NOT included in 'all' pattern** (must explicitly specify)
- See `auto_bulk/README.md` for full documentation

**Future Automation** (Task 2 from Branch 005):

- Pre-validation sanitizer: Strip `#>|` and `#|` prefixes BEFORE entity type validation
- Expected result: 100% recovery of rejected entities, 0% corruption warnings
- Implementation: `src/utils/entity_sanitizer.py`

**PostgreSQL Tracking** (Phase 8):

- Corruption patterns will be logged to `entity_corruption_tracking` table
- Enables trend analysis across RFPs and LLM model versions
- See `docs/POSTGRESQL_IMPLEMENTATION_PLAN.md` for schema details

**See**: Server logs during processing for real-time corruption detection

---

## Workflow Recommendation

1. **Analyze** graph with bulk tool dry-run:

   ```powershell
   python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run
   ```

2. **Apply** automated fixes for common patterns:

   ```powershell
   python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --apply
   ```

3. **Review** remaining issues with interactive CLI:

   ```powershell
   .\graph_node_edits\manual\interactive_graph_edit.ps1
   ```

4. **Verify** changes in Web UI (visual confirmation)

---

## Available Patterns (Bulk Tool)

| Pattern             | Description                         | Example Fix                         |
| ------------------- | ----------------------------------- | ----------------------------------- |
| `isolated_nodes`    | Nodes with < 3 edges                | SINCGARS → MCPP II Program          |
| `missing_hierarchy` | Missing parent-child links          | ANNEX J-#### → Section J            |
| `corruption` ⚠️     | Entity type corruption (Branch 005) | #>\|LOCATION → LOCATION             |
| `all`               | Run all patterns EXCEPT corruption  | Combined fixes (safe patterns only) |

---

## When to Use Each Tool

| Scenario                  | Recommended Tool    | Reason           |
| ------------------------- | ------------------- | ---------------- |
| 50+ isolated nodes        | Bulk Tool           | Fast, consistent |
| ANNEX → Section patterns  | Bulk Tool           | Rule-based       |
| 5 controversial items     | Interactive CLI     | Human judgment   |
| Add 1 custom relationship | Interactive CLI     | Quick, guided    |
| Edit node description     | Web UI              | Visual context   |
| Test fix strategy         | Bulk Tool (dry-run) | Preview first    |

---

## Advanced Usage

### Python API (For Custom Scripts)

See `manual/edit_graph_example.py` for programmatic examples:

```python
from lightrag import LightRAG

rag = LightRAG(working_dir='./rag_storage')

await rag.acreate_relation(
    source_entity="SINCGARS",
    target_entity="MCPP II Program",
    relation_data={
        'description': 'SINCGARS is part of MCPP II',
        'relationship_type': 'CHILD_OF',
        'weight': 0.9
    }
)
```

### REST API (For External Tools)

```bash
curl -X POST http://localhost:5000/create_relation \
  -H "Content-Type: application/json" \
  -d '{
    "source_entity": "SINCGARS",
    "target_entity": "MCPP II Program",
    "description": "SINCGARS is part of MCPP II",
    "relationship_type": "CHILD_OF",
    "weight": 0.9
  }'
```

---

## Archive Folder

The `archive/` folder contains **deprecated scripts** that have been superseded by the new tools:

- ❌ `check_sincgars.py` - Entity-specific checker (use bulk tool now)
- ❌ `fix_sincgars_relationships.py` - Entity-specific fix (use bulk tool now)

**Do not use** these scripts - they are kept for reference only.

---

## Troubleshooting

### "GraphML not found"

- Ensure you've processed at least one document
- Check `rag_storage/graph_chunk_entity_relation.graphml` exists

### "No module named 'lightrag'"

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

### "No isolated nodes found"

- Your graph is well-connected! ✅
- Try lowering threshold: `--threshold 2`

### "Relationship not created"

- Entity names are case-sensitive
- Use exact names from graph
- Check both entities exist

---

## Documentation

- **Bulk Tool**: `auto_bulk/README.md`
- **Interactive CLI**: `manual/README.md`
- **Web UI**: `manual/WEBUI_NODE_EDITING_GUIDE.md`
- **Full Guide**: `docs/MANUAL_EDITING_TOOLS.md` (project root)

---

## Status

✅ **Production Ready**

All tools tested with MCPP II RFP dataset (3,436 nodes, 3,260 edges)

**Last Updated**: October 7, 2025
