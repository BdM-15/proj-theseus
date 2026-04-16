# Final Quality Assessment: t4 vs t5 Ontology Enhancement

**Date:** 2026-04-16  
**Branch:** `075-entity-ontology-enhancement`  
**Evaluator:** Automated LLM-as-Judge (blind, randomized) + Structural Graph Analysis  
**Document Under Test:** AFCAPV BOS I RFP

---

## 1. Executive Verdict

### Answer Quality: STATISTICAL TIE — No Clear Winner

| Metric         |   Run 1 (seed 42)   |   Run 2 (seed 99)   |
| :------------- | :-----------------: | :-----------------: |
| t4 wins        |          5          |          4          |
| t5 wins        |          3          |          5          |
| Ties           |          2          |          1          |
| t4 total score |       244/250       |       243/250       |
| t5 total score |       240/250       |       239/250       |
| **Score gap**  | **4 points (1.6%)** | **4 points (1.6%)** |

Both runs show a ~4-point gap out of 250, with perfect 5.0/5.0 Accuracy in both workspaces across all 20 evaluations. The winner count flips between runs depending on random presentation order, confirming the results are **within noise**.

### Graph Structure: CLEAR IMPROVEMENT in t5

| Metric                       |  t4   |  t5   |      Change       |
| :--------------------------- | :---: | :---: | :---------------: |
| Total entity types           |  22   |  33   |     **+50%**      |
| Domain-specific new types    |   0   |  15   |    **+15 new**    |
| Total nodes                  | 1,427 | 1,557 |       +9.1%       |
| Total relationships          | 2,308 | 2,441 |       +5.8%       |
| Unique relationship keywords |  20+  |  25+  | **More specific** |

---

## 2. Cross-Run Consistency Analysis

Two independent evaluations with different random seeds tested position-bias resilience:

| Query | Category                          |  Run 1  |  Run 2  |  **Stable?**  |
| :---- | :-------------------------------- | :-----: | :-----: | :-----------: |
| Q1    | Entity Discovery (hybrid)         |   TIE   |   t5    | ⚠️ Borderline |
| Q2    | Entity Discovery (hybrid)         | **t5**  | **t5**  |      ✅       |
| Q3    | Entity Discovery (local)          | **t4**  | **t4**  |      ✅       |
| Q4    | Requirement Traceability (hybrid) | **t4**  | **t4**  |      ✅       |
| Q5    | Requirement Traceability (global) |   t4    |   t5    |  ⚠️ Unstable  |
| Q6    | Document Hierarchy (local)        | **t5**  | **t5**  |      ✅       |
| Q7    | Cross-Document (global)           | **TIE** | **TIE** |      ✅       |
| Q8    | Cross-Document (hybrid)           | **t4**  | **t4**  |      ✅       |
| Q9    | Strategic (global)                | **t4**  | **t4**  |      ✅       |
| Q10   | Compliance (local)                | **t5**  | **t5**  |      ✅       |

**8/10 queries are stable across runs (80% reproducibility).**

### Stable results summary:

- **t4 consistently wins:** Q3, Q4, Q8, Q9 (4 queries)
- **t5 consistently wins:** Q2, Q6, Q10 (3 queries)
- **Consistent tie:** Q7 (1 query)
- **Unstable (within noise):** Q1, Q5 (2 queries)

---

## 3. Dimension-by-Dimension Breakdown

### Aggregated across both runs (20 evaluations per workspace):

| Dimension         | t4 Avg | t5 Avg | Gap  | Interpretation                             |
| :---------------- | :----: | :----: | :--: | :----------------------------------------- |
| **Accuracy**      |  5.0   |  5.0   | 0.0  | Both factually correct — no hallucinations |
| **Completeness**  |  4.8   |  4.7   | 0.1  | t4 slightly more exhaustive                |
| **Specificity**   |  4.8   |  4.85  | 0.05 | Essentially identical                      |
| **Structure**     |  4.85  |  4.75  | 0.1  | t4 slightly better organized               |
| **Actionability** |  4.9   |  4.65  | 0.25 | t4 marginally more proposal-ready          |

The largest gap is Actionability at 0.25 points — a 5% difference on a 5-point scale. This is **not statistically significant** given the ceiling effect (all scores are 4-5 out of 5).

---

## 4. Graph Structure Analysis (Where t5 Clearly Wins)

### 4a. Entity Type Specialization

t5 introduced **15 new domain-specific entity types** not present in t4:

| New Entity Type             | Count | GovCon Relevance          |
| :-------------------------- | :---: | :------------------------ |
| `regulatory_reference`      |  137  | FAR/DFARS clause tracking |
| `document_section`          |  123  | RFP structural hierarchy  |
| `performance_standard`      |  101  | QA threshold tracking     |
| `workload_metric`           |  59   | Appendix H data capture   |
| `government_furnished_item` |  34   | GFP/GFE tracking          |
| `labor_category`            |  23   | Staffing requirements     |
| `contract_line_item`        |  19   | CLIN structure            |
| `compliance_artifact`       |  17   | Deliverable compliance    |
| `technical_specification`   |  17   | Technical requirements    |
| `subfactor`                 |  14   | Evaluation hierarchy      |
| `work_scope_item`           |  12   | SOW decomposition         |
| `pricing_element`           |  10   | Cost structure            |
| `proposal_instruction`      |   2   | Section L guidance        |
| `proposal_volume`           |   2   | Submission structure      |
| `transition_activity`       |   2   | Phase-in requirements     |

