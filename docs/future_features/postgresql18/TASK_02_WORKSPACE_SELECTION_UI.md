# TASK 02: Workspace Selection UI for Multi-Document Intelligence

**Feature**: WebUI workspace dropdown for RFP/Amendment/Proposal/Feedback association  
**Branch**: Branch 010 (prerequisite for event sourcing)  
**Status**: Implementation Required (URGENT - Blocks Branch 011)  
**Estimated Time**: 12-16 hours  
**Date Created**: October 20, 2025

---

## 🎯 Problem Statement

### Current System Gap

**User Question**: "How will the system know which workspace [amendments, feedback, proposals] are associated with automatically when using WebUI upload?"

**Current Limitation**:

- RAG-Anything uses `working_dir` (file path: `./rag_storage/`) but **does NOT expose LightRAG's `workspace` parameter**
- All documents processed into SAME PostgreSQL workspace (no row-level isolation)
- No UI for users to select which RFP an amendment/proposal belongs to

**Example Scenario**:

```
User uploads:
1. Navy_MBOS_RFP.pdf → Processes to workspace = ??? (defaults to hardcoded value)
2. Navy_MBOS_Amendment_0001.pdf → Processes to workspace = ??? (same hardcoded value)
3. Army_Comms_RFP.pdf → Processes to workspace = ??? (SAME hardcoded value!)
```

**Result**: All 3 RFPs mix in PostgreSQL with NO isolation → Event sourcing fails!

---

## 💡 Solution: Extend RAG-Anything with Workspace Support

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ WebUI (Upload Form)                                          │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Select RFP file: [Browse...]                          │   │
│ │ Workspace: [Dropdown: navy_mbos_2025 ▼]              │   │
│ │            - navy_mbos_2025                           │   │
│ │            - army_comms_2025                          │   │
│ │            - + Create New Workspace                   │   │
│ │ [Upload & Process]                                     │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Server (/insert endpoint)                            │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ 1. Extract workspace from form data                   │   │
│ │ 2. Get/Create RAGAnything instance for workspace      │   │
│ │ 3. Process document with workspace-specific instance  │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Extended RAGAnything (with workspace parameter)              │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ RAGAnythingConfig:                                     │   │
│ │   - working_dir = "./rag_storage"                     │   │
│ │   - workspace = "navy_mbos_2025"  ← NEW PARAMETER     │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LightRAG (with workspace support - EXISTING)                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ PGKVStorage: workspace="navy_mbos_2025"               │   │
│ │ PGVectorStorage: workspace="navy_mbos_2025"           │   │
│ │ PGGraphStorage: workspace="navy_mbos_2025"            │   │
│ │                                                        │   │
│ │ PostgreSQL Queries:                                    │   │
│ │ SELECT * FROM entities WHERE workspace='navy_mbos_2025'│   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Implementation Plan

### Step 1: Extend RAGAnythingConfig (Minimal Monkey Patch)

**File**: `src/core/extended_raganything_config.py` (NEW FILE)

```python
"""
Extended RAGAnything configuration with LightRAG workspace support

This module extends the base RAGAnythingConfig to expose LightRAG's workspace
parameter, enabling row-level isolation in PostgreSQL storage.
"""

from raganything import RAGAnythingConfig as BaseRAGAnythingConfig
from dataclasses import dataclass, field
import os

@dataclass
class ExtendedRAGAnythingConfig(BaseRAGAnythingConfig):
    """
    RAGAnything configuration extended with workspace parameter

    Adds workspace support for multi-tenant PostgreSQL storage without
    modifying the upstream RAG-Anything library.
    """

    workspace: str = field(
        default_factory=lambda: os.getenv("WORKSPACE", "default")
    )
    """
    Workspace identifier for data isolation in PostgreSQL.

    Use cases:
    - Multi-RFP storage: navy_mbos_2025, army_comms_2025, air_force_cloud_2025
    - Event sourcing: navy_mbos_2025_amendment_001, navy_mbos_2025_proposal
    - Testing: test_workspace_1, test_workspace_2

    Default: "default" (reads from WORKSPACE env var if set)
    """

    def get_lightrag_init_params(self) -> dict:
        """
        Get parameters for LightRAG initialization including workspace

        Returns:
            dict: Parameters to pass to LightRAG.__init__()
        """
        # Get base parameters from parent config
        base_params = {
            "working_dir": self.working_dir,
            # Add other base parameters as needed
        }

        # Add workspace parameter
        base_params["workspace"] = self.workspace

        return base_params
```

