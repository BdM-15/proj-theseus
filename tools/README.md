# Utility Tools

Helper scripts for managing and testing the GovCon Capture Vibe system.

## Quick Reference

### Production Tools

**`clear_neo4j.py`** - Clear Neo4j workspace for fresh testing

```powershell
python tools/clear_neo4j.py              # Clear current workspace
python tools/clear_neo4j.py --list       # List all workspaces
python tools/clear_neo4j.py --workspace NAME  # Clear specific workspace
```

**`assess_quality.py`** - Analyze Neo4j data quality

```powershell
python tools/assess_quality.py
```

Shows:

- Entity/relationship counts
- Type distributions
- Correction statistics
- Sample inferred relationships
- Quality metrics

**`check_neo4j_props.py`** - Inspect Neo4j node properties

```powershell
python tools/check_neo4j_props.py
```

Useful for debugging property name issues.

---

## Testing Workflow

**Before each test:**

```powershell
# 1. Clear Neo4j workspace
python tools/clear_neo4j.py

# 2. Upload RFP via WebUI (http://localhost:9621/webui)

# 3. Assess quality
python tools/assess_quality.py
```

**Quick validation (no document upload needed):**

```powershell
# Run from project root
python test_neo4j_quick.py
```

---

## When to Use Each Tool

| Tool                   | Use When            | Time    |
| ---------------------- | ------------------- | ------- |
| `clear_neo4j.py`       | Starting fresh test | 5 sec   |
| `assess_quality.py`    | After processing    | 10 sec  |
| `check_neo4j_props.py` | Debugging schema    | 2 sec   |
| `test_neo4j_quick.py`  | Verify system works | 2-5 min |

---

## Installation

These tools are already configured and ready to use. They:

- Auto-load `.env` configuration
- Connect to Neo4j using project settings
- Work with workspace isolation

No additional setup needed!
