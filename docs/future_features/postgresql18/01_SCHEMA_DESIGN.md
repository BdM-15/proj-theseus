# PostgreSQL Schema Design for GovCon Capture Intelligence

**Complete Database Architecture for Agent-Powered RFP Analysis**

**Date**: October 19, 2025  
**Purpose**: Define PostgreSQL schema to support knowledge graphs, agent outputs, and cross-RFP intelligence  
**Extensions Required**: pgvector (embeddings), Apache AGE (graph queries), JSONB (flexible metadata)

---

## 🎯 Design Principles

### 1. Hybrid Storage Model

**Problem**: Knowledge graphs (GraphML) are great for relationships, but rigid for agent outputs  
**Solution**: Store both structured relational data AND flexible JSON for evolving schemas

```
Relational Tables (structured, indexed, queryable)
    ↓
JSONB Columns (flexible metadata, agent outputs)
    ↓
pgvector (semantic search on embeddings)
    ↓
Apache AGE (graph traversal queries)
```

### 2. Single Source of Truth

- ✅ All RFP data in PostgreSQL (no more JSON file juggling)
- ✅ Knowledge graph stored as both GraphML (blob) AND relational tables (queryable)
- ✅ Agent outputs stored alongside source data (traceability)
- ✅ Audit trail for all changes (who/when/what)

### 3. Agent-First Design

- ✅ Every agent output gets its own table (compliance_assessments, gap_analyses, etc.)
- ✅ Foreign keys link outputs to source entities (requirement → compliance item)
- ✅ Versioning for iterative refinement (Proposal V1 → V2 → V3)

---

## 📊 Complete Schema (17 Tables)

### Category 1: Document Management (3 tables)

#### Table: `rfp_documents`

**Purpose**: Master list of all RFPs processed  
**Usage**: Root entity for all relationships, workspace selection

```sql
CREATE TABLE rfp_documents (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document metadata
    original_filename VARCHAR(500) NOT NULL,          -- "Navy_MBOS_RFP_2024.pdf"
    sanitized_filename VARCHAR(500) NOT NULL,         -- Filename used in storage
    upload_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed

    -- Agency/contract info (extracted from document)
    agency VARCHAR(200),                               -- "Department of Navy"
    solicitation_number VARCHAR(100),                  -- "N00189-24-R-0045"
    title TEXT,                                        -- "MBOS Base Operating Support"
    contract_type VARCHAR(50),                         -- "IDIQ", "Task Order", "FFP"
    estimated_value NUMERIC(15,2),                     -- Dollar amount

    -- Parent-child hierarchy (for IDIQ + Task Orders)
    parent_rfp_id UUID REFERENCES rfp_documents(id),   -- NULL for base contracts, links to IDIQ for task orders
    hierarchy_level INT DEFAULT 0,                     -- 0=base, 1=task order, 2=sub-task order

    -- Dates
    solicitation_date DATE,
    proposal_due_date TIMESTAMPTZ,
    contract_start_date DATE,
    contract_end_date DATE,

    -- Processing metrics
    page_count INT,
    entity_count INT,                                  -- Total entities extracted
    relationship_count INT,                            -- Total relationships inferred
    processing_time_seconds INT,
    processing_cost_usd NUMERIC(10,4),                 -- LLM cost

    -- Knowledge graph storage
    graphml_data BYTEA,                                -- Compressed GraphML file
    graphml_checksum VARCHAR(64),                      -- SHA-256 for change detection

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),                           -- User email or system

    -- Indexes
    CONSTRAINT unique_solicitation UNIQUE(solicitation_number)
);

-- Indexes for common queries
CREATE INDEX idx_rfp_agency ON rfp_documents(agency);
CREATE INDEX idx_rfp_status ON rfp_documents(processing_status);
CREATE INDEX idx_rfp_parent ON rfp_documents(parent_rfp_id);
CREATE INDEX idx_rfp_upload_date ON rfp_documents(upload_date DESC);
```

---

#### Table: `document_sections`

**Purpose**: Store UCF sections (Section A-M, J attachments) with hierarchies  
**Usage**: Section-level queries, attachment linkage

```sql
CREATE TABLE document_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Section identification
    structural_label VARCHAR(100) NOT NULL,            -- "Section L", "J-02000000", "Attachment 5"
    semantic_type VARCHAR(50),                         -- SOLICITATION_FORM, EVALUATION_CRITERIA, etc.
    section_title TEXT,                                -- "Instructions to Offerors"

    -- Hierarchy
    parent_section_id UUID REFERENCES document_sections(id),  -- For nested sections
    section_order INT,                                 -- Sequential order in document

    -- Content
    page_range VARCHAR(20),                            -- "15-25"
    full_text TEXT,                                    -- Complete section text
    summary TEXT,                                      -- LLM-generated summary

    -- Detection metadata
    detection_confidence FLOAT,                        -- 0.0-1.0 (UCF detection confidence)
    also_contains VARCHAR(200)[],                      -- ["SUBMISSION_INSTRUCTION"] if mixed content

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_section_per_rfp UNIQUE(rfp_id, structural_label)
);

CREATE INDEX idx_sections_rfp ON document_sections(rfp_id);
CREATE INDEX idx_sections_type ON document_sections(semantic_type);
CREATE INDEX idx_sections_parent ON document_sections(parent_section_id);
```

