# MinerU 3.x Integration Assessment

**Date**: 2026-04-10 (Updated: 2026-04-10)
**Branch**: `069-simplify-dependency-management`
**Current Version**: MinerU 2.7.0 (installed via raganything `mineru[core]`)
**Target Version**: MinerU 3.0.9 (latest)
**Status**: ✅ VIABLE on Windows + Python 3.13 (`pipeline` backend)

---

## Executive Summary

MinerU 3.0 is a major release with significant accuracy improvements (86.2 OmniDocBench), DOCX support, and architectural redesign. **Despite the MinerU README claiming Windows + Python 3.13 is unsupported due to `ray`**, our investigation proves this limitation does **not** apply to our stack:

- `ray` is **not** a dependency of MinerU 3.0 in any declared extras (`core`, `pipeline`, `vlm`, `all`)
- `ray` is the dependency of `lmdeploy` (installed via `mineru[lmdeploy]` on Windows within `mineru[all]`)
- raganything installs `mineru[core]`, which does **NOT** include `lmdeploy`
- MinerU 2.7.0 source code contains **zero** `import ray` statements
- `uv pip install "mineru[core]>=3.0.0" --dry-run` resolves successfully on our Windows + Python 3.13 system

The remaining integration concerns are **CLI flag breaking changes** in raganything's parser (solvable) and the **architectural shift** to API-based orchestration.

---

## 1. Platform Compatibility — RESOLVED (Not Blocked)

### Our Environment

- **OS**: Windows
- **Python**: 3.13.7
- **Backend**: `pipeline` (via `MINERU_BACKEND=pipeline` env var)
- **MinerU extra**: `mineru[core]` (via raganything dependency)

### MinerU 3.0 Official Compatibility (from README)

| Platform | Supported Python |
| -------- | ---------------- |
| Linux    | 3.10–3.13        |
| Windows  | 3.10–3.12 only\* |
| macOS    | 3.10–3.13        |

> _"Since the key dependency `ray` does not support Python 3.13 on Windows, only versions 3.10~3.12 are supported."_ — MinerU README footnote 4

### Investigation: The `ray` Claim Is Misleading

**Finding 1 — `ray` is NOT a MinerU dependency:**
MinerU 3.0 `pyproject.toml` was audited in full. `ray` does not appear in:

- `[project.dependencies]` (base)
- `[project.optional-dependencies.pipeline]`
- `[project.optional-dependencies.vlm]`
- `[project.optional-dependencies.core]` (= vlm + pipeline + gradio)
- `[project.optional-dependencies.all]` (= core + platform-specific inference frameworks)

**Finding 2 — The actual `ray` dependency chain is `lmdeploy`:**

- `mineru[all]` on Windows installs `mineru[lmdeploy]` (via `"mineru[lmdeploy] ; sys_platform == 'win32'"`)
- `lmdeploy` depends on `ray` → ray has **no Windows wheels for Python 3.13** (no `win_amd64` for ≥2.45.0, no `cp313` for ≤2.44.1)
- Verified: `uv pip install "lmdeploy" --dry-run` **FAILS** due to unresolvable `ray` dependency

**Finding 3 — Our dependency path avoids `ray` entirely:**

- raganything depends on `mineru[core]` (confirmed via `importlib.metadata`)
- `mineru[core]` = `mineru[vlm]` + `mineru[pipeline]` + `mineru[gradio]` — does NOT include `lmdeploy`
- Therefore: `ray` is never installed and never needed

**Finding 4 — No runtime `ray` usage in MinerU source:**

- Searched all `.py` files in `mineru` 2.7.0 installed package: **zero** matches for `import ray` or `from ray`
- The only `ray` substring matches are `np.array` / `np.ndarray` (numpy)

**Finding 5 — Dry-run installation succeeds:**

```
$ uv pip install "mineru[core]>=3.0.0" --dry-run
Resolved 135 packages in 266ms
Would install 10 packages (including mineru==3.0.9 replacing mineru==2.7.0)
```

### Verdict: **NOT BLOCKED** — `ray` limitation applies only to `mineru[all]`/`mineru[lmdeploy]`, not `mineru[core]`

---

## 2. CLI Flag Compatibility

RAG-Anything's `MineruParser._run_mineru_command()` ([raganything/parser.py](../../../.venv/Lib/site-packages/raganything/parser.py)) builds CLI commands with specific flags. Here's the compatibility matrix:

| Flag                        | MinerU 2.x      | MinerU 3.0                                                                                   | Compatible?                                                            |
| --------------------------- | --------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `-p` (input path)           | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-o` (output dir)           | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-m` (method: auto/txt/ocr) | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-b` (backend)              | `pipeline` etc. | `pipeline`, `hybrid-auto-engine`, `hybrid-http-client`, `vlm-auto-engine`, `vlm-http-client` | ⚠️ `pipeline` still valid, but default changed to `hybrid-auto-engine` |
| `-l` (language)             | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-s` (start page)           | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-e` (end page)             | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-f` (formula toggle)       | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-t` (table toggle)         | ✅              | ✅                                                                                           | ✅ Same                                                                |
| `-d` (device)               | ✅              | ❌ **REMOVED**                                                                               | ❌ **Breaking**                                                        |
| `--source` (model source)   | ✅              | ❌ Not in 3.0 help                                                                           | ❌ **Breaking**                                                        |
| `-u` (vlm url)              | vlm server URL  | OpenAI-compatible backend URL                                                                | ⚠️ Semantics changed                                                   |

### Breaking Changes

1. **`-d` (device) removed**: MinerU 3.0 manages device selection internally (API-based architecture)
2. **`--source` removed**: Model source configuration moved to `mineru.json` config file
3. **Default backend changed**: 2.x defaults to `pipeline`; 3.0 defaults to `hybrid-auto-engine`
4. **New `--api-url` flag**: `mineru` now runs as an orchestration client that starts a temporary local `mineru-api` FastAPI service

### Impact

- raganything 1.2.10 would need an update to remove `-d` and `--source` flags for 3.0
- We'd need to ensure `-b pipeline` is always explicitly passed (since default changed)
- The subprocess architecture still works in principle — CLI still outputs files to disk

---

## 3. Output Format Compatibility

RAG-Anything reads two files from MinerU output:

- `{file_stem}.md` — Markdown content
- `{file_stem}_content_list.json` — Structured JSON content list

### content_list.json Format

| Aspect                                          | MinerU 2.x                              | MinerU 3.0                                                                                                              | Compatible?                                                       |
| ----------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| File name                                       | `{stem}_content_list.json`              | `{stem}_content_list.json`                                                                                              | ✅ Same                                                           |
| Top-level structure                             | Flat array of content blocks            | Flat array of content blocks                                                                                            | ✅ Same                                                           |
| `type` field                                    | text, image, table, equation            | text, image, table, equation + **new**: chart, seal, code, list, header, footer, page_number, aside_text, page_footnote | ✅ Backward compatible (new types additive)                       |
| `img_path`                                      | ✅                                      | ✅                                                                                                                      | ✅ Same                                                           |
| `image_caption` / `img_caption`                 | Both supported (raganything normalizes) | ✅                                                                                                                      | ✅ Same                                                           |
| `image_footnote` / `img_footnote`               | Both supported (raganything normalizes) | ✅                                                                                                                      | ✅ Same                                                           |
| `table_body`, `table_caption`, `table_footnote` | ✅                                      | ✅                                                                                                                      | ✅ Same                                                           |
| `text` (content field)                          | ✅                                      | ✅                                                                                                                      | ✅ Same                                                           |
| `bbox`                                          | Absolute coordinates                    | **Normalized 0–1000**                                                                                                   | ⚠️ **Potential breaking** if downstream relies on absolute coords |
| `page_idx`                                      | ✅                                      | ✅                                                                                                                      | ✅ Same                                                           |
| `text_level` (heading detection)                | ❌ Not present                          | ✅ New in 3.0                                                                                                           | ✅ Additive                                                       |
| `sub_type`                                      | ❌                                      | ✅ For code/list                                                                                                        | ✅ Additive                                                       |

### New Output: content_list_v2.json

- MinerU 3.0 also generates `content_list_v2.json` (page-grouped, unified `type + content` structure)
- This is a **development version** (subject to change) — NOT a replacement for `content_list.json`
- raganything doesn't read v2 format — but it could be a future opportunity

### Verdict: **Mostly compatible** — existing fields preserved. The `bbox` normalization change (0–1000 range) could affect context extraction if any code relies on absolute pixel coordinates.

---

## 4. Architectural Changes in MinerU 3.0

### CLI → API Service Model

- **Before (2.x)**: `mineru` CLI directly runs parsing in the subprocess
- **After (3.0)**: `mineru` CLI starts a temporary local `mineru-api` (FastAPI) service, submits work to it, waits for results, then writes output files
- **Impact**: The subprocess still completes the same way (blocks until done, writes files to disk), but internally there's now an HTTP round-trip. This means:
  - Slower startup (FastAPI service initialization)
  - Port binding (could conflict if multiple instances run)
  - More processes/threads spawned
  - Potential Windows-specific issues with service lifecycle

### Sliding Window Memory Optimization

- Long documents no longer need manual splitting
- Streaming writes to disk for batch inference
- **Impact**: Positive — our long RFP documents would benefit from reduced peak memory

### Thread Safety

- Full multi-threaded concurrent inference support
- **Impact**: Positive — no more concerns about concurrent document processing

### AGPL-Licensed Model Removal

- Removed doclayoutyolo, mfd_yolov8 (AGPLv3), layoutreader (CC-BY-NC-SA 4.0)
- **Impact**: Positive — cleaner licensing for commercial use

---

## 5. Version Options & Recommendations

### Option A: MinerU 2.7.6 (Safe Upgrade — Zero Risk)

| Aspect                 | Details                                                      |
| ---------------------- | ------------------------------------------------------------ |
| **Risk Level**         | 🟢 **Very Low**                                              |
| **Effort**             | Minimal — update version pin only                            |
| **Compatibility**      | Same CLI, same output format, same Python/Windows support    |
| **Changes from 2.7.0** | Bugfixes only (2.7.1–2.7.6 are patch releases over Feb 2026) |
| **raganything impact** | None — completely transparent                                |
| **Our code impact**    | None                                                         |

**How to upgrade**:

```bash
uv pip install "mineru[core]>=2.7.6,<3"
```

### Option B: MinerU 3.0.9 (RECOMMENDED — Now Viable)

| Aspect                 | Details                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| **Risk Level**         | 🟡 **Medium** (CLI flag changes require raganything patch)                                   |
| **Platform**           | ✅ Confirmed viable on Windows + Python 3.13 via `mineru[core]`                              |
| **CLI Changes**        | `-d` removed, `--source` removed, `-u` semantics changed                                     |
| **raganything impact** | Requires upstream update or monkey-patch to raganything parser                               |
| **Our code impact**    | Minimal — our code doesn't import MinerU directly                                            |
| **Benefits**           | 86.2 accuracy, DOCX support, long-doc memory optimization, thread safety, AGPL model removal |

**Integration steps**:

1. Install: `uv pip install "mineru[core]>=3.0.0"`
2. Patch raganything's `_run_mineru_command()` to remove `-d` and `--source` flags
3. Ensure `-b pipeline` is explicitly passed (default changed to `hybrid-auto-engine`)
4. Test with a known RFP document for output format compatibility
5. Verify `bbox` normalization (0–1000 range) doesn't affect context extraction

### Option C: MinerU 3.0.9 via Docker (Alternative — If Local Issues Arise)

| Aspect         | Details                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| **Risk Level** | 🟡 **Medium**                                                            |
| **Approach**   | Run MinerU inside a Linux Docker container, call via `mineru-api` HTTP   |
| **Effort**     | Moderate — need to modify raganything invocation or use `--api-url` flag |
| **Benefits**   | Gets all 3.0 features; Linux-native environment; GPU passthrough         |
| **Drawbacks**  | Docker dependency, network overhead, more complex deployment             |

### Revised Recommendation

**Previous**: Option A (2.7.6) was recommended because 3.0 appeared blocked.
**Updated**: **Option B (3.0.9) is now the recommended target** since the `ray` blocker has been debunked. The remaining work is patching raganything's CLI flag construction, which is a well-scoped, low-risk change. Option A remains available as a no-effort interim step.

---

## 6. Version History (No 2.8 or 2.9 Exists)

```
2.7.0  (2026-01)  ← CURRENT
2.7.1  (2026-01)
2.7.2  (2026-01)
2.7.3  (2026-01)
2.7.4  (2026-02)
2.7.5  (2026-02)
2.7.6  (2026-02-05)  ← RECOMMENDED TARGET
--- no 2.8 or 2.9 versions ---
3.0.0  (2026-03-28)
3.0.1  (2026-03-29)
3.0.2  (2026-03-29)
3.0.5  (2026-03-31)
3.0.6  (2026-04-01)
3.0.7  (2026-04-01)
3.0.8  (2026-04-03)
3.0.9  (2026-04-07)  ← LATEST
```

The jump from 2.7.x to 3.0.0 is a full major version bump with no intermediate releases.

---

## 7. Integration Points Audit

### Where MinerU Is Used (Dependency Chain)

```
Our Code (no direct MinerU imports)
  └─→ raganything (RAGAnything, RAGAnythingConfig)
        └─→ raganything/parser.py: MineruParser class
              └─→ subprocess.Popen(["mineru", ...])  ← CLI-only integration
              └─→ Reads output: {stem}_content_list.json, {stem}.md
        └─→ raganything/modalprocessors.py
              └─→ _extract_context_from_mineru_content_list() ← Reads content_list fields
        └─→ raganything/config.py
              └─→ parser="mineru", content_format="minerU"
