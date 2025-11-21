ATTACHMENT → SECTION LINKING (ATTACHMENT_OF)

PURPOSE
Link TOP-LEVEL attachments/annexes/documents to their parent RFP sections to enable section-based navigation (e.g., all Section J attachments).

CORE PATTERN
ANNEX/DOCUMENT --ATTACHMENT_OF--> SECTION
This is different from CHILD_OF (document→document hierarchy).

INFERENCE PATTERNS
1) NAMING CONVENTION (confidence ≈ 1.0)
    - J-###### → Section J (List of Attachments).
    - A-###### → Section A (Solicitation/Contract Form).
    - H-###### → Section H (Special Requirements).
    - Generic "Attachment #", "Annex #", "Exhibit #" → Section J by default (unless agency pattern says otherwise).

2) EXPLICIT CITATION (confidence ≈ 0.95)
    - Attachment listed under a section heading.
    - Example: "Section J: List of Attachments – J-02000000 PWS, J-03000000 QASP".

3) CONTENT ALIGNMENT (confidence ≈ 0.70)
    - Pricing/Cost schedules → Section B (Supplies/Services and Prices/Costs).
    - PWS/SOW/SOO → Section C or Section J (if attached as J- document).
    - Key Personnel lists → Section H.
    - Quality Plans → Section J.
    - Security Plans → Section H or J.

AGENCY PATTERNS (GUIDANCE)
- DoD (Navy/Air Force/Army/USMC):
   - J-######## attachments (PWS, QASP, CDRL, DD254, etc.) → Section J.

- GSA:
   - Exhibit + pricing keywords ("Pricing Schedule", "Price/Cost") → Section B.
   - Attachment (PWS, QCP, technical docs) → Section J.

- NASA:
   - Annex with Roman numerals (Annex I, II, XVII) → Section J.

- DoE:
   - Exhibit + pricing → Section B.
   - Attachment → Section J.

- State:
   - Annex lettered (Annex A, B, C) → Section J.

RULES & SPECIAL CASES
- TOP-LEVEL ONLY: Only top-level attachments get ATTACHMENT_OF. Sub-attachments (e.g., J-02000000-10) use CHILD_OF→parent attachment, not ATTACHMENT_OF→section.
- ONE SECTION PER ATTACHMENT: Do not link the same attachment to multiple sections.
- REFERENCED BUT NOT ATTACHED: Standards/guides cited (e.g., MIL-STD-882E) are not ATTACHMENT_OF; use REFERENCES relationships elsewhere.
- WORK STATEMENT LOCATION FLEXIBLE: SOW/PWS/SOO may be inline in Section C or attached via Section J; link based on naming + where it actually appears.

OUTPUT FORMAT (PER RELATIONSHIP)
{
   "source_id": "attachment_id",
   "target_id": "section_id",
   "relationship_type": "ATTACHMENT_OF",
   "confidence": 0.70-1.0,
   "reasoning": "Pattern + specific match details (e.g., 'J-prefix → Section J', 'Pricing Exhibit → Section B (GSA pattern)')."
}