# Branch 004: Code Optimization & Refactoring

**Branch**: `004-code-optimization`  
**Parent**: `main` (clean slate after Branch 003 merge)  
**Created**: October 7, 2025  
**Status**: 🟢 ACTIVE - Assessment Phase  
**Next Branch**: `005-postgresql-integration` (after completion)

---

## 🎯 Mission Statement

**Refactor codebase into clean modular architecture before PostgreSQL integration.**

Branch 003 merged large monolithic files that need restructuring. This branch focuses **exclusively** on code quality, modularity, and maintainability—no new features, no PostgreSQL yet.

---

## 📊 Current State Assessment

### **Critical Issues Identified**

#### **1. Large Monolithic Files**

```
src/raganything_server.py          789 lines  ❌ (API + routing + logic mixed)
src/llm_relationship_inference.py  881 lines  ❌ (inference + prompts + validation)
src/phase6_prompts.py              518 lines  ⚠️  (could be modularized)
src/ucf_extractor.py               382 lines  ✅ (acceptable, focused)
src/ucf_detector.py                299 lines  ✅ (acceptable, focused)
src/phase6_validation.py           293 lines  ✅ (acceptable, focused)
src/ucf_section_processor.py       295 lines  ✅ (acceptable, focused)
```

**Target**: No file >400 lines (except generated/config files)

#### **2. Deleted Modular Structure**

Branch 003 removed well-organized modules:
```
❌ Deleted: src/core/           (ontology, chunking, integration)
❌ Deleted: src/agents/         (PydanticAI agents)
❌ Deleted: src/models/         (Pydantic models)
❌ Deleted: src/api/            (route organization)
❌ Deleted: src/utils/          (logging, monitoring)
```

**Consequence**: All functionality now in flat `src/` with large monolithic files.

#### **3. Mixed Responsibilities**

**`raganything_server.py` (789 lines)**:
- FastAPI application setup
- Multiple route definitions (documents, graph, query, health)
- LightRAG initialization logic
- Error handling and logging
- Business logic mixed with API layer

**`llm_relationship_inference.py` (881 lines)**:
- LLM-powered relationship inference
- Prompt templates (hardcoded strings)
- Entity/relationship validation
- Batch processing logic
- Storage interaction

#### **4. Hardcoded Configuration**

- Prompt templates embedded in Python files
- No clear configuration management
- Environment variables scattered across files
- Storage logic tightly coupled to implementation

---

## 🏗️ Target Architecture

### **New Modular Structure**

```
src/
├── __init__.py
│
├── core/                          # Core LightRAG integration & config
│   ├── __init__.py
│   ├── ontology.py               # Entity types, relationships, constraints
│   ├── lightrag_config.py        # LightRAG initialization & configuration
│   ├── storage_interface.py      # Abstract storage layer (prep PostgreSQL)
│   └── context_manager.py        # Workspace & environment management
│
├── extractors/                    # Domain-specific content extraction
│   ├── __init__.py
│   ├── ucf_detector.py           # ✅ Keep existing (299 lines)
│   ├── ucf_extractor.py          # ✅ Keep existing (382 lines)
│   ├── section_processor.py      # Refactor from ucf_section_processor.py
│   ├── program_extractor.py      # NEW: Extract PROGRAM entity logic
│   └── requirement_extractor.py  # NEW: Extract requirement logic
│
├── inference/                     # LLM-powered post-processing
│   ├── __init__.py
│   ├── relationship_engine.py    # Main inference orchestrator
│   ├── l_m_mapper.py             # Section L ↔ M relationship mapping
│   ├── clause_clusterer.py       # FAR/DFARS clause clustering
│   ├── annex_linker.py           # Annex/attachment linkage
│   ├── requirement_mapper.py     # Requirement → evaluation factor mapping
│   └── validators.py             # Entity/relationship validation
│
├── prompts/                       # Centralized prompt management
│   ├── __init__.py
│   ├── extraction_prompts.py     # Entity extraction prompts
│   ├── inference_prompts.py      # Relationship inference prompts
│   ├── validation_prompts.py     # Validation prompts
│   └── templates/                # Jinja2 templates for complex prompts
│       ├── entity_extraction.j2
│       ├── relationship_inference.j2
│       └── section_analysis.j2
│
├── api/                           # Clean API layer
│   ├── __init__.py
│   ├── app.py                    # FastAPI application factory
│   ├── middleware.py             # Logging, error handling, CORS
│   ├── dependencies.py           # Dependency injection
│   └── routes/                   # Organized route modules
│       ├── __init__.py
│       ├── documents.py          # Document upload/management
│       ├── graph.py              # Knowledge graph operations
│       ├── query.py              # RAG query endpoints
│       ├── analysis.py           # RFP analysis endpoints
│       └── health.py             # Health checks & monitoring
│
├── models/                        # Pydantic data models
│   ├── __init__.py
│   ├── entities.py               # Entity schemas (all 18 types)
│   ├── relationships.py          # Relationship schemas
│   ├── rfp.py                    # RFP-specific models
│   ├── config.py                 # Configuration models
│   └── responses.py              # API response models
│
└── utils/                         # Cross-cutting utilities
    ├── __init__.py
    ├── logging.py                # Centralized logging configuration
    ├── performance.py            # Performance monitoring utilities
    ├── file_operations.py        # File I/O helpers
    └── validation.py             # Common validation functions

app.py                             # Entry point (minimal, delegates to api/app.py)
```

