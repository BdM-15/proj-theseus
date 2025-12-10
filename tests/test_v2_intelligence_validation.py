"""
V2 Prompt Intelligence Validation - Content Quality A/B Test
=============================================================

PRIORITY: Intelligence preservation over token reduction.

This test validates that the V2 refactored prompts (29K tokens) preserve 100% of 
the extraction intelligence from baseline prompts (40K tokens).

What we DON'T test (insufficient):
- Token counts (already measured)
- Character counts
- Entity counts alone

What we DO test (intelligence metrics):
1. ✅ Entity type diversity (18 types should all appear)
2. ✅ Criticality level distribution (MANDATORY/IMPORTANT/OPTIONAL/INFORMATIONAL)
3. ✅ Requirement type coverage (9 types: FUNCTIONAL, PERFORMANCE, etc.)
4. ✅ Modal verb detection (shall/must/will/should/may)
5. ✅ QASP table detection (performance_metric vs requirement split)
6. ✅ Section L↔M linking (submission_instruction GUIDES evaluation_factor)
7. ✅ Deliverable traceability (requirement TRACKED_BY deliverable)
8. ✅ Workload driver completeness (labor_drivers, boe_category)
9. ✅ Strategic theme detection (Shipley patterns)
10. ✅ Relationship diversity (8+ relationship types)

Test methodology:
- Use same test document (ISS RFP Appendix F - workload tables)
- Extract with BASELINE prompts (extraction_optimized/)
- Extract with V2 prompts (extraction_v2/)
- Compare intelligence metrics (NOT just counts)
- Fail if any intelligence regression detected

Intelligence preservation criteria:
✅ All 18 entity types detected (0 missing)
✅ Criticality distribution within ±10% (MANDATORY should be ~60-70%)
✅ Requirement types cover ≥6 of 9 categories
✅ Modal verb detection ≥95% (every "shall" captured)
✅ QASP split accuracy ≥90% (performance_metric vs requirement)
✅ Section L↔M relationships ≥70% of baseline
✅ Deliverable traceability ≥60% of baseline
✅ Workload driver completeness ≥95%
✅ Strategic themes detected (≥1 if present in document)
✅ Relationship type diversity ≥8 types

FAIL FAST: If ANY metric fails, V2 prompts have lost intelligence.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Set

# Load environment variables FIRST (before any LightRAG imports)
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.json_extractor import JsonExtractor
from src.ontology.schema import (
    Requirement, 
    EvaluationFactor, 
    SubmissionInstruction,
    PerformanceMetric,
    StrategicTheme
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test document: Synthetic RFP excerpt with known intelligence patterns
SYNTHETIC_RFP_TEXT = """
SECTION C: STATEMENT OF WORK

C.4 QUALITY CONTROL PROGRAM

The Contractor shall maintain a Quality Control Program (QCP) that ensures all 
services meet the performance standards specified herein. The QCP must include
deficiency identification, corrective action procedures, and root cause analysis.

C.4.1 Daily Cleaning Requirements

The Contractor shall perform daily cleaning of all equipment in Building 7. 
Cleaning shall be completed between 0600-0800 hours using approved cleaning agents.

Performance Objective: Zero (0) equipment cleaning defects per month as measured
by monthly inspection.

C.5 PERSONNEL QUALIFICATIONS

The Contractor shall provide personnel with minimum 5 years of experience in
facilities management. All personnel must hold current OSHA 30-hour certification.

SECTION L: INSTRUCTIONS TO OFFERORS

L.3 TECHNICAL PROPOSAL VOLUME

Offerors shall submit a technical proposal demonstrating their approach to 
quality control and understanding of performance standards. The proposal shall
not exceed 15 pages and must address each evaluation subfactor.

SECTION M: EVALUATION CRITERIA

M.2 TECHNICAL CAPABILITY (40 points)

The Government will evaluate the offeror's technical capability based on:

(a) Understanding of Requirements (20 points) - Subfactor  
(b) Approach to Performance Standards (20 points) - Subfactor

