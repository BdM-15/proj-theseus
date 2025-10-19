# LightRAG MultiDiGraph Edge Access Bug

**Status**: Temporary monkey patch applied (awaiting upstream fix)  
**Affected Version**: LightRAG v1.4.9.3  
**Issue Date**: January 2025  
**Resolution**: In-memory runtime patching

---

## Problem Description

LightRAG's `get_knowledge_graph()` method fails when the graph is a `MultiDiGraph` due to incorrect edge access pattern in `networkx_impl.py` line 454.

### Error

```
ValueError: not enough values to unpack (expected 3, got 2)
File: networkx/classes/reportviews.py, line 1368
```

### Root Cause

```python
# Line 454 in lightrag/kg/networkx_impl.py
for edge in subgraph.edges():
    source, target = edge
    edge_data = dict(subgraph.edges[edge])  # ❌ Fails for MultiDiGraph
```

**Why it fails**:

- Iterating `subgraph.edges()` returns 2-tuples: `(u, v)`
- Accessing `subgraph.edges[u, v]` on MultiDiGraph triggers NetworkX's `__getitem__`
- NetworkX expects 3-tuple indexing `(u, v, k)` for MultiDiGraph, causing unpack error

---

## Our Solution

**File**: `src/utils/lightrag_multidigraph_fix.py`

Minimal, targeted monkey patch that replaces ONLY the problematic edge iteration:

```python
# ✅ FIXED: Use .edges(data=True) iteration
for source, target, edge_data in subgraph.edges(data=True):
    # edge_data is already a dict, no indexing needed
    # Works for ALL graph types: Graph, DiGraph, MultiGraph, MultiDiGraph
```

### Application Point

```python
# src/server/initialization.py
from src.utils.lightrag_multidigraph_fix import apply_multidigraph_fix

async def initialize_raganything():
    # ... RAG-Anything initialization ...

    # Apply MultiDiGraph compatibility fix for LightRAG 1.4.9.3
    apply_multidigraph_fix()  # ← Monkey patch applied here

    return _rag_anything
```

---

## How Monkey Patching Works

### Process Flow

```
1. Server Startup (app.py)
   ↓
2. initialize_raganything() called
   ↓
3. RAG-Anything instance created (pip package)
   ↓
4. LightRAG initialized inside RAG-Anything
   ↓
5. apply_multidigraph_fix() executes  ← PATCH APPLIED
   |  ├─ Import NetworkXStorage from pip-installed package
   |  ├─ Save original method reference
   |  └─ Replace get_knowledge_graph() method with fixed version
   ↓
6. Server ready - all subsequent calls use patched method
```

### In-Memory Modification

```python
def apply_multidigraph_fix():
    from lightrag.kg.networkx_impl import NetworkXStorage

    # 1. Store original for potential rollback
    if not hasattr(NetworkXStorage, '_original_get_knowledge_graph'):
        NetworkXStorage._original_get_knowledge_graph = NetworkXStorage.get_knowledge_graph

    # 2. Replace method in-memory (NO disk files modified)
    NetworkXStorage.get_knowledge_graph = fixed_get_knowledge_graph

    logger.info("Applied MultiDiGraph fix to LightRAG NetworkXStorage.get_knowledge_graph()")
```

**Key Properties**:

- ✅ **Runtime only**: No pip package files modified on disk
- ✅ **Applied once**: Affects all NetworkXStorage instances created afterwards
- ✅ **Scoped**: Only replaces ONE method (`get_knowledge_graph`)
- ✅ **Reversible**: Original method stored for potential rollback
- ✅ **Transparent**: LightRAG code doesn't know it's been patched

---

## Why It's Called "Monkey Patching"

Etymology: "Guerrilla patching" → sounds like "gorilla" → monkey 🐒

**Definition**: Dynamic runtime modification of code behavior without altering source files.

**Common Use Cases**:

- Temporary workarounds for library bugs
- Adding functionality to closed-source packages
- Hot-fixing production issues without redeployment
- Testing/mocking in unit tests

---

## Upstream Fix Plan

### Option 1: Submit PR to LightRAG (RECOMMENDED)

**File to modify**: `lightrag/kg/networkx_impl.py` (lines 445-454)