### **Design Principles**

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Injection**: Use FastAPI's dependency system
3. **Interface Segregation**: Abstract storage layer for future PostgreSQL
4. **Configuration Management**: Centralized config with Pydantic models
5. **Separation of Concerns**: API ≠ Business Logic ≠ Data Access

---

## 📋 Implementation Plan

### **Phase 1: Assessment & Planning** (30 minutes)

#### **Task 1.1: Analyze Current Files**
- [ ] Read and document `src/raganything_server.py` structure
- [ ] Read and document `src/llm_relationship_inference.py` structure
- [ ] Identify all dependencies and imports
- [ ] Map current functionality to target modules

#### **Task 1.2: Create Module Structure**
- [ ] Create all new directories (`core/`, `extractors/`, `inference/`, `prompts/`, `api/`, `models/`, `utils/`)
- [ ] Create `__init__.py` files with docstrings
- [ ] Document module responsibilities

#### **Task 1.3: Define Interfaces**
- [ ] Design `StorageInterface` abstract class (prep for PostgreSQL)
- [ ] Define configuration schema in `models/config.py`
- [ ] Document API contract for each route module

---

### **Phase 2: Core Infrastructure** (45 minutes)

#### **Task 2.1: Configuration Management**
**Target**: `src/core/lightrag_config.py` + `src/models/config.py`

**Extract from**: `raganything_server.py` initialization logic

**Implementation**:
```python
# src/models/config.py
from pydantic_settings import BaseSettings

class LightRAGConfig(BaseSettings):
    """LightRAG configuration with environment variable support."""
    working_dir: str
    llm_model: str
    embedding_model: str
    chunk_size: int
    # ... all config parameters
    
    class Config:
        env_file = ".env"
        env_prefix = "LIGHTRAG_"

# src/core/lightrag_config.py
def create_lightrag_instance(config: LightRAGConfig) -> LightRAG:
    """Factory function to create configured LightRAG instance."""
    # Clean initialization logic here
```

#### **Task 2.2: Storage Abstraction**
**Target**: `src/core/storage_interface.py`

**Purpose**: Prepare for PostgreSQL integration in Branch 005

**Implementation**:
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class StorageInterface(ABC):
    """Abstract storage layer for LightRAG data."""
    
    @abstractmethod
    async def save_entities(self, entities: List[Dict]) -> None:
        """Save entities to storage."""
        pass
    
    @abstractmethod
    async def save_relationships(self, relationships: List[Dict]) -> None:
        """Save relationships to storage."""
        pass
    
    @abstractmethod
    async def query(self, query: str, mode: str) -> Dict:
        """Execute query against storage."""
        pass

class FileSystemStorage(StorageInterface):
    """Current file-based storage implementation."""
    # Wrap existing LightRAG file operations

class PostgreSQLStorage(StorageInterface):
    """Future PostgreSQL storage (Branch 005)."""
    pass  # Placeholder
```

#### **Task 2.3: Ontology Module**
**Target**: `src/core/ontology.py`

**Extract from**: Scattered entity type definitions

**Implementation**:
```python
from enum import Enum
from typing import Dict, List

