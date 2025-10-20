# PostgreSQL 18 Implementation - Master Plan

**Feature**: Multi-workspace data warehouse with event sourcing for RFP intelligence  
**Status**: Planning Phase  
**Target Version**: PostgreSQL 18.1+  
**Timeline**: 8-12 weeks (Branch 010, Branch 011)

---

## 🎯 Vision

Transform GovCon-Capture-Vibe from single-workspace JSON storage to enterprise-grade PostgreSQL data warehouse that supports:

1. **Multi-workspace storage**: 100+ RFPs in single database
2. **Event sourcing**: Immutable snapshots of RFPs, amendments, proposals, feedback
3. **Agent intelligence**: Store compliance checklists, gap analyses, proposal outlines
4. **Cross-RFP queries**: Clause trends, factor weights, lessons learned
5. **IDIQ hierarchies**: Parent-child tracking for task orders

---

## 📚 Documentation Structure

### 1. Planning Documents (Reference Architecture)

| Document                              | Purpose                                    | Status      |
| ------------------------------------- | ------------------------------------------ | ----------- |
| **README.md** (this file)             | Master plan and navigation                 | ✅ Complete |
| **01_SCHEMA_DESIGN.md**               | Complete 17-table schema for Branch 010    | ✅ Complete |
| **02_EVENT_SOURCING_ARCHITECTURE.md** | Advanced event-based design for Branch 011 | ✅ Complete |
| **03_FILE_MIGRATION_MAP.md**          | JSON → PostgreSQL migration guide          | ✅ Complete |

### 2. Implementation Tasks (PRD-Style - Created As Needed)

Each implementation task gets its own focused document:

| Task                         | Document                            | Branch     | Status                | Estimated Time |
| ---------------------------- | ----------------------------------- | ---------- | --------------------- | -------------- |
| PostgreSQL 18 local setup    | `TASK_01_LOCAL_SETUP.md`            | Branch 010 | ✅ Complete           | Week 1         |
| Workspace selection UI       | `TASK_02_WORKSPACE_SELECTION_UI.md` | Branch 010 | 🔴 **URGENT**         | Week 2         |
| Schema creation (17 tables)  | `TASK_03_SCHEMA_CREATION.md`        | Branch 010 | 📋 Create when needed | Week 2-3       |
| JSON migration script        | `TASK_04_JSON_MIGRATION.md`         | Branch 010 | 📋 Create when needed | Week 3-4       |
| Update app.py for PostgreSQL | `TASK_05_APP_INTEGRATION.md`        | Branch 010 | 📋 Create when needed | Week 4-5       |
| Test with Navy MBOS baseline | `TASK_06_BASELINE_TESTING.md`       | Branch 010 | 📋 Create when needed | Week 5         |
| Event sourcing tables        | `TASK_07_EVENT_TABLES.md`           | Branch 011 | 📋 Create when needed | Week 6-7       |
| Entity matching agent        | `TASK_08_MATCHING_AGENT.md`         | Branch 011 | 📋 Create when needed | Week 8-9       |
| Amendment processing         | `TASK_09_AMENDMENT_FLOW.md`         | Branch 011 | 📋 Create when needed | Week 10        |
| Proposal comparison          | `TASK_10_PROPOSAL_COMPARISON.md`    | Branch 011 | 📋 Create when needed | Week 11        |
| Lessons learned dashboard    | `TASK_11_LESSONS_LEARNED.md`        | Branch 011 | 📋 Create when needed | Week 12        |

---

## 🏗️ Architecture Evolution

### Phase 1: Simple Schema (Branch 010) - Weeks 1-5

**Goal**: Replace JSON files with PostgreSQL, maintain existing functionality

```
Current State:
rag_storage/
├── graph_chunk_entity_relation.graphml
├── kv_store_full_entities.json
└── ... (9 more JSON files)

Target State (Branch 010):
PostgreSQL Database (17 tables)
├── rfp_documents (1 row per RFP)
├── entities (594 rows)
├── relationships (250 rows)
├── requirements (80 rows - denormalized)
├── evaluation_factors (5 rows - denormalized)
└── ... (12 more tables)
```

**Benefits**:

- ✅ Multi-workspace support (100+ RFPs)
- ✅ SQL queries across RFPs
- ✅ Faster semantic search (pgvector)
- ✅ Agent output storage

**Limitations**:

- ❌ No amendment tracking
- ❌ No proposal comparison
- ❌ Single snapshot per RFP

---

### Phase 2: Event Sourcing (Branch 011) - Weeks 6-12

**Goal**: Immutable event streams for RFP → Amendment → Proposal → Feedback

