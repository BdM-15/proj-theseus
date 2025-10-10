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
- Local Ollama integration (qwen2.5-coder:7b + bge-m3)

Usage:
    python app.py
    
Then visit: http://localhost:9621
"""

import asyncio
import sys
from pathlib import Path

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
    print("🎯 Starting GovCon Capture Vibe Server...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)