**Rationale**:

- ✅ Grounded in existing library (LightRAG already has workspace parameter)
- ✅ Minimal code (~40 lines)
- ✅ No forking of RAG-Anything (composition pattern)
- ✅ Clean separation of concerns

---

### Step 2: Workspace Instance Manager

**File**: `src/core/workspace_manager.py` (NEW FILE)

```python
"""
Workspace instance manager for multi-tenant RAGAnything instances

Handles workspace-specific RAGAnything instances with proper initialization
and cleanup. Solves the immutability constraint of LightRAG workspace parameter.
"""

from typing import Dict, Optional
from raganything import RAGAnything
from .extended_raganything_config import ExtendedRAGAnythingConfig
import logging

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """
    Manages multiple RAGAnything instances, one per workspace

    LightRAG workspace is immutable after initialization, so we maintain
    a pool of instances (one per workspace) and lazy-initialize on demand.
    """

    def __init__(self):
        """Initialize workspace manager"""
        self._instances: Dict[str, RAGAnything] = {}
        self._base_config: Optional[ExtendedRAGAnythingConfig] = None
        logger.info("WorkspaceManager initialized")

    def set_base_config(self, config: ExtendedRAGAnythingConfig):
        """
        Set base configuration (shared across all workspaces)

        Args:
            config: Extended config with workspace parameter
        """
        self._base_config = config
        logger.info(f"Base config set: working_dir={config.working_dir}")

    async def get_instance(self, workspace: str) -> RAGAnything:
        """
        Get or create RAGAnything instance for workspace

        Args:
            workspace: Workspace identifier (e.g., "navy_mbos_2025")

        Returns:
            RAGAnything instance configured for workspace

        Raises:
            ValueError: If base config not set
        """
        if self._base_config is None:
            raise ValueError("Base config not set. Call set_base_config() first.")

        # Return existing instance if available
        if workspace in self._instances:
            logger.debug(f"Returning existing instance for workspace: {workspace}")
            return self._instances[workspace]

        # Create new instance for workspace
        logger.info(f"Creating new RAGAnything instance for workspace: {workspace}")

        # Clone base config and override workspace
        workspace_config = ExtendedRAGAnythingConfig(
            working_dir=self._base_config.working_dir,
            workspace=workspace,
            parser=self._base_config.parser,
            parse_method=self._base_config.parse_method,
            enable_image_processing=self._base_config.enable_image_processing,
            enable_table_processing=self._base_config.enable_table_processing,
            enable_equation_processing=self._base_config.enable_equation_processing,
            # Copy other config parameters as needed
        )

        # Initialize RAGAnything with workspace-specific config
        rag_instance = RAGAnything(config=workspace_config)

        # CRITICAL: Pass workspace to LightRAG initialization
        # This is done in RAGAnything.__post_init__() when it creates LightRAG instance
        # We ensure workspace parameter flows through via config.get_lightrag_init_params()

        # Store instance
        self._instances[workspace] = rag_instance
        logger.info(f"RAGAnything instance created for workspace: {workspace}")

        return rag_instance

    def list_workspaces(self) -> list[str]:
        """
        List all active workspaces

        Returns:
            List of workspace identifiers
        """
        return list(self._instances.keys())

    async def close_workspace(self, workspace: str):
        """
        Close and remove workspace instance

        Args:
            workspace: Workspace identifier to close
        """
        if workspace in self._instances:
            instance = self._instances[workspace]
            await instance.close()  # Cleanup resources
            del self._instances[workspace]
            logger.info(f"Closed workspace: {workspace}")

    async def close_all(self):
        """Close all workspace instances"""
        for workspace in list(self._instances.keys()):
            await self.close_workspace(workspace)
        logger.info("All workspaces closed")


# Global singleton instance
_workspace_manager = WorkspaceManager()

def get_workspace_manager() -> WorkspaceManager:
    """Get global workspace manager instance"""
    return _workspace_manager
```

