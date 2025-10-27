# Execution Framework: Discrete Task Steps

**Version**: 2.0 (Branch 011 - Execution Framework Architecture)  
**Last Updated**: January 27, 2025  
**Purpose**: Define HOW to execute extraction with discrete, ordered steps to build **decision-ready intelligence**

---

## Overview: Five-Step Extraction Process

You will process each RFP chunk through **five discrete steps** in this exact order, with each step building toward the ultimate goal: **quality intelligence for informed decision making**.

```
STEP 1: Scan & Detect    → Identify decision-critical entity candidates
STEP 2: Classify         → Assign entity type (17 types) with precision
STEP 3: Enrich          → Add operational context that enables decisions
STEP 4: Relate          → Map decision pathways between entities
STEP 5: Output          → Validate decision-making value and format
```

**Each step builds on the previous** - do not skip or reorder steps.

**Why this matters**: Speed and scale advantages only create competitive edge when extraction quality enables informed decisions. Generic entities → generic insights → uninformed decisions. Decision-ready entities → strategic insights → informed decisions.

---

## STEP 1: Scan & Detect Entity Candidates

### Goal

Identify ALL **decision-critical** entities in the chunk using **semantic signals** (not just keyword matching).

**Decision-making value**: Missing an entity = missing information = uninformed decision. Comprehensive detection ensures complete intelligence coverage.

### Detection Patterns

**Look for**:

- **Noun phrases with domain significance**: "Cost reimbursement pricing", "System Security Plan", "Past Performance evaluation"
- **Defined terms**: "MCPP II", "NIST 800-171", "FAR 52.212-1", "Factor 1: Technical Approach"
- **Temporal markers**: "within 30 days", "NLT 1 October 2025", "Q&A period closes"
- **Obligation markers**: "shall", "must", "is required to", "should", "may"
- **Evaluation language**: "will be evaluated", "scoring criteria", "adjectival ratings", "point-based"
- **Structural references**: "Section C", "Attachment J-0005", "Volume II", "CLIN 0001"

### Candidate Recording

**For each candidate**, note:

- Exact text (as it appears)
- Semantic signal that triggered detection (e.g., "obligation marker 'shall'", "evaluation language 'will be scored'")
- Surrounding context (2-3 sentences before/after)

**Example candidates from chunk**:

```
Candidate 1: "FAR 52.204-21 NIST 800-171 Compliance"
Signal: Regulatory reference pattern + defined term
Context: "Contractor shall implement FAR 52.204-21 NIST 800-171 security controls for all CUI systems."

Candidate 2: "Factor 1: Technical Approach"
Signal: Evaluation language + structured naming pattern
Context: "Proposals will be evaluated based on Factor 1: Technical Approach (40% weight)..."

Candidate 3: "Weekly Status Reports"
Signal: Deliverable pattern (periodic + report type)
Context: "Contractor shall submit weekly status reports to COR NLT COB Friday."
```

---

## STEP 2: Classify Entity Type

### Goal

Assign each candidate to ONE of 17 entity types using semantic meaning (not location).

**Decision-making value**: Correct classification determines which domain knowledge to apply and which relationships to infer. Misclassification of an evaluation factor as a requirement = wrong proposal strategy. Precision here enables accurate downstream intelligence.

### The 17 Entity Types (with Semantic Definitions)

**Core Entities** (generic, useful for baseline connectivity):

1. **organization**: Companies, agencies, departments, teams, prime/sub contractors
2. **concept**: Abstract ideas, methodologies, frameworks, budget concepts, CLINs
3. **event**: Milestones, deadlines, reviews, site visits, orals, phase gates
4. **technology**: Systems, platforms, software, hardware, tools
5. **person**: POCs, CORs, contracting officers, key personnel
6. **location**: Performance sites, delivery locations, geographic areas

**Contracting Entities** (government-specific operational content): 7. **requirement**: Obligations with criticality levels (MANDATORY/SHOULD/MAY)