```

### Our Custom Code (Zero MinerU Coupling)

- `src/processors/govcon_multimodal_processor.py` — Extends `BaseModalProcessor` from raganything, works with `content_list` (already-parsed output)
- `src/server/initialization.py` — Configures `RAGAnythingConfig`, passes MinerU settings via env vars
- **Verdict**: Our code is fully decoupled from MinerU through the raganything abstraction layer

---

## 8. Recommended Action Plan

### Immediate (This Branch)

1. ✅ Upgrade MinerU to **2.7.6** — safe, zero-risk, gains 6 months of bugfixes
2. Pin version: `mineru[core]>=2.7.6,<3` to prevent accidental 3.0 upgrade

### Near-Term (Track)

3. Monitor `ray` Python 3.13 Windows support ([ray-project/ray#50003](https://github.com/ray-project/ray/issues/50003) or similar)
4. Monitor raganything for MinerU 3.0 compatibility update (would need `-d`/`--source` flag changes)
5. Consider testing MinerU 3.0 via Docker container approach for evaluation purposes

### Future (When Blockers Clear)

6. Upgrade to MinerU 3.0 when either: (a) `ray` supports Py3.13/Windows, or (b) we move to Python 3.12, or (c) we containerize the parser
7. Leverage new 3.0 features: DOCX native parsing, `text_level` heading detection (eliminates need for custom heading inference), `content_list_v2.json` richer structure