---

#### Table: `amendments`

**Purpose**: Track RFP amendments with change detection  
**Usage**: Amendment impact analysis agent, change tracking

```sql
CREATE TABLE amendments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    base_rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Amendment metadata
    amendment_number INT NOT NULL,                     -- 0001, 0002, etc.
    issue_date DATE NOT NULL,
    title VARCHAR(500),

    -- Change summary
    total_changes INT,                                 -- Count of modifications
    critical_changes INT,                              -- High-impact changes
    sections_affected VARCHAR(100)[],                  -- ["Section L", "Section M", "J-02"]

    -- Change types
    additions_count INT DEFAULT 0,
    modifications_count INT DEFAULT 0,
    deletions_count INT DEFAULT 0,

    -- Impact assessment (agent-generated)
    impact_summary TEXT,                               -- LLM-generated summary
    revision_required BOOLEAN DEFAULT FALSE,           -- Does proposal need revision?
    estimated_revision_hours INT,

    -- File storage
    amendment_file_path VARCHAR(500),
    graphml_data BYTEA,                                -- Knowledge graph of amended RFP

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_amendment UNIQUE(base_rfp_id, amendment_number)
);

CREATE INDEX idx_amendments_rfp ON amendments(base_rfp_id);
CREATE INDEX idx_amendments_date ON amendments(issue_date DESC);
```

---

### Category 2: Knowledge Graph Entities (6 tables)

#### Table: `entities`

**Purpose**: Master entity table (all 17 types)  
**Usage**: Semantic search, cross-RFP entity queries

```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Entity core
    entity_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,                 -- REQUIREMENT, EVALUATION_FACTOR, etc. (17 types)
    description TEXT NOT NULL,

    -- Source location
    source_section_id UUID REFERENCES document_sections(id),
    page_reference VARCHAR(50),

    -- Semantic search (pgvector)
    embedding vector(3072),                            -- OpenAI text-embedding-3-large

    -- Flexible metadata (JSONB for entity-specific fields)
    metadata JSONB NOT NULL DEFAULT '{}',
    /*
    Example metadata structures:

    REQUIREMENT:
    {
      "requirement_type": "FUNCTIONAL",
      "criticality_level": "MANDATORY",
      "priority_score": 100,
      "modal_verb": "shall",
      "subject": "Contractor",
      "section_origin": "Section C.3.1.2"
    }

    EVALUATION_FACTOR:
    {
      "factor_id": "M1",
      "relative_importance": "Most Important",
      "factor_weight": 0.40,
      "subfactors": ["M1.1", "M1.2"],
      "tradeoff_methodology": "Best Value",
      "evaluated_by_rating": "Adjectival"
    }

    CLAUSE:
    {
      "clause_number": "FAR 52.212-1",
      "agency_supplement": "FAR",
      "clause_title": "Instructions to Offerors",
      "incorporation_method": "Full Text",
      "date": "JAN 2024"
    }

    DELIVERABLE:
    {
      "deliverable_id": "CDRL A001",
      "due_date": "2025-02-05",
      "format": "Excel",
      "submission_method": "Electronic"
    }

    STRATEGIC_THEME:
    {
      "theme_type": "CUSTOMER_HOT_BUTTON",
      "competitive_context": "Incumbent advantage",
      "customer_benefit": "Zero-downtime migration",
      "discriminator": "Phased approach unique to our team"
    }
    */

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_entity_type CHECK (entity_type IN (
        'ORGANIZATION', 'CONCEPT', 'EVENT', 'TECHNOLOGY', 'PERSON', 'LOCATION',
        'REQUIREMENT', 'CLAUSE', 'SECTION', 'DOCUMENT', 'DELIVERABLE',
        'PROGRAM', 'EQUIPMENT', 'EVALUATION_FACTOR', 'SUBMISSION_INSTRUCTION',
        'STRATEGIC_THEME', 'STATEMENT_OF_WORK'
    ))
);

-- Indexes for common queries
CREATE INDEX idx_entities_rfp ON entities(rfp_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities(entity_name);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops);  -- pgvector
CREATE INDEX idx_entities_metadata ON entities USING gin(metadata);  -- JSONB index

-- JSONB indexes for specific metadata queries
CREATE INDEX idx_requirement_criticality ON entities ((metadata->>'criticality_level')) WHERE entity_type = 'REQUIREMENT';
CREATE INDEX idx_factor_weight ON entities ((metadata->>'factor_weight')) WHERE entity_type = 'EVALUATION_FACTOR';
```

