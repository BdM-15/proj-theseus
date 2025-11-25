# TASK 01: PostgreSQL 18 Local Setup

**Branch**: Branch 010  
**Duration**: Week 1 (4-8 hours)  
**Prerequisites**: Docker Desktop OR Windows PostgreSQL installer  
**Success Criteria**: PostgreSQL 18.1+ running with pgvector extension

---

## 🎯 Objective

Install and configure PostgreSQL 18.1+ locally with required extensions for GovCon-Capture-Vibe multi-workspace support.

---

## 📋 Prerequisites

### System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 8 GB minimum (16 GB recommended for pgvector indexing)
- **Disk**: 10 GB free space (5 GB for PostgreSQL + 5 GB for data)
- **Network**: Internet access for Docker/installer downloads

### Software Requirements

**Option A (Recommended)**: Docker Desktop  
**Option B**: Native PostgreSQL installer

---

## 🚀 Installation Options

### Option A: Docker Installation (Recommended for Development)

#### Step 1: Install Docker Desktop

**Windows**:

```powershell
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Install and restart computer
# Verify installation
docker --version
# Expected: Docker version 24.0+ or higher
```

**macOS**:

```bash
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Homebrew
brew install --cask docker
```

**Linux**:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 2: Pull PostgreSQL 18 with pgvector

```bash
# Pull PostgreSQL 18 image with pgvector extension pre-installed
docker pull pgvector/pgvector:pg18

# Verify image downloaded
docker images | grep pgvector
```

#### Step 3: Run PostgreSQL Container

```bash
# Create and start PostgreSQL 18 container
docker run -d \
  --name govcon-postgres \
  -e POSTGRES_USER=govcon_user \
  -e POSTGRES_PASSWORD=secure_password_change_me \
  -e POSTGRES_DB=govcon_rfp_db \
  -p 5432:5432 \
  -v govcon_pg_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg18

# Verify container running
docker ps | grep govcon-postgres
```

**Windows PowerShell equivalent**:

```powershell
docker run -d `
  --name govcon-postgres `
  -e POSTGRES_USER=govcon_user `
  -e POSTGRES_PASSWORD=secure_password_change_me `
  -e POSTGRES_DB=govcon_rfp_db `
  -p 5432:5432 `
  -v govcon_pg_data:/var/lib/postgresql/data `
  pgvector/pgvector:pg18
```

#### Step 4: Verify PostgreSQL Installation

```bash
# Connect to PostgreSQL container
docker exec -it govcon-postgres psql -U govcon_user -d govcon_rfp_db

# Inside psql:
# Check PostgreSQL version (should be 18.1+)
SELECT version();

# Check pgvector extension available
CREATE EXTENSION IF NOT EXISTS vector;

# Verify extension installed
\dx

# Expected output should include:
#  vector | 0.8.0 | public | vector data type and ivfflat/hnsw access methods

# Exit psql
\q
```

#### Step 5: Configure Persistence

```bash
# PostgreSQL data persists in Docker volume 'govcon_pg_data'
# View volumes
docker volume ls | grep govcon

# Backup volume (recommended weekly)
docker run --rm -v govcon_pg_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

---

### Option B: Native Installation (Windows)

#### Step 1: Download PostgreSQL 18

1. Visit https://www.postgresql.org/download/windows/
2. Download PostgreSQL 18.1+ installer (EDB installer recommended)
3. Run installer

**Installation Settings**:

- **Port**: 5432 (default)
- **Locale**: English, United States
- **Superuser password**: Choose strong password (save securely!)
- **Components**: Install PostgreSQL Server, pgAdmin, Command Line Tools

#### Step 2: Add PostgreSQL to PATH

```powershell
# Add PostgreSQL bin directory to PATH
$env:PATH += ";C:\Program Files\PostgreSQL\18\bin"

# Verify psql available
psql --version
# Expected: psql (PostgreSQL) 18.1
```

#### Step 3: Create Database and User

```powershell
# Connect to PostgreSQL as superuser
psql -U postgres

# Inside psql:
# Create database
CREATE DATABASE govcon_rfp_db;

# Create user
CREATE USER govcon_user WITH PASSWORD 'secure_password_change_me';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE govcon_rfp_db TO govcon_user;

# Exit
\q
```

#### Step 4: Install pgvector Extension

**Windows Installation**:

