"""
REVISED STRATEGY: Intelligence Preservation First

Key Insight: Examples are NOT redundant - they teach different domain patterns.
Goal: Reorganize for clarity, NOT reduce for the sake of compression.

Analysis of Example Intelligence:
1. QASP examples: Teach performance metric vs requirement split
2. Section L↔M: Teach evaluation/submission linkage patterns
3. Workload examples: Teach labor_drivers vs material_needs extraction
4. Equipment tables: Teach HTML table parsing for inventories
5. Maintenance schedules: Teach preventive maintenance workload patterns
6. PWS appendix: Teach document hierarchy and references
7. Strategic themes: Teach customer hot button detection

EACH example provides UNIQUE intelligence about federal RFP patterns.

Revised Plan:
============

Instead of REDUCING examples, we:

1. ORGANIZE by entity type (already done in schema_mirror/)
2. ADD cross-references to related examples
3. PRESERVE all domain intelligence
4. ENHANCE with Grok-4 structured format (patterns before prose)

Token savings will come from:
- Eliminating repeated preambles ("Input Text:", "Extracted Entities:")
- Grok-4 decision tree format (structure over narrative)
- Consolidating repeated rules (modal verb explanations, etc.)
- NOT from cutting examples

Example Reorganization:
=======================

Current v1 structure:
  Example 1: Title
  [Long narrative setup]
  Input Text:
  [RFP text]
  Extracted Entities:
  [JSON]
  Note: [Explanation]

Grok-4 optimized structure:
  PATTERN: Title
  INPUT:
    [RFP text - concise]
  OUTPUT:
    [JSON - minimal comments]
  INTELLIGENCE:
    - Key takeaway 1
    - Key takeaway 2

Token savings: ~30% per example through format optimization, NOT content reduction.

Estimated Impact:
================

Current examples: ~47,900 tokens (1,916 lines × 25 tokens/line)
Grok-4 optimized: ~33,500 tokens (30% format reduction)
Intelligence: 100% preserved (all 23 examples retained)

This achieves compression through STRUCTURE, not DELETION.
"""

def print_strategy():
    print(__doc__)

if __name__ == "__main__":
    print_strategy()
