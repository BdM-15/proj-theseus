# Event Sourcing Architecture for Multi-Document Intelligence

**Document**: 02_EVENT_SOURCING_ARCHITECTURE.md  
**Purpose**: Advanced PostgreSQL design for immutable RFP → Amendment → Proposal → Feedback tracking  
**Branch**: Branch 011 (after Branch 010 simple schema)  
**Date**: October 20, 2025

---

## 🎯 Problem Statement

### The Core Challenge

**User Question**: "How do I process RFP, amendments, proposals, and feedback as isolated documents (each with unique ID) while still connecting them deeply for cross-document queries - without contaminating the baseline knowledge graph?"

### Why Current Schema Isn't Enough

The **Branch 010 simple schema** (17 tables) stores ONE snapshot per RFP:

```
rfp_documents table:
├── Row 1: Navy MBOS RFP (594 entities, 250 relationships)
├── Row 2: Air Force Cloud Migration (450 entities, 180 relationships)
└── Row 3: Army Cybersecurity (520 entities, 200 relationships)
```

**Problems**:
1. ❌ **Amendment contamination**: When Amendment 0001 changes a requirement, do you UPDATE the entity (lose history) or INSERT new entity (duplicates)?
2. ❌ **Proposal comparison**: How do you compare "what RFP required" vs. "what we proposed" if both are in same entities table?
3. ❌ **Feedback traceability**: "Lacks detail on cloud migration" (debrief) → which proposal section → which RFP requirement?
4. ❌ **Lessons learned**: Can't query "show me all requirements we missed across 10 proposals" because proposal content isn't in database.

---

## 💡 Solution: Event Sourcing + Entity Matching

### Conceptual Model (Git-Style Immutable Events)

Think of each document processing as a **Git commit**:

```
RFP_INITIAL (commit abc123)
├── 594 entities
├── 250 relationships
└── Immutable snapshot

AMENDMENT_0001 (commit def456, parent: abc123)
├── 620 entities (14 modified, 40 new)
├── 265 relationships
└── Immutable snapshot

PROPOSAL_SUBMISSION (commit ghi789, parent: def456)
├── 450 entities (proposal content)
├── 180 relationships
└── Immutable snapshot

EVALUATION_FEEDBACK (commit jkl012, parent: ghi789)
├── 85 entities (strengths, weaknesses)
├── 40 relationships
└── Immutable snapshot
```

**Key Insight**: Each event is **isolated** (no contamination), but **linked** via entity matching (deep connections).

---

## 🏗️ Schema Design (4 New Tables)

### Table 1: `document_events` (Event Log)

**Purpose**: Master event log - every document processing creates an event

```sql
CREATE TABLE document_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event metadata
    event_type VARCHAR(50) NOT NULL,              -- RFP_INITIAL, AMENDMENT, PROPOSAL_SUBMISSION, EVALUATION_FEEDBACK
    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Git-style lineage
    parent_event_id UUID REFERENCES document_events(id),  -- NULL for base RFP, links to parent for amendments/proposals
    root_rfp_id UUID,                             -- Always points to base RFP (for fast "show all events for this RFP" queries)
    
    -- Document metadata
    document_type VARCHAR(50),                    -- RFP, AMENDMENT, PROPOSAL_TECHNICAL, PROPOSAL_COST, DEBRIEF, EVALUATION_NOTICE
    original_filename VARCHAR(500),
    
    -- ISOLATED knowledge graph (immutable)
    graphml_data BYTEA NOT NULL,                  -- THIS EVENT's knowledge graph (compressed)
    graphml_checksum VARCHAR(64) NOT NULL,        -- SHA-256 hash for integrity verification
    
    -- Processing metadata
    entity_count INT,
    relationship_count INT,
    processing_time_seconds INT,
    processing_cost_usd NUMERIC(10,4),
    
    -- Event-specific metadata (flexible JSONB)
    event_metadata JSONB DEFAULT '{}',
    /*
    Example for AMENDMENT:
    {
      "amendment_number": "0001",
      "sections_affected": ["L", "M", "J-02"],
      "critical_changes": 5,
      "changes_summary": "Changed page limits and added new deliverable"
    }
    
    Example for PROPOSAL_SUBMISSION:
    {
      "volume": "Technical",
      "page_count": 45,
      "submission_date": "2024-12-15",
      "team_members": ["Company A (Prime)", "Company B (Sub)"]
    }
    
    Example for EVALUATION_FEEDBACK:
    {
      "feedback_type": "DEBRIEF",
      "overall_rating": "Good",
      "competitive_range": true,
      "award_status": "LOST",
      "winner": "Competitor X"
    }
    */
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),                      -- User email or "system"
    
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'RFP_INITIAL', 'AMENDMENT', 'PROPOSAL_SUBMISSION', 
        'EVALUATION_FEEDBACK', 'INTERCHANGE', 'DISCUSSION_NOTES',
        'PROTEST_RESPONSE', 'CONTRACT_AWARD'
    ))
);

-- Indexes
CREATE INDEX idx_events_type ON document_events(event_type);
CREATE INDEX idx_events_parent ON document_events(parent_event_id);
CREATE INDEX idx_events_root ON document_events(root_rfp_id);
CREATE INDEX idx_events_date ON document_events(event_date DESC);
CREATE INDEX idx_events_checksum ON document_events(graphml_checksum);
```

