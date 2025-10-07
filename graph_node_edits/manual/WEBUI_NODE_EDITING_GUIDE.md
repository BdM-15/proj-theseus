# LightRAG Web UI - Visual Node/Edge Editing Guide

## Overview

The LightRAG Web UI **does support visual editing** of nodes and edges, but it doesn't use traditional right-click context menus. Instead, it uses a **Properties Panel** with inline editing.

## How to Edit Nodes and Edges

### Step 1: Enable the Properties Panel

1. Open the Web UI at `http://localhost:9621`
2. Look for the **Settings icon (⚙️)** in the bottom-left corner
3. Click it to open settings
4. Make sure **"Show Property Panel"** is checked ✅

### Step 2: Select an Element

**Click on any node or edge** in the graph visualization. When selected:

- The element will highlight
- A **Properties Panel** appears (usually on the right side)

### Step 3: Edit Properties

In the Properties Panel, you'll see:

#### For Nodes:

```
Node Details
├── id: node_123
├── labels: "Section J"
├── degree: 15
└── Properties:
    ├── entity_type: "section"
    ├── entity_id: "Section J" ✏️ ← EDITABLE
    ├── description: "Sections and clauses..." ✏️ ← EDITABLE
    └── keywords: "section, contract" ✏️ ← EDITABLE
```

#### For Edges:

```
Edge Details
├── id: edge_456
├── source: "Section J"
├── target: "Clause 52.212-1"
└── Properties:
    ├── relationship_type: "CONTAINS"
    ├── description: "Section J contains clause..." ✏️ ← EDITABLE
    └── keywords: "contains hierarchical" ✏️ ← EDITABLE
```

### Step 4: Make Your Edit

1. **Click the pencil icon (✏️)** next to an editable property
2. An **edit dialog** will open with a text area
3. Make your changes
4. Click **"Save"** to commit the changes to the graph

## Editable vs Read-Only Properties

### ✏️ Editable Properties:

- **entity_id** (node name) - Changes the node's display name
- **description** - Edit the node/edge description
- **keywords** - Modify search keywords

### 🔒 Read-Only Properties:

- **id** - Internal identifier (cannot change)
- **entity_type** - Node type (clause, section, etc.)
- **relationship_type** - Edge type (CONTAINS, CHILD_OF, etc.)
- **created_at** - Timestamp
- **weight** - Relationship strength

## Advanced Features

### Expand Node

- Click the **"Expand"** button (GitBranch+ icon) in the node properties
- Fetches connected nodes with depth=2
- Adds them to the current visualization

### Prune Node

- Click the **"Prune"** button (Scissors icon) in the node properties
- Removes the node and its orphaned connections
- Asks for confirmation if it would delete all nodes

### Rename Node (entity_id)

When you edit `entity_id`:

- The system checks if the new name already exists
- If unique, it updates:
  - The node itself
  - All connected edges
  - All references in the graph
- This is essentially a "rename" operation

## Why No Right-Click Menu?

The Web UI uses a **modern panel-based interface** instead of context menus because:

1. **Better for complex edits** - Multi-line descriptions work better in dialogs
2. **Touch-friendly** - Works on tablets/mobile devices
3. **Clearer feedback** - Shows all properties in one place
4. **Safer** - Edit dialog prevents accidental changes

## Programmatic Editing Tools

For bulk edits or pattern-based fixes, we provide two complementary tools:

### 🔧 Primary Method: Pattern-Based Bulk Tool

**Use this for:** Common graph issues, bulk operations, automated fixes

```powershell
# Preview fixes (dry run)
python bulk_graph_fixes.py --pattern isolated_nodes --dry-run

# Apply isolated nodes fixes
python bulk_graph_fixes.py --pattern isolated_nodes --apply

# Run all fix patterns
python bulk_graph_fixes.py --pattern all --apply
```

**Available patterns:**
- `isolated_nodes` - Fix nodes with < 3 edges
- `missing_hierarchy` - Add missing CHILD_OF relationships (ANNEX → Section, CLAUSE → Section)
- `all` - Run all patterns