---

#### Table: `relationships`

**Purpose**: Store all entity relationships  
**Usage**: Graph traversal, requirement→factor mapping, Section L↔M linking

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Relationship core
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,           -- EVALUATED_BY, GUIDES, ATTACHMENT_OF, etc.

    -- Inference metadata
    confidence FLOAT,                                  -- 0.0-1.0 (for LLM-inferred relationships)
    inference_method VARCHAR(50),                      -- "explicit", "semantic", "pattern", "llm"
    reasoning TEXT,                                    -- Why this relationship was inferred

    -- Relationship-specific metadata
    metadata JSONB DEFAULT '{}',
    /*
    Example:
    {
      "weight": 0.85,
      "evidence_page": "42",
      "cross_reference": "Section L.3.1"
    }
    */

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT no_self_reference CHECK (source_entity_id != target_entity_id),
    CONSTRAINT unique_relationship UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

CREATE INDEX idx_relationships_rfp ON relationships(rfp_id);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
```

---

#### Table: `requirements` (Denormalized View)

**Purpose**: Fast queries for requirement-specific fields (denormalized from entities)  
**Usage**: Compliance checklists, gap analysis, requirement→factor mapping

```sql
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE REFERENCES entities(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Requirement core (denormalized for query performance)
    requirement_id VARCHAR(100) NOT NULL,              -- "REQ-012", "REQUIREMENT_043"
    description TEXT NOT NULL,

    -- Shipley criticality
    requirement_type VARCHAR(50),                      -- FUNCTIONAL, PERFORMANCE, SECURITY, etc.
    criticality_level VARCHAR(50) NOT NULL,            -- MANDATORY, IMPORTANT, OPTIONAL, INFORMATIONAL
    priority_score INT NOT NULL,                       -- 0-100
    modal_verb VARCHAR(20),                            -- shall, should, may, must, will
    subject VARCHAR(50),                               -- Contractor, Offeror, Government

    -- Source
    section_origin VARCHAR(100),                       -- "Section C.3.1.2"
    page_reference VARCHAR(50),

    -- Evaluation linkage (denormalized for performance)
    evaluation_factors UUID[],                         -- Array of evaluation_factor entity_ids

    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', requirement_id || ' ' || description)
    ) STORED,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_requirements_rfp ON requirements(rfp_id);