---

### Table 2: `entity_snapshots` (Per-Event Entities)

**Purpose**: Each event has its OWN entities - no sharing, no contamination

```sql
CREATE TABLE entity_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES document_events(id) ON DELETE CASCADE,
    
    -- Entity core (from THIS event's processing)
    entity_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    
    -- Source tracking
    source_event_type VARCHAR(50),                -- RFP_INITIAL, AMENDMENT, PROPOSAL_SUBMISSION, etc.
    page_reference VARCHAR(50),
    section_reference VARCHAR(100),
    
    -- Semantic search (pgvector)
    embedding vector(3072),                       -- OpenAI text-embedding-3-large
    
    -- Event-specific metadata (flexible JSONB)
    metadata JSONB NOT NULL DEFAULT '{}',
    /*
    Example for REQUIREMENT (from RFP):
    {
      "criticality_level": "MANDATORY",
      "priority_score": 100,
      "modal_verb": "shall"
    }
    
    Example for PROPOSED_SOLUTION (from Proposal):
    {
      "addresses_requirements": ["REQ_001", "REQ_042"],
      "win_theme": "Zero-downtime migration",
      "differentiator": "Unique phased approach"
    }
    
    Example for WEAKNESS (from Feedback):
    {
      "factor_affected": "Technical Approach",
      "severity": "MODERATE",
      "evaluator_comment": "Lacks detail on report format"
    }
    */
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_entity_per_event UNIQUE(event_id, entity_name),
    CONSTRAINT valid_entity_type CHECK (entity_type IN (
        'ORGANIZATION', 'CONCEPT', 'EVENT', 'TECHNOLOGY', 'PERSON', 'LOCATION',
        'REQUIREMENT', 'CLAUSE', 'SECTION', 'DOCUMENT', 'DELIVERABLE',
        'PROGRAM', 'EQUIPMENT', 'EVALUATION_FACTOR', 'SUBMISSION_INSTRUCTION',
        'STRATEGIC_THEME', 'STATEMENT_OF_WORK',
        -- Proposal-specific types
        'PROPOSED_SOLUTION', 'PAST_PERFORMANCE_REFERENCE', 'KEY_PERSONNEL',
        'SUBCONTRACTOR', 'TEAMING_PARTNER', 'WIN_THEME', 'DISCRIMINATOR',
        -- Feedback-specific types
        'STRENGTH', 'WEAKNESS', 'DEFICIENCY', 'SIGNIFICANT_WEAKNESS',
        'EVALUATOR_COMMENT', 'SCORING_RATIONALE'
    ))
);

-- Indexes
CREATE INDEX idx_entity_snapshots_event ON entity_snapshots(event_id);
CREATE INDEX idx_entity_snapshots_type ON entity_snapshots(entity_type);
CREATE INDEX idx_entity_snapshots_name ON entity_snapshots(entity_name);
CREATE INDEX idx_entity_snapshots_embedding ON entity_snapshots USING ivfflat (embedding vector_cosine_ops);

-- Full-text search
CREATE INDEX idx_entity_snapshots_description_fts ON entity_snapshots USING gin(to_tsvector('english', description));
```

---

### Table 3: `relationship_snapshots` (Per-Event Relationships)