class EntityType(str, Enum):
    """Government contracting entity types."""
    REQUIREMENT = "REQUIREMENT"
    DELIVERABLE = "DELIVERABLE"
    EVALUATION_FACTOR = "EVALUATION_FACTOR"
    PROGRAM = "PROGRAM"
    # ... all 18 types

class RelationshipType(str, Enum):
    """Relationship types in government contracting."""
    LINKS_TO = "LINKS_TO"
    EVALUATED_BY = "EVALUATED_BY"
    PART_OF = "PART_OF"
    # ... all relationship types

ENTITY_CONSTRAINTS: Dict[EntityType, Dict] = {
    # Validation rules, metadata schema, etc.
}
```

---

### **Phase 3: Break Up Large Files** (60 minutes)

#### **Task 3.1: Refactor `llm_relationship_inference.py` (881 lines)**

**Target Structure**:
```
inference/
├── relationship_engine.py     # Main orchestrator (150 lines)
├── l_m_mapper.py             # L↔M mapping (120 lines)
├── clause_clusterer.py       # FAR/DFARS clustering (120 lines)
├── annex_linker.py           # Annex linkage (100 lines)
├── requirement_mapper.py     # Req→eval mapping (120 lines)
└── validators.py             # Validation logic (100 lines)

prompts/
└── inference_prompts.py      # Extracted prompt templates (150 lines)
```

**Steps**:
1. Extract prompt templates to `prompts/inference_prompts.py`
2. Extract validation logic to `inference/validators.py`
3. Split inference algorithms into separate modules
4. Create orchestrator in `relationship_engine.py`
5. Update imports and test

#### **Task 3.2: Refactor `raganything_server.py` (789 lines)**

**Target Structure**:
```
api/
├── app.py                    # FastAPI factory (80 lines)
├── middleware.py             # Middleware setup (60 lines)
├── dependencies.py           # DI helpers (40 lines)
└── routes/
    ├── documents.py          # Document routes (120 lines)
    ├── graph.py              # Graph routes (100 lines)
    ├── query.py              # Query routes (120 lines)
    ├── analysis.py           # Analysis routes (80 lines)
    └── health.py             # Health routes (40 lines)
```

**Steps**:
1. Extract route definitions to separate route modules
2. Create FastAPI factory function in `app.py`
3. Move middleware to `middleware.py`
4. Extract dependency injection to `dependencies.py`
5. Update `app.py` (root) to use factory function
6. Test all endpoints

#### **Task 3.3: Modularize `phase6_prompts.py` (518 lines)**

**Target Structure**:
```
prompts/
├── extraction_prompts.py     # Entity extraction (200 lines)
├── inference_prompts.py      # Relationship inference (200 lines)
└── templates/                # Jinja2 templates
    ├── entity_extraction.j2  # Complex extraction prompt
    └── relationship_inference.j2
```

**Steps**:
1. Split prompts by type (extraction vs inference)
2. Convert complex prompts to Jinja2 templates
3. Create prompt loading utilities
4. Update inference modules to use new structure

---

### **Phase 4: Create Data Models** (30 minutes)

#### **Task 4.1: Entity Models**
**Target**: `src/models/entities.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from src.core.ontology import EntityType

class BaseEntity(BaseModel):
    """Base entity model with common fields."""
    id: str
    type: EntityType
    content: str
    metadata: Optional[Dict] = None

class Requirement(BaseEntity):
    """Requirement entity with domain-specific fields."""
    type: EntityType = EntityType.REQUIREMENT
    section: Optional[str] = None
    compliance_level: Optional[str] = None
    criticality: Optional[str] = None

class Program(BaseEntity):
    """Program entity (Branch 003 addition)."""
    type: EntityType = EntityType.PROGRAM
    program_name: Optional[str] = None
    agency: Optional[str] = None
    # ... PROGRAM-specific fields
```

#### **Task 4.2: Relationship Models**
**Target**: `src/models/relationships.py`

```python
class BaseRelationship(BaseModel):
    """Base relationship model."""
    source_id: str
    target_id: str
    type: RelationshipType
    metadata: Optional[Dict] = None

