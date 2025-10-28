# Clause Clustering: FAR/DFARS/Agency Supplement Patterns

**Purpose**: Group scattered FAR/DFARS/agency supplement clauses under parent sections  
**Focus**: CHILD_OF relationships (Clause → Section I parent)  
**Coverage**: FAR (Part 52), DFARS (Part 252), 26+ agency supplements  
**Confidence Target**: ≥0.80 for all clause-to-section mappings  
**Last Updated**: October 28, 2025 (Proven Patterns from Production)

---

## The Core Pattern: CHILD_OF for Clauses

```
CLAUSE --CHILD_OF--> SECTION
```

This maps a contract clause to its parent section in the RFP structure.

**Typical target**: Section I (Contract Clauses)  
**Exception**: Some clauses may be embedded in other sections (infer correctly)

---

## Pattern 1: FAR Numbering Series (Confidence: 0.95)

**Rule**: FAR clauses use 52.### numbering scheme → Parent is Section I

### FAR Coverage

| Series  | Range          | Topic                               | Parent |
| ------- | -------------- | ----------------------------------- | ------ |
| 52.2xx  | 52.201-52.299  | General contract clauses            | Sec I  |
| 52.3xx  | 52.301-52.399  | Indefinite delivery contracts       | Sec I  |
| 52.4xx  | 52.401-52.499  | General services clauses            | Sec I  |
| 52.5xx  | 52.500-52.599  | Safety and security clauses         | Sec I  |

**Examples**:
- `FAR 52.204-21 Basic Safeguarding of Covered Defense Information` → Section I
- `FAR 52.212-4 Contract Terms and Conditions—Commercial Products` → Section I
- `FAR 52.204-25 Prohibition on Contracting for Hardware/Software with Kaspersky Products` → Section I
- `FAR 52.225-1 Buy American Act—Supplies` → Section I

**Extraction**:
```
Source: "FAR 52.204-21"
Target: "Section I"
Type: CHILD_OF
Confidence: 0.95
Reasoning: "FAR 52.### numbering scheme indicates Section I (Contract Clauses)"
```

---

## Pattern 2: DFARS Numbering Series (Confidence: 0.95)

**Rule**: DFARS clauses use 252.### numbering scheme → Parent is Section I

### DFARS Coverage (DoD Supplement)

| Series  | Range             | Topic                                  | Parent |
| ------- | ----------------- | -------------------------------------- | ------ |
| 252.2xx | 252.201-252.299   | General contract clauses (DoD variant) | Sec I  |
| 252.3xx | 252.301-252.399   | Indefinite delivery (DoD variant)      | Sec I  |
| 252.4xx | 252.401-252.499   | General services (DoD variant)         | Sec I  |
| 252.5xx | 252.500-252.599   | Safety/security (DoD variant)          | Sec I  |

**Examples**:
- `DFARS 252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting` → Section I
- `DFARS 252.225-7001 Buy American—Supplies` (DoD variant of FAR 52.225-1) → Section I
- `DFARS 252.227-7015 Technical Data—Commercial Items` → Section I

**Extraction**:
```
Source: "DFARS 252.204-7012"
Target: "Section I"
Type: CHILD_OF
Confidence: 0.95
Reasoning: "DFARS 252.### numbering indicates DoD clause in Section I"
```

---

## Pattern 3: Agency Supplements (Confidence: 0.90)

**Rule**: 26+ agency supplements follow similar patterns

### Major Agency Supplements

| Supplement | Numbering  | Parent | Agencies                    |
| ---------- | ---------- | ------ | --------------------------- |
| AFFARS     | 5352.###   | Sec I  | Air Force                   |
| AFARS      | 4352.###   | Sec I  | Army                        |
| DFARS      | 252.###    | Sec I  | DoD (covers Army/Navy/AF)   |
| NMCARS     | 5252.###   | Sec I  | Navy                        |
| CAR        | 48 CFR 1   | Sec I  | Commerce Department         |
| TAR        | 48 CFR 10  | Sec I  | DOT                         |
| DIAR       | 48 CFR 14  | Sec I  | Interior                    |
| EPAAR      | 48 CFR 15  | Sec I  | EPA                         |
| DEAR       | 48 CFR 9   | Sec I  | Energy                      |
| HSAR       | 48 CFR 3   | Sec I  | Homeland Security           |

**Examples**:
- `AFFARS 5352.204-70 Counterintelligence` → Section I (Air Force)
- `NMCARS 5252.204-7012 CMMC Requirements` → Section I (Navy)
- `EPAAR 1552.211-70 Environmental Clause` → Section I (EPA)

---

## Pattern 4: Explicit Section I Listing (Confidence: 0.98)

**Rule**: If clause is listed under "Section I: Contract Clauses", map to Section I

### Signal: Explicit Section Heading

```
Section I: Contract Clauses

52.204-21 Basic Safeguarding of Covered Defense Information
52.212-4 Contract Terms and Conditions
252.204-7012 Safeguarding CUI and Cyber Incident Reporting
```

**Extraction**:
```
Source: "52.204-21"
Target: "Section I"
Type: CHILD_OF
Confidence: 0.98
Reasoning: "Explicitly listed under Section I heading"
```

---

## Pattern 5: Embedded Clauses (Confidence: 0.75-0.85)

**Rule**: Some clauses may be embedded within other sections (infer based on content)

### Embedded Clause Scenarios

| Scenario                         | Likely Section | Confidence | Examples               |
| -------------------------------- | -------------- | ---------- | ---------------------- |
| Security clearance clause        | Section H      | 0.85       | FAR 52.209             |
| Key personnel requirements       | Section C      | 0.80       | Staffing clauses       |
| Classified information handling  | Section H      | 0.85       | NOFORN, SECRET marking |
| Proprietary information (SBIR)   | Section C      | 0.80       | Rights in data         |

**Decision Tree**:
1. FAR 52.### or DFARS 252.### numbering? → Section I (Confidence 0.95)
2. Listed under "Section I"? → Section I (Confidence 0.98)
3. Agency supplement? → Section I (Confidence 0.90)
4. Embedded in specific section? → That section (Confidence 0.75-0.85)
5. Unknown location? → REJECT (< 0.70)

---

## Output Checklist for CHILD_OF (Clauses)

✅ Source is a CLAUSE entity  
✅ Target is a SECTION entity (typically I, sometimes H or C)  
✅ Type is exactly `CHILD_OF`  
✅ Confidence ≥ 0.70  
✅ Reasoning explains which pattern was used  
✅ Agency clearly identified (DFARS, NMCARS, AFFARS, etc.)  
✅ No duplicate relationships
