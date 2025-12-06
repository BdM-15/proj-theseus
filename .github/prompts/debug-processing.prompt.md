# Debug RFP Processing

Troubleshoot issues with RFP document processing.

## Common Issues

### 1. Document Upload Fails

**Symptoms**: 500 error on `/insert` or `/documents/upload`

**Check**:

```powershell
# Is server running?
curl http://localhost:9621/health

# Check logs
Get-Content logs/server.log -Tail 50
```

**Common Causes**:

- MinerU parsing failed (PDF corruption)
- Out of memory (large PDF)
- API key expired

### 2. No Entities Extracted

**Symptoms**: Upload succeeds but no entities in Neo4j

**Check**:

```cypher
MATCH (n:`workspace_name`)
RETURN count(n)
```

**Common Causes**:

- LLM API error (check xAI status)
- Prompt parsing failed
- Entity types not in config

### 3. Missing Relationships

**Symptoms**: Entities exist but few relationships

**Check**:

```cypher
MATCH (:`workspace_name`)-[r]->(:`workspace_name`)
RETURN type(r), count(r)
```

**Common Causes**:

- Semantic post-processing not triggered
- Batch timeout too short
- LLM inference errors

### 4. Wrong Entity Types

**Symptoms**: Entities have type "UNKNOWN" or incorrect types

**Check**:

```cypher
MATCH (n:`workspace_name`)
WHERE n.entity_type = 'unknown' OR n.entity_type IS NULL
RETURN n.entity_name, n.entity_type
LIMIT 25
```

**Fix**: Entity type correction runs in semantic post-processing.

## Diagnostic Commands

```powershell
# Check environment
python -c "import os; print(os.getenv('LLM_MODEL'))"

# Test LLM connection
python -c "
from src.server.initialization import get_llm_func
llm = get_llm_func()
print(asyncio.run(llm('test')))
"

# Check Neo4j connection
python tools/neo4j/check_connection.py

# List workspaces
python tools/neo4j/clear_neo4j.py --list
```

## Log Locations

- Server logs: `logs/server.log`
- MinerU logs: Check terminal output
- Neo4j logs: `docker logs neo4j-govcon`
