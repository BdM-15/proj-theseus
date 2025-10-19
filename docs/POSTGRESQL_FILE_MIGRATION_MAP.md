# PostgreSQL File Migration Map

**What Happens to Each `/rag_storage` File?**

**Date**: October 19, 2025  
**Purpose**: Simple explanation of how current JSON files map to PostgreSQL tables

---

## 📁 Current `/rag_storage` Files (11 files per RFP)

```
rag_storage/
├── graph_chunk_entity_relation.graphml      # NetworkX graph (entities + relationships)
├── kv_store_full_entities.json              # Entity metadata (name, type, description)
├── kv_store_full_relations.json             # Relationship metadata (source, target, type)
├── kv_store_text_chunks.json                # Document chunks (4096-token chunks)
├── kv_store_full_docs.json                  # Full document text
├── kv_store_doc_status.json                 # Processing status
├── kv_store_llm_response_cache.json         # LLM API cache (cost optimization)
├── kv_store_parse_cache.json                # MinerU parsing cache
├── vdb_chunks.json                          # Chunk embeddings (vector DB)
├── vdb_entities.json                        # Entity embeddings (vector DB)
└── vdb_relationships.json                   # Relationship embeddings (vector DB)
```

---

## 🎯 Short Answer to Your Question

**Q: "So the graphml file is the only file that goes into the workspace row of the table and not the other files from /rag_storage?"**

**A: NO - ALL 11 files get migrated to PostgreSQL, but in different ways:**

1. **GraphML file** → Stored as **blob** in `rfp_documents.graphml_data` (backup only)
2. **JSON KV store files** → Converted to **relational table rows** (primary storage)
3. **Vector DB files** → Converted to **pgvector columns** (semantic search)

---

## 📊 Migration Map (File → PostgreSQL)

| Current File                            | Size   | PostgreSQL Destination               | Storage Type        | Why?                                    |
| --------------------------------------- | ------ | ------------------------------------ | ------------------- | --------------------------------------- |
| **graph_chunk_entity_relation.graphml** | 500 KB | `rfp_documents.graphml_data` (BYTEA) | **Binary blob**     | Backup/export original graph            |
| **kv_store_full_entities.json**         | 300 KB | `entities` table (594 rows)          | **Relational rows** | Queryable entities with JSONB metadata  |
| **kv_store_full_relations.json**        | 100 KB | `relationships` table (250 rows)     | **Relational rows** | Queryable relationships                 |
| **kv_store_text_chunks.json**           | 200 KB | `document_chunks` table (15 rows)    | **Relational rows** | Searchable 4096-token chunks            |
| **kv_store_full_docs.json**             | 150 KB | `rfp_documents.full_text` (TEXT)     | **Single column**   | Full document text (searchable)         |
| **kv_store_doc_status.json**            | 1 KB   | `rfp_documents.processing_status`    | **Single column**   | "completed", "failed", "pending"        |
| **kv_store_llm_response_cache.json**    | 50 KB  | `llm_cache` table (120 rows)         | **Relational rows** | Cost optimization (reuse API responses) |
| **kv_store_parse_cache.json**           | 40 KB  | `parse_cache` table (1 row)          | **Relational rows** | MinerU parsing cache (avoid re-parsing) |
| **vdb_chunks.json**                     | 180 KB | `document_chunks.embedding` (vector) | **pgvector column** | Semantic search on chunks               |
| **vdb_entities.json**                   | 250 KB | `entities.embedding` (vector)        | **pgvector column** | Semantic search on entities             |
| **vdb_relationships.json**              | 120 KB | `relationships.embedding` (vector)   | **pgvector column** | Semantic search on relationships        |

**Total**: 11 files (~2 MB) → 8 PostgreSQL tables

---

## 🔍 Visual Breakdown

### What "Workspace Row" Actually Means

The `rfp_documents` table is the **master record** for each RFP (like a workspace). Here's what ONE row contains:

```sql
-- ONE ROW in rfp_documents table = ONE RFP workspace
rfp_documents
├── id: "abc-123-uuid"                        -- Workspace identifier
├── original_filename: "Navy_MBOS_RFP.pdf"    -- Your uploaded file
├── processing_status: "completed"            -- FROM kv_store_doc_status.json
├── graphml_data: <binary blob>               -- FROM graph_chunk_entity_relation.graphml
├── full_text: "Section A: Solicitation..."   -- FROM kv_store_full_docs.json
├── entity_count: 594                         -- Calculated from entities table
└── relationship_count: 250                   -- Calculated from relationships table
```

**But the actual entities/relationships are in separate tables:**