CREATE INDEX idx_requirements_criticality ON requirements(criticality_level);
CREATE INDEX idx_requirements_type ON requirements(requirement_type);
CREATE INDEX idx_requirements_search ON requirements USING gin(search_vector);
CREATE INDEX idx_requirements_factors ON requirements USING gin(evaluation_factors);
```

---

#### Table: `evaluation_factors` (Denormalized View)

**Purpose**: Fast queries for Section M evaluation factors  
**Usage**: Proposal outline generation, page allocation, factor analysis

```sql
CREATE TABLE evaluation_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE REFERENCES entities(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Factor core
    factor_id VARCHAR(50) NOT NULL,                    -- "M1", "M2.1", "Factor 1"
    factor_name VARCHAR(500) NOT NULL,                 -- "Technical Approach"
    description TEXT,

    -- Weighting
    relative_importance VARCHAR(100),                  -- "Most Important", "40% weight"
    factor_weight FLOAT,                               -- 0.40 for 40%
    subfactors VARCHAR(100)[],                         -- ["M2.1", "M2.2"]

    -- Evaluation methodology
    tradeoff_methodology VARCHAR(50),                  -- "Best Value", "LPTA"
    evaluated_by_rating VARCHAR(50),                   -- "Adjectival", "Point Score"

    -- Section L linkage
    section_l_references VARCHAR(100)[],               -- ["L.3.1", "L.3.2"]
    page_limits VARCHAR(50),                           -- "25 pages"
    format_requirements TEXT,

    -- Requirements linkage (denormalized)
    requirement_count INT DEFAULT 0,                   -- Count of requirements mapped to this factor

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_factors_rfp ON evaluation_factors(rfp_id);
CREATE INDEX idx_eval_factors_weight ON evaluation_factors(factor_weight DESC NULLS LAST);
CREATE INDEX idx_eval_factors_id ON evaluation_factors(factor_id);
```

---

#### Table: `clauses` (Denormalized View)

**Purpose**: Fast queries for FAR/DFARS clauses  
**Usage**: Compliance analysis, clause frequency trends, regulatory intelligence

```sql
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE REFERENCES entities(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Clause core
    clause_number VARCHAR(50) NOT NULL,                -- "FAR 52.212-1", "DFARS 252.204-7012"
    agency_supplement VARCHAR(20) NOT NULL,            -- "FAR", "DFARS", "AFFARS", etc.
    clause_title TEXT NOT NULL,

    -- Metadata
    section_attribution VARCHAR(50),                   -- "Section I", "Section K"
    incorporation_method VARCHAR(50),                  -- "Full Text", "By Reference"
    effective_date VARCHAR(20),                        -- "JAN 2024"

    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', clause_number || ' ' || clause_title)
    ) STORED,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_clauses_rfp ON clauses(rfp_id);
CREATE INDEX idx_clauses_number ON clauses(clause_number);
CREATE INDEX idx_clauses_agency ON clauses(agency_supplement);
CREATE INDEX idx_clauses_search ON clauses USING gin(search_vector);
```

---

#### Table: `deliverables` (Denormalized View)

**Purpose**: Fast queries for CDRLs and deliverables  
**Usage**: Deliverable tracking, SOW→CDRL mapping, schedule analysis

```sql
CREATE TABLE deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE REFERENCES entities(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Deliverable core
    deliverable_id VARCHAR(50) NOT NULL,               -- "CDRL A001"
    deliverable_name VARCHAR(500) NOT NULL,            -- "Monthly Status Report"
    description TEXT,

    -- Schedule
    due_date DATE,
    frequency VARCHAR(50),                             -- "Monthly", "Quarterly", "One-time"

    -- Format
    format VARCHAR(50),                                -- "Excel", "PDF", "PowerPoint"
    submission_method VARCHAR(100),                    -- "Electronic via email", "Hard copy"

    -- SOW linkage (denormalized)
    sow_section VARCHAR(100),                          -- "Task 3.4"

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deliverables_rfp ON deliverables(rfp_id);
CREATE INDEX idx_deliverables_id ON deliverables(deliverable_id);
CREATE INDEX idx_deliverables_due ON deliverables(due_date);
```

---

### Category 3: Agent Outputs (6 tables)

#### Table: `compliance_assessments`

**Purpose**: Store compliance checklist agent outputs  
**Usage**: Compliance tracking, gap analysis, proposal review

```sql
CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Assessment metadata
    assessment_version INT DEFAULT 1,                  -- Version for iterative refinement
    assessment_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assessed_by VARCHAR(100),                          -- User email or "agent"

    -- Overall assessment
    total_requirements INT NOT NULL,
    mandatory_requirements INT NOT NULL,
    compliant_count INT DEFAULT 0,
    partial_count INT DEFAULT 0,
    non_compliant_count INT DEFAULT 0,
    not_addressed_count INT DEFAULT 0,
    overall_status VARCHAR(50) NOT NULL,               -- COMPLIANT, ACCEPTABLE, MARGINAL, UNACCEPTABLE

    -- File reference
    output_file_path VARCHAR(500),                     -- Path to generated Excel file

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_assessment_version UNIQUE(rfp_id, assessment_version)
);

CREATE INDEX idx_assessments_rfp ON compliance_assessments(rfp_id);
CREATE INDEX idx_assessments_date ON compliance_assessments(assessment_date DESC);
```

---

#### Table: `compliance_items`

**Purpose**: Individual requirement compliance status  
**Usage**: Detailed compliance tracking, gap mitigation planning

```sql
CREATE TABLE compliance_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES compliance_assessments(id) ON DELETE CASCADE,
    requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,

    -- Compliance status
    compliance_status VARCHAR(50) NOT NULL,            -- COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT, NOT_ADDRESSED
    gap_description TEXT,
    mitigation_strategy TEXT,
    risk_level VARCHAR(20) NOT NULL,                   -- CRITICAL, HIGH, MEDIUM, LOW

    -- Proposal tracking
    proposal_section VARCHAR(100),                     -- "1.1 Technical Approach"
    page_reference VARCHAR(50),                        -- "15-18"

    -- Evidence
    evidence_text TEXT,                                -- Quote from proposal

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_compliance_item UNIQUE(assessment_id, requirement_id)
);

CREATE INDEX idx_compliance_items_assessment ON compliance_items(assessment_id);
CREATE INDEX idx_compliance_items_requirement ON compliance_items(requirement_id);
CREATE INDEX idx_compliance_items_status ON compliance_items(compliance_status);
CREATE INDEX idx_compliance_items_risk ON compliance_items(risk_level);
```

---

#### Table: `gap_analyses`

**Purpose**: Store gap analysis agent outputs  
**Usage**: Capability gap tracking, teaming decisions, risk assessment

```sql
CREATE TABLE gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Analysis metadata
    analysis_version INT DEFAULT 1,
    analysis_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analyzed_by VARCHAR(100),

    -- Overall gap summary
    total_gaps INT NOT NULL,
    critical_gaps INT DEFAULT 0,
    high_gaps INT DEFAULT 0,
    medium_gaps INT DEFAULT 0,
    low_gaps INT DEFAULT 0,
    overall_risk VARCHAR(20) NOT NULL,                 -- CRITICAL, HIGH, MEDIUM, LOW

    -- Teaming recommendation
    teaming_required BOOLEAN DEFAULT FALSE,
    recommended_partners TEXT[],

    -- File reference
    output_file_path VARCHAR(500),

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_gap_analysis_version UNIQUE(rfp_id, analysis_version)
);