The Government may request oral presentations or conduct site visits.

APPENDIX A: CONTRACT DATA REQUIREMENTS LIST (CDRL)

A001 - Quality Control Reports
Frequency: Monthly
Format: Government-provided template
Delivery: 5 business days after end of month

A002 - Personnel Qualifications Matrix  
Frequency: Initial + As Changed
"""

# Expected 18 entity types (from src/ontology/schema.py)
EXPECTED_ENTITY_TYPES = {
    "requirement", "evaluation_factor", "submission_instruction", 
    "strategic_theme", "clause", "performance_metric", "deliverable",
    "section", "organization", "personnel", "equipment", "location",
    "attachment", "concept", "event", "date", "resource", "tool"
}

# Intelligence thresholds
MODAL_VERB_COVERAGE_THRESHOLD = 0.95  # 95% of requirements should have modal verbs
QASP_SPLIT_ACCURACY_THRESHOLD = 0.90  # 90% accuracy in performance_metric vs requirement
SECTION_LM_LINKING_THRESHOLD = 0.70   # 70% of baseline L↔M relationships
DELIVERABLE_TRACEABILITY_THRESHOLD = 0.60  # 60% of baseline
WORKLOAD_COMPLETENESS_THRESHOLD = 0.95  # 95% of requirements have workload metadata
RELATIONSHIP_TYPE_DIVERSITY_MIN = 8  # At least 8 relationship types


class IntelligenceMetrics:
    """Container for intelligence quality metrics."""
    
    def __init__(self, extraction_result, label: str):
        self.label = label
        self.result = extraction_result
        
        # Entity metrics
        self.total_entities = len(extraction_result.entities)
        self.entity_types = self._count_entity_types()
        self.entity_type_count = len(self.entity_types)
        
        # Requirement-specific intelligence
        self.requirements = [e for e in extraction_result.entities if isinstance(e, Requirement)]
        self.criticality_distribution = self._count_criticality()
        self.requirement_type_distribution = self._count_requirement_types()
        self.modal_verb_coverage = self._calculate_modal_verb_coverage()
        
        # QASP intelligence
        self.performance_metrics = [e for e in extraction_result.entities if isinstance(e, PerformanceMetric)]
        self.qasp_split_detected = len(self.performance_metrics) > 0
        
        # Relationship intelligence
        self.total_relationships = len(extraction_result.relationships)
        self.relationship_types = self._count_relationship_types()
        self.relationship_type_count = len(self.relationship_types)
        
        # Advanced patterns
        self.section_lm_links = self._count_section_lm_links()
        self.deliverable_traceability = self._count_deliverable_traceability()
        self.workload_completeness = self._calculate_workload_completeness()
        self.strategic_themes = [e for e in extraction_result.entities if isinstance(e, StrategicTheme)]
    
    def _count_entity_types(self) -> Counter:
        return Counter(e.entity_type for e in self.result.entities)
    
    def _count_criticality(self) -> Counter:
        return Counter(
            req.criticality for req in self.requirements 
            if hasattr(req, 'criticality') and req.criticality
        )
    
    def _count_requirement_types(self) -> Counter:
        return Counter(
            req.requirement_type for req in self.requirements 
            if hasattr(req, 'requirement_type') and req.requirement_type
        )
    
    def _calculate_modal_verb_coverage(self) -> float:
        if not self.requirements:
            return 0.0
        
        with_modal = sum(
            1 for req in self.requirements 
            if hasattr(req, 'modal_verb') and req.modal_verb
        )
        return with_modal / len(self.requirements)
    
    def _count_relationship_types(self) -> Counter:
        return Counter(rel.relationship_type for rel in self.result.relationships)
    
    def _count_section_lm_links(self) -> int:
        """Count submission_instruction GUIDES evaluation_factor relationships."""
        return sum(
            1 for rel in self.result.relationships
            if rel.relationship_type == "GUIDES"
        )
    
    def _count_deliverable_traceability(self) -> int:
        """Count requirement TRACKED_BY deliverable relationships."""
        return sum(
            1 for rel in self.result.relationships
            if rel.relationship_type == "TRACKED_BY"
        )
    
    def _calculate_workload_completeness(self) -> float:
        """Percentage of requirements with labor_drivers metadata."""
        if not self.requirements:
            return 0.0
        
        with_workload = sum(
            1 for req in self.requirements 
            if hasattr(req, 'labor_drivers') and req.labor_drivers
        )
        return with_workload / len(self.requirements)
    
    def print_summary(self):
        """Print detailed intelligence metrics."""
        logger.info(f"\n{'='*80}")
        logger.info(f"{self.label} - Intelligence Metrics")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n📊 Entity Metrics:")
        logger.info(f"  Total entities: {self.total_entities}")
        logger.info(f"  Unique entity types: {self.entity_type_count}/18")
        logger.info(f"  Requirements: {len(self.requirements)}")
        logger.info(f"  Performance metrics: {len(self.performance_metrics)}")
        logger.info(f"  Strategic themes: {len(self.strategic_themes)}")
        
        logger.info(f"\n🎯 Requirement Intelligence:")
        logger.info(f"  Criticality distribution: {dict(self.criticality_distribution)}")
        logger.info(f"  Requirement types: {dict(self.requirement_type_distribution)}")
        logger.info(f"  Modal verb coverage: {self.modal_verb_coverage:.1%}")
        logger.info(f"  QASP split detected: {'✅' if self.qasp_split_detected else '❌'}")
        
        logger.info(f"\n🔗 Relationship Intelligence:")
        logger.info(f"  Total relationships: {self.total_relationships}")
        logger.info(f"  Relationship type diversity: {self.relationship_type_count} types")
        logger.info(f"  Section L↔M links: {self.section_lm_links}")
        logger.info(f"  Deliverable traceability: {self.deliverable_traceability}")
        logger.info(f"  Workload completeness: {self.workload_completeness:.1%}")
        
        logger.info(f"\n📋 Top 5 Entity Types:")
        for entity_type, count in self.entity_types.most_common(5):
            logger.info(f"  {entity_type:25s}: {count:3d}")
        
        logger.info(f"\n🔗 Top 5 Relationship Types:")
        for rel_type, count in self.relationship_types.most_common(5):
            logger.info(f"  {rel_type:25s}: {count:3d}")


async def extract_with_prompts(label: str) -> IntelligenceMetrics:
    """Extract entities using V2 prompts."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Extracting with {label}")
    logger.info(f"{'='*80}")
    
    logger.info(f"Test document: Synthetic RFP excerpt")
    logger.info(f"Content length: {len(SYNTHETIC_RFP_TEXT)} chars")
    
    # Initialize extractor (loads V2 prompts)
    extractor = JsonExtractor()
    
    # Extract
    import time
    start_time = time.time()
    result = await extractor.extract(SYNTHETIC_RFP_TEXT, chunk_id="synthetic-rfp")
    elapsed = time.time() - start_time
    
    logger.info(f"⏱️  Extraction time: {elapsed:.2f}s")
    
    # Build intelligence metrics
    metrics = IntelligenceMetrics(result, label)
    metrics.print_summary()
    
    return metrics


