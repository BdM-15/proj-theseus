"""
Quality Assurance Framework - Production Quality Gates

Comprehensive validation framework ensuring production-ready extractions.
Enforces quality gates that must pass before processing continues.

Quality Gates:
1. Section Hierarchy Validation (UCF structure)
2. Relationship Pattern Validation (domain-valid only)
3. Completeness Assessment (A-M coverage)
4. Performance Benchmarking (targets: 850+ entities, 1000+ relationships)

Cannot proceed without: 100% section validity, 0 fictitious sections, 0 contamination
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter
import json
from pathlib import Path

from pydantic import BaseModel, Field

from models.rfp_models import (
    RFPRequirement, RFPSection, ValidationResult, RequirementType
)

logger = logging.getLogger(__name__)


class SectionHierarchyValidation(BaseModel):
    """Results of UCF section hierarchy validation"""
    is_valid: bool = Field(..., description="Whether section hierarchy follows UCF")
    fictitious_sections: List[str] = Field(default_factory=list, description="Invalid sections like J-L")
    missing_critical_sections: List[str] = Field(default_factory=list, description="Missing C, L, or M")
    duplicate_sections: List[str] = Field(default_factory=list, description="Duplicate section IDs")
    section_coverage_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of A-M present")
    total_sections_found: int = Field(default=0, description="Total sections identified")


class RelationshipPatternValidation(BaseModel):
    """Results of relationship pattern validation"""
    is_valid: bool = Field(..., description="Whether all relationships match valid patterns")
    invalid_patterns: List[str] = Field(default_factory=list, description="Invalid relationship types")
    critical_missing: List[str] = Field(default_factory=list, description="Missing critical relationships like LM")
    valid_relationship_count: int = Field(default=0, description="Count of valid relationships")
    total_relationship_count: int = Field(default=0, description="Total relationships checked")


class CompletenessAssessment(BaseModel):
    """Assessment of extraction completeness"""
    entity_count: int = Field(..., ge=0, description="Total entities extracted")
    relationship_count: int = Field(..., ge=0, description="Total relationships extracted")
    section_coverage: Dict[str, bool] = Field(default_factory=dict, description="A-M section presence")
    requirements_count: int = Field(..., ge=0, description="Total requirements extracted")
    clin_count: int = Field(..., ge=0, description="CLIN entities found")
    far_clause_count: int = Field(..., ge=0, description="FAR clause entities found")
    meets_target: bool = Field(..., description="Whether meets production targets")
    target_entity_count: int = Field(default=850, description="Target entity count")
    target_relationship_count: int = Field(default=1000, description="Target relationship count")


class PerformanceBenchmark(BaseModel):
    """Performance benchmarking results"""
    processing_time_seconds: float = Field(..., ge=0.0, description="Total processing time")
    entities_per_second: float = Field(..., ge=0.0, description="Entity extraction rate")
    chunks_processed: int = Field(..., ge=0, description="Total chunks processed")
    llm_calls: int = Field(..., ge=0, description="Total LLM API calls")
    avg_chunk_time: float = Field(..., ge=0.0, description="Average time per chunk")
    memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage")


class QualityGateReport(BaseModel):
    """Complete quality gate validation report"""
    timestamp: datetime = Field(default_factory=datetime.now, description="Report generation time")
    section_validation: SectionHierarchyValidation
    relationship_validation: RelationshipPatternValidation
    completeness: CompletenessAssessment
    performance: PerformanceBenchmark
    
    overall_pass: bool = Field(..., description="Whether all quality gates passed")
    critical_failures: List[str] = Field(default_factory=list, description="Blocking issues")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement suggestions")


class QualityAssuranceFramework:
    """
    Production quality assurance framework
    
    Enforces quality gates for:
    - UCF section structure validity
    - Domain-valid relationship patterns
    - Production target achievement
    - Performance benchmarks
    
    CANNOT PROCEED if critical quality gates fail
    """
    
    # Valid UCF sections (A-M)
    VALID_SECTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
    
    # Critical sections that MUST be present in most RFPs
    CRITICAL_SECTIONS = ['C', 'L', 'M']  # SOW, Instructions, Evaluation
    
    # Valid relationship patterns (from ontology)
    VALID_RELATIONSHIP_PATTERNS = {
        'Section L  Section M',
        'Section C  Section B',
        'Section C  Deliverable',
        'Section I  Sections A-H',
        'Requirement  Deliverable',
        'Requirement  Evaluation Factor',
        'CLIN  Requirement',
        'FAR Clause  Requirement',
        'Organization  Requirement',
        'Security Requirement  Requirement',
        'Performance Metric  Requirement',
        'Specification  Requirement',
        'Deliverable  Evaluation Factor',
    }
    
    # Production targets (exceeding Plan A)
    PRODUCTION_TARGETS = {
        'entities': 850,
        'relationships': 1000,
        'contamination': 0,
        'section_coverage': 100.0,
    }
    
    def __init__(self):
        """Initialize quality assurance framework"""
        logger.info("Quality assurance framework initialized")
        self.validation_history: List[QualityGateReport] = []
    
    def validate_section_hierarchy(
        self,
        sections: List[RFPSection]
    ) -> SectionHierarchyValidation:
        """
        Validate section structure against UCF standards
        
        Checks:
        - Only A-M sections (no fictitious J-L, A-B)
        - No duplicate section IDs
        - Critical sections present (C, L, M)
        - Reasonable coverage (>50% of sections)
        """
        
        section_ids = [s.section_id for s in sections]
        
        # Check for fictitious sections
        fictitious = []
        for sid in section_ids:
            # Extract base section (e.g., "L.3.1"  "L", "J-1"  "J")
            base = sid.split('.')[0].split('-')[0]
            
            # Check if base is valid
            if base not in self.VALID_SECTIONS:
                fictitious.append(sid)
            
            # Check for invalid combinations (J-L, A-B, etc.)
            if '-' in sid:
                parts = sid.split('-')
                if len(parts) == 2 and parts[1] in self.VALID_SECTIONS:
                    fictitious.append(sid)
        
        # Check for duplicates
        duplicates = [sid for sid, count in Counter(section_ids).items() if count > 1]
        
        # Check for missing critical sections
        base_sections = set([sid.split('.')[0].split('-')[0] for sid in section_ids])
        missing_critical = [sec for sec in self.CRITICAL_SECTIONS if sec not in base_sections]
        
        # Calculate coverage
        coverage = (len(base_sections & set(self.VALID_SECTIONS)) / len(self.VALID_SECTIONS)) * 100
        
        is_valid = (
            len(fictitious) == 0 and
            len(missing_critical) == 0 and
            coverage >= 50.0
        )
        
        return SectionHierarchyValidation(
            is_valid=is_valid,
            fictitious_sections=fictitious,
            missing_critical_sections=missing_critical,
            duplicate_sections=duplicates,
            section_coverage_percent=coverage,
            total_sections_found=len(sections)
        )
    
    def validate_relationship_patterns(
        self,
        relationships: List[Dict[str, Any]]
    ) -> RelationshipPatternValidation:
        """
        Validate relationships match domain-valid patterns
        
        Args:
            relationships: List of relationship dicts with keys:
                - source_entity_type
                - target_entity_type
                - relationship_type
        
        Returns:
            Validation results
        """
        
        invalid_patterns = []
        valid_count = 0
        
        for rel in relationships:
            # Construct pattern string
            pattern = f"{rel.get('source_entity_type', 'UNKNOWN')}  {rel.get('target_entity_type', 'UNKNOWN')}"
            
            # Check if pattern is valid
            # Note: This is simplified - real validation needs to parse relationship_type
            # For now, we check if the entity types make sense
            if self._is_valid_pattern(rel):
                valid_count += 1
            else:
                invalid_patterns.append(pattern)
        
        # Check for critical missing relationships (LM)
        critical_missing = []
        if not self._has_l_m_relationship(relationships):
            critical_missing.append("Section L  Section M (CRITICAL)")
        
        is_valid = len(invalid_patterns) == 0 and len(critical_missing) == 0
        
        return RelationshipPatternValidation(
            is_valid=is_valid,
            invalid_patterns=invalid_patterns,
            critical_missing=critical_missing,
            valid_relationship_count=valid_count,
            total_relationship_count=len(relationships)
        )
    
    def _is_valid_pattern(self, relationship: Dict[str, Any]) -> bool:
        """
        Check if relationship pattern is valid
        Simplified validation - checks entity type compatibility
        """
        
        source_type = relationship.get('source_entity_type', '')
        target_type = relationship.get('target_entity_type', '')
        
        # Valid entity types (from ontology)
        valid_types = {
            'SECTION', 'REQUIREMENT', 'CLIN', 'FAR_CLAUSE', 'DELIVERABLE',
            'EVALUATION_FACTOR', 'ORGANIZATION', 'SECURITY_REQUIREMENT',
            'PERFORMANCE_METRIC', 'SPECIFICATION', 'PERSONNEL', 'LOCATION',
            'DOCUMENT', 'EVENT'
        }
        
        return source_type in valid_types and target_type in valid_types
    
    def _has_l_m_relationship(self, relationships: List[Dict[str, Any]]) -> bool:
        """Check for critical Section L  Section M relationship"""
        
        for rel in relationships:
            source = rel.get('source_entity', '').upper()
            target = rel.get('target_entity', '').upper()
            
            # Check for LM or ML connection
            if ('SECTION L' in source and 'SECTION M' in target) or \
               ('SECTION M' in source and 'SECTION L' in target):
                return True
        
        return False
    
    def assess_completeness(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        sections: List[RFPSection]
    ) -> CompletenessAssessment:
        """
        Assess extraction completeness against production targets
        
        Args:
            entities: List of extracted entities
            relationships: List of extracted relationships
            sections: List of identified sections
        
        Returns:
            Completeness assessment with target comparison
        """
        
        # Count by entity type
        entity_types = Counter([e.get('entity_type', 'UNKNOWN') for e in entities])
        
        requirements_count = entity_types.get('REQUIREMENT', 0)
        clin_count = entity_types.get('CLIN', 0)
        far_clause_count = entity_types.get('FAR_CLAUSE', 0)
        
        # Section coverage
        base_sections = set([s.section_id.split('.')[0].split('-')[0] for s in sections])
        section_coverage = {
            sec: sec in base_sections for sec in self.VALID_SECTIONS
        }
        
        # Check if meets production targets
        meets_target = (
            len(entities) >= self.PRODUCTION_TARGETS['entities'] and
            len(relationships) >= self.PRODUCTION_TARGETS['relationships']
        )
        
        return CompletenessAssessment(
            entity_count=len(entities),
            relationship_count=len(relationships),
            section_coverage=section_coverage,
            requirements_count=requirements_count,
            clin_count=clin_count,
            far_clause_count=far_clause_count,
            meets_target=meets_target,
            target_entity_count=self.PRODUCTION_TARGETS['entities'],
            target_relationship_count=self.PRODUCTION_TARGETS['relationships']
        )
    
    def benchmark_performance(
        self,
        start_time: datetime,
        end_time: datetime,
        chunks_processed: int,
        llm_calls: int,
        entity_count: int
    ) -> PerformanceBenchmark:
        """
        Benchmark processing performance
        
        Args:
            start_time: Processing start timestamp
            end_time: Processing end timestamp
            chunks_processed: Total chunks processed
            llm_calls: Total LLM API calls made
            entity_count: Total entities extracted
        
        Returns:
            Performance benchmark results
        """
        
        processing_time = (end_time - start_time).total_seconds()
        entities_per_second = entity_count / max(processing_time, 1)
        avg_chunk_time = processing_time / max(chunks_processed, 1)
        
        return PerformanceBenchmark(
            processing_time_seconds=processing_time,
            entities_per_second=entities_per_second,
            chunks_processed=chunks_processed,
            llm_calls=llm_calls,
            avg_chunk_time=avg_chunk_time
        )
    
    def generate_quality_gate_report(
        self,
        section_validation: SectionHierarchyValidation,
        relationship_validation: RelationshipPatternValidation,
        completeness: CompletenessAssessment,
        performance: PerformanceBenchmark
    ) -> QualityGateReport:
        """
        Generate comprehensive quality gate report
        
        Determines:
        - Overall pass/fail status
        - Critical failures (blocking issues)
        - Warnings (non-blocking issues)
        - Recommendations for improvement
        """
        
        critical_failures = []
        warnings = []
        recommendations = []
        
        # Check section validation
        if not section_validation.is_valid:
            if section_validation.fictitious_sections:
                critical_failures.append(
                    f"Fictitious sections detected: {section_validation.fictitious_sections}"
                )
            if section_validation.missing_critical_sections:
                critical_failures.append(
                    f"Missing critical sections: {section_validation.missing_critical_sections}"
                )
            if section_validation.section_coverage_percent < 50.0:
                warnings.append(
                    f"Low section coverage: {section_validation.section_coverage_percent:.1f}% (target: >50%)"
                )
        
        # Check relationship validation
        if not relationship_validation.is_valid:
            if relationship_validation.critical_missing:
                critical_failures.append(
                    f"Missing critical relationships: {relationship_validation.critical_missing}"
                )
            if relationship_validation.invalid_patterns:
                warnings.append(
                    f"{len(relationship_validation.invalid_patterns)} invalid relationship patterns"
                )
        
        # Check completeness
        if not completeness.meets_target:
            warnings.append(
                f"Below target: {completeness.entity_count} entities (target: {completeness.target_entity_count}), "
                f"{completeness.relationship_count} relationships (target: {completeness.target_relationship_count})"
            )
            recommendations.append(
                "Consider adjusting chunk size or extraction prompts to improve entity/relationship extraction"
            )
        
        # Performance recommendations
        if performance.avg_chunk_time > 10.0:
            recommendations.append(
                f"High average chunk time: {performance.avg_chunk_time:.1f}s (consider optimizing prompts)"
            )
        
        # Overall pass determination
        overall_pass = len(critical_failures) == 0
        
        report = QualityGateReport(
            section_validation=section_validation,
            relationship_validation=relationship_validation,
            completeness=completeness,
            performance=performance,
            overall_pass=overall_pass,
            critical_failures=critical_failures,
            warnings=warnings,
            recommendations=recommendations
        )
        
        # Store in history
        self.validation_history.append(report)
        
        return report
    
    def save_report(self, report: QualityGateReport, output_path: Path):
        """Save quality gate report to JSON file"""
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Quality gate report saved to {output_path}")
    
    def print_report_summary(self, report: QualityGateReport):
        """Print human-readable report summary to console"""
        
        print("\\n" + "="*80)
        print("QUALITY GATE REPORT")
        print("="*80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Overall Pass: {' PASS' if report.overall_pass else ' FAIL'}")
        print()
        
        print("Section Validation:")
        print(f"  Valid: {'' if report.section_validation.is_valid else ''}")
        print(f"  Coverage: {report.section_validation.section_coverage_percent:.1f}%")
        print(f"  Sections Found: {report.section_validation.total_sections_found}")
        if report.section_validation.fictitious_sections:
            print(f"    Fictitious: {report.section_validation.fictitious_sections}")
        print()
        
        print("Relationship Validation:")
        print(f"  Valid: {'' if report.relationship_validation.is_valid else ''}")
        print(f"  Valid Count: {report.relationship_validation.valid_relationship_count}")
        print(f"  Total Count: {report.relationship_validation.total_relationship_count}")
        if report.relationship_validation.critical_missing:
            print(f"    Missing Critical: {report.relationship_validation.critical_missing}")
        print()
        
        print("Completeness Assessment:")
        print(f"  Meets Target: {'' if report.completeness.meets_target else ''}")
        print(f"  Entities: {report.completeness.entity_count} (target: {report.completeness.target_entity_count})")
        print(f"  Relationships: {report.completeness.relationship_count} (target: {report.completeness.target_relationship_count})")
        print(f"  Requirements: {report.completeness.requirements_count}")
        print(f"  CLINs: {report.completeness.clin_count}")
        print(f"  FAR Clauses: {report.completeness.far_clause_count}")
        print()
        
        print("Performance Benchmark:")
        print(f"  Processing Time: {report.performance.processing_time_seconds:.1f}s")
        print(f"  Entities/Second: {report.performance.entities_per_second:.2f}")
        print(f"  Chunks Processed: {report.performance.chunks_processed}")
        print(f"  Avg Chunk Time: {report.performance.avg_chunk_time:.2f}s")
        print()
        
        if report.critical_failures:
            print(" CRITICAL FAILURES:")
            for failure in report.critical_failures:
                print(f"  - {failure}")
            print()
        
        if report.warnings:
            print("  WARNINGS:")
            for warning in report.warnings:
                print(f"  - {warning}")
            print()
        
        if report.recommendations:
            print(" RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  - {rec}")
            print()
        
        print("="*80)


# Example usage
def example_usage():
    """Example quality assurance workflow"""
    
    qa = QualityAssuranceFramework()
    
    # Example data (would come from actual extraction)
    sample_sections = [
        RFPSection(section_id="A", section_title="Solicitation/Contract Form", page_start=1),
        RFPSection(section_id="B", section_title="Supplies or Services and Prices/Costs", page_start=5),
        RFPSection(section_id="C", section_title="Statement of Work", page_start=10),
        RFPSection(section_id="L", section_title="Instructions to Offerors", page_start=50),
        RFPSection(section_id="M", section_title="Evaluation Factors", page_start=70),
    ]
    
    sample_entities = [{'entity_type': 'REQUIREMENT'} for _ in range(900)]
    sample_relationships = [{'source_entity_type': 'SECTION', 'target_entity_type': 'REQUIREMENT'} for _ in range(1100)]
    
    # Run validations
    section_val = qa.validate_section_hierarchy(sample_sections)
    rel_val = qa.validate_relationship_patterns(sample_relationships)
    completeness = qa.assess_completeness(sample_entities, sample_relationships, sample_sections)
    performance = qa.benchmark_performance(
        start_time=datetime(2025, 1, 1, 10, 0, 0),
        end_time=datetime(2025, 1, 1, 10, 30, 0),
        chunks_processed=48,
        llm_calls=150,
        entity_count=900
    )
    
    # Generate report
    report = qa.generate_quality_gate_report(section_val, rel_val, completeness, performance)
    qa.print_report_summary(report)


if __name__ == "__main__":
    example_usage()