CREATE INDEX idx_gap_analyses_rfp ON gap_analyses(rfp_id);
CREATE INDEX idx_gap_analyses_date ON gap_analyses(analysis_date DESC);
```

---

#### Table: `gap_items`

**Purpose**: Individual capability gaps with mitigation plans  
**Usage**: Detailed gap tracking, mitigation cost estimation

```sql
CREATE TABLE gap_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_analysis_id UUID NOT NULL REFERENCES gap_analyses(id) ON DELETE CASCADE,
    requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,

    -- Gap details
    gap_type VARCHAR(50) NOT NULL,                     -- CERTIFICATION, CLEARANCE, EXPERIENCE, CAPABILITY, FACILITY, EQUIPMENT
    severity VARCHAR(20) NOT NULL,                     -- CRITICAL, HIGH, MEDIUM, LOW

    -- Current vs. required
    current_capability TEXT,
    required_capability TEXT,

    -- Mitigation
    mitigation_options TEXT[],
    recommended_mitigation TEXT NOT NULL,
    cost_estimate VARCHAR(100),                        -- "$50K-$100K"
    timeline VARCHAR(100),                             -- "6-12 months"
    risk_to_win VARCHAR(20) NOT NULL,                  -- CRITICAL, HIGH, MEDIUM, LOW

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_gap_item UNIQUE(gap_analysis_id, requirement_id)
);

CREATE INDEX idx_gap_items_analysis ON gap_items(gap_analysis_id);
CREATE INDEX idx_gap_items_requirement ON gap_items(requirement_id);
CREATE INDEX idx_gap_items_type ON gap_items(gap_type);
CREATE INDEX idx_gap_items_severity ON gap_items(severity);
```

---

#### Table: `proposal_outlines`

**Purpose**: Store proposal outline agent outputs  
**Usage**: Proposal structure, page allocation, win theme placement

```sql
CREATE TABLE proposal_outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Outline metadata
    outline_version INT DEFAULT 1,
    outline_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    -- Page budget
    total_pages INT NOT NULL,
    volumes TEXT[],                                    -- ["Technical", "Management", "Past Performance"]
    page_budget_rationale TEXT,

    -- File reference
    output_file_path VARCHAR(500),                     -- Path to generated Word document

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_outline_version UNIQUE(rfp_id, outline_version)
);

CREATE INDEX idx_outlines_rfp ON proposal_outlines(rfp_id);
CREATE INDEX idx_outlines_date ON proposal_outlines(outline_date DESC);
```

---

#### Table: `proposal_sections`

**Purpose**: Individual sections in proposal outline  
**Usage**: Detailed section planning, requirement→section mapping

```sql
CREATE TABLE proposal_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outline_id UUID NOT NULL REFERENCES proposal_outlines(id) ON DELETE CASCADE,

    -- Section details
    section_number VARCHAR(50) NOT NULL,               -- "1.1", "2.3.1"
    section_title VARCHAR(500) NOT NULL,               -- "Technical Approach"
    page_allocation INT NOT NULL,

    -- Evaluation factor linkage
    evaluation_factor_id UUID REFERENCES evaluation_factors(id),
    factor_weight FLOAT,

    -- Requirements addressed
    requirement_ids UUID[],                            -- Array of requirement entity_ids
    requirement_count INT DEFAULT 0,

    -- Win themes
    win_themes TEXT[],
    key_discriminators TEXT[],
    pain_points_addressed TEXT[],
    action_captions TEXT[],

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_proposal_sections_outline ON proposal_sections(outline_id);
CREATE INDEX idx_proposal_sections_factor ON proposal_sections(evaluation_factor_id);
```

---

### Category 4: Cross-RFP Intelligence (2 tables)

#### Table: `cross_rfp_trends`

**Purpose**: Store trend analysis across multiple RFPs  
**Usage**: Competitive intelligence, clause frequency, factor weight trends

```sql
CREATE TABLE cross_rfp_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trend metadata
    trend_type VARCHAR(50) NOT NULL,                   -- "clause_frequency", "factor_weights", "requirement_types"
    agency VARCHAR(200),                               -- "Navy", "Air Force" (filter)
    date_range_start DATE,
    date_range_end DATE,

    -- Trend data (flexible JSON for different trend types)
    trend_data JSONB NOT NULL,
    /*
    Example for clause_frequency:
    {
      "FAR 52.212-1": {"count": 45, "percentage": 0.90},
      "DFARS 252.204-7012": {"count": 38, "percentage": 0.76},
      ...
    }

    Example for factor_weights:
    {
      "Technical Approach": {"avg_weight": 0.38, "min": 0.30, "max": 0.45, "count": 50},
      "Past Performance": {"avg_weight": 0.25, "min": 0.15, "max": 0.30, "count": 50},
      ...
    }
    */

    -- Analysis summary
    summary TEXT,                                      -- LLM-generated insights
    rfp_count INT NOT NULL,                            -- Number of RFPs analyzed

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trends_type ON cross_rfp_trends(trend_type);
CREATE INDEX idx_trends_agency ON cross_rfp_trends(agency);
CREATE INDEX idx_trends_date ON cross_rfp_trends(created_at DESC);
```

---

#### Table: `idiq_task_mappings`

**Purpose**: Map task orders to parent IDIQ contracts  
**Usage**: Hierarchical queries, incremental requirement detection, clause inheritance

```sql
CREATE TABLE idiq_task_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent-child relationship
    idiq_rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,
    task_order_rfp_id UUID NOT NULL REFERENCES rfp_documents(id) ON DELETE CASCADE,

    -- Mapping metadata
    task_order_number VARCHAR(50) NOT NULL,            -- "001", "002", etc.

    -- Delta analysis (what changed from IDIQ to task order)
    new_requirements_count INT DEFAULT 0,
    modified_requirements_count INT DEFAULT 0,
    inherited_clauses_count INT DEFAULT 0,
    new_clauses_count INT DEFAULT 0,

    -- Evaluation factor comparison
    factor_changes JSONB,
    /*
    Example:
    {
      "Technical Approach": {"idiq_weight": 0.40, "task_weight": 0.45, "delta": 0.05},
      "Past Performance": {"idiq_weight": 0.30, "task_weight": 0.25, "delta": -0.05}
    }
    */

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_task_mapping UNIQUE(idiq_rfp_id, task_order_rfp_id)
);