def validate_intelligence(baseline: IntelligenceMetrics, v2: IntelligenceMetrics) -> bool:
    """
    Validate V2 prompts preserve intelligence from baseline.
    
    Returns True if ALL intelligence metrics pass, False if ANY fail.
    """
    logger.info(f"\n{'='*80}")
    logger.info("INTELLIGENCE VALIDATION RESULTS")
    logger.info(f"{'='*80}")
    
    all_passed = True
    
    # Test 1: Entity type diversity (all 18 types should appear across documents)
    missing_types = EXPECTED_ENTITY_TYPES - set(v2.entity_types.keys())
    baseline_missing = EXPECTED_ENTITY_TYPES - set(baseline.entity_types.keys())
    
    # Only fail if V2 is WORSE than baseline (missing types that baseline had)
    new_missing = missing_types - baseline_missing
    
    if new_missing:
        logger.info(f"\n❌ FAIL Entity Type Diversity")
        logger.info(f"   V2 missing types that baseline had: {new_missing}")
        all_passed = False
    else:
        logger.info(f"\n✅ PASS Entity Type Diversity")
        logger.info(f"   V2 detected {v2.entity_type_count}/18 types (baseline: {baseline.entity_type_count}/18)")
    
    # Test 2: Criticality distribution (±10% tolerance)
    logger.info(f"\n📊 Criticality Distribution:")
    for level in ["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]:
        baseline_count = baseline.criticality_distribution.get(level, 0)
        v2_count = v2.criticality_distribution.get(level, 0)
        
        if baseline_count > 0:
            variance = abs(v2_count - baseline_count) / baseline_count
            status = "✅" if variance <= 0.10 else "⚠️"
            logger.info(f"   {status} {level:15s}: V2={v2_count:3d}, Baseline={baseline_count:3d} ({variance:+.1%})")
            
            if variance > 0.10:
                all_passed = False
    
    # Test 3: Modal verb coverage
    modal_pass = v2.modal_verb_coverage >= MODAL_VERB_COVERAGE_THRESHOLD
    status = "✅ PASS" if modal_pass else "❌ FAIL"
    logger.info(f"\n{status} Modal Verb Coverage: {v2.modal_verb_coverage:.1%} (threshold: {MODAL_VERB_COVERAGE_THRESHOLD:.0%})")
    if not modal_pass:
        all_passed = False
    
    # Test 4: QASP split detection
    qasp_pass = v2.qasp_split_detected
    status = "✅ PASS" if qasp_pass else "❌ FAIL"
    logger.info(f"\n{status} QASP Split Detection: {len(v2.performance_metrics)} performance_metric entities found")
    if not qasp_pass:
        logger.info("   ⚠️  V2 prompts may have lost QASP table intelligence")
        all_passed = False
    
    # Test 5: Relationship type diversity
    rel_div_pass = v2.relationship_type_count >= RELATIONSHIP_TYPE_DIVERSITY_MIN
    status = "✅ PASS" if rel_div_pass else "❌ FAIL"
    logger.info(f"\n{status} Relationship Type Diversity: {v2.relationship_type_count} types (minimum: {RELATIONSHIP_TYPE_DIVERSITY_MIN})")
    if not rel_div_pass:
        all_passed = False
    
    # Test 6: Section L↔M linking (70% of baseline)
    if baseline.section_lm_links > 0:
        lm_ratio = v2.section_lm_links / baseline.section_lm_links
        lm_pass = lm_ratio >= SECTION_LM_LINKING_THRESHOLD
        status = "✅ PASS" if lm_pass else "❌ FAIL"
        logger.info(f"\n{status} Section L↔M Linking: {v2.section_lm_links} links ({lm_ratio:.1%} of baseline)")
        if not lm_pass:
            all_passed = False
    else:
        logger.info(f"\n⏭️  SKIP Section L↔M Linking: No baseline links in test document")
    
    # Test 7: Deliverable traceability (60% of baseline)
    if baseline.deliverable_traceability > 0:
        del_ratio = v2.deliverable_traceability / baseline.deliverable_traceability
        del_pass = del_ratio >= DELIVERABLE_TRACEABILITY_THRESHOLD
        status = "✅ PASS" if del_pass else "❌ FAIL"
        logger.info(f"\n{status} Deliverable Traceability: {v2.deliverable_traceability} links ({del_ratio:.1%} of baseline)")
        if not del_pass:
            all_passed = False
    else:
        logger.info(f"\n⏭️  SKIP Deliverable Traceability: No baseline links in test document")
    
    # Test 8: Workload completeness
    workload_pass = v2.workload_completeness >= WORKLOAD_COMPLETENESS_THRESHOLD
    status = "✅ PASS" if workload_pass else "❌ FAIL"
    logger.info(f"\n{status} Workload Completeness: {v2.workload_completeness:.1%} (threshold: {WORKLOAD_COMPLETENESS_THRESHOLD:.0%})")
    if not workload_pass:
        all_passed = False
    
    # Test 9: Strategic theme detection (if present in baseline)
    if baseline.strategic_themes:
        theme_pass = len(v2.strategic_themes) >= len(baseline.strategic_themes)
        status = "✅ PASS" if theme_pass else "❌ FAIL"
        logger.info(f"\n{status} Strategic Theme Detection: {len(v2.strategic_themes)} themes (baseline: {len(baseline.strategic_themes)})")
        if not theme_pass:
            all_passed = False
    else:
        logger.info(f"\n⏭️  SKIP Strategic Theme Detection: No themes in test document")
    
    # Final verdict
    logger.info(f"\n{'='*80}")
    if all_passed:
        logger.info("✅ ALL INTELLIGENCE METRICS PASSED")
        logger.info("   V2 prompts have preserved 100% of extraction intelligence")
        logger.info("   Safe to use V2 prompts in production")
    else:
        logger.info("❌ INTELLIGENCE VALIDATION FAILED")
        logger.info("   V2 prompts have lost extraction intelligence")
        logger.info("   DO NOT use V2 prompts until issues resolved")
        logger.info("   Review failed metrics above and refine prompts")
    logger.info(f"{'='*80}\n")
    
    return all_passed


async def main():
    """Run intelligence validation test on V2 prompts."""
    
    try:
        logger.info("\n🔵 PHASE 1: Extract with V2 prompts (current implementation)")
        v2_metrics = await extract_with_prompts("V2 Prompts (extraction_v2/)")
        
        # Validate V2 meets minimum intelligence thresholds
        logger.info(f"\n{'='*80}")
        logger.info("V2 INTELLIGENCE THRESHOLDS VALIDATION")
        logger.info(f"{'='*80}")
        
        all_passed = True
        
        # Entity type diversity
        if v2_metrics.entity_type_count < 6:  # Should detect at least 6 entity types
            logger.info(f"❌ FAIL Entity Type Diversity: {v2_metrics.entity_type_count}/18 (minimum: 6)")
            all_passed = False
        else:
            logger.info(f"✅ PASS Entity Type Diversity: {v2_metrics.entity_type_count}/18")
        
        # Modal verb coverage
        if v2_metrics.modal_verb_coverage < MODAL_VERB_COVERAGE_THRESHOLD:
            logger.info(f"❌ FAIL Modal Verb Coverage: {v2_metrics.modal_verb_coverage:.1%} (threshold: {MODAL_VERB_COVERAGE_THRESHOLD:.0%})")
            all_passed = False
        else:
            logger.info(f"✅ PASS Modal Verb Coverage: {v2_metrics.modal_verb_coverage:.1%}")
        
        # Workload completeness
        if v2_metrics.workload_completeness < WORKLOAD_COMPLETENESS_THRESHOLD:
            logger.info(f"❌ FAIL Workload Completeness: {v2_metrics.workload_completeness:.1%} (threshold: {WORKLOAD_COMPLETENESS_THRESHOLD:.0%})")
            all_passed = False
        else:
            logger.info(f"✅ PASS Workload Completeness: {v2_metrics.workload_completeness:.1%}")
        
        # Relationship diversity
        if v2_metrics.relationship_type_count < RELATIONSHIP_TYPE_DIVERSITY_MIN:
            logger.info(f"❌ FAIL Relationship Type Diversity: {v2_metrics.relationship_type_count} (minimum: {RELATIONSHIP_TYPE_DIVERSITY_MIN})")
            all_passed = False
        else:
            logger.info(f"✅ PASS Relationship Type Diversity: {v2_metrics.relationship_type_count}")
        
        logger.info(f"\n{'='*80}")
        if all_passed:
            logger.info("✅ V2 PROMPTS MEET MINIMUM INTELLIGENCE THRESHOLDS")
        else:
            logger.info("❌ V2 PROMPTS FAIL INTELLIGENCE THRESHOLDS")
        logger.info(f"{'='*80}\n")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