**Example output:**
```
Found 15 isolated nodes (edge count < 3):

  • SINCGARS (technology)
    Edges: 2
    Description: SINCGARS radio systems, including Interface Module...
    → FIX: Add CHILD_OF relationship to MCPP II Program
       Reason: Technology mentioned in MCPP II context

SUMMARY: 15 fixes identified
```

### 🎯 Secondary Method: Interactive CLI (PowerShell)

**Use this for:** One-off edits, controversial items, manual review

```powershell
# Launch interactive editor
.\interactive_graph_edit.ps1

# With custom working directory
.\interactive_graph_edit.ps1 -WorkingDir ".\custom_rag_storage"
```

**Features:**
- Interactive review of isolated nodes
- Manual relationship creation
- PowerShell-native (Windows-friendly)
- Guided prompts with validation
- Confirmation before changes

**Example workflow:**
```
What would you like to do?
  [1] Fix isolated nodes (interactive review)
  [2] Add single relationship (manual)
  [3] Exit

Enter choice: 1

Node: SINCGARS
  Type: technology
  Edges: 2
  Description: SINCGARS radio systems...

What would you like to do?
  [1] Add relationship to program (MCPP II Program)
  [2] Add relationship to SOW
  [3] Add custom relationship
  [4] Skip this node

Enter choice: 1
Continue? (y/n): y
✅ Relationship added successfully!
```

## Backend API (Programmatic Editing)

For custom scripts or advanced automation, you can use the REST API or Python API directly:

### REST API:
<!-- Need to convert to powershell format -->
```bash 
# Edit a node
POST http://localhost:9621/graph/entity/edit
{
  "entity_name": "Section J",
  "updated_data": {
    "description": "New description here"
  }
}

# Create a relationship
POST http://localhost:9621/graph/relation/create
{
  "source_entity": "Section J",
  "target_entity": "Clause 52.212-1",
  "relation_data": {
    "description": "Section J contains this clause",
    "relationship_type": "CONTAINS",
    "weight": 1.0
  }
}
```

### Python API:

```python
from lightrag import LightRAG

rag = LightRAG(working_dir="./rag_storage")

# Edit node
await rag.aedit_entity(
    entity_name="Section J",
    updated_data={"description": "New description"}
)

# Create relationship
await rag.acreate_relation(
    source_entity="Section J",
    target_entity="Clause 52.212-1",
    relation_data={
        "description": "Contains relationship",
        "relationship_type": "CONTAINS",
        "weight": 1.0
    }
)
```

See `examples/edit_graph_example.py` for complete examples.

## Troubleshooting

### "I don't see the Properties Panel"

- Check Settings (⚙️) → "Show Property Panel" is enabled
- Make sure you **clicked on a node or edge** to select it
- Try refreshing the page

### "I don't see pencil icons"

- Only **description**, **entity_id**, and **keywords** are editable
- Other properties are read-only for data integrity

### "My changes aren't saving"

- Check browser console for errors
- Verify the server is running (`http://localhost:9621`)
- Make sure you clicked "Save" in the edit dialog

### "Right-click only shows browser menu"

- This is expected! The Web UI doesn't use right-click menus
- Use the Properties Panel instead

## Settings to Explore

In the Settings panel (⚙️), you can also configure:

- **Show Node Labels** - Display entity names on nodes
- **Node Draggable** - Enable/disable drag-to-move
- **Show Edge Labels** - Display relationship types
- **Max Query Depth** - How many hops to traverse (1-3)
- **Max Nodes** - Limit graph size for performance

## Summary

✅ **Visual editing IS supported** via the Properties Panel
❌ **No right-click context menus** (by design)
✏️ **Click node/edge → Properties Panel → Pencil icon → Edit dialog**
🔧 **Advanced edits via REST/Python API**

The Web UI is designed for interactive exploration and quick edits, while the API is better for bulk operations or programmatic modifications.