CREATE INDEX idx_idiq_mappings_parent ON idiq_task_mappings(idiq_rfp_id);
CREATE INDEX idx_idiq_mappings_child ON idiq_task_mappings(task_order_rfp_id);
```

---

## 🔧 PostgreSQL Extensions Setup

```sql
-- 1. pgvector for semantic embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Apache AGE for graph queries
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- 3. UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 4. Full-text search (built-in, no extension needed)
-- Already enabled via tsvector columns
```

---

## 📈 Example Queries (Agent Intelligence)

### Query 1: Compliance Checklist Data

```sql
-- Get all MANDATORY requirements for compliance assessment
SELECT
    r.requirement_id,
    r.description,
    r.criticality_level,
    r.modal_verb,
    r.section_origin,
    ARRAY_AGG(ef.factor_name) AS evaluation_factors,
    ARRAY_AGG(ef.factor_weight) AS factor_weights
FROM requirements r
LEFT JOIN LATERAL (
    SELECT DISTINCT e.entity_name AS factor_name,
           (e.metadata->>'factor_weight')::FLOAT AS factor_weight
    FROM entities e
    WHERE e.id = ANY(r.evaluation_factors)
) ef ON TRUE
WHERE r.rfp_id = '12345-uuid'
  AND r.criticality_level = 'MANDATORY'
GROUP BY r.id, r.requirement_id, r.description, r.criticality_level, r.modal_verb, r.section_origin
ORDER BY r.priority_score DESC;
```

---

### Query 2: Proposal Outline Page Allocation

```sql
-- Calculate page allocation by evaluation factor weight
WITH factor_summary AS (
    SELECT
        ef.factor_id,
        ef.factor_name,
        ef.factor_weight,
        ef.page_limits,
        COUNT(r.id) AS requirement_count
    FROM evaluation_factors ef
    LEFT JOIN requirements r ON ef.entity_id = ANY(r.evaluation_factors)
    WHERE ef.rfp_id = '12345-uuid'
    GROUP BY ef.id, ef.factor_id, ef.factor_name, ef.factor_weight, ef.page_limits
)
SELECT
    factor_id,
    factor_name,
    factor_weight,
    ROUND((factor_weight * 50)::NUMERIC, 0) AS recommended_pages,  -- Assuming 50 total pages
    page_limits AS section_l_limit,
    requirement_count
FROM factor_summary
ORDER BY factor_weight DESC NULLS LAST;
```

---

### Query 3: Gap Analysis - Missing Certifications

```sql
-- Find all certification requirements where company lacks capability
SELECT
    r.requirement_id,
    r.description,
    r.criticality_level,
    gi.gap_type,
    gi.severity,
    gi.current_capability,
    gi.required_capability,
    gi.recommended_mitigation,
    gi.cost_estimate,
    gi.timeline
