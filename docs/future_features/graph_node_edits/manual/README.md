# Manual Graph Editing Tools

This folder contains the **SECONDARY** methods for manual and interactive graph editing.

## Tools Overview

| Tool                          | Type            | Best For                           |
| ----------------------------- | --------------- | ---------------------------------- |
| `interactive_graph_edit.ps1`  | PowerShell CLI  | One-off edits, controversial items |
| `WEBUI_NODE_EDITING_GUIDE.md` | Web UI Guide    | Visual editing with context        |
| `edit_graph_example.py`       | Python Examples | Custom automation scripts          |

---

## Tool 1: Interactive CLI (PowerShell)

### When to Use

✅ **Use interactive CLI for**:

- One-off custom relationships
- Controversial items needing human judgment
- Manual review of specific nodes
- Learning what edits are needed
- Quick fixes without writing scripts

❌ **Don't use for**:

- Bulk operations → Use `auto_bulk/bulk_graph_fixes.py`
- Simple node edits → Use Web UI Properties Panel

---

### Quick Start

```powershell
# Launch interactive editor
.\graph_node_edits\manual\interactive_graph_edit.ps1

# With custom working directory
.\graph_node_edits\manual\interactive_graph_edit.ps1 -WorkingDir ".\custom_rag"
```

---

### Features

#### 1. Fix Isolated Nodes (Interactive Review)

**What it does**:

- Finds nodes with < 3 edges
- Shows each node one at a time
- Prompts for action with guided options
- Confirms before applying changes

**Workflow**:

```
1. Load graph structure
2. Find isolated nodes
3. For each node:
   - Show details (name, type, edges, description)
   - Offer options:
     [1] Add to program (MCPP II Program)
     [2] Add to SOW
     [3] Add custom relationship
     [4] Skip
   - Confirm action
   - Apply change
```

**Example Session**:

```powershell
PS> .\graph_node_edits\manual\interactive_graph_edit.ps1

================================================================================
Interactive Graph Editor - PowerShell CLI
================================================================================

Working Directory: .\rag_storage

✅ Loaded 3436 nodes and 3260 edges

What would you like to do?
  [1] Fix isolated nodes (interactive review)
  [2] Add single relationship (manual)
  [3] Exit

Enter choice (1-3): 1

================================================================================
Finding Isolated Nodes
================================================================================

ℹ️  Found 15 isolated nodes (edge count < 3)

Review nodes interactively?
Continue? (y/n): y

================================================================================
Reviewing Node 1 of 15
================================================================================

Node: SINCGARS
  ID: SINCGARS
  Type: technology
  Edges: 2
  Description: SINCGARS radio systems, including Interface Module (SIM)...

What would you like to do?
  [1] Add relationship to program (MCPP II Program)
  [2] Add relationship to SOW
  [3] Add custom relationship
  [4] Skip this node

Enter choice (1-4): 1

Add CHILD_OF relationship to 'MCPP II Program'?
Continue? (y/n): y

ℹ️  Creating relationship...
  Source: SINCGARS
  Target: MCPP II Program
  Type: CHILD_OF
  Description: SINCGARS is part of MCPP II Program
  Weight: 0.9

✅ Relationship created successfully
✅ Relationship added successfully!
```

#### 2. Add Single Relationship (Manual)

**What it does**:

- Prompts for source and target entities
- Offers relationship type selection
- Asks for description
- Confirms before creation

**Workflow**:

```
1. Enter source entity name
2. Enter target entity name
3. Select relationship type from menu
4. Enter description
5. Enter weight (0.0-1.0)
6. Confirm
7. Apply
```

**Example Session**:

```powershell
What would you like to do?
  [1] Fix isolated nodes (interactive review)
  [2] Add single relationship (manual)
  [3] Exit

Enter choice (1-3): 2

================================================================================
Add Manual Relationship
================================================================================

Enter source entity name: SINCGARS
Enter target entity name: Section C

Select relationship type
  [1] CHILD_OF
  [2] COMPONENT_OF
  [3] REFERENCES
  [4] RELATED_TO
  [5] CONTAINS
  [6] GUIDES
  [7] EVALUATED_BY

Enter choice (1-7): 3

Enter description: SINCGARS requirements referenced in Section C
Enter weight (0.0-1.0, default 0.9): 0.8

Add REFERENCES relationship: 'SINCGARS' → 'Section C'?
Continue? (y/n): y

ℹ️  Creating relationship...
  Source: SINCGARS
  Target: Section C
  Type: REFERENCES
  Description: SINCGARS requirements referenced in Section C
  Weight: 0.8

✅ Relationship created successfully
✅ Relationship added successfully!
```

---

### User Interface Features

#### Color-Coded Output

- **Green** (✅): Success messages
- **Red** (❌): Error messages
- **Yellow** (⚠️): Warnings
- **Cyan** (ℹ️): Information
- **Magenta**: Prompts and questions

#### Numbered Menus

All choices use numbers (no ambiguous text matching):

```
  [1] Option A
  [2] Option B
  [3] Option C
```

#### Confirmation Prompts

All changes require confirmation:

```
Add CHILD_OF relationship to 'MCPP II Program'?
Continue? (y/n):
```

---

### Implementation Details

**PowerShell Native**:

- Uses `Get-Content`, `Select-Xml` for GraphML parsing
- No Python dependencies for graph reading
- Windows-friendly (PowerShell 5.1+)

**Integration with Python**:

- Generates temporary Python scripts
- Calls LightRAG API for changes
- Cleans up temp files automatically

**Error Handling**:

- Try/catch blocks for all operations
- Clear error messages
- Stack traces on failure

---

### Troubleshooting

#### Error: "GraphML not found"

**Fix**:

```powershell
# Check path
Test-Path .\rag_storage\graph_chunk_entity_relation.graphml

# If false, process document first
```

#### Error: "Python command not found"

**Fix**:

```powershell
# Add Python to PATH or use full path
# Edit line 207 in script:
& "C:\Python313\python.exe" $tempScript
```

#### Error: "Relationship not created"

**Causes**:

- Entity names don't match (case-sensitive)
- Target entity doesn't exist
- LightRAG not initialized

**Fix**:

```powershell
# Verify entity names in GraphML
Select-String -Path .\rag_storage\graph_chunk_entity_relation.graphml -Pattern "SINCGARS"
```

---

## Tool 2: Web UI Properties Panel

See `WEBUI_NODE_EDITING_GUIDE.md` for complete guide.

### Quick Reference

**Access**:

1. Click node in graph visualization
2. Properties Panel opens on right
3. Click pencil icon to edit

**Editable Fields**:

- `entity_id`: Unique identifier (caution!)
- `description`: Node description
- `keywords`: Comma-separated keywords

**Best for**:

- Single node edits
- Adding/updating descriptions
- Adding keywords for better search
- Visual context (see connected nodes)

---

## Tool 3: Python API Examples

See `edit_graph_example.py` for full examples.

### Quick Examples

#### Create Node

```python
from lightrag import LightRAG

rag = LightRAG(working_dir='./rag_storage')

await rag.acreate_entity(
    entity_name="MCPP II Program",
    entity_data={
        'description': 'Marine Corps Prepositioning Program II',
        'entity_type': 'program',
        'source_id': 'manual_creation'
    }
)
```

#### Create Relationship

