REQUIREMENT → EVALUATION FACTOR MAPPING (EVALUATED_BY)

PURPOSE
Link REQUIREMENT entities to EVALUATION_FACTOR entities that will score them, so proposal teams can allocate effort and build Section M–aligned outlines.

CORE PATTERN
REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR
Meaning: this requirement is evaluated under this factor.

INFERENCE PATTERNS
1) TOPIC ALIGNMENT (≈0.80)
   - Requirement topic matches factor topic.
   - Example: "24/7 help desk support" → "Technical Approach – Help Desk Operations".

2) CRITICALITY MAPPING (≈0.75)
   - MANDATORY requirements (criticality_level ≥ 0.8) map into high-weight factors.
   - Example: "Weekly status reports" (MANDATORY) → "Management Approach" (30%).

3) CONTENT PROXIMITY (≈0.70)
   - Requirement and factor discussed near each other in the document (location-agnostic: Section C, H, M, attachments).

4) EXPLICIT CROSS-REFERENCE (≈0.95)
   - Requirement text explicitly references a factor or Section M.
   - Example: "see Section M, Factor 3: Quality Control".

TOPIC CATEGORIES (FOR ALIGNMENT)
- Technical: IT systems, integration, cloud, performance, uptime → Technical Approach/Capability/Architecture factors.
- Management: status reports, schedules, risk, PM processes → Management/Program Management/Risk Management.
- Performance: past performance, relevant experience → Past Performance/Demonstrated/Corporate Experience.
- Personnel: staffing, qualifications, key personnel → Key Personnel/Staffing/Qualifications.
- Quality: ISO, quality audits, standards → Quality Control/Quality Assurance/Quality Management.
- Transition: phase-in, continuity of operations, cutover risk → Transition/Phase-In/COOP.

REQUIREMENT TYPE OVERRIDE (HIGH-CONFIDENCE)
Use requirement.requirement_type to override naive keyword matches:
- FUNCTIONAL → Technical Approach–type factors.
- PERFORMANCE → Performance Standards/SLAs.
- SECURITY → Security factor (if exists) or Technical Approach (security subcategory).
- MANAGEMENT → Management Approach–type factors.

Special rule: if requirement_type clearly signals MANAGEMENT, prefer Management Approach even if words like "risk" or "security" appear.

MAPPING RULES
- A requirement may map to multiple factors (e.g., cybersecurity controls → Technical + Security; reporting-heavy requirement → Technical + Management Approach).
- Skip INFORMATIONAL requirements (government obligations, admin details) – especially when criticality_level = 0 or requirement is clearly Government-shall.
- MANDATORY requirements (criticality_level ≥ 0.8) should have at least one EVALUATED_BY link unless truly administrative.
- Confidence must be ≥ 0.70 for any relationship created.

EXPECTED BEHAVIOR
- Coverage: ≈75% of MANDATORY requirements receive at least one factor mapping; INFORMATIONAL requirements receive none.
- Multiple-factor mappings are common for complex, cross-cutting requirements.

OUTPUT FORMAT (PER RELATIONSHIP)
{
  "source_id": "requirement_id",
  "target_id": "factor_id",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.70-0.95,
  "reasoning": "Pattern name + brief topic/type explanation (e.g., 'Topic alignment: help desk requirement → Technical Approach – Help Desk Operations')."
}

ADVANCED EXAMPLE – MULTI-FACTOR, TYPE-OVERRIDDEN MAPPING
Requirement:
"The Contractor shall implement NIST 800-171 controls across all mission systems, provide quarterly compliance reports to the Government, and ensure zero downtime during cutover to the new architecture."

Expected mappings:
- To Technical Approach factor (cybersecurity implementation & architecture).
- To Management/Quality factor (recurring compliance reporting).
- To Transition/COOP factor (zero-downtime cutover).

Example relationships:
[
   {
      "source_id": "req_nist_controls_cutover",
      "target_id": "factor_technical_approach",
      "relationship_type": "EVALUATED_BY",
      "confidence": 0.88,
      "reasoning": "Topic alignment: NIST 800-171 implementation and mission system architecture → Technical Approach."
   },
   {
      "source_id": "req_nist_controls_cutover",
      "target_id": "factor_management_or_quality",
      "relationship_type": "EVALUATED_BY",
      "confidence": 0.8,
      "reasoning": "Criticality + topic alignment: quarterly compliance reporting → Management/Quality factor focused on reporting and control."
   },
   {
      "source_id": "req_nist_controls_cutover",
      "target_id": "factor_transition_or_coop",
      "relationship_type": "EVALUATED_BY",
      "confidence": 0.8,
      "reasoning": "Topic alignment: zero downtime during cutover → Transition/Continuity of Operations factor."
   }
]