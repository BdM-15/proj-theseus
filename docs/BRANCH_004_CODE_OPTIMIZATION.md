# Branch 004: Performance-Based Refactoring Charter

Branch: 004-code-optimization
Parent: main (post-Branch 003 merge)
Created: October 7, 2025
Status: ACTIVE – Requirements defined; solution intentionally not prescribed

This document intentionally avoids prescribing any specific architecture, file layout, or patterns. The goal is to optimize the codebase under explicit performance, size, and maintainability constraints without drawing inspiration from prior “vestige” structures or historical commits.

## Purpose

Set non-prescriptive, measurable requirements for code optimization that prevent code bloat, ensure a fresh approach, and preserve or improve runtime behavior. Solutions are left to the implementing agent, provided they satisfy the constraints and acceptance criteria below.

## Scope

In-scope:
- Reduce code footprint (net) while maintaining or improving clarity and performance
- Remove dead/duplicate code and unnecessary abstractions
- Improve readability and testability without expanding overall complexity
- Preserve current external behavior (APIs, outputs, CLI)

Out-of-scope (for this branch):
- New features or functional changes
- PostgreSQL integration or storage changes
- RAG-Anything or multimodal extensions

## Hard Constraints and Guardrails

1) No code bloat, fresh look only
- Do not replicate old patterns or structures from prior commits; do not “mirror” historical layouts
- Prefer deletion over abstraction if it reduces complexity and lines of code
- Avoid gratuitous layering, over-modularization, or speculative abstractions

2) Net footprint budgets (measured on src/ and app entrypoint)
- Net LOC across src/ and app entrypoint must not increase; target a negative delta
- New files permitted only if total LOC decreases or complexity measurably improves
- New third‑party dependencies must reduce net code and complexity to be justified

3) Complexity and readability budgets
- Maintain or lower cyclomatic complexity per function/file (where measurable)
- Keep import graph depth flat or reduced; avoid deep dependency chains
- Prefer simple, cohesive units over many tiny wrappers

4) Runtime non‑regression
- Startup: time-to-ready must not increase
- Memory: steady-state RSS must not increase
- p95 endpoint latency for critical paths (e.g., health, query) must not increase

5) API/behavior stability
- No breaking changes to public endpoints or documented outputs
- Log levels and messages may be simplified, but not removed if relied upon by tooling

6) Security/ops hygiene
- No hard-coded secrets; keep .env.example authoritative
- Retain the project’s rule: activate .venv before Python invocations

## Measurement Plan (lightweight)

Baseline (before changes), then after each batch of changes capture:
- Static:
  - Net LOC (src/ and app entrypoint)
  - File count and average file size
  - Import graph depth (qualitative or using a simple script)
- Runtime (local dev baseline is acceptable):
  - Startup time: app launch to “ready” log
  - p95 latency: minimal hit on /health and one representative query
  - Memory: steady-state RSS after idle

Tooling notes:
- Favor tiny, scriptable measurements over new frameworks
- Avoid adding heavy profiling dependencies; keep instrumentation minimal

## Working Method

Operate in short, measurable iterations:
1) Propose a minimal change with expected impact (e.g., remove duplication in X; inline helper in Y)
2) Implement the smallest viable change
3) Re-measure metrics above; if any non-regression fails, revert or further minimize
4) Commit with a one-line impact note (e.g., “-420 LOC, same startup, -5% p95 /health”)

Decision principles (ordered):
1) Delete unused or redundant code
2) Simplify control flow; collapse indirection where it doesn’t pay for itself
3) Prefer configuration or data over code, when it materially reduces LOC/complexity
4) Consolidate similar logic rather than creating new layers
5) Only extract functions/modules if it lowers net LOC or increases clarity measurably

## Acceptance Criteria

All must be satisfied for this branch to complete:
- Net LOC Δ in src/ and app entrypoint ≤ 0 (preferably < 0)
- p95 latency: no increase on critical endpoints (health, representative query)
- Startup time: no increase
- Memory steady-state: no increase
- No API/behavior regressions; smoke tests pass (server starts, /health OK)
- No new heavy dependencies unless they clearly reduce net code and maintenance burden

## Deliverables

- Short change log in commits summarizing deltas (LOC, key metrics)
- Optional tiny scripts used for measurements (kept minimal and documented)
- Brief summary in a PR description: baseline vs. final numbers and notable deletions/simplifications

## Handoff for Implementation Agent (next conversation)

Start by establishing a baseline with tiny, local measurements (LOC, file count, startup, p95 for /health and a representative query, steady RSS). Propose the first minimal deletion/simplification with expected impact. Implement, re-measure, and iterate until budgets are met with a clearly negative net LOC and non-regressed runtime metrics. Avoid any reliance on prior commit structures; favor fresh, smallest-necessary changes.

Notes:
- Keep changes reversible and atomic; commit after each green iteration
- Prefer fewer, higher-quality improvements over sweeping rewrites
