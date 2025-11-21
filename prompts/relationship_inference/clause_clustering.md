CLAUSE CLUSTERING (CHILD_OF)
Purpose: Group scattered FAR/DFARS/agency-supplement clauses under correct parent sections.
Pattern: CLAUSE --CHILD_OF--> SECTION (e.g., FAR 52.212-4 → Section I).

3 INFERENCE PATTERNS
1) NUMBERING (0.90):
	 - FAR 52.### → usually Section I (Contract Clauses).
	 - FAR 52.2##-## → usually Section K (Representations/Certifications).
	 - DFARS 252.###-#### → typically Section I.

2) ATTRIBUTION (0.95):
	 - Clause listed directly under a section heading ("Section I: Contract Clauses", "Section K: Representations").

3) CLUSTERING (0.70):
	 - Similar clause series (e.g., FAR 52.212-1/4/5) grouped into the same logical section even if physically scattered.

AGENCY SUPPLEMENTS (26+)
- FAR, DFARS, AFFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, AIDAR, CAR, DIAR, DOLAR, EDAR, EPAAR, FEHBAR, HHSAR, HUDAR, IAAR, JAR, LIFAR, NRCAR, SOFARS, TAR, AGAR.
	(LLM understands these series semantically; do NOT hardcode beyond patterns above.)

RULES
- FAR 52.2##-## → Section K (Representations/Certifications), NOT Section I.
- Special requirements clauses under Section H headings → CHILD_OF Section H.
- Group fragmented clauses from the same series even when pages apart.
- Each clause should have exactly one primary parent SECTION.
- Confidence must be ≥ 0.70.

OUTPUT FORMAT
[
	{
		"source_id": "clause_id",
		"target_id": "section_id",
		"relationship_type": "CHILD_OF",
		"confidence": 0.70-0.95,
		"reasoning": "Numbering/heading/cluster pattern that justifies this parent"
	}
]

COMMON ERRORS TO AVOID
- Do NOT classify representation clauses (FAR 52.2##-##) under Section I; they belong in Section K unless the heading clearly says otherwise.
- Do NOT assign multiple different parent sections to the same clause; choose the logically dominant one.
- Do NOT ignore clauses from the same series just because they appear in different parts of the PDF; clustering must override fragmentation.