**Rationale**:

- ✅ Solves workspace immutability constraint (one instance per workspace)
- ✅ Lazy initialization (only create instances when needed)
- ✅ Memory efficient (reuse instances across requests)
- ✅ Clean shutdown (proper resource cleanup)

---

### Step 3: Update FastAPI Server Endpoints

**File**: `src/raganything_server.py` (MODIFICATIONS)

```python
# Add imports at top
from src.core.workspace_manager import get_workspace_manager
from src.core.extended_raganything_config import ExtendedRAGAnythingConfig
from typing import Optional

# Initialize workspace manager at startup
workspace_manager = get_workspace_manager()

# Modify /insert endpoint to accept workspace parameter
@app.post("/insert")
async def insert_document(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
    workspace: Optional[str] = Form(None)  # NEW PARAMETER
):
    """
    Insert document with optional workspace selection

    Args:
        file: Document file to process
        mode: Processing mode (auto, manual, etc.)
        workspace: Workspace identifier (e.g., "navy_mbos_2025")
                   If None, uses WORKSPACE env var or "default"
    """
    try:
        # Determine workspace
        if workspace is None:
            workspace = os.getenv("WORKSPACE", "default")

        logger.info(f"Processing document in workspace: {workspace}")

        # Get workspace-specific RAGAnything instance
        rag = await workspace_manager.get_instance(workspace)

        # Save uploaded file
        file_path = f"./inputs/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Process document with workspace-specific instance
        await rag.process_document_complete(file_path=file_path)

        # Phase 6 post-processing (if enabled)
        if mode == "auto":
            await run_phase_6_pipeline(rag, file_path, workspace)

        return {
            "status": "success",
            "workspace": workspace,
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Add endpoint to list available workspaces
@app.get("/workspaces")
async def list_workspaces():
    """
    List all available workspaces from PostgreSQL

    Returns:
        List of workspace identifiers with metadata
    """
    try:
        # Query PostgreSQL for distinct workspaces
        # This assumes PostgreSQL storage is configured (Branch 010)

        # For now, return active workspaces from manager
        active_workspaces = workspace_manager.list_workspaces()

        # TODO (Branch 010): Query PostgreSQL for ALL workspaces
        # SELECT DISTINCT workspace FROM entities ORDER BY workspace;

        return {
            "workspaces": active_workspaces,
            "count": len(active_workspaces)
        }

    except Exception as e:
        logger.error(f"Error listing workspaces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Step 4: WebUI Workspace Dropdown (Frontend)

**File**: `src/server/webui/upload.html` (MODIFICATIONS)

```html
<!-- Workspace selection dropdown (add before file upload) -->
<div class="form-group">
  <label for="workspace-select">
    Workspace:
    <span class="help-text">Select which RFP this document belongs to</span>
  </label>
  <select id="workspace-select" class="form-control" required>
    <option value="">-- Select or create workspace --</option>
    <!-- Options populated dynamically from /workspaces endpoint -->
  </select>
  <div class="workspace-actions">
    <button
      type="button"
      id="create-workspace-btn"
      class="btn btn-secondary btn-sm"
    >
      + Create New Workspace
    </button>
  </div>
</div>

<!-- File upload (existing) -->
<div class="form-group">
  <label for="file-upload">Select Document:</label>
  <input
    type="file"
    id="file-upload"
    class="form-control"
    accept=".pdf,.docx,.doc"
    required
  />
</div>

<!-- Upload button (existing) -->
<button type="submit" id="upload-btn" class="btn btn-primary">
  Upload & Process
</button>

