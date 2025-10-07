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

| Pattern             | Description                | Example Fix                |
| ------------------- | -------------------------- | -------------------------- |
| `isolated_nodes`    | Nodes with < 3 edges       | SINCGARS → MCPP II Program |
| `missing_hierarchy` | Missing parent-child links | ANNEX J-#### → Section J   |
| `all`               | Run all patterns           | Combined fixes             |

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
