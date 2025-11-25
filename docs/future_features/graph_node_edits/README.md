# Neo4j Graph Correction Scripts

**With Neo4j storage, manual graph editing is now done directly in Neo4j Browser using Cypher queries.**

This folder contains reusable Cypher script templates and workspace-specific corrections that can be run in Neo4j Browser.

## 🎯 Why Neo4j Makes This Folder Different

**Old Way (NetworkX file storage)**:

- Required Python scripts to parse/edit GraphML files
- Complex, error-prone, no validation
- No real-time updates

**New Way (Neo4j storage)**:

- Direct database editing via Cypher queries
- Real-time, transactional, validated
- Built-in undo/rollback support

## Folder Structure

```
graph_node_edits/
├── README.md                           # This file - Overview
├── neo4j_corrections/                  # Neo4j Cypher correction scripts
│   ├── mcpp_drfp_2025_corrections.cypher    # MCPP RFP corrections
│   ├── navy_mbos_2025_corrections.cypher    # Navy MBOS corrections
│   └── templates/                      # Reusable script templates
│       ├── 01_find_orphaned_nodes.cypher
│       ├── 02_fix_missing_section_l_m_links.cypher
│       ├── 03_merge_duplicate_entities.cypher
│       ├── 04_add_missing_metadata.cypher
│       ├── 05_fix_entity_types.cypher
│       └── 06_delete_bad_relationships.cypher
├── archive/                            # Old NetworkX-based tools (deprecated)
│   ├── auto_bulk/                      # Python bulk editing (obsolete)
│   ├── manual/                         # Python manual editing (obsolete)
│   └── DEPRECATED_README.md            # Old documentation
└── MANUAL_EDITING_TOOLS.md             # Historical reference
```

## Quick Start: Neo4j Graph Editing

### 1️⃣ Open Neo4j Browser

- URL: http://localhost:7474
- Username: `neo4j`
- Password: `govcon-capture-2025`

### 2️⃣ Choose a Template Script

Browse `neo4j_corrections/templates/` for common fixes:

- **01_find_orphaned_nodes.cypher** - Find entities with no relationships
- **02_fix_missing_section_l_m_links.cypher** - Link submission instructions to evaluation factors
- **03_merge_duplicate_entities.cypher** - Merge formatting variations
- **04_add_missing_metadata.cypher** - Add metadata properties
- **05_fix_entity_types.cypher** - Correct misclassified entities
- **06_delete_bad_relationships.cypher** - Remove incorrect relationships

### 3️⃣ Customize and Run

1. Open a template file in your text editor
2. Replace `{WORKSPACE}` with your workspace name (e.g., `mcpp_drfp_2025`)
3. Replace placeholder entity names with actual names from your graph
4. Copy the Cypher query
5. Paste into Neo4j Browser
6. Click ▶️ Run

### 4️⃣ Save Your Corrections

Create a workspace-specific correction file:

```cypher
// Save to: neo4j_corrections/mcpp_drfp_2025_corrections.cypher

// Correction 1: Link orphaned technical volume instruction
MATCH (inst:`mcpp_drfp_2025` {entity_name: 'Technical Volume Page Limit'})
MATCH (factor:`mcpp_drfp_2025` {entity_name: 'Technical Methodology'})
CREATE (inst)-[r:GUIDES {
  confidence: 1.0,
  reasoning: 'Manual correction: Page limit guides methodology evaluation',
  source: 'manual_correction',
  corrected_by: 'ben',
  corrected_at: datetime()
}]->(factor);

// Correction 2: Fix entity type
MATCH (n:`mcpp_drfp_2025` {entity_name: 'PM Schedule'})
SET n.entity_type = 'requirement',
    n.requirement_type = 'performance';
```

This way, if you reprocess the RFP, you can re-run your corrections!

---

## Common Neo4j Editing Patterns

### Pattern 1: Find Issues

```cypher
// Find orphaned submission instructions
MATCH (inst:`mcpp_drfp_2025`)
WHERE inst.entity_type = 'submission_instruction'
  AND NOT (inst)-[:GUIDES]->()
RETURN inst.entity_name, inst.description
LIMIT 10
```

### Pattern 2: Fix Issues

```cypher
// Create missing Section L→M link
MATCH (inst:`mcpp_drfp_2025` {entity_name: 'Technical Volume Page Limit'})
MATCH (factor:`mcpp_drfp_2025` {entity_name: 'Technical Methodology'})
CREATE (inst)-[r:GUIDES {
  confidence: 1.0,
  reasoning: 'Manual correction: Clear relationship in RFP',
  source: 'manual_correction'
}]->(factor)
```

### Pattern 3: Verify Fix