- Semantic signals: "shall", "must", "is required to", "should", "may", "optionally"

8. **clause**: FAR/DFARS/agency supplement regulatory clauses
   - Semantic signals: "FAR 52.xxx", "DFARS 252.xxx", "NMCARS 5252.xxx", regulatory reference patterns
9. **section**: RFP structural sections (UCF A-M or semantic equivalent)
   - Semantic signals: "Section [letter/number]", "Part", "Volume", "Attachment", "Annex"
10. **document**: Referenced external documents (specs, standards, manuals, regulations)
    - Semantic signals: "MIL-STD-", "ISO ", "NIST ", "in accordance with [doc name]"
11. **deliverable**: Contract work products, reports, CDRLs
    - Semantic signals: "shall deliver", "shall provide", "submit [report/plan/product]"

**Evaluation Entities** (scoring and submission): 12. **evaluation_factor**: Scoring criteria, weights, subfactors - Semantic signals: "will be evaluated", "Factor [X]", "criterion", "scoring", "weight", "%"

13. **submission_instruction**: Format, page limits, proposal structure requirements
    - Semantic signals: "shall submit", "page limit", "font size", "format", "organize as follows"

**Strategic Entities** (capture intelligence): 14. **strategic_theme**: Win themes, mission priorities, discriminators, customer hot buttons - Semantic signals: "mission", "priority", "critical to", "maximize", "emphasis on"

**Work Scope** (semantic detection regardless of location): 15. **statement_of_work**: PWS/SOW/SOO narrative content describing work to be performed - Semantic signals: Work descriptions, "contractor shall perform", scope narratives

**Programs & Equipment**: 16. **program**: Named major programs, initiatives, systems-of-systems - Semantic signals: "MCPP II", "Navy MBOS", proper nouns for programs

17. **equipment**: Physical items, materials, tools, vehicles, assets
    - Semantic signals: Concrete physical objects, quantities, NSNs

### Disambiguation Rules

**When multiple types could apply**, use these tiebreakers:

**CLAUSE vs REQUIREMENT**:

- If text matches FAR/DFARS/agency pattern → **clause**
- If text describes obligation but no regulatory reference → **requirement**

**EVALUATION_FACTOR vs SUBMISSION_INSTRUCTION**:

- If describes WHAT is scored (criteria, methodology) → **evaluation_factor**
- If describes HOW to submit (format, limits) → **submission_instruction**
- If BOTH in same sentence → create TWO entities

**CONCEPT vs PROGRAM**:

- If proper noun for named program (MCPP II, NGEN) → **program**
- If abstract methodology (Agile, DevSecOps) → **concept**

**DELIVERABLE vs REQUIREMENT**:

- If tangible work product (report, plan, software) → **deliverable**
- If ongoing obligation (shall maintain, shall comply) → **requirement**

**DOCUMENT vs SECTION**:

- If external reference (MIL-STD-882, NIST 800-171) → **document**
- If internal RFP structure (Section C, Attachment J) → **section**

### Classification Output

**For each candidate**, record:

```
Entity: [exact text]
Type: [one of 17 types]
Confidence: [high/medium/low]
Disambiguation notes: [if applicable]
```

**Example**:

```
Entity: "FAR 52.204-21 NIST 800-171 Compliance"
Type: clause
Confidence: high
Notes: Matches FAR regulatory pattern, no disambiguation needed

Entity: "Weekly Status Reports"
Type: deliverable
Confidence: high
Notes: Tangible work product (report), not ongoing obligation
```

---

## STEP 3: Enrich with Domain Intelligence

### Goal

Add **operational context that enables informed decisions** by **contextually consulting** domain knowledge libraries.

**Decision-making value**: Rich context = better decisions. "FAR 52.204-21" alone doesn't help—but "FAR 52.204-21 requires NIST 800-171, costs $50K-$500K, non-compliance = rejection" enables bid/no-bid and pricing decisions.

### Consultation Steering (IF-THEN Logic)

