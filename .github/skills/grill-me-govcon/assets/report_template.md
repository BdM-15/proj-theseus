% Title: Grill-Me Report
% Author: Theseus GovCon Platform

# {{title}}

Generated for workspace: **{{workspace}}**

**Run ID:** {{run_id}} • **Skill:** {{skill}}

## Questions and Reasoning

|   # | Question | AI Rationale | Recommended Answer | User Answer | Evidence |
| --: | -------- | ------------ | ------------------ | ----------- | -------- |

{% for q in questions %}
| {{q.id}} | {{q.text}} | {{q.ai_reasoning}} | {{q.recommended_answer}} | {{q.user_answer or ''}} | {{q.evidence.chunks | join(', ')}} |
{% endfor %}

## Recommendations

{% for r in recommendations %}

- **{{r.priority}}**: {{r.text}} — _Justification_: {{r.justification}} (evidence: {{r.evidence | join(', ')}})
  {% endfor %}

## Top Risks

{% for risk in top_risks %}

- {{risk.text}} — likelihood: {{risk.likelihood}}, impact: {{risk.impact}} (evidence: {{risk.evidence | join(', ')}})
  {% endfor %}

## Open Intelligence Gaps

{% for gap in open_intel_gaps %}

- {{gap}}
  {% endfor %}

---

Generated on {{timestamp}}