FROM gap_items gi
JOIN requirements r ON gi.requirement_id = r.id
JOIN gap_analyses ga ON gi.gap_analysis_id = ga.id
WHERE ga.rfp_id = '12345-uuid'
  AND gi.gap_type = 'CERTIFICATION'
  AND gi.severity IN ('CRITICAL', 'HIGH')
ORDER BY
    CASE gi.severity
        WHEN 'CRITICAL' THEN 0
        WHEN 'HIGH' THEN 1
    END,
    r.priority_score DESC;
```

---

### Query 4: Cross-RFP Intelligence - Clause Frequency

```sql
-- Find most common FAR clauses across Navy RFPs
SELECT
    c.clause_number,
    c.clause_title,
    c.agency_supplement,
    COUNT(DISTINCT c.rfp_id) AS rfp_count,
    ROUND((COUNT(DISTINCT c.rfp_id)::FLOAT / (
        SELECT COUNT(DISTINCT id)
        FROM rfp_documents
        WHERE agency = 'Department of Navy'
    )) * 100, 1) AS percentage
FROM clauses c
JOIN rfp_documents rd ON c.rfp_id = rd.id
WHERE rd.agency = 'Department of Navy'
  AND rd.processing_status = 'completed'
GROUP BY c.clause_number, c.clause_title, c.agency_supplement
HAVING COUNT(DISTINCT c.rfp_id) >= 5  -- Appears in 5+ RFPs
ORDER BY rfp_count DESC
LIMIT 20;
```

---

### Query 5: IDIQ vs. Task Order Comparison

```sql
-- Compare evaluation factors between IDIQ base and task order
SELECT
    base_ef.factor_name,
    base_ef.factor_weight AS idiq_weight,
    task_ef.factor_weight AS task_weight,
    (task_ef.factor_weight - base_ef.factor_weight) AS weight_delta,
    CASE
        WHEN task_ef.factor_weight > base_ef.factor_weight THEN 'INCREASED'
        WHEN task_ef.factor_weight < base_ef.factor_weight THEN 'DECREASED'
        ELSE 'UNCHANGED'
    END AS trend
FROM evaluation_factors base_ef
JOIN idiq_task_mappings itm ON base_ef.rfp_id = itm.idiq_rfp_id
JOIN evaluation_factors task_ef ON task_ef.rfp_id = itm.task_order_rfp_id
    AND task_ef.factor_name = base_ef.factor_name
WHERE itm.idiq_rfp_id = 'idiq-uuid'
  AND itm.task_order_rfp_id = 'task-uuid'
ORDER BY ABS(task_ef.factor_weight - base_ef.factor_weight) DESC;
```

---

### Query 6: Semantic Search (pgvector)

```sql
-- Find similar requirements across RFPs using embedding similarity
SELECT
    r.rfp_id,
    rd.original_filename,
    r.requirement_id,
    r.description,
    1 - (e.embedding <=> (SELECT embedding FROM entities WHERE id = 'target-uuid')) AS similarity
FROM requirements r
JOIN entities e ON r.entity_id = e.id
JOIN rfp_documents rd ON r.rfp_id = rd.id
WHERE r.rfp_id != (SELECT rfp_id FROM entities WHERE id = 'target-uuid')  -- Exclude source RFP
  AND e.embedding <=> (SELECT embedding FROM entities WHERE id = 'target-uuid') < 0.3  -- Cosine distance threshold
ORDER BY similarity DESC
LIMIT 10;
```

---

## 🚀 Migration Strategy (From JSON to PostgreSQL)

### Phase 1: Database Setup (Week 1)

```sql
-- Run all CREATE TABLE statements
-- Configure extensions (pgvector, Apache AGE)
-- Set up indexes
-- Create database roles and permissions
```

### Phase 2: Data Migration Script (Week 2)

```python
# migrate_to_postgres.py
import networkx as nx
import psycopg2
import json
from pathlib import Path

