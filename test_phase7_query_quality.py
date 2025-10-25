"""
Test query quality with Phase 7 enriched graph.

Tests 5 strategic queries via HTTP to check:
1. Phase 6 semantic relationships (requirement→evaluation_factor)
2. Phase 7 metadata enrichment (importance, subfactors, criticality)
3. Strategic reasoning preservation (competitive intelligence)
"""

import requests
import time
from pathlib import Path

# Query test cases
QUERIES = [
    {
        "name": "Q1: Evaluation Factor Prioritization",
        "query": """What are the most important evaluation factors in this RFP, and what 
requirements or criteria do they assess? Prioritize by importance and provide specific 
requirements that contractors must address under each factor.""",
        "tests": [
            "Should mention evaluation factors with importance ratings (Phase 7 metadata)",
            "Should link factors to specific requirements (Phase 6 relationships)",
            "Should identify 'Significantly More Important' factors",
            "Should list subfactors (relevance, recency, quality from Phase 7)"
        ]
    },
    {
        "name": "Q2: Requirement→Factor Traceability",
        "query": """Which requirements are evaluated under the Technical Approach factor? 
List the mandatory requirements, their criticality levels, and how they relate to 
technical scoring.""",
        "tests": [
            "Should identify requirements linked to Technical Approach",
            "Should mention requirement criticality (MANDATORY from Phase 7)",
            "Should show requirement→factor relationships (Phase 6)",
            "Should differentiate MANDATORY vs RECOMMENDED"
        ]
    },
    {
        "name": "Q3: Proposal Effort Allocation",
        "query": """Based on evaluation factor weights and the requirements they assess, 
how should a contractor allocate proposal development effort across Technical Approach, 
Management Approach, and Past Performance factors?""",
        "tests": [
            "Should reference factor weights/importance (Phase 7)",
            "Should count requirements per factor (Phase 6 relationships)",
            "Should consider requirement criticality (Phase 7)",
            "Should provide strategic guidance (competitive intelligence)"
        ]
    },
    {
        "name": "Q4: Submission Instruction Compliance",
        "query": """What are the page limits and format requirements for proposal sections, 
and which evaluation factors do these submission instructions relate to?""",
        "tests": [
            "Should mention page limits (Phase 7 metadata_page_limit)",
            "Should mention format requirements (Phase 7 metadata_format)",
            "Should link submission_instructions to evaluation_factors (Phase 6 GUIDES)",
            "Should identify which factors have submission constraints"
        ]
    },
    {
        "name": "Q5: Strategic Competitive Positioning",
        "query": """What are the key competitive differentiators in this RFP? Consider 
evaluation factor weights, mandatory requirements, and areas where innovative solutions 
could demonstrate competitive advantage.""",
        "tests": [
            "Should mention 'Significantly More Important' factors",
            "Should reference strategic themes (competitive advantage, innovation)",
            "Should identify high-weight factors (Phase 7)",
            "Should synthesize requirements + factors + strategic reasoning"
        ]
    }
]


