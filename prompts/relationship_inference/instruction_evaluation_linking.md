SUBMISSION INSTRUCTION↔EVALUATION FACTOR LINKING (GUIDES)
Purpose: Link submission instructions to evaluation factors for proposal compliance
Pattern: SUBMISSION_INSTRUCTION --GUIDES--> EVALUATION_FACTOR (Technical Volume format→Factor 1)
Locations: UCF (Section L→M), Task Orders (Proposal Instructions→Selection Criteria), Non-UCF (embedded in deliverables/requirements/factors)

4 INFERENCE PATTERNS:
1. EXPLICIT CROSS-REF (0.95): Direct factor mention
   "Technical Volume addresses Factor 2", "Volume I addresses criteria M1-M3"
2. IMPLICIT CO-LOCATION (0.80): Page limit near factor description (same paragraph)
   "M.2 Management Approach... Management Volume ≤15 pages"
3. CONTENT ALIGNMENT (0.70): Topic match
   "Technical Volume" ↔ "Technical Approach factor"
4. AGNOSTIC CONTENT (0.75-0.90): Instruction-like content in ANY entity type
   Modal verbs: shall submit, must provide, will include
   Format terms: page limit, font size, volume, max pages
   Delivery: due date, submission format, electronic delivery
   Structure: section, paragraph, attachment, annex

SPECIAL CASES:
- One instruction→multiple factors: Create separate relationships
- Embedded instructions (Section M): Extract instruction entity, link to factor
- No clear mapping (<0.70): Do NOT create relationship
- Administrative only (delivery, email): Skip (not evaluation-linked)

RULES:
- Confidence ≥0.70
- Reasoning required
- No circular refs
- Works UCF + non-UCF structures

OUTPUT:
[{"source_id":"instruction_id","target_id":"factor_id","relationship_type":"GUIDES","confidence":0.70-0.95,"reasoning":"1-2 sentences"}]