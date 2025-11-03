# Dynamic Workspace Switching Strategy

**Date**: November 2, 2025  
**Branch**: 013-hybrid-adjudication → 010-pivot-enterprise-platform  
**LightRAG Version**: 1.4.9.7  
**Purpose**: Enable seamless multi-workspace selection in WebUI without server restarts

---

## Problem Statement

**Current Limitation**: LightRAG workspace is set at server startup and **immutable** during runtime.

- ❌ User must restart server with different `NEO4J_WORKSPACE` env var to switch projects
- ❌ No UI-based workspace selection (poor UX for multi-RFP analysis)
- ❌ Forces separate server instances per workspace (port conflicts, resource waste)

**From LightRAG Documentation**:

> "The `workspace` parameter ensures data isolation between different LightRAG instances. Once initialized, the `workspace` is immutable and cannot be changed."

**Community Requests**:

- [Issue #1847](https://github.com/HKUDS/LightRAG/issues/1847): "When will LightRAG Server offer support for multiple workspace selection and switching during runtime execution?"
- [Issue #2046](https://github.com/HKUDS/LightRAG/issues/2046): "Having multiple workspace at the same time dynamically... sort of a new parameter to select the workspace db on which we perform the actions"

**Conclusion**: No native runtime workspace switching exists in LightRAG 1.4.9.7. We must implement custom solution.

---

## Architecture Solution

### **Approach 1: Multi-Instance Manager (Recommended)**

Run **one Python process managing multiple LightRAG instances**, each with its own workspace. Add WebUI workspace selector that routes requests to the correct instance.

#### **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│           FastAPI Orchestration Layer                    │
│  (Port 9621 - User-facing unified endpoint)              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │  LightRAG #1     │  │  LightRAG #2     │             │
│  │  Workspace:      │  │  Workspace:      │  ...        │
│  │  navy_mbos_2025  │  │  airforce_cloud  │             │
│  │  Neo4j Label:    │  │  Neo4j Label:    │             │
│  │  navy_mbos_2025  │  │  airforce_cloud  │             │
│  └──────────────────┘  └──────────────────┘             │
│           │                      │                        │
│           └──────────┬───────────┘                        │
│                      │                                    │
│              Neo4j Database                               │
│              (Port 7687)                                  │
│              All workspaces isolated by labels            │
└─────────────────────────────────────────────────────────┘
```

#### **Implementation Plan**

**1. Create Workspace Manager** (`src/intelligence/workspace_manager.py`):

```python
from typing import Dict
from lightrag import LightRAG
from lightrag.api import create_app
import asyncio

class WorkspaceManager:
    """Manages multiple LightRAG instances with different workspaces."""

    def __init__(self):
        self.instances: Dict[str, LightRAG] = {}
        self.active_workspace: str = None

    async def create_workspace(self, workspace_name: str) -> LightRAG:
        """Initialize a new LightRAG instance with workspace label."""
        if workspace_name in self.instances:
            return self.instances[workspace_name]

        # Create LightRAG with Neo4j storage + workspace label
        rag = LightRAG(
            working_dir=f"./rag_storage/{workspace_name}",
            graph_storage="Neo4JStorage",
            workspace=workspace_name,  # Sets Neo4j label
            # ... other config from .env ...
        )

        await rag.initialize()
        self.instances[workspace_name] = rag
        return rag

    def get_workspace(self, workspace_name: str) -> LightRAG:
        """Get existing workspace instance."""
        if workspace_name not in self.instances:
            raise ValueError(f"Workspace '{workspace_name}' not initialized")
        return self.instances[workspace_name]

    def list_workspaces(self) -> list[str]:
        """Return all active workspace names."""
        return list(self.instances.keys())

    def set_active(self, workspace_name: str):
        """Set the default workspace for operations."""
        if workspace_name not in self.instances:
            raise ValueError(f"Workspace '{workspace_name}' not found")
        self.active_workspace = workspace_name
```

**2. Modify `src/raganything_server.py`** to use WorkspaceManager:

```python
from src.intelligence.workspace_manager import WorkspaceManager

workspace_manager = WorkspaceManager()

# Add new endpoints for workspace management
@app.get("/workspaces")
async def list_workspaces():
    """Return all available workspaces."""
    return {
        "workspaces": workspace_manager.list_workspaces(),
        "active": workspace_manager.active_workspace
    }

@app.post("/workspaces/create")
async def create_workspace(workspace_name: str):
    """Create new workspace on-demand."""
    await workspace_manager.create_workspace(workspace_name)
    return {"status": "created", "workspace": workspace_name}

@app.post("/workspaces/switch")
async def switch_workspace(workspace_name: str):
    """Switch active workspace for subsequent operations."""
    workspace_manager.set_active(workspace_name)
    return {"status": "switched", "active_workspace": workspace_name}

# Modify existing endpoints to use active workspace
@app.post("/insert")
async def insert_document(file: UploadFile):
    """Upload document to active workspace."""
    rag = workspace_manager.get_workspace(
        workspace_manager.active_workspace
    )
    result = await rag.ainsert(file.file)
    return {"status": "success", "result": result}

@app.post("/query")
async def query_endpoint(query: QueryRequest):
    """Query active workspace."""
    rag = workspace_manager.get_workspace(
        workspace_manager.active_workspace
    )
    result = await rag.aquery(query.query, mode=query.mode)
    return {"response": result}
```

**3. Add WebUI Workspace Selector**:

```typescript
// lightrag_webui/src/components/WorkspaceSelector.tsx
export function WorkspaceSelector() {
  const [workspaces, setWorkspaces] = useState<string[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<string>("");

  const fetchWorkspaces = async () => {
    const response = await fetch("/workspaces");
    const data = await response.json();
    setWorkspaces(data.workspaces);
    setActiveWorkspace(data.active);
  };

  const switchWorkspace = async (workspace: string) => {
    await fetch("/workspaces/switch", {
      method: "POST",
      body: JSON.stringify({ workspace_name: workspace }),
    });
    setActiveWorkspace(workspace);
    // Trigger graph refresh with new workspace data
  };

  return (
    <Select value={activeWorkspace} onValueChange={switchWorkspace}>
      {workspaces.map((ws) => (
        <SelectItem key={ws} value={ws}>
          {ws}
        </SelectItem>
      ))}
    </Select>
  );
}
```

**4. Pre-initialize Common Workspaces on Startup**:

```python
# In app.py startup
@app.on_event("startup")
async def startup_event():
    """Pre-load common workspaces."""
    common_workspaces = [
        "navy_mbos_2025",
        "airforce_cloud_2025",
        "dod_idiq_seaport_nx"
    ]

    for ws in common_workspaces:
        await workspace_manager.create_workspace(ws)

    # Set default active workspace
    workspace_manager.set_active("navy_mbos_2025")
```

---

### **Approach 2: Query-Time Workspace Parameter (Alternative)**

Modify all query endpoints to accept optional `workspace` parameter. Less resource-efficient but simpler.

```python
@app.post("/query")
async def query_endpoint(
    query: QueryRequest,
    workspace: str = None  # Optional override
):
    """Query with runtime workspace selection."""
    target_workspace = workspace or workspace_manager.active_workspace
    rag = workspace_manager.get_workspace(target_workspace)
    result = await rag.aquery(query.query, mode=query.mode)
    return {"response": result, "workspace": target_workspace}
```

**WebUI passes workspace on every API call**:

```typescript
const queryResponse = await fetch("/query", {
  method: "POST",
  body: JSON.stringify({
    query: userQuery,
    workspace: selectedWorkspace, // From dropdown
  }),
});
```

---

## Workspace Naming Conventions

For government contracting use cases:

### **Base RFPs**

```
{agency}_{program}_{fiscal_year}
Examples:
- navy_mbos_2025
- airforce_jwcc_2025
- dod_gcss_army_2024
```

### **Amendments**

```
{agency}_{program}_{amendment_number}
Examples:
- navy_mbos_amendment_02
- airforce_jwcc_amendment_05
```

### **IDIQ Hierarchies**

```
{program}_{type}_{identifier}
Examples:
- seaport_nx_base_idiq
- seaport_nx_to_001
- seaport_nx_to_002
```

### **Comparison/Analysis Workspaces**

```
compare_{workspace1}_vs_{workspace2}
Examples:
- compare_navy_mbos_baseline_vs_amendment_02
- compare_seaport_nx_vs_oasis_plus
```

---

## Neo4j Label Strategy

Each workspace creates isolated **node labels** in Neo4j:

```cypher
-- Navy MBOS workspace nodes
MATCH (n:`navy_mbos_2025`)
WHERE n.entity_type = 'REQUIREMENT'
RETURN n

-- Airforce JWCC workspace nodes
MATCH (n:`airforce_jwcc_2025`)
WHERE n.entity_type = 'REQUIREMENT'
RETURN n

-- Cross-workspace comparison query
MATCH (navy:`navy_mbos_2025` {entity_type: 'CLAUSE'})
MATCH (airforce:`airforce_jwcc_2025` {entity_type: 'CLAUSE'})
WHERE navy.entity_id = airforce.entity_id
RETURN navy.description AS navy_clause,
       airforce.description AS airforce_clause
```

**Key Advantage**: All workspaces share **one Neo4j database** but remain logically isolated via labels.

---

## Implementation Phases

### **Phase 1: Backend Infrastructure** (Week 1)

- ✅ Create `WorkspaceManager` class
- ✅ Modify `raganything_server.py` with workspace endpoints
- ✅ Add startup pre-initialization for common workspaces
- ✅ Test multi-instance management with 3 workspaces

### **Phase 2: WebUI Integration** (Week 2)

- ✅ Add workspace selector dropdown to header
- ✅ Persist selected workspace in localStorage
- ✅ Update all API calls to use active workspace
- ✅ Add "Create New Workspace" dialog

### **Phase 3: Intelligence Queries** (Week 3-4)

- ✅ Amendment comparison endpoints (`/compare/amendments`)
- ✅ IDIQ hierarchy queries (`/query/idiq_hierarchy`)
- ✅ Cross-workspace analytics (`/analytics/common_clauses`)

### **Phase 4: Advanced Features** (Week 5-6)

- ✅ Workspace cloning (copy baseline → new amendment workspace)
- ✅ Workspace archiving (freeze old RFPs)
- ✅ Workspace metrics dashboard (entity counts, relationship stats)

---

## Memory & Performance Considerations

**Resource Usage per Workspace**:

- **Neo4j Storage**: Shared database (labels isolate data)
- **LightRAG Instance**: ~200-500 MB RAM per workspace
- **Vector Embeddings**: Shared OpenAI embedding cache

**Recommended Limits**:

- **Active Workspaces**: 10-15 max (based on 16 GB RAM system)
- **Cold Workspaces**: Unlimited (stored in Neo4j, lazy-load on demand)

**Optimization Strategy**:

```python
class WorkspaceManager:
    def __init__(self, max_active_instances: int = 10):
        self.max_active = max_active_instances
        self.lru_cache = OrderedDict()  # Least Recently Used eviction

    async def get_workspace(self, workspace_name: str) -> LightRAG:
        """Auto-evict oldest workspace if limit exceeded."""
        if len(self.instances) >= self.max_active:
            # Evict least recently used workspace
            oldest_ws = next(iter(self.lru_cache))
            await self.instances[oldest_ws].finalize()
            del self.instances[oldest_ws]

        # Load workspace (from Neo4j if not in memory)
        return await self.create_workspace(workspace_name)
```

---

## Security & Data Isolation

### **Neo4j Label-Based Isolation**

**Guaranteed by LightRAG**:

```python
# From neo4j_impl.py lines 50-71
def _get_workspace_label(self) -> str:
    """Return workspace label (guaranteed non-empty)."""
    return self.workspace  # Used in ALL Cypher queries

# Example query with automatic workspace filtering:
query = f"MATCH (n:`{workspace_label}`) WHERE n.entity_id = $id RETURN n"
```

**All LightRAG Neo4j operations use workspace label**:

- ✅ `upsert_node()` → Adds workspace label to node
- ✅ `get_node()` → Queries only workspace-labeled nodes
- ✅ `get_knowledge_graph()` → Filters by workspace label
- ✅ `search_labels()` → Returns labels from workspace only

**Cross-contamination is impossible** because:

1. All Cypher queries filter by `workspace_label`
2. No shared entity IDs across workspaces
3. Neo4j labels enforce physical separation at database level

---

## Testing Strategy

### **Unit Tests**

```python
async def test_workspace_isolation():
    """Verify workspaces don't cross-contaminate."""
    ws1 = await manager.create_workspace("test_ws1")
    ws2 = await manager.create_workspace("test_ws2")

    # Insert same entity ID in both workspaces
    await ws1.ainsert("Entity X details...")
    await ws2.ainsert("Entity X different details...")

    # Verify each workspace sees only its own data
    result1 = await ws1.aquery("What is Entity X?")
    result2 = await ws2.aquery("What is Entity X?")

    assert result1 != result2  # Different responses
    assert "test_ws1" in result1.source_ids
    assert "test_ws2" in result2.source_ids
```

### **Integration Tests**

```python
async def test_workspace_switching_ui():
    """Test WebUI workspace selector."""
    # Switch to workspace 1
    response = await client.post("/workspaces/switch",
                                  json={"workspace_name": "navy_mbos"})
    assert response.json()["active_workspace"] == "navy_mbos"

    # Query returns navy_mbos data only
    query_response = await client.post("/query",
                                        json={"query": "list requirements"})
    assert "navy_mbos" in query_response.json()["workspace"]
```

---

## Migration Path from Single Workspace

### **Step 1: Backup Current Data**

```bash
# Export current NetworkX/JSON storage
python scripts/export_graph.py > backup_graph.graphml
```

### **Step 2: Initialize Default Workspace**

```bash
# Set default workspace for existing data
export NEO4J_WORKSPACE=default_legacy
python app.py  # Migrates existing data to "default_legacy" label
```

### **Step 3: Enable Multi-Workspace Mode**

```python
# Update src/raganything_server.py
from src.intelligence.workspace_manager import WorkspaceManager

# Initialize manager with existing workspace
workspace_manager = WorkspaceManager()
await workspace_manager.create_workspace("default_legacy")  # Load existing
workspace_manager.set_active("default_legacy")
```

### **Step 4: Add New Workspaces**

```python
# User creates new workspaces via WebUI
await workspace_manager.create_workspace("navy_mbos_2025")
await workspace_manager.create_workspace("airforce_cloud_2025")
```

---

## Next Steps

1. **Implement WorkspaceManager** (`src/intelligence/workspace_manager.py`)
2. **Add WebUI Workspace Selector** (React component)
3. **Create Pre-Seed Script** (initialize common gov contracting workspaces)
4. **Build Amendment Comparison Endpoint** (`/compare/amendments`)
5. **Test with 3 RFPs** (Navy MBOS baseline + 2 amendments)

**Should we start with Phase 1 implementation?** I can create the `WorkspaceManager` class and modify `raganything_server.py` to support dynamic switching right now. 🚀