```cypher
// Check that the relationship was created
MATCH (inst:`mcpp_drfp_2025` {entity_name: 'Technical Volume Page Limit'})
      -[r:GUIDES]->(factor:`mcpp_drfp_2025`)
RETURN inst, r, factor
```

---

## Advantages of Neo4j Editing

✅ **Real-time**: Changes visible immediately  
✅ **Transactional**: All-or-nothing (ACID compliance)  
✅ **Validated**: Cypher validates queries before running  
✅ **Reversible**: Can rollback transactions  
✅ **Auditable**: Add metadata to track changes  
✅ **Concurrent**: Multiple users can edit safely  
✅ **Visual**: See changes in graph visualization instantly

---

## Deprecated: Old NetworkX Tools (Branch 005)

**Best for**: Fixing LLM reasoning artifact corruption (~2% of entities)

**Context**: Grok-4-fast-reasoning occasionally outputs entity names with chain-of-thought prefixes:

- `#>|LOCATION` instead of valid `LOCATION` type
- `#|PROGRAM` instead of valid `PROGRAM` type
- `#>|evaluation_factor` (lowercase) instead of `EVALUATION_FACTOR`

**Baseline Corruption Rate**: 2.2% (13/594 entities in Navy MBOS)

**Detection**: Check server logs during processing for warnings like:

```
WARNING: Invalid entity type '#>|LOCATION' for entity 'San Diego Naval Base' (expected one of 17 valid types)
WARNING: Invalid entity type '#|PROGRAM' for entity 'MCPP II' (expected one of 17 valid types)
```

**Manual Cleanup Workflow**:

```powershell
# Step 1: Identify corrupted entities in logs
# Look for "WARNING: Invalid entity type" during processing

# Step 2: Find affected entities in GraphML
python -c "
from llm_relationship_inference import parse_graphml
entities, _ = parse_graphml('./rag_storage/graph_chunk_entity_relation.graphml')
corrupted = [e for e in entities if e['entity_type'].startswith('#')]
print(f'Found {len(corrupted)} corrupted entities:')
for e in corrupted: print(f'  - {e[\"entity_name\"]}: {e[\"entity_type\"]}')"

# Step 3: Fix using bulk corruption tool (RECOMMENDED)
# ⚠️  CRITICAL: Web UI CANNOT edit entity_type field - only description/keywords
# ⚠️  CRITICAL: Web UI limited to 1000 nodes - unusable for 4000+ node graphs

# ONLY option: Automated bulk corruption cleanup
python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --dry-run

# ⚠️  WARNING: DO NOT apply without dedicated branch and backup!
# python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --apply
```

**Common Corruption Patterns**:

| Corrupted Type          | Expected Type        | Frequency (Navy MBOS) | Fix Priority |
| ----------------------- | -------------------- | --------------------- | ------------ |
| `#>\|LOCATION`          | `LOCATION`           | 3 instances           | Medium       |
| `#>\|DELIVERABLE`       | `DELIVERABLE`        | 2 instances           | Medium       |
| `#>\|DOCUMENT`          | `DOCUMENT`           | 2 instances           | Low          |
| `#>\|CONCEPT`           | `CONCEPT`            | 2 instances           | Low          |
| `#>\|REQUIREMENT`       | `REQUIREMENT`        | 1 instance            | High         |
| `#\|PROGRAM`            | `PROGRAM`            | 1 instance            | High         |
| `#\|EQUIPMENT`          | `EQUIPMENT`          | 1 instance            | Medium       |
| `#\|DOCUMENT`           | `DOCUMENT`           | 1 instance            | Low          |
| `#>\|Other`             | _(invalid - delete)_ | 1 instance            | High         |
| `#>\|evaluation_factor` | `EVALUATION_FACTOR`  | 1 instance            | **CRITICAL** |

**Priority Guidance**:

- **CRITICAL**: `EVALUATION_FACTOR` corruption affects Section M analysis (proposal scoring)
- **HIGH**: `REQUIREMENT` and `PROGRAM` are core RFP entities
- **MEDIUM**: Other corruptions impact queries but aren't blocking
- **LOW**: `DOCUMENT`/`CONCEPT` are generic types with less impact

**Automated Cleanup Tool** (Branch 005 - EXPERIMENTAL):

- `python graph_node_edits/auto_bulk/bulk_graph_fixes.py --pattern corruption --dry-run`
- Detects #>|TYPE, #|TYPE, lowercase types, invalid types
- Auto-fixes high-confidence patterns (≥0.80 confidence)
- Flags low-confidence items for manual review
- **⚠️ NOT TESTED YET** - requires dedicated branch for implementation
- **⚠️ NOT included in 'all' pattern** (must explicitly specify)
- See `auto_bulk/README.md` for full documentation

