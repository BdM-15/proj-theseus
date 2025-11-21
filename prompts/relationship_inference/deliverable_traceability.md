DELIVERABLE TRACEABILITY – REQUIREMENTS & WORK STATEMENTS

PURPOSE
Link deliverables to:
- REQUIREMENTS for performance/functional/technical compliance (primary)
- SOW/PWS/SOO work statements for work planning context (secondary)

RELATIONSHIP TYPES
- REQUIREMENT --SATISFIED_BY--> DELIVERABLE
- STATEMENT_OF_WORK --PRODUCES--> DELIVERABLE

KEY INSIGHT
- 60–80% of deliverables come from CDRLs, clauses, and evaluation criteria (not SOW text).
- Requirement→deliverable links are PRIMARY; SOW→deliverable links are SECONDARY.

PATTERN 1 (PRIMARY): REQUIREMENT --SATISFIED_BY--> DELIVERABLE
Deliverables provide evidence that a requirement has been met.

COMMON PATTERNS
- Reporting Requirements: "99.9% system uptime" → "Monthly Uptime Report (CDRL A001)"
- Documentation Requirements: "support 500 concurrent users" → "Performance Test Report (CDRL B003)"
- Proof Point Deliverables: "Implement zero-trust architecture" → "Security Architecture Document (Section M reference)"
- Compliance Evidence: "Comply with NIST SP 800-171" → "System Security Plan (CDRL C002)"

DETECTION RULES
1) Semantic Overlap
	- Testing requirements → test reports/results
	- Performance requirements → performance/uptime reports
	- Security requirements → security plans/assessments
	- Training requirements → training materials/records

2) Keyword Correlation
	- "shall maintain" → monitoring/status reports
	- "shall implement" → design/implementation documents
	- "shall demonstrate" → test results/demonstrations
	- "shall comply with" → compliance reports/certifications

3) Evidence Chain
	- Requirement defines capability/standard.
	- Deliverable documents or validates that capability.
	- Reasoning should explicitly tie deliverable content to requirement intent.

CONFIDENCE GUIDANCE (PATTERN 1)
- 0.85–0.95: Direct evidence (test report for test requirement, uptime report for uptime requirement).
- 0.75–0.85: Strong semantic overlap (security plan for security requirements).
- 0.65–0.75: Moderate/indirect evidence (general status report supporting multiple requirements).

PATTERN 2 (SECONDARY): STATEMENT_OF_WORK --PRODUCES--> DELIVERABLE
Work statements describe activities that produce deliverables used for planning and execution.

COMMON PATTERNS
- Explicit CDRL References: "Prepare monthly status reports per CDRL A001" → "Monthly Status Report (CDRL A001)".
- Work-Product Mapping: "Maintain facility infrastructure and equipment" → "Facility Maintenance Logs (CDRL B012)".
- Timeline Alignment: "Complete Phase 1 cybersecurity objectives by Q2" → "Phase 1 Security Assessment Report (due June 30)".

DETECTION RULES
1) Direct CDRL/Deliverable References
	- CDRL numbers (A001, B002, etc.).
	- Report names that match deliverable entities.
	- "contractor shall deliver X" language.

2) Work-Product Correlation
	- Testing tasks → test reports.
	- Training tasks → training materials/records.
	- Maintenance tasks → maintenance logs.

3) Timeline Matching
	- Phase/milestone completion → phase reports.
	- Monthly tasks → monthly deliverables.
	- Quarterly reviews → quarterly reports.

CONFIDENCE GUIDANCE (PATTERN 2)
- >0.90: Explicit CDRL/deliverable reference in SOW text.
- 0.70–0.90: Strong work-product semantic match.
- 0.50–0.70: Weak temporal/topical alignment.

SPECIAL CASES & RULES
- Deliverable may link to multiple requirements and/or work statements – create separate edges.
- Deliverables that only appear in CDRLs/clauses/eval criteria still link to requirements (Pattern 1) even if no SOW reference exists.
- Avoid creating links with only generic topical similarity and no evidence chain.

COMMON ERRORS TO AVOID (CRITICAL)
- Do NOT create SATISFIED_BY edges from generic "status reports" to every requirement in a section; require a clear evidence chain to specific requirement topics.
- Do NOT attach the same deliverable as PRODUCES to a SOW paragraph unless there is an explicit or strongly implied work-product relationship (e.g., "prepare", "submit", "deliver").
- Do NOT use deliverables that are only cited as examples in Section M ("such as …") as if they were mandatory, unless they also appear as CDRLs or explicit obligations.
- Do NOT ignore CDRL table structure: if a CDRL row clearly names a requirement or section reference, that should strongly favor Pattern 1 links to those requirements.

OUTPUT FORMAT (PER RELATIONSHIP)
{
  "source_id": "requirement_or_sow_entity_id",
  "target_id": "deliverable_entity_id",
  "relationship_type": "SATISFIED_BY" | "PRODUCES",
  "confidence": 0.50-0.96,
  "reasoning": "Clear explanation of how the deliverable evidences the requirement or is produced by the work statement."
}

EXAMPLE OUTPUT ARRAY
[
  {
	 "source_id": "req_security_123",
	 "target_id": "deliv_ssp_456",
	 "relationship_type": "SATISFIED_BY",
	 "confidence": 0.92,
	 "reasoning": "System Security Plan deliverable provides evidence of NIST 800-171 compliance requirement satisfaction."
  },
  {
	 "source_id": "sow_section_789",
	 "target_id": "deliv_status_101",
	 "relationship_type": "PRODUCES",
	 "confidence": 0.94,
	 "reasoning": "SOW Section 3.4 explicitly references CDRL A001 Monthly Status Report as required deliverable."
  },
  {
	 "source_id": "req_uptime_234",
	 "target_id": "deliv_uptime_567",
	 "relationship_type": "SATISFIED_BY",
	 "confidence": 0.88,
	 "reasoning": "Monthly Uptime Report provides performance evidence for 99.9% availability requirement."
  }
]