```python
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

#### Update Node

```python
await rag.aupdate_entity(
    entity_name="SINCGARS",
    entity_data={
        'description': 'Updated description...',
        'keywords': ['radio', 'communications', 'tactical']
    }
)
```

#### Delete Relationship

```python
await rag.adelete_relation(
    source_entity="SINCGARS",
    target_entity="Old Target"
)
```

---

## Workflow Comparison

### When to Use Each Tool

| Scenario              | Tool            | Reason                |
| --------------------- | --------------- | --------------------- |
| 50+ similar issues    | `auto_bulk/`    | Automated, consistent |
| 5 controversial nodes | Interactive CLI | Human judgment        |
| Add 1 relationship    | Interactive CLI | Quick, guided         |
| Edit node description | Web UI          | Visual context        |
| Custom automation     | Python API      | Full control          |
| Learn graph structure | Web UI          | Visual exploration    |

### Recommended Workflow

1. **Bulk fixes first**:

   ```powershell
   python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --apply
   ```

2. **Interactive review**:

   ```powershell
   .\graph_node_edits\manual\interactive_graph_edit.ps1
   ```

3. **Visual verification**:

   - Open Web UI
   - Click edited nodes
   - Verify changes correct

4. **Custom automation** (if needed):
   - Write Python script using examples
   - Test with small dataset
   - Apply to full graph

---

## REST API Reference

For external tools and integrations.

### Create Relationship

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

### Update Entity

```bash
curl -X POST http://localhost:5000/update_entity \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "SINCGARS",
    "description": "Updated description",
    "keywords": ["radio", "communications"]
  }'
```

### Delete Relationship

```bash
curl -X POST http://localhost:5000/delete_relation \
  -H "Content-Type: application/json" \
  -d '{
    "source_entity": "SINCGARS",
    "target_entity": "Old Target"
  }'
```

---

## Best Practices

### Entity Name Matching

**CRITICAL**: Entity names are case-sensitive!

✅ **Correct**:

```powershell
Source: SINCGARS
Target: MCPP II Program
```

❌ **Wrong**:

```powershell
Source: sincgars          # lowercase
Target: MCPP 2 Program   # missing "II"
```

**How to find exact names**:

```powershell
# Search GraphML
Select-String -Path .\rag_storage\graph_chunk_entity_relation.graphml -Pattern "SINCGARS"

# Or use Web UI (click node, see exact name)
```

### Relationship Types

Use **standard types** for consistency:

| Type           | When to Use              | Direction             |
| -------------- | ------------------------ | --------------------- |
| `CHILD_OF`     | Hierarchical containment | Child → Parent        |
| `CONTAINS`     | Hierarchical containment | Parent → Child        |
| `COMPONENT_OF` | Part of larger whole     | Part → Whole          |
| `REFERENCES`   | Citation or mention      | Referrer → Referenced |
| `RELATED_TO`   | Generic association      | Either                |
| `GUIDES`       | Process/procedure        | Guide → Guided        |
| `EVALUATED_BY` | Assessment               | Evaluated → Evaluator |

### Weight Guidelines

| Weight    | Confidence | Use Case                           |
| --------- | ---------- | ---------------------------------- |
| 0.95+     | Very High  | Explicit mention, direct hierarchy |
| 0.85-0.94 | High       | Strong context clues               |
| 0.75-0.84 | Medium     | Inferred from description          |
| 0.60-0.74 | Lower      | Heuristic-based                    |
| < 0.60    | Uncertain  | Requires validation                |

---

## Testing Your Changes

### Step 1: Verify in GraphML

```powershell
# Check relationship exists
Select-String -Path .\rag_storage\graph_chunk_entity_relation.graphml -Pattern "SINCGARS"
```

### Step 2: Verify in Web UI

1. Open Web UI (http://localhost:5000)
2. Click source node
3. Check "Connected Edges" section
4. Verify new relationship appears

### Step 3: Test Query

```python
# Query graph
response = rag.query("What is SINCGARS?")

# Should mention MCPP II Program if relationship added
```

---

## Related Documentation

- **Bulk Tool**: `../auto_bulk/README.md`
- **Main Overview**: `../README.md`
- **Full Guide**: `../../docs/MANUAL_EDITING_TOOLS.md`
- **Web UI Guide**: `WEBUI_NODE_EDITING_GUIDE.md` (this folder)

---

**Status**: ✅ Production Ready  
**Last Updated**: October 7, 2025
