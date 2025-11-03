# Neo4j User Guide for Project Theseus

**GovCon Capture Vibe - Government Contracting Intelligence Platform**

---

## Quick Start: Accessing Neo4j Browser

1. **Start the Application** (if not already running):

   ```powershell
   .venv\Scripts\Activate.ps1
   python app.py
   ```

   The application automatically starts Neo4j Docker container and waits for it to be ready.

2. **Open Neo4j Browser**:

   - URL: http://localhost:7474
   - Username: `neo4j`
   - Password: `govcon-capture-2025`

3. **Select Database**: `neo4j` (default)

---

## Understanding Workspaces

**Each RFP gets its own isolated workspace** using Neo4j labels:

- **MCPP II DRAFT RFP**: `mcpp_drfp_2025`
- **Navy MBOS**: `navy_mbos_2025`
- **Future RFPs**: Automatically named from filename

All nodes in a workspace share the same label (e.g., `mcpp_drfp_2025`), providing complete isolation between different RFPs.

---

## Essential Cypher Queries

### 1. Count Nodes in Your Workspace

```cypher
// Replace 'mcpp_drfp_2025' with your workspace name
MATCH (n:`mcpp_drfp_2025`)
RETURN count(n) AS total_entities
```

### 2. Entity Breakdown by Type

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type IS NOT NULL
RETURN n.entity_type AS type, count(n) AS count
ORDER BY count DESC
```

**Expected types**:

- `requirement`, `section`, `document`, `organization`, `concept`, `clause`, `deliverable`, `evaluation_factor`, `submission_instruction`, `program`, `technology`, `event`, `person`, `location`, `equipment`, `strategic_theme`, `statement_of_work`

### 3. Sample Entities

```cypher
// View 25 random entities
MATCH (n:`mcpp_drfp_2025`)
RETURN n
LIMIT 25
```

### 4. Find Specific Entity by Name

```cypher
// Search for entity by name (case-insensitive)
MATCH (n:`mcpp_drfp_2025`)
WHERE toLower(n.entity_name) CONTAINS 'section c'
RETURN n.entity_name, n.entity_type, n.description
LIMIT 10
```

### 5. Count Relationships

```cypher
MATCH (:`mcpp_drfp_2025`)-[r]->(:`mcpp_drfp_2025`)
RETURN count(r) AS total_relationships
```

### 6. Relationship Types

```cypher
MATCH (:`mcpp_drfp_2025`)-[r]->(:`mcpp_drfp_2025`)
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC
```

**Expected types**:

- `CHILD_OF`, `EVALUATED_BY`, `GUIDES`, `REQUIRES`, `RELATED_TO`

### 7. Find All Requirements

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'requirement'
RETURN n.entity_name, n.description
LIMIT 25
```

### 8. Section L ↔ M Mapping (Submission Instructions → Evaluation Factors)

```cypher
MATCH (inst:`mcpp_drfp_2025`)-[r:GUIDES]->(factor:`mcpp_drfp_2025`)
WHERE inst.entity_type = 'submission_instruction'
  AND factor.entity_type = 'evaluation_factor'
RETURN inst.entity_name AS instruction,
       factor.entity_name AS factor,
       r.confidence AS confidence,
       r.reasoning AS reasoning
LIMIT 25
```

### 9. Requirements → Evaluation Factors Mapping

```cypher
MATCH (req:`mcpp_drfp_2025`)-[r:EVALUATED_BY]->(factor:`mcpp_drfp_2025`)
WHERE req.entity_type = 'requirement'
  AND factor.entity_type = 'evaluation_factor'
RETURN req.entity_name AS requirement,
       factor.entity_name AS evaluation_factor,
       r.confidence AS confidence
ORDER BY r.confidence DESC
LIMIT 25
```

### 10. Document Hierarchy (Attachments → Sections)

```cypher
MATCH (doc:`mcpp_drfp_2025`)-[r:CHILD_OF]->(section:`mcpp_drfp_2025`)
WHERE doc.entity_type = 'document'
  AND section.entity_type = 'section'
RETURN doc.entity_name AS document,
       section.entity_name AS parent_section,
       r.reasoning AS reasoning
LIMIT 25
```

---

## Graph Visualization Queries

### Visualize Section L↔M Network

```cypher
MATCH path = (inst:`mcpp_drfp_2025`)-[:GUIDES]-(factor:`mcpp_drfp_2025`)
WHERE inst.entity_type = 'submission_instruction'
  AND factor.entity_type = 'evaluation_factor'
RETURN path
LIMIT 50
```

### Visualize Requirements Network

```cypher
MATCH (req:`mcpp_drfp_2025`)-[r]->(target:`mcpp_drfp_2025`)
WHERE req.entity_type = 'requirement'
RETURN req, r, target
LIMIT 100
```

### Visualize Document Structure

```cypher
MATCH path = (doc:`mcpp_drfp_2025`)-[:CHILD_OF*1..2]->(section:`mcpp_drfp_2025`)
WHERE doc.entity_type IN ['document', 'section']
  AND section.entity_type = 'section'
RETURN path
LIMIT 50
```

---

## Advanced Queries

