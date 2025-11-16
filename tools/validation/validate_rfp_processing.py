"""
RFP Processing Validation Runner
=================================

Orchestrates all validation metrics and generates comprehensive production
readiness report.

Usage:
    python tools/validate_rfp_processing.py [workspace]
    python tools/validate_rfp_processing.py afcapv_adab_iss_2025

Validation Metrics:
    1. Query Quality (92%+)         - Test queries return relevant answers
    2. Section L↔M Coverage (85%+)  - Requirements linked to evaluation criteria
    3. Workload Completeness (95%+) - Requirements enriched with BOE metadata
    4. Deliverable Traceability (80%+) - Deliverables traced to requirements

Production Readiness Thresholds:
    < 70%: ❌ FAIL - Needs reprocessing
    70-85%: ⚠️ PASS - Minor gaps, document limitations
    85%+: ✅ PRODUCTION READY - Deploy with confidence
"""

import sys
import os
from pathlib import Path

# Add project root to path to access src modules (tools/validation/ -> project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from validation.query_quality import QueryQualityValidator
from validation.section_l_m_coverage import SectionLMCoverageValidator
from validation.workload_completeness import WorkloadCompletenessValidator
from validation.deliverable_traceability import DeliverableTraceabilityValidator


def calculate_overall_score(results: dict) -> float:
    """
    Calculate weighted overall validation score.
    
    Weights:
        Query Quality: 30%
        Section L↔M: 25%
        Workload: 25%
        Deliverable: 20%
    
    Args:
        results: Dict of all validation results
    
    Returns:
        Overall score (0-100)
    """
    weights = {
        "query_quality": 0.30,
        "section_l_m": 0.25,
        "workload": 0.25,
        "deliverable": 0.20,
    }
    
    overall = (
        results["query_quality"]["score"] * weights["query_quality"] +
        results["section_l_m"]["score"] * weights["section_l_m"] +
        results["workload"]["score"] * weights["workload"] +
        results["deliverable"]["score"] * weights["deliverable"]
    )
    
    return overall


def get_readiness_status(score: float) -> tuple:
    """
    Get production readiness status based on score.
    
    Args:
        score: Overall validation score (0-100)
    
    Returns:
        Tuple of (emoji, status_text, description)
    """
    if score >= 85:
        return ("✅", "PRODUCTION READY", "Deploy with confidence")
    elif score >= 70:
        return ("⚠️", "PASS WITH WARNINGS", "Minor gaps - document limitations")
    else:
        return ("❌", "FAIL", "Needs reprocessing or manual review")


def print_summary_report(workspace: str, results: dict, overall_score: float):
    """Print executive summary of all validation results."""
    emoji, status, description = get_readiness_status(overall_score)
    
    print("\n" + "="*80)
    print("🎯 RFP PROCESSING VALIDATION REPORT")
    print("="*80)
    print(f"\nWorkspace: {workspace}")
    print(f"Overall Score: {overall_score:.1f}%")
    print(f"Status: {emoji} {status}")
    print(f"        {description}")
    
    print("\n" + "─"*80)
    print("METRIC SCORES:")
    print("─"*80)
    
    metrics = [
        ("Query Quality", results["query_quality"]["score"], "queries answered"),
        ("Section L↔M Coverage", results["section_l_m"]["score"], "requirements linked"),
        ("Workload Enrichment", results["workload"]["score"], "requirements enriched"),
        ("Deliverable Traceability", results["deliverable"]["score"], "deliverables traced"),
    ]
    
    for name, score, unit in metrics:
        status_icon = "✅" if score >= 85 else "⚠️" if score >= 70 else "❌"
        print(f"  {status_icon} {name:30s} {score:5.1f}%  ({unit})")
    
    # Collect all recommendations
    all_recommendations = []
    for key in results:
        if "recommendations" in results[key]:
            all_recommendations.extend(results[key]["recommendations"])
    
    if all_recommendations:
        print("\n" + "─"*80)
        print("RECOMMENDATIONS:")
        print("─"*80)
        for rec in all_recommendations[:10]:  # Top 10 recommendations
            print(f"  • {rec}")
        if len(all_recommendations) > 10:
            print(f"  ... and {len(all_recommendations) - 10} more (see detailed reports)")
    
    print("\n" + "="*80)
    print(f"{emoji} OVERALL: {status} ({overall_score:.1f}%)")
    print("="*80 + "\n")


def main():
    """Run all validation metrics and generate report."""
    # Get workspace from command line or use default
    workspace = sys.argv[1] if len(sys.argv) > 1 else "afcapv_adab_iss_2025"
    
    print(f"\n🔍 Running validation for workspace: {workspace}\n")
    
    # Initialize validators
    validators = {
        "query_quality": QueryQualityValidator(workspace),
        "section_l_m": SectionLMCoverageValidator(workspace),
        "workload": WorkloadCompletenessValidator(workspace),
        "deliverable": DeliverableTraceabilityValidator(workspace),
    }
    
    # Run all validations
    results = {}
    
    print("Running validations...")
    print("  [1/4] Query Quality...")
    results["query_quality"] = validators["query_quality"].validate()
    
    print("  [2/4] Section L↔M Coverage...")
    results["section_l_m"] = validators["section_l_m"].validate()
    
    print("  [3/4] Workload Enrichment Completeness...")
    results["workload"] = validators["workload"].validate()
    
    print("  [4/4] Deliverable Traceability...")
    results["deliverable"] = validators["deliverable"].validate()
    
    # Calculate overall score
    overall_score = calculate_overall_score(results)
    
    # Print summary report
    print_summary_report(workspace, results, overall_score)
    
    # Print detailed reports
    print("\n" + "="*80)
    print("📋 DETAILED VALIDATION REPORTS")
    print("="*80)
    
    validators["query_quality"].print_report(results["query_quality"])
    validators["section_l_m"].print_report(results["section_l_m"])
    validators["workload"].print_report(results["workload"])
    validators["deliverable"].print_report(results["deliverable"])
    
    # Exit with status code based on score
    if overall_score >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
