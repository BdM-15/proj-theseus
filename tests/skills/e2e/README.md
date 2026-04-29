# Skills E2E Test Harness

End-to-end validation that each skill's tool-calling loop completes against a real workspace + real LLM, captures a transcript, and emits artifacts where declared.

## What this harness proves

- Tool loop completes without exception (`finish_reason != "error"`).
- Transcript records ≥1 KG retrieval call (`kg_chunks` / `kg_query` / `kg_entities`).
- Final response cites ≥1 chunk identifier (`chunk-[0-9a-f]{4,}`).
- For skills declaring `metadata.deliverable`, an artifact file lands under `skill_runs/<skill>/<run_id>/artifacts/`.

## What this harness does NOT prove

- That the response prose is _accurate_ (subjective; that's branch 147 grounding-ratio audit).
- That the Studio UI download/edit loop works (branch 148 manual + Playwright).

## Running

This harness is double-gated to keep CI / fresh clones from failing:

1. `RUN_SKILL_E2E=1` env var must be set.
2. Theseus server must be reachable on `THESEUS_E2E_BASE_URL` (default `http://127.0.0.1:9621`).
3. The active workspace on that server must be `afcap5_adab_iss` (or override via `THESEUS_E2E_WORKSPACE`).

### Local run

```powershell
# Terminal 1 — start server pointed at the e2e fixture workspace
$env:WORKSPACE_NAME = "afcap5_adab_iss"
$env:WORKING_DIR = "./rag_storage/afcap5_adab_iss"
python app.py

# Terminal 2 — run the harness
$env:RUN_SKILL_E2E = "1"
.\.venv\Scripts\python.exe -m pytest tests/skills/e2e -v
```

## Why HTTP and not in-process

Booting LightRAG in-process pulls in MinerU, the OpenAI embedding client, the xAI LLM client, and the full route layer with its closure-captured slice/retrieve helpers. Hitting the running server via HTTP exercises the **same stack a real user invokes** — including the `/api/ui/skills/{name}/invoke` endpoint, runtime-mode dispatch, transcript persistence, and artifact registry. Lower coupling, higher fidelity.

## Why `afcap5_adab_iss`

It is the AFCAP V FOPR (FA8051-26-R-1002) for Al Dhafra Air Base (UAE) Installation Support Services. The workspace is fully processed locally (4 source PDFs/XLSX — Amend 4 FOPR + PWS + CLIN price schedule + 1 attachment, 125 chunks, 2,087 entities, 4,615 relationships). It is a real, format-rich federal solicitation small enough that each skill's LLM tool loop completes in well under a minute against Grok. The vdb stores total ~165 MB and cannot be checked into git, so this harness is a **developer-machine validation tool**, not a CI gate. Branch 146 (`skill-creator-reverify-pass`) and branch 147 (`renderers-grounding-audit`) both depend on running this harness once locally to record per-skill baselines.

## Cost

Real Grok calls. Rough estimate per full run (11 skills × ~3 turns × ~5K tokens) ≈ 150K input tokens. Run sparingly.