**Purpose**: Each event has its OWN relationships

```sql
CREATE TABLE relationship_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES document_events(id) ON DELETE CASCADE,
    
    -- Relationship core
    source_entity_id UUID NOT NULL REFERENCES entity_snapshots(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entity_snapshots(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    
    -- Inference metadata
    confidence FLOAT,                              -- 0.0-1.0 (for LLM-inferred relationships)
    inference_method VARCHAR(50),                  -- "explicit", "semantic", "pattern", "llm"
    reasoning TEXT,                                -- Why this relationship was inferred
    
    -- Relationship-specific metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT no_self_reference CHECK (source_entity_id != target_entity_id),
    CONSTRAINT unique_relationship_per_event UNIQUE(event_id, source_entity_id, target_entity_id, relationship_type)
);

-- Indexes
CREATE INDEX idx_rel_snapshots_event ON relationship_snapshots(event_id);
CREATE INDEX idx_rel_snapshots_source ON relationship_snapshots(source_entity_id);
CREATE INDEX idx_rel_snapshots_target ON relationship_snapshots(target_entity_id);
CREATE INDEX idx_rel_snapshots_type ON relationship_snapshots(relationship_type);
```

---

### Table 4: `entity_matches` (Cross-Event Linking - The Magic!)

**Purpose**: Link entities across events without modifying source data

```sql
CREATE TABLE entity_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- The two entities being matched
    entity_1_id UUID NOT NULL REFERENCES entity_snapshots(id) ON DELETE CASCADE,
    entity_2_id UUID NOT NULL REFERENCES entity_snapshots(id) ON DELETE CASCADE,
    
    -- Match metadata
    match_type VARCHAR(50) NOT NULL,              -- EXACT, SEMANTIC, EVOLVED, REFERENCED, ADDRESSES, CRITICIZES
    match_confidence FLOAT NOT NULL,              -- 0.0-1.0 (semantic similarity or LLM confidence)
    match_reasoning TEXT,                         -- LLM-generated explanation
    
    -- Which events are being connected?
    event_1_id UUID NOT NULL REFERENCES document_events(id),
    event_2_id UUID NOT NULL REFERENCES document_events(id),
    
    -- Evolution tracking (what changed between events?)
    delta_description TEXT,                       -- "Amendment changed page limit from 25 to 30 pages"
    impact_level VARCHAR(20),                     -- CRITICAL, HIGH, MEDIUM, LOW, NONE
    
    -- Directional relationship (optional)
    relationship_direction VARCHAR(20),           -- FORWARD, BACKWARD, BIDIRECTIONAL
    /*
    Example:
    - FORWARD: RFP requirement → Proposal solution (proposal addresses requirement)
    - BACKWARD: Feedback weakness → Proposal section (feedback critiques proposal)
    - BIDIRECTIONAL: Amendment requirement → Original requirement (evolution)
    */
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    match_method VARCHAR(50),                     -- AUTOMATIC, MANUAL, AGENT
    validated_by VARCHAR(100),                    -- User who confirmed match (if manual)
    
    CONSTRAINT unique_match UNIQUE(entity_1_id, entity_2_id),
    CONSTRAINT no_self_match CHECK (entity_1_id != entity_2_id),
    CONSTRAINT different_events CHECK (event_1_id != event_2_id),
    CONSTRAINT valid_match_type CHECK (match_type IN (
        'EXACT',        -- Same entity, no changes
        'SEMANTIC',     -- Similar meaning, different wording
        'EVOLVED',      -- Modified version (amendment changed requirement)
        'REFERENCED',   -- Entity mentions another (proposal references RFP requirement)
        'ADDRESSES',    -- Entity responds to another (proposal solution addresses requirement)
        'CRITICIZES',   -- Entity critiques another (feedback weakness about proposal)
        'SUPERSEDES',   -- Entity replaces another (amendment supersedes original)
        'DUPLICATES'    -- Entity is duplicate of another (data quality issue)
    ))
);

-- Indexes
CREATE INDEX idx_matches_entity1 ON entity_matches(entity_1_id);
CREATE INDEX idx_matches_entity2 ON entity_matches(entity_2_id);
CREATE INDEX idx_matches_events ON entity_matches(event_1_id, event_2_id);
CREATE INDEX idx_matches_type ON entity_matches(match_type);
CREATE INDEX idx_matches_confidence ON entity_matches(match_confidence DESC);
CREATE INDEX idx_matches_impact ON entity_matches(impact_level);
```