**Future Automation** (Task 2 from Branch 005):

- Pre-validation sanitizer: Strip `#>|` and `#|` prefixes BEFORE entity type validation
- Expected result: 100% recovery of rejected entities, 0% corruption warnings
- Implementation: `src/utils/entity_sanitizer.py`

**PostgreSQL Tracking** (Phase 8):

- Corruption patterns will be logged to `entity_corruption_tracking` table
- Enables trend analysis across RFPs and LLM model versions
- See `docs/POSTGRESQL_IMPLEMENTATION_PLAN.md` for schema details

**See**: Server logs during processing for real-time corruption detection

---

## Recommended Workflow

### Step 1: Identify Issues

Use diagnostic queries to find data quality problems:

```cypher
// Find orphaned nodes
MATCH (n:`mcpp_drfp_2025`)
WHERE NOT (n)-[]-()
RETURN n.entity_type, count(n) AS orphaned_count
ORDER BY orphaned_count DESC
```

### Step 2: Review Template Scripts

Browse `neo4j_corrections/templates/` for applicable fixes.

### Step 3: Customize and Test

1. Copy template to your workspace file (e.g., `mcpp_drfp_2025_corrections.cypher`)
2. Replace placeholders with actual entity names
3. Run in Neo4j Browser
4. Verify with visualization query

### Step 4: Document Your Changes

Add comments to your correction file:

```cypher
// Date: 2025-11-03
// Issue: Missing Section L→M link for technical volume
// Resolution: Created GUIDES relationship with manual correction metadata
MATCH (inst:`mcpp_drfp_2025` {entity_name: '...'})
...
```

### Step 5: Save for Future Use

If you reprocess the RFP, you can re-run your corrections by pasting the entire file into Neo4j Browser.

---

## Template Scripts

| Template                                  | Purpose                    | Common Use Cases                                   |
| ----------------------------------------- | -------------------------- | -------------------------------------------------- |
| `01_find_orphaned_nodes.cypher`           | Diagnostic query           | Find entities with no relationships                |
| `02_fix_missing_section_l_m_links.cypher` | Fix missing relationships  | Link submission instructions to evaluation factors |
| `03_merge_duplicate_entities.cypher`      | Consolidate duplicates     | "Section C.6" vs "section c.6"                     |
| `04_add_missing_metadata.cypher`          | Enrich entities            | Add requirement_type, criticality_level            |
| `05_fix_entity_types.cypher`              | Correct misclassifications | Change 'concept' to 'requirement'                  |
| `06_delete_bad_relationships.cypher`      | Remove incorrect links     | Delete wrong GUIDES relationships                  |

**📖 See [`neo4j_corrections/README.md`](neo4j_corrections/README.md) for detailed usage instructions, examples, and best practices.**

---

## Archive: Old NetworkX Tools (Deprecated)

The `archive/` folder contains **obsolete Python-based tools** from when we used NetworkX file storage:

- ❌ `archive/auto_bulk/` - Python bulk editing scripts (superseded by Neo4j Cypher)
- ❌ `archive/manual/` - Python manual editing tools (superseded by Neo4j Browser)

**These are kept for historical reference only.** With Neo4j storage, all editing is done directly in Neo4j Browser using Cypher queries.

---

## Troubleshooting

### "Label does not exist"

This warning is normal if you haven't processed data yet. Process an RFP first.

### "Entity not found"

Entity names are case-sensitive. Use exact names:

```cypher
// Find correct name first
MATCH (n:`mcpp_drfp_2025`)
WHERE toLower(n.entity_name) CONTAINS 'technical volume'
RETURN n.entity_name
```

### "Relationship already exists"

Use `MERGE` instead of `CREATE` to avoid duplicates:

```cypher
MERGE (inst)-[r:GUIDES]->(factor)
ON CREATE SET r.confidence = 1.0
```

### "Need to undo changes"

Neo4j transactions are atomic. If you made a mistake, you can:

1. Run a DELETE query to remove bad data
2. Restore from Neo4j backup
3. Reprocess the RFP (deletes old data)

---

## Documentation

- **Neo4j User Guide**: `docs/neo4j/NEO4J_USER_GUIDE.md` - Complete Cypher reference
- **Template Scripts**: `neo4j_corrections/templates/` - Reusable patterns
- **Historical Reference**: `MANUAL_EDITING_TOOLS.md` - Old NetworkX approach

---

## Status

✅ **Transitioned to Neo4j** (November 2025)

Old NetworkX tools archived. All graph editing now done via Neo4j Browser with Cypher queries.

**Last Updated**: November 3, 2025 (Branch 013 - Neo4j Implementation)
