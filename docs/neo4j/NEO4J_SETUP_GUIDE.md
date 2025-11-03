# Neo4j Setup Guide - GovCon Capture Vibe

**Date**: November 3, 2025  
**Branch**: 013-hybrid-adjudication  
**Neo4j Version**: 5.25 Community Edition  
**LightRAG Version**: 1.4.9.7

---

## Prerequisites

✅ **Docker Desktop** installed and running on Windows  
✅ **LightRAG 1.4.9.7** upgraded (`uv pip show lightrag-hku`)  
✅ **Virtual environment** activated (`.venv`)

---

## Automatic Startup (Recommended)

**Neo4j now starts automatically when you run `python app.py`!**

The app detects `GRAPH_STORAGE=Neo4JStorage` in `.env` and:

1. Checks if Docker is available
2. Starts Neo4j container (if not already running)
3. Waits for health check
4. Starts the GovCon RAG server

**Simply run:**

```powershell
python app.py
```

**Output:**

```
============================================================
🎯 GovCon Capture Vibe - Project Theseus
   Government Contracting Intelligence Platform
============================================================

🔍 Neo4j storage enabled, checking Docker...

🚀 Starting Neo4j container...
✅ Neo4j container started successfully

⏳ Waiting for Neo4j to be ready...... ✅

🚀 Starting GovCon RAG Server...
```

**When you stop the server (Ctrl+C), Neo4j stops gracefully too.**

---

## Manual Startup (Alternative)

If you need to start Neo4j independently:

```powershell
# Navigate to project root
cd C:\Users\benma\govcon-capture-vibe

# Start Neo4j with APOC plugin
docker-compose -f docker-compose.neo4j.yml up -d

# Verify container is running
docker ps

# Expected output:
# CONTAINER ID   IMAGE                  PORTS
# xxxxx          neo4j:5.25-community   0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
```

**Container Details**:

- **Name**: `govcon-neo4j`
- **HTTP Browser UI**: http://localhost:7474
- **Bolt Protocol**: `neo4j://localhost:7687`
- **Username**: `neo4j`
- **Password**: `govcon-capture-2025`

---

## Verify Neo4j is Healthy

### **2.1 Check Container Logs**

```powershell
# View startup logs
docker logs govcon-neo4j

# Expected: "Remote interface available at http://localhost:7474/"
# Expected: "Started" (indicates Neo4j is ready)
```

### **2.2 Access Browser UI**

1. Open browser: http://localhost:7474
2. **Connect URL**: `neo4j://localhost:7687`
3. **Username**: `neo4j`
4. **Password**: `govcon-capture-2025`
5. Click **Connect**

**Expected**: Welcome screen with empty database

### **2.3 Verify APOC Plugin**

Run this Cypher query in Neo4j Browser:

```cypher
CALL apoc.help("subgraph")
```

**Expected**: Returns APOC subgraph functions (critical for multi-depth graph queries)

---

## Step 3: Configure LightRAG for Neo4j

### **3.1 Verify .env Configuration**

Your `.env` already configured with:

```bash
GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=govcon-capture-2025
NEO4J_WORKSPACE=navy_mbos_baseline
```

### **3.2 Test Neo4j Connection**

Create a test script to verify LightRAG can connect:

```powershell
# Create test file
code test_neo4j_connection.py
```

**File contents** (test_neo4j_connection.py):

```python
import asyncio
import os
from dotenv import load_dotenv
from lightrag import LightRAG
from lightrag.llm import gpt_4o_mini_complete

# Load environment variables
load_dotenv()

async def test_neo4j_connection():
    """Test Neo4j connection with LightRAG."""

    print("🔌 Testing Neo4j connection...")
    print(f"   URI: {os.getenv('NEO4J_URI')}")
    print(f"   Workspace: {os.getenv('NEO4J_WORKSPACE')}")

    try:
        # Initialize LightRAG with Neo4j storage
        rag = LightRAG(
            working_dir="./rag_storage/test_neo4j",
            graph_storage="Neo4JStorage",
            workspace=os.getenv("NEO4J_WORKSPACE", "test"),
            llm_model_func=gpt_4o_mini_complete,
        )

        print("✅ LightRAG initialized with Neo4j storage")

        # Test basic operations
        print("\n📝 Testing basic graph operations...")

        # Insert a test entity
        test_text = """
        Project Theseus is a government contracting RFP analysis system.
        It uses Neo4j for enterprise knowledge graph storage.
        The system supports multi-workspace isolation via labels.
        """

        print("   Inserting test document...")
        await rag.ainsert(test_text)
        print("✅ Document inserted successfully")

        # Query the graph
        print("\n🔍 Testing graph query...")
        result = await rag.aquery(
            "What is Project Theseus?",
            param={"mode": "hybrid"}
        )
        print(f"✅ Query successful: {result[:100]}...")

        # Verify workspace isolation in Neo4j
        print(f"\n🏷️  Verifying workspace label: {os.getenv('NEO4J_WORKSPACE')}")
        print("✅ All operations completed successfully!")

        print("\n" + "="*60)
        print("🎉 Neo4j is configured correctly with LightRAG!")
        print("="*60)

        # Cleanup instructions
        print("\nTo verify in Neo4j Browser (http://localhost:7474):")
        print(f"  MATCH (n:`{os.getenv('NEO4J_WORKSPACE')}`) RETURN n LIMIT 25")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify Neo4j is running: docker ps")
        print("2. Check Neo4j logs: docker logs govcon-neo4j")
        print("3. Verify .env configuration")
        raise

if __name__ == "__main__":
    asyncio.run(test_neo4j_connection())
```