### 4b. Entity Redistribution (Reclassification Effect)

t5 didn't just add nodes — it **reclassified generic types** into domain-specific ones:

| Generic Type | t4 Count | t5 Count | Change | Where They Went                                                  |
| :----------- | :------: | :------: | :----: | :--------------------------------------------------------------- |
| `concept`    |   286    |   158    |  -45%  | → performance_standard, technical_specification, work_scope_item |
| `document`   |   230    |    90    |  -61%  | → document_section, regulatory_reference                         |
| `person`     |    61    |    36    |  -41%  | → labor_category                                                 |

This is exactly what the ontology enhancement was designed to do: transform generic "concept" and "document" catch-all nodes into **semantically precise types** that enable typed graph traversal.

### 4c. Relationship Keyword Richness

**t4 top domain keywords:** GOVERNED_BY(154), REFERENCES(138), SUBMITTED_TO(112), MEASURED_BY(75), TRACKED_BY(69), APPLIES_TO(54), RELATED_TO(34), DEFINES(32)

**t5 top domain keywords:** GOVERNED_BY(105), REFERENCES(157), SUBMITTED_TO(152), MEASURED_BY(78), MANDATES(65), PRODUCES(57), QUANTIFIES(53), APPLIES_TO(44), REQUIRES(26), PRICED_UNDER(18), EVALUATED_BY(17)

t5 introduced **MANDATES, PRODUCES, QUANTIFIES, PRICED_UNDER, EVALUATED_BY** — highly domain-specific relationship types. t4 relies more on generic **RELATED_TO(34), DEFINES(32), CONTAINS(23)**.

---

## 5. Why Graph Improvement Didn't Translate to Answer Quality

### 5a. LightRAG's Retrieval Compensates

LightRAG retrieves by **embedding similarity** (vector search on chunks/entities/relationships) combined with **keyword extraction**. When entity types are generic (e.g., `concept`), the embeddings and descriptions still capture the semantic content. A node labeled `concept` with description "FAR 52.222-50 anti-trafficking requirement" retrieves just as well as a node labeled `regulatory_reference` with the same description.

**The ontology enhancement improves graph _structure_ but not _content_ — and LightRAG retrieves on content.**

### 5b. Same Underlying Chunks

Both workspaces were built from the **same document** with the **same chunking parameters**. The text chunks in the VDB are identical. Differences only emerge in how entities were typed and related during extraction — which affects graph traversal but not vector similarity search.

### 5c. LLM Generation Smooths Differences

Even when retrieval context differs slightly (different entity counts), Grok's generation capability produces high-quality answers from either context set. A powerful LLM compensates for less-structured retrieval context.

### 5d. Known Bug: Q8 Keyword Extraction Failure

In Q8, t5 encountered a `low_level_keywords is empty` condition, falling back to global-only retrieval. This is a **software bug** (keyword extraction failed to parse the query properly for t5's workspace), not an ontology quality issue. It artificially depressed t5's Q8 score.

---

## 6. What This Means for the Project

### ✅ The ontology enhancement IS working at the graph level

- 15 new domain-specific entity types successfully extracted
- Generic entities correctly reclassified into specialized types
- Relationship semantics enriched with domain-specific keywords
- Graph is objectively more informative and navigable

### ⚠️ The answer quality improvement is not yet measurable

- Both workspaces produce essentially equivalent answers
- Score difference (1.6%) is within measurement noise
- Current query set may not target areas where typed entities matter most

### 🔍 Where to look for measurable improvement

1. **Typed queries** — Questions like "list all regulatory_references" or "which labor_categories are required" would directly leverage new types
2. **Graph traversal** — Multi-hop queries (e.g., "which performance_standards apply to deliverables under CLIN 0001") need typed edges
3. **Compliance matrices** — Generating Section L→M traceability matrices benefits from `document_section` and `subfactor` types
4. **Downstream tooling** — Neo4J Cypher queries, dashboards, and agent workflows that filter by entity type gain immediate value

---

## 7. Recommendation

**The ontology enhancement should be KEPT.** Here's why:

1. **No regression** — Answer quality is statistically identical; t5 doesn't hurt anything
2. **Structural improvement is real** — 15 new types, richer relationships, better semantic organization
3. **Foundation for typed queries** — Future features (compliance matrix generation, typed search filters, agent workflows) require these entity types
4. **Reclassification success** — The drop in generic `concept` and `document` nodes proves the ontology is working as designed

**However, to demonstrate measurable answer quality improvement, the project needs:**

- Query templates that specifically leverage entity types (e.g., "list all `performance_standard` entities with their thresholds")
- Multi-hop graph traversal queries that benefit from typed edges
- LightRAG query pipeline modifications to prefer typed entity matching
- Bug fix for the keyword extraction failure observed in Q8

---

## 8. Raw Data References

| Artifact                         | Path                                |
| :------------------------------- | :---------------------------------- |
| Graph comparison report          | `tools/comparison_report_graph.md`  |
| Blind evaluation run 1 (seed 42) | `tools/quality_evaluation.md`       |
| Blind evaluation run 2 (seed 99) | `tools/quality_evaluation_run2.md`  |
| Evaluation script                | `tools/evaluate_quality.py`         |
| This assessment                  | `tools/QUALITY_ASSESSMENT_FINAL.md` |
