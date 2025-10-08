# 🚀 Quick Handoff Summary — Branch 004 (Performance-Based Refactoring)

Date: October 7, 2025
Branch: 004-code-optimization
Status: Planning complete (non‑prescriptive charter), ready for baseline + iterations

---

## What matters in this branch

We will optimize the codebase under strict, non‑prescriptive constraints. No architecture is mandated in advance. The only source of truth for requirements is the charter:

- Document: docs/BRANCH_004_CODE_OPTIMIZATION.md (Performance‑Based Refactoring Charter)
- Principle: No code bloat, no vestige patterns, no uniqueness/complexity for its own sake
- Behavior: Preserve external behavior; keep runtime non‑regression

Rely on upstream libraries instead of reinventing:
- LightRAG: https://github.com/HKUDS/LightRAG
- RAG‑Anything: https://github.com/HKUDS/RAG-Anything/tree/main

Do not introduce invasive changes that diverge from these libraries unless it clearly reduces net code and complexity and keeps behavior intact.

---

## Non‑prescriptive constraints (from the charter)

- Net LOC (src/ + app entrypoint) ≤ baseline; target negative delta
- No increases in startup time, steady‑state memory, or p95 latency on critical endpoints
- No breaking API/output changes
- Avoid new heavy dependencies unless they reduce net code and maintenance

---

## Quick start for the next conversation

1) Verify branch
```powershell
git branch  # should show: * 004-code-optimization
```

2) Read the charter
- Open docs/BRANCH_004_CODE_OPTIMIZATION.md

3) Establish a tiny baseline (keep it simple)
- Count LOC for src/ and app entrypoint
- Start the app; record time‑to‑ready and steady RSS
- Hit /health and one representative query; record p95 (very small sample OK for baseline)

4) Propose the first minimal change
- Example: delete obvious dead code, collapse redundant helpers, remove unused imports
- State expected effect (e.g., “-150 LOC, no runtime impact”)

5) Implement → re‑measure → commit (atomic)
- If any metric regresses, reduce scope or revert

First question to ask in the new conversation:
“Baseline captured. Here are the numbers (LOC/startup/p95/memory). Proposing the smallest change X with expected impact Y. Proceed?”

---

## Critical rules

- Activate venv before Python commands
```powershell
.venv\Scripts\Activate.ps1
```

- Use workspace tools for file ops (not PowerShell)
- Prefer deletion and simplification over new abstractions
- Maximize reuse of LightRAG / RAG‑Anything; avoid uniqueness/complexity

---

## Deliverables (lightweight)

- Short commit messages with impact notes (e.g., “-220 LOC; same p95 /health”)
- Optional tiny scripts for measurements (kept minimal)
- Brief PR summary comparing baseline vs final metrics

---

This summary intentionally avoids prescribing structure or modules. The implementing agent should choose the most effective minimal path to meet the charter’s constraints while leveraging upstream libraries and avoiding invasiveness.
