# Project Ariadne

**Official Workspace Guide**

**Project Name:** Project Ariadne  
**Tagline:** The Golden Thread - Full-Lifecycle Federal Capture Management Platform  
**Core Engine Inside It:** Theseus RFP Navigator  
**Mythos Theme:** Ariadne gives Theseus the thread to navigate the labyrinth.

**Theseus** = your existing RFP processor (Shipley Phases 4-6)  
**Ariadne** = the broader platform (Shipley Phases 0-6)

## 1. Vision

Project Ariadne turns your current Theseus repo into a complete, GovDash-inspired capture command center:

- Early-phase intel capture (calls, conferences, emails) -> LLM Wiki synthesis
- Editable, versioned knowledge base so you can edit or delete intel without reprocessing RFPs
- Pursuit pipeline dashboard with Shipley decision gates
- Unified chat and agent orchestration
- Live graph visualization
- Theseus RFP Navigator remains untouched and powerful

All of it is intended to be 100% free, local, and built in VS Code plus Obsidian.

## 2. Repo Structure After Reorganization

```text
govcon-capture-vibe/              <- Root repo (you can rename to project-ariadne later)
├── theseus/                      <- ALL your existing Theseus code moved here
│   ├── src/
│   ├── LightRAG WebUI, MinerU, ontology, API, etc.
│   └── (everything that was in the root before)
├── ariadne/                      <- New Ariadne platform layer
│   ├── theseus-wiki/
│   │   ├── raw/                  <- Drop raw notes, voice transcripts, emails
│   │   ├── wiki/                 <- LLM Wiki outputs clean .md pages
│   │   └── ontology.md           <- Copy your 33-entity schema here
│   ├── theseus-superapp.py       <- Streamlit dashboard (GovDash + Shipley style)
│   ├── synthesize_intel.py       <- LLM Wiki synthesizer script
│   ├── pursuits.db.sql           <- Postgres pipeline table
│   └── README-ariadne.md         <- Optional extra notes
├── README.md                     <- This file
├── .env                          <- Shared (Grok keys, embeddings, etc.)
└── requirements-ariadne.txt      <- Additional deps
```

### One-Time Reorganization Steps

1. Create the `theseus/` folder and move all existing files and folders into it.
2. Create the `ariadne/` folder and the subfolders above.
3. Update any internal imports and paths in `theseus/` as needed. This will usually affect Dockerfiles and config files.
4. Commit with message: `Reorg: Theseus subfolder + Ariadne platform layer`

## 3. Quick-Start Setup

Run this in the VS Code terminal:

```bash
cd govcon-capture-vibe
pip install -r ariadne/requirements-ariadne.txt
```

Create `ariadne/requirements-ariadne.txt` with:

```text
streamlit
psycopg2-binary
pyvis
langgraph
```

## 4. Core Daily Instructions

### A. Add New Capture Intel (Phases 0-3)

- Paste notes, voice transcripts, emails, or PDFs into `synthesize_intel.py`
- It uses your domain ontology plus an LLM Wiki pattern to create clean, linked Markdown
- It automatically performs incremental insert into LightRAG so only the new file is added

### B. Edit or Remove Intel (Customer Changes Direction)

- Open the specific `.md` file in `ariadne/theseus-wiki/wiki/`
- Edit or delete it
- Commit the change in Git for full history
- Run `lightrag.delete_by_doc_id("filename.md")` so only that piece updates

### C. Visualization

- Open `ariadne/theseus-wiki/` in the free Obsidian app for an interactive graph of all intel plus ontology links
- Or use a VS Code Obsidian Graph View extension

### D. Launch the Full Ariadne Dashboard

```bash
streamlit run ariadne/theseus-superapp.py
```

Expected tabs:

- Pipeline Dashboard: Shipley gates, PWin, status
- Capture Intel: one-click synthesis
- Pursuit Detail: per-pursuit chat, graph, and gate notes
- Theseus RFP Navigator: direct link to your existing WebUI

## 5. Next Steps

Do these today:

1. Reorganize the repo as shown above.
2. Copy this entire README into the root `README.md`.
3. Reply with exactly one of these:

```text
paste synthesize_intel.py
paste theseus-superapp.py
paste pursuits.db.sql
```

We will build the scripts together inside this workspace. Every future message that starts with `Project Ariadne workspace` will stay in context.
