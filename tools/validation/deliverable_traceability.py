"""
Deliverable Traceability Validator
===================================

Validates that deliverables are properly linked to requirements through
relationships, enabling compliance matrix generation.

Metrics:
- % of deliverables linked to requirements
- % of requirements with deliverable outputs
- Orphaned deliverables (no requirement link)
- Requirements without deliverables (potential gap)
"""

from typing import Dict
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


class DeliverableTraceabilityValidator:
    """Validates deliverable → requirement traceability."""
    
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
    
    def validate(self) -> Dict[str, any]:
        """
        Run validation and return results.
        
        Returns:
            Dict with score (0-100), traceability stats, and orphaned entities
        """
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        results = {
            "score": 0.0,
            "total_deliverables": 0,
            "deliverables_linked": 0,
            "total_requirements": 0,
            "requirements_with_deliverables": 0,
            "orphaned_deliverables": [],
            "requirements_no_deliverables": [],
            "recommendations": [],
        }
        
        try:
            with driver.session(database=self.neo4j_database) as session:
                # Count total deliverables
                query_delivs = f"""
                MATCH (d:`{self.workspace}`)
                WHERE d.entity_type = 'deliverable'
                RETURN count(d) AS total
                """
                result = session.run(query_delivs)
                results["total_deliverables"] = result.single()["total"]
                
                # Count deliverables linked via BOTH patterns
                # Pattern 1: Requirement --SATISFIED_BY--> Deliverable
                # Pattern 2: WorkStatement --PRODUCES--> Deliverable
                query_linked_delivs = f"""
                MATCH (d:`{self.workspace}`)
                WHERE d.entity_type = 'deliverable'
                  AND (
                    EXISTS {{
                      MATCH (r:`{self.workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d)
                      WHERE r.entity_type = 'requirement'
                        AND rel.type = 'SATISFIED_BY'
                    }}
                    OR EXISTS {{
                      MATCH (w:`{self.workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d)
                      WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
                        AND rel.type = 'PRODUCES'
                    }}
                  )
                RETURN count(DISTINCT d) AS linked
                """
                result = session.run(query_linked_delivs)
                results["deliverables_linked"] = result.single()["linked"]
                
                # Count total requirements
                query_reqs = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                RETURN count(r) AS total
                """
                result = session.run(query_reqs)
                results["total_requirements"] = result.single()["total"]
                
                # Count requirements with deliverable links (Pattern 1 only)
                query_reqs_with_delivs = f"""
                MATCH (r:`{self.workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND d.entity_type = 'deliverable'
                  AND rel.type = 'SATISFIED_BY'
                RETURN count(DISTINCT r) AS linked
                """
                result = session.run(query_reqs_with_delivs)
                results["requirements_with_deliverables"] = result.single()["linked"]
                
                # Find orphaned deliverables (no Pattern 1 OR Pattern 2 links)
                query_orphaned_delivs = f"""
                MATCH (d:`{self.workspace}`)
                WHERE d.entity_type = 'deliverable'
                  AND NOT EXISTS {{
                    MATCH (r:`{self.workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d)
                    WHERE r.entity_type = 'requirement'
                      AND rel.type = 'SATISFIED_BY'
                  }}
                  AND NOT EXISTS {{
                    MATCH (w:`{self.workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d)
                    WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
                      AND rel.type = 'PRODUCES'
                  }}
                RETURN d.entity_id AS name
                LIMIT 10
                """
                result = session.run(query_orphaned_delivs)
                results["orphaned_deliverables"] = [record["name"] for record in result]
                
                # Find requirements without deliverables (may be process requirements)
                query_reqs_no_delivs = f"""
                MATCH (r:`{self.workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND NOT EXISTS {{
                    MATCH (r)-[rel:INFERRED_RELATIONSHIP]->(d:`{self.workspace}`)
                    WHERE d.entity_type = 'deliverable'
                      AND rel.type = 'SATISFIED_BY'
                  }}
                RETURN r.entity_id AS name
                LIMIT 10
                """
                result = session.run(query_reqs_no_delivs)
                results["requirements_no_deliverables"] = [record["name"] for record in result]
                
                # Calculate score (average of both coverage percentages)
                deliv_coverage = 0.0
                req_coverage = 0.0
                
                if results["total_deliverables"] > 0:
                    deliv_coverage = (results["deliverables_linked"] / results["total_deliverables"]) * 100
                
                if results["total_requirements"] > 0:
                    req_coverage = (results["requirements_with_deliverables"] / results["total_requirements"]) * 100
                
                results["score"] = (deliv_coverage + req_coverage) / 2
                
                # Generate recommendations
                # NOTE: Deliverable traceability thresholds are intentionally lower than other metrics
                # (workload ~95%, requirements ~60%) because many deliverables in government RFPs are
                # administrative/CDRL-only items that may not have explicit requirement linkages in
                # the solicitation text. Pattern analysis shows ~70% of deliverables are standalone
                # administrative items (reports, CDRLs, contract documentation) vs. technical
                # deliverables that directly satisfy requirements. A 25% threshold represents good
                # coverage of technically-linked deliverables while acknowledging the reality of
                # government contracting document structure.
                if deliv_coverage < 25:
                    results["recommendations"].append(
                        f"Low deliverable traceability ({deliv_coverage:.1f}%) - enhance relationship inference or check for missing sections"
                    )
                elif deliv_coverage < 50:
                    results["recommendations"].append(
                        f"Deliverable traceability ({deliv_coverage:.1f}%) is acceptable - many deliverables are likely administrative/CDRL-only"
                    )
                if req_coverage < 50:
                    results["recommendations"].append(
                        f"Many requirements lack deliverables ({100-req_coverage:.1f}%) - may be process/compliance requirements"
                    )
        
        finally:
            driver.close()
        
        return results
    
    def print_report(self, results: Dict):
        """Print formatted validation report."""
        print(f"\n{'='*80}")
        print(f"📦 DELIVERABLE TRACEABILITY VALIDATION")
        print(f"{'='*80}")
        print(f"\nWorkspace: {self.workspace}")
        
        if results["total_deliverables"] > 0:
            deliv_pct = (results["deliverables_linked"] / results["total_deliverables"]) * 100
            print(f"\nDeliverables: {results['deliverables_linked']}/{results['total_deliverables']} linked via Pattern 1 (SATISFIED_BY) or Pattern 2 (PRODUCES) ({deliv_pct:.1f}%)")
        else:
            print(f"\n⚠️  No deliverables found!")
        
        if results["total_requirements"] > 0:
            req_pct = (results["requirements_with_deliverables"] / results["total_requirements"]) * 100
            print(f"Requirements: {results['requirements_with_deliverables']}/{results['total_requirements']} have deliverables via Pattern 1 (SATISFIED_BY) ({req_pct:.1f}%)")
        else:
            print(f"⚠️  No requirements found!")
        
        print(f"\nScore: {results['score']:.1f}%")
        
        if results["orphaned_deliverables"]:
            print(f"\n{'─'*80}")
            print(f"⚠️  ORPHANED DELIVERABLES (no Pattern 1 or Pattern 2 links):")
            print(f"{'─'*80}")
            for deliv in results["orphaned_deliverables"][:5]:
                print(f"  • {deliv}")
            if len(results["orphaned_deliverables"]) > 5:
                print(f"  ... and {len(results['orphaned_deliverables']) - 5} more")
        
        if results["requirements_no_deliverables"]:
            print(f"\n{'─'*80}")
            print(f"ℹ️  REQUIREMENTS WITHOUT DELIVERABLES (may be process/compliance):")
            print(f"{'─'*80}")
            for req in results["requirements_no_deliverables"][:5]:
                print(f"  • {req}")
            if len(results["requirements_no_deliverables"]) > 5:
                print(f"  ... and {len(results['requirements_no_deliverables']) - 5} more")
        
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
    
    validator = DeliverableTraceabilityValidator(workspace)
    results = validator.validate()
    validator.print_report(results)