```
PostgreSQL Database (4 new tables)
├── document_events (event log)
│   ├── Event 1: RFP_INITIAL
│   ├── Event 2: AMENDMENT_0001
│   ├── Event 3: PROPOSAL_SUBMISSION
│   └── Event 4: EVALUATION_FEEDBACK
│
├── entity_snapshots (per-event entities)
│   ├── 594 entities (event-1)
│   ├── 620 entities (event-2) - includes changes
│   ├── 450 entities (event-3) - proposal content
│   └── 85 entities (event-4) - feedback
│
├── relationship_snapshots (per-event relationships)
│
└── entity_matches (cross-event linking)
    ├── REQ_001 (event-1) → REQ_001_AMENDED (event-2) [EVOLVED]
    ├── REQ_001_AMENDED (event-2) → PROPOSED_SOL_5 (event-3) [REFERENCED]
    └── PROPOSED_SOL_5 (event-3) → WEAKNESS_TECH_2 (event-4) [REFERENCED]
```

**Benefits**:

- ✅ Immutable audit trail (Git-style)
- ✅ Amendment change detection
- ✅ Proposal → RFP traceability
- ✅ Lessons learned from feedback
- ✅ Cross-event queries (recursive SQL)

---

## 🔑 Key Design Decisions

### 1. Why PostgreSQL 18?

- **pgvector 0.8.0**: 16x faster HNSW indexing (vs pgvector 0.5.0)
- **Parallel hash joins**: 2-3x faster cross-table queries
- **JSONB improvements**: Faster metadata parsing
- **Incremental sorting**: Better performance on large result sets
- **Released**: September 2024 (stable)

### 2. Why Workspace Isolation?

**Problem**: Multiple RFPs, amendments, proposals stored in one database need logical separation without multiple databases.

**Solution**: LightRAG's built-in `workspace` parameter provides row-level isolation in PostgreSQL:

```sql
-- Each workspace has its own entities
SELECT * FROM entities WHERE workspace = 'navy_mbos_2025';
SELECT * FROM entities WHERE workspace = 'army_comms_2025';
```

**Benefits**:

- ✅ One PostgreSQL database, 100+ RFPs
- ✅ Cross-workspace queries (lessons learned)
- ✅ Event sourcing with workspace hierarchy
- ✅ Zero data contamination

**Implementation**: TASK_02 adds WebUI workspace dropdown for document uploads.

### 3. Why Event Sourcing?

**Problem**: Amendments modify requirements, proposals respond to RFPs, feedback references proposals. If you update entities in-place, you lose history.

**Solution**: Each document processing creates an **immutable event** with its own knowledge graph. Entity matching links events without modifying source data.

**Analogy**: Git commits vs. overwriting files.

### 3. Why Denormalized Tables?

**Problem**: Agents need fast queries like "show all MANDATORY requirements" without parsing JSONB metadata.

**Solution**: `requirements` table extracts REQUIREMENT entities with clean columns (criticality_level, priority_score, modal_verb). Same for evaluation_factors, clauses, deliverables.

**Trade-off**: More storage (minimal) for 10-100x faster queries.

### 5. Why Hybrid Storage (Relational + JSONB)?

**Problem**: Entity types have unique fields (REQUIREMENT has criticality, EVALUATION_FACTOR has weight). Can't predict all future fields.

**Solution**:

- **Relational columns**: Common fields (entity_name, entity_type, description)
- **JSONB column**: Entity-specific metadata (flexible schema)

**Benefit**: No ALTER TABLE migrations when adding new entity types or fields.

---

## 🎯 Success Criteria

### Branch 010 (Simple Schema)

- ✅ PostgreSQL 18 running locally
- ✅ 17 tables created with indexes
- ✅ Navy MBOS RFP migrated from JSON → PostgreSQL
- ✅ app.py queries PostgreSQL (not JSON files)
- ✅ Processing time ≤ 69 seconds (no regression)
- ✅ Agent outputs stored in database (compliance, gap, outline)

### Branch 011 (Event Sourcing)

- ✅ 4 event-sourcing tables added
- ✅ Amendment processing creates new event (preserves original)
- ✅ Entity matching agent achieves ≥90% accuracy
- ✅ Proposal comparison queries working
- ✅ Lessons learned dashboard functional
- ✅ Cross-event recursive queries ≤ 2 seconds

---

## 📊 Cost Estimates

### Local Development (Weeks 1-5)

- **PostgreSQL 18**: Free (open source)
- **Storage**: ~2 MB per RFP × 10 RFPs = 20 MB (negligible)
- **RAM**: 4 GB recommended for pgvector indexing

### AWS RDS Production (Weeks 6+)

- **Instance**: db.t3.medium (2 vCPU, 4 GB RAM) = $61/month
- **Storage**: 100 GB SSD = $10/month
- **Backup**: Automated daily snapshots = $5/month
- **Total**: ~$76/month for 1,000 RFPs

