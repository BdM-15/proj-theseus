# Evaluation Factor Extraction Patterns

**Purpose**: Extract evaluation factors with agency-specific intelligence and scoring methodology patterns  
**Philosophy**: Recognize evaluation factor semantics regardless of naming variations  
**Usage**: Loaded during RAG-Anything extraction to enrich evaluation_factor entities  
**Last Updated**: January 26, 2025 (Branch 011 - Option A Lean Extraction)

---

## Extraction Philosophy

When extracting evaluation factors, **recognize patterns semantically** rather than matching exact strings:

```
❌ BASIC: entity|Factor 1: Technical Approach|evaluation_factor|Technical approach evaluation

✅ ENHANCED: entity|Factor 1: Technical Approach|evaluation_factor|Technical Approach (DoD pattern: typically 30-50% weight in Three-Factor Trinity structure). Likely evaluates: solution architecture, innovation, risk mitigation, compliance with technical requirements. Recognize variants: "Solution Design", "Methodology", "Project Approach", "Technical Solution" (same semantic meaning).
```

**Key Pattern**: LLM should recognize evaluation intent (WHAT is being scored) regardless of specific naming

---

## Section 1: Common Evaluation Patterns (Pattern Recognition, Not Rules)

> **CRITICAL**: These patterns represent COMMON observations from federal RFPs, NOT universal requirements. RFPs vary widely. Use LLM semantic understanding to recognize evaluation INTENT.

### Pattern 1: Three-Factor Trinity (Observed in ~80% of RFPs)

**When you see this pattern**, enrich entity extraction:

**Factor indicators**:

- "Technical Approach" OR "Solution Design" OR "Methodology" OR "Project Approach" OR "Technical Solution"
  → Recognize as: Technical capability evaluation (HOW work will be done)
  → Typical weight: 30-50%
  → Common sub-factors: Architecture, innovation, risk mitigation, compliance

- "Management Approach" OR "Program Management" OR "Team Organization" OR "Management Plan" OR "Project Controls"
  → Recognize as: Management capability evaluation (HOW work will be managed)
  → Typical weight: 20-35%
  → Common sub-factors: Staffing, quality assurance, schedule, subcontractor oversight

- "Past Performance" OR "Relevant Experience" OR "Corporate Experience" OR "Contract History" OR "References"
  → Recognize as: Track record evaluation (PROOF of capability)
  → Typical weight: 20-40%
  → Common criteria: Relevance, recency, quality (CPARS ratings)

**Relationship triggers**:

- Create `CHILD_OF` relationships for sub-factors to parent factors
- Create `EVALUATED_BY` relationships from requirements to relevant factors

**Semantic variance handling**:
If RFP uses "Solution Effectiveness" + "Team Qualifications" + "Prior Work Quality":

- Recognize: Solution Effectiveness = Technical (different naming, same semantic meaning)
- Recognize: Team Qualifications = Management/Personnel
- Recognize: Prior Work Quality = Past Performance
- Extract with semantic notes in description

---

### Pattern 2: Adjectival vs Numerical Scoring (Recognize from RFP Language)

**Adjectival Scoring** (Common in DoD RFPs):

**Detection signals**:

- Keywords: "Outstanding", "Good", "Acceptable", "Marginal", "Unacceptable"
- Keywords: "Excellent", "Very Good", "Satisfactory", "Unsatisfactory"
- Phrase patterns: "adjectival ratings", "color ratings", "performance confidence assessment"

**Entity enrichment**:

```
entity|Factor 1: Technical Approach|evaluation_factor|Technical Approach evaluated using adjectival scoring (Outstanding/Good/Acceptable/Marginal/Unacceptable). DoD pattern: Outstanding = exceeds requirements with minimal risk and significant strengths. Recognize as Best Value Tradeoff methodology.
```

**Relationship triggers**:

- Link to Section M-specific scoring methodology descriptions
- Extract scoring definitions as separate CONCEPT entities if detailed

**Numerical Scoring** (Common in civilian RFPs):

**Detection signals**:

- Keywords: "points", "100-point scale", "weighted scoring", "0-5 rating"
- Phrase patterns: "maximum points available", "technical merit score", "point allocation"