class EvaluationLink(BaseRelationship):
    """Requirement → Evaluation Factor link."""
    type: RelationshipType = RelationshipType.EVALUATED_BY
    evaluation_weight: Optional[float] = None
```

#### **Task 4.3: Configuration Models**
**Target**: `src/models/config.py`

```python
class LightRAGConfig(BaseSettings):
    """Complete LightRAG configuration."""
    # All environment variables with validation
    working_dir: Path = Field(default="./rag_storage")
    llm_model: str = Field(default="mistral-nemo:latest")
    # ... all config parameters with defaults and validation
```

---

### **Phase 5: API Layer Cleanup** (45 minutes)

#### **Task 5.1: Route Modules**
Create clean route modules using FastAPI best practices:

```python
# src/api/routes/documents.py
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from src.api.dependencies import get_lightrag_instance
from src.models.responses import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    lightrag = Depends(get_lightrag_instance)
):
    """Upload and process RFP document."""
    # Clean, focused implementation
    pass
```

#### **Task 5.2: Dependency Injection**
```python
# src/api/dependencies.py
from fastapi import Depends
from src.core.lightrag_config import create_lightrag_instance
from src.models.config import LightRAGConfig

def get_config() -> LightRAGConfig:
    """Get application configuration."""
    return LightRAGConfig()

def get_lightrag_instance(config: LightRAGConfig = Depends(get_config)):
    """Get configured LightRAG instance."""
    return create_lightrag_instance(config)
```

#### **Task 5.3: Application Factory**
```python
# src/api/app.py
from fastapi import FastAPI
from src.api.middleware import setup_middleware
from src.api.routes import documents, graph, query, analysis, health

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="GovCon Capture Vibe API")
    
    setup_middleware(app)
    
    app.include_router(documents.router)
    app.include_router(graph.router)
    app.include_router(query.router)
    app.include_router(analysis.router)
    app.include_router(health.router)
    
    return app
```

---

### **Phase 6: Utilities & Cross-Cutting Concerns** (30 minutes)

#### **Task 6.1: Logging Configuration**
**Target**: `src/utils/logging.py`

```python
import logging
from pathlib import Path

def setup_logging(log_dir: Path = Path("logs")) -> None:
    """Configure application logging."""
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    # Add file and console handlers
    # Set format and levels
```

#### **Task 6.2: Performance Monitoring**
**Target**: `src/utils/performance.py`

```python
from contextlib import contextmanager
from time import perf_counter

@contextmanager
def measure_time(operation: str):
    """Context manager for performance measurement."""
    start = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - start
        logger.info(f"{operation} completed in {elapsed:.2f}s")
```

#### **Task 6.3: Validation Utilities**
**Target**: `src/utils/validation.py`

```python
from typing import List, Dict
from src.models.entities import BaseEntity

def validate_entity_structure(entity: Dict) -> bool:
    """Validate entity has required fields."""
    # Validation logic
    pass

def validate_relationships(
    relationships: List[Dict],
    entities: List[BaseEntity]
) -> List[str]:
    """Validate relationships reference existing entities."""
    # Return list of errors
    pass
```

---

### **Phase 7: Testing & Validation** (30 minutes)

#### **Task 7.1: Import Validation**
- [ ] Verify all imports resolve correctly
- [ ] Check for circular dependencies
- [ ] Validate module organization

#### **Task 7.2: Functional Testing**
```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start server
python app.py