---

## 🔄 Workflow Examples

### Example 1: Process Navy MBOS RFP (Base Event)

```sql
-- Step 1: Upload RFP → RAG-Anything processing → Phase 6 → Create Event 1
INSERT INTO document_events (
    event_type, document_type, original_filename,
    graphml_data, entity_count, relationship_count
) VALUES (
    'RFP_INITIAL',
    'RFP',
    'Navy_MBOS_RFP_2024.pdf',
    <graphml_blob>,
    594,
    250
) RETURNING id;  -- Returns: event-1-uuid

-- Step 2: Insert 594 entity snapshots
INSERT INTO entity_snapshots (event_id, entity_name, entity_type, description, embedding, metadata)
SELECT 
    'event-1-uuid',
    entity_name,
    entity_type,
    description,
    embedding,
    metadata
FROM parsed_graphml_entities;  -- From GraphML parsing

-- Step 3: Insert 250 relationship snapshots
INSERT INTO relationship_snapshots (event_id, source_entity_id, target_entity_id, relationship_type)
SELECT ...
FROM parsed_graphml_relationships;

-- Result: Isolated, immutable RFP knowledge graph
```

---

### Example 2: Process Amendment 0001 (Child Event)

```sql
-- Step 1: Upload Amendment → RAG-Anything processing → Phase 6 → Create Event 2
INSERT INTO document_events (
    event_type, parent_event_id, root_rfp_id,
    document_type, original_filename,
    graphml_data, entity_count, relationship_count,
    event_metadata
) VALUES (
    'AMENDMENT',
    'event-1-uuid',  -- Parent is base RFP
    'event-1-uuid',  -- Root is also base RFP
    'AMENDMENT',
    'Amendment_0001.pdf',
    <graphml_blob>,
    620,  -- 14 modified + 40 new entities
    265,
    '{"amendment_number": "0001", "sections_affected": ["L", "M"], "critical_changes": 5}'::jsonb
) RETURNING id;  -- Returns: event-2-uuid

-- Step 2: Insert 620 entity snapshots (includes original + modified + new)
INSERT INTO entity_snapshots (event_id, entity_name, entity_type, description, embedding, metadata)
SELECT ...;

-- Step 3: Run Entity Matching Agent to link event-1 → event-2
-- Agent finds:
-- - 580 EXACT matches (unchanged entities)
-- - 14 EVOLVED matches (modified requirements)
-- - 40 NEW entities (no match to event-1)

-- Example match:
INSERT INTO entity_matches (
    entity_1_id, entity_2_id,
    match_type, match_confidence,
    event_1_id, event_2_id,
    delta_description, impact_level
) VALUES (
    'req-001-event-1',  -- Original: "Contractor shall provide weekly reports"
    'req-001-event-2',  -- Amended: "Contractor shall provide daily reports"
    'EVOLVED',
    0.95,
    'event-1-uuid',
    'event-2-uuid',
    'Amendment changed reporting frequency from weekly to daily',
    'CRITICAL'
);
```

---

### Example 3: Process Proposal Submission (Grandchild Event)

```sql
-- Step 1: Upload Proposal → RAG-Anything processing → Create Event 3
INSERT INTO document_events (
    event_type, parent_event_id, root_rfp_id,
    document_type, original_filename,
    graphml_data, entity_count, relationship_count,
    event_metadata
) VALUES (
    'PROPOSAL_SUBMISSION',
    'event-2-uuid',  -- Parent is amended RFP
    'event-1-uuid',  -- Root is still base RFP
    'PROPOSAL_TECHNICAL',
    'Navy_MBOS_Technical_Proposal.docx',
    <graphml_blob>,
    450,
    180,
    '{"volume": "Technical", "page_count": 45, "submission_date": "2024-12-15"}'::jsonb
) RETURNING id;  -- Returns: event-3-uuid

-- Step 2: Insert 450 entity snapshots (proposal content)
-- Entity types: PROPOSED_SOLUTION, WIN_THEME, PAST_PERFORMANCE_REFERENCE, etc.

-- Step 3: Entity Matching Agent links event-2 (RFP) → event-3 (Proposal)
-- Example match:
INSERT INTO entity_matches (
    entity_1_id, entity_2_id,
    match_type, match_confidence,
    event_1_id, event_2_id,
    delta_description, impact_level,
    relationship_direction
) VALUES (
    'req-001-event-2',        -- RFP requirement (after amendment)
    'solution-5-event-3',     -- Proposal section 1.2.3 "Reporting Process"
    'ADDRESSES',
    0.88,
    'event-2-uuid',
    'event-3-uuid',
    'Proposal addresses requirement with automated dashboard approach',
    'HIGH',
    'FORWARD'
);
```