```python
# CURRENT (buggy):
for edge in subgraph.edges():
    source, target = edge
    if str(source) > str(target):
        source, target = target, source
    edge_id = f"{source}-{target}"
    if edge_id in seen_edges:
        continue
    edge_data = dict(subgraph.edges[edge])  # ❌ FAILS

# PROPOSED FIX:
for source, target, edge_data in subgraph.edges(data=True):
    if str(source) > str(target):
        source, target = target, source
    edge_id = f"{source}-{target}"
    if edge_id in seen_edges:
        continue
    # edge_data already a dict from .edges(data=True)  # ✅ WORKS
```

**Benefits**:

- Works for ALL NetworkX graph types (Graph, DiGraph, MultiGraph, MultiDiGraph)
- Cleaner code (no indexing needed)
- Better performance (no dict conversion)

### Option 2: LightRAG switches to simple `DiGraph`

Our GraphML uses `MultiDiGraph` because RAG-Anything sets `edgedefault="directed"` and NetworkX interprets this as MultiDiGraph. However:

- We don't use multi-edges (multiple edges between same nodes)
- Simple `DiGraph` would work fine and avoid the bug entirely

### Option 3: NetworkX fixes the bug

Unlikely - this might be intended behavior for edge accessor consistency.

---

## GitHub Issue Template

If you'd like to submit this to LightRAG, here's the issue template:

### Title

```
Bug: get_knowledge_graph() fails with MultiDiGraph - ValueError unpacking edge tuple
```

### Description

````markdown
## Bug Description

The `get_knowledge_graph()` method in `NetworkXStorage` fails when the graph is a `MultiDiGraph` due to incorrect edge access pattern on line 454.

## Environment

- LightRAG version: 1.4.9.3
- NetworkX version: 3.x
- Graph type: MultiDiGraph with directed edges

## Error

```
ValueError: not enough values to unpack (expected 3, got 2)
File: networkx/classes/reportviews.py, line 1368
```

## Root Cause

Line 454 in `lightrag/kg/networkx_impl.py`:

```python
for edge in subgraph.edges():
    source, target = edge
    edge_data = dict(subgraph.edges[edge])  # ❌ Fails for MultiDiGraph
```

When iterating `subgraph.edges()`, we get 2-tuples `(u, v)`, but accessing `subgraph.edges[edge]` on a MultiDiGraph triggers NetworkX's `__getitem__` which expects 3-tuple `(u, v, k)` indexing.

## Reproduction Steps

1. Load a MultiDiGraph into LightRAG storage (e.g., from GraphML with `edgedefault="directed"`)
2. Call `get_knowledge_graph(node_label="*")`
3. Observe ValueError at edge iteration

## Proposed Fix

Replace edge indexing with direct iteration:

```python
for source, target, edge_data in subgraph.edges(data=True):
    # edge_data is already a dict, no indexing needed
    # Works for all NetworkX graph types
```

## Benefits of Fix

- ✅ Works for all graph types: Graph, DiGraph, MultiGraph, MultiDiGraph
- ✅ Cleaner code (no manual dict conversion)
- ✅ Better performance (avoids redundant indexing)
- ✅ Follows NetworkX best practices

## Temporary Workaround

We've implemented a runtime monkey patch that replaces the method. This confirms the fix works correctly in production.
````

---

## When to Remove This Patch

**Remove when**:

1. LightRAG releases a version with the upstream fix
2. We upgrade to that version
3. Testing confirms Knowledge Graph works without the patch

**How to remove**:

1. Delete `src/utils/lightrag_multidigraph_fix.py`
2. Remove import from `src/server/initialization.py`
3. Remove `apply_multidigraph_fix()` call
4. Test Knowledge Graph visualization
5. Commit with message: "Remove: MultiDiGraph monkey patch (fixed upstream in LightRAG vX.X.X)"

---

## Testing the Fix

### Before Fix

```bash
# Start server without patch
# Navigate to http://localhost:9621/webui
# Open Knowledge Graph
# Result: ValueError, blank screen
```

### After Fix

```bash
# Start server with patch
# Navigate to http://localhost:9621/webui
# Open Knowledge Graph
# Result: Graph loads successfully (1000 nodes, 2769 edges)
```

---

## Related Documentation

- **NetworkX MultiDiGraph docs**: https://networkx.org/documentation/stable/reference/classes/multidigraph.html
- **LightRAG GitHub**: https://github.com/HKUDS/LightRAG
- **RAG-Anything GitHub**: https://github.com/HKUDS/RAG-Anything

---

**Last Updated**: January 2025  
**Patch Version**: 1.0  
**Impact**: Knowledge Graph visualization only (query/search unaffected)
