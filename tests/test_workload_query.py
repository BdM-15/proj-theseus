"""
Optional Neo4j integration test: workload enrichment properties exist.

Skipped by default; enable with RUN_NEO4J_TESTS=true.
"""

import os

import pytest
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


@pytest.mark.skipif(
    (os.getenv("RUN_NEO4J_TESTS", "") or "").strip().lower() not in {"1", "true", "yes", "y"},
    reason="Set RUN_NEO4J_TESTS=true to run Neo4j workload enrichment test",
)
def test_workload_enrichment_properties_exist():
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", os.getenv("NEO4J_USERNAME", "neo4j"))
    pwd = os.getenv("NEO4J_PASSWORD")
    if not pwd:
        pytest.skip("NEO4J_PASSWORD not set")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    try:
        with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
            q = """
            MATCH (r:Entity)
            WHERE r.entity_type = 'requirement' AND r.has_workload_metric = true
            RETURN count(r) AS n
            """
            n = session.run(q).single()["n"]
            assert isinstance(n, int)
    except ServiceUnavailable:
        pytest.skip("Neo4j not reachable on NEO4J_URI")
    finally:
        driver.close()

