# Automated Bulk Graph Editing

This folder contains the **PRIMARY** method for fixing common graph issues through pattern-based automation.

## Tool: `bulk_graph_fixes.py`

Pattern-based bulk editing tool for automated graph fixes.

### When to Use

✅ **Use bulk tool for**:

- 10+ nodes with similar issues
- Common patterns (isolated nodes, missing hierarchies)
- Repetitive fixes
- Testing fix strategies (dry-run mode)
- Consistent rule application

❌ **Don't use bulk tool for**:

- One-off custom edits → Use `manual/interactive_graph_edit.ps1`
- Controversial items → Use interactive CLI for human review
- Complex judgment calls → Manual review needed

---

## Quick Start

### Preview Fixes (Dry Run - SAFE)

```powershell
# See what would be fixed (no changes made)
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run
```

### Apply Fixes

```powershell
# Apply isolated nodes fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern isolated_nodes --apply

# Apply all fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --apply
```

---

## Available Patterns

### 1. `isolated_nodes`

**Finds**: Nodes with < 3 edges (weakly connected)

**Fixes**:

- Technology → Connect to MCPP II Program or Navy GSE
- Requirements → Connect to MCPP II SOW
- Deliverables → Connect to MCPP II SOW

**Example Output**:

```
Found 15 isolated nodes (edge count < 3):

  • SINCGARS (technology)
    Edges: 2
    Description: SINCGARS radio systems, including Interface Module...
    → FIX: Add CHILD_OF relationship to MCPP II Program
       Reason: Technology mentioned in MCPP II context
```

### 2. `missing_hierarchy`

**Finds**: Missing parent-child relationships

**Fixes**:

- ANNEX with prefix → Link to parent Section
  - `J-0200000-18` → `Section J` (CHILD_OF)
- CLAUSE → Link to Section I or K based on description
- REQUIREMENT → Link to STATEMENT_OF_WORK

**Example Output**:

```
Found 12 missing hierarchical relationships:

  • Annex J-0200000-18 → Section J
    Type: CHILD_OF
    Reason: Annex has 'J-' prefix matching Section J naming pattern
    Confidence: 0.95
```

### 3. `all`

Runs all patterns sequentially.

---

## Command-Line Options

```bash
python graph_node_edits/auto_bulk/bulk_graph_fixes.py \
  --pattern <pattern>      # Required: isolated_nodes | missing_hierarchy | all
  --apply                  # Apply fixes (default is dry-run)
  --dry-run               # Preview only (default)
  --working-dir <path>    # Custom RAG storage (default: ./rag_storage)
```

### Examples

```powershell
# Preview isolated nodes fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern isolated_nodes --dry-run

# Apply isolated nodes fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern isolated_nodes --apply

# Preview all fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run

# Apply all fixes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --apply

# Use custom working directory
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run --working-dir ./custom_rag
```

---

## How It Works

### Step 1: Load Graph

```
📊 Loaded graph: 3436 nodes, 3260 edges
```

Parses `graph_chunk_entity_relation.graphml` using XML ElementTree.

### Step 2: Analyze Patterns

**For Isolated Nodes**:

1. Count edges per node
2. Identify nodes with < 3 edges
3. Determine appropriate targets based on:
   - Entity type (technology, requirement, deliverable)
   - Description content (keywords like "MCPP", "Navy")
   - Context clues

**For Missing Hierarchies**:

1. Find ANNEX entities with section prefixes
2. Find CLAUSE entities referencing sections
3. Match to parent entities
4. Verify connections don't already exist

### Step 3: Propose Fixes

```
SUMMARY: 15 fixes identified
DRY RUN - No changes applied
Run with --apply to execute fixes
```

Each fix includes:

- Source entity name
- Target entity name
- Relationship type (CHILD_OF, COMPONENT_OF, etc.)
- Reason (explanation for transparency)
- Confidence score (0.0-1.0)

### Step 4: Apply (If --apply Used)

```
Applying fixes...
  ✅ SINCGARS → MCPP II Program (CHILD_OF)
  ✅ Equipment Maintenance → MCPP II SOW (COMPONENT_OF)
  ...
✅ All fixes applied!
```

Uses LightRAG async API to create relationships.

---

## Safety Features

### 1. Dry Run by Default

**ALWAYS preview first**:

```powershell
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern all --dry-run
```

No changes made unless `--apply` explicitly used.

### 2. Confidence Scoring

Each fix has a confidence score (0.0-1.0):

- **0.95**: High confidence (exact pattern match)
- **0.85**: Medium-high (strong context clues)
- **0.75**: Medium (heuristic-based)
- **0.60**: Lower (requires validation)

Review confidence scores before applying.

### 3. Clear Reasoning

Every fix includes human-readable explanation:

```
Reason: Technology mentioned in MCPP II context
```

Allows manual validation of automated decisions.

### 4. Incremental Application

Run patterns individually for control:

```powershell
# Step 1: Fix isolated nodes
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern isolated_nodes --apply

# Step 2: Fix hierarchies
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern missing_hierarchy --apply
```