**Entity enrichment**:

```
entity|Factor 2: Management Approach|evaluation_factor|Management Approach evaluated on 100-point numerical scale (40 points maximum, 40% of technical evaluation). Civilian agency pattern: Numerical scoring allows precise tradeoff analysis.
```

---

### Pattern 3: Price/Cost Evaluation Methodology

**Best Value Tradeoff** (Most common):

**Detection signals**:

- "best value to the Government"
- "tradeoff between technical merit and cost"
- "technical superiority may justify higher cost"

**Entity enrichment**: Extract price evaluation approach as CONCEPT entity, create EVALUATED_BY relationship to price/cost factors

**LPTA (Lowest Price Technically Acceptable)**:

**Detection signals**:

- "lowest price technically acceptable"
- "technical proposal is pass/fail"
- "award to lowest-priced acceptable offeror"

**Entity enrichment**: Note LPTA means technical is gate, not scored → focus extraction on pass/fail criteria rather than relative excellence

**Two-Step Evaluation**:

**Detection signals**:

- "Step 1: Technical qualification"
- "Step 2: Price competition among qualified offerors"
- "down-select to competitive range"

**Entity enrichment**: Extract two-step process as sequence of EVENT entities with temporal relationships

---

## Section 2: Agency-Specific Evaluation Tendencies

> **REMEMBER**: These are TENDENCIES based on historical observation, NOT deterministic rules. Always prioritize what the specific RFP states.

### DoD Evaluation Patterns

**When RFP indicates DoD agency** (Navy, Air Force, Army, USMC, DLA, etc.):

**Scoring tendency**: Tends toward adjectival ratings (Outstanding/Good/Acceptable)

**Past performance emphasis**: Higher weight (often 30-40%, sometimes equal to technical)

**CPARS scrutiny**: Extract CPARS ratings as critical past performance element

- "Exceptional", "Very Good", "Satisfactory", "Marginal", "Unsatisfactory"
- Anything below "Very Good" = competitive disadvantage

**Security clearance criticality**:

- Extract clearance requirements (SECRET, TS, SCI) as REQUIREMENT entities
- "Will obtain" clearances often unacceptable for critical positions
- Create relationships: Clearance Requirement --EVALUATED_BY--> Personnel Qualifications factor

**Frequently observed unstated factors**:

- Transition risk (if successor contract) → Extract transition language as strategic_theme
- Small business utilization (even on unrestricted) → Extract SB plan as deliverable
- Mission understanding → Look for "why this work matters" language in SOW

**Entity enrichment pattern**:

```
entity|Factor 3: Past Performance|evaluation_factor|Past Performance (DoD emphasis: typically 30-40% weight, equal or higher than civilian patterns). CPARS ratings heavily scrutinized - anything below "Very Good" is competitive disadvantage. Evaluates relevance (similar scope/customer), recency (within 3-5 years), quality (CPARS/customer references).
```

---

### Civilian Agency Evaluation Patterns

**When RFP indicates civilian agency** (HHS, DHS, GSA, VA, EPA, etc.):

**Scoring tendency**: More commonly uses numerical/point-based scoring (0-100 scales)

**Management emphasis**: Higher weight on management approach (often 35-45% vs 20-30% for DoD)

**Personnel qualifications**: Specific degrees, certifications, licenses emphasized

- Extract required credentials as REQUIREMENT entities with criticality: MANDATORY
- Create relationships: Credential Requirement --EVALUATED_BY--> Key Personnel factor

**Cost consciousness**: Budget control and efficiency frequently mentioned

- Extract cost savings language as strategic_theme
- Look for "taxpayer stewardship" or "value for taxpayer dollar" phrases

**Diversity & inclusion**: Section 508 compliance, EEO policies may be evaluation subfactors

- Extract accessibility requirements as REQUIREMENT entities
- Create relationships to evaluation factors mentioning "accessibility" or "Section 508"

**Entity enrichment pattern**:

```
entity|Factor 2: Management Approach|evaluation_factor|Management Approach (Civilian emphasis: typically 35-45% weight, higher than DoD 20-30%). Likely uses numerical scoring (0-100 points). Common subfactors: staffing plan, quality assurance, cost control, diversity initiatives, Section 508 compliance. Evaluates project management capability and budget consciousness.
```

