"""
Quick Query Test - Single query execution for rapid testing
Usage: python test_query_quick.py
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:9621"
PROMPT_DIR = Path("prompts/user_queries")

# ============================================================================
# QUICK TEST CONFIGURATION - Edit these for different tests
# ============================================================================

# Choose your prompt (one of: compliance_checklist, compliance_assessment, 
#                            proposal_outline_generation, generate_qfg, 
#                            win_theme_identification)
PROMPT_NAME = "compliance_checklist"

# Your test query
QUERY = "Generate a compliance checklist for this RFP"

# Query mode (hybrid, local, naive, or global)
MODE = "hybrid"

# ============================================================================

def load_prompt(prompt_name: str) -> str:
    prompt_file = PROMPT_DIR / f"{prompt_name}.md"
    return prompt_file.read_text(encoding='utf-8')

def query_rag(query: str, user_prompt: str, mode: str = "hybrid"):
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": query, "mode": mode, "user_prompt": user_prompt},
        timeout=120
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    print("=" * 80)
    print("QUICK QUERY TEST")
    print("=" * 80)
    print(f"\n📝 Prompt: {PROMPT_NAME}")
    print(f"🔍 Query: {QUERY}")
    print(f"🎯 Mode: {MODE}")
    print(f"\n{'─' * 80}\n")
    
    try:
        user_prompt = load_prompt(PROMPT_NAME)
        print("⏳ Querying RAG server...")
        
        response = query_rag(QUERY, user_prompt, MODE)
        
        print("\n✅ Response received:\n")
        print("=" * 80)
        print(response.get('response', 'No response'))
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