<script>
  // Load available workspaces on page load
  async function loadWorkspaces() {
    try {
      const response = await fetch("/workspaces");
      const data = await response.json();

      const select = document.getElementById("workspace-select");

      // Clear existing options (except first)
      while (select.options.length > 1) {
        select.remove(1);
      }

      // Add workspaces
      data.workspaces.forEach((workspace) => {
        const option = document.createElement("option");
        option.value = workspace;
        option.textContent = workspace;
        select.appendChild(option);
      });
    } catch (error) {
      console.error("Error loading workspaces:", error);
    }
  }

  // Create new workspace modal
  document
    .getElementById("create-workspace-btn")
    .addEventListener("click", () => {
      const workspaceName = prompt(
        "Enter new workspace name (e.g., navy_mbos_2025):"
      );

      if (workspaceName && workspaceName.trim()) {
        const sanitized = workspaceName
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9_-]/g, "_");

        // Add to dropdown
        const select = document.getElementById("workspace-select");
        const option = document.createElement("option");
        option.value = sanitized;
        option.textContent = sanitized;
        option.selected = true;
        select.appendChild(option);
      }
    });

  // Modify upload form submission to include workspace
  document
    .getElementById("upload-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById("file-upload");
      const workspace = document.getElementById("workspace-select").value;

      if (!workspace) {
        alert("Please select a workspace");
        return;
      }

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);
      formData.append("workspace", workspace);
      formData.append("mode", "auto");

      try {
        const response = await fetch("/insert", {
          method: "POST",
          body: formData,
        });

        const result = await response.json();

        if (response.ok) {
          alert(`✅ Document processed in workspace: ${result.workspace}`);
        } else {
          alert(`❌ Error: ${result.detail}`);
        }
      } catch (error) {
        console.error("Upload error:", error);
        alert(`❌ Upload failed: ${error.message}`);
      }
    });

  // Load workspaces on page load
  document.addEventListener("DOMContentLoaded", loadWorkspaces);
</script>

<style>
  .form-group {
    margin-bottom: 20px;
  }

  .help-text {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
  }

  .workspace-actions {
    margin-top: 8px;
  }
</style>
```

---

## 📋 Implementation Checklist

### Prerequisites

- [ ] PostgreSQL 18 running locally (TASK_01 complete)
- [ ] Current system using LightRAG with PostgreSQL storage
- [ ] `.env` file has `WORKSPACE` variable defined

### Week 2 Implementation

**Day 1-2: Backend Extensions** (6-8 hours)

- [ ] Create `src/core/extended_raganything_config.py`
  - [ ] Extend RAGAnythingConfig with workspace parameter
  - [ ] Add `get_lightrag_init_params()` method
  - [ ] Test: Verify workspace passed to LightRAG init
- [ ] Create `src/core/workspace_manager.py`
  - [ ] Implement WorkspaceManager class
  - [ ] Add lazy instance initialization
  - [ ] Add workspace cleanup methods
  - [ ] Test: Create/get/close workspace instances

**Day 3-4: API Integration** (4-6 hours)

- [ ] Modify `src/raganything_server.py`
  - [ ] Add workspace parameter to `/insert` endpoint
  - [ ] Initialize workspace_manager at startup
  - [ ] Add `/workspaces` endpoint
  - [ ] Test: Upload document with workspace parameter
- [ ] Test workspace isolation
  - [ ] Upload Navy RFP to `navy_mbos_2025`
  - [ ] Upload Army RFP to `army_comms_2025`
  - [ ] Verify PostgreSQL: entities isolated by workspace

**Day 5-6: Frontend UI** (2-4 hours)

- [ ] Modify WebUI upload form
  - [ ] Add workspace dropdown
  - [ ] Add "Create New Workspace" button
  - [ ] Load workspaces from `/workspaces` endpoint
  - [ ] Update form submission with workspace
  - [ ] Test: Select workspace, upload, verify

**Day 7: Integration Testing** (2-3 hours)

- [ ] End-to-end workflow test
  - [ ] Create workspace "test_rfp_1"
  - [ ] Upload RFP to "test_rfp_1"
  - [ ] Create workspace "test_rfp_2"
  - [ ] Upload different RFP to "test_rfp_2"
  - [ ] Query PostgreSQL: Verify isolation
- [ ] Performance validation
  - [ ] Processing time unchanged (≤69 seconds)
  - [ ] No memory leaks with multiple workspaces
  - [ ] Workspace switching instantaneous

---

## 🧪 Testing Scenarios

### Test 1: Basic Workspace Isolation

```python
# Test script: tests/test_workspace_isolation.py

