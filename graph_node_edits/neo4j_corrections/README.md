# Neo4j Graph Correction Scripts

**Neo4j-native correction workflow** for manual knowledge graph edits using Cypher queries in Neo4j Browser.

## Overview

This directory contains **reusable Cypher script templates** for common graph corrections and **workspace-specific correction files** documenting all manual edits made to processed RFPs.

### Why Neo4j Corrections?

The old approach (Python scripts parsing GraphML files) is obsolete. Neo4j provides:

- ✅ **Real-time editing**: Changes immediately visible
- ✅ **Transactional**: Atomic commits with rollback support
- ✅ **Validated**: Database enforces constraints
- ✅ **Reversible**: Document and replay corrections
- ✅ **Auditable**: Metadata tracks who/when/why
- ✅ **Concurrent**: Multiple analysts can work simultaneously
- ✅ **Visual**: See impact in graph visualization

## Quick Start

### 1. Open Neo4j Browser

Navigate to: **http://localhost:7474**

- Username: `neo4j`
- Password: `govcon-capture-2025`

### 2. Choose a Template

Browse `templates/` directory for common correction patterns:

| Template                                  | Purpose                                   |
| ----------------------------------------- | ----------------------------------------- |
| `01_find_orphaned_nodes.cypher`           | Find entities with no relationships       |
| `02_fix_missing_section_l_m_links.cypher` | Create Section L ↔ M GUIDES relationships |
| `03_merge_duplicate_entities.cypher`      | Consolidate formatting variations         |
| `04_add_missing_metadata.cypher`          | Enrich with requirement_type, etc.        |
| `05_fix_entity_types.cypher`              | Correct misclassifications                |
| `06_delete_bad_relationships.cypher`      | Remove incorrect relationships            |

### 3. Customize for Your Workspace

Replace placeholders:

- `{WORKSPACE}` → Your workspace label (e.g., `mcpp_drfp_2025`)
- `ENTITY_NAME` → Specific entity name (e.g., `'Section L.6: Technical Proposal Format'`)
- `USERNAME` → Your username (e.g., `'analyst'`)

### 4. Execute in Neo4j Browser

Copy query → Paste into Neo4j Browser → Click **Run** (Ctrl+Enter)

### 5. Save Corrections

Document your corrections in a workspace-specific file:

```cypher
// Example: neo4j_corrections/mcpp_drfp_2025_corrections.cypher

// CORRECTION 1: Fix Missing Section L ↔ M Link
// Issue: Section L.6 not linked to Factor 1
// Date: 2025-01-XX
// Resolution: Created GUIDES relationship

MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})
MATCH (m:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
CREATE (l)-[r:GUIDES {
  confidence: 0.98,
  reasoning: 'Section L.6 guides Factor 1 evaluation',
  source: 'manual_correction',
  corrected_by: 'analyst',
  corrected_at: datetime()
}]->(m);
```

**Why save corrections?** If you reprocess an RFP, you can re-run your correction file to restore manual edits.

## Template Structure

Each template follows a standard pattern:

1. **STEP 1: FIND** - Diagnostic queries to identify issues
2. **STEP 2: FIX** - Single entity/relationship correction
3. **STEP 3: VERIFY** - Confirm changes applied correctly
4. **EXAMPLE** - Real-world usage with actual entity names
5. **BULK** - Batch operations for multiple corrections
6. **NOTES** - Best practices and warnings

## Workflow

### Recommended Process

1. **Diagnose** → Run diagnostic queries from templates to find issues
2. **Prioritize** → Focus on high-value corrections first (Section L↔M links, requirements)
3. **Test** → Execute corrections on small subset
4. **Verify** → Run verification queries to confirm success
5. **Document** → Save corrections to workspace file with dates/reasoning
6. **Repeat** → Address next priority issue

### Common Correction Priorities

**High Priority** (critical for compliance matrix generation):

- Section L ↔ M GUIDES relationships (`02_fix_missing_section_l_m_links.cypher`)
- Requirement → Evaluation Factor EVALUATED_BY relationships
- Entity type misclassifications (`05_fix_entity_types.cypher`)

**Medium Priority** (improves query accuracy):

- Missing metadata on requirements (`04_add_missing_metadata.cypher`)
- Orphaned nodes (`01_find_orphaned_nodes.cypher`)

**Low Priority** (cleanup):

- Duplicate entities (`03_merge_duplicate_entities.cypher`)
- Low-confidence relationships (`06_delete_bad_relationships.cypher`)

## Examples

### Example 1: Find Orphaned Section L Items

```cypher
// Find submission instructions with no evaluation factor links
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'submission_instruction'
  AND NOT (n)-[:GUIDES]->()
RETURN n.entity_name AS instruction, n.description
ORDER BY n.entity_name;
```

### Example 2: Create Missing Section L ↔ M Link

```cypher
// Link Section L.6 (Technical Proposal) → Factor 1 (Technical Approach)
MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})
MATCH (m:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
CREATE (l)-[r:GUIDES {
  confidence: 0.98,
  reasoning: 'Section L.6 specifies format for Technical Approach evaluation',
  source: 'manual_correction',
  corrected_by: 'analyst',
  corrected_at: datetime()
}]->(m);
```

### Example 3: Verify Correction

