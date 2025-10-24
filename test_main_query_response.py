#!/usr/bin/env python3
"""
Test the same query on main branch to compare strategic reasoning depth.
"""

import requests
import json

def test_query():
    """Test the proposal outline query on main branch."""
    
    query = """Based on the proposal instructions provide me a bulletized proposal outline 
and specifics on the content I should address the customer pain points and 
identify solutioning opportunities that may gain me more favor in the award decision."""
    
    url = "http://localhost:9621/query"
    
    payload = {
        "query": query,
        "mode": "hybrid",
        "only_need_context": False
    }
    
    print("=" * 80)
    print("MAIN BRANCH QUERY TEST")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print("\nSending request to LightRAG...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n" + "=" * 80)
        print("RESPONSE")
        print("=" * 80)
        print(result.get('response', 'No response field'))
        print("\n" + "=" * 80)
        
        # Analyze response quality
        response_text = result.get('response', '')
        
        print("\nRESPONSE QUALITY ANALYSIS")
        print("=" * 80)
        
        # Strategic indicators
        strategic_phrases = [
            'gain favor', 'competitive advantage', 'exceed', 'innovative',
            'demonstrate', 'position', 'risk mitigation', 'proof point',
            'outstanding rating', 'exceptional understanding', 'low-risk',
            'high-efficiency', 'directly target', 'earning', 'pain point'
        ]
        
        found_strategic = [phrase for phrase in strategic_phrases if phrase.lower() in response_text.lower()]
        
        print(f"\nStrategic phrases found ({len(found_strategic)}):")
        for phrase in found_strategic:
            print(f"  ✓ {phrase}")
        
        # Length analysis
        print(f"\nResponse length: {len(response_text)} characters")
        print(f"Word count: {len(response_text.split())} words")
        
        # Structure analysis
        bullet_count = response_text.count('•') + response_text.count('-') + response_text.count('*')
        print(f"Bullet points: ~{bullet_count}")
        
        # Evaluation factor references
        if 'factor' in response_text.lower():
            print("\n✓ Contains evaluation factor references")
        
        if 'section m' in response_text.lower() or 'section l' in response_text.lower():
            print("✓ References Section L/M evaluation criteria")
        
        # Competitive intelligence
        competitive_terms = ['competitive', 'advantage', 'differentiate', 'exceed', 'superior']
        competitive_count = sum(1 for term in competitive_terms if term in response_text.lower())
        print(f"\nCompetitive intelligence terms: {competitive_count}")
        
        # Risk mitigation
        if 'risk' in response_text.lower():
            print("✓ Includes risk mitigation strategies")
        
        # Proof points
        if 'past performance' in response_text.lower() or 'certification' in response_text.lower():
            print("✓ Recommends proof points")
        
        print("\n" + "=" * 80)
        print("COMPARISON TO BRANCH 010 BASELINE")
        print("=" * 80)
        print("\nBranch 010 response was described as:")
        print("  - Bland and light on reasoning")
        print("  - Minimal strategic language")
        print("  - Mostly compliance-focused structure")
        
        print("\nMain branch response shows:")
        if len(found_strategic) > 5:
            print("  ✅ Rich strategic language (5+ strategic phrases)")
        else:
            print(f"  ⚠️ Limited strategic language ({len(found_strategic)} phrases)")
        
        if competitive_count > 2:
            print("  ✅ Strong competitive intelligence")
        else:
            print("  ⚠️ Limited competitive intelligence")
        
        if len(response_text) > 1000:
            print("  ✅ Comprehensive depth (1000+ chars)")
        else:
            print(f"  ⚠️ Brief response ({len(response_text)} chars)")
        
        print("\n" + "=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the server is running: python app.py")

if __name__ == "__main__":
    test_query()
