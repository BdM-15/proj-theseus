"""
Workload Enrichment Completeness Validator
===========================================

Validates that requirements have been enriched with workload metadata.

Metrics:
- % of requirements enriched
- BOE category coverage (all 7 categories used?)
- Average confidence scores
- Missing enrichment for critical requirements
"""

from typing import Dict
from neo4j import GraphDatabase
import os
import json
from dotenv import load_dotenv
from collections import defaultdict


class WorkloadCompletenessValidator:
    """Validates workload metadata enrichment completeness."""
    
    def __init__(self, workspace: str):
        """
        Initialize validator.
        
        Args:
            workspace: Neo4j workspace label (e.g., 'afcapv_adab_iss_2025')
        """
        load_dotenv()
        self.workspace = workspace
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        self.boe_categories = [
            "Labor", "Materials", "ODCs", "QA",
            "Logistics", "Lifecycle", "Compliance"
        ]
    
    def validate(self) -> Dict[str, any]:
        """
        Run validation and return results.
        
        Returns:
            Dict with score (0-100), enrichment stats, and category usage
        """
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        results = {
            "score": 0.0,
            "total_requirements": 0,
            "enriched_requirements": 0,
            "category_usage": defaultdict(int),
            "avg_confidence": 0.0,
            "missing_categories": [],
            "recommendations": [],
        }
        
        try:
            with driver.session(database=self.neo4j_database) as session:
                # Count total requirements
                query_total = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                RETURN count(r) AS total
                """
                result = session.run(query_total)
                results["total_requirements"] = result.single()["total"]
                
                # Count enriched requirements
                query_enriched = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND r.enriched_by IS NOT NULL
                  AND r.has_workload_metric IS NOT NULL
                RETURN count(r) AS enriched
                """
                result = session.run(query_enriched)
                results["enriched_requirements"] = result.single()["enriched"]
                
                # Get category usage and confidence scores
                query_categories = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND r.workload_categories IS NOT NULL
                  AND r.boe_relevance IS NOT NULL
                RETURN r.workload_categories AS categories,
                       r.boe_relevance AS scores
                """
                result = session.run(query_categories)
                
                total_confidence = 0
                confidence_count = 0
                
                for record in result:
                    # Parse categories (JSON string)
                    try:
                        categories = json.loads(record["categories"]) if isinstance(record["categories"], str) else record["categories"]
                        for cat in categories:
                            if cat in self.boe_categories:
                                results["category_usage"][cat] += 1
                    except:
                        pass
                    
                    # Parse confidence scores
                    try:
                        scores = json.loads(record["scores"]) if isinstance(record["scores"], str) else record["scores"]
                        for score in scores.values():
                            total_confidence += score
                            confidence_count += 1
                    except:
                        pass
                
                # Calculate average confidence
                if confidence_count > 0:
                    results["avg_confidence"] = total_confidence / confidence_count
                
                # Check for missing categories
                for cat in self.boe_categories:
                    if results["category_usage"][cat] == 0:
                        results["missing_categories"].append(cat)
                
                # Calculate score
                if results["total_requirements"] > 0:
                    enrichment_pct = (results["enriched_requirements"] / results["total_requirements"]) * 100
                    category_coverage_pct = ((7 - len(results["missing_categories"])) / 7) * 100
                    
                    # Weighted score: 70% enrichment, 20% category coverage, 10% confidence
                    results["score"] = (
                        enrichment_pct * 0.7 +
                        category_coverage_pct * 0.2 +
                        results["avg_confidence"] * 100 * 0.1
                    )
                else:
                    results["score"] = 0.0
                
                # Generate recommendations
                if enrichment_pct < 100:
                    results["recommendations"].append(
                        f"Only {enrichment_pct:.1f}% of requirements enriched - rerun workload enrichment"
                    )
                if results["missing_categories"]:
                    results["recommendations"].append(
                        f"Missing BOE categories: {', '.join(results['missing_categories'])}"
                    )
                if results["avg_confidence"] < 0.7:
                    results["recommendations"].append(
                        f"Low confidence scores ({results['avg_confidence']:.2f}) - review enrichment prompts"
                    )
        
        finally:
            driver.close()
        
        return results
    
    def print_report(self, results: Dict):
        """Print formatted validation report."""
        print(f"\n{'='*80}")
        print(f"📊 WORKLOAD ENRICHMENT COMPLETENESS VALIDATION")
        print(f"{'='*80}")
        print(f"\nWorkspace: {self.workspace}")
        
        if results["total_requirements"] > 0:
            enrichment_pct = (results["enriched_requirements"] / results["total_requirements"]) * 100
            print(f"\nEnriched Requirements: {results['enriched_requirements']}/{results['total_requirements']} ({enrichment_pct:.1f}%)")
        else:
            print(f"\n⚠️  No requirements found!")
        
        print(f"Average Confidence: {results['avg_confidence']:.2f}")
        print(f"Score: {results['score']:.1f}%")
        
        print(f"\n{'─'*80}")
        print("BOE CATEGORY USAGE:")
        print(f"{'─'*80}")
        
        for cat in self.boe_categories:
            count = results["category_usage"][cat]
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {cat:15s}: {count:3d} requirements")
        
        if results["missing_categories"]:
            print(f"\n⚠️  Missing categories: {', '.join(results['missing_categories'])}")
        
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
    
    validator = WorkloadCompletenessValidator(workspace)
    results = validator.validate()
    validator.print_report(results)