# Test endpoints
# POST /documents (upload RFP)
# GET /documents (list documents)
# POST /query (RAG query)
# GET /kg (knowledge graph)
```

#### **Task 7.3: Compare with Branch 003**
- [ ] Verify all functionality preserved
- [ ] Compare entity extraction results
- [ ] Validate knowledge graph quality
- [ ] Check performance metrics

---

### **Phase 8: Documentation & Cleanup** (30 minutes)

#### **Task 8.1: Update Documentation**
- [ ] Update `README.md` architecture section
- [ ] Document new module structure
- [ ] Update API documentation
- [ ] Create module-level docstrings

#### **Task 8.2: Clean Up Old Files**
- [ ] Remove/archive old monolithic files
- [ ] Update `.gitignore` if needed
- [ ] Clean up test files

#### **Task 8.3: Create Migration Guide**
- [ ] Document changes from Branch 003
- [ ] List breaking changes (if any)
- [ ] Provide import path updates

---

## 🎯 Success Criteria

### **Code Quality Metrics**

- [ ] **No file >400 lines** (except config/generated files)
- [ ] **All modules <200 lines average**
- [ ] **Clear separation of concerns** (API ≠ Business Logic ≠ Data)
- [ ] **Single responsibility** per module
- [ ] **No circular dependencies**

### **Functionality Preservation**

- [ ] **All Branch 003 features working** (PROGRAM entities, Phase 6.1 inference)
- [ ] **API endpoints functional** (documents, graph, query)
- [ ] **Entity extraction quality maintained** (285 entities, 267 relationships)
- [ ] **Knowledge graph construction intact**
- [ ] **WebUI compatibility** (LightRAG interface)

### **PostgreSQL Readiness**

- [ ] **Storage interface defined** (`StorageInterface` abstract class)
- [ ] **Configuration externalized** (Pydantic models)
- [ ] **Dependencies injectable** (FastAPI DI)
- [ ] **Clean data models** (Pydantic schemas)

### **Documentation**

- [ ] **Module docstrings** for all new modules
- [ ] **README.md updated** with new architecture
- [ ] **Migration guide created** for Branch 003 → 004
- [ ] **API documentation current**

---

## 📊 Estimated Timeline

| Phase | Tasks | Time | Dependencies |
|-------|-------|------|--------------|
| **Phase 1** | Assessment & Planning | 30 min | None |
| **Phase 2** | Core Infrastructure | 45 min | Phase 1 |
| **Phase 3** | Break Up Large Files | 60 min | Phase 2 |
| **Phase 4** | Create Data Models | 30 min | Phase 2 |
| **Phase 5** | API Layer Cleanup | 45 min | Phase 3, 4 |
| **Phase 6** | Utilities | 30 min | Phase 2 |
| **Phase 7** | Testing & Validation | 30 min | Phase 3-6 |
| **Phase 8** | Documentation | 30 min | Phase 7 |
| **Total** | - | **4.5 hours** | - |

---

## 🔄 Next Steps After Completion

### **Immediate Actions**
1. **Commit all changes** to `004-code-optimization` branch
2. **Push to remote** GitHub repository
3. **Merge to main** after validation
4. **Create Branch 005** (`005-postgresql-integration`)

### **Branch 005 Preview: PostgreSQL Integration**

With clean modular architecture from Branch 004, PostgreSQL integration becomes straightforward:

1. **Implement `PostgreSQLStorage`** class (already abstracted in `storage_interface.py`)
2. **Add database migrations** (Alembic)
3. **Update configuration** (add PostgreSQL connection strings)
4. **Swap storage backend** via dependency injection
5. **No API changes** (interface already defined)

**Estimated Time**: 2 hours (vs 4+ hours without refactoring)

---

## 🚨 Important Notes

### **DO NOT in This Branch**
- ❌ **No PostgreSQL implementation** (that's Branch 005)
- ❌ **No new features** (optimization only)
- ❌ **No RAG-Anything integration** (future Phase 4-6)
- ❌ **No prompt improvements** (just organize existing)

### **DO in This Branch**
- ✅ **Refactor existing code** into clean modules
- ✅ **Break up large files** (<400 lines each)
- ✅ **Add abstractions** (storage interface, config management)
- ✅ **Improve organization** (clear module responsibilities)
- ✅ **Preserve functionality** (all Branch 003 features work)

### **Critical Rules**
1. **Activate `.venv` before any Python command**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Use workspace tools for file operations** (never PowerShell):
   - ✅ `create_file`, `read_file`, `replace_string_in_file`
   - ❌ `New-Item`, `Get-Content`, `Set-Content`

3. **Test frequently** (verify imports after each module split)

4. **Commit incrementally** (one phase at a time)

---

## 📁 Quick Reference: File Mapping

### **Current (Branch 003) → Target (Branch 004)**

```
Current Monolithic Files              Target Modular Structure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
src/
├── raganything_server.py (789)  →   api/
│                                    ├── app.py (80)
│                                    ├── middleware.py (60)
│                                    ├── dependencies.py (40)
│                                    └── routes/
│                                        ├── documents.py (120)
│                                        ├── graph.py (100)
│                                        ├── query.py (120)
│                                        ├── analysis.py (80)
│                                        └── health.py (40)
│
├── llm_relationship_inference.py →  inference/
│   (881 lines)                      ├── relationship_engine.py (150)
│                                    ├── l_m_mapper.py (120)
│                                    ├── clause_clusterer.py (120)
│                                    ├── annex_linker.py (100)
│                                    ├── requirement_mapper.py (120)
│                                    └── validators.py (100)
│                                    
│                                    prompts/
│                                    └── inference_prompts.py (150)
│
├── phase6_prompts.py (518)      →   prompts/
│                                    ├── extraction_prompts.py (200)
│                                    ├── inference_prompts.py (200)
│                                    └── templates/ (Jinja2)
│
├── ucf_detector.py (299)        →   extractors/ucf_detector.py ✅
├── ucf_extractor.py (382)       →   extractors/ucf_extractor.py ✅
├── ucf_section_processor.py     →   extractors/section_processor.py
├── phase6_validation.py (293)   →   inference/validators.py (merge)
│
└── (NEW)                        →   core/
                                     ├── ontology.py (entity types)
                                     ├── lightrag_config.py (init)
                                     └── storage_interface.py (abstract)
                                     
                                     models/
                                     ├── entities.py (Pydantic)
                                     ├── relationships.py (Pydantic)
                                     ├── config.py (Pydantic)
                                     └── responses.py (API models)
                                     
                                     utils/
                                     ├── logging.py
                                     ├── performance.py
                                     └── validation.py
