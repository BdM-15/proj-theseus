"""
GovCon Capture Vibe - RFP Analysis Tool

Startup script for the extended LightRAG server with government contracting features.
Replaces the previous Streamlit interface with a professional React-based WebUI
that includes custom RFP analysis capabilities grounded in Shipley methodology.

Features:
- Document processing with LightRAG knowledge graphs
- Requirements extraction and compliance matrices
- Gap analysis using Shipley Capture Guide methods
- Professional React WebUI with custom RFP components

Usage:
    python app.py
    
This will:
1. Start GovCon RAG server (LightRAG WebUI + RAG-Anything ingestion)
    
Then visit: http://localhost:9621
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# ═══════════════════════════════════════════════════════════════════════════════
# CRITICAL: Load .env and set LLM_TIMEOUT BEFORE any LightRAG imports!
# LightRAG reads LLM_TIMEOUT at class definition time (dataclass field default).
# If we import LightRAG first, the timeout is locked to 180s regardless of
# what we set later. This caused "Worker execution timeout after 360s" errors.
# ═══════════════════════════════════════════════════════════════════════════════
from dotenv import load_dotenv
load_dotenv()

# Set LLM_TIMEOUT before LightRAG imports (default: 300s → worker timeout ~600s)
# This prevents timeout failures on large RFP chunks during entity extraction.
if not os.getenv("LLM_TIMEOUT"):
    os.environ["LLM_TIMEOUT"] = "300"

# Enforce chunking + query defaults BEFORE LightRAG imports.
# These must be set early because LightRAG reads env defaults at import time.
os.environ.setdefault("CHUNK_SIZE", "8192")
os.environ.setdefault("CHUNK_OVERLAP_SIZE", "1200")

# CRITICAL: Disable reranking everywhere (project requirement).
# LightRAG defaults enable_rerank via RERANK_BY_DEFAULT=true.
os.environ.setdefault("RERANK_BY_DEFAULT", "false")

logger = logging.getLogger(__name__)


# Import LightRAG and RAG-Anything from pip BEFORE adding src to path
# This prevents any old fork from shadowing the pip package
from raganything import RAGAnything
from lightrag.api.lightrag_server import create_app as _verify_lightrag_import

# NOW add src to Python path for our custom server module
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import our RAG-Anything server (RAG-Anything is built on top of LightRAG)
from raganything_server import main


if __name__ == "__main__":
    # ANSI color codes for PowerShell
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'
    
    print(f"""
{CYAN}{'═' * 65}{RESET}
  {YELLOW}██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗{RESET}
  {YELLOW}██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝{RESET}
  {YELLOW}██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║{RESET}
  {YELLOW}██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║{RESET}
  {YELLOW}██║     ██║  ██║╚██████╔╝╚██████╔╝███████╗╚██████╗   ██║{RESET}
  {YELLOW}╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝   ╚═╝{RESET}

  {YELLOW}████████╗██╗  ██╗███████╗███████╗███████╗██╗   ██╗███████╗{RESET}
  {YELLOW}╚══██╔══╝██║  ██║██╔════╝██╔════╝██╔════╝██║   ██║██╔════╝{RESET}
  {YELLOW}   ██║   ███████║█████╗  ███████╗█████╗  ██║   ██║███████╗{RESET}
  {YELLOW}   ██║   ██╔══██║██╔══╝  ╚════██║██╔══╝  ██║   ██║╚════██║{RESET}
  {YELLOW}   ██║   ██║  ██║███████╗███████║███████╗╚██████╔╝███████║{RESET}
  {YELLOW}   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝{RESET}

  {MAGENTA}Government Contracting Intelligence Platform{RESET}
  {DIM}Ontology-Based RAG for Federal RFP Analysis{RESET}
{CYAN}{'═' * 65}{RESET}
""")
    
    # Now initialize logging (after banner is displayed)
    from src.utils.logging_config import setup_logging
    log_info = setup_logging(
        log_level="INFO",
        log_dir="logs",
        max_file_size=10 * 1024 * 1024,  # 10MB per file
        backup_count=5,  # Keep 5 backup files per log
        console_output=True  # Also show in terminal (filtered)
    )
    try:
        # Start the RAG server
        print("🚀 Starting GovCon RAG Server...\n")
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)