### Development Time

- **Branch 010**: 40-60 hours (5 weeks × 8-12 hrs/week)
- **Branch 011**: 60-80 hours (7 weeks × 8-12 hrs/week)
- **Total**: 100-140 hours over 12 weeks

---

## 🚀 Getting Started

### Step 1: Read Planning Documents (This Week)

1. **README.md** (this file) - Understand overall architecture and timeline
2. **01_SCHEMA_DESIGN.md** - Review 17-table structure
3. **02_EVENT_SOURCING_ARCHITECTURE.md** - Review event-based design (Branch 011)
4. **03_FILE_MIGRATION_MAP.md** - Review JSON → PostgreSQL mapping

### Step 2: Set Up PostgreSQL 18 (Week 1)

Follow **TASK_01_LOCAL_SETUP.md** to install PostgreSQL 18 + pgvector locally.

**Success Criteria**: PostgreSQL 18.1+ running, pgvector installed, test connection works

### Step 3: Implement Workspace Selection UI (Week 2) - 🔴 **URGENT**

Follow **TASK_02_WORKSPACE_SELECTION_UI.md** to add workspace dropdown to WebUI.

**Why This is Critical**:

- Blocks all event sourcing (Branch 011) - cannot process amendments/proposals without workspace isolation
- Prevents data contamination - without workspace selection, all RFPs mix in PostgreSQL
- Required for multi-RFP support - the core reason for PostgreSQL migration

**Success Criteria**:

- WebUI shows workspace dropdown
- Users can create/select workspaces
- Documents process to correct workspace (verify in PostgreSQL)
- Workspace isolation confirmed (entities don't leak between workspaces)

### Step 4: Create Schema (Weeks 2-3)

Follow **TASK_03_SCHEMA_CREATION.md** (create from 01_SCHEMA_DESIGN.md when ready) to create 17 tables.

**Success Criteria**: All 17 tables created with indexes, no SQL errors

### Step 5: Migrate Navy MBOS (Weeks 3-4)

Follow **TASK_04_JSON_MIGRATION.md** (create from 03_FILE_MIGRATION_MAP.md when ready) to migrate baseline RFP.

**Success Criteria**: 594 entities, 250 relationships migrated successfully

### Step 6: Update Application (Weeks 4-5)

Follow **TASK_05_APP_INTEGRATION.md** (create when ready) to update `src/raganything_server.py` for PostgreSQL.

**Success Criteria**: app.py queries PostgreSQL, WebUI works, no performance regression

### Step 7: Baseline Testing (Week 5)

Follow **TASK_06_BASELINE_TESTING.md** (create when ready) to validate PostgreSQL migration with Navy MBOS.

**Success Criteria**: Processing time ≤ 69 seconds, entity count matches, queries work

---

## 🔗 Related Documentation

### Current System (Branch 008)

- `docs/ARCHITECTURE.md` - Current JSON-based system architecture
- `.github/copilot-instructions.md` - Complete system overview
- `docs/capture-intelligence/SHIPLEY_LLM_CURATED_REFERENCE.md` - Shipley methodology

### PostgreSQL Implementation (This Folder)

- `README.md` (this file) - Master plan and navigation
- `01_SCHEMA_DESIGN.md` - 17-table schema reference
- `02_EVENT_SOURCING_ARCHITECTURE.md` - Event-based design (Branch 011)
- `03_FILE_MIGRATION_MAP.md` - JSON → PostgreSQL migration mapping
- `TASK_01_LOCAL_SETUP.md` - PostgreSQL 18 installation guide
- `TASK_02_WORKSPACE_SELECTION_UI.md` - Workspace dropdown implementation (URGENT)

### Future Features (After PostgreSQL Complete)

- `docs/capture-intelligence/FEATURE_ROADMAP.md` - Phase 9+ feature planning
- `docs/agents/PYDANTICAI_DECISION_SUMMARY.md` - Agent architecture
- `docs/amendments/AMENDMENT_HANDLING_ROADMAP.md` - Amendment processing

---

## 📝 Document Changelog

| Date       | Change                                      | Author         |
| ---------- | ------------------------------------------- | -------------- |
| 2025-10-20 | Initial master plan created                 | Copilot + User |
| 2025-10-20 | Moved existing docs to postgresql18/ folder | Copilot        |
| TBD        | Add TASK_01-10 implementation guides        | TBD            |

---

**Next Steps**:

1. Review this master plan
2. Create `02_EVENT_SOURCING_ARCHITECTURE.md` with detailed event-based design
3. Start `TASK_01_LOCAL_SETUP.md` for Week 1 implementation

**Questions?** See individual planning documents or task guides for details.