def migrate_rfp_to_postgres(rfp_id: str):
    """Migrate single RFP from JSON files to PostgreSQL"""

    # 1. Load GraphML
    graphml_path = Path(f"./rag_storage/graph_chunk_entity_relation.graphml")
    G = nx.read_graphml(graphml_path)

    # 2. Load JSON KV stores
    with open("./rag_storage/kv_store_full_entities.json") as f:
        entities_kv = json.load(f)

    with open("./rag_storage/kv_store_full_relations.json") as f:
        relations_kv = json.load(f)

    # 3. Connect to PostgreSQL
    conn = psycopg2.connect("postgresql://user:pass@localhost:5432/govcon")
    cur = conn.cursor()

    # 4. Insert RFP document
    cur.execute("""
        INSERT INTO rfp_documents (id, original_filename, processing_status, graphml_data)
        VALUES (%s, %s, 'completed', %s)
        RETURNING id
    """, (rfp_id, "Navy_MBOS_RFP_2024.pdf", graphml_path.read_bytes()))

    # 5. Insert entities
    for node_id, data in G.nodes(data=True):
        cur.execute("""
            INSERT INTO entities (id, rfp_id, entity_name, entity_type, description, metadata)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
        """, (rfp_id, data['entity_name'], data['entity_type'], data['description'], json.dumps(data)))

    # 6. Insert relationships
    for source, target, data in G.edges(data=True):
        cur.execute("""
            INSERT INTO relationships (rfp_id, source_entity_id, target_entity_id, relationship_type)
            SELECT %s,
                   (SELECT id FROM entities WHERE entity_name = %s AND rfp_id = %s),
                   (SELECT id FROM entities WHERE entity_name = %s AND rfp_id = %s),
                   %s
        """, (rfp_id, source, rfp_id, target, rfp_id, data['relationship_type']))

    # 7. Populate denormalized tables (requirements, evaluation_factors, etc.)
    cur.execute("""
        INSERT INTO requirements (entity_id, rfp_id, requirement_id, description, criticality_level, priority_score, modal_verb, subject)
        SELECT
            e.id,
            e.rfp_id,
            e.entity_name,
            e.description,
            e.metadata->>'criticality_level',
            (e.metadata->>'priority_score')::INT,
            e.metadata->>'modal_verb',
            e.metadata->>'subject'
        FROM entities e
        WHERE e.entity_type = 'REQUIREMENT'
          AND e.rfp_id = %s
    """, (rfp_id,))

    conn.commit()
    cur.close()
    conn.close()
```

### Phase 3: Agent Integration (Week 3-4)

```python
# Update agents to query PostgreSQL instead of JSON files

# src/ingestion/graph_loader.py - BEFORE
def load_rfp_knowledge_graph(rfp_id: str) -> dict:
    graphml_path = Path(f"./rag_storage/graph_chunk_entity_relation.graphml")
    G = nx.read_graphml(graphml_path)
    # ... parse JSON files

# src/ingestion/graph_loader.py - AFTER
def load_rfp_knowledge_graph(rfp_id: str) -> dict:
    """Load RFP knowledge graph from PostgreSQL"""
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Load entities
    cur.execute("""
        SELECT id, entity_name, entity_type, description, metadata
        FROM entities
        WHERE rfp_id = %s
    """, (rfp_id,))
    entities = [dict(zip(['id', 'name', 'type', 'description', 'metadata'], row)) for row in cur.fetchall()]

    # Load relationships
    cur.execute("""
        SELECT source_entity_id, target_entity_id, relationship_type, confidence
        FROM relationships
        WHERE rfp_id = %s
    """, (rfp_id,))
    relationships = [dict(zip(['source', 'target', 'type', 'confidence'], row)) for row in cur.fetchall()]

    return {"rfp_id": rfp_id, "entities": entities, "relationships": relationships}
```

---

## 📊 Storage Estimates

**Per RFP** (Navy MBOS baseline):

- Entities: 594 × 2KB = 1.2 MB
- Relationships: 250 × 500 bytes = 125 KB
- Requirements: 80 × 1KB = 80 KB
- Evaluation factors: 5 × 1KB = 5 KB
- Compliance items: 50 × 500 bytes = 25 KB
- GraphML blob: 500 KB
- **Total per RFP**: ~2 MB

**100 RFPs**: 200 MB  
**1,000 RFPs**: 2 GB

**Cost** (AWS RDS PostgreSQL):

- db.t3.medium (2 vCPU, 4 GB RAM): $61/month
- 100 GB storage: $10/month
- **Total**: $71/month for 1,000 RFPs

---

## ✅ Summary

**What This Schema Enables**:

1. ✅ **Agent Intelligence Storage**: All 4 agents store outputs in dedicated tables
2. ✅ **Cross-RFP Queries**: SQL queries across 100+ RFPs in database
3. ✅ **IDIQ Hierarchies**: Parent-child relationships for task order tracking
4. ✅ **Amendment Tracking**: Change detection with impact analysis
5. ✅ **Semantic Search**: pgvector embeddings for similarity queries
6. ✅ **Graph Traversal**: Apache AGE for complex relationship queries
7. ✅ **Flexible Metadata**: JSONB columns for evolving agent outputs
8. ✅ **Audit Trail**: created_at/updated_at on all tables

**Next Steps**:

1. Review schema with your team
2. Set up PostgreSQL instance (local or AWS RDS)
3. Run CREATE TABLE scripts
4. Build migration script (JSON → PostgreSQL)
5. Update agents to query PostgreSQL
6. Test with Navy MBOS baseline RFP

---

**Last Updated**: October 19, 2025  
**Status**: Schema design complete, ready for implementation  
**Database**: PostgreSQL 16.6+ with pgvector + Apache AGE
