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

### 1. Planning Documents (This Folder)

| Document                              | Purpose                                    | Status         |
| ------------------------------------- | ------------------------------------------ | -------------- |
| **README.md** (this file)             | Master plan and navigation                 | ✅ Complete    |
| **01_SCHEMA_DESIGN.md**               | Complete 17-table schema for Branch 010    | ✅ Complete    |
| **02_EVENT_SOURCING_ARCHITECTURE.md** | Advanced event-based design for Branch 011 | 🚧 In Progress |
| **03_FILE_MIGRATION_MAP.md**          | JSON → PostgreSQL migration guide          | ✅ Complete    |
| **04_ENTITY_MATCHING_ALGORITHM.md**   | Agent-powered cross-event linking          | 📋 Planned     |
| **05_POSTGRESQL18_SETUP_GUIDE.md**    | Installation and configuration             | 📋 Planned     |

### 2. Implementation Tasks (PRD-Style)

Each implementation task gets its own focused document:

| Task                         | Document                         | Branch     | Estimated Time |
| ---------------------------- | -------------------------------- | ---------- | -------------- |
| PostgreSQL 18 local setup    | `TASK_01_LOCAL_SETUP.md`         | Branch 010 | Week 1         |
| Schema creation (17 tables)  | `TASK_02_SCHEMA_CREATION.md`     | Branch 010 | Week 2         |
| JSON migration script        | `TASK_03_JSON_MIGRATION.md`      | Branch 010 | Week 3         |
| Update app.py for PostgreSQL | `TASK_04_APP_INTEGRATION.md`     | Branch 010 | Week 4         |
| Test with Navy MBOS baseline | `TASK_05_BASELINE_TESTING.md`    | Branch 010 | Week 5         |
| Event sourcing tables        | `TASK_06_EVENT_TABLES.md`        | Branch 011 | Week 6-7       |
| Entity matching agent        | `TASK_07_MATCHING_AGENT.md`      | Branch 011 | Week 8-9       |
| Amendment processing         | `TASK_08_AMENDMENT_FLOW.md`      | Branch 011 | Week 10        |
| Proposal comparison          | `TASK_09_PROPOSAL_COMPARISON.md` | Branch 011 | Week 11        |
| Lessons learned dashboard    | `TASK_10_LESSONS_LEARNED.md`     | Branch 011 | Week 12        |

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

### 2. Why Event Sourcing?

**Problem**: Amendments modify requirements, proposals respond to RFPs, feedback references proposals. If you update entities in-place, you lose history.

**Solution**: Each document processing creates an **immutable event** with its own knowledge graph. Entity matching links events without modifying source data.

**Analogy**: Git commits vs. overwriting files.

### 3. Why Denormalized Tables?

**Problem**: Agents need fast queries like "show all MANDATORY requirements" without parsing JSONB metadata.

**Solution**: `requirements` table extracts REQUIREMENT entities with clean columns (criticality_level, priority_score, modal_verb). Same for evaluation_factors, clauses, deliverables.

**Trade-off**: More storage (minimal) for 10-100x faster queries.

### 4. Why Hybrid Storage (Relational + JSONB)?

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

1. **01_SCHEMA_DESIGN.md** - Understand 17-table structure
2. **02_EVENT_SOURCING_ARCHITECTURE.md** - Understand event-based design
3. **03_FILE_MIGRATION_MAP.md** - Understand JSON → PostgreSQL mapping

### Step 2: Set Up PostgreSQL 18 (Week 1)

Follow **TASK_01_LOCAL_SETUP.md** to install PostgreSQL 18 + pgvector + Apache AGE locally.

### Step 3: Create Schema (Week 2)

Run SQL scripts from **TASK_02_SCHEMA_CREATION.md** to create 17 tables.

### Step 4: Migrate Navy MBOS (Week 3)

Run Python migration script from **TASK_03_JSON_MIGRATION.md** to move your baseline RFP.

### Step 5: Update Application (Week 4-5)

Follow **TASK_04_APP_INTEGRATION.md** to update `src/raganything_server.py` to query PostgreSQL.

---

## 🔗 Related Documentation

### Current System (Branch 008)

- `docs/ARCHITECTURE.md` - Current JSON-based system
- `.github/copilot-instructions.md` - System overview
- `docs/SHIPLEY_LLM_CURATED_REFERENCE.md` - Shipley methodology

### Future Features (After PostgreSQL)

- `docs/PYDANTICAI_DECISION_SUMMARY.md` - Branch 009 agent implementation
- `docs/AMENDMENT_HANDLING_ROADMAP.md` - Amendment processing (enabled by event sourcing)
- `docs/CAPTURE_INTELLIGENCE_PATTERNS.md` - Lessons learned queries

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