```sql
-- entities table (594 ROWS for this workspace)
entities
├── Row 1: id="ent-1", rfp_id="abc-123-uuid", entity_name="REQUIREMENT_001", entity_type="REQUIREMENT"
├── Row 2: id="ent-2", rfp_id="abc-123-uuid", entity_name="EVALUATION_FACTOR_M1", entity_type="EVALUATION_FACTOR"
├── Row 3: id="ent-3", rfp_id="abc-123-uuid", entity_name="FAR 52.212-1", entity_type="CLAUSE"
└── ... (591 more rows)

-- relationships table (250 ROWS for this workspace)
relationships
├── Row 1: source="ent-1", target="ent-2", type="EVALUATED_BY", rfp_id="abc-123-uuid"
├── Row 2: source="ent-3", target="ent-4", type="ATTACHMENT_OF", rfp_id="abc-123-uuid"
└── ... (248 more rows)
```

---

## 🚀 Migration Example (Navy MBOS RFP)

**Before** (11 JSON/GraphML files):

```
rag_storage/
├── graph_chunk_entity_relation.graphml (500 KB)
├── kv_store_full_entities.json (300 KB)
├── kv_store_full_relations.json (100 KB)
└── ... (8 more files, ~1.1 MB)

Total: 11 files, ~2 MB on disk
```

**After** (PostgreSQL database):

```sql
-- 1 workspace row
INSERT INTO rfp_documents VALUES (
    'navy-mbos-uuid',
    'Navy_MBOS_RFP_2024.pdf',
    'completed',
    <graphml_binary_blob>  -- ← graph_chunk_entity_relation.graphml stored here
);

-- 594 entity rows (from kv_store_full_entities.json)
INSERT INTO entities (rfp_id, entity_name, entity_type, description, embedding) VALUES
    ('navy-mbos-uuid', 'REQUIREMENT_001', 'REQUIREMENT', 'Contractor shall...', <vector>),
    ('navy-mbos-uuid', 'REQUIREMENT_002', 'REQUIREMENT', 'Offeror must...', <vector>),
    ... (592 more rows)

-- 250 relationship rows (from kv_store_full_relations.json)
INSERT INTO relationships (rfp_id, source_entity_id, target_entity_id, relationship_type) VALUES
    ('navy-mbos-uuid', 'ent-1', 'ent-2', 'EVALUATED_BY'),
    ('navy-mbos-uuid', 'ent-3', 'ent-4', 'ATTACHMENT_OF'),
    ... (248 more rows)

-- 15 chunk rows (from kv_store_text_chunks.json + vdb_chunks.json)
INSERT INTO document_chunks (rfp_id, chunk_id, chunk_text, embedding) VALUES
    ('navy-mbos-uuid', 'chunk_0', 'Section A: Solicitation Form...', <vector>),
    ('navy-mbos-uuid', 'chunk_1', 'Section B: Supplies or Services...', <vector>),
    ... (13 more rows)

Total: 1 + 594 + 250 + 15 = 860 rows across 4 tables
```

---

## ❓ FAQ

### Q1: Why store GraphML as a blob if we're converting to relational tables?

**A**: Backup and export. If you need to download the original graph for Gephi or Neo4j, you can extract the GraphML blob. But day-to-day queries use the relational tables.

### Q2: Do we keep the JSON files after migration?

**A**: No! Once migrated to PostgreSQL, you can delete the JSON files. PostgreSQL becomes the single source of truth.

### Q3: What about the embeddings (vdb\_\*.json files)?

**A**: They become pgvector columns (`entities.embedding`, `document_chunks.embedding`). No separate vector database needed - PostgreSQL handles it with the pgvector extension.

### Q4: How do I query this data?

**A**: Simple SQL queries:

```sql
-- Get all requirements for Navy MBOS
SELECT requirement_id, description, criticality_level
FROM requirements
WHERE rfp_id = 'navy-mbos-uuid';

-- Find similar requirements using embeddings
SELECT entity_name, description,
       1 - (embedding <=> (SELECT embedding FROM entities WHERE id = 'target-id')) AS similarity
FROM entities
WHERE entity_type = 'REQUIREMENT'
ORDER BY similarity DESC
LIMIT 10;
```

---

## 🎯 Summary

**Your Question**: Does only GraphML go into the workspace row?

**Answer**: The workspace row (`rfp_documents` table) stores:

1. ✅ GraphML file as binary blob (backup)
2. ✅ Full document text (from kv_store_full_docs.json)
3. ✅ Processing status (from kv_store_doc_status.json)
4. ✅ Metadata (filename, page count, cost, etc.)

**But the actual data (entities, relationships, chunks) goes into separate tables:**

- `entities` table ← kv_store_full_entities.json + vdb_entities.json
- `relationships` table ← kv_store_full_relations.json + vdb_relationships.json
- `document_chunks` table ← kv_store_text_chunks.json + vdb_chunks.json
- `llm_cache` table ← kv_store_llm_response_cache.json
- `parse_cache` table ← kv_store_parse_cache.json

**Why?** Because relational tables let you query "show me all MANDATORY requirements" (fast) instead of parsing a 500KB GraphML file (slow).

---

**Last Updated**: October 19, 2025  
**Reference**: See `POSTGRESQL_SCHEMA_DESIGN.md` for full table definitions
