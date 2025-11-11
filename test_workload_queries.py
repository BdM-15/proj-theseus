"""
Test Workload Queries Against ISS RFP Baseline
===============================================

Tests the comprehensive workload query prompts from capture_manager_queries.md
against the ISS RFP baseline (afcapv_adab_iss_2025 workspace).

Usage:
    python test_workload_queries.py
"""

import requests
import json
from pathlib import Path

# LightRAG server endpoint
BASE_URL = "http://localhost:9621"

def test_query(query_name: str, query_text: str, mode: str = "hybrid"):
    """
    Send query to LightRAG and display results.
    
    Args:
        query_name: Name of query being tested
        query_text: The actual query prompt
        mode: Query mode (naive, local, global, hybrid)
    """
    print("\n" + "="*80)
    print(f"🔍 Testing: {query_name}")
    print("="*80)
    print(f"Query: {query_text[:200]}...")
    print()
    
    # Send query to LightRAG
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": query_text,
            "mode": mode
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get("response", "No response")
        
        print("📊 RESULTS:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        print(f"\n✅ Query completed successfully ({len(answer)} chars)")
        
        return answer
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text)
        return None


def main():
    """Run workload query tests"""
    
    print("\n" + "="*80)
    print("🎯 WORKLOAD QUERY BASELINE TESTING")
    print("="*80)
    print("Workspace: afcapv_adab_iss_2025")
    print("Mode: hybrid (combines local + global search)")
    print()
    
    # Test Query 1.1: Complete Labor Workload Breakdown
    query_1_1 = """Provide a comprehensive list of ALL labor workload drivers for Installation Support Services at Al Dhafra Air Base.

Workload drivers include:
- Service frequencies (daily, weekly, monthly, continuous, on-demand)
- Operating hours and shift coverage (8x5, 24/7, business hours, etc.)
- Staffing levels (FTE requirements, team sizes, ratios)
- Response time requirements (SLA targets, emergency response times)
- Quality assurance activities (inspections, audits, reviews)
- Training requirements (initial, recurring, certification)
- Administrative tasks (reporting, documentation, meetings)
- Peak demand periods (seasonal, event-driven)

Organization:
- Start with a brief summary of the scope
- Group workload drivers by PWS section in logical order
- For each driver, include: description, frequency/quantity, location/coverage area, rationale/context
- Highlight MANDATORY vs IMPORTANT requirements
- Flag implicit workload (e.g., "24/7 coverage" implies 3-shift staffing)

Focus on TOTALITY - provide ALL quantifiable workload metrics, not samples. This data will be used to develop labor Basis of Estimate and calculate Full-Time Equivalent (FTE) requirements."""
    
    result_1_1 = test_query("Query 1.1: Complete Labor Workload Breakdown", query_1_1)
    
    # Test Query 2.1: Complete Material/Supply Inventory (simplified)
    query_2_1 = """Provide a comprehensive inventory of ALL material, supply, and equipment requirements for Installation Support Services.

Categories to extract:
1. CONSUMABLES (recurring purchases):
   - Item description, quantity per period, frequency, unit specifications

2. EQUIPMENT (capital/durable goods):
   - Item description, quantity, model/specifications, replacement cycle

3. GOVERNMENT-FURNISHED EQUIPMENT (GFE):
   - Items provided by government (note: affects cost proposal)
   - Contractor-furnished vs GFE distinction

Organization:
- Group by service area or PWS subsection
- Include quantities, frequencies, specifications
- Distinguish one-time (capital) vs recurring (consumable) costs
- Flag GFE items (reduce contractor costs)

Focus on TOTALITY - this data drives BOM development and procurement planning."""
    
    result_2_1 = test_query("Query 2.1: Complete Material/Supply Inventory", query_2_1)
    
    # Test Query 7.1: Government-Furnished Equipment & Facilities
    query_7_1 = """Provide a total list of Government-Furnished Equipment (GFE) and Government-Furnished Facilities (GFF) for Installation Support Services at Al Dhafra Air Base.

Extract:
1. EQUIPMENT PROVIDED BY GOVERNMENT:
   - Item description, quantity, condition (new, refurbished, as-is)
   - Delivery timeline (available at contract start, phased delivery)
   - Maintenance responsibility (government, contractor, shared)

2. FACILITIES PROVIDED BY GOVERNMENT:
   - Facility type (warehouse, office, workspace, secure areas)
   - Square footage, utilities included, access hours
   - Condition (move-in ready, requires renovation)

3. CONTRACTOR-FURNISHED ALTERNATIVES:
   - Items contractor must provide if GFE unavailable
   - Cost impact (lease vs purchase vs GFE)

4. RISK FACTORS:
   - GFE delivery delays (impact on contract start)
   - GFE condition issues (maintenance, obsolescence)
   - Facility access restrictions (security, hours)

Organization:
- Group by relevant PWS section
- Distinguish GFE vs contractor-furnished clearly
- Calculate cost savings from GFE/GFF
- Flag delivery dependencies and risks

This knowledge helps us know if we need to lease equipment and save costs. Focus on totality, not samples."""
    
    result_7_1 = test_query("Query 7.1: Government-Furnished Equipment & Facilities", query_7_1)
    
    # Save results to file
    output_file = Path("test_results_workload_queries.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("WORKLOAD QUERY TEST RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Workspace: afcapv_adab_iss_2025\n")
        f.write(f"Date: 2025-11-09\n\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("Query 1.1: Complete Labor Workload Breakdown\n")
        f.write("="*80 + "\n")
        f.write(result_1_1 or "FAILED")
        
        f.write("\n\n" + "="*80 + "\n")
        f.write("Query 2.1: Complete Material/Supply Inventory\n")
        f.write("="*80 + "\n")
        f.write(result_2_1 or "FAILED")
        
        f.write("\n\n" + "="*80 + "\n")
        f.write("Query 7.1: Government-Furnished Equipment & Facilities\n")
        f.write("="*80 + "\n")
        f.write(result_7_1 or "FAILED")
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n" + "="*80)
    print("🎯 BASELINE TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
