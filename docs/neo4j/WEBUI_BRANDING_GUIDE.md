# WebUI Branding Customization

## Overview

LightRAG 1.4.9.7 provides **custom title and description** for the WebUI via environment variables.

---

## Configuration

**Environment Variables in `.env`:**

```bash
# WebUI Branding (LightRAG 1.4.9.7+)
WEBUI_TITLE=Project Theseus
WEBUI_DESCRIPTION=Government Contracting Intelligence Platform - Navigate the labyrinth of federal RFPs
```

**Result:**

- WebUI header displays: `LightRAG | Project Theseus`
- Tooltip appears on hover: "Government Contracting Intelligence Platform - Navigate the labyrinth of federal RFPs"
- Custom title persists across all WebUI tabs (Documents, Knowledge Graph, Retrieval, API)
- Login page shows custom title

**Server Restart Required:** Yes - changes take effect when you restart `python app.py`

---

## Usage

**Start Server:**

```powershell
python app.py
```

**Verify Branding:**

1. Open: http://localhost:9621/webui
2. Header should show: `LightRAG | Project Theseus`
3. Hover over "Project Theseus" to see tooltip with full description

---

**Last Updated:** Branch 013 - Neo4j Integration (November 2025)
