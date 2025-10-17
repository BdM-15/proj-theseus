# PostgreSQL Implementation Plan: Multi-Workspace RFP Intelligence

**Status**: Planning (Pre-Phase 8)  
**Branch Context**: Post-004-mineru-multimodal completion  
**Target Start**: After Branch 004 merge to main  
**Estimated Duration**: 3-4 weeks

---

## Executive Summary

**Goal**: Migrate from JSON file storage to PostgreSQL to enable multi-RFP workspace management, cross-document analytics, and systematic training data collection for future fine-tuning (Phase 7).

**Current State**:

- **Storage**: JSON files (`kv_store_*.json`, `graph_chunk_entity_relation.graphml`)
- **Capacity**: Single RFP (Navy MBOS: 3,792 entities, 5,179 relationships)
- **Limitations**: No workspace isolation, manual file management, no cross-RFP queries

**Target State**:

- **Storage**: PostgreSQL 16.6+ with pgvector + Apache AGE
- **Capacity**: 50+ RFPs with workspace isolation
- **Features**: Workspace switching, cross-RFP analytics, persistent storage, team collaboration

---

## Phase 8.1: PostgreSQL Migration (Week 1)

### Objectives

- ✅ Setup PostgreSQL with required extensions
- ✅ Configure LightRAG for PostgreSQL backend
- ✅ Migrate existing Navy MBOS data
- ✅ Validate query performance (no regression)

### Technical Setup

#### Database Installation

**Option A: Docker (Recommended for Development)**

```bash
docker run -d \
  --name govcon-postgres \
  -e POSTGRES_USER=govcon_user \
  -e POSTGRES_PASSWORD=secure_password_here \
  -e POSTGRES_DB=govcon_rfp_db \
  -p 5432:5432 \
  -v govcon_pg_data:/var/lib/postgresql/data \
  ankane/pgvector:latest

# Install Apache AGE extension (for graph storage)
docker exec -it govcon-postgres psql -U govcon_user -d govcon_rfp_db -c \
  "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS age;"
```

**Option B: Local Installation**

```powershell
# Download PostgreSQL 16.6+
# https://www.postgresql.org/download/windows/

# Install pgvector extension
# https://github.com/pgvector/pgvector/releases

# Install Apache AGE (graph database)
# https://age.apache.org/
```

#### Environment Configuration

**Add to `.env`**:

```bash
# ============================================================================
# PostgreSQL Configuration (Phase 8)
# ============================================================================
# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=govcon_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DATABASE=govcon_rfp_db

# Workspace isolation (change this to switch between RFPs)
POSTGRES_WORKSPACE=navy_mbos_2025

# LightRAG storage backend configuration
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage

# Keep JSON as fallback during migration
# LIGHTRAG_KV_STORAGE=JsonKVStorage  # Uncomment to revert to JSON
```

#### Migration Script

**Create**: `scripts/migrate_json_to_postgres.py`

```python
"""
Migrate existing JSON storage to PostgreSQL.

Usage:
    python scripts/migrate_json_to_postgres.py --workspace navy_mbos_2025
"""

import asyncio
import json
from pathlib import Path
from lightrag import LightRAG
from lightrag.kg.postgres_impl import PGKVStorage, PGVectorStorage, PGGraphStorage

async def migrate_workspace(json_dir: str, workspace: str):
    """Migrate JSON files to PostgreSQL workspace"""
    print(f"🔄 Migrating {json_dir} → PostgreSQL workspace '{workspace}'")

    # Load JSON data
    entities = json.loads(Path(json_dir, "kv_store_full_entities.json").read_text())
    relations = json.loads(Path(json_dir, "kv_store_full_relations.json").read_text())
    doc_status = json.loads(Path(json_dir, "kv_store_doc_status.json").read_text())

    # Initialize PostgreSQL storage
    pg_storage = PGKVStorage(workspace=workspace)
    await pg_storage.connect()

    # Migrate entities
    for doc_id, entity_data in entities.items():
        await pg_storage.upsert(doc_id, entity_data)

    # Migrate relationships
    # ... (similar pattern)

    print(f"✅ Migration complete: {len(entities)} entities, {len(relations)} relationships")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, help="Target workspace name")
    args = parser.parse_args()

    asyncio.run(migrate_workspace("./rag_storage", args.workspace))
```

#### Validation Tests

**Create**: `tests/test_postgres_migration.py`

```python
"""Validate PostgreSQL migration maintains query quality"""

import pytest
from lightrag import LightRAG

@pytest.fixture
async def rag_json():
    """LightRAG with JSON storage (baseline)"""
    return LightRAG(working_dir="./rag_storage_json")

@pytest.fixture
async def rag_postgres():
    """LightRAG with PostgreSQL storage (migrated)"""
    return LightRAG(
        working_dir="./rag_storage",
        kv_storage="PGKVStorage",
        workspace="navy_mbos_2025"
    )

@pytest.mark.asyncio
async def test_entity_count_matches(rag_json, rag_postgres):
    """Verify all entities migrated"""
    json_entities = await rag_json.aget_all_entities()
    pg_entities = await rag_postgres.aget_all_entities()

    assert len(json_entities) == len(pg_entities) == 3792

@pytest.mark.asyncio
async def test_query_quality_maintained(rag_json, rag_postgres):
    """Verify query results match (no regression)"""
    query = "What are the evaluation factors in Section M and their weights?"

    json_result = await rag_json.aquery(query, mode="hybrid")
    pg_result = await rag_postgres.aquery(query, mode="hybrid")

    # Should return same entities (order may differ)
    assert "Factor A" in json_result and "Factor A" in pg_result
    assert "Factor D: Past Performance" in json_result and "Factor D: Past Performance" in pg_result
```

### Success Criteria

- [ ] PostgreSQL container running, extensions installed
- [ ] Navy MBOS data migrated (3,792 entities, 5,179 relationships)
- [ ] Query performance ≤ JSON baseline (<5 sec for hybrid queries)
- [ ] WebUI loads correctly with PostgreSQL backend
- [ ] No data loss (entity counts match)

---

## Phase 8.2: Workspace Management UI (Week 2)

### Objectives

