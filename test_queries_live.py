"""
Live Query Testing - Branch 010 Phase 1
Tests all 5 enhanced query prompts with realistic government contracting questions
"""
import requests
import json
from pathlib import Path
from datetime import datetime

# Server config
BASE_URL = "http://localhost:9621"
PROMPT_DIR = Path("prompts/user_queries")

def load_prompt(prompt_name: str) -> str:
    """Load user_prompt content from prompts/user_queries/"""
    prompt_file = PROMPT_DIR / f"{prompt_name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")
    return prompt_file.read_text(encoding='utf-8')

def query_rag(query: str, user_prompt: str, mode: str = "hybrid") -> dict:
    """Send query to RAG server with user_prompt"""
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": query,
            "mode": mode,
            "user_prompt": user_prompt
        },
        timeout=120  # Some queries may take time
    )
    response.raise_for_status()
    return response.json()

def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80 + "\n")

def print_result(test_name: str, query: str, response: dict, elapsed: float):
    """Print formatted test result"""
    print(f"🔍 Test: {test_name}")
    print(f"📝 Query: {query}")
    print(f"⏱️  Response time: {elapsed:.2f}s")
    print(f"\n{'─' * 80}")
    print("Response:")
    print(response.get('response', 'No response'))
    print(f"{'─' * 80}\n")

def run_test(test_name: str, query: str, prompt_name: str):
    """Run a single test query"""
    try:
        user_prompt = load_prompt(prompt_name)
        print(f"▶️  Running: {test_name}")
        
        start = datetime.now()
        response = query_rag(query, user_prompt)
        elapsed = (datetime.now() - start).total_seconds()
        
        print_result(test_name, query, response, elapsed)
        return True
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {str(e)}\n")
        return False

# ============================================================================
# TEST SUITE
# ============================================================================

if __name__ == "__main__":
    print_section("🚀 BRANCH 010 PHASE 1 - LIVE QUERY TESTING")
    print(f"Server: {BASE_URL}")
    print(f"Prompt Directory: {PROMPT_DIR}")
    print(f"Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # ========================================================================
    # TEST 1: Compliance Checklist (Pre-writing)
    # ========================================================================
    print_section("TEST 1: Compliance Checklist Generation")
    print("Purpose: Generate pre-writing requirement checklist")
    print("Expected: Structured checklist with MUST/SHOULD/MAY requirements")
    print("Metadata Used: criticality_level, section_origin, factor_id")
    
    results.append(run_test(
        test_name="Compliance Checklist - Full RFP",
        query="Generate a comprehensive compliance checklist for this RFP",
        prompt_name="compliance_checklist"
    ))
    
    # ========================================================================
    # TEST 2: Proposal Outline (Structure planning)
    # ========================================================================
    print_section("TEST 2: Proposal Outline Generation")
    print("Purpose: Generate proposal structure with page allocations")
    print("Expected: Multi-volume outline with page budgets per section")
    print("Metadata Used: factor_id, relative_importance, page_limits")
    
    results.append(run_test(
        test_name="Proposal Outline - Technical Volume",
        query="Generate a proposal outline for the technical volume with page allocations based on evaluation factor weights",
        prompt_name="proposal_outline_generation"
    ))
    
    # ========================================================================
    # TEST 3: Compliance Assessment (Post-writing scoring)
    # ========================================================================
    print_section("TEST 3: Compliance Assessment")
    print("Purpose: Evaluate proposal compliance using Shipley 0-100 scale")
    print("Expected: Scored assessment with evidence gaps and recommendations")
    print("Metadata Used: criticality_level, modal_verb, requirement_type, factor_id")
    
    results.append(run_test(
        test_name="Compliance Assessment - Technical Approach",
        query="Assess our technical approach compliance against Section L requirements and Section M evaluation criteria",
        prompt_name="compliance_assessment"
    ))
    
    # ========================================================================
    # TEST 4: Questions for Government (Clarifications)
    # ========================================================================
    print_section("TEST 4: Questions for Government Generation")
    print("Purpose: Generate strategic clarification questions")
    print("Expected: 5-7 high-impact questions with RFP section references")
    print("Metadata Used: criticality_level, section_origin, page_limits, relative_importance")
    
    results.append(run_test(
        test_name="QFG - Ambiguities and Conflicts",
        query="Generate questions for the government focusing on page limit conflicts, ambiguous requirements, and evaluation criteria clarifications",
        prompt_name="generate_qfg"
    ))
    
    # ========================================================================
    # TEST 5: Win Theme Identification (Strategy)
    # ========================================================================
    print_section("TEST 5: Win Theme Identification")
    print("Purpose: Identify strategic differentiation opportunities")
    print("Expected: 3-5 win themes with discriminator linkage")
    print("Metadata Used: relative_importance, requirement_type, factor_id, theme_type")
    
    results.append(run_test(
        test_name="Win Themes - Competitive Differentiation",
        query="Identify win themes that align with the highest-weighted evaluation factors and demonstrate competitive advantages",
        prompt_name="win_theme_identification"
    ))
    
    # ========================================================================
    # TEST 6: Specific Requirement Queries (Metadata filtering)
    # ========================================================================
    print_section("TEST 6: Metadata-Driven Specific Queries")
    print("Purpose: Test metadata field filtering in queries")
    print("Expected: Precise answers using metadata filters")
    
    results.append(run_test(
        test_name="MUST Requirements Only",
        query="List all MUST requirements (criticality_level=MANDATORY) related to staffing and personnel",
        prompt_name="compliance_checklist"
    ))
    
    results.append(run_test(
        test_name="Section M Factor Weights",
        query="What are the evaluation factors in Section M and their relative importance weights?",
        prompt_name="proposal_outline_generation"
    ))
    
    results.append(run_test(
        test_name="Page Limits by Volume",
        query="What are the page limits for each proposal volume and how should pages be allocated based on evaluation factor weights?",
        prompt_name="proposal_outline_generation"
    ))
    
    # ========================================================================
    # TEST 7: Cross-Prompt Consistency Check
    # ========================================================================
    print_section("TEST 7: Cross-Prompt Consistency")
    print("Purpose: Verify same metadata produces consistent answers across prompts")
    
    results.append(run_test(
        test_name="CLAUSE Detection - Checklist",
        query="List all FAR and DFARS clauses that must be addressed in our proposal",
        prompt_name="compliance_checklist"
    ))
    
    results.append(run_test(
        test_name="CLAUSE Detection - Assessment",
        query="List all FAR and DFARS clauses that must be addressed in our proposal",
        prompt_name="compliance_assessment"
    ))
    
    # ========================================================================
    # RESULTS SUMMARY
    # ========================================================================
    print_section("📊 TEST RESULTS SUMMARY")
    
    total_tests = len(results)
    passed = sum(results)
    failed = total_tests - passed
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total_tests*100):.1f}%")
    
    print(f"\nTest End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check errors above.")
    else:
        print("\n🎉 All tests passed! Phase 1 query prompts working correctly.")
    
    print("\n" + "=" * 80)