---

### Example 4: Process Evaluation Feedback (Great-grandchild Event)

```sql
-- Step 1: Upload Debrief → RAG-Anything processing → Create Event 4
INSERT INTO document_events (
    event_type, parent_event_id, root_rfp_id,
    document_type, original_filename,
    graphml_data, entity_count, relationship_count,
    event_metadata
) VALUES (
    'EVALUATION_FEEDBACK',
    'event-3-uuid',  -- Parent is proposal
    'event-1-uuid',  -- Root is still base RFP
    'DEBRIEF',
    'Navy_MBOS_Debrief_Notes.pdf',
    <graphml_blob>,
    85,
    40,
    '{"feedback_type": "DEBRIEF", "overall_rating": "Good", "competitive_range": true, "award_status": "LOST"}'::jsonb
) RETURNING id;  -- Returns: event-4-uuid

-- Step 2: Insert 85 entity snapshots (feedback content)
-- Entity types: STRENGTH, WEAKNESS, DEFICIENCY, EVALUATOR_COMMENT, etc.

-- Step 3: Entity Matching Agent links event-3 (Proposal) → event-4 (Feedback)
-- Example match:
INSERT INTO entity_matches (
    entity_1_id, entity_2_id,
    match_type, match_confidence,
    event_1_id, event_2_id,
    delta_description, impact_level,
    relationship_direction
) VALUES (
    'solution-5-event-3',     -- Proposal section
    'weakness-2-event-4',     -- "Lacks detail on report format"
    'CRITICIZES',
    0.92,
    'event-3-uuid',
    'event-4-uuid',
    'Evaluators noted missing CDRL format specification',
    'MEDIUM',
    'BACKWARD'  -- Feedback looks back at proposal
);
```

---

## 🔍 Powerful Cross-Event Queries

### Query 1: Trace Requirement Evolution (RFP → Amendment → Proposal → Feedback)

```sql
-- Find the complete lineage of REQUIREMENT_001
WITH RECURSIVE entity_lineage AS (
    -- Start with original RFP requirement
    SELECT 
        es.id AS entity_id,
        es.entity_name,
        es.description,
        de.event_type,
        de.event_date,
        de.event_metadata->>'amendment_number' AS amendment_number,
        1 AS depth,
        ARRAY[es.id] AS path
    FROM entity_snapshots es
    JOIN document_events de ON es.event_id = de.id
    WHERE es.entity_name = 'REQUIREMENT_001'
      AND de.event_type = 'RFP_INITIAL'
      AND de.root_rfp_id = 'navy-mbos-event-1'
    
    UNION ALL
    
    -- Recursively follow entity_matches to find evolution
    SELECT 
        es.id,
        es.entity_name,
        es.description,
        de.event_type,
        de.event_date,
        de.event_metadata->>'amendment_number',
        el.depth + 1,
        el.path || es.id
    FROM entity_lineage el
    JOIN entity_matches em ON el.entity_id IN (em.entity_1_id, em.entity_2_id)
    JOIN entity_snapshots es ON es.id = CASE 
        WHEN em.entity_1_id = el.entity_id THEN em.entity_2_id
        ELSE em.entity_1_id
    END
    JOIN document_events de ON es.event_id = de.id
    WHERE el.depth < 10  -- Prevent infinite loops
      AND es.id != ALL(el.path)  -- Prevent cycles
)
SELECT 
    entity_name,
    description,
    event_type,
    event_date,
    amendment_number,
    depth
FROM entity_lineage 
ORDER BY depth, event_date;
```