```

---

## 🎓 Refactoring Strategy Tips

### **Approach for Large Files**

1. **Read entire file** first (understand full context)
2. **Identify functional sections** (what does each part do?)
3. **Extract utilities first** (easiest, least dependencies)
4. **Extract data models** (entities, relationships)
5. **Extract prompts** (move strings to separate files)
6. **Extract business logic** (inference algorithms)
7. **Keep orchestration** (main coordination logic)
8. **Update imports** (test after each extraction)

### **Dependency Management**

```python
# BEFORE: Circular dependency risk
# file_a.py imports file_b.py
# file_b.py imports file_a.py

# AFTER: Clean layered architecture
# models/ (no dependencies)
#   ↓
# core/ (depends on models/)
#   ↓
# extractors/ (depends on core/, models/)
#   ↓
# inference/ (depends on extractors/, core/, models/)
#   ↓
# api/ (depends on all layers)
```

### **Testing Each Phase**

```powershell
# After each major refactoring step:

# 1. Check imports
python -c "from src.api.app import create_app; print('Imports OK')"

# 2. Start server
python app.py  # Should start without errors

# 3. Test endpoints
# Visit http://localhost:9621/docs
# Try health check endpoint
# Upload test RFP document
```

---

## 📞 Handoff Checklist

When starting new conversation with this plan:

- [ ] **Branch**: Verify you're on `004-code-optimization`
- [ ] **Context**: Read this document top to bottom
- [ ] **Current State**: List `src/` directory files
- [ ] **Start Phase 1**: Begin with assessment tasks
- [ ] **Incremental Commits**: Commit after each phase completion

**First Command in New Conversation**:
```powershell
git branch  # Confirm on 004-code-optimization
```

**First Question to Ask**:
"I'm ready to start Branch 004 code optimization. Should I begin with Phase 1 assessment, reading the current structure of `src/raganything_server.py` and `src/llm_relationship_inference.py`?"

---

## 🎯 Final Goal Statement

**Transform Branch 003's monolithic codebase into clean, modular architecture that:**

1. ✅ **Maintains all functionality** (PROGRAM entities, Phase 6.1 inference, LightRAG integration)
2. ✅ **Reduces file sizes** (no file >400 lines)
3. ✅ **Improves maintainability** (clear separation of concerns)
4. ✅ **Prepares for PostgreSQL** (storage abstraction, configuration management)
5. ✅ **Enhances testability** (small, focused modules with clear interfaces)

**Result**: Clean foundation for Branch 005 (PostgreSQL) and future enhancements (RAG-Anything, fine-tuning).

---

**Branch Created**: October 7, 2025  
**Document Version**: 1.0  
**Next Update**: After Phase 1 completion
