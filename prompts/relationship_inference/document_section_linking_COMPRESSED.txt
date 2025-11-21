DOCUMENT→SECTION LINKING (CHILD_OF)
Purpose: Link referenced documents to parent sections
Pattern: DOCUMENT --CHILD_OF--> SECTION (J-12345→Section J)

4 DETECTION RULES:
1. NUMERIC PREFIX (>0.8): Extract section letter
   [A-Z]-\d+ → Section matches letter (J-0005→Section J, Attachment 17→Section J)
2. SEMANTIC NAMING (0.5-0.8): Topic match
   Transportation/Logistics → Section C (SOW)
   Past Performance → Section L (Instructions)
   Standards/Specs → Section C or J
3. EXPLICIT REFS (>0.8): Text mentions
   "Referenced in Section J", "See Attachment to Section C"
4. DOC TYPE PATTERNS: Standard section mappings
   Standards (MIL-STD, ISO) → Section C or J
   Regulations (FAR, DFARS, USC) → Section I or H
   Attachments/Annexes → Section J primary

OUTPUT:
[{"source_id":"document_id","target_id":"section_id","relationship_type":"CHILD_OF","confidence":0.3-1.0,"reasoning":"1-2 sentence explanation"}]