**Result**:
```
entity_name              | description                                    | event_type            | amendment | depth
-------------------------|------------------------------------------------|-----------------------|-----------|-------
REQUIREMENT_001          | Contractor shall provide weekly reports       | RFP_INITIAL           | NULL      | 1
REQUIREMENT_001_AMENDED  | Contractor shall provide daily reports        | AMENDMENT             | 0001      | 2
PROPOSED_SOLUTION_5      | We will provide real-time dashboard...        | PROPOSAL_SUBMISSION   | NULL      | 3
WEAKNESS_TECH_2          | Lacks detail on report format                 | EVALUATION_FEEDBACK   | NULL      | 4
```

---

### Query 2: Find All Missed Requirements (Gap Analysis)

```sql
-- Find RFP requirements NOT addressed in proposal
SELECT 
    es_rfp.entity_name AS requirement_id,
    es_rfp.description AS requirement_description,
    es_rfp.metadata->>'criticality_level' AS criticality,
    ef.entity_name AS evaluation_factor,
    ef.metadata->>'factor_weight' AS factor_weight,
    'NOT_ADDRESSED' AS coverage_status
FROM entity_snapshots es_rfp
JOIN document_events de_rfp ON es_rfp.event_id = de_rfp.id
-- Find linked evaluation factor
LEFT JOIN LATERAL (
    SELECT es.entity_name, es.metadata
    FROM relationship_snapshots rs
    JOIN entity_snapshots es ON rs.target_entity_id = es.id
    WHERE rs.source_entity_id = es_rfp.id
      AND rs.relationship_type = 'EVALUATED_BY'
      AND es.entity_type = 'EVALUATION_FACTOR'
) ef ON TRUE
-- Check if requirement is addressed in proposal
LEFT JOIN LATERAL (
    SELECT 1
    FROM entity_matches em
    JOIN entity_snapshots es_prop ON es_prop.id = em.entity_2_id
    JOIN document_events de_prop ON es_prop.event_id = de_prop.id
    WHERE em.entity_1_id = es_rfp.id
      AND em.match_type IN ('ADDRESSES', 'REFERENCED')
      AND de_prop.event_type = 'PROPOSAL_SUBMISSION'
      AND de_prop.root_rfp_id = de_rfp.id
) proposal_match ON TRUE
WHERE de_rfp.event_type IN ('RFP_INITIAL', 'AMENDMENT')
  AND de_rfp.root_rfp_id = 'navy-mbos-event-1'
  AND es_rfp.entity_type = 'REQUIREMENT'
  AND es_rfp.metadata->>'criticality_level' = 'MANDATORY'
  AND proposal_match IS NULL  -- NOT addressed in proposal
ORDER BY (ef.metadata->>'factor_weight')::FLOAT DESC NULLS LAST;
```

---

### Query 3: Lessons Learned - Recurring Feedback Patterns

```sql
-- Find weaknesses that appear across multiple proposals for same agency
WITH feedback_patterns AS (
    SELECT 
        es_feedback.entity_type,
        es_feedback.metadata->>'factor_affected' AS factor_affected,
        es_feedback.description AS weakness_description,
        de_rfp.event_metadata->>'agency' AS agency,
        COUNT(DISTINCT de_feedback.id) AS occurrence_count,
        STRING_AGG(DISTINCT de_rfp.original_filename, ' | ') AS rfp_list
    FROM entity_snapshots es_feedback
    JOIN document_events de_feedback ON es_feedback.event_id = de_feedback.id
    JOIN document_events de_rfp ON de_feedback.root_rfp_id = de_rfp.id
    WHERE de_feedback.event_type = 'EVALUATION_FEEDBACK'
      AND es_feedback.entity_type IN ('WEAKNESS', 'DEFICIENCY')
      AND de_rfp.event_metadata->>'agency' = 'Department of Navy'
      AND de_feedback.created_at > NOW() - INTERVAL '2 years'
    GROUP BY 
        es_feedback.entity_type,
        es_feedback.metadata->>'factor_affected',
        es_feedback.description,
        de_rfp.event_metadata->>'agency'
    HAVING COUNT(DISTINCT de_feedback.id) >= 3  -- Appears in 3+ proposals
)
SELECT * FROM feedback_patterns
ORDER BY occurrence_count DESC;
```

**Result**: Shows recurring weaknesses across Navy proposals (e.g., "Lacks past performance detail" appears 5 times).

---

## 🤖 Entity Matching Agent (Automatic Cross-Event Linking)

### Agent Architecture