**IF entity type is CLAUSE**:
→ **CONSULT §4.1 FAR/DFARS Comprehensive Intelligence**
→ Add: Operational implications, flowdown requirements, cost impacts, temporal constraints

**IF entity type is EVALUATION_FACTOR**:
→ **CONSULT §4.2 Evaluation Comprehensive Intelligence**
→ Add: Scoring methodology (adjectival vs numerical), typical weights, DoD vs civilian patterns, subfactor recognition

**IF entity type is REQUIREMENT**:
→ **CONSULT §4.4 Requirement Classification Intelligence**
→ Add: Criticality level (MANDATORY/SHOULD/MAY), Shipley compliance implications, acceptance criteria

**IF entity type is STRATEGIC_THEME**:
→ **CONSULT §4.3 Proposal Comprehensive Intelligence**
→ Add: Win theme framework (FAB pattern), discriminator potential, competitive advantage linkage

**IF entity type is SUBMISSION_INSTRUCTION**:
→ **CONSULT §4.2 Evaluation Comprehensive Intelligence (Section L patterns)**
→ Add: Evaluation factor linkage, format enforcement implications

**IF entity type is SECTION**:
→ **CONSULT §4.5 Section Pattern Library**
→ Add: UCF structure patterns, semantic content expectations, cross-reference patterns

**IF entity type is DELIVERABLE, DOCUMENT, STATEMENT_OF_WORK, PROGRAM, EQUIPMENT**:
→ **Enrich from chunk context** (domain knowledge libraries may have limited specific guidance)
→ Add: Operational implications, relationships to requirements/evaluation

**IF entity type is ORGANIZATION, CONCEPT, EVENT, TECHNOLOGY, PERSON, LOCATION**:
→ **Enrich from chunk context** (generic entities, domain knowledge less applicable)
→ Add: Role, relevance, connections to contracting-specific entities

### Enrichment Formula Template

**Target description structure**:

```
[Entity Name]. [Primary operational implication]. [Temporal constraints]. [Cost/risk impact]. [Relationship hints]. [Semantic variants recognition].
```

**Example enrichment progression**:

**Basic** (classified only):

```
entity|FAR 52.204-21|clause|NIST 800-171 compliance clause
```

**Good** (chunk context added):

```
entity|FAR 52.204-21|clause|FAR 52.204-21 requires implementation of NIST 800-171 security controls for CUI. Non-compliance results in contract ineligibility.
```

**Excellent** (domain intelligence consulted from §4.1):

```
entity|FAR 52.204-21|clause|FAR 52.204-21 Basic Safeguarding (DFARS 252.204-7012 for DoD). Contractor SHALL implement NIST 800-171 security controls for all CUI systems. Non-compliance = contract ineligibility (go/no-go criterion). Deliverables required: SSP (System Security Plan), POAM (Plan of Action & Milestones), SPRS score (min 110 for DoD). Cost impact: $50K-$500K depending on gap assessment. Creates relationships: FAR 52.204-21 --REQUIRES--> SSP, FAR 52.204-21 --REQUIRES--> POAM, FAR 52.204-21 --EVALUATED_BY--> Cyber Posture Assessment.
```

### Domain Knowledge Consultation Mechanics

**How to consult**:

1. Identify entity type from STEP 2
2. Check IF-THEN steering above
3. **Jump to indicated §4.x section** in domain knowledge
4. **Scan for relevant patterns** (use semantic matching, not exact keywords)
5. **Extract applicable intelligence** (operational context, typical patterns, implications)
6. **Apply to entity description** (merge chunk context + domain intelligence)

**Example consultation**:

Entity: "Factor 1: Technical Approach" (type: evaluation_factor)
→ Consult §4.2 Evaluation Comprehensive Intelligence
→ Find: "Three-Factor Trinity pattern: Technical Approach typically 30-50% weight in DoD RFPs, evaluated using adjectival ratings"
→ Find: "Common subfactors: solution architecture, innovation, risk mitigation, compliance"
→ Find: "Semantic variants: Solution Design, Methodology, Project Approach"
→ Apply: "Factor 1: Technical Approach (DoD pattern: typically 30-50% weight in Three-Factor Trinity structure). Evaluated using adjectival ratings (Outstanding/Good/Acceptable). Common subfactors: solution architecture, innovation, risk mitigation, compliance. Evaluates HOW contractor will execute technical work. Recognize variants: 'Solution Design', 'Methodology', 'Project Approach' (same semantic meaning)."

---

## STEP 4: Infer Relationships

### Goal

Identify meaningful connections between entities that represent **decision pathways** - the links that enable strategic queries.

**Decision-making value**: Relationships answer "how does X affect Y?" questions. EVALUATED_BY links enable "which requirements drive scoring?" REQUIRES links enable "what compliance obligations exist?" FLOWS_TO links enable "what subcontractor responsibilities?"

### Primary Relationship Types

**EVALUATED_BY** (requirement/deliverable → evaluation_factor):

- Pattern: Work obligation mentioned near scoring criteria
- Example: "Weekly status reports" (deliverable) --EVALUATED_BY--> "Factor 2: Management Approach" (evaluation_factor)

**GUIDES** (submission_instruction ↔ evaluation_factor):

- Pattern: Format/page limit for specific evaluation response
- Example: "Technical volume 25-page limit" (submission_instruction) --GUIDES--> "Factor 1: Technical Approach" (evaluation_factor)

**REQUIRES** (clause/requirement → deliverable/document):

- Pattern: Regulatory obligation specifies required work product
- Example: "FAR 52.204-21" (clause) --REQUIRES--> "System Security Plan" (deliverable)

**CHILD_OF** (hierarchical structure):

- Pattern: Subfactors, sub-requirements, annexes to parent sections
- Example: "Factor 1.1: Solution Architecture" --CHILD_OF--> "Factor 1: Technical Approach"

**FLOWS_TO** (prime → subcontractor obligations):

- Pattern: Clause or requirement with flowdown language
- Example: "FAR 52.222-26 Equal Opportunity" --FLOWS_TO--> "All subcontractors"

**REFERENCES** (cross-document linkage):

- Pattern: "See Attachment J-0005", "IAW MIL-STD-882"
- Example: "Section C SOW" --REFERENCES--> "Attachment J-0005 PWS"

### Relationship Inference Patterns

**Consult §5 Relationship Patterns** for detailed detection rules, then apply:

**For each entity pair**, ask:

1. **Topical proximity**: Do they appear in same/adjacent paragraphs?
2. **Semantic connection**: Does one constrain, evaluate, require, or define the other?
3. **Structural linkage**: Are they parent-child, cross-referenced, or co-located by design?

**If YES to any**, create relationship:

```
relationship|[source entity]|[relationship type]|[target entity]|[description explaining WHY they're connected]
```

**Example**:

```
relationship|Weekly Status Reports|EVALUATED_BY|Factor 2: Management Approach|Management reporting deliverable (weekly status reports) demonstrates project management capability, scored under Factor 2: Management Approach per Section M evaluation criteria.
```

---

## STEP 5: Output Structured Entities and Relationships

### Goal

Generate properly formatted, **decision-ready** output for knowledge graph ingestion.

**Decision-making value**: Validate that extracted intelligence meets quality standards. Every entity should enable at least one strategic query. Every relationship should answer at least one "how does X affect Y?" question.

### Output Format

**Entity format**:

```
entity|[entity name]|[entity type]|[description with domain intelligence]
```

**Relationship format**:

```
relationship|[source]|[relationship type]|[target]|[description]
```

### Quality Checklist (Before Output)

**Every entity MUST have**:

- ✅ Unique name (exact text from RFP or normalized form)
- ✅ Valid entity type (one of 17 types)
- ✅ Description ≥100 characters (target 150-250)
- ✅ Operational context (not just definition)
- ✅ **Decision-making value**: Does this description enable informed decisions? Would a capture manager understand implications?