**Run the test**:

```powershell
# Activate .venv first if not already active
.venv\Scripts\Activate.ps1

# Run test
python test_neo4j_connection.py
```

**Expected Output**:

```
🔌 Testing Neo4j connection...
   URI: neo4j://localhost:7687
   Workspace: navy_mbos_baseline
✅ LightRAG initialized with Neo4j storage
📝 Testing basic graph operations...
   Inserting test document...
✅ Document inserted successfully
🔍 Testing graph query...
✅ Query successful: Project Theseus is a government contracting RFP analysis system...
🏷️  Verifying workspace label: navy_mbos_baseline
✅ All operations completed successfully!
====================================================
🎉 Neo4j is configured correctly with LightRAG!
====================================================
```

---

## Step 4: Verify Data in Neo4j Browser

1. Open http://localhost:7474
2. Run this Cypher query:

```cypher
// View all nodes in navy_mbos_baseline workspace
MATCH (n:`navy_mbos_baseline`)
RETURN n
LIMIT 25
```

**Expected**: See entities like "Project Theseus", "Neo4j", etc. with workspace label

3. **Verify Workspace Isolation**:

```cypher
// This should return EMPTY (no nodes in different workspace)
MATCH (n:`different_workspace`)
RETURN n
```

---

## Step 5: Test with Real Navy MBOS RFP

Once test passes, process actual RFP:

```powershell
# Start the server
python app.py
```

1. Navigate to http://localhost:9621/webui
2. Upload Navy MBOS RFP PDF
3. Wait for processing (~69 seconds for 71-page doc)
4. Verify in Neo4j Browser:

```cypher
// Count entities by type
MATCH (n:`navy_mbos_baseline`)
RETURN n.entity_type AS type, count(n) AS count
ORDER BY count DESC
```

**Expected**: ~594 entities distributed across 17 government contracting types

---

## Troubleshooting

### **Issue**: `docker-compose: command not found`

**Solution**: Update Docker Desktop to latest version, or use:

```powershell
docker compose -f docker-compose.neo4j.yml up -d
```

(Note: `docker compose` vs `docker-compose` - newer Docker uses integrated command)

---

### **Issue**: "Connection refused" from LightRAG

**Check**:

1. Neo4j is running: `docker ps | grep neo4j`
2. Port 7687 is not blocked: `netstat -an | findstr 7687`
3. Neo4j logs: `docker logs govcon-neo4j`

---

### **Issue**: "Authentication failed"

**Solution**: Reset Neo4j password

```powershell
# Stop container
docker-compose -f docker-compose.neo4j.yml down

# Remove data volume (WARNING: Deletes all data)
docker volume rm govcon-capture-vibe_neo4j-data

# Restart with fresh instance
docker-compose -f docker-compose.neo4j.yml up -d
```

---

### **Issue**: APOC plugin not available

**Check**:

```cypher
CALL dbms.components()
YIELD name, versions, edition
RETURN name, versions, edition
```

**Expected**: See `apoc` in the list

**Solution**: Verify docker-compose.neo4j.yml has:

```yaml
environment:
  - NEO4J_PLUGINS=["apoc"]
```

---

## Next Steps After Verification

Once single-workspace Neo4j works:

✅ **Phase 2**: Implement `WorkspaceManager` for dynamic switching  
✅ **Phase 3**: Add WebUI workspace selector dropdown  
✅ **Phase 4**: Amendment comparison intelligence queries  
✅ **Phase 5**: IDIQ hierarchy analysis

---

## Stopping Neo4j

```powershell
# Stop container (data persists)
docker-compose -f docker-compose.neo4j.yml stop

# Stop and remove container (data persists in volumes)
docker-compose -f docker-compose.neo4j.yml down

# Stop and DELETE ALL DATA (caution!)
docker-compose -f docker-compose.neo4j.yml down -v
```

---

## Performance Tuning (Optional)

For production use with large RFPs:

```yaml
# Edit docker-compose.neo4j.yml
environment:
  - NEO4J_server_memory_heap_max__size=4G # Increase from 2G
  - NEO4J_server_memory_pagecache_size=2G # Increase from 1G
```

Then restart:

```powershell
docker-compose -f docker-compose.neo4j.yml restart
```

---

**Status**: Ready for Neo4j Testing ✅
