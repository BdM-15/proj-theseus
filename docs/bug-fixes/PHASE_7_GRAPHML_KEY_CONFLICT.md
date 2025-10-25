# Phase 7 GraphML Key Conflict Resolution

**Date**: January 25, 2025  
**Branch**: 010-query-prompts-integration  
**Status**: ✅ RESOLVED

## Problem

After processing MCPP II RFP with Phase 7 metadata enrichment, attempting to load the graph in WebUI caused a fatal error:

```
ERROR: Error getting popular labels: invalid literal for int() with base 10: 'Significantly More Important'
ValueError: invalid literal for int() with base 10: 'Significantly More Important'
```

## Root Cause

**Phase 7 metadata enrichment used GraphML key IDs d10-d18 for node metadata attributes**, not knowing that LightRAG reserves specific key ranges:

- **d0-d5**: Node attributes (entity_id, entity_type, description, source_id, file_path, created_at)
- **d6-d11**: Edge attributes (weight, description, keywords, source_id, file_path, created_at)
- **d12+**: Available for custom attributes

When Phase 7 wrote node data with `key="d11"` containing string values like "Significantly More Important", NetworkX tried to parse it using the existing d11 key definition for **edges** (attr.type="long"), causing the ValueError.

## Impact

- **Graph visualization broken**: WebUI couldn't load graph due to NetworkX parse error
- **Query processing unaffected**: Queries still worked because LightRAG uses internal storage
- **40 nodes corrupted**: 52 data elements had conflicting key assignments

## Solution

### 1. Update Phase 7 Code

Modified `src/inference/phase7_metadata_enrichment.py` to use **d12-d20** for metadata keys:

```python
metadata_keys = {
    # Evaluation factor metadata
    'd12': ('metadata_weight', 'node', 'Evaluation factor weight (percentage or points)'),
    'd13': ('metadata_importance', 'node', 'Relative importance hierarchy'),
    'd14': ('metadata_subfactors', 'node', 'List of subfactors with weights'),
    # Submission instruction metadata
    'd15': ('metadata_page_limit', 'node', 'Page limit for submission'),
    'd16': ('metadata_format', 'node', 'Format requirements (font, margins, spacing)'),
    'd17': ('metadata_addressed_factors', 'node', 'Evaluation factors addressed by instruction'),
    # Requirement metadata
    'd18': ('metadata_criticality', 'node', 'Requirement criticality (MANDATORY/IMPORTANT/OPTIONAL)'),
    'd19': ('metadata_modal_verb', 'node', 'Modal verb used (shall/should/may)'),
    'd20': ('metadata_subject', 'node', 'Subject with obligation (Contractor/Offeror/Government)'),
}
```

### 2. Repair Existing GraphML

Created `repair_graphml_keys.py` to:
1. Remap data elements: d10→d12, d11→d13, d12→d14, d13→d15, d14→d16, d15→d17, d16→d18, d17→d19, d18→d20
2. Remove old conflicting key definitions (d12-d18 with wrong positions)
3. Add new key definitions (d12-d20 with correct descriptions)

**Results**:
- ✅ 52 data elements remapped in 40 nodes
- ✅ 7 old key definitions removed
- ✅ 9 new key definitions added
- ✅ Graph loads successfully: 4,793 nodes, 5,932 edges
- ✅ Metadata preserved: 6 importance, 8 subfactors, 14 criticality attributes

## Validation

```powershell
# Before fix
python -c "import networkx as nx; nx.read_graphml('...')"
# ValueError: invalid literal for int() with base 10: 'Significantly More Important'

# After fix
python -c "import networkx as nx; G = nx.read_graphml('...'); print(f'{len(G.nodes())} nodes, {len(G.edges())} edges')"
# SUCCESS: Graph loaded
# Nodes: 4793, Edges: 5932
```

## Lessons Learned

### 1. Always Check Existing Key Allocations

Before adding custom GraphML attributes, inspect existing key definitions:

```python
import xml.etree.ElementTree as ET
tree = ET.parse('graph.graphml')
root = tree.getroot()
ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

for key in root.findall('.//graphml:key', ns):
    print(f"{key.get('id')} ({key.get('for')}): {key.get('attr.name')} ({key.get('attr.type')})")
```

### 2. LightRAG Key Allocation Pattern

LightRAG uses a **consistent numbering scheme**:
- Node keys: d0-d5 (6 attributes)
- Edge keys: d6-d11 (6 attributes)
- **Safe range for custom node metadata: d12+**

### 3. GraphML Key Scope Matters

Key definitions specify `for="node"` or `for="edge"`. You **can** reuse the same key ID (e.g., d10) for both nodes and edges, but:
- Each must have separate `<key>` definitions
- Data type must match the usage
- Mixing causes NetworkX parse errors

**Best practice**: Avoid reusing key IDs across scopes - use separate ranges.

### 4. Validate GraphML After Schema Changes

Always test with NetworkX after modifying GraphML schema:

```python
import networkx as nx
G = nx.read_graphml('graph.graphml')  # Will raise ValueError if schema is invalid
```

Don't rely solely on WebUI - it may mask errors until visualization time.

### 5. Repair Strategy for Corrupted GraphML

If GraphML is corrupted with conflicting keys:
1. Parse XML with ElementTree (not NetworkX - it will fail)
2. Remap data element keys to non-conflicting IDs
3. Update/add correct key definitions
4. Validate with NetworkX before redeploying

## Future Prevention

### Phase 7 Code Guard

Add key allocation check at startup:

```python
def validate_key_allocation(graphml_path: Path) -> bool:
    """Verify custom keys don't conflict with LightRAG reserved range."""
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    # Get existing node keys
    node_keys = {k.get('id') for k in root.findall('.//graphml:key[@for="node"]', ns)}
    
    # Check our metadata keys are in safe range (d12+)
    for key_id in ['d12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18', 'd19', 'd20']:
        if key_id in node_keys and int(key_id[1:]) < 12:
            logger.error(f"❌ Key conflict: {key_id} overlaps with LightRAG reserved range")
            return False
    
    return True
```

### Documentation

Added to `copilot-instructions.md`:

> **GraphML Key Allocation**:
> - LightRAG reserves d0-d5 (nodes), d6-d11 (edges)
> - Phase 7 metadata uses d12-d20 (custom node attributes)
> - Always validate key definitions before adding new attributes

## References

- **NetworkX GraphML Format**: https://networkx.org/documentation/stable/reference/readwrite/graphml.html
- **GraphML Primer**: http://graphml.graphdrawing.org/primer/graphml-primer.html
- **LightRAG Storage**: `.venv/Lib/site-packages/lightrag/kg/networkx_impl.py` (lines 20-35)

## Commit

```
commit 77f91ba
Author: GitHub Copilot
Date: January 25, 2025

Fix Phase 7 GraphML key conflict: remap d10-d18 to d12-d20
```

**Files Changed**:
- `src/inference/phase7_metadata_enrichment.py`: Updated key allocation (d12-d20)
- `repair_graphml_keys.py`: One-time repair script for corrupted GraphML
- `docs/bug-fixes/PHASE_7_GRAPHML_KEY_CONFLICT.md`: This document

---

**Status**: ✅ Resolved - Graph loads successfully, metadata preserved, future processing will use correct key range
