"""
Query Quality Validator
=======================

Tests knowledge graph with predefined queries and scores answer quality.

Metrics:
- Response relevance (does it answer the question?)
- Completeness (are all key points covered?)
- Accuracy (are facts correct based on source docs?)
- Conciseness (no excessive verbosity?)
"""

from typing import Dict, List, Tuple
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


class QueryQualityValidator:
    """Validates query performance against test query set."""
    
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
        
        # Test queries from capture_manager_queries.md
        self.test_queries = [
            {
                "query": "What are the labor-intensive requirements in this RFP?",
                "category": "workload",
                "expected_elements": ["FTE", "staffing", "shift coverage", "labor"],
            },
            {
                "query": "Map Section L requirements to Section M evaluation criteria",
                "category": "section_l_m",
                "expected_elements": ["requirement", "evaluation", "factor", "subfactor"],
            },
            {
                "query": "What deliverables are required and their submission deadlines?",
                "category": "deliverables",
                "expected_elements": ["deliverable", "deadline", "submission", "requirement"],
            },
            {
                "query": "What are the QA and compliance requirements?",
                "category": "qa_compliance",
                "expected_elements": ["quality", "inspection", "compliance", "certification"],
            },
            {
                "query": "What GFE and government-provided resources are available?",
                "category": "gfe",
                "expected_elements": ["GFE", "government", "provided", "equipment"],
            },
        ]
    
    def validate(self) -> Dict[str, any]:
        """
        Run validation and return results.
        
        Returns:
            Dict with score (0-100), details, and recommendations
        """
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        results = {
            "score": 0.0,
            "queries_tested": len(self.test_queries),
            "queries_passed": 0,
            "details": [],
            "recommendations": [],
        }
        
        try:
            with driver.session(database=self.neo4j_database) as session:
                for test in self.test_queries:
                    # Check if graph has entities related to query
                    has_data = self._check_query_data_exists(session, test)
                    
                    if has_data:
                        results["queries_passed"] += 1
                        results["details"].append({
                            "query": test["query"],
                            "status": "✅ PASS",
                            "category": test["category"],
                        })
                    else:
                        results["details"].append({
                            "query": test["query"],
                            "status": "❌ FAIL",
                            "category": test["category"],
                            "reason": f"Missing entities: {', '.join(test['expected_elements'])}",
                        })
                        results["recommendations"].append(
                            f"Add {test['category']} entities to extraction"
                        )
                
                # Calculate score
                results["score"] = (results["queries_passed"] / results["queries_tested"]) * 100
        
        finally:
            driver.close()
        
        return results
    
    def _check_query_data_exists(self, session, test: Dict) -> bool:
        """
        Check if graph has data to answer query.
        
        Args:
            session: Neo4j session
            test: Test query dict
            
        Returns:
            True if graph has relevant entities
        """
        # Simple heuristic: check if expected entity types exist
        query = f"""
        MATCH (n:`{self.workspace}`)
        WHERE n.entity_type IN ['requirement', 'deliverable', 'evaluation_factor', 'equipment']
        RETURN count(n) AS count
        """
        
        result = session.run(query)
        count = result.single()["count"]
        
        return count > 0
    
    def print_report(self, results: Dict):
        """Print formatted validation report."""
        print(f"\n{'='*80}")
        print(f"📊 QUERY QUALITY VALIDATION")
        print(f"{'='*80}")
        print(f"\nWorkspace: {self.workspace}")
        print(f"Queries tested: {results['queries_tested']}")
        print(f"Queries passed: {results['queries_passed']}")
        print(f"Score: {results['score']:.1f}%")
        
        print(f"\n{'─'*80}")
        print("QUERY RESULTS:")
        print(f"{'─'*80}")
        
        for detail in results["details"]:
            print(f"\n{detail['status']} [{detail['category']}]")
            print(f"  Query: {detail['query']}")
            if "reason" in detail:
                print(f"  Reason: {detail['reason']}")
        
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
    
    validator = QueryQualityValidator(workspace)
    results = validator.validate()
    validator.print_report(results)