### Find Orphaned Entities (No Relationships)

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE NOT (n)-[]-()
RETURN n.entity_type AS type, n.entity_name AS name
LIMIT 25
```

### Find Highly Connected Entities (Hubs)

```cypher
MATCH (n:`mcpp_drfp_2025`)-[r]-()
RETURN n.entity_name AS entity,
       n.entity_type AS type,
       count(r) AS connections
ORDER BY connections DESC
LIMIT 25
```

### Full-Text Search Across Descriptions

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE n.description CONTAINS 'maintenance'
RETURN n.entity_name, n.entity_type, n.description
LIMIT 25
```

### Find All Deliverables with CDRLs

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'deliverable'
  AND (n.entity_name CONTAINS 'CDRL' OR n.entity_name CONTAINS 'DID')
RETURN n.entity_name, n.description
ORDER BY n.entity_name
```

### Requirements by Criticality (if metadata enriched)

```cypher
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'requirement'
  AND n.criticality_level IS NOT NULL
RETURN n.criticality_level AS criticality,
       count(n) AS count
ORDER BY
  CASE n.criticality_level
    WHEN 'mandatory' THEN 1
    WHEN 'highly_desirable' THEN 2
    WHEN 'desirable' THEN 3
    ELSE 4
  END
```

---

## Property Reference

### Common Entity Properties

Every entity node has these properties:

- `entity_name`: Display name (e.g., "Section C.6", "Preventative Maintenance")
- `entity_type`: One of 17 govcon types (e.g., "requirement", "section")
- `description`: Full text description from RFP (can be very long)
- `source_id`: Original chunk ID from document parsing

### Relationship Properties

Every relationship has these properties:

- `relationship_type`: Type name (CHILD_OF, EVALUATED_BY, GUIDES, REQUIRES)
- `confidence`: Float 0.0-1.0 (LLM confidence score)
- `reasoning`: Human-readable explanation of why this relationship exists

### Metadata Properties (Phase 7 Enrichment)

**Requirements** may have:

- `requirement_type`: "functional", "performance", "interface", "constraint"
- `criticality_level`: "mandatory", "highly_desirable", "desirable"
- `compliance_method`: "inspection", "test", "analysis", "demonstration"

**Evaluation Factors** may have:

- `scoring_method`: "adjectival", "numeric", "pass_fail"
- `weight_percentage`: Float (e.g., 35.0 for 35%)

**Submission Instructions** may have:

- `page_limit`: Integer
- `format_requirement`: String (e.g., "single-spaced, 12pt Arial")

---

## Performance Tips

### 1. Always Filter by Workspace Label

❌ **Slow** (scans entire database):

```cypher
MATCH (n) WHERE n.entity_type = 'requirement' RETURN n
```

✅ **Fast** (uses label index):

```cypher
MATCH (n:`mcpp_drfp_2025`) WHERE n.entity_type = 'requirement' RETURN n
```

### 2. Use LIMIT for Exploration

Always use `LIMIT` when exploring large result sets:

```cypher
MATCH (n:`mcpp_drfp_2025`) RETURN n LIMIT 25
```

### 3. Create Indexes (Optional)

For frequently queried properties:

```cypher
CREATE INDEX entity_type_index FOR (n:`mcpp_drfp_2025`) ON (n.entity_type);
CREATE INDEX entity_name_index FOR (n:`mcpp_drfp_2025`) ON (n.entity_name);
```

---

## Troubleshooting

### "Label does not exist" Warning

This is **normal** if no data has been processed yet. The warning just means Neo4j hasn't seen that label before.

### No Nodes Found

**Check**:

1. Has the RFP been processed? Look in logs for "Processing complete"
2. Is `GRAPH_STORAGE=Neo4JStorage` in .env?
3. Was the server restarted after changing .env?

### Connection Refused

**Check**:

1. Is Docker Desktop running?
2. Is Neo4j container running? `docker ps | grep neo4j`
3. Start container: `docker-compose -f docker-compose.neo4j.yml up -d`

### Password Incorrect

The password is set in `.env`:

```bash
NEO4J_PASSWORD=govcon-capture-2025
```

---

## Switching Between RFPs

To query different RFPs, just change the workspace label in queries:

```cypher
// Query MCPP RFP
MATCH (n:`mcpp_drfp_2025`) RETURN count(n)

// Query Navy MBOS
MATCH (n:`navy_mbos_2025`) RETURN count(n)
```

Future enhancement: WebUI workspace selector dropdown.

---

## Exporting Data

### Export to JSON

```cypher
// Export all entities to JSON
MATCH (n:`mcpp_drfp_2025`)
RETURN n.entity_name, n.entity_type, n.description
```

Click the download icon in Neo4j Browser → Select JSON format.

### Export to CSV

```cypher
// Export requirements to CSV
MATCH (n:`mcpp_drfp_2025`)
WHERE n.entity_type = 'requirement'
RETURN n.entity_name AS name, n.description AS description
```

Click the download icon → Select CSV format.

---

## Resources

- **Neo4j Browser**: http://localhost:7474
- **APOC Documentation**: https://neo4j.com/docs/apoc/current/
- **Cypher Cheat Sheet**: https://neo4j.com/docs/cypher-cheat-sheet/
- **Project Documentation**: `docs/neo4j/`

---

**Last Updated**: November 2025 (Branch 013 - Neo4j Implementation)
