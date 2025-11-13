"""
Test Workload Analysis User Query Prompt
========================================

Tests the workload_analysis.md user query prompt with LightRAG to validate
the query interface returns properly formatted workload intelligence.

This complements test_workload_query.py (Neo4j direct) by testing the
LightRAG query path that end users will actually use.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv


async def test_workload_user_query():
    """Test workload analysis via LightRAG user query prompt."""
    load_dotenv()
    
    # Import LightRAG and components
    try:
        from lightrag import LightRAG, QueryParam
    except ImportError:
        print("❌ LightRAG not installed. Install with: pip install lightrag-hku")
        return False
    
    # Load workload analysis prompt
    prompt_path = Path("prompts/user_queries/workload_analysis.md")
    if not prompt_path.exists():
        print(f"❌ Prompt not found: {prompt_path}")
        return False
    
    user_prompt = prompt_path.read_text(encoding='utf-8')
    
    print(f"\n{'='*80}")
    print(f"🏗️  WORKLOAD ANALYSIS USER QUERY TEST")
    print(f"{'='*80}")
    print(f"\nPrompt: {prompt_path}")
    print(f"Prompt size: {len(user_prompt)} chars")
    
    # Initialize LightRAG
    working_dir = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")
    working_dir_path = f"./rag_storage/{working_dir}"
    
    if not Path(working_dir_path).exists():
        print(f"❌ Workspace not found: {working_dir_path}")
        print("   Process RFP first with: python app.py")
        return False
    
    print(f"Workspace: {working_dir}")
    print(f"Working dir: {working_dir_path}")
    
    # Configure LightRAG (using Neo4j storage)
    rag = LightRAG(
        working_dir=working_dir_path,
        # LLM and embeddings configured via environment variables
        # Neo4j storage will be detected from existing graph
    )
    
    # Test query
    test_query = "What are the labor-intensive requirements with high workload complexity?"
    
    print(f"\n{'─'*80}")
    print(f"📝 Test Query: {test_query}")
    print(f"{'─'*80}\n")
    
    try:
        # Execute query with workload analysis prompt
        query_param = QueryParam(
            mode="hybrid",  # Use both local and global context
            user_prompt=user_prompt  # Apply workload analysis formatting
        )
        
        print("⏳ Executing LightRAG query with workload analysis prompt...")
        response = await rag.aquery(test_query, param=query_param)
        
        print(f"\n{'='*80}")
        print(f"📊 LIGHTRAG RESPONSE")
        print(f"{'='*80}\n")
        print(response)
        print(f"\n{'='*80}")
        
        # Validate response quality
        print(f"\n✅ Response Quality Checks:")
        
        quality_checks = {
            "Contains complexity scores": "complexity" in response.lower(),
            "Contains BOE categories": any(cat in response for cat in ["Labor", "Materials", "ODCs", "QA", "Logistics", "Lifecycle", "Compliance"]),
            "Contains operational metrics": any(term in response.lower() for term in ["metric", "volume", "frequency", "hour", "location"]),
            "Contains effort estimates": "effort" in response.lower(),
            "Avoids staffing solutions": "fte" not in response.lower() and "hire" not in response.lower(),
            "Shows confidence scores": "confidence" in response.lower(),
        }
        
        passed = sum(quality_checks.values())
        total = len(quality_checks)
        
        for check, result in quality_checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
        
        print(f"\n📈 Quality Score: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed >= total * 0.7:  # 70% threshold
            print(f"\n{'='*80}")
            print("✅ WORKLOAD USER QUERY TEST PASSED")
            print(f"{'='*80}\n")
            return True
        else:
            print(f"\n{'='*80}")
            print("⚠️  WORKLOAD USER QUERY TEST NEEDS IMPROVEMENT")
            print(f"{'='*80}\n")
            return False
    
    except Exception as e:
        print(f"\n❌ Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_workload_user_query())
    exit(0 if success else 1)