---

## Pattern Development

### Adding New Patterns

Edit `bulk_graph_fixes.py` to add new patterns:

```python
def find_custom_pattern(self, nodes, edges):
    """
    Find entities matching custom pattern.
    """
    matches = []

    for node in nodes:
        # Your detection logic
        if condition:
            matches.append({
                'source': node['entity_name'],
                'target': 'Target Entity',
                'relationship_type': 'CUSTOM_TYPE',
                'reason': 'Why this fix makes sense',
                'confidence': 0.85
            })

    return matches

async def fix_custom_pattern(self, matches, apply=False):
    """
    Apply custom pattern fixes.
    """
    # Similar to existing fix methods
    pass
```

Then add to `run_pattern()`:

```python
if pattern in ['custom', 'all']:
    matches = self.find_custom_pattern(nodes, edges)
    await self.fix_custom_pattern(matches, apply=apply)
```

---

## Integration with LightRAG

### Async API Calls

```python
await self.rag.acreate_relation(
    source_entity='SINCGARS',
    target_entity='MCPP II Program',
    relation_data={
        'description': 'SINCGARS is part of MCPP II',
        'relationship_type': 'CHILD_OF',
        'weight': 0.85
    }
)
```

### Relationship Types Used

- `CHILD_OF`: Hierarchical containment (bottom-up)
- `COMPONENT_OF`: Part of larger whole
- `RELATED_TO`: Generic association (weak)
- `REFERENCES`: Citation or mention
- `MAINTAINED_BY`: Maintenance relationship

---

## Performance

### MCPP II RFP Dataset

- **Nodes**: 3,436
- **Edges**: 3,260
- **Isolated nodes found**: 15-20
- **Missing hierarchies**: 10-15
- **Processing time**: ~2-5 seconds (dry-run)
- **Application time**: ~10-20 seconds (--apply)

### Scalability

Tested up to 10,000 nodes without performance issues.

---

## Troubleshooting

### Error: "GraphML not found"

**Cause**: RAG storage not initialized

**Fix**:

```powershell
# Check file exists
Test-Path .\rag_storage\graph_chunk_entity_relation.graphml

# If not, process a document first via web UI
```

### Error: "No module named 'lightrag'"

**Cause**: Virtual environment not activated

**Fix**:

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

### Warning: "No fixes identified"

**Cause**: Graph already well-connected ✅

**Action**: Try lowering threshold:

```powershell
# Edit bulk_graph_fixes.py line 125
threshold=2  # instead of 3
```

### Error: "Relationship creation failed"

**Cause**: Target entity doesn't exist

**Fix**: Check entity names are exact (case-sensitive):

```powershell
# Search GraphML for entity
Select-String -Path .\rag_storage\graph_chunk_entity_relation.graphml -Pattern "MCPP II Program"
```

---

## Output Examples

### Successful Dry Run

```
================================================================================
Pattern-Based Bulk Graph Editing Tool
================================================================================

✅ Connected to graph: .\rag_storage

📊 Loaded graph: 3436 nodes, 3260 edges

================================================================================
FIX PATTERN: Isolated Nodes
================================================================================

Found 15 isolated nodes (edge count < 3):

  • SINCGARS (technology)
    Edges: 2
    Description: SINCGARS radio systems, including Interface Module (SIM)...
    → FIX: Add CHILD_OF relationship to MCPP II Program
       Reason: Technology mentioned in MCPP II context

  • Equipment Maintenance (requirement)
    Edges: 1
    Description: Contractor shall maintain equipment per specifications...
    → FIX: Add COMPONENT_OF relationship to MCPP II SOW
       Reason: Requirement specified in Statement of Work

================================================================================
SUMMARY: 15 fixes identified
================================================================================

DRY RUN - No changes applied
Run with --apply to execute fixes
```

### Successful Application

```
================================================================================
FIX PATTERN: Isolated Nodes
================================================================================

Found 15 isolated nodes (edge count < 3):
[... node details ...]

================================================================================
SUMMARY: 15 fixes identified
================================================================================

Applying fixes...
  ✅ SINCGARS → MCPP II Program (CHILD_OF)
  ✅ Equipment Maintenance → MCPP II SOW (COMPONENT_OF)
  ✅ Technical Documentation → MCPP II SOW (COMPONENT_OF)
  [... 12 more ...]

✅ All fixes applied!
```

---

## Next Steps

After running bulk tool:

1. **Verify** changes in Web UI (visual confirmation)
2. **Review** remaining issues with interactive CLI:
   ```powershell
   .\graph_node_edits\manual\interactive_graph_edit.ps1
   ```
3. **Test** queries to ensure graph quality improved

---

## Related Documentation

- **Interactive CLI**: `../manual/README.md`
- **Web UI Guide**: `../manual/WEBUI_NODE_EDITING_GUIDE.md`
- **Python API Examples**: `../manual/edit_graph_example.py`
- **Full Documentation**: `../../docs/MANUAL_EDITING_TOOLS.md`

---

**Status**: ✅ Production Ready  
**Last Updated**: October 7, 2025