import asyncio
from src.core.workspace_manager import get_workspace_manager
from src.core.extended_raganything_config import ExtendedRAGAnythingConfig

async def test_workspace_isolation():
    """Verify workspace isolation in PostgreSQL"""

    manager = get_workspace_manager()

    # Set base config
    config = ExtendedRAGAnythingConfig(
        working_dir="./rag_storage",
        workspace="test_workspace_1"
    )
    manager.set_base_config(config)

    # Get instance for workspace 1
    rag1 = await manager.get_instance("test_workspace_1")

    # Process document in workspace 1
    await rag1.process_document_complete("./tests/fixtures/test_rfp_1.pdf")

    # Get instance for workspace 2
    rag2 = await manager.get_instance("test_workspace_2")

    # Process document in workspace 2
    await rag2.process_document_complete("./tests/fixtures/test_rfp_2.pdf")

    # Verify isolation in PostgreSQL
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Count entities in workspace 1
    cur.execute("SELECT COUNT(*) FROM entities WHERE workspace = %s", ("test_workspace_1",))
    count_1 = cur.fetchone()[0]

    # Count entities in workspace 2
    cur.execute("SELECT COUNT(*) FROM entities WHERE workspace = %s", ("test_workspace_2",))
    count_2 = cur.fetchone()[0]

    print(f"Workspace 1 entities: {count_1}")
    print(f"Workspace 2 entities: {count_2}")

    assert count_1 > 0, "Workspace 1 should have entities"
    assert count_2 > 0, "Workspace 2 should have entities"

    # Verify no cross-contamination
    cur.execute("""
        SELECT COUNT(*) FROM entities
        WHERE workspace NOT IN ('test_workspace_1', 'test_workspace_2')
    """)
    other_count = cur.fetchone()[0]
    assert other_count == 0, "No entities should exist in other workspaces"

    print("✅ Workspace isolation verified")

    # Cleanup
    await manager.close_all()
    cur.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_workspace_isolation())
```

---

### Test 2: WebUI Workflow

**Manual Test Steps**:

1. Start server: `python app.py`
2. Open WebUI: http://localhost:9621/webui
3. Create workspace:
   - Click "+ Create New Workspace"
   - Enter: `navy_mbos_2025`
4. Upload RFP:
   - Select workspace: `navy_mbos_2025`
   - Upload: `Navy_MBOS_RFP.pdf`
   - Wait for processing (69 seconds)
   - Verify success message
5. Verify in PostgreSQL:
   ```sql
   SELECT workspace, entity_name, entity_type
   FROM entities
   WHERE workspace = 'navy_mbos_2025'
   LIMIT 10;
   ```
6. Create second workspace:
   - Click "+ Create New Workspace"
   - Enter: `army_comms_2025`
7. Upload different RFP:
   - Select workspace: `army_comms_2025`
   - Upload: `Army_Comms_RFP.pdf`
   - Verify success
8. Query isolation:
   ```sql
   SELECT workspace, COUNT(*)
   FROM entities
   GROUP BY workspace;
   ```

**Expected Result**:

```
workspace         | count
------------------|-------
navy_mbos_2025    | 594
army_comms_2025   | 450
```

---

## 🔗 Integration with Event Sourcing (Branch 011)

### Workspace Naming Convention for Events

Once workspace selection UI is implemented, Branch 011 event sourcing will use workspace-based isolation:

```
Base RFP:
  workspace = "navy_mbos_2025"

Amendment 0001:
  workspace = "navy_mbos_2025_amendment_001"
  parent_workspace = "navy_mbos_2025"

Amendment 0002:
  workspace = "navy_mbos_2025_amendment_002"
  parent_workspace = "navy_mbos_2025_amendment_001"

