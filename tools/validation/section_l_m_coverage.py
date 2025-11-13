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
        Determine if evaluation_factor entity is a main factor vs supporting entity.
        
        Matches the filter logic in semantic_post_processor.py Algorithm 2b.
        
        Main factors: Factor 1, Subfactor 1.1, Technical Factor, Price Factor, etc.
        Supporting entities: Rating scales (Outstanding, Good), metrics (95% Compliance),
                           thresholds, processes (Price Realism Analysis)
        
        Args:
            entity_id: The entity_id string to classify
        
        Returns:
            True if main evaluation factor, False if supporting entity
        """
        name_lower = entity_id.lower()
        
        # Keep: Main evaluation factors
        keep_patterns = [
            'factor 1', 'factor 2', 'factor 3', 'factor 4',
            'subfactor', 'technical factor', 'price factor',
            'tomp', 'mission essential', 'quality control plan'
        ]
        
        if any(pattern in name_lower for pattern in keep_patterns):
            return True
        
        # Exclude: Rating terms (supporting entities for HAS_RATING_SCALE)
        rating_terms = [
            'outstanding', 'good', 'acceptable', 'marginal', 'unacceptable',
            'pass', 'fail', 'satisfactory', 'unsatisfactory'
        ]
        
        if any(term in name_lower for term in rating_terms):
            return False
        
        # Exclude: Metrics and thresholds (supporting entities for MEASURED_BY)
        if any(indicator in name_lower for indicator in ['%', 'rate', 'threshold', 'level']):
            return False
        
        # Exclude: Evaluation processes and tables (supporting entities for EVALUATED_USING)
        if any(term in name_lower for term in ['evaluation', 'analysis', 'table', '(table)']):
            return False
        
        # Default: Keep as main factor if not explicitly excluded
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
                if req_coverage < 80:
                    results["recommendations"].append(
                        f"Low requirement coverage ({req_coverage:.1f}%) - enhance relationship inference"
                    )
                if eval_coverage < 80:
                    results["recommendations"].append(
                        f"Low eval factor coverage ({eval_coverage:.1f}%) - verify Section M extraction"
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