```python
# src/agents/entity_matching_agent.py

from pydanticai import Agent
from pydantic import BaseModel
import psycopg2
from typing import List, Tuple

class EntityMatchResult(BaseModel):
    """Structured output for entity matching"""
    match_type: str  # EXACT, SEMANTIC, EVOLVED, ADDRESSES, CRITICIZES
    confidence: float  # 0.0-1.0
    delta_description: str
    impact_level: str  # CRITICAL, HIGH, MEDIUM, LOW, NONE
    reasoning: str

async def match_entities_between_events(
    event_1_id: str,
    event_2_id: str,
    similarity_threshold: float = 0.85
):
    """
    Agent: Automatically find entity matches between two document events
    
    Algorithm:
    1. Semantic similarity (pgvector) - Fast first pass
    2. LLM analysis (Grok) - Determine match type and delta
    3. Insert entity_matches records
    """
    
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    # Step 1: Load entities from both events
    cur.execute("""
        SELECT id, entity_name, entity_type, description, embedding, metadata
        FROM entity_snapshots
        WHERE event_id = %s
    """, (event_1_id,))
    entities_1 = cur.fetchall()
    
    cur.execute("""
        SELECT id, entity_name, entity_type, description, embedding, metadata
        FROM entity_snapshots
        WHERE event_id = %s
    """, (event_2_id,))
    entities_2 = cur.fetchall()
    
    # Step 2: Semantic similarity search (pgvector)
    matches_found = 0
    for e1_id, e1_name, e1_type, e1_desc, e1_emb, e1_meta in entities_1:
        
        # Find similar entities in event 2 using cosine similarity
        cur.execute("""
            SELECT 
                id, entity_name, entity_type, description, metadata,
                1 - (embedding <=> %s::vector) AS similarity
            FROM entity_snapshots
            WHERE event_id = %s
              AND entity_type = %s  -- Match same type
              AND 1 - (embedding <=> %s::vector) >= %s  -- Similarity threshold
            ORDER BY similarity DESC
            LIMIT 3  -- Top 3 candidates
        """, (e1_emb, event_2_id, e1_type, e1_emb, similarity_threshold))
        
        candidates = cur.fetchall()
        
        for e2_id, e2_name, e2_type, e2_desc, e2_meta, similarity in candidates:
            
            # Step 3: LLM determines match type and delta
            agent = Agent(
                model="openai:grok-beta",
                result_type=EntityMatchResult
            )
            
            result = await agent.run(f"""
            Compare these two entities and determine if they should be matched:
            
            Entity 1 (from {event_1_id}):
            - Name: {e1_name}
            - Type: {e1_type}
            - Description: {e1_desc}
            - Metadata: {e1_meta}
            
            Entity 2 (from {event_2_id}):
            - Name: {e2_name}
            - Type: {e2_type}
            - Description: {e2_desc}
            - Metadata: {e2_meta}
            
            Semantic similarity: {similarity:.2f}
            
            Determine:
            1. match_type: EXACT (unchanged), EVOLVED (modified), SEMANTIC (similar), ADDRESSES (responds to), CRITICIZES (critiques), or NO_MATCH
            2. confidence: 0.0-1.0 (adjust semantic similarity based on semantic analysis)
            3. delta_description: What changed between the two? (or how they relate)
            4. impact_level: CRITICAL, HIGH, MEDIUM, LOW, NONE
            5. reasoning: Why did you choose this match type?
            
            If NO_MATCH, set confidence to 0.0.
            """)
            
            match_result: EntityMatchResult = result.data
            
            # Step 4: Insert match if confidence > threshold
            if match_result.confidence >= 0.7 and match_result.match_type != "NO_MATCH":
                cur.execute("""
                    INSERT INTO entity_matches (
                        entity_1_id, entity_2_id,
                        match_type, match_confidence,
                        event_1_id, event_2_id,
                        delta_description, impact_level,
                        match_reasoning, match_method
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'AGENT')
                    ON CONFLICT (entity_1_id, entity_2_id) DO NOTHING
                """, (
                    e1_id, e2_id,
                    match_result.match_type, match_result.confidence,
                    event_1_id, event_2_id,
                    match_result.delta_description, match_result.impact_level,
                    match_result.reasoning
                ))
                matches_found += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return matches_found
```

### Agent Performance

