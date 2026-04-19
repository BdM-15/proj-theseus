"""
Deprecated shim — use tools/workspace_cleanup.py instead.

This script now delegates to the full workspace cleanup tool, which handles
both Neo4j graph data and rag_storage files and supports interactive workspace
selection.
"""

import sys
from pathlib import Path

# Forward to the new tool without changing argv
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.workspace_cleanup import main

if __name__ == "__main__":
    main()
