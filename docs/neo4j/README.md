# Neo4j Integration Documentation

**Purpose**: Neo4j graph database migration planning and implementation guides  
**Status**: 🚧 Foundation Phase (Branch 011)  
**Created**: October 26, 2025

---

## 📁 Directory Structure

```
docs/neo4j/
├── README.md (this file)
├── WORKSPACE_SELECTION_DESIGN.md (planned - Week 2)
├── API_SPECIFICATION.md (planned - Week 2)
├── TASK_01_NEO4J_SETUP.md (planned - Week 2)
└── MIGRATION_STRATEGY.md (planned - Week 3)
```

---

## 🎯 Neo4j Migration Overview

### Why Neo4j?

**Primary Graph Store** (replacing PostgreSQL 18 plan):

- ✅ **Native LightRAG support**: `Neo4JStorage` is production-tested
- ✅ **Workspace isolation**: Labels like `:navy_mbos_2025` = workspace
- ✅ **Performance**: 10-100x faster graph queries than PostgreSQL AGE
- ✅ **Simplicity**: Schema-free (no 17-table design needed)
- ✅ **Cost**: $0 (self-hosted) vs $71/month (AWS RDS)

### Key Features for GovCon Intelligence

**1. Workspace Isolation via Labels**

```cypher
// Navy MBOS workspace
MATCH (n:REQUIREMENT:navy_mbos_2025)
WHERE n.criticality_level >= 0.80
RETURN n

// Army Comms workspace (different RFP, isolated)
MATCH (n:REQUIREMENT:army_comms_2025)
RETURN n
```

**2. Section L↔M Relationship Queries**

```cypher
// Find evaluation factors linked to submission instructions
MATCH (i:SUBMISSION_INSTRUCTION)-[:GUIDES]->(f:EVALUATION_FACTOR)
WHERE i.workspace = 'navy_mbos_2025'
RETURN i.description, f.name, f.weight
ORDER BY f.weight DESC
```

**3. Cross-RFP Intelligence** (future capability)

```cypher
// Historical evaluation factor weights across Navy contracts
MATCH (f:EVALUATION_FACTOR)
WHERE f.agency = 'Navy' AND f.entity_type CONTAINS 'Technical Approach'
RETURN AVG(f.weight) as avg_weight, COUNT(*) as sample_size
```

---

## 📋 Implementation Phases

### Phase 1: Foundation (Branch 011 - Current)

**Focus**: Cleanup and design work

- [x] Create documentation structure
- [ ] Design workspace selection UI (Week 2)
- [ ] Document API endpoints (Week 2)
- [ ] Create Neo4j setup guide (Week 2)
- [ ] Draft migration strategy (Week 3)

### Phase 2: Integration (Branch 012 - Next)

**Focus**: Actual Neo4j installation and configuration

- [ ] Install Neo4j Community Edition (Docker)
- [ ] Configure LightRAG `Neo4JStorage`
- [ ] Migrate GraphML → Neo4j (test data)
- [ ] Implement workspace selection UI
- [ ] Performance benchmarking

### Phase 3: Production (Branch 013+)

**Focus**: Advanced features and scale

- [ ] Event sourcing (RFP → Amendment → Proposal)
- [ ] Cross-RFP intelligence queries
- [ ] Neo4j AuraDB deployment (optional cloud)
- [ ] Hybrid PostgreSQL integration (agent outputs only)

---

## 🔗 Key References

### LightRAG Documentation

- [Neo4JStorage Implementation](https://github.com/HKUDS/LightRAG/blob/main/lightrag/kg/neo4j_impl.py)
- [LightRAG WebUI (React 19)](https://github.com/HKUDS/LightRAG/tree/main/lightrag_webui)
- [LightRAG Constants](https://github.com/HKUDS/LightRAG/blob/main/lightrag/constants.py)

### Neo4j Resources

- [Neo4j Community Edition](https://neo4j.com/deployment-center/)
- [Neo4j Docker Images](https://hub.docker.com/_/neo4j)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Browser](https://neo4j.com/docs/browser-manual/current/)

### Related Documentation

- `../BRANCH_011_NEO4J_FOUNDATION.md` - Branch charter and objectives
- `../postgresql18/README.md` - Archived PostgreSQL 18 plan (reference only)
- `../ARCHITECTURE.md` - System architecture (to be updated for Neo4j)
- `../ontology/` - 17 government contracting entity types (Neo4j labels)

---

## 🚀 Quick Start (Coming in Branch 012)

**Preview of Neo4j Setup**:

```bash
# 1. Pull Neo4j Docker image
docker pull neo4j:latest

# 2. Run Neo4j container
docker run -d \
  --name neo4j-govcon \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest

# 3. Configure LightRAG (.env)
GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# 4. Verify connection
curl http://localhost:7474
```

**Full guide coming in**: `TASK_01_NEO4J_SETUP.md`

---

## 📊 Current vs Future State

### Current State (Branch 010)

```
Storage: JSON files (GraphML + kv_store)
Location: ./rag_storage/default/
Size: ~6.1 MB per RFP
Workspace Isolation: None (file paths only)
Cross-RFP Queries: Manual parsing
```

### Target State (Branch 012+)

```
Storage: Neo4j graph database
Location: bolt://localhost:7687
Size: Similar (compressed nodes/relationships)
Workspace Isolation: Native labels (:workspace_name)
Cross-RFP Queries: Cypher (sub-second responses)
```

---

## ⚠️ Important Notes

### What Neo4j Does NOT Replace

**Keep Current JSON Storage For**:

1. **Document Processing**: RAG-Anything still uses `./rag_storage/` for intermediate files
2. **LightRAG KV Store**: Text chunks stored in JSON (separate from graph)
3. **Backups**: GraphML exports for disaster recovery

**Neo4j Replaces**:

- ❌ `graph_chunk_entity_relation.graphml` → Neo4j graph
- ❌ Manual relationship queries → Cypher queries
- ❌ Workspace file paths → Workspace labels

### License & Cost

**Neo4j Community Edition**:

- ✅ Free and open source (GPLv3)
- ✅ Unlimited nodes and relationships
- ✅ Single-server deployment
- ❌ No clustering (not needed for current scale)

**Neo4j AuraDB** (optional cloud):

- 💰 $45/month (Professional tier)
- ✅ Managed service, automated backups
- ✅ Multi-region support
- ❌ Overkill for development (use Community Edition)

---

## 📝 Documentation To-Do

### Week 2 Deliverables

- [ ] `WORKSPACE_SELECTION_DESIGN.md` - UI/UX design for workspace dropdown
- [ ] `API_SPECIFICATION.md` - `/workspaces`, `/insert` endpoint contracts
- [ ] `TASK_01_NEO4J_SETUP.md` - Docker installation guide with test queries

### Week 3 Deliverables

- [ ] `MIGRATION_STRATEGY.md` - Phased rollout plan with rollback strategy
- [ ] `PERFORMANCE_BASELINE.md` - Neo4j vs JSON benchmarks
- [ ] `TESTING_PLAN.md` - 5-10 RFP test corpus for validation

---

**Last Updated**: October 26, 2025  
**Next Milestone**: Week 2 - Workspace selection design + Neo4j setup guide  
**Status**: Foundation phase (design work, no implementation yet)
