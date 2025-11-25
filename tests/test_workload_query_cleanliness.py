import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.server.initialization import initialize_raganything, get_rag_instance
from src.core.prompt_loader import load_prompt
from lightrag.api.config import global_args

async def test_workload_query():
    load_dotenv()
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Set the working directory to the root rag_storage
    # RAGAnything will append the WORKSPACE name to this path
    rag_storage_root = os.path.join(project_root, "rag_storage")
    global_args.working_dir = rag_storage_root
    
    # Override the WORKSPACE environment variable to target the DFAC workspace
    # This tells RAGAnything which subfolder to use
    target_workspace_name = "afcapv_adab_dfac_2025"
    os.environ["WORKSPACE"] = target_workspace_name
    
    print(f"Targeting workspace: {target_workspace_name} in {rag_storage_root}")
    
    # Initialize RAG
    await initialize_raganything()
    rag = get_rag_instance()
    
    # Load the fixed prompt
    prompt_template = load_prompt("user_queries/workload_analysis")
    
    # Construct a query
    query = "Provide me a total list of workload drivers for the dining facility."
    
    # Use LightRAG's aquery directly to avoid event loop issues
    # "Mix" mode in WebUI usually corresponds to "hybrid" in the API
    
    print(f"Running query in 'hybrid' mode with prompt injection...")
    
    response = await rag.aquery(
        query, 
        mode="hybrid",
        user_prompt=prompt_template
    )
    
    print("Response:")
    print(response)
    
    # Check for contamination
    contamination_markers = [
        "95%", "98%", "100%", "99.9%", 
        "Acceptable Quality Level", "AQL",
        "threshold", "standard"
    ]
    
    found_contamination = []
    for marker in contamination_markers:
        if marker in response:
            found_contamination.append(marker)
            
    if found_contamination:
        print(f"\n❌ FAILURE: Found performance metrics in workload list: {found_contamination}")
    else:
        if "[no-context]" in response:
             print("\n⚠️ WARNING: No context found. Test may be inconclusive if no data was retrieved.")
        else:
             print("\n✅ SUCCESS: Response is clean of performance metrics")

if __name__ == "__main__":
    asyncio.run(test_workload_query())
