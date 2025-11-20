import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.inference.semantic_post_processor import enhance_knowledge_graph, _call_llm_async

async def main():
    # 1. Determine Workspace
    rag_storage_path = Path("rag_storage")
    if not rag_storage_path.exists():
        print("❌ rag_storage directory not found!")
        return

    workspaces = [d.name for d in rag_storage_path.iterdir() if d.is_dir()]
    
    print("\nAvailable Workspaces:")
    for i, ws in enumerate(workspaces):
        print(f"{i+1}. {ws}")
    
    choice = input("\nSelect workspace number (or press Enter for 'afcapv_adab_iss_2025_pwstst'): ")
    
    if choice.strip() == "":
        workspace = "afcapv_adab_iss_2025_pwstst"
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(workspaces):
                workspace = workspaces[idx]
            else:
                print("❌ Invalid selection.")
                return
        except ValueError:
            print("❌ Invalid input.")
            return

    print(f"\n🚀 Starting Enrichment for Workspace: {workspace}")
    
    # 2. Set Environment Variables for Neo4jGraphIO
    os.environ["NEO4J_WORKSPACE"] = workspace
    os.environ["GRAPH_STORAGE"] = "Neo4JStorage"
    
    # 3. Run Enhancement
    try:
        stats = await enhance_knowledge_graph(
            rag_storage_path=str(rag_storage_path),
            llm_func=_call_llm_async,
            batch_size=50
        )
        
        print("\n✅ Enrichment Complete!")
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