1. Download pgvector binary from https://github.com/pgvector/pgvector/releases
2. Extract files to PostgreSQL extension directory:

   - `C:\Program Files\PostgreSQL\18\lib\` (place `vector.dll`)
   - `C:\Program Files\PostgreSQL\18\share\extension\` (place `vector.control`, `vector--*.sql`)

3. Connect and create extension:

```powershell
psql -U govcon_user -d govcon_rfp_db

# Inside psql:
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
\dx
# Should show vector extension

\q
```

**Alternative (Build from Source)**:

```powershell
# Requires Visual Studio Build Tools
git clone https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

---

## 🔧 Configuration

### Update .env File

Add PostgreSQL connection details to `.env`:

```bash
# ============================================================================
# PostgreSQL Configuration (Branch 010)
# ============================================================================

# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=govcon_user
POSTGRES_PASSWORD=secure_password_change_me
POSTGRES_DATABASE=govcon_rfp_db

# Workspace isolation (change to switch between RFPs)
POSTGRES_WORKSPACE=navy_mbos_2025

# LightRAG storage backend
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage

# Connection pooling (optional)
POSTGRES_POOL_MIN_SIZE=5
POSTGRES_POOL_MAX_SIZE=20
POSTGRES_POOL_TIMEOUT=30
```

### Test Connection from Python

```python
# test_postgres_connection.py
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

async def test_connection():
    load_dotenv()

    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT')),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DATABASE')
        )

        version = await conn.fetchval('SELECT version()')
        print(f"✅ Connected to PostgreSQL")
        print(f"Version: {version}")

        # Check pgvector
        extensions = await conn.fetch("SELECT * FROM pg_extension WHERE extname = 'vector'")
        if extensions:
            print(f"✅ pgvector extension installed: {extensions[0]['extversion']}")
        else:
            print("❌ pgvector extension NOT found")

        await conn.close()

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run test:

```powershell
python test_postgres_connection.py
```

Expected output:

```
✅ Connected to PostgreSQL
Version: PostgreSQL 18.1 on x86_64-pc-linux-gnu, compiled by gcc ...
✅ pgvector extension installed: 0.8.0
```

---

## 🧪 Validation Checklist

- [ ] PostgreSQL 18.1+ installed and running
- [ ] Can connect to database via psql
- [ ] pgvector extension (0.8.0+) installed and working
- [ ] Database `govcon_rfp_db` created
- [ ] User `govcon_user` has privileges
- [ ] `.env` file updated with connection details
- [ ] Python test script connects successfully
- [ ] Port 5432 accessible (check firewall if needed)

---

## 🐛 Troubleshooting

### Issue: Docker container won't start

```bash
# Check logs
docker logs govcon-postgres

# Common fixes:
# 1. Port 5432 already in use
docker ps -a | grep 5432
# Stop conflicting service or use different port

# 2. Permission denied (Linux)
sudo chown -R $USER:$USER /var/lib/docker/volumes/govcon_pg_data

# 3. Container exists but stopped
docker start govcon-postgres
```

### Issue: pgvector extension not found

```sql
-- Check available extensions
SELECT * FROM pg_available_extensions WHERE name LIKE '%vector%';

-- If not listed, extension files not installed
-- Reinstall pgvector binaries
```

### Issue: Python connection fails

```powershell
# Test with psql first
psql -h localhost -p 5432 -U govcon_user -d govcon_rfp_db

# If psql works but Python fails, check:
# 1. asyncpg installed
pip install asyncpg

# 2. .env file in correct location
Get-Content .env | Select-String POSTGRES

# 3. Firewall allows localhost connections
```

### Issue: Performance slow

```sql
-- Increase shared buffers (requires PostgreSQL restart)
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';

-- Restart PostgreSQL
-- Docker: docker restart govcon-postgres
-- Native: restart PostgreSQL service
```

---

## 🚀 Next Steps

✅ **Task Complete**: PostgreSQL 18 running with pgvector

**Next Task**: [TASK_02_SCHEMA_CREATION.md](TASK_02_SCHEMA_CREATION.md)  
Create 17-table schema from [01_SCHEMA_DESIGN.md](01_SCHEMA_DESIGN.md)

---

## 📚 References

- [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/18/release-18.html)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Docker PostgreSQL Image](https://hub.docker.com/_/postgres)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)

---

**Document Status**: Complete  
**Last Updated**: October 20, 2025  
**Estimated Time**: 4-8 hours (including troubleshooting)