Proposal Submission:
  workspace = "navy_mbos_2025_proposal"
  parent_workspace = "navy_mbos_2025_amendment_002"

Evaluation Feedback:
  workspace = "navy_mbos_2025_feedback"
  parent_workspace = "navy_mbos_2025_proposal"
```

**Benefit**: Each event gets isolated workspace → No contamination → Entity matching links across workspaces.

---

## ✅ Success Criteria

### Functional Requirements

- ✅ WebUI displays workspace dropdown
- ✅ Users can create new workspaces
- ✅ Document processing respects workspace selection
- ✅ PostgreSQL isolates entities by workspace
- ✅ `/workspaces` endpoint returns active workspaces

### Performance Requirements

- ✅ Processing time unchanged (≤69 seconds for Navy MBOS)
- ✅ Workspace switching instantaneous (≤100ms)
- ✅ No memory leaks with 10+ workspaces

### Data Integrity Requirements

- ✅ Entities in workspace A never visible in workspace B
- ✅ Workspace parameter persists in PostgreSQL
- ✅ LightRAG workspace immutability respected

---

## 📊 Code Complexity Estimate

| Component                     | Lines of Code | Complexity | Risk    |
| ----------------------------- | ------------- | ---------- | ------- |
| Extended RAGAnythingConfig    | 40            | Low        | Low     |
| WorkspaceManager              | 120           | Medium     | Low     |
| Server endpoint modifications | 80            | Low        | Low     |
| WebUI dropdown (HTML/JS)      | 100           | Medium     | Low     |
| Test suite                    | 150           | Low        | None    |
| **Total**                     | **490**       | **Low**    | **Low** |

**Rationale for Low Risk**:

- Leverages existing LightRAG workspace parameter (not custom isolation)
- Composition pattern (no library forking)
- Minimal changes to existing code
- Well-tested workspace support in LightRAG

---

## 🚀 Deployment Considerations

### Environment Variables

Add to `.env`:

```bash
# Workspace Configuration (Branch 010+)
WORKSPACE=default  # Default workspace for backwards compatibility
```

### Migration Path

**Existing Data** (pre-workspace):

```sql
-- Backfill workspace column for existing entities
UPDATE entities SET workspace = 'default' WHERE workspace IS NULL;
UPDATE relationships SET workspace = 'default' WHERE workspace IS NULL;
```

**New Data** (post-workspace):

- All new uploads require workspace selection
- Old data accessible in "default" workspace

---

## 🔗 Related Documentation

- `README.md` - Master plan and navigation
- `01_SCHEMA_DESIGN.md` - PostgreSQL schema (includes workspace column)
- `02_EVENT_SOURCING_ARCHITECTURE.md` - Event-based design (depends on workspace isolation)
- `TASK_01_LOCAL_SETUP.md` - PostgreSQL 18 installation (prerequisite)
- `TASK_03_SCHEMA_CREATION.md` - Schema creation (includes workspace column)

---

## 📝 Implementation Notes

### Why Not Use `working_dir` for Isolation?

**Problem**: RAG-Anything uses `working_dir` as file path (`./rag_storage/navy_mbos/`), but:

- ❌ File-based isolation doesn't work with PostgreSQL
- ❌ Multiple `working_dir` = multiple databases (not scalable)
- ❌ No way to query across workspaces (e.g., lessons learned)

**Solution**: Use LightRAG's `workspace` parameter for **logical** isolation in **one** PostgreSQL database.

### Why Global Workspace Manager?

**Problem**: LightRAG workspace is immutable after init.

**Options**:

1. ❌ Re-initialize RAGAnything on every request (slow, memory leak)
2. ❌ Fork RAG-Anything to make workspace mutable (high maintenance)
3. ✅ Maintain pool of instances (one per workspace) with lazy init

**Trade-off**: Uses more memory (~50MB per workspace) but enables instant workspace switching.

---

**Last Updated**: October 20, 2025  
**Status**: Ready for implementation (Week 2)  
**Dependencies**: TASK_01 (PostgreSQL 18 setup) complete  
**Blocks**: TASK_06+ (Event sourcing requires workspace isolation)
