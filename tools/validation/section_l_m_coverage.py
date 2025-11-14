"""
Section L ↔ M Coverage Validator
=================================

Validates that requirements (Section L) are properly linked to evaluation
criteria (Section M) through relationships.

Metrics:
- % of requirements linked to evaluation factors
- % of evaluation factors linked to requirements
- Orphaned requirements (no eval criteria)
- Orphaned eval factors (no requirements)
"""

from typing import Dict
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


class SectionLMCoverageValidator:
    """Validates Section L ↔ M requirement/evaluation linkage."""
    
    def __init__(self, workspace: str = None):
        """
        Initialize validator.
        
        Args:
            workspace: Neo4j workspace label (e.g., 'afcapv_adab_iss_2025')
                       If not provided, reads from NEO4J_WORKSPACE env var
        """
        load_dotenv()
        # Use NEO4J_WORKSPACE from .env if workspace not provided
        self.workspace = workspace or os.getenv("NEO4J_WORKSPACE", "default")
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    @staticmethod
    def is_main_evaluation_factor(entity_id: str) -> bool:
        """
        Determine if evaluation_factor entity is a main factor/subfactor vs supporting entity.
        
        STRICT FILTERING APPROACH (similar to deliverable traceability validation):
        - Government RFPs typically have 3-8 main evaluation factors (e.g., Factor A, Technical, Price)
        - Each may have 0-5 subfactors (e.g., Subfactor 1.1, Management Methodology)
        - BUT also have 20-40 supporting entities (rating scales, metrics, processes, tables)
        - ONLY main factors and subfactors should be linked to Section L requirements/instructions
        
        Main factors/subfactors: "Factor A", "Technical Factor", "Past Performance", "Management Methodology"
        Supporting entities (DO NOT LINK): "Outstanding", "95% Compliance", "Price Analysis", "Evaluation Table"
        
        Args:
            entity_id: The entity_id string to classify
        
        Returns:
            True if main factor/subfactor (linkable), False if supporting entity (non-linkable)
        """
        name_lower = entity_id.lower()
        
        # STRICT KEEP: Explicit main factor patterns (high precision)
        # These are the ONLY patterns that indicate a true evaluation factor worth linking
        main_factor_patterns = [
            # Standard factor naming (most common in government RFPs)
            'factor a', 'factor b', 'factor c', 'factor d', 'factor e', 'factor f',
            'factor 1', 'factor 2', 'factor 3', 'factor 4', 'factor 5', 'factor 6',
            'subfactor',
            
            # Named factors (common in AFCAP/SEAPORT/etc.)
            'technical factor', 'price factor', 'cost factor', 'management factor',
            
            # Methodology subfactors (common subfactor naming)
            'methodology' if any(x in name_lower for x in ['management', 'technical', 'navy', 'usmc', 'army']) else None,
            
            # Specific high-value subfactors
            'tomp', 'past performance', 'small business',
            'mission essential', 'quality control plan'
        ]
        
        # Remove None values and check for matches
        main_factor_patterns = [p for p in main_factor_patterns if p is not None]
        
        # CRITICAL: Must match at least ONE main factor pattern
        has_main_pattern = any(pattern in name_lower for pattern in main_factor_patterns)
        
        if not has_main_pattern:
            # If no main pattern found, it's a supporting entity by default
            return False
        
        # EXCLUDE: Even if it matches main pattern, exclude if it's clearly a supporting entity
        
        # Exclude: Rating scale values (HAS_RATING_SCALE supporting entities)
        rating_values = [
            'outstanding', 'good', 'acceptable', 'marginal', 'unacceptable',
            'satisfactory', 'unsatisfactory', 'pass', 'fail',
            'substantial confidence', 'satisfactory confidence', 'limited confidence',
            'no confidence', 'neutral confidence', 'neutral rating',
            'very relevant', 'relevant', 'somewhat relevant', 'not relevant'
        ]
        
        if any(rating in name_lower for rating in rating_values):
            return False
        
        # Exclude: Generic process/analysis terms (EVALUATED_USING supporting entities)
        generic_processes = [
            'analysis', 'assessment', 'government evaluation', 'interviews',
            'realism', 'reasonableness', 'probable cost', 'completeness',
            'adjectival', 'confidence ratings', 'relevancy ratings',
            'description', 'rating' if name_lower == 'rating' else None  # "RATING" alone is generic
        ]
        
        generic_processes = [p for p in generic_processes if p is not None]
        
        if any(term in name_lower for term in generic_processes):
            return False
        
        # Exclude: Metrics/indices (MEASURED_BY supporting entities)
        if any(indicator in name_lower for indicator in [
            '%', 'cei', 'sei', 'kpi', 'index', 'performance',
            'cost effectiveness', 'schedule effectiveness'
        ]):
            return False
        
        # Exclude: Tables and outlines (structural supporting entities)
        if '(table)' in name_lower or 'table' in name_lower or 'outline' in name_lower:
            return False
        
        # Exclude: Volume references (document structure, not evaluation criteria)
        if 'volume' in name_lower and any(x in name_lower for x in ['i', 'ii', 'iii', 'iv', 'v']):
            return False
        
        # PASSED: Has main factor pattern AND not excluded = TRUE MAIN FACTOR
        return True
    
    def validate(self) -> Dict[str, any]:
        """
        Run validation and return results.
        
        Returns:
            Dict with score (0-100), coverage stats, and orphaned entities
        """
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        results = {
            "score": 0.0,
            "total_requirements": 0,
            "requirements_linked": 0,
            "total_eval_factors": 0,
            "eval_factors_linked": 0,
            "orphaned_requirements": [],
            "orphaned_eval_factors": [],
            "recommendations": [],
        }
        
        try:
            with driver.session(database=self.neo4j_database) as session:
                # Count total requirements
                query_reqs = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                RETURN count(r) AS total
                """
                result = session.run(query_reqs)
                results["total_requirements"] = result.single()["total"]
                
                # Count requirements linked to eval factors
                query_linked_reqs = f"""
                MATCH (r:`{self.workspace}`)-[rel]-(e:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND e.entity_type = 'evaluation_factor'
                RETURN count(DISTINCT r) AS linked
                """
                result = session.run(query_linked_reqs)
                results["requirements_linked"] = result.single()["linked"]
                
                # Count total evaluation factors (FILTERED to main factors only)
                query_evals = f"""
                MATCH (e:`{self.workspace}`)
                WHERE e.entity_type = 'evaluation_factor'
                RETURN e.entity_id AS entity_id
                """
                result = session.run(query_evals)
                all_eval_factors = [record["entity_id"] for record in result]
                main_eval_factors = [ef for ef in all_eval_factors if self.is_main_evaluation_factor(ef)]
                results["total_eval_factors"] = len(main_eval_factors)
                results["total_eval_factors_all"] = len(all_eval_factors)  # Track for reporting
                
                # Count eval factors linked to requirements (FILTERED to main factors only)
                query_linked_evals = f"""
                MATCH (e:`{self.workspace}`)-[rel]-(r:`{self.workspace}`)
                WHERE e.entity_type = 'evaluation_factor'
                  AND r.entity_type = 'requirement'
                RETURN DISTINCT e.entity_id AS entity_id
                """
                result = session.run(query_linked_evals)
                linked_eval_factors = [record["entity_id"] for record in result]
                main_linked_eval_factors = [ef for ef in linked_eval_factors if self.is_main_evaluation_factor(ef)]
                results["eval_factors_linked"] = len(main_linked_eval_factors)
                
                # Find orphaned requirements (no eval factor links)
                query_orphaned_reqs = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND NOT EXISTS {{
                    MATCH (r)-[]-(e:`{self.workspace}`)
                    WHERE e.entity_type = 'evaluation_factor'
                  }}
                RETURN r.entity_id AS name
                LIMIT 10
                """
                result = session.run(query_orphaned_reqs)
                results["orphaned_requirements"] = [record["name"] for record in result]
                
                # Find orphaned eval factors (no requirement links) - FILTERED to main factors
                query_orphaned_evals = f"""
                MATCH (e:`{self.workspace}`)
                WHERE e.entity_type = 'evaluation_factor'
                  AND NOT EXISTS {{
                    MATCH (e)-[]-(r:`{self.workspace}`)
                    WHERE r.entity_type = 'requirement'
                  }}
                RETURN e.entity_id AS name
                """
                result = session.run(query_orphaned_evals)
                all_orphaned_evals = [record["name"] for record in result]
                main_orphaned_evals = [ef for ef in all_orphaned_evals if self.is_main_evaluation_factor(ef)]
                results["orphaned_eval_factors"] = main_orphaned_evals[:10]  # Limit to 10 for display
                
                # Calculate score (average of both coverage percentages)
                if results["total_requirements"] > 0 and results["total_eval_factors"] > 0:
                    req_coverage = (results["requirements_linked"] / results["total_requirements"]) * 100
                    eval_coverage = (results["eval_factors_linked"] / results["total_eval_factors"]) * 100
                    results["score"] = (req_coverage + eval_coverage) / 2
                else:
                    results["score"] = 0.0
                
                # Generate recommendations
                # NOTE: Section L↔M thresholds are intentionally lower than workload metrics (~95%)
                # because government RFPs typically have:
                # - 3-8 main evaluation factors (e.g., Factor A, Technical, Price)
                # - 20-100+ requirements (Section L instructions, compliance items)
                # - NOT all requirements map to factors (many are process/admin requirements)
                # - ~60-80% requirement coverage is realistic and acceptable
                # - ~50%+ factor coverage indicates good Section M extraction
                #
                # Many requirements are procedural (deadlines, formats, submission rules) and don't
                # directly map to scored evaluation factors. This is normal RFP structure.
                if req_coverage < 60:
                    results["recommendations"].append(
                        f"Low requirement coverage ({req_coverage:.1f}%) - may need to enhance relationship inference"
                    )
                elif req_coverage < 80:
                    results["recommendations"].append(
                        f"Requirement coverage ({req_coverage:.1f}%) is acceptable - many requirements are procedural/administrative"
                    )
                
                if eval_coverage < 50:
                    results["recommendations"].append(
                        f"Low eval factor coverage ({eval_coverage:.1f}%) - verify Section M extraction quality or check for missing factors"
                    )
                elif eval_coverage < 80:
                    results["recommendations"].append(
                        f"Eval factor coverage ({eval_coverage:.1f}%) is acceptable - most main factors have requirement links"
                    )
        
        finally:
            driver.close()
        
        return results
    
    def print_report(self, results: Dict):
        """Print formatted validation report."""
        print(f"\n{'='*80}")
        print(f"🔗 SECTION L ↔ M COVERAGE VALIDATION")
        print(f"{'='*80}")
        print(f"\nWorkspace: {self.workspace}")
        
        if results["total_requirements"] > 0:
            req_pct = (results["requirements_linked"] / results["total_requirements"]) * 100
            print(f"\nRequirements: {results['requirements_linked']}/{results['total_requirements']} linked ({req_pct:.1f}%)")
        else:
            print(f"\n⚠️  No requirements found!")
        
        if results["total_eval_factors"] > 0:
            eval_pct = (results["eval_factors_linked"] / results["total_eval_factors"]) * 100
            total_all = results.get("total_eval_factors_all", results["total_eval_factors"])
            filtered_count = total_all - results["total_eval_factors"]
            print(f"Eval Factors: {results['eval_factors_linked']}/{results['total_eval_factors']} linked ({eval_pct:.1f}%)")
            if filtered_count > 0:
                print(f"              ({filtered_count} supporting entities filtered: rating scales, metrics, processes)")
        else:
            print(f"⚠️  No evaluation factors found!")
        
        print(f"\nScore: {results['score']:.1f}%")
        
        if results["orphaned_requirements"]:
            print(f"\n{'─'*80}")
            print(f"⚠️  ORPHANED REQUIREMENTS (no eval factor links):")
            print(f"{'─'*80}")
            for req in results["orphaned_requirements"][:5]:
                print(f"  • {req}")
            if len(results["orphaned_requirements"]) > 5:
                print(f"  ... and {len(results['orphaned_requirements']) - 5} more")
        
        if results["orphaned_eval_factors"]:
            print(f"\n{'─'*80}")
            print(f"⚠️  ORPHANED EVAL FACTORS (no requirement links):")
            print(f"{'─'*80}")
            for ef in results["orphaned_eval_factors"][:5]:
                print(f"  • {ef}")
            if len(results["orphaned_eval_factors"]) > 5:
                print(f"  ... and {len(results['orphaned_eval_factors']) - 5} more")
        
        if results["recommendations"]:
            print(f"\n{'─'*80}")
            print("RECOMMENDATIONS:")
            print(f"{'─'*80}")
            for rec in results["recommendations"]:
                print(f"  • {rec}")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import sys
    
    workspace = sys.argv[1] if len(sys.argv) > 1 else "afcapv_adab_iss_2025"
    
    validator = SectionLMCoverageValidator(workspace)
    results = validator.validate()
    validator.print_report(results)