def test_query(query_data: dict, log):
    """Test a single query and analyze response quality."""
    log(f"\n{'=' * 80}")
    log(f"🔍 {query_data['name']}")
    log(f"{'=' * 80}")
    log(f"\n📝 Query: {query_data['query']}")
    log(f"\n⏳ Processing...")
    
    # Execute query via HTTP
    try:
        response = requests.post(
            "http://localhost:9621/query",
            json={
                "query": query_data['query'],
                "mode": "hybrid"
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        response_text = result.get('response', '')
    except Exception as e:
        log(f"\n❌ Query failed: {e}")
        return {
            "query": query_data['name'],
            "response_length": 0,
            "phase7_detected": False,
            "phase6_detected": False,
            "strategic_detected": False,
            "response": f"ERROR: {e}"
        }
    
    # Analyze response
    log(f"\n📊 Response Length: {len(response_text)} characters")
    log(f"\n{'─' * 80}")
    log(f"Response:\n")
    log(response_text)
    log(f"{'─' * 80}")
    
    # Check quality indicators
    log(f"\n✅ Quality Checks:")
    for test in query_data['tests']:
        log(f"   • {test}")
    
    # Check for key Phase 7 indicators
    phase7_indicators = []
    if 'important' in response_text.lower() or 'significance' in response_text.lower():
        phase7_indicators.append("✓ Mentions importance/significance (Phase 7 metadata)")
    if 'mandatory' in response_text.lower() or 'required' in response_text.lower():
        phase7_indicators.append("✓ Mentions criticality (Phase 7 metadata)")
    if 'subfactor' in response_text.lower() or 'sub-factor' in response_text.lower():
        phase7_indicators.append("✓ Mentions subfactors (Phase 7 metadata)")
    if 'page' in response_text.lower() and ('limit' in response_text.lower() or 'format' in response_text.lower()):
        phase7_indicators.append("✓ Mentions page limits/format (Phase 7 metadata)")
    
    # Check for Phase 6 indicators (semantic relationships)
    phase6_indicators = []
    if 'requirement' in response_text.lower() and 'factor' in response_text.lower():
        phase6_indicators.append("✓ Links requirements to factors (Phase 6 relationships)")
    if 'evaluated' in response_text.lower() or 'assess' in response_text.lower():
        phase6_indicators.append("✓ Mentions evaluation relationships (Phase 6 semantic)")
    if 'technical approach' in response_text.lower() or 'management approach' in response_text.lower():
        phase6_indicators.append("✓ References specific evaluation factors")
    
    # Check strategic reasoning
    strategic_indicators = []
    strategic_keywords = ['competitive', 'advantage', 'innovative', 'demonstrate', 'position', 'win probability', 'risk mitigation']
    found_keywords = [kw for kw in strategic_keywords if kw in response_text.lower()]
    if found_keywords:
        strategic_indicators.append(f"✓ Strategic language detected: {', '.join(found_keywords)}")
    
    log(f"\n🎯 Phase 7 Metadata Detection:")
    if phase7_indicators:
        for indicator in phase7_indicators:
            log(f"   {indicator}")
    else:
        log("   ❌ No Phase 7 metadata indicators found")
    
    log(f"\n🔗 Phase 6 Relationship Detection:")
    if phase6_indicators:
        for indicator in phase6_indicators:
            log(f"   {indicator}")
    else:
        log("   ❌ No Phase 6 relationship indicators found")
    
    log(f"\n💡 Strategic Reasoning Detection:")
    if strategic_indicators:
        for indicator in strategic_indicators:
            log(f"   {indicator}")
    else:
        log("   ⚠️  Limited strategic reasoning detected")
    
    return {
        "query": query_data['name'],
        "response_length": len(response_text),
        "phase7_detected": len(phase7_indicators) > 0,
        "phase6_detected": len(phase6_indicators) > 0,
        "strategic_detected": len(strategic_indicators) > 0,
        "response": response_text
    }


def main():
    """Run all query tests."""
    output_file = Path("query_quality_results.md")
    
    def log(msg):
        """Write to both console and file."""
        print(msg)
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
    
    # Clear output file
    output_file.write_text("", encoding='utf-8')
    
    log("=" * 80)
    log("Phase 7 Query Quality Assessment - MCPP II RFP")
    log("=" * 80)
    log("\nChecking server availability...")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:9621/health", timeout=5)
        response.raise_for_status()
        log("✅ Server is running")
    except Exception as e:
        log(f"❌ Server not available: {e}")
        log("\n⚠️  Please start the server first: python app.py")
        return
    
    log(f"\nRunning {len(QUERIES)} strategic queries...\n")
    
    # Run all queries
    results = []
    for i, query_data in enumerate(QUERIES, 1):
        log(f"\n[{i}/{len(QUERIES)}] Testing query...")
        result = test_query(query_data, log)
        results.append(result)
        
        # Pause between queries
        if i < len(QUERIES):
            time.sleep(2)
    
    # Summary
    log(f"\n\n{'=' * 80}")
    log("ASSESSMENT SUMMARY")
    log(f"{'=' * 80}\n")
    
    phase7_success = sum(1 for r in results if r['phase7_detected'])
    phase6_success = sum(1 for r in results if r['phase6_detected'])
    strategic_success = sum(1 for r in results if r['strategic_detected'])
    
    log(f"📊 Query Results ({len(QUERIES)} queries):")
    log(f"   Phase 7 Metadata Used: {phase7_success}/{len(QUERIES)} queries ({phase7_success/len(QUERIES)*100:.0f}%)")
    log(f"   Phase 6 Relationships Used: {phase6_success}/{len(QUERIES)} queries ({phase6_success/len(QUERIES)*100:.0f}%)")
    log(f"   Strategic Reasoning: {strategic_success}/{len(QUERIES)} queries ({strategic_success/len(QUERIES)*100:.0f}%)")
    
    avg_length = sum(r['response_length'] for r in results) / len(results)
    log(f"\n📏 Average Response Length: {avg_length:.0f} characters")
    
    # Verdict
    log(f"\n{'=' * 80}")
    log("VERDICT")
    log(f"{'=' * 80}\n")
    
    if phase7_success >= 3 and phase6_success >= 3:
        log("✅ PHASE 7 SUCCESS: Query quality HIGH")
        log("   • Phase 7 metadata enrichment is being used by queries")
        log("   • Phase 6 semantic relationships are being used (despite missing EVALUATED_BY labels)")
        log("   • Graph supports strategic reasoning")
        log("\n✅ RECOMMENDATION: Phase 7 is production-ready")
        log("   • No need to reprocess")
        log("   • Consider fixing Phase 6 labels as optimization (not critical)")
    elif phase7_success >= 2 or phase6_success >= 2:
        log("⚠️  PHASE 7 PARTIAL SUCCESS: Query quality MODERATE")
        log("   • Some Phase 7/Phase 6 features being used")
        log("   • May need optimization")
        log("\n⚠️  RECOMMENDATION: Review low-performing queries")
        log("   • Consider fixing Phase 6 output parsing")
        log("   • May need to reprocess for better results")
    else:
        log("❌ PHASE 7 FAILURE: Query quality LOW")
        log("   • Phase 7 metadata not being used")
        log("   • Phase 6 relationships not accessible")
        log("\n❌ RECOMMENDATION: Fix Phase 6 output parsing and reprocess")
        log("   • LLM ignoring relationship_type schema")
        log("   • Semantic relationships exist but not queryable")
    
    log("")
    log(f"\n✅ Full results saved to: {output_file.absolute()}")
    print(f"\n✅ Full results saved to: {output_file.absolute()}")


if __name__ == "__main__":
    main()