**Every relationship MUST have**:

- ✅ Valid source and target entities (both already output)
- ✅ Semantic relationship type (EVALUATED_BY, GUIDES, REQUIRES, etc.)
- ✅ Description explaining WHY they're connected
- ✅ **Decision-making value**: Does this relationship answer a strategic question ("what affects what?")?

### Example Complete Output

```
entity|FAR 52.204-21 NIST 800-171 Compliance|clause|FAR 52.204-21 Basic Safeguarding. Contractor SHALL implement NIST 800-171 security controls for all CUI systems. Non-compliance = contract ineligibility. Deliverables: SSP, POAM, SPRS score (min 110). Cost impact: $50K-$500K.

entity|System Security Plan (SSP)|deliverable|Documented security controls implementing NIST 800-171 for CUI systems. Required by FAR 52.204-21. Must detail administrative, technical, and physical safeguards. Typically 50-200 pages depending on system complexity.

entity|Factor 1: Technical Approach|evaluation_factor|Technical Approach (DoD pattern: typically 30-50% weight). Evaluated using adjectival ratings. Common subfactors: solution architecture, innovation, risk mitigation. Evaluates HOW contractor executes technical work.

relationship|FAR 52.204-21 NIST 800-171 Compliance|REQUIRES|System Security Plan (SSP)|FAR 52.204-21 mandates SSP as evidence of NIST 800-171 implementation. SSP demonstrates security control deployment for CUI protection.

relationship|System Security Plan (SSP)|EVALUATED_BY|Factor 1: Technical Approach|SSP quality and comprehensiveness likely assessed under Factor 1 Technical Approach as evidence of security architecture and risk mitigation capability.
```

---

## Execution Workflow Summary

**For each RFP chunk, execute in order**:

```
1. SCAN & DETECT
   ├─ Identify 10-50 entity candidates using semantic signals
   ├─ Record exact text + triggering pattern + context
   └─ Move to STEP 2

2. CLASSIFY
   ├─ Assign 1 of 17 entity types to each candidate
   ├─ Apply disambiguation rules where multiple types possible
   ├─ Record classification + confidence + notes
   └─ Move to STEP 3

3. ENRICH
   ├─ For each classified entity:
   │  ├─ Check IF-THEN steering for domain knowledge consultation
   │  ├─ IF applicable, CONSULT relevant §4.x section
   │  ├─ Extract operational context, patterns, implications
   │  └─ Merge chunk context + domain intelligence → description
   └─ Move to STEP 4

4. RELATE
   ├─ For all entity pairs in chunk:
   │  ├─ Check topical proximity (same/adjacent paragraphs)
   │  ├─ Check semantic connection (evaluation, requirement, reference)
   │  ├─ If connected, create relationship with description
   └─ Move to STEP 5

5. OUTPUT
   ├─ Quality check: All entities meet minimum standards
   ├─ Quality check: All relationships have valid source/target
   ├─ Format entities: entity|name|type|description
   ├─ Format relationships: relationship|source|type|target|description
   └─ Return structured output
```

---

## Remember

- **Execute steps sequentially** - each builds on the previous toward decision-ready intelligence
- **Consult domain knowledge contextually** - apply intelligence that enables decisions, not blanket patterns
- **Prioritize decision-making value** - every entity should answer strategic questions, every relationship should map decision pathways
- **Speed AND quality matter** - process 425-page RFPs in 45-60 minutes with comprehensive coverage competitors can't match manually

**Your extraction quality determines competitive advantage**: While others spend 8+ hours manually analyzing and miss critical details, you deliver complete intelligence for informed decision making.

---

**Next Layer**: Entity Specifications (detailed semantic definitions for all 17 types with decision-making value for each)

- **Semantic understanding over keyword matching** - recognize meaning, not just words
- **Quality over speed** - better to process carefully than extract generically

**Next Layer**: Entity Type Specifications (detailed definitions + disambiguation rules for all 17 types)
