EVALUATION HIERARCHY & METRICS INFERENCE
Purpose: Build full evaluation framework structure (factor hierarchy, rating scales, metrics, thresholds, processes).

INPUT: evaluation_factor entities only (from extraction step)
[{
  "entity_id": "unique_id",
  "entity_name": "Factor 1 - Technical",
  "description": "Technical Factor with subfactors 1.1-1.4, rated Outstanding to Unacceptable"
}]

6 RELATIONSHIP TYPES
1) HAS_SUBFACTOR (parent factor → child subfactor)
	- Pattern: "Factor 1" → "Subfactor 1.1" / "1.2" / etc.
	- Also use explicit phrases: "subfactors 1.1-1.4", "consists of", "comprises"

2) HAS_RATING_SCALE (factor/subfactor → rating term)
	- Rating entities: Outstanding, Good, Acceptable, Marginal, Unacceptable, Pass, Fail, Neutral, High Confidence, Low Confidence.
	- Use when description ties factor to specific rating levels or table.

3) MEASURED_BY (factor/subfactor → metric)
	- Metrics: any entity with numeric % / rates / counts that measure performance.
	- Look for: "95% compliance", "100% inspection", "zero discrepancies", "95% operational rate".

4) HAS_THRESHOLD (metric → threshold/criterion)
	- Metric has explicit acceptance criterion: "95% compliance required", "no more than 2 defects", "threshold" / "minimum" / "standard".

5) EVALUATED_USING (factor → evaluation process/method)
	- Processes: "Price Realism Analysis", "Best-Value Tradeoff", "Pass/Fail evaluation", "Lowest Price Technically Acceptable".

6) DEFINES_SCALE (scale/table → factor or rating terms)
	- Entities that define rating structures: "Technical Rating Definitions Table", "Past Performance Confidence Ratings".

MAIN FACTORS (keep for Requirement→Factor linking)
- Name contains "Factor" + number ("Factor 1", "Factor 2").
- Name contains "Subfactor" + number ("Subfactor 1.1").
- Named evaluation categories: "Technical", "Management", "Price", "Past Performance", "Risk".
- Specific evaluation plans: "TOMP", "Mission Essential Plan", "Quality Control Plan" when clearly defined as subfactors.

SUPPORTING ENTITIES (used only as children/attributes)
- Rating terms: Outstanding, Good, Acceptable, Marginal, Unacceptable, Pass, Fail, etc.
- Metrics: entities with % values, numeric targets, rates, thresholds.
- Processes: names containing "evaluation", "analysis", "assessment", "rating".
- Thresholds: terms like "threshold", "level", "criteria", "standard".
- Tables: names with "(table)" or "Table" + number that define scales.

CONFIDENCE SCORING
- 0.95–1.00: Explicit hierarchy or linkage in description ("subfactor", "rated using", "evaluated using").
- 0.85–0.94: Strong contextual evidence (consistent naming, numbering, table structures).
- 0.75–0.84: Moderate domain-based inference (typical evaluation patterns).
- <0.75: Do NOT create relationship.

OUTPUT FORMAT (JSON array)
[
  {
	 "source_id": "parent_or_factor_id",
	 "target_id": "child_or_supporting_entity_id",
	 "relationship_type": "HAS_SUBFACTOR|HAS_RATING_SCALE|MEASURED_BY|HAS_THRESHOLD|EVALUATED_USING|DEFINES_SCALE",
	 "confidence": 0.75-1.0,
	 "reasoning": "Quote key text + explain why relationship exists"
  }
]

COMMON ERRORS TO AVOID (CRITICAL)
- Do NOT treat generic narrative about "good" or "acceptable" performance as rating scale entities unless there is clear rating-table context.
- Do NOT create HAS_SUBFACTOR between two top-level factors (e.g., "Factor 1" and "Factor 2"). Only use when numbering/description clearly shows parent→child.
- Do NOT invent numeric thresholds from vague language ("high quality", "timely"). Thresholds require explicit or strongly implied numbers.
- Do NOT treat administrative entities (e.g., proposal delivery instructions) as evaluation processes; EVALUATED_USING must describe how proposals are scored.