---

## Section 3: Subfactor Extraction Patterns

**When extracting evaluation subfactors**, recognize hierarchical structure:

### Technical Subfactor Patterns

**Common subfactors** (names vary, recognize semantically):

- Architecture/Design → "How system will be structured"
- Approach/Methodology → "How work will be executed"
- Innovation → "Novel solutions or process improvements"
- Risk Mitigation → "How risks will be managed"
- Compliance → "How requirements will be met"

**Extraction pattern**:

```
entity|Factor 1.1: Technical Architecture|evaluation_factor|Technical Architecture (subfactor of Factor 1: Technical Approach). Evaluates system design, technology stack, scalability, integration with existing systems. Weight: typically 30-40% of parent technical factor.

relationship|Factor 1.1: Technical Architecture|CHILD_OF|Factor 1: Technical Approach|hierarchy|Subfactor evaluation under parent technical factor
```

### Management Subfactor Patterns

**Common subfactors**:

- Staffing Plan → "Team size, roles, qualifications"
- Quality Assurance → "QA/QC processes, metrics, audits"
- Schedule Management → "Timeline, milestones, critical path"
- Subcontractor Management → "Prime-sub relationships, oversight"
- Transition Plan → "Startup, knowledge transfer, minimal disruption"

**Extraction pattern with relationship**:

```
entity|Factor 2.2: Quality Assurance Approach|evaluation_factor|Quality Assurance Approach (subfactor of Factor 2: Management). Evaluates QA/QC processes, defect tracking, quality metrics, corrective action procedures. Likely links to ISO 9001 or similar quality standards.

relationship|ISO 9001 Certification|SUPPORTS|Factor 2.2: Quality Assurance Approach|evidence|Quality certification demonstrates structured QA capability
```

### Past Performance Criteria Patterns

**Common criteria** (typical patterns, specific criteria vary):

- Relevance → "Similar scope, size, complexity, customer type"
- Recency → "Work within last 3-5 years" (timeframe varies: some 2 years, some 7 years)
- Quality → "CPARS ratings, customer references, contract completion"

**Semantic variance**:

- "Comparable contracts" = Relevance
- "Recent experience" = Recency
- "Performance quality" = Quality
- "Reference checks" = Quality assessment method

**Extraction pattern**:

```
entity|Past Performance Relevance Assessment|evaluation_factor|Past Performance Relevance (subfactor of Past Performance factor). Evaluates similarity to current requirement: similar scope, customer type, contract size, technical complexity. Common pattern: "Very Relevant" contracts (same agency, same work) score higher than "Somewhat Relevant" (related work, different customer).

relationship|Navy IT Support Contracts|DEMONSTRATES_RELEVANCE_FOR|Past Performance Relevance Assessment|evidence|Similar customer type and technical scope supports relevance scoring
```

---

## Section 4: Evaluation Factor Relationship Patterns

### Section L ↔ Section M Linkage (GUIDES Relationships)

**Pattern**: Submission instructions (Section L) guide how to respond to evaluation factors (Section M)

**Detection signals**:

- "Technical Volume addresses Factor 1"
- "Management proposal responds to Factors 2-3"
- "Volume I shall address evaluation criteria M1-M3"

**Extraction pattern**:

```
relationship|Technical Volume Format (25 pages, 12pt font)|GUIDES|Factor 1: Technical Approach|submission_instruction|Page limits and format requirements for technical factor response

relationship|Section L.3.2 Management Proposal|GUIDES|Factor 2: Management Approach|cross_reference|Explicit linkage between submission instruction and evaluation criteria
```

**Implicit co-location pattern**:

- If page limit appears in same paragraph as factor description, create GUIDES relationship
- Confidence: 0.80 (lower than explicit cross-reference but strong signal)

---

### Requirement ↔ Evaluation Factor Linkage (EVALUATED_BY Relationships)

**Pattern**: Requirements in SOW/PWS are scored under specific evaluation factors

**Detection signals**:

- Topic alignment: "help desk support" requirement → "Technical Approach - Help Desk Operations" factor
- Criticality mapping: MANDATORY requirements → high-weight factors
- Content proximity: Requirement discussed near factor in RFP text

**Extraction pattern**:

```
relationship|Weekly Status Reports|EVALUATED_BY|Factor 2: Management Approach|topic_alignment|Management reporting requirement scored under management factor

relationship|24/7 Help Desk Support|EVALUATED_BY|Factor 1: Technical Approach|criticality_mapping|MANDATORY technical requirement scored under technical capability factor
```

**Confidence scoring**:

- Explicit reference: 0.95 ("this requirement will be evaluated under Factor X")
- Topic alignment: 0.80 (semantic match between requirement and factor scope)
- Criticality mapping: 0.75 (MANDATORY requirement → high-weight factor)
- Content proximity: 0.70 (requirement and factor appear in adjacent sections)

---

## Section 5: Evaluation Methodology Recognition

### Source Selection Process Extraction

**Extract as EVENT entities** when RFP describes evaluation timeline:

**Pattern examples**:

- "Phase 1: Initial evaluation" (30 days after proposal due)
- "Phase 2: Discussions/Clarifications" (if needed)
- "Phase 3: Final Proposal Revisions" (if competitive range)
- "Phase 4: Award Decision" (within 90 days of proposal due)

**Relationship pattern**:

```
relationship|Phase 1: Initial Evaluation|PRECEDES|Phase 2: Discussions|sequence|Evaluation process temporal ordering

relationship|Competitive Range Determination|AFFECTS|Factor Scores|decision_point|Only offerors in competitive range proceed to Phase 3
```

---

### Oral Presentation Extraction

**When RFP includes oral presentations**, extract as EVENT with special handling:

**Pattern**:

```
entity|Technical Oral Presentation|event|30-minute oral presentation to evaluation panel (60 minutes total: 30-minute presentation + 30-minute Q&A). No slides allowed, whiteboard only. Evaluates Factor 1: Technical Approach. Oral presentation may adjust initial written proposal score up or down.

relationship|Technical Oral Presentation|EVALUATES|Factor 1: Technical Approach|assessment_method|Oral presentation provides additional evidence for technical scoring

relationship|Technical Written Proposal|PREREQUISITE_FOR|Technical Oral Presentation|sequence|Written proposal score determines invitation to oral presentation
```

---

## Extraction Guidelines Summary

### Entity Type Selection

**Primary type**: `evaluation_factor` (for all factors, subfactors, and criteria)

**Related entities to extract**:

- Scoring methodology → `concept` ("Adjectival Scoring Methodology", "Best Value Tradeoff")
- Evaluation events → `event` (oral presentations, site visits, competitive range determination)
- Page limits for proposals → `submission_instruction` (with GUIDES relationships to factors)

### Description Enrichment Formula

**Template**: `[Factor Name] ([Agency Pattern]: [Weight/Importance]). [Scoring Methodology]. [Common Subfactors]. [What Gets Evaluated]. [Semantic Variants Recognition].`

**Example**:

```
entity|Factor 1: Technical Solution|evaluation_factor|Technical Solution (DoD pattern: typically 30-50% weight in three-factor structure). Evaluated using adjectival ratings (Outstanding/Good/Acceptable). Common subfactors: solution architecture, risk mitigation, innovation, compliance. Evaluates HOW contractor will execute technical work. Recognize variants: "Technical Approach", "Methodology", "Solution Design", "Project Approach" (same semantic meaning).
```

### Relationship Prioritization

**High-priority relationships to create**:

1. `CHILD_OF` - Subfactor to parent factor hierarchy
2. `GUIDES` - Section L instructions to Section M factors
3. `EVALUATED_BY` - SOW requirements to evaluation factors
4. `SUPPORTS` - Past performance examples to relevance criteria
5. `PRECEDES` - Evaluation phase sequencing

---

**Version**: 1.0 (Option A - Lean Extraction)  
**Lines**: ~450 (vs 477 in original library)  
**Focus**: Pattern recognition for evaluation factors, agency tendencies, scoring methodologies  
**Integration**: Load alongside FAR/DFARS patterns and entity_detection_rules