**Navy MBOS Amendment Example**:
- Event 1 (RFP): 594 entities
- Event 2 (Amendment): 620 entities
- Combinations: 594 × 620 = 368,280 possible matches

**Optimizations**:
1. **Type filtering**: Only compare same entity types (REQUIREMENT → REQUIREMENT) → Reduces to ~80 × 80 = 6,400
2. **Semantic similarity threshold**: Only analyze entities with similarity ≥ 0.85 → Reduces to ~200 candidates
3. **LLM batch processing**: Analyze 10 entity pairs per prompt → 20 LLM calls

**Cost**: ~$0.05 per event pair (20 calls × $2.50/M tokens × 1,000 tokens/call)  
**Time**: ~30 seconds per event pair

---

## 📊 Storage Estimates

### Per RFP (4-Event Chain)

| Event | Entities | Relationships | Matches | GraphML Blob | Total Size |
|-------|----------|---------------|---------|--------------|------------|
| RFP_INITIAL | 594 | 250 | 0 | 500 KB | 1.5 MB |
| AMENDMENT_0001 | 620 | 265 | 594 | 520 KB | 2.0 MB |
| PROPOSAL_SUBMISSION | 450 | 180 | 320 | 400 KB | 1.8 MB |
| EVALUATION_FEEDBACK | 85 | 40 | 50 | 100 KB | 0.5 MB |
| **Total** | **1,749** | **735** | **964** | **1.52 MB** | **5.8 MB** |

**100 RFPs with 4-event chains**: 580 MB  
**1,000 RFPs with 4-event chains**: 5.8 GB

**PostgreSQL 18 Performance**: Handles 10+ GB databases on db.t3.medium (4 GB RAM) with no performance degradation.

---

## ✅ Success Criteria (Branch 011)

### Functional Requirements
- ✅ Process amendments without modifying original RFP entities
- ✅ Link proposal sections to RFP requirements via entity matching
- ✅ Trace requirement evolution through 4+ event chain
- ✅ Query "show all missed requirements across 10 proposals"
- ✅ Agent achieves ≥90% entity matching accuracy

### Performance Requirements
- ✅ Entity matching completes in ≤60 seconds per event pair
- ✅ Cross-event recursive query completes in ≤2 seconds
- ✅ Amendment processing creates new event (not update) in ≤90 seconds

### Data Integrity Requirements
- ✅ Original event data never modified after creation
- ✅ GraphML checksums verify integrity
- ✅ Entity matches can be deleted/recreated without data loss

---

## 🚀 Implementation Roadmap

### Week 6: Event Sourcing Tables
- Create 4 new tables (document_events, entity_snapshots, relationship_snapshots, entity_matches)
- Migrate existing rfp_documents → document_events (convert to event-based model)

### Week 7: Entity Matching Agent
- Build PydanticAI agent for semantic similarity + LLM analysis
- Test on Navy MBOS RFP + Amendment 0001
- Tune similarity thresholds for ≥90% accuracy

### Week 8: Amendment Processing
- Add /process_amendment endpoint to app.py
- Create event-2 from amendment upload
- Run entity matching automatically

### Week 9: Proposal Processing
- Add /process_proposal endpoint
- Create event-3 from proposal upload
- Match proposal sections to RFP requirements

### Week 10: Feedback Processing
- Add /process_feedback endpoint
- Create event-4 from debrief/evaluation notice
- Match feedback weaknesses to proposal sections

### Week 11: Cross-Event Queries
- Build recursive SQL queries for lineage tracing
- Create lessons learned dashboard
- Test with 5-10 real RFP chains

### Week 12: Production Deployment
- AWS RDS migration
- Performance optimization
- User acceptance testing

---

## 🔗 Related Documentation

- `README.md` - Master plan and navigation
- `01_SCHEMA_DESIGN.md` - Branch 010 simple schema (17 tables)
- `TASK_06_EVENT_TABLES.md` - Implementation guide for event-sourcing tables
- `TASK_07_MATCHING_AGENT.md` - Entity matching agent implementation
- `docs/AMENDMENT_HANDLING_ROADMAP.md` - Amendment processing workflows

---

**Last Updated**: October 20, 2025  
**Status**: Architecture design complete, ready for Branch 011 implementation  
**Next**: Create TASK_06-10 implementation guides