```cypher
// Confirm relationship exists
MATCH (l:`mcpp_drfp_2025` {entity_name: 'Section L.6: Technical Proposal Format'})-[r:GUIDES]->(m:`mcpp_drfp_2025` {entity_name: 'Factor 1: Technical Approach'})
RETURN l.entity_name, r.confidence, m.entity_name;
```

## Best Practices

### Always Include Metadata

Document corrections with metadata for audit trail:

```cypher
CREATE (l)-[r:GUIDES {
  confidence: 0.95,
  reasoning: 'Clear 1:1 mapping between instruction and factor',
  source: 'manual_correction',
  corrected_by: 'analyst',
  corrected_at: datetime()
}]->(m)
```

### Test Before Bulk Operations

```cypher
// WRONG: Bulk delete without testing
MATCH (n:`workspace`)-[r]->(m) WHERE r.confidence < 0.5 DELETE r;

// RIGHT: Test on small subset first
MATCH (n:`workspace`)-[r]->(m) WHERE r.confidence < 0.5 RETURN count(r);  // Review count
MATCH (n:`workspace`)-[r]->(m) WHERE r.confidence < 0.5 RETURN n.entity_name, r, m.entity_name LIMIT 10;  // Review samples
// Then execute bulk delete after validation
```

### Use Descriptive Reasoning

```cypher
// WRONG: Vague reasoning
reasoning: 'These are related'

// RIGHT: Specific reasoning
reasoning: 'Section L.6 specifies the required format and content structure for the Technical Proposal, which is evaluated under Factor 1 (Technical Approach). The submission instructions directly guide how responses are structured for this evaluation criterion.'
```

### Verify After Every Change

Always run verification queries after corrections:

```cypher
// After creating relationship
MATCH (l)-[r:GUIDES]->(m) WHERE id(r) = ... RETURN l, r, m;

// After deleting relationship
MATCH (l)-[r:GUIDES]->(m) WHERE ... RETURN count(r);  // Should be 0
```

## Troubleshooting

### Issue: "Label `workspace` does not exist"

**Cause**: Wrong workspace name or no data processed yet.

**Fix**: List all labels to find correct workspace name:

```cypher
CALL db.labels() YIELD label RETURN label;
```

### Issue: "Cannot find entity"

**Cause**: Entity name doesn't match exactly (case-sensitive, whitespace-sensitive).

**Fix**: Search for entity with partial name:

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE toLower(n.entity_name) CONTAINS 'technical approach'
RETURN n.entity_name;
```

### Issue: "Relationship already exists"

**Cause**: Using `CREATE` creates duplicates. Use `MERGE` for idempotent operations.

**Fix**:

```cypher
// WRONG: CREATE (duplicates if run twice)
CREATE (l)-[r:GUIDES]->(m);

// RIGHT: MERGE (idempotent)
MERGE (l)-[r:GUIDES]->(m)
  ON CREATE SET r.confidence = 0.95, r.created_at = datetime()
  ON MATCH SET r.updated_at = datetime();
```

## File Organization

```
neo4j_corrections/
├── templates/                                # Reusable Cypher patterns
│   ├── 01_find_orphaned_nodes.cypher
│   ├── 02_fix_missing_section_l_m_links.cypher
│   ├── 03_merge_duplicate_entities.cypher
│   ├── 04_add_missing_metadata.cypher
│   ├── 05_fix_entity_types.cypher
│   └── 06_delete_bad_relationships.cypher
├── mcpp_drfp_2025_corrections.cypher        # MCPP-specific corrections
├── navy_mbos_2025_corrections.cypher        # Navy MBOS-specific corrections
└── README.md                                 # This file
```

## Advanced Techniques

### Using APOC for Complex Corrections

Neo4j APOC plugin provides advanced graph refactoring:

```cypher
// Merge nodes with APOC
MATCH (n1:`mcpp_drfp_2025` {entity_name: 'section c.6'})
MATCH (n2:`mcpp_drfp_2025` {entity_name: 'Section C.6'})
CALL apoc.refactor.mergeNodes([n1, n2], {properties: 'combine'})
YIELD node
RETURN node;
```

### Conditional Corrections

```cypher
// Only create relationship if confidence threshold met
MATCH (l:`mcpp_drfp_2025`)
MATCH (m:`mcpp_drfp_2025`)
WHERE l.entity_type = 'submission_instruction'
  AND m.entity_type = 'evaluation_factor'
  AND apoc.text.jaroWinklerDistance(l.entity_name, m.entity_name) > 0.8
CREATE (l)-[r:GUIDES {
  confidence: apoc.text.jaroWinklerDistance(l.entity_name, m.entity_name),
  reasoning: 'High name similarity',
  source: 'automated_inference'
}]->(m);
```

## Resources

- **Neo4j Browser Guide**: http://localhost:7474/browser/
- **Cypher Syntax**: https://neo4j.com/docs/cypher-manual/current/
- **APOC Documentation**: https://neo4j.com/docs/apoc/current/
- **Project Neo4j Guide**: `docs/neo4j/NEO4J_USER_GUIDE.md`

## Contributing

When adding new templates:

1. Follow numbered naming: `07_template_name.cypher`
2. Include FIND → FIX → VERIFY → EXAMPLE → BULK → NOTES structure
3. Use placeholder pattern: `{WORKSPACE}`, `ENTITY_NAME`, `USERNAME`
4. Document in this README's template table
5. Add real-world examples from actual RFPs

---

**Last Updated**: November 2025  
**Maintained By**: Project Theseus Team
