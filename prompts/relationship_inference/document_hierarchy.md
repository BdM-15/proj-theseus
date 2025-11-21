DOCUMENT HIERARCHY (CHILD_OF)
Purpose: Build parent-child relationships across DOCUMENT/CLAUSE/ANNEX entities
Pattern: CHILD --CHILD_OF--> PARENT (J-02000000-10→J-02000000, NIST 800-171 3.1.1→NIST 800-171 Rev 2)

4 HIERARCHICAL PATTERNS:
1. PREFIX+DELIMITER (0.95): Navy/DoD/DoE
   J-02000000, J-02000000-10, J-02000000-20 (extract prefix before last delimiter)
   H-1, H-1.1, H-1.2 (decimal notation)
   PWS-001, PWS-001-A (alphanumeric suffix)
2. STANDARD+SUBSECTION (0.90): Technical specs
   MIL-STD-882E Task 101 → MIL-STD-882E
   NIST 800-171 3.1.1 → NIST 800-171 Rev 2
   ISO 9001:2015 8.2.3 → ISO 9001:2015
3. CLAUSE+PARAGRAPH (0.95): FAR/DFARS
   FAR 52.212-4(a) → FAR 52.212-4
   DFARS 252.204-7012(b)(2) → DFARS 252.204-7012(b)
4. DECIMAL NOTATION (0.90): GSA/Commercial
   Exhibit A.1 → Exhibit A, Section 3.1.2 → Section 3.1

RULES:
- Acyclic graph (no circular relationships)
- Single parent (≤1 CHILD_OF parent)
- Same document family (J→J, NIST→NIST, FAR→FAR, NOT cross-family)
- Version detection: 4-digit year or "Rev N" → version NOT hierarchy
- Confidence ≥0.70

COMPLEMENTARY RELATIONSHIPS:
ATTACHMENT_OF: J-02000000→Section J (section linkage)
CHILD_OF: J-02000000-10→J-02000000 (document hierarchy)
REFERENCES: Section C→NIST 800-171 (content citation)

OUTPUT:
[{"source_id":"child_id","target_id":"parent_id","relationship_type":"CHILD_OF","confidence":0.70-0.95,"reasoning":"Pattern name + specific match"}]