- ✅ Add workspace selector to WebUI
- ✅ Implement workspace switching API
- ✅ Test with 3-5 RFPs
- ✅ Validate isolation (queries don't cross-contaminate)

### Minimal Workspace Selector

**Modify**: `lightrag/api/static/index.html` (or inject via custom endpoint)

```html
<!-- Add workspace selector bar -->
<div
  id="workspace-bar"
  style="padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
     color: white; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
>
  <!-- Left: Workspace selector -->
  <div style="display: flex; align-items: center; gap: 15px;">
    <label style="font-weight: 600; font-size: 14px;">📁 Active RFP:</label>
    <select
      id="workspace-selector"
      onchange="switchWorkspace(this.value)"
      style="padding: 8px 12px; font-size: 14px; border-radius: 6px; 
                   border: 2px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.15); 
                   color: white; min-width: 300px; cursor: pointer;"
    >
      <option value="navy_mbos_2025">
        Navy MBOS - Maritime Prepositioning (425 pages)
      </option>
      <option value="army_gfebs_2025">
        Army GFEBS - Financial Management (580 pages)
      </option>
      <option value="af_awacs_2025">
        Air Force AWACS - Sustainment (310 pages)
      </option>
      <option value="" disabled>────────────────────</option>
      <option value="__new__">+ Upload New RFP</option>
    </select>
  </div>

  <!-- Right: Workspace stats -->
  <div
    id="workspace-stats"
    style="display: flex; gap: 20px; font-size: 13px; opacity: 0.95;"
  >
    <span>📊 <strong id="entity-count">3,792</strong> entities</span>
    <span>🔗 <strong id="relation-count">5,179</strong> relationships</span>
    <span>⚡ <strong id="processing-time">69s</strong> processing</span>
  </div>
</div>

<script>
  async function switchWorkspace(workspace) {
    if (workspace === "__new__") {
      // Redirect to upload page
      window.location.href = "/upload";
      return;
    }

    // Show loading indicator
    document.getElementById("workspace-bar").style.opacity = "0.6";

    try {
      // Call backend to switch workspace
      const response = await fetch("/api/workspace/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workspace: workspace }),
      });

      const result = await response.json();

      if (result.success) {
        // Update stats
        document.getElementById("entity-count").textContent =
          result.stats.entities.toLocaleString();
        document.getElementById("relation-count").textContent =
          result.stats.relationships.toLocaleString();
        document.getElementById("processing-time").textContent =
          result.stats.processing_time;

        // Reload graph visualization
        location.reload();
      } else {
        alert("Failed to switch workspace: " + result.error);
      }
    } catch (error) {
      alert("Error switching workspace: " + error.message);
    } finally {
      document.getElementById("workspace-bar").style.opacity = "1";
    }
  }

  // Load workspace list on page load
  async function loadWorkspaces() {
    const response = await fetch("/api/workspace/list");
    const workspaces = await response.json();

    const selector = document.getElementById("workspace-selector");
    selector.innerHTML =
      workspaces
        .map(
          (ws) =>
            `<option value="${ws.name}">${ws.display_name} (${ws.page_count} pages)</option>`
        )
        .join("\n") +
      '<option value="" disabled>────────────────────</option><option value="__new__">+ Upload New RFP</option>';
  }

  window.addEventListener("DOMContentLoaded", loadWorkspaces);
</script>

<style>
  /* Workspace selector hover effects */
  #workspace-selector:hover {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.5);
  }

  #workspace-selector:focus {
    outline: none;
    border-color: rgba(255, 255, 255, 0.8);
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  }

  /* Responsive design for smaller screens */
  @media (max-width: 768px) {
    #workspace-bar {
      flex-direction: column;
      gap: 10px;
    }

    #workspace-stats {
      width: 100%;
      justify-content: space-around;
    }
  }
</style>
```

### Backend API Endpoints

**Add to**: `src/raganything_server.py` (or new `src/server/workspace_management.py`)

```python
"""
Workspace management API endpoints for PostgreSQL multi-RFP support.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

class WorkspaceSwitchRequest(BaseModel):
    workspace: str

class WorkspaceInfo(BaseModel):
    name: str
    display_name: str
    page_count: int
    entity_count: int
    relationship_count: int
    processing_time: str
    created_at: str

@router.post("/switch")
async def switch_workspace(request: WorkspaceSwitchRequest):
    """
    Switch active PostgreSQL workspace.

    This updates the POSTGRES_WORKSPACE environment variable and reinitializes
    RAGAnything to point to the new workspace schema.
    """
    workspace = request.workspace

    # Validate workspace exists in PostgreSQL
    if not await workspace_exists(workspace):
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace}' not found")

    # Update environment variable (affects future LightRAG initializations)
    os.environ['POSTGRES_WORKSPACE'] = workspace

    # Reinitialize RAGAnything with new workspace
    from src.server.initialization import initialize_raganything
    await initialize_raganything()

    # Get workspace stats
    stats = await get_workspace_stats(workspace)

    return {
        "success": True,
        "workspace": workspace,
        "stats": stats
    }

@router.get("/list")
async def list_workspaces() -> List[WorkspaceInfo]:
    """
    List all available PostgreSQL workspaces with metadata.
    """
    # Query PostgreSQL for workspace schemas
    # SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE '%_202%'
    workspaces = await get_all_workspaces()

    return [
        WorkspaceInfo(
            name=ws['name'],
            display_name=ws['display_name'],
            page_count=ws['page_count'],
            entity_count=ws['entity_count'],
            relationship_count=ws['relationship_count'],
            processing_time=ws['processing_time'],
            created_at=ws['created_at']
        )
        for ws in workspaces
    ]

@router.get("/stats/{workspace}")
async def get_workspace_stats(workspace: str) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific workspace.
    """
    from src.server.initialization import get_rag_instance

    rag = get_rag_instance()
    if not rag:
        raise HTTPException(status_code=500, detail="RAG instance not initialized")

    # Query PostgreSQL for workspace stats
    entities = await rag.lightrag.get_entity_count(workspace=workspace)
    relationships = await rag.lightrag.get_relationship_count(workspace=workspace)

    # Get document metadata
    doc_status = await rag.lightrag.doc_status.get_all(workspace=workspace)

    return {
        "entities": entities,
        "relationships": relationships,
        "documents": len(doc_status),
        "processing_time": doc_status[0]['metadata'].get('processing_end_time', 0) -
                          doc_status[0]['metadata'].get('processing_start_time', 0) if doc_status else 0
    }

async def workspace_exists(workspace: str) -> bool:
    """Check if workspace schema exists in PostgreSQL"""
    # Query: SELECT 1 FROM information_schema.schemata WHERE schema_name = '{workspace}'
    # Implementation depends on your PostgreSQL client
    pass

async def get_all_workspaces() -> List[Dict[str, Any]]:
    """Get list of all workspaces from PostgreSQL"""
    # Query workspace metadata from PostgreSQL
    pass
```

### Testing Plan

**Process 3-5 RFPs**:

1. Navy MBOS (existing) - 425 pages
2. Army GFEBS - upload new
3. Air Force AWACS - upload new
4. Coast Guard FRC - upload new
5. DHS EAGLE III - upload new

**Validation**:

```python
# Test workspace isolation
async def test_workspace_isolation():
    # Query in navy_mbos_2025
    os.environ['POSTGRES_WORKSPACE'] = 'navy_mbos_2025'
    navy_result = await rag.aquery("What are the evaluation factors?")
    assert "Past Performance" in navy_result  # Navy-specific factor

    # Query in army_gfebs_2025
    os.environ['POSTGRES_WORKSPACE'] = 'army_gfebs_2025'
    army_result = await rag.aquery("What are the evaluation factors?")
    assert "Financial Management Experience" in army_result  # Army-specific
    assert "Past Performance" not in army_result  # Should NOT see Navy data
```

### Success Criteria

- [ ] Workspace selector visible in WebUI header
- [ ] Can switch between 3-5 RFPs without errors
- [ ] Query results isolated per workspace (no cross-contamination)
- [ ] Workspace stats update correctly on switch
- [ ] UI responsive (<2 sec workspace switch time)

---

## Phase 8.3: Cross-RFP Analytics (Week 3)

### Objectives

- ✅ Enable SQL queries across multiple workspaces
- ✅ Build comparison views (evaluation factors, requirements, clauses)
- ✅ Export cross-RFP intelligence reports

### Cross-Workspace Query Examples

**SQL**: `scripts/cross_rfp_queries.sql`

```sql
-- Compare evaluation factors across all RFPs
SELECT
    workspace,
    entity_name,
    description,
    (data->>'weight')::FLOAT as weight
FROM (
    SELECT 'navy_mbos_2025' as workspace, * FROM navy_mbos_2025.entities
    UNION ALL
    SELECT 'army_gfebs_2025' as workspace, * FROM army_gfebs_2025.entities
    UNION ALL
    SELECT 'af_awacs_2025' as workspace, * FROM af_awacs_2025.entities
)
WHERE entity_type = 'EVALUATION_FACTOR'
ORDER BY workspace, weight DESC;

-- Find common FAR clauses across all RFPs
SELECT
    entity_name,
    COUNT(DISTINCT workspace) as rfp_count,
    STRING_AGG(workspace, ', ') as used_in_rfps
FROM (
    SELECT 'navy_mbos_2025' as workspace, * FROM navy_mbos_2025.entities
    UNION ALL
    SELECT 'army_gfebs_2025' as workspace, * FROM army_gfebs_2025.entities
    UNION ALL
    SELECT 'af_awacs_2025' as workspace, * FROM af_awacs_2025.entities
)
WHERE entity_type = 'CLAUSE' AND entity_name LIKE 'FAR%'
GROUP BY entity_name
HAVING COUNT(DISTINCT workspace) >= 2
ORDER BY rfp_count DESC;

-- Identify unique strategic themes per agency
SELECT
    workspace,
    entity_name,
    description
FROM (
    SELECT 'navy_mbos_2025' as workspace, * FROM navy_mbos_2025.entities
    UNION ALL
    SELECT 'army_gfebs_2025' as workspace, * FROM army_gfebs_2025.entities
)
WHERE entity_type = 'STRATEGIC_THEME'
ORDER BY workspace, entity_name;
```

### API Endpoints for Cross-RFP Queries

**Add to**: `src/server/analytics.py`

```python
"""
Cross-RFP analytics API for comparing multiple workspaces.
"""

from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/compare/evaluation-factors")
async def compare_evaluation_factors(workspaces: List[str]) -> Dict[str, Any]:
    """
    Compare evaluation factors across multiple RFPs.

    Returns:
        {
            "navy_mbos_2025": [
                {"name": "Past Performance", "weight": "Significant", "order": 4},
                {"name": "Management Approach", "weight": "Most Important", "order": 1}
            ],
            "army_gfebs_2025": [...]
        }
    """
    # Query PostgreSQL across workspaces
    pass

@router.get("/compare/requirements")
async def compare_requirements(workspaces: List[str],
                              requirement_type: str = None) -> Dict[str, Any]:
    """
    Compare requirements (must/should/may) across RFPs.
    """
    pass

@router.get("/common/clauses")
async def find_common_clauses(min_rfp_count: int = 2) -> List[Dict[str, Any]]:
    """
    Find FAR/DFARS clauses that appear in multiple RFPs.
    """
    pass
```

### Success Criteria

- [ ] SQL queries return results from multiple workspaces
- [ ] API endpoints expose cross-RFP comparisons
- [ ] No performance degradation (queries <5 sec for 5 RFPs)

---

## Phase 8.4: Training Data Collection (Week 4)

### Objectives

- ✅ Build user correction tracking system
- ✅ Export training examples for Phase 7 fine-tuning
- ✅ Quality scoring for extraction results

### User Correction Schema

**Add to PostgreSQL**: `schema/training_data.sql`

```sql
-- Track user corrections to LLM extractions
CREATE TABLE user_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    original_extraction JSONB NOT NULL,  -- What LLM extracted
    corrected_extraction JSONB NOT NULL, -- User's correction
    correction_type TEXT,                -- 'entity_type', 'description', 'relationship', 'missing'
    user_id TEXT,
    correction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    correction_notes TEXT
);

-- Track extraction quality scores
CREATE TABLE extraction_quality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace TEXT NOT NULL,
    document_id TEXT NOT NULL,
    entity_count INT,
    relationship_count INT,
    user_validated_count INT,
    correction_count INT,
    quality_score DECIMAL(3,2),  -- 0.00 to 1.00
    feedback_timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Training examples for fine-tuning
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_text TEXT NOT NULL,              -- RFP chunk
    expected_output JSONB NOT NULL,        -- Entities/relationships
    entity_types TEXT[],
    user_corrected BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(3,2),
    source_workspace TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track entity extraction corruption patterns (Branch 005)
CREATE TABLE entity_corruption_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace TEXT NOT NULL REFERENCES rfp_workspaces(workspace_name) ON DELETE RESTRICT,
    document_id TEXT NOT NULL,
    chunk_id TEXT,
    entity_name TEXT NOT NULL,
    corruption_pattern TEXT NOT NULL,    -- e.g., "#>|LOCATION", "#|PROGRAM", "#>|evaluation_factor"
    detected_type TEXT,                  -- What the corrupted entity_type was
    expected_type TEXT,                  -- What it should be (if known)
    original_value TEXT NOT NULL,        -- Full entity extraction string
    corrected_value TEXT,                -- After manual cleanup
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    corrected_at TIMESTAMPTZ,
    corrected_by TEXT,
    correction_method TEXT,              -- 'manual', 'automated', 'validation_filter'
    notes TEXT,

    -- Metadata for tracking LLM behavior
    llm_model TEXT,                      -- e.g., "grok-4-fast-reasoning"
    prompt_version TEXT,                 -- Track which prompt caused corruption
    reasoning_artifacts TEXT             -- Chain-of-thought bleed-through
);

-- Corruption pattern statistics (for monitoring trends)
CREATE TABLE corruption_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace TEXT NOT NULL REFERENCES rfp_workspaces(workspace_name) ON DELETE RESTRICT,
    document_id TEXT NOT NULL,
    processing_date DATE NOT NULL,
    total_entities INT NOT NULL,
    corrupted_entities INT NOT NULL,
    corruption_rate DECIMAL(5,2),        -- e.g., 2.2%
    pattern_breakdown JSONB,             -- {"#>|TYPE": 10, "#|TYPE": 2, "lowercase": 1}
    llm_model TEXT,
    prompt_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX idx_corrections_workspace ON user_corrections(workspace);
CREATE INDEX idx_corrections_type ON user_corrections(correction_type);
CREATE INDEX idx_training_quality ON training_examples(quality_score DESC);
CREATE INDEX idx_corruption_workspace ON entity_corruption_tracking(workspace);
CREATE INDEX idx_corruption_pattern ON entity_corruption_tracking(corruption_pattern);
CREATE INDEX idx_corruption_detected_at ON entity_corruption_tracking(detected_at DESC);
CREATE INDEX idx_corruption_stats_date ON corruption_statistics(processing_date DESC);
CREATE INDEX idx_corruption_stats_workspace ON corruption_statistics(workspace);
```

### API Endpoints for Corrections

**Add to**: `src/server/corrections.py`

```python
"""
User correction tracking for training data collection.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/corrections", tags=["corrections"])

class EntityCorrectionRequest(BaseModel):
    workspace: str
    entity_id: str
    original: Dict[str, Any]
    corrected: Dict[str, Any]
    correction_type: str
    notes: str = None

@router.post("/entity")
async def submit_entity_correction(request: EntityCorrectionRequest):
    """
    Track user correction to an entity extraction.

    Example:
        Original: {"entity_name": "MCPP II", "entity_type": "organization"}
        Corrected: {"entity_name": "MCPP II", "entity_type": "program"}
    """
    # Store correction in PostgreSQL
    # Update entity in graph
    # Generate training example
    pass

@router.get("/export/{workspace}")
async def export_training_data(workspace: str, min_quality: float = 0.7):
    """
    Export training examples from workspace for fine-tuning.

    Returns JSONL format:
        {"input": "Section L.3.2 requires...", "output": {"entities": [...], "relationships": [...]}}
        {"input": "Factor D evaluates...", "output": {...}}
    """
    pass
```

### Success Criteria

- [ ] User can submit corrections via API
- [ ] Corrections stored in PostgreSQL
- [ ] Training data export generates valid JSONL
- [ ] Quality scores calculated automatically

---

## Database Schema Reference

### LightRAG Built-in Tables (Per Workspace)

```sql
-- Workspace: navy_mbos_2025
CREATE SCHEMA navy_mbos_2025;

-- Entities (from LightRAG extraction)
CREATE TABLE navy_mbos_2025.entities (
    id TEXT PRIMARY KEY,
    entity_name TEXT NOT NULL,
    entity_type TEXT,
    description TEXT,
    source_id TEXT,
    data JSONB,
    embedding VECTOR(1024)  -- pgvector extension
);

-- Relationships
CREATE TABLE navy_mbos_2025.relationships (
    id TEXT PRIMARY KEY,
    source_entity TEXT REFERENCES navy_mbos_2025.entities(id),
    target_entity TEXT REFERENCES navy_mbos_2025.entities(id),
    relationship_type TEXT,
    description TEXT,
    weight FLOAT,
    data JSONB
);

-- Document status
CREATE TABLE navy_mbos_2025.doc_status (
    doc_id TEXT PRIMARY KEY,
    status TEXT,
    chunks_count INT,
    chunks_list TEXT[],
    content_length INT,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Vector index for similarity search
CREATE INDEX idx_entities_embedding ON navy_mbos_2025.entities
    USING ivfflat (embedding vector_cosine_ops);
```

### Custom Govcon Tables (Global)

```sql
-- RFP metadata (workspace registry)
CREATE TABLE rfp_workspaces (
    workspace_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    agency TEXT,
    solicitation_number TEXT,
    page_count INT,
    entity_count INT,
    relationship_count INT,
    processing_time_seconds INT,
    processed_date TIMESTAMPTZ,
    rfp_file_path TEXT,
    status TEXT DEFAULT 'active'  -- 'active', 'archived', 'deleted'
);

-- User corrections (training data)
CREATE TABLE user_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace TEXT REFERENCES rfp_workspaces(workspace_name) ON DELETE RESTRICT,
    entity_id TEXT,
    original_extraction JSONB,
    corrected_extraction JSONB,
    correction_type TEXT,
    user_id TEXT,
    correction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    correction_notes TEXT
);

-- Training examples (for Phase 7 fine-tuning)
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_text TEXT NOT NULL,
    expected_output JSONB NOT NULL,
    entity_types TEXT[],
    user_corrected BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(3,2),
    source_workspace TEXT REFERENCES rfp_workspaces(workspace_name) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_corrections_workspace ON user_corrections(workspace);
CREATE INDEX idx_training_quality ON training_examples(quality_score DESC);
CREATE INDEX idx_workspaces_status ON rfp_workspaces(status);
```

---

## Performance Benchmarks

### Target Metrics (5 RFPs in PostgreSQL)

| Operation        | JSON Baseline | PostgreSQL Target | Notes                    |
| ---------------- | ------------- | ----------------- | ------------------------ |
| Query (hybrid)   | 3-5 sec       | 3-5 sec           | No regression            |
| Entity lookup    | <100ms        | <50ms             | Indexed faster           |
| Workspace switch | N/A           | <2 sec            | Acceptable UX            |
| Cross-RFP query  | N/A           | <5 sec            | 5 workspaces             |
| Document upload  | 69 sec        | 69 sec            | Unchanged (parsing time) |

### Optimization Strategies

**If query performance degrades**:

1. **Indexes**: Add indexes on frequently queried fields

   ```sql
   CREATE INDEX idx_entity_type ON entities(entity_type);
   CREATE INDEX idx_entity_name ON entities(entity_name);
   ```

2. **Connection pooling**: Use asyncpg with connection pool

   ```python
   import asyncpg
   pool = await asyncpg.create_pool(dsn=postgres_url, min_size=5, max_size=20)
   ```

3. **Query optimization**: Use EXPLAIN ANALYZE for slow queries

   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM entities WHERE entity_type = 'EVALUATION_FACTOR';
   ```

4. **Materialized views**: Pre-compute common cross-RFP queries
   ```sql
   CREATE MATERIALIZED VIEW all_evaluation_factors AS
   SELECT workspace, entity_name, description FROM ...
   UNION ALL ...;
   ```

---

## Rollback Plan

**If PostgreSQL migration has issues**, revert to JSON:

1. **Environment variables**:

   ```bash
   # Comment out PostgreSQL config
   # LIGHTRAG_KV_STORAGE=PGKVStorage

   # Enable JSON storage
   LIGHTRAG_KV_STORAGE=JsonKVStorage
   LIGHTRAG_GRAPH_STORAGE=NetworkXStorage
   ```

2. **Restart server**:

   ```powershell
   python app.py
   ```

3. **Verify JSON files intact**:
   ```powershell
   Get-ChildItem .\rag_storage\*.json
   ```

**Data loss prevention**:

- Keep JSON backups during migration (don't delete until PostgreSQL validated)
- Export PostgreSQL data weekly: `pg_dump govcon_rfp_db > backup_$(date).sql`

---

## Cost Analysis

### Infrastructure Costs

| Component  | Development | Production    | Notes                      |
| ---------- | ----------- | ------------- | -------------------------- |
| PostgreSQL | $0 (Docker) | $20-50/mo     | Digital Ocean/AWS RDS      |
| Storage    | $0          | $0.10/GB      | Estimated 10GB for 50 RFPs |
| Backups    | $0          | $5-10/mo      | Automated daily backups    |
| **Total**  | **$0/mo**   | **$30-70/mo** | Scales with RFP count      |

### Time Investment

| Phase              | Duration      | Dev Hours  | Notes                            |
| ------------------ | ------------- | ---------- | -------------------------------- |
| 8.1: Migration     | 1 week        | 20-30h     | Setup, migration script, testing |
| 8.2: Workspace UI  | 1 week        | 10-15h     | Minimal dropdown + API           |
| 8.3: Analytics     | 1 week        | 15-20h     | Cross-RFP queries, API endpoints |
| 8.4: Training Data | 1 week        | 10-15h     | Correction tracking, export      |
| **Total**          | **3-4 weeks** | **55-80h** | Includes testing, documentation  |

---

## Risk Assessment

### High Risk

- **Migration data loss**: Backup JSON before migration, validate entity counts
- **Query performance regression**: Benchmark before/after, rollback plan ready
- **PostgreSQL complexity**: Docker simplifies setup, but requires PostgreSQL knowledge

### Medium Risk

- **Workspace isolation bugs**: Test thoroughly with 3-5 RFPs before production
- **Cross-RFP query performance**: May need indexes/optimization for 10+ RFPs
- **UI integration breaking**: Minimal WebUI modifications reduce risk

### Low Risk

- **Storage costs**: 10GB for 50 RFPs = $1/mo, negligible
- **Maintenance burden**: PostgreSQL is stable, Docker simplifies updates
- **Team adoption**: Familiar SQL, widely used in enterprise

---

## Success Metrics

### Phase 8 Complete When:

- [ ] 5+ RFPs processed in PostgreSQL workspaces
- [ ] Workspace switching works reliably (<2 sec switch time)
- [ ] Query performance maintained (no regression vs JSON)
- [ ] Cross-RFP analytics queries working (<5 sec for 5 RFPs)
- [ ] Training data collection active (10+ user corrections tracked)
- [ ] Documentation updated (README, ARCHITECTURE.md)
- [ ] Rollback tested successfully (can revert to JSON if needed)

### Key Performance Indicators

- **Workspace count**: 5+ active RFPs
- **Query latency p95**: <5 seconds (hybrid mode)
- **Workspace switch time**: <2 seconds
- **Cross-RFP query time**: <5 seconds (5 workspaces)
- **Training examples**: 100+ high-quality examples for Phase 7

---

## Future Enhancements (Post-Phase 8)

**Phase 9: Advanced Features** (Month 2-3)

- Side panel UI with collapsible workspace tree
- Real-time collaboration (multiple users querying same workspace)
- Export tools (compliance matrices, checklists, proposals outlines)
- Role-based access control (capture manager vs proposal writer views)

**Phase 10: Enterprise Scale** (Month 4+)

- Neo4j migration (if processing 100+ RFPs)
- Distributed PostgreSQL (Citus) for horizontal scaling
- Multi-tenant architecture (separate databases per client)
- Advanced analytics (win/loss analysis, pricing trends, competitive intelligence)

---

## Appendix A: Environment Variables Reference

```bash
# ============================================================================
# PostgreSQL Configuration (Phase 8)
# ============================================================================

# Database connection
POSTGRES_HOST=localhost              # PostgreSQL server hostname
POSTGRES_PORT=5432                   # PostgreSQL server port
POSTGRES_USER=govcon_user            # Database user
POSTGRES_PASSWORD=secure_password    # Database password (use secrets management in prod)
POSTGRES_DATABASE=govcon_rfp_db      # Database name

# Workspace isolation (change to switch between RFPs)
POSTGRES_WORKSPACE=navy_mbos_2025    # Active workspace schema

# LightRAG storage backend (Phase 8)
LIGHTRAG_KV_STORAGE=PGKVStorage               # Key-value storage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage       # Vector embeddings (pgvector)
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage         # Graph relationships (Apache AGE)
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage # Document processing status

# Fallback to JSON (comment out to revert)
# LIGHTRAG_KV_STORAGE=JsonKVStorage
# LIGHTRAG_GRAPH_STORAGE=NetworkXStorage
# LIGHTRAG_VECTOR_STORAGE=NanoVectorDBStorage
# LIGHTRAG_DOC_STATUS_STORAGE=JsonDocStatusStorage

# Connection pooling (optional, for high concurrency)
POSTGRES_POOL_MIN_SIZE=5             # Minimum connections in pool
POSTGRES_POOL_MAX_SIZE=20            # Maximum connections in pool
POSTGRES_POOL_TIMEOUT=30             # Connection timeout (seconds)
```

---

## Appendix B: PostgreSQL Setup Commands

### Docker Installation (Recommended)

```bash
# Pull PostgreSQL with pgvector extension
docker pull ankane/pgvector:latest

# Run PostgreSQL container
docker run -d \
  --name govcon-postgres \
  -e POSTGRES_USER=govcon_user \
  -e POSTGRES_PASSWORD=secure_password_here \
  -e POSTGRES_DB=govcon_rfp_db \
  -p 5432:5432 \
  -v govcon_pg_data:/var/lib/postgresql/data \
  ankane/pgvector:latest

# Install Apache AGE extension (graph database)
docker exec -it govcon-postgres psql -U govcon_user -d govcon_rfp_db -c \
  "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify extensions installed
docker exec -it govcon-postgres psql -U govcon_user -d govcon_rfp_db -c \
  "SELECT * FROM pg_extension WHERE extname IN ('vector');"

# Create first workspace schema
docker exec -it govcon-postgres psql -U govcon_user -d govcon_rfp_db -c \
  "CREATE SCHEMA IF NOT EXISTS navy_mbos_2025;"
```

### Local Installation (Windows)

```powershell
# Download PostgreSQL 16.6+
# https://www.postgresql.org/download/windows/

# Install via installer (next, next, finish)

# Add to PATH
$env:PATH += ";C:\Program Files\PostgreSQL\16\bin"

# Create database
psql -U postgres -c "CREATE DATABASE govcon_rfp_db;"
psql -U postgres -c "CREATE USER govcon_user WITH PASSWORD 'secure_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE govcon_rfp_db TO govcon_user;"

# Install pgvector extension
# Download from: https://github.com/pgvector/pgvector/releases
# Follow Windows installation guide
psql -U govcon_user -d govcon_rfp_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
psql -U govcon_user -d govcon_rfp_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

---

## Appendix C: Useful PostgreSQL Queries

```sql
-- List all workspaces (schemas)
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name LIKE '%_202%'
ORDER BY schema_name;

-- Get entity count per workspace
SELECT
    schemaname as workspace,
    COUNT(*) as entity_count
FROM pg_tables
WHERE schemaname LIKE '%_202%' AND tablename = 'entities'
GROUP BY schemaname;

-- Find largest workspaces by storage size
SELECT
    schemaname as workspace,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as size
FROM pg_tables
WHERE schemaname LIKE '%_202%'
GROUP BY schemaname
ORDER BY SUM(pg_total_relation_size(schemaname||'.'||tablename)) DESC;

-- Vacuum and analyze (performance maintenance)
VACUUM ANALYZE;

-- Check index usage (optimize slow queries)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Next Steps After Branch 004 Completion

1. **Merge Branch 004** to main (after query testing validates quality)
2. **Create Branch 005**: `git checkout -b 005-postgresql-migration`
3. **Follow Phase 8.1**: Setup PostgreSQL, migrate Navy MBOS data
4. **Test thoroughly**: Validate query performance, workspace isolation
5. **Document learnings**: Update this plan based on real-world experience

---

**Document Status**: Planning (Pre-Phase 8)  
**Last Updated**: October 9, 2025  
**Author**: AI Assistant + User Collaboration  
**Next Review**: After Branch 004 merge to main

---

## User Feature Roadmap

_Organized from user requirements into phased implementation plan_

---

## 🎯 Core Capture Management Features (High Priority)

### 1. **Intelligent Proposal Outline Generator**

**Description**: Analyzes RFP structure (Section L/M/C) and automatically generates compliant proposal outline with recommended page allocations, volume structure, and content guidance. Ensures all "shall" requirements mapped to proposal sections.

**Use Case**:

- Proposal kickoff: Generate initial outline within 1 hour of RFP release
- Capture manager creates strawman structure for team review
- Maps evaluation factors → proposal volumes → page limits

**Priority**: 🔴 **HIGH** (Core value proposition)

**Dependencies**:

- ✅ Already possible: Query knowledge graph for Section L/M entities
- ⚠️ Needs: PydanticAI agents (Phase 9) for structured generation
- ⚠️ Needs: Section L↔M relationship inference (Phase 6 ✅ complete)

**Technical Approach**:

```python
# Phase 9: PydanticAI Agent Implementation
from pydantic_ai import Agent

outline_agent = Agent(
    model="grok-4-fast-reasoning",
    system_prompt="""You are a Shipley-trained proposal manager.
    Generate proposal outlines following FAR 15.210 guidelines."""
)

async def generate_proposal_outline(workspace: str):
    # Step 1: Query RFP structure
    sections = await rag.aquery(
        "What sections, volumes, and page limits are defined in Section L?",
        workspace=workspace
    )

    # Step 2: Query evaluation factors
    factors = await rag.aquery(
        "What are the evaluation factors in Section M with weights?",
        workspace=workspace
    )

    # Step 3: Agent generates outline
    outline = await outline_agent.run(
        f"Generate proposal outline mapping {factors} to {sections}"
    )

    return outline  # Structured Pydantic model
```

**Output Format**:

```
Volume I: Technical Approach (50 pages, Factor B: 40% weight)
  ├─ Section 1: Management Approach (10 pages)
  │   ├─ 1.1 Program Management Organization (addresses REQ-001, REQ-005)
  │   ├─ 1.2 Risk Management Process (addresses REQ-012)
  │   └─ 1.3 Quality Assurance (addresses REQ-023)
  ├─ Section 2: Technical Solution (25 pages)
  │   ├─ 2.1 System Architecture (SHALL requirement from C.3.2.1)
  │   └─ 2.2 Technology Stack (innovation opportunity)
  └─ Section 3: Transition Plan (15 pages)

Volume II: Past Performance (25 pages, Factor D: 30% weight)
  ├─ Section 1: Relevant Contracts (max 5 per Section L.4.2)
  └─ Section 2: Past Performance Questionnaires (S-Attachment S-3)

Volume III: Cost Proposal (CLIN-based, Factor E: 30% weight)
```

**Implementation Phase**: Phase 9 (PydanticAI agents)  
**Estimated Effort**: 40-60 hours (includes Shipley methodology integration)

---

### 2. **Deliverables Intelligence Extractor**

**Description**: Identifies and catalogs ALL required deliverables from RFP (reports, CDRLs, data items, services, meetings, reviews) with frequency, format, and deadlines. Cross-references Section C, Section J attachments, and clauses.

**Use Case**:

- Cost estimation: Ensure labor hours account for all reporting requirements
- Proposal development: Create deliverables matrix for compliance
- Contract execution: Generate deliverables tracking spreadsheet

**Priority**: 🔴 **HIGH** (Critical for cost accuracy)

**Dependencies**:

- ✅ Already possible: Query for DELIVERABLE entities (12 entity types include this)
- ⚠️ Needs: Enhanced extraction prompts for CDRL parsing
- ⚠️ Needs: Export to Excel/CSV functionality

**Technical Approach**:

```python
# Already working with Phase 6 entity extraction!
deliverables = await rag.aquery(
    "List all deliverables with frequency, format, and section references",
    workspace="navy_mbos_2025"
)

# Phase 8.3: Export to Excel
import pandas as pd

df = pd.DataFrame({
    'Deliverable': [...],
    'Type': ['Report', 'Service', 'Review', 'Data Item'],
    'Frequency': ['Monthly', 'Quarterly', 'As Needed'],
    'Format': ['PDF', 'Excel', 'Presentation'],
    'Due Date': ['Monthly +5 days', 'Quarterly +10 days'],
    'Section Reference': ['C.3.4.5', 'J-05000000', 'FAR 52.232-6'],
    'CLIN': ['CLIN 0001', 'CLIN 0002'],
    'Estimated Hours': [8, 16, 24]
})

df.to_excel('deliverables_matrix.xlsx', index=False)
```

**Output Format**:
| Deliverable | Type | Frequency | Format | Due Date | Section | CLIN | Est. Hours |
|-------------|------|-----------|--------|----------|---------|------|------------|
| Status of Funds Report | Report | Monthly | Excel | Monthly +5 days | C.3.4.5 | 0001 | 8 |
| Past Performance Questionnaire | Data Item | As Needed | PDF | With proposal | L.4.2 | N/A | 16 |
| Technical Design Review | Review | Quarterly | Presentation | Quarterly +10 days | C.5.2.1 | 0003 | 24 |

**Implementation Phase**: Phase 8.3 (Cross-RFP analytics) + Phase 9 (Export tools)  
**Estimated Effort**: 20-30 hours (entity extraction tuning + Excel export)

---

### 3. **Compliance Matrix Generator**

**Description**: Automated extraction of ALL Section L instructions ("ankle biters") with page limits, format requirements, font size, margins, submission deadlines, and cross-reference to evaluation factors. Ensures nothing overlooked.

**Use Case**:

- Proposal manager creates compliance checklist for writers
- Red Team review: Verify every instruction addressed
- Color reviews: Track compliance status per requirement

**Priority**: 🔴 **HIGH** (Risk mitigation - non-compliance = proposal rejection)

**Dependencies**:

- ✅ Already possible: SUBMISSION_INSTRUCTION entities extracted
- ✅ Phase 6 complete: Section L↔M relationships inferred
- ⚠️ Needs: Export to Excel with compliance tracking columns

**Technical Approach**:

```python
# Query Section L instructions
instructions = await rag.aquery(
    "What are all the submission instructions from Section L with page limits and format requirements?",
    workspace="navy_mbos_2025"
)

# Generate compliance matrix
compliance_matrix = {
    'Instruction': [],
    'Requirement': [],
    'Page Limit': [],
    'Format': [],
    'Evaluated By': [],  # Section M factor
    'Proposal Section': [],  # Where addressed
    'Compliance Status': ['Not Started', 'In Progress', 'Complete'],
    'Owner': [],  # Team member assigned
    'Notes': []
}

# Export to Excel with conditional formatting
df = pd.DataFrame(compliance_matrix)
with pd.ExcelWriter('compliance_matrix.xlsx', engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Compliance', index=False)

    # Apply conditional formatting (red/yellow/green status)
    workbook = writer.book
    worksheet = writer.sheets['Compliance']
    worksheet.conditional_format('G2:G100', {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Complete',
        'format': workbook.add_format({'bg_color': '#C6EFCE'})
    })
```

**Output Format**:
| Instruction | Requirement | Page Limit | Format | Evaluated By | Proposal Section | Status | Owner | Notes |
|-------------|-------------|------------|--------|--------------|------------------|--------|-------|-------|
| L.3.2 | Technical approach limited to 50 pages | 50 | 12pt Times, 1" margins | Factor B (40%) | Volume I, Section 2 | Complete | John D. | ✅ |
| L.4.1 | Include organizational chart | 1 page | Landscape OK | Factor A (30%) | Volume I, Section 1.1 | In Progress | Sarah K. | Chart in review |
| L.5.3 | Electronic submission via SAM.gov | N/A | PDF/A format | N/A | All volumes | Not Started | PM | Need PDF/A tool |

**Implementation Phase**: Phase 8.3 (Cross-RFP analytics) + Phase 9 (Export tools)  
**Estimated Effort**: 25-35 hours (extraction refinement + Excel export with formatting)

---

## 📊 Strategic Intelligence Features (Medium Priority)

### 4. **RFP Question Generator (Pre-Proposal Intelligence)**

**Description**: AI-powered analysis identifies ambiguities, vagueness, conflicts, inconsistencies, and opportunities for clarification. Generates recommended questions to shape RFP quality and gain competitive advantage.

**Use Case**:

- Capture phase: Submit questions during Q&A period to clarify requirements
- Competitive intelligence: Questions reveal understanding depth
- Risk mitigation: Resolve ambiguities before proposal submission

**Priority**: 🟡 **MEDIUM-HIGH** (Strategic advantage, but not blocking)

**Dependencies**:

- ✅ Already possible: Query knowledge graph for conflicts
- ⚠️ Needs: PydanticAI agents (Phase 9) for question generation
- ⚠️ Needs: Semantic analysis of RFP consistency

**Technical Approach**:

```python
# Phase 9: PydanticAI Question Generation Agent
question_agent = Agent(
    model="grok-4-fast-reasoning",
    system_prompt="""You are a capture manager analyzing RFPs for competitive advantage.
    Generate insightful questions following Shipley Capture Guide p.25 guidelines."""
)

async def generate_rfp_questions(workspace: str):
    # Step 1: Analyze for ambiguities
    analysis = await rag.aquery(
        """Identify:
        1. Conflicting requirements between sections
        2. Undefined technical terms or acronyms
        3. Ambiguous evaluation criteria
        4. Missing scope details
        5. Unclear submission requirements""",
        workspace=workspace
    )

    # Step 2: Agent generates questions
    questions = await question_agent.run(
        f"Generate strategic questions to clarify: {analysis}"
    )

    return questions  # Structured with rationale, section reference
```

**Output Format**:

```
Question 1: Technical Scope Clarification
  Reference: Section C.3.2.1 "System shall support multiple platforms"
  Ambiguity: "Multiple platforms" undefined (2, 5, 10+?)
  Suggested Question: "How many platforms must the system support concurrently?
                      Is there a minimum or maximum threshold?"
  Competitive Advantage: Allows precise sizing and cost optimization
  Risk if Unanswered: HIGH - Could underbid and fail to deliver

Question 2: Evaluation Weight Conflict
  Reference: Section M states "Technical Approach most important" but assigns 35% weight
             while Past Performance gets 40%
  Conflict: Weight contradicts stated importance order
  Suggested Question: "Section M describes Technical Approach as 'most important' but
                      assigns 35% weight vs Past Performance at 40%. Please clarify
                      the relative importance or correct the weight allocation."
  Competitive Advantage: Proposal emphasis aligns with actual evaluation priority
  Risk if Unanswered: MEDIUM - Misallocated proposal effort

Question 3: Transition Timeline Ambiguity
  Reference: Section C.4.2 "Transition to be completed promptly"
  Ambiguity: "Promptly" undefined (30 days, 60 days, 90 days?)
  Suggested Question: "What is the required transition completion timeline in calendar days?"
  Competitive Advantage: Accurate resource planning and pricing
  Risk if Unanswered: MEDIUM - Unrealistic timeline in proposal
```

**Max Questions**: 7 high-impact questions (per Shipley guidance)  
**Implementation Phase**: Phase 9 (PydanticAI agents)  
**Estimated Effort**: 30-40 hours (semantic analysis + question generation logic)

---

### 5. **Agency Trends Analyzer (Cross-RFP Intelligence)**

**Description**: Analyzes patterns across multiple RFPs from same agency to identify recurring pain points, common evaluation criteria, preferred metrics, typical conflicts, hot buttons, and win themes.

**Use Case**:

- Capture strategy: Tailor messaging to agency preferences
- Pricing strategy: Understand evaluation weight trends (cost vs technical)
- Risk identification: Common agency pain points = opportunity to differentiate

**Priority**: 🟡 **MEDIUM** (High value, but requires 10+ RFPs for meaningful trends)

**Dependencies**:

- ⚠️ **REQUIRES**: PostgreSQL workspace management (Phase 8.3)
- ⚠️ **REQUIRES**: 10+ RFPs processed from same agency
- ⚠️ Needs: Cross-RFP SQL analytics

**Technical Approach**:

```python
# Phase 8.3: Cross-RFP SQL Analytics
async def analyze_agency_trends(agency: str):
    # Query PostgreSQL across all workspaces for same agency
    query = """
    SELECT
        workspace,
        entity_name,
        description,
        COUNT(*) as frequency
    FROM (
        SELECT 'navy_rfp_1' as workspace, * FROM navy_rfp_1.entities
        UNION ALL
        SELECT 'navy_rfp_2' as workspace, * FROM navy_rfp_2.entities
        UNION ALL
        SELECT 'navy_rfp_3' as workspace, * FROM navy_rfp_3.entities
    )
    WHERE entity_type IN ('STRATEGIC_THEME', 'EVALUATION_FACTOR', 'REQUIREMENT')
    GROUP BY entity_name, description
    HAVING COUNT(*) >= 2  -- Appears in 2+ RFPs
    ORDER BY frequency DESC;
    """

    trends = await execute_postgres_query(query)

    return {
        'recurring_themes': trends['STRATEGIC_THEME'],
        'common_evaluation_factors': trends['EVALUATION_FACTOR'],
        'frequent_requirements': trends['REQUIREMENT']
    }
```

**Output Format**:

```
Navy RFP Trends Analysis (10 RFPs analyzed: 2020-2025)

📊 Recurring Strategic Themes:
  1. "Cybersecurity resilience" (10/10 RFPs, 100%)
  2. "Sailor safety" (9/10 RFPs, 90%)
  3. "Interoperability with legacy systems" (8/10 RFPs, 80%)
  4. "Reduced total cost of ownership" (7/10 RFPs, 70%)

🎯 Common Evaluation Factors:
  1. Past Performance (10/10, avg weight: 38%)
  2. Technical Approach (10/10, avg weight: 35%)
  3. Management Approach (9/10, avg weight: 18%)
  4. Small Business Participation (7/10, avg weight: 5%)

📋 Frequent Requirements:
  1. "Weekly status reports" (10/10 RFPs)
  2. "Compliance with NIST 800-171" (9/10 RFPs)
  3. "Secret clearance for key personnel" (8/10 RFPs)
  4. "On-site presence required" (7/10 RFPs)

⚠️ Common Pain Points:
  1. "Integration with GCSS-MC" (mentioned in 6/10 SOWs as challenge)
  2. "Legacy system modernization" (5/10 RFPs cite as risk)
  3. "Budget constraints" (4/10 RFPs mention funding uncertainty)

💡 Win Theme Recommendations:
  - Emphasize cybersecurity track record (100% of RFPs prioritize)
  - Highlight small business teaming (70% include SB factor)
  - Demonstrate GCSS-MC integration experience (60% pain point)
```

**Implementation Phase**: Phase 8.3 (PostgreSQL analytics) + Phase 9 (Reporting)  
**Estimated Effort**: 40-50 hours (cross-RFP SQL queries + trend analysis logic)

---

## 🚀 Advanced Collaboration Features (Lower Priority)

### 6. **Solution Workshop Assistant (Web-Enhanced Brainstorming)**

**Description**: Interactive AI assistant that helps brainstorm innovative solutions by combining RFP requirements with external web research (emerging technologies, industry best practices, competitive solutions).

**Use Case**:

- Capture workshops: Generate solution ideas team may not have considered
- Competitive differentiation: Research what competitors offer
- Technology scouting: Identify emerging tools/platforms relevant to RFP

**Priority**: 🟢 **MEDIUM-LOW** (Nice-to-have, but not blocking proposal development)

**Dependencies**:

- ⚠️ Needs: Web search integration (Tavily, Perplexity, or Bing API)
- ⚠️ Needs: PydanticAI agents (Phase 9) for brainstorming
- ✅ Already possible: Query RFP requirements from knowledge graph

**Technical Approach**:

```python
# Phase 9+: Web-Enhanced Solution Assistant
from tavily import TavilyClient  # Or use vscode-websearchforcopilot tool

solution_agent = Agent(
    model="grok-4-fast-reasoning",
    system_prompt="""You are a solution architect helping teams win government contracts.
    Combine RFP requirements with industry research to suggest innovative approaches."""
)

async def brainstorm_solutions(workspace: str, requirement: str):
    # Step 1: Get requirement details from RFP
    rfp_context = await rag.aquery(
        f"What are the technical requirements related to: {requirement}",
        workspace=workspace
    )

    # Step 2: Web search for industry solutions
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    research = tavily.search(
        query=f"{requirement} government contracting solutions best practices",
        search_depth="advanced"
    )

    # Step 3: Agent synthesizes solutions
    ideas = await solution_agent.run(
        f"RFP requires: {rfp_context}\n\nIndustry research: {research}\n\n"
        f"Suggest 3-5 innovative solution approaches."
    )

    return ideas
```

**Output Format**:

```
Requirement: "System must integrate with GCSS-MC and legacy LOGAIS systems"

💡 Solution Ideas:

1. API Gateway Pattern with Event-Driven Architecture
   - RFP Alignment: Addresses integration requirement (C.3.2.1)
   - Industry Research: Modern integration approach used by DoD's DEVSECOPS initiative
   - Innovation: Event-driven reduces point-to-point complexity (6 systems = 2 integrations, not 15)
   - Risk: LOW (proven in DoD environments)
   - Competitive Advantage: Reduces integration timeline by 40% vs traditional approach

2. Federated Data Layer with GraphQL
   - RFP Alignment: Supports "single pane of glass" requirement (C.4.1.2)
   - Industry Research: Air Force using GraphQL for legacy system integration (source: DIU case study)
   - Innovation: Query any system through unified interface
   - Risk: MEDIUM (newer tech, but Air Force precedent)
   - Competitive Advantage: User experience improvement (Sailor pain point from Navy study)

3. Hybrid Cloud Deployment (Azure Gov + On-Prem)
   - RFP Alignment: Security requirements (C.5.2) + budget constraints (Section B)
   - Industry Research: Navy moving to hybrid model per NMCI transformation
   - Innovation: Balance security + cost (sensitive data on-prem, analytics in cloud)
   - Risk: LOW (Navy preference based on NMCI strategy)
   - Competitive Advantage: 30% cost reduction vs all on-prem (cloud economics white paper)

[Web Sources: 15 articles analyzed, 3 DoD case studies, 2 vendor white papers]
```

**Implementation Phase**: Phase 10+ (Optional, after core features complete)  
**Estimated Effort**: 30-40 hours (web search integration + synthesis logic)

---

## 📑 Proposal Development Automation (Medium Priority)

### 7. **Proposal Kickoff Slide Generator**

**Description**: Auto-generates focused PowerPoint slides for proposal kickoff meetings with RFP salient points: evaluation factors, key requirements, win themes, compliance risks, timeline, and team assignments. Follows Shipley methodology.

**Use Case**:

- RFP release: Generate kickoff deck within 2 hours
- Capture manager briefs team on pursuit strategy
- Ensures team aligned on evaluation priorities and win strategy

**Priority**: 🟡 **MEDIUM** (High value for efficiency, but manual deck creation is alternative)

**Dependencies**:

- ⚠️ Needs: PydanticAI agents (Phase 9) for slide content generation
- ⚠️ Needs: PowerPoint generation library (python-pptx)
- ✅ Already possible: Query all required RFP intelligence

**Technical Approach**:

```python
# Phase 9: PowerPoint Generation
from pptx import Presentation
from pptx.util import Inches, Pt

async def generate_kickoff_slides(workspace: str):
    # Step 1: Query RFP intelligence
    eval_factors = await rag.aquery("What are the evaluation factors with weights?", workspace=workspace)
    requirements = await rag.aquery("What are the top 10 critical SHALL requirements?", workspace=workspace)
    themes = await rag.aquery("What strategic themes or pain points are mentioned?", workspace=workspace)
    timeline = await rag.aquery("What are the key dates: Q&A deadline, proposal due date, contract award?", workspace=workspace)

    # Step 2: Create PowerPoint
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    title.text = f"Proposal Kickoff: {workspace}"

    # Slide 2: RFP Overview
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "RFP Overview"
    content = slide.placeholders[1]
    content.text = f"""
    • Solicitation: {solicitation_number}
    • Agency: {agency}
    • Contract Type: {contract_type}
    • Period of Performance: {pop}
    • Estimated Value: {estimated_value}
    • Proposal Due: {due_date}
    """

    # Slide 3: Evaluation Factors (Critical!)
    # Slide 4: Top 10 Critical Requirements
    # Slide 5: Win Themes
    # Slide 6: Compliance Risks
    # Slide 7: Proposal Timeline & Milestones
    # Slide 8: Team Assignments

    prs.save(f'kickoff_{workspace}.pptx')
```

**Slide Deck Structure** (8-12 slides):

```
1. Title: "Proposal Kickoff - Navy MBOS Maritime Prepositioning"
2. RFP Overview: Solicitation #, agency, value, due date
3. Evaluation Factors: Visual chart with weights (40%, 30%, 20%, 10%)
4. Top 10 Critical Requirements: SHALL requirements from Section C
5. Win Themes: Navy pain points + our differentiators
6. Compliance Risks: Section L ankle biters, formatting requirements
7. Proposal Timeline: Color reviews (Pink, Red, Gold), milestones
8. Volume Outline: Proposed structure with page allocations
9. Team Assignments: Who owns what (BD, Capture, Technical, Ops, PM, Contracts)
10. Next Steps: Action items, meeting schedule
```

**Implementation Phase**: Phase 9 (PydanticAI + Export tools)  
**Estimated Effort**: 35-45 hours (Shipley methodology + PowerPoint generation)

---

### 8. **Shipley Color Review Milestone Prep**

**Description**: Generates PowerPoint slides for Pink Team, Red Team, and Gold Team reviews based on Shipley Guide principles. Includes automated task assignments by functional area (BD, Capture, Technical, Operations, PM, Contracts, Legal).

**Use Case**:

- Color team prep: Auto-generate review materials
- Task tracking: Ensure all functional areas have clear assignments
- Quality assurance: Shipley-compliant review process

**Priority**: 🟡 **MEDIUM** (Valuable for proposal quality, but manual process works)

**Dependencies**:

- ⚠️ Needs: PydanticAI agents (Phase 9) for slide generation
- ⚠️ Needs: Shipley Guide integration (prompt engineering)
- ⚠️ Needs: PowerPoint generation (python-pptx)

**Technical Approach**:

```python
# Phase 9: Shipley Color Review Generator
async def generate_color_review_slides(workspace: str, review_type: str):
    # review_type: 'pink', 'red', 'gold'

    shipley_prompts = {
        'pink': "Focus on compliance, outline structure, win themes coverage",
        'red': "Focus on technical accuracy, evaluation alignment, ghost/counter competitors",
        'gold': "Focus on grammar, formatting, final compliance check"
    }

    # Query RFP for review criteria
    compliance = await rag.aquery("List all Section L compliance requirements", workspace=workspace)
    eval_factors = await rag.aquery("What are evaluation factors and how to score well?", workspace=workspace)

    # Generate review slides
    prs = Presentation()

    # Slide 1: Review Objectives (Shipley-specific)
    # Slide 2: Compliance Checklist Status
    # Slide 3: Evaluation Factor Alignment
    # Slide 4: Win Themes Coverage Analysis
    # Slide 5: Risk Areas Identified
    # Slide 6: Action Items by Team

    # Task assignments by functional area
    assignments = {
        'BD': ['Competitive analysis', 'Pricing strategy review'],
        'Capture': ['Win themes validation', 'Customer hot buttons'],
        'Technical': ['Solution validation', 'Technical discriminators'],
        'Operations': ['Past performance relevance', 'Execution approach'],
        'PM': ['Schedule feasibility', 'Resource allocation'],
        'Contracts': ['Compliance with FAR clauses', 'T&Cs review'],
        'Legal': ['IP rights', 'Liability clauses', 'Protests risks']
    }

    prs.save(f'{review_type}_team_review_{workspace}.pptx')
```

**Slide Deck Structure**:

```
Pink Team Review (Compliance & Structure)
  1. Pink Team Objectives (Shipley Guide p.142-145)
  2. Compliance Status: 45/50 requirements addressed (90%)
  3. Outline vs RFP Alignment: Visual mapping
  4. Win Themes Coverage: 6/6 themes present
  5. Risks Identified: Missing cost narrative for CLIN 0003
  6. Action Items:
     - BD: Complete competitive pricing analysis by 10/15
     - Technical: Add cybersecurity discriminators by 10/16
     - PM: Validate schedule feasibility by 10/17

Red Team Review (Content Quality & Ghosting)
  1. Red Team Objectives (Shipley Guide p.146-150)
  2. Evaluation Factor Scoring Prediction
  3. Competitive Ghosting Analysis
  4. Technical Solution Validation
  5. Action Items by Team...

Gold Team Review (Final Polish)
  1. Gold Team Objectives (Shipley Guide p.151-153)
  2. Grammar/Formatting Checklist
  3. Final Compliance Verification
  4. Action Items: Final edits by 10/20, print by 10/21
```

**Implementation Phase**: Phase 9 (PydanticAI + Shipley integration)  
**Estimated Effort**: 40-50 hours (Shipley methodology + automation logic)

---

## 🏗️ Advanced Architecture Features (Future)

### 9. **IDIQ Task Order Knowledge Graph**

**Description**: Hierarchical knowledge graph for IDIQ contracts with base contract + ability to add/remove task order solicitations. Enables insights across task orders for solutioning patterns, pricing trends, and compliance requirements.

**Use Case**:

- IDIQ pursuit: Analyze base contract + 10 task orders for patterns
- Pricing strategy: Identify labor category trends across TOs
- Win strategy: Find what solutions won previous TOs

**Priority**: 🟢 **LOW-MEDIUM** (Niche use case, but high value for IDIQ pursuits)

**Dependencies**:

- ⚠️ **REQUIRES**: PostgreSQL hierarchical relationships (Phase 8+)
- ⚠️ **REQUIRES**: Custom graph schema for IDIQ structure
- ⚠️ Needs: Document hierarchy management (add/remove TOs)

**Technical Approach**:

```python
# Phase 10: IDIQ Knowledge Graph Architecture
#
# Graph Structure:
# BASE_CONTRACT (Navy SeaPort-NxG)
#   ├─ TASK_ORDER_1 (TO-001: IT Support)
#   │   ├─ SOLICITATION_001
#   │   ├─ PWS_001
#   │   ├─ EVALUATION_CRITERIA_001
#   │   └─ AWARDEE_INFO_001
#   ├─ TASK_ORDER_2 (TO-002: Cybersecurity)
#   │   ├─ SOLICITATION_002
#   │   └─ ...
#   └─ TASK_ORDER_3 (TO-003: Cloud Migration)

# PostgreSQL Schema
CREATE TABLE idiq_contracts (
    id UUID PRIMARY KEY,
    contract_name TEXT,
    ceiling_value DECIMAL,
    period_of_performance TEXT
);

CREATE TABLE task_orders (
    id UUID PRIMARY KEY,
    idiq_contract_id UUID REFERENCES idiq_contracts(id),
    to_number TEXT,
    title TEXT,
    value DECIMAL,
    award_date DATE,
    awardee TEXT
);

CREATE TABLE to_documents (
    id UUID PRIMARY KEY,
    task_order_id UUID REFERENCES task_orders(id),
    document_type TEXT,  -- 'solicitation', 'pws', 'evaluation'
    workspace TEXT  -- Points to LightRAG workspace
);

# Query patterns
async def analyze_idiq_trends(idiq_contract_id: str):
    # Analyze labor categories across all TOs
    labor_trends = """
    SELECT
        labor_category,
        AVG(hourly_rate) as avg_rate,
        COUNT(DISTINCT to_number) as to_count
    FROM task_orders
    WHERE idiq_contract_id = '{idiq_contract_id}'
    GROUP BY labor_category
    ORDER BY to_count DESC;
    """

    # Analyze winning solution patterns
    solution_patterns = await cross_query_workspaces([
        to['workspace'] for to in task_orders
    ], query="What technical solutions were proposed and won?")

    return {
        'labor_trends': labor_trends,
        'solution_patterns': solution_patterns
    }
```

**Output Format**:

```
IDIQ Analysis: Navy SeaPort-NxG (Base + 15 Task Orders)

📊 Labor Category Trends:
  Senior Software Engineer: $125/hr avg (15/15 TOs)
  Project Manager: $145/hr avg (12/15 TOs)
  Cybersecurity Analyst: $135/hr avg (10/15 TOs)

🏆 Winning Solution Patterns:
  - Cloud-native architecture (8/15 TOs, 53%)
  - Agile methodology (12/15 TOs, 80%)
  - DevSecOps pipeline (7/15 TOs, 47%)

📈 Pricing Intelligence:
  - TO-001 through TO-005: Cost-type, avg margin 8%
  - TO-006 through TO-015: FFP, avg margin 12%
  - Trend: Navy preferring FFP for well-defined scopes

💡 Competitive Intelligence:
  - Company A: Won 5/15 TOs (33%)
  - Company B: Won 4/15 TOs (27%)
  - Our company: Won 2/15 TOs (13%) - need to improve win rate
```

**Implementation Phase**: Phase 10+ (Complex, requires hierarchical graph design)  
**Estimated Effort**: 80-120 hours (custom schema + UI + analytics)

---

## 📋 Feature Priority Matrix

| Feature                         | Priority    | Phase   | Effort (hrs) | PostgreSQL Required? | PydanticAI Required? |
| ------------------------------- | ----------- | ------- | ------------ | -------------------- | -------------------- |
| **Proposal Outline Generator**  | 🔴 HIGH     | 9       | 40-60        | No                   | Yes                  |
| **Deliverables Extractor**      | 🔴 HIGH     | 8.3 + 9 | 20-30        | No                   | No                   |
| **Compliance Matrix Generator** | 🔴 HIGH     | 8.3 + 9 | 25-35        | No                   | No                   |
| **RFP Question Generator**      | 🟡 MED-HIGH | 9       | 30-40        | No                   | Yes                  |
| **Agency Trends Analyzer**      | 🟡 MEDIUM   | 8.3 + 9 | 40-50        | **YES**              | No                   |
| **Kickoff Slide Generator**     | 🟡 MEDIUM   | 9       | 35-45        | No                   | Yes                  |
| **Color Review Prep**           | 🟡 MEDIUM   | 9       | 40-50        | No                   | Yes                  |
| **Solution Workshop Assistant** | 🟢 MED-LOW  | 10+     | 30-40        | No                   | Yes + Web Search     |
| **IDIQ Task Order Graph**       | 🟢 LOW-MED  | 10+     | 80-120       | **YES**              | Optional             |

---

## 🗓️ Recommended Implementation Sequence

### **Phase 8: PostgreSQL Foundation** (Weeks 1-4)

_Already planned in main document_

- ✅ PostgreSQL migration
- ✅ Workspace management
- ✅ Cross-RFP analytics foundation

### **Phase 9: Core Capture Features** (Weeks 5-10, ~200 hours)

**Priority: High-value, high-usage features**

**Week 5-6: Deliverables + Compliance (50-65 hrs)**

1. Deliverables Intelligence Extractor
2. Compliance Matrix Generator
3. Excel export functionality

**Week 7-8: PydanticAI Setup + Proposal Outline (40-60 hrs)**

1. Install PydanticAI framework
2. Shipley methodology integration
3. Proposal Outline Generator (flagship feature)

**Week 9-10: Strategic Intelligence (60-80 hrs)**

1. RFP Question Generator
2. Agency Trends Analyzer (PostgreSQL analytics)
3. Testing and refinement

**Deliverables**:

- ✅ Export deliverables matrix to Excel
- ✅ Export compliance matrix to Excel
- ✅ Generate proposal outlines (Pydantic models)
- ✅ Generate RFP questions (max 7, strategic)
- ✅ Analyze agency trends (10+ RFPs required)

### **Phase 10: Presentation Automation** (Weeks 11-14, ~110 hours)

**Priority: Efficiency gains for capture managers**

**Week 11-12: Kickoff Slides (35-45 hrs)**

1. PowerPoint generation library setup
2. Kickoff slide template with Shipley structure
3. Auto-populate with RFP intelligence

**Week 13-14: Color Review Automation (40-50 hrs)**

1. Pink/Red/Gold team slide templates
2. Task assignment logic by functional area
3. Shipley Guide integration (compliance criteria)

**Week 15: Web-Enhanced Brainstorming (30-40 hrs)**

1. Web search integration (Tavily API)
2. Solution Workshop Assistant
3. Industry research synthesis

**Deliverables**:

- ✅ Generate kickoff PowerPoint decks
- ✅ Generate color review slide decks
- ✅ Web-enhanced solution brainstorming

### **Phase 11: Advanced Architecture** (Month 4+, ~100+ hours)

**Priority: Specialized use cases**

**IDIQ Task Order Knowledge Graph**

- Hierarchical graph design
- Task order management UI
- Cross-TO analytics

---

## 🎯 Quick Wins (Implement First)

### **Immediate (This Week) - No New Dependencies**

1. **Deliverables Query**: Already works! Just query for DELIVERABLE entities

   ```python
   deliverables = await rag.aquery(
       "List all deliverables with frequency and due dates",
       workspace="navy_mbos_2025"
   )
   ```

2. **Compliance Instructions Query**: Already works! Query SUBMISSION_INSTRUCTION entities

   ```python
   compliance = await rag.aquery(
       "What are all the Section L submission instructions and requirements?",
       workspace="navy_mbos_2025"
   )
   ```

3. **RFP Ambiguity Detection**: Query for conflicts
   ```python
   conflicts = await rag.aquery(
       "Identify any conflicting or ambiguous requirements between sections",
       workspace="navy_mbos_2025"
   )
   ```

### **Phase 8 (PostgreSQL) - Export Features**

1. **Excel Export Library**: Add `openpyxl` or `xlsxwriter` to dependencies
2. **CSV Export**: Simple pandas `to_csv()` for quick data extraction
3. **Cross-RFP Queries**: SQL analytics once PostgreSQL setup complete

### **Phase 9 (PydanticAI) - Structured Generation**

1. **Proposal Outline**: Flagship feature, highest ROI
2. **RFP Questions**: Strategic advantage, moderate effort
3. **Kickoff Slides**: High efficiency gain for capture managers

---

## 💡 Implementation Notes

### **Naming Conventions**

Original user terms → Renamed for clarity:

- ~~"Proposals outlines"~~ → **Proposal Outline Generator**
- ~~"deliverables"~~ → **Deliverables Intelligence Extractor**
- ~~"solution workshop assistant"~~ → **Solution Workshop Assistant (Web-Enhanced)**
- ~~"Compliance maxtix assistant"~~ → **Compliance Matrix Generator**
- ~~"RFP Question Generator"~~ → _(kept same)_
- ~~"Proposal Kickoff slides"~~ → **Proposal Kickoff Slide Generator**
- ~~"Shipley Milestone Color review prep slides"~~ → **Shipley Color Review Milestone Prep**
- ~~"Agency Trends"~~ → **Agency Trends Analyzer (Cross-RFP Intelligence)**
- ~~"IDIQ Task Order Knowlege Graph"~~ → **IDIQ Task Order Knowledge Graph**

### **Architecture Decisions**

**Why PydanticAI?**

- Type-safe structured outputs (proposal outlines, questions, slide content)
- Agent orchestration (multi-step reasoning for complex features)
- Validation (ensure generated content meets requirements)
- Already in roadmap (FUTURE_AGENT_ARCHITECTURE.md)

**Why PostgreSQL Required for Some Features?**

- **Agency Trends**: Needs SQL queries across 10+ RFPs
- **IDIQ Graph**: Hierarchical relationships require relational DB
- **Cross-RFP Analytics**: JSON files don't support efficient multi-document queries

**Why Export Tools Critical?**

- Capture managers need Excel/PowerPoint for client deliverables
- Integration with existing workflows (no one uses WebUI for final output)
- Compliance matrices, deliverables lists, cost estimates all require Excel

---

## 🚀 Revised Implementation Priority (User Decision: October 9, 2025)

### **CRITICAL PATH: Phase 8 PostgreSQL Only**

**User Requirement**: "The only feature I need to worry about is getting the ability to store multiple projects. Any feature beside the database integration is secondary at this stage. We have to get beyond the ability to only do one project/RFP at a time."

**Business Context**:

- **RFP Volume**: 10-20 proposals/year
- **RFP Timeline**: 30 days typical (90% of cases), 45 days occasionally
- **Current Blocker**: Can only work on 1 RFP at a time with JSON storage

**Immediate Action Plan**:

### **Week 1-2: Phase 8.1 - PostgreSQL Migration**

Focus: Get multi-workspace working, nothing else matters yet

1. ✅ **Setup PostgreSQL** (Docker recommended, 2-3 hours)
2. ✅ **Migrate Navy MBOS** (existing RFP, validate no data loss, 4-6 hours)
3. ✅ **Process 2-3 more RFPs** (test workspace isolation, 2-3 hours each)
4. ✅ **Validate switching works** (no cross-contamination, 2-3 hours)

**Success Criteria**: Can work on 3 different RFPs without conflicts

### **Week 3: Phase 8.2 - Minimal Workspace UI**

Focus: Simple dropdown selector, no fancy features

1. ✅ **Add workspace dropdown** (50-100 lines HTML/JavaScript, 4-6 hours)
2. ✅ **Backend switching API** (FastAPI endpoint, 2-3 hours)
3. ✅ **Test with 3-5 RFPs** (real usage validation, 4-6 hours)

**Success Criteria**: Can switch between RFPs in <2 seconds, queries isolated

### **Week 4: Validation & Documentation**

Focus: Production readiness, team adoption

1. ✅ **Performance testing** (5 workspaces, query latency <5 sec)
2. ✅ **Backup/recovery testing** (can rollback to JSON if needed)
3. ✅ **Documentation** (how to add new RFP, how to switch workspaces)
4. ✅ **Team training** (if applicable)

**Success Criteria**: System ready for production use with 10-20 RFPs/year

---

### **AFTER Phase 8 Complete: Feature Prioritization Workshop**

**When**: After processing 5+ RFPs in PostgreSQL workspaces  
**Why**: Real usage data reveals actual pain points  
**How**: Revisit feature wishlist, prioritize based on:

- Which manual tasks most time-consuming? (Proposal Outline? Compliance Matrix?)
- Which queries most frequent? (Deliverables? Evaluation factors?)
- Which exports most valuable? (Excel? PowerPoint?)

**Don't build Phase 9 features until Phase 8 proven in production.**

---

## 📚 Shipley Guide Digitization Strategy

**Current State**: Shipley PDFs in `docs/` folder  
**Goal**: Machine-readable format for PydanticAI agents (Phase 9+)

### **Option A: RAG-Anything Processing (Recommended)**

**Use your own system to digitize Shipley Guides!**

```powershell
# Step 1: Process Shipley PDFs through your RAG system
# Create separate workspace for reference materials
$env:POSTGRES_WORKSPACE = "reference_shipley_guides"

# Upload Shipley Capture Guide
curl -X POST http://localhost:9621/insert \
  -F "file=@docs/Shipley Capture Guide.pdf" \
  -F "mode=auto"

# Upload Shipley Proposal Guide
curl -X POST http://localhost:9621/insert \
  -F "file=@docs/Shipley Proposal Guide.pdf" \
  -F "mode=auto"

# Step 2: Query for methodology
# "What are the Shipley phases for capture planning?"
# "What are Pink Team, Red Team, Gold Team objectives?"
# "How does Shipley recommend structuring proposal outlines?"
```

**Benefits**:

- ✅ Uses your existing multimodal processing (tables, diagrams)
- ✅ Creates queryable Shipley knowledge graph
- ✅ Same entity extraction works on reference docs
- ✅ Can cross-reference: "Apply Shipley capture methodology to Navy MBOS RFP"

**Estimated Effort**: 2-3 hours (just upload PDFs, let system process)

### **Option B: Manual Markdown Extraction**

**For critical sections only** (Phase 9 implementation):

```markdown
# docs/shipley_methodology/proposal_outline_guidelines.md

## Shipley Proposal Outline Principles (Proposal Guide p.85-92)

### Volume Structure

- Separate technical and cost volumes (FAR requirement)
- Order volumes by evaluation factor importance
- Map each volume to specific Section M factor

### Section Organization

- Lead with executive summary (1-2 pages max)
- Structure sections around evaluation criteria
- Use active voice, present tense
- Include visual discriminators (charts, tables, diagrams)

### Page Allocation Formula

- Allocate pages proportional to evaluation weights
- Example: If Technical = 40%, Cost = 30%, Past Perf = 30%
  - 100-page proposal: Technical=40 pages, Cost=30 pages, Past Perf=30 pages

### Compliance Matrix Integration

- Every Section L instruction → Proposal section mapping
- Track SHALL/MUST requirements separately (zero tolerance)
- Color-code compliance status (Green/Yellow/Red)

...
```

**Benefits**:

- ✅ Human-curated (only extract what's needed)
- ✅ Markdown easy to reference in prompts
- ✅ Version control (track methodology updates)

**Estimated Effort**: 8-12 hours (extract key sections only)

### **Option C: Hybrid Approach (Best)**

1. **Phase 8**: Process Shipley PDFs through RAG system (automatic)
2. **Phase 9**: Extract critical sections to Markdown (manual, as needed)
3. **Phase 10**: Build PydanticAI agents that query Shipley workspace

**Example query pattern**:

```python
# Query Shipley knowledge base for methodology
shipley_guidance = await rag.aquery(
    "What are Shipley's recommendations for Pink Team review objectives?",
    workspace="reference_shipley_guides"
)

# Apply to current RFP
pink_team_slides = await generate_color_review_slides(
    workspace="navy_mbos_2025",
    review_type="pink",
    methodology=shipley_guidance
)
```

---

## 🎯 Simplified Next Steps (Focus on PostgreSQL Only)

### **This Week (Branch 004 Completion)**

1. ✅ **Test query performance** (last todo)
2. ✅ **Merge to main** (validate multimodal success)
3. ✅ **Create Branch 005**: `git checkout -b 005-postgresql-migration`

### **Week 1-2 (PostgreSQL Setup)**

1. ✅ **Install PostgreSQL** (Docker command in Appendix B)
2. ✅ **Migrate Navy MBOS** (migration script provided)
3. ✅ **Process 2 new RFPs** (test workspace isolation)
4. ✅ **Document any issues** (update this plan)

### **Week 3 (Workspace UI)**

1. ✅ **Add dropdown selector** (HTML code provided in Phase 8.2)
2. ✅ **Test workspace switching** (performance <2 sec)
3. ✅ **Process 2 more RFPs** (reach 5 total workspaces)

### **Week 4 (Production Readiness)**

1. ✅ **Performance testing** (5 workspaces, queries <5 sec)
2. ✅ **Backup strategy** (pg_dump automation)
3. ✅ **Rollback testing** (verify can revert to JSON)
4. ✅ **Merge Branch 005 to main** (PostgreSQL migration complete)

### **Month 2+ (Feature Evaluation)**

1. ✅ **Use system for 5+ real RFPs** (identify pain points)
2. ✅ **Prioritize features** based on actual usage
3. ✅ **Plan Phase 9** (only after Phase 8 proven)

**DO NOT build Phase 9 features until Phase 8 works in production!**

---

## 📊 Effort Estimate (PostgreSQL Only)

| Phase                 | Duration      | Dev Hours       | User Testing Hours      | Total           |
| --------------------- | ------------- | --------------- | ----------------------- | --------------- |
| 8.1: PostgreSQL Setup | Week 1-2      | 20-30           | 8-12 (process RFPs)     | 28-42           |
| 8.2: Workspace UI     | Week 3        | 10-15           | 4-6 (test switching)    | 14-21           |
| 8.3: Validation       | Week 4        | 8-12            | 4-6 (performance tests) | 12-18           |
| **Total**             | **3-4 weeks** | **38-57 hours** | **16-24 hours**         | **54-81 hours** |

**Timeline with 10-20 RFPs/year**:

- 30-day RFP cycle × 15 RFPs/year = 450 days/year in proposals
- PostgreSQL investment: 54-81 hours = ~2 weeks one-time
- **Payback**: Immediate (can work on multiple RFPs concurrently)

---

## 🚨 Critical Success Factors

### **Must-Haves for Phase 8**

- ✅ **Workspace isolation**: Queries don't cross-contaminate
- ✅ **Switching speed**: <2 seconds to switch RFPs
- ✅ **Query performance**: No regression vs JSON (<5 sec)
- ✅ **Rollback plan**: Can revert to JSON if PostgreSQL fails

### **Nice-to-Haves (Defer to Phase 9)**

- ❌ Proposal outline generation (PydanticAI)
- ❌ Compliance matrix export (Excel)
- ❌ Deliverables extraction (CSV)
- ❌ RFP question generation (agents)
- ❌ Kickoff slide automation (PowerPoint)

**User Priority**: "Any feature beside the database integration is secondary at this stage."

---

## 📝 Document Status

**Status**: Refocused on PostgreSQL migration only  
**Last Updated**: October 9, 2025  
**User Guidance**: Focus 100% on Phase 8, defer all Phase 9+ features  
**Next Milestone**: Complete Branch 004, start Branch 005 (PostgreSQL)  
**Feature Prioritization**: After Phase 8 production validation (Month 2+)

---

## 🎯 Success Definition

**Phase 8 Complete When**:

1. Can process 10-20 RFPs in separate PostgreSQL workspaces
2. Can switch between RFPs in <2 seconds via WebUI dropdown
3. Queries isolated per workspace (no cross-contamination)
4. System performs at JSON baseline levels (<5 sec queries)
5. Team comfortable with PostgreSQL workflow

**Then and only then**: Prioritize Phase 9 features based on real usage patterns.

**Expected Timeline**: 3-4 weeks development + 1-2 months production validation = Phase 9 decision by Month 3-4.
