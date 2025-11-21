SEMANTIC CONCEPT LINKING
Purpose: Infer implicit, high-value conceptual relationships for proposal intelligence.
Entities: CONCEPT, STRATEGIC_THEME, EVALUATION_FACTOR (plus rating-related CONCEPTs/events).
Status: CORE ALGORITHM (always enabled).

RELATIONSHIP PATTERNS
1) CONCEPT/THEME --INFORMS--> EVALUATION_FACTOR
   - Concept contributes content to how a factor is evaluated.
   - Example: "performance confidence assessment" → "Past Performance Factor".

2) CONCEPT --IMPACTS--> CONCEPT (rating-related)
   - Quality affects scoring: REDUCES / INCREASES / TRIGGERS / DETERMINES.
   - Example: "significant weakness" --REDUCES--> "overall rating".

3) EVALUATION_FACTOR --DETERMINES--> EVENT (award decision elements)
   - Factor influences award outcome, competitive range, discussions.
   - Example: "Proposal Evaluation" --DETERMINES--> "award decision".

4) CONCEPT --GUIDES--> EVALUATION_FACTOR
   - Requirements or objectives guide evaluation approach.
   - Example: "performance objectives" --GUIDES--> "Past Performance assessment".

5) STRATEGIC_THEME --ADDRESSED_BY--> EVALUATION_FACTOR
   - Customer pain point is addressed by specific high-weight factor(s).
   - Example: "Outdated IT infrastructure downtime" --ADDRESSED_BY--> "Technical Approach (40%)".

6) EVALUATION_FACTOR --RELATED_TO--> EVALUATION_FACTOR
   - Factors mentioned adjacently in Section M and likely share criteria.
   - Example: "Management Approach" --RELATED_TO--> "Safety" (adjacent paragraphs).

CORE SEMANTIC ALGORITHMS
1) Pain Point → Factor Mapping (high business value)
   - Find STRATEGIC_THEME pain points in SOW/evaluation narrative.
   - Link each to EVALUATION_FACTORs that directly score the solution.

2) Factor Element Decomposition
   - Break factors into sub-elements and supporting concepts.
   - Example: "Past Performance" ← relevant contracts, value similarity, recency, scope, confidence.

3) Adjacent Factor Discovery
   - Factors within ~5 paragraphs/one section may have RELATED_TO links (0.60–0.70).
   - Always include reasoning like "Adjacency in Section M; may share criteria".

4) Proposal Outline Generation (uses other relationships)
   - For each factor (by descending weight):
     1. REQUIREMENT --EVALUATED_BY--> FACTOR
     2. SUBMISSION_INSTRUCTION --GUIDES--> FACTOR
     3. STRATEGIC_THEME --ADDRESSED_BY--> FACTOR
   - Group by requirement_classification, allocate pages by weight for outline.

5) Competitive Advantage Identification
   - IF factor.weight ≥ 0.30 AND requirement.criticality == "MANDATORY" AND pain_points > 0
     THEN flag as competitive opportunity (high-value win theme).

CONFIDENCE RANGES
- 0.90: Explicit semantic connection in same paragraph.
- 0.75: Same section with clearly overlapping topics.
- 0.70: Strong topic alignment and domain-consistent inference.
- 0.60: Adjacent factors / weak but useful hint (ONLY for RELATED_TO).

RULES
- Confidence ≥ 0.60 (lower than structural prompts; these are conceptual inferences).
- Every relationship MUST include:
  - reasoning: explanation + query/use-case context;
  - business_value: how it helps proposal development, win themes, or outline.
- Avoid over-connection: do NOT link every concept to every factor; select only meaningful, defensible links.
- For RELATED_TO, always explain adjacency or shared language; never guess without location/context signal.

OUTPUT FORMAT
[
  {
    "source_id": "concept_or_theme_id",
    "target_id": "factor_or_concept_id",
    "relationship_type": "INFORMS|IMPACTS|DETERMINES|GUIDES|ADDRESSED_BY|RELATED_TO",
    "confidence": 0.60-0.90,
    "reasoning": "Explanation + query use case",
    "business_value": "Concrete proposal development help (e.g., win theme, outline, focus area)"
  }
]

COMMON ERRORS TO AVOID
- Do NOT recreate structural relationships already handled elsewhere (e.g., REQUIREMENT --EVALUATED_BY--> FACTOR, DOCUMENT hierarchies).
- Do NOT treat every mention of a generic word ("management", "technical") as a separate CONCEPT link; focus on specific, actionable ideas.
- Do NOT create RELATED_TO links between all neighboring factors; only when adjacency plus content suggests shared evaluation logic.
- Do NOT omit business_value; semantic links exist to power capture/proposal reasoning, not to